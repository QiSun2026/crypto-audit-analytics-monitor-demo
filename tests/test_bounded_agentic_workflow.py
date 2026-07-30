from __future__ import annotations

import json
from pathlib import Path

import pytest

from crypto_audit_monitor.bounded_agentic import (
    FixtureDraftingProvider,
    build_demo_mandate,
    build_planning_proposal,
    draft_bounded_conclusion,
    execute_frozen_plan,
    freeze_plan,
    repository_root,
    run_bounded_workflow,
    validate_investigation_draft,
)
from crypto_audit_monitor.harness import canonical_json, sha256_bytes
from crypto_audit_monitor.integrity import sha256_file
from crypto_audit_monitor.showcase import (
    render_bounded_workflow_case,
    render_showcase,
)


class StateChangingProvider:
    provider_id = "malicious-fixture"
    provider_version = "1"
    external_model_used = False

    def generate(self, prompt: dict) -> dict:
        return {
            "sentences": [
                {
                    "text": "Close the exception.",
                    "source_row_ids": prompt["allowed_source_row_ids"],
                }
            ],
            "investigation_questions": [],
            "unknowns": [],
            "disposition": "close_with_explanation",
        }


class UncitedProvider:
    provider_id = "uncited-fixture"
    provider_version = "1"
    external_model_used = False

    def generate(self, prompt: dict) -> dict:
        return {
            "sentences": [
                {
                    "text": "This statement has no source row.",
                    "source_row_ids": [],
                }
            ],
            "investigation_questions": [],
            "unknowns": [],
        }


class NoIssueProvider:
    provider_id = "no-issue-fixture"
    provider_version = "1"
    external_model_used = False

    def generate(self, prompt: dict) -> dict:
        return {
            "sentences": [
                {
                    "text": "There is no issue.",
                    "source_row_ids": prompt["allowed_source_row_ids"],
                }
            ],
            "investigation_questions": [],
            "unknowns": [],
        }


class UnauthorizedExternalProvider(NoIssueProvider):
    provider_id = "external-provider"
    external_model_used = True


def _frozen_demo() -> tuple[dict, dict, dict]:
    mandate = build_demo_mandate(repository_root())
    proposal = build_planning_proposal(mandate)
    freeze = freeze_plan(
        mandate,
        proposal,
        reviewer_id="audit-owner-demo",
        frozen_at_utc="2026-07-30T16:00:00Z",
    )
    return mandate, proposal, freeze


def _rehash(record: dict, field: str) -> None:
    payload = dict(record)
    payload.pop(field, None)
    record[field] = sha256_bytes(canonical_json(payload))


def _draft_fixture(
    text: str,
    source_rows: list[str],
    **extra: object,
) -> tuple[dict, dict]:
    exception = {
        "exception_id": "EX-1",
        "source_row_ids": ["ROW-1"],
    }
    draft = {
        "exception_id": "EX-1",
        "status": "draft_for_human_review",
        "allowed_source_row_ids": ["ROW-1"],
        "sentences": [
            {
                "text": text,
                "source_row_ids": source_rows,
            }
        ],
        "investigation_questions": [],
        "unknowns": [
            {
                "text": "Intent remains unknown.",
                "source_row_ids": ["ROW-1"],
            }
        ],
        "state_changes": [],
        **extra,
    }
    return draft, exception


def test_human_mandate_binds_scope_thresholds_and_prohibitions() -> None:
    mandate = build_demo_mandate(repository_root())

    assert mandate["authority"] == "human_directed"
    assert mandate["synthetic_only"] is True
    assert mandate["thresholds"] == {
        "review_threshold_minor": 1_000_000,
        "window_days_inclusive": 7,
    }
    assert mandate["allowed_test_ids"] == [
        "commission_full_population_v4"
    ]
    assert len(mandate["implementation_sha256"]) == 64
    assert {
        "agent_must_not_change_scope",
        "agent_must_not_change_thresholds",
        "agent_must_not_close_exceptions",
        "agent_must_not_sign_conclusions",
    } <= set(mandate["prohibitions"])
    assert len(mandate["mandate_sha256"]) == 64


def test_plan_requires_exact_human_freeze_before_execution(
    tmp_path: Path,
) -> None:
    mandate = build_demo_mandate(repository_root())
    proposal = build_planning_proposal(mandate)

    with pytest.raises(ValueError, match="human freeze"):
        execute_frozen_plan(
            mandate,
            proposal,
            {},
            tmp_path / "run",
        )

    freeze = freeze_plan(
        mandate,
        proposal,
        reviewer_id="audit-owner-demo",
        frozen_at_utc="2026-07-30T16:00:00Z",
    )
    result = execute_frozen_plan(
        mandate,
        proposal,
        freeze,
        tmp_path / "run",
    )
    assert result["run_manifest"]["configuration_version_id"] == (
        "audit-policy-v4"
    )


def test_threshold_change_after_freeze_fails_closed(
    tmp_path: Path,
) -> None:
    mandate, proposal, freeze = _frozen_demo()
    mandate["thresholds"]["review_threshold_minor"] += 1

    with pytest.raises(ValueError, match="mandate hash mismatch"):
        execute_frozen_plan(
            mandate,
            proposal,
            freeze,
            tmp_path / "blocked",
        )


def test_unallowlisted_test_cannot_be_frozen() -> None:
    mandate = build_demo_mandate(repository_root())
    proposal = build_planning_proposal(mandate)
    proposal["procedure_calls"][0]["test_id"] = "dynamic_unreviewed_sql"
    _rehash(proposal, "proposal_sha256")

    with pytest.raises(ValueError, match="not allowlisted"):
        freeze_plan(
            mandate,
            proposal,
            reviewer_id="audit-owner-demo",
            frozen_at_utc="2026-07-30T16:00:00Z",
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("created_by", "", "identity fields"),
        ("created_at_utc", "not-a-time", "UTC timestamp"),
        ("identity_status", "authenticated", "identity status"),
    ],
)
def test_rehashed_mandate_cannot_weaken_human_identity_semantics(
    field: str,
    value: str,
    message: str,
) -> None:
    mandate = build_demo_mandate(repository_root())
    mandate[field] = value
    _rehash(mandate, "mandate_sha256")

    with pytest.raises(ValueError, match=message):
        build_planning_proposal(mandate)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("proposal_origin", "external_agent", "origin"),
        ("external_model_used", True, "external model"),
        ("post_execution_steps", ["sign_conclusion"], "post-execution"),
    ],
)
def test_rehashed_proposal_cannot_expand_automation_authority(
    field: str,
    value: object,
    message: str,
) -> None:
    mandate = build_demo_mandate(repository_root())
    proposal = build_planning_proposal(mandate)
    proposal[field] = value
    _rehash(proposal, "proposal_sha256")

    with pytest.raises(ValueError, match=message):
        freeze_plan(
            mandate,
            proposal,
            reviewer_id="audit-owner-demo",
            frozen_at_utc="2026-07-30T16:00:00Z",
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("reviewer_id", "", "reviewer_id"),
        ("frozen_at_utc", "not-a-time", "UTC timestamp"),
        (
            "frozen_at_utc",
            "2026-07-30T15:00:00Z",
            "cannot predate",
        ),
        ("identity_status", "authenticated", "identity status"),
    ],
)
def test_rehashed_freeze_cannot_weaken_human_checkpoint(
    tmp_path: Path,
    field: str,
    value: str,
    message: str,
) -> None:
    mandate, proposal, freeze = _frozen_demo()
    freeze[field] = value
    _rehash(freeze, "freeze_record_sha256")

    with pytest.raises(ValueError, match=message):
        execute_frozen_plan(
            mandate,
            proposal,
            freeze,
            tmp_path / "blocked",
        )


def test_investigation_drafts_are_fully_cited_and_state_neutral(
    tmp_path: Path,
) -> None:
    result = run_bounded_workflow(tmp_path / "workflow")

    assert result["workflow_manifest"]["status"] == (
        "demo_execution_complete_human_signoff_pending"
    )
    assert result["workflow_manifest"]["external_agent_executed"] is False
    assert result["workflow_manifest"]["workflow_execution_mode"] == (
        "deterministic_fixture_simulation"
    )
    for draft in result["investigation_drafts"]:
        allowed = set(draft["allowed_source_row_ids"])
        assert draft["status"] == "draft_for_human_review"
        assert draft["state_changes"] == []
        assert draft["sentences"]
        for sentence in draft["sentences"]:
            assert sentence["source_row_ids"]
            assert set(sentence["source_row_ids"]) <= allowed
    assert result["drafting_control_metrics"] == {
        "drafted_exceptions": 6,
        "sentences": 6,
        "cited_sentences": 6,
        "citation_coverage_percent": 100.0,
        "unauthorized_state_mutations": 0,
    }


def test_provider_cannot_close_or_reclassify_exception(
    tmp_path: Path,
) -> None:
    draft, exception = _draft_fixture(
        "The cited pattern requires review.",
        ["ROW-1"],
        disposition="close_with_explanation",
    )
    with pytest.raises(ValueError, match="prohibited output field"):
        validate_investigation_draft(draft, exception)


def test_uncited_provider_statement_is_blocked(tmp_path: Path) -> None:
    draft, exception = _draft_fixture(
        "This statement has no source row.",
        [],
    )
    with pytest.raises(ValueError, match="claim-level citation"):
        validate_investigation_draft(draft, exception)


def test_missing_evidence_cannot_be_drafted_as_no_issue(
    tmp_path: Path,
) -> None:
    draft, exception = _draft_fixture(
        "There is no issue.",
        ["ROW-1"],
    )
    with pytest.raises(ValueError, match="bounded conclusion"):
        validate_investigation_draft(draft, exception)


def test_external_model_provider_requires_new_authorization(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="not authorized"):
        run_bounded_workflow(
            tmp_path / "blocked",
            provider=UnauthorizedExternalProvider(),
        )


def test_raw_provider_exchange_is_preserved(tmp_path: Path) -> None:
    output_dir = tmp_path / "workflow"
    result = run_bounded_workflow(
        output_dir,
        provider=FixtureDraftingProvider(),
    )

    raw = json.loads(
        (output_dir / "drafting_raw_exchange.json").read_text(
            encoding="utf-8"
        )
    )
    assert raw["provider"] == {
        "provider_id": "deterministic_fixture",
        "provider_version": "1",
        "external_model_used": False,
    }
    assert len(raw["exchanges"]) == len(result["investigation_drafts"])
    assert all("prompt" in item and "raw_output" in item for item in raw["exchanges"])


def test_conclusion_draft_uses_human_records_only_and_cannot_sign(
    tmp_path: Path,
) -> None:
    result = run_bounded_workflow(tmp_path / "workflow")
    conclusion = result["conclusion_draft"]

    assert conclusion["status"] == "unsigned_draft"
    assert conclusion["signature"] is None
    assert conclusion["source_basis"] == "human_review_chain_only"
    assert conclusion["human_review_record_ids"]
    assert conclusion["open_exception_ids"]
    assert conclusion["automated_audit_opinion"] is False

    changed = dict(conclusion)
    changed["signature"] = "agent"
    with pytest.raises(ValueError, match="must remain unsigned"):
        draft_bounded_conclusion(
            result["deterministic_result"]["exceptions"],
            result["human_reviews"],
            proposed=changed,
        )

    forged = dict(conclusion)
    forged["closed_with_explanation_ids"] = sorted(
        item["exception_id"]
        for item in result["deterministic_result"]["exceptions"]
        if item["bucket"] == "potential_exception"
    )
    forged["open_exception_ids"] = []
    with pytest.raises(ValueError, match="canonical human-review derivation"):
        draft_bounded_conclusion(
            result["deterministic_result"]["exceptions"],
            result["human_reviews"],
            proposed=forged,
        )


def test_conclusion_draft_rejects_unlinked_review_override(
    tmp_path: Path,
) -> None:
    result = run_bounded_workflow(tmp_path / "workflow")
    reviews = list(result["human_reviews"])
    current = reviews[-1]
    unlinked = dict(current)
    unlinked.update(
        {
            "review_id": "REV-unlinked-override",
            "supersedes_review_id": None,
            "disposition": "close_with_explanation",
        }
    )

    with pytest.raises(ValueError, match="supersede"):
        draft_bounded_conclusion(
            result["deterministic_result"]["exceptions"],
            [*reviews, unlinked],
        )


def test_draft_validator_rejects_rows_outside_exception_lineage() -> None:
    exception = {
        "exception_id": "EX-1",
        "source_row_ids": ["ROW-1"],
    }
    draft = {
        "exception_id": "EX-1",
        "status": "draft_for_human_review",
        "allowed_source_row_ids": ["ROW-1"],
        "sentences": [
            {
                "text": "Unsupported source.",
                "source_row_ids": ["ROW-2"],
            }
        ],
        "investigation_questions": [],
        "unknowns": [],
        "state_changes": [],
    }
    with pytest.raises(ValueError, match="outside exception lineage"):
        validate_investigation_draft(draft, exception)


def test_workflow_artifacts_are_byte_stable(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    run_bounded_workflow(first)
    run_bounded_workflow(second)

    for name in (
        "human_audit_mandate.json",
        "planning_proposal.json",
        "human_freeze_record.json",
        "drafting_raw_exchange.json",
        "investigation_drafts.json",
        "bounded_conclusion_draft.json",
        "workflow_manifest.json",
        "index.html",
    ):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_existing_workflow_is_verified_and_tampering_blocks_reuse(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "workflow"
    first = run_bounded_workflow(output_dir)
    second = run_bounded_workflow(output_dir)
    assert (
        second["workflow_manifest"]["workflow_id"]
        == first["workflow_manifest"]["workflow_id"]
    )

    mandate_path = output_dir / "human_audit_mandate.json"
    mandate = json.loads(mandate_path.read_text(encoding="utf-8"))
    mandate["thresholds"]["review_threshold_minor"] += 1
    mandate_path.write_text(json.dumps(mandate), encoding="utf-8")
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        run_bounded_workflow(output_dir)


def test_draft_content_must_match_replayed_raw_output(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "workflow"
    run_bounded_workflow(output_dir)

    draft_path = output_dir / "investigation_drafts.json"
    drafts = json.loads(draft_path.read_text(encoding="utf-8"))
    drafts[0]["sentences"][0]["text"] = (
        "Changed while retaining the original raw-output hash."
    )
    draft_path.write_text(
        json.dumps(drafts, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    manifest_path = output_dir / "workflow_artifact_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"]["investigation_drafts.json"] = sha256_file(
        draft_path
    )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="draft content does not match replayed raw output",
    ):
        run_bounded_workflow(output_dir)


def test_bounded_workflow_demo_is_bilingual_and_not_a_third_domain(
    tmp_path: Path,
) -> None:
    result = run_bounded_workflow(tmp_path / "workflow")
    html = render_bounded_workflow_case(result)
    landing = render_showcase()

    assert "Human-directed, workflow-executed" in html
    assert "人工定向、工作流执行" in html
    assert "Fixture provider — no external model" in html
    assert "未调用外部模型" in html
    assert "The workflow view belongs to Case 1" in landing
    assert "工作流视图属于案例 1" in landing
    assert "bounded_workflow_case.html" in landing


def test_committed_workflow_demo_matches_fresh_render(tmp_path: Path) -> None:
    root = repository_root()
    result = run_bounded_workflow(tmp_path / "workflow")

    assert (root / "demo" / "bounded_workflow_case.html").read_text(
        encoding="utf-8"
    ) == render_bounded_workflow_case(result)
