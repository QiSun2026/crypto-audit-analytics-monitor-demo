from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from .engine import load_precommitment, repository_root, run_demo
from .harness.artifacts import (
    build_artifact_manifest,
    verify_artifact_manifest,
)
from .harness.canonical import (
    canonical_json,
    sha256_bytes,
    sha256_file,
    stable_id,
    write_canonical_json,
)
from .harness.review_chain import active_review_records
from .review_log import read_review_log


ALLOWED_TESTS = {
    "commission_full_population_v4": "run_registered_commission_test",
}

PROHIBITED_DRAFT_FIELDS = {
    "automated_action",
    "conclusion",
    "control_effectiveness",
    "disposition",
    "review_status",
    "signature",
    "signed_by",
    "thresholds",
}

PROHIBITED_DRAFT_PHRASES = {
    "control is effective",
    "fraud confirmed",
    "misconduct confirmed",
    "no exception",
    "no issue",
}

HUMAN_PROHIBITIONS = [
    "agent_must_not_change_scope",
    "agent_must_not_change_materiality",
    "agent_must_not_change_thresholds",
    "agent_must_not_run_unreviewed_code",
    "agent_must_not_modify_source_data",
    "agent_must_not_hide_or_close_exceptions",
    "agent_must_not_close_exceptions",
    "agent_must_not_convert_missing_evidence_to_no_issue",
    "agent_must_not_authenticate_evidence",
    "agent_must_not_sign_conclusions",
]

EXPECTED_POST_EXECUTION_STEPS = [
    "draft_source_cited_investigation_questions",
    "preserve_unknowns",
    "route_every_exception_to_human_review",
    "draft_unsigned_conclusion_from_human_records_only",
]

MANDATE_FIELDS = {
    "schema_version",
    "mandate_id",
    "case_id",
    "authority",
    "identity_status",
    "created_by",
    "created_at_utc",
    "synthetic_only",
    "scope",
    "thresholds",
    "configuration_version_id",
    "configuration_sha256",
    "implementation_sha256",
    "allowed_test_ids",
    "required_human_checkpoints",
    "prohibitions",
    "mandate_sha256",
}

PROPOSAL_FIELDS = {
    "schema_version",
    "proposal_id",
    "status",
    "proposal_origin",
    "external_model_used",
    "mandate_id",
    "mandate_sha256",
    "procedure_calls",
    "post_execution_steps",
    "proposal_sha256",
}

FREEZE_FIELDS = {
    "schema_version",
    "freeze_id",
    "action",
    "identity_status",
    "reviewer_id",
    "frozen_at_utc",
    "mandate_id",
    "mandate_sha256",
    "proposal_id",
    "proposal_sha256",
    "locked_thresholds",
    "locked_test_ids",
    "note",
    "freeze_record_sha256",
}


class DraftingProvider(Protocol):
    provider_id: str
    provider_version: str
    external_model_used: bool

    def generate(self, prompt: dict[str, Any]) -> dict[str, Any]:
        ...


class FixtureDraftingProvider:
    """Deterministic fixture used to test the control plane without an LLM."""

    provider_id = "deterministic_fixture"
    provider_version = "1"
    external_model_used = False

    def generate(self, prompt: dict[str, Any]) -> dict[str, Any]:
        source_rows = list(prompt["allowed_source_row_ids"])
        exception_id = prompt["exception"]["exception_id"]
        rule_branch = prompt["exception"]["rule_branch"]
        return {
            "sentences": [
                {
                    "text": (
                        f"{exception_id} was routed by registered assertion "
                        f"{rule_branch} and remains pending human review."
                    ),
                    "source_row_ids": source_rows,
                }
            ],
            "investigation_questions": [
                {
                    "text": (
                        "What authorization or commercial evidence explains "
                        "the cited source-row pattern?"
                    ),
                    "source_row_ids": source_rows,
                }
            ],
            "unknowns": [
                {
                    "text": (
                        "The cited rows do not establish intent, misconduct, "
                        "or control effectiveness."
                    ),
                    "source_row_ids": source_rows,
                }
            ],
        }


def _record_hash(record: dict[str, Any], field: str) -> str:
    payload = dict(record)
    payload.pop(field, None)
    return sha256_bytes(canonical_json(payload))


def _implementation_hash(root: Path) -> str:
    files = sorted(
        (root / "src" / "crypto_audit_monitor").rglob("*.py"),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    inventory = [
        {
            "path": path.relative_to(root).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in files
    ]
    return sha256_bytes(canonical_json(inventory))


def _attach_hash(record: dict[str, Any], field: str) -> dict[str, Any]:
    result = dict(record)
    result[field] = _record_hash(result, field)
    return result


def _validate_hash(
    record: dict[str, Any],
    field: str,
    label: str,
) -> None:
    stored = record.get(field)
    if not stored or stored != _record_hash(record, field):
        raise ValueError(f"{label} hash mismatch")


def _require_exact_fields(
    record: dict[str, Any],
    expected: set[str],
    label: str,
) -> None:
    if set(record) != expected:
        missing = sorted(expected - set(record))
        unexpected = sorted(set(record) - expected)
        raise ValueError(
            f"{label} schema mismatch; missing={missing}; "
            f"unexpected={unexpected}"
        )


def _parse_utc_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{label} must be an ISO-8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise ValueError(
            f"{label} must be an ISO-8601 UTC timestamp"
        ) from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(
        parsed
    ):
        raise ValueError(f"{label} must be an ISO-8601 UTC timestamp")
    return parsed


def build_demo_mandate(root: Path) -> dict[str, Any]:
    config = load_precommitment(root)
    config_path = root / "config" / "rule_precommitment.json"
    mandate = {
        "schema_version": 1,
        "mandate_id": "MANDATE-COMMISSION-AGENTIC-V1",
        "case_id": "synthetic-commission-assurance",
        "authority": "human_directed",
        "identity_status": "self_attested_prototype",
        "created_by": "audit-owner-demo",
        "created_at_utc": "2026-07-30T15:30:00Z",
        "synthetic_only": True,
        "scope": {
            "population": "fabricated wallet and commission population",
            "control_objectives": ["CO-01", "CO-02"],
            "materiality_basis": (
                "Prototype review configuration; not company risk appetite "
                "or a production audit threshold."
            ),
        },
        "thresholds": {
            "review_threshold_minor": config["review_threshold_minor"],
            "window_days_inclusive": config["window_days_inclusive"],
        },
        "configuration_version_id": config["configuration_version_id"],
        "configuration_sha256": sha256_file(config_path),
        "implementation_sha256": _implementation_hash(root),
        "allowed_test_ids": ["commission_full_population_v4"],
        "required_human_checkpoints": [
            "freeze_plan_before_execution",
            "decide_each_exception",
            "sign_any_final_assurance_conclusion",
        ],
        "prohibitions": HUMAN_PROHIBITIONS,
    }
    return _attach_hash(mandate, "mandate_sha256")


def _validate_mandate(mandate: dict[str, Any]) -> None:
    _require_exact_fields(mandate, MANDATE_FIELDS, "mandate")
    _validate_hash(mandate, "mandate_sha256", "mandate")
    if mandate.get("schema_version") != 1:
        raise ValueError("unsupported mandate schema version")
    if (
        not str(mandate.get("mandate_id", "")).strip()
        or not str(mandate.get("case_id", "")).strip()
        or not str(mandate.get("created_by", "")).strip()
    ):
        raise ValueError("mandate identity fields must be non-empty")
    if mandate.get("identity_status") != "self_attested_prototype":
        raise ValueError("mandate identity status is not authorized")
    _parse_utc_timestamp(mandate.get("created_at_utc"), "mandate created_at")
    if mandate.get("authority") != "human_directed":
        raise ValueError("mandate must remain human directed")
    if mandate.get("synthetic_only") is not True:
        raise ValueError("this Prototype accepts synthetic data only")
    allowed = mandate.get("allowed_test_ids")
    if not isinstance(allowed, list) or not allowed:
        raise ValueError("mandate test allowlist is empty")
    unknown = sorted(set(allowed) - set(ALLOWED_TESTS))
    if unknown:
        raise ValueError("mandate contains a test that is not allowlisted")
    if not set(HUMAN_PROHIBITIONS) <= set(mandate.get("prohibitions", [])):
        raise ValueError("mandate is missing a required prohibition")


def build_planning_proposal(mandate: dict[str, Any]) -> dict[str, Any]:
    _validate_mandate(mandate)
    test_id = mandate["allowed_test_ids"][0]
    proposal = {
        "schema_version": 1,
        "proposal_id": f"PLAN-{stable_id(mandate['mandate_sha256'])}",
        "status": "untrusted_proposal_pending_human_freeze",
        "proposal_origin": "deterministic_planning_fixture",
        "external_model_used": False,
        "mandate_id": mandate["mandate_id"],
        "mandate_sha256": mandate["mandate_sha256"],
        "procedure_calls": [
            {
                "sequence": 1,
                "tool": ALLOWED_TESTS[test_id],
                "test_id": test_id,
                "configuration_version_id": (
                    mandate["configuration_version_id"]
                ),
                "configuration_sha256": mandate["configuration_sha256"],
                "implementation_sha256": (
                    mandate["implementation_sha256"]
                ),
                "purpose": (
                    "Run the frozen deterministic full-population tests and "
                    "export their evidence pack."
                ),
            }
        ],
        "post_execution_steps": EXPECTED_POST_EXECUTION_STEPS,
    }
    return _attach_hash(proposal, "proposal_sha256")


def _validate_proposal(
    mandate: dict[str, Any],
    proposal: dict[str, Any],
) -> None:
    _require_exact_fields(proposal, PROPOSAL_FIELDS, "proposal")
    _validate_hash(proposal, "proposal_sha256", "proposal")
    if proposal.get("schema_version") != 1:
        raise ValueError("unsupported proposal schema version")
    if proposal.get("status") != "untrusted_proposal_pending_human_freeze":
        raise ValueError("proposal status is not authorized")
    if proposal.get("proposal_origin") != "deterministic_planning_fixture":
        raise ValueError("proposal origin is not authorized")
    if proposal.get("external_model_used") is not False:
        raise ValueError("external model proposal is not authorized")
    if (
        proposal.get("mandate_id") != mandate["mandate_id"]
        or proposal.get("mandate_sha256") != mandate["mandate_sha256"]
    ):
        raise ValueError("proposal is not bound to the current mandate")
    if proposal.get("post_execution_steps") != EXPECTED_POST_EXECUTION_STEPS:
        raise ValueError("proposal post-execution steps are not authorized")
    _validate_procedure_allowlist(mandate, proposal)


def _validate_procedure_allowlist(
    mandate: dict[str, Any],
    proposal: dict[str, Any],
) -> None:
    calls = proposal.get("procedure_calls")
    if not isinstance(calls, list) or len(calls) != 1:
        raise ValueError("the lean workflow requires exactly one procedure call")
    call = calls[0]
    test_id = call.get("test_id")
    if (
        test_id not in ALLOWED_TESTS
        or test_id not in mandate.get("allowed_test_ids", [])
        or call.get("tool") != ALLOWED_TESTS.get(test_id)
    ):
        raise ValueError("procedure is not allowlisted")
    if (
        call.get("configuration_version_id")
        != mandate.get("configuration_version_id")
        or call.get("configuration_sha256")
        != mandate.get("configuration_sha256")
        or call.get("implementation_sha256")
        != mandate.get("implementation_sha256")
    ):
        raise ValueError("procedure configuration does not match the mandate")


def freeze_plan(
    mandate: dict[str, Any],
    proposal: dict[str, Any],
    *,
    reviewer_id: str,
    frozen_at_utc: str,
) -> dict[str, Any]:
    _validate_mandate(mandate)
    _validate_proposal(mandate, proposal)
    if not reviewer_id.strip():
        raise ValueError("human freeze requires a reviewer_id")
    frozen_at = _parse_utc_timestamp(frozen_at_utc, "freeze frozen_at")
    created_at = _parse_utc_timestamp(
        mandate["created_at_utc"],
        "mandate created_at",
    )
    if frozen_at < created_at:
        raise ValueError("human freeze cannot predate the mandate")
    freeze = {
        "schema_version": 1,
        "freeze_id": f"FREEZE-{stable_id(proposal['proposal_sha256'])}",
        "action": "human_freeze_approved_for_execution",
        "identity_status": "self_attested_prototype",
        "reviewer_id": reviewer_id,
        "frozen_at_utc": frozen_at_utc,
        "mandate_id": mandate["mandate_id"],
        "mandate_sha256": mandate["mandate_sha256"],
        "proposal_id": proposal["proposal_id"],
        "proposal_sha256": proposal["proposal_sha256"],
        "locked_thresholds": mandate["thresholds"],
        "locked_test_ids": mandate["allowed_test_ids"],
        "note": (
            "Prototype self-attestation only; this is not authenticated "
            "identity or an external timestamp."
        ),
    }
    return _attach_hash(freeze, "freeze_record_sha256")


def _validate_frozen_plan(
    mandate: dict[str, Any],
    proposal: dict[str, Any],
    freeze: dict[str, Any],
) -> None:
    _validate_mandate(mandate)
    _validate_proposal(mandate, proposal)
    _require_exact_fields(freeze, FREEZE_FIELDS, "human freeze")
    if freeze.get("schema_version") != 1:
        raise ValueError("unsupported human freeze schema version")
    if freeze.get("action") != "human_freeze_approved_for_execution":
        raise ValueError("valid human freeze is required before execution")
    if freeze.get("identity_status") != "self_attested_prototype":
        raise ValueError("human freeze identity status is not authorized")
    if not str(freeze.get("reviewer_id", "")).strip():
        raise ValueError("human freeze requires a reviewer_id")
    frozen_at = _parse_utc_timestamp(
        freeze.get("frozen_at_utc"),
        "freeze frozen_at",
    )
    created_at = _parse_utc_timestamp(
        mandate["created_at_utc"],
        "mandate created_at",
    )
    if frozen_at < created_at:
        raise ValueError("human freeze cannot predate the mandate")
    _validate_hash(freeze, "freeze_record_sha256", "human freeze")
    if (
        freeze.get("mandate_id") != mandate["mandate_id"]
        or freeze.get("proposal_id") != proposal["proposal_id"]
    ):
        raise ValueError("human freeze identity binding mismatch")
    if freeze.get("mandate_sha256") != mandate["mandate_sha256"]:
        raise ValueError("human freeze is bound to a different mandate")
    if freeze.get("proposal_sha256") != proposal["proposal_sha256"]:
        raise ValueError("human freeze is bound to a different proposal")
    if freeze.get("locked_thresholds") != mandate["thresholds"]:
        raise ValueError("human freeze threshold binding mismatch")
    if freeze.get("locked_test_ids") != mandate["allowed_test_ids"]:
        raise ValueError("human freeze test binding mismatch")


def execute_frozen_plan(
    mandate: dict[str, Any],
    proposal: dict[str, Any],
    freeze: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    _validate_frozen_plan(mandate, proposal, freeze)
    root = repository_root()
    current = load_precommitment(root)
    current_hash = sha256_file(root / "config" / "rule_precommitment.json")
    if (
        current["configuration_version_id"]
        != mandate["configuration_version_id"]
        or current_hash != mandate["configuration_sha256"]
        or current["review_threshold_minor"]
        != mandate["thresholds"]["review_threshold_minor"]
        or current["window_days_inclusive"]
        != mandate["thresholds"]["window_days_inclusive"]
        or _implementation_hash(root) != mandate["implementation_sha256"]
    ):
        raise ValueError("frozen mandate no longer matches registered configuration")
    result = run_demo(output_dir)
    manifest = result["run_manifest"]
    if (
        manifest["configuration_version_id"]
        != mandate["configuration_version_id"]
        or manifest["precommitment_sha256"]
        != mandate["configuration_sha256"]
    ):
        raise ValueError("deterministic run is not bound to the frozen mandate")
    return result


def _find_prohibited_fields(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        found.update(set(value) & PROHIBITED_DRAFT_FIELDS)
        for child in value.values():
            found.update(_find_prohibited_fields(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_find_prohibited_fields(child))
    return found


def validate_investigation_draft(
    draft: dict[str, Any],
    exception: dict[str, Any],
) -> None:
    prohibited = sorted(_find_prohibited_fields(draft))
    if prohibited:
        raise ValueError(
            "prohibited output field: " + ", ".join(prohibited)
        )
    if draft.get("exception_id") != exception.get("exception_id"):
        raise ValueError("draft references a different exception")
    if draft.get("status") != "draft_for_human_review":
        raise ValueError("investigation output must remain a human-review draft")
    if draft.get("state_changes") != []:
        raise ValueError("investigation draft cannot mutate exception state")
    allowed = set(exception.get("source_row_ids", []))
    if set(draft.get("allowed_source_row_ids", [])) != allowed:
        raise ValueError("draft lineage declaration does not match the exception")
    for field in ("sentences", "investigation_questions", "unknowns"):
        items = draft.get(field)
        if not isinstance(items, list):
            raise ValueError(f"draft {field} must be a list")
        if field in {"sentences", "unknowns"} and not items:
            raise ValueError(
                f"investigation draft requires at least one {field[:-1]}"
            )
        for item in items:
            cited = item.get("source_row_ids")
            if not isinstance(cited, list) or not cited:
                raise ValueError("every drafted claim requires a claim-level citation")
            if not set(cited) <= allowed:
                raise ValueError("draft citation is outside exception lineage")
            if not str(item.get("text", "")).strip():
                raise ValueError("drafted claim text is empty")
            normalized = str(item["text"]).strip().lower()
            if any(
                phrase in normalized
                for phrase in PROHIBITED_DRAFT_PHRASES
            ):
                raise ValueError(
                    "draft cannot convert evidence into a bounded conclusion"
                )


def _draft_investigations(
    exceptions: list[dict[str, Any]],
    provider: DraftingProvider,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    drafts: list[dict[str, Any]] = []
    exchanges: list[dict[str, Any]] = []
    for exception in exceptions:
        if exception.get("bucket") != "potential_exception":
            continue
        prompt = {
            "system_boundary": (
                "Draft source-cited explanation and questions only. Do not "
                "change status, threshold, disposition, conclusion or source."
            ),
            "exception": {
                key: exception.get(key)
                for key in (
                    "exception_id",
                    "control_objective",
                    "rule_branch",
                    "rule_version_id",
                    "signal_statement",
                    "review_status",
                )
            },
            "allowed_source_row_ids": exception["source_row_ids"],
        }
        raw_output = provider.generate(prompt)
        prohibited = sorted(_find_prohibited_fields(raw_output))
        if prohibited:
            raise ValueError(
                "prohibited output field: " + ", ".join(prohibited)
            )
        prompt_sha256 = sha256_bytes(canonical_json(prompt))
        raw_output_sha256 = sha256_bytes(canonical_json(raw_output))
        draft = {
            "schema_version": 1,
            "draft_id": f"DRAFT-{stable_id(exception['exception_id'])}",
            "exception_id": exception["exception_id"],
            "provider_id": provider.provider_id,
            "provider_version": provider.provider_version,
            "prompt_sha256": prompt_sha256,
            "raw_output_sha256": raw_output_sha256,
            "status": "draft_for_human_review",
            "allowed_source_row_ids": exception["source_row_ids"],
            "sentences": raw_output.get("sentences"),
            "investigation_questions": raw_output.get(
                "investigation_questions"
            ),
            "unknowns": raw_output.get("unknowns"),
            "state_changes": [],
        }
        validate_investigation_draft(draft, exception)
        drafts.append(draft)
        exchanges.append(
            {
                "exception_id": exception["exception_id"],
                "prompt": prompt,
                "prompt_sha256": prompt_sha256,
                "raw_output": raw_output,
                "raw_output_sha256": raw_output_sha256,
            }
        )
    sentence_count = sum(len(item["sentences"]) for item in drafts)
    cited_count = sum(
        bool(sentence["source_row_ids"])
        for draft in drafts
        for sentence in draft["sentences"]
    )
    raw = {
        "schema_version": 1,
        "provider": {
            "provider_id": provider.provider_id,
            "provider_version": provider.provider_version,
            "external_model_used": provider.external_model_used,
        },
        "exchanges": exchanges,
        "retention_note": (
            "Raw fixture input and output retained for replay. Synthetic "
            "Prototype data only."
        ),
    }
    metrics = {
        "drafted_exceptions": len(drafts),
        "sentences": sentence_count,
        "cited_sentences": cited_count,
        "citation_coverage_percent": (
            round(cited_count / sentence_count * 100, 1)
            if sentence_count
            else 0.0
        ),
        "unauthorized_state_mutations": 0,
    }
    return drafts, raw, metrics


def draft_bounded_conclusion(
    exceptions: list[dict[str, Any]],
    human_reviews: list[dict[str, Any]],
    *,
    proposed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    latest_by_exception = active_review_records(human_reviews)
    potential_ids = {
        item["exception_id"]
        for item in exceptions
        if item.get("bucket") == "potential_exception"
    }
    closed = sorted(
        exception_id
        for exception_id, review in latest_by_exception.items()
        if exception_id in potential_ids
        and review["disposition"] == "close_with_explanation"
    )
    escalated = sorted(
        exception_id
        for exception_id, review in latest_by_exception.items()
        if exception_id in potential_ids
        and review["disposition"] == "escalate_for_investigation"
    )
    open_ids = sorted(
        potential_ids - set(closed) - set(escalated)
    )
    expected = {
        "schema_version": 1,
        "draft_id": (
            f"CONCLUSION-DRAFT-"
            f"{stable_id(*sorted(potential_ids), length=16)}"
        ),
        "status": "unsigned_draft",
        "signature": None,
        "source_basis": "human_review_chain_only",
        "human_review_record_ids": [
            item["review_id"] for item in human_reviews
        ],
        "closed_with_explanation_ids": closed,
        "escalated_exception_ids": escalated,
        "open_exception_ids": open_ids,
        "statement": (
            f"Human review records close {len(closed)} item(s) with an "
            f"explanation, escalate {len(escalated)} item(s), and leave "
            f"{len(open_ids)} item(s) open. This draft is not an audit "
            "opinion or a control-effectiveness conclusion."
        ),
        "automated_audit_opinion": False,
        "human_sign_off_required": True,
        "review_record_origin": (
            "worked_demo_fixture_generated_by_demo_builder_not_"
            "authenticated_human_input"
        ),
    }
    if proposed is None:
        return expected
    if (
        proposed.get("status") != "unsigned_draft"
        or proposed.get("signature") is not None
    ):
        raise ValueError("bounded conclusion must remain unsigned")
    if canonical_json(proposed) != canonical_json(expected):
        raise ValueError(
            "stored conclusion does not match canonical human-review derivation"
        )
    return proposed


def _validate_provider_boundary(provider: DraftingProvider) -> None:
    if type(provider) is not FixtureDraftingProvider:
        raise ValueError(
            "provider is not authorized; v0.3 permits only the "
            "deterministic fixture provider"
        )
    if (
        provider.provider_id != "deterministic_fixture"
        or provider.provider_version != "1"
        or provider.external_model_used is not False
    ):
        raise ValueError("deterministic fixture provider metadata mismatch")


def run_bounded_workflow(
    output_dir: Path,
    *,
    provider: DraftingProvider | None = None,
) -> dict[str, Any]:
    provider = provider or FixtureDraftingProvider()
    _validate_provider_boundary(provider)
    if output_dir.exists() and any(output_dir.iterdir()):
        return _load_existing_workflow(
            output_dir,
            provider,
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    mandate = build_demo_mandate(repository_root())
    proposal = build_planning_proposal(mandate)
    freeze = freeze_plan(
        mandate,
        proposal,
        reviewer_id="audit-owner-demo",
        frozen_at_utc="2026-07-30T16:00:00Z",
    )
    deterministic_result = execute_frozen_plan(
        mandate,
        proposal,
        freeze,
        output_dir / "deterministic_run",
    )
    drafts, raw_exchange, metrics = _draft_investigations(
        deterministic_result["exceptions"],
        provider,
    )
    from .run_demo import seed_worked_reviews

    human_reviews = seed_worked_reviews(deterministic_result)
    conclusion = draft_bounded_conclusion(
        deterministic_result["exceptions"],
        human_reviews,
    )
    manifest = {
        "schema_version": 1,
        "workflow_id": (
            f"WORKFLOW-{stable_id(freeze['freeze_record_sha256'])}"
        ),
        "status": "demo_execution_complete_human_signoff_pending",
        "synthetic_only": True,
        "external_model_used": False,
        "provider_id": provider.provider_id,
        "human_directed": True,
        "external_agent_executed": False,
        "workflow_execution_mode": "deterministic_fixture_simulation",
        "evidence_bound": True,
        "deterministic_detection": True,
        "automated_audit_opinion": False,
        "execution_trace": [
            "mandate_created_by_human_fixture",
            "plan_proposed",
            "plan_frozen_by_human_fixture",
            "allowlisted_test_executed",
            "source_cited_investigation_drafted",
            "human_exception_records_applied",
            "unsigned_bounded_conclusion_drafted",
        ],
        "bindings": {
            "mandate_sha256": mandate["mandate_sha256"],
            "proposal_sha256": proposal["proposal_sha256"],
            "freeze_record_sha256": freeze["freeze_record_sha256"],
            "deterministic_run_id": (
                deterministic_result["run_manifest"]["run_id"]
            ),
            "deterministic_snapshot_id": (
                deterministic_result["run_manifest"]["snapshot_id"]
            ),
            "implementation_sha256": mandate["implementation_sha256"],
        },
        "control_metrics": metrics,
        "limitations": [
            "deterministic fixture provider; no external model run",
            "synthetic data only",
            (
                "worked human-review records are generated Demo fixtures "
                "with self-attested prototype identities"
            ),
            "no autonomous audit opinion or production action",
        ],
        "human_review_record_origin": (
            "worked_demo_fixture_generated_by_demo_builder_not_"
            "authenticated_human_input"
        ),
    }

    paths = {
        "human_audit_mandate.json": mandate,
        "planning_proposal.json": proposal,
        "human_freeze_record.json": freeze,
        "drafting_raw_exchange.json": raw_exchange,
        "investigation_drafts.json": drafts,
        "bounded_conclusion_draft.json": conclusion,
        "workflow_manifest.json": manifest,
    }
    for filename, value in paths.items():
        write_canonical_json(output_dir / filename, value)

    from .showcase import render_bounded_workflow_case

    html_path = output_dir / "index.html"
    result = {
        "output_dir": str(output_dir),
        "mandate": mandate,
        "planning_proposal": proposal,
        "human_freeze": freeze,
        "deterministic_result": deterministic_result,
        "investigation_drafts": drafts,
        "raw_exchange": raw_exchange,
        "drafting_control_metrics": metrics,
        "human_reviews": human_reviews,
        "conclusion_draft": conclusion,
        "workflow_manifest": manifest,
    }
    html_path.write_text(
        render_bounded_workflow_case(result),
        encoding="utf-8",
        newline="\n",
    )
    artifact_files = [
        output_dir / filename for filename in paths
    ] + [html_path]
    artifact_manifest = build_artifact_manifest(
        output_dir,
        artifact_files,
    )
    write_canonical_json(
        output_dir / "workflow_artifact_manifest.json",
        artifact_manifest,
    )
    result["workflow_artifact_manifest"] = artifact_manifest
    return result


def _load_existing_workflow(
    output_dir: Path,
    provider: DraftingProvider,
) -> dict[str, Any]:
    artifact_names = {
        "human_audit_mandate.json",
        "planning_proposal.json",
        "human_freeze_record.json",
        "drafting_raw_exchange.json",
        "investigation_drafts.json",
        "bounded_conclusion_draft.json",
        "workflow_manifest.json",
        "index.html",
    }
    required = artifact_names | {"workflow_artifact_manifest.json"}
    missing = sorted(
        name for name in required if not (output_dir / name).is_file()
    )
    if missing:
        raise RuntimeError(
            "existing workflow evidence pack is incomplete: "
            + ", ".join(missing)
        )
    artifact_manifest = json.loads(
        (output_dir / "workflow_artifact_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    verify_artifact_manifest(
        output_dir,
        artifact_manifest,
        required_artifacts=artifact_names,
    )
    mandate = json.loads(
        (output_dir / "human_audit_mandate.json").read_text(
            encoding="utf-8"
        )
    )
    proposal = json.loads(
        (output_dir / "planning_proposal.json").read_text(encoding="utf-8")
    )
    freeze = json.loads(
        (output_dir / "human_freeze_record.json").read_text(
            encoding="utf-8"
        )
    )
    deterministic_result = execute_frozen_plan(
        mandate,
        proposal,
        freeze,
        output_dir / "deterministic_run",
    )
    drafts = json.loads(
        (output_dir / "investigation_drafts.json").read_text(
            encoding="utf-8"
        )
    )
    exception_by_id = {
        item["exception_id"]: item
        for item in deterministic_result["exceptions"]
    }
    for draft in drafts:
        exception = exception_by_id.get(draft["exception_id"])
        if exception is None:
            raise ValueError("draft references an unknown exception")
        validate_investigation_draft(draft, exception)
    raw_exchange = json.loads(
        (output_dir / "drafting_raw_exchange.json").read_text(
            encoding="utf-8"
        )
    )
    provider_record = raw_exchange.get("provider", {})
    if (
        provider_record.get("provider_id") != provider.provider_id
        or provider_record.get("provider_version")
        != provider.provider_version
        or provider_record.get("external_model_used")
        != provider.external_model_used
    ):
        raise ValueError("existing workflow uses a different provider")
    drafts_by_exception = {
        item["exception_id"]: item for item in drafts
    }
    exchanges = raw_exchange.get("exchanges")
    if not isinstance(exchanges, list) or len(exchanges) != len(drafts):
        raise ValueError("raw exchange count does not match draft count")
    for exchange in exchanges:
        prompt = exchange.get("prompt")
        raw_output = exchange.get("raw_output")
        if (
            exchange.get("prompt_sha256")
            != sha256_bytes(canonical_json(prompt))
            or exchange.get("raw_output_sha256")
            != sha256_bytes(canonical_json(raw_output))
        ):
            raise ValueError("raw exchange hash mismatch")
        if canonical_json(provider.generate(prompt)) != canonical_json(
            raw_output
        ):
            raise ValueError("fixture replay does not match stored raw output")
        draft = drafts_by_exception.get(exchange.get("exception_id"))
        if draft is None:
            raise ValueError("raw exchange has no corresponding draft")
        if (
            draft.get("prompt_sha256")
            != exchange["prompt_sha256"]
            or draft.get("raw_output_sha256")
            != exchange["raw_output_sha256"]
        ):
            raise ValueError("draft is not bound to its raw exchange")
        for field in (
            "sentences",
            "investigation_questions",
            "unknowns",
        ):
            if canonical_json(draft.get(field)) != canonical_json(
                raw_output.get(field)
            ):
                raise ValueError(
                    "draft content does not match replayed raw output"
                )
    human_reviews = read_review_log(
        output_dir / "deterministic_run" / "review_log.jsonl"
    )
    conclusion = json.loads(
        (output_dir / "bounded_conclusion_draft.json").read_text(
            encoding="utf-8"
        )
    )
    draft_bounded_conclusion(
        deterministic_result["exceptions"],
        human_reviews,
        proposed=conclusion,
    )
    manifest = json.loads(
        (output_dir / "workflow_manifest.json").read_text(encoding="utf-8")
    )
    if manifest.get("provider_id") != provider.provider_id:
        raise ValueError("workflow manifest provider mismatch")
    if manifest.get("bindings") != {
        "mandate_sha256": mandate["mandate_sha256"],
        "proposal_sha256": proposal["proposal_sha256"],
        "freeze_record_sha256": freeze["freeze_record_sha256"],
        "deterministic_run_id": (
            deterministic_result["run_manifest"]["run_id"]
        ),
        "deterministic_snapshot_id": (
            deterministic_result["run_manifest"]["snapshot_id"]
        ),
        "implementation_sha256": mandate["implementation_sha256"],
    }:
        raise ValueError("workflow manifest binding mismatch")
    result = {
        "output_dir": str(output_dir),
        "mandate": mandate,
        "planning_proposal": proposal,
        "human_freeze": freeze,
        "deterministic_result": deterministic_result,
        "investigation_drafts": drafts,
        "raw_exchange": raw_exchange,
        "drafting_control_metrics": manifest["control_metrics"],
        "human_reviews": human_reviews,
        "conclusion_draft": conclusion,
        "workflow_manifest": manifest,
        "workflow_artifact_manifest": artifact_manifest,
    }
    from .showcase import render_bounded_workflow_case

    if (output_dir / "index.html").read_text(
        encoding="utf-8"
    ) != render_bounded_workflow_case(result):
        raise ValueError("committed workflow Demo does not match artifacts")
    return result
