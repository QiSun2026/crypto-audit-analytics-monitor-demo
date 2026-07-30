from __future__ import annotations

from typing import Any, Iterable


APPROVED_CONCLUSIONS = {
    "no_exceptions_detected",
    "exceptions_identified",
    "not_testable",
}

REQUIRED_EVIDENCE_FIELDS = {
    "control_objective",
    "rule_version_id",
    "run_id",
    "snapshot_id",
    "source_row_ids",
    "signal_statement",
    "review_status",
    "bucket",
}

RUNTIME_GATES = {
    "G1_snapshot_integrity",
    "G2_population_completeness",
    "G3_precommitment",
    "G4_rule_validation",
    "G5_traceability",
    "G8_bounded_conclusions",
}


def assurance_profile(level: str) -> dict[str, Any]:
    if level != "L1_deterministic_recomputation":
        raise ValueError("unsupported assurance level")
    return {
        "profile_version": "evidence-assurance-v0.1",
        "achieved_level": "L0_declaration_consistency",
        "target_level": level,
        "claim_status": "release_candidate",
        "pending_release_gates": [
            "G6_append_only_review_contract",
            "G7_determinism",
        ],
        "not_achieved": [
            "L2_source_authenticated",
            "L3_external_validation",
        ],
        "non_compensating": True,
        "note": (
            "The evidence pack is an L1 release candidate on fabricated, "
            "hash-bound inputs. G6 and G7 remain release-harness checks; no "
            "source authentication or independent external validation."
        ),
    }


def validate_evidence_contract(
    run_manifest: dict[str, Any],
    evidence_items: Iterable[dict[str, Any]],
    source_row_universe: set[str] | None = None,
) -> None:
    if run_manifest.get("human_decision") != "required":
        raise ValueError("human decision boundary is missing")
    if run_manifest.get("automated_action") != "none":
        raise ValueError("automated action is outside the harness boundary")
    if set(run_manifest.get("objective_conclusions", {}).values()) - (
        APPROVED_CONCLUSIONS
    ):
        raise ValueError("unbounded objective conclusion")
    if "assurance_profile" not in run_manifest:
        raise ValueError("assurance profile is missing")
    gates = run_manifest.get("gates", {})
    failed_gates = sorted(
        gate for gate in RUNTIME_GATES if gates.get(gate) != "passed"
    )
    if failed_gates:
        raise ValueError(
            "runtime evidence gate is not passed: "
            + ", ".join(failed_gates)
        )

    seen: set[str] = set()
    for item in evidence_items:
        missing = sorted(REQUIRED_EVIDENCE_FIELDS - set(item))
        if missing:
            raise ValueError(
                f"evidence item is missing fields: {', '.join(missing)}"
            )
        item_id = item.get("evidence_item_id") or item.get("exception_id")
        if not item_id:
            raise ValueError("evidence item identifier is missing")
        if item_id in seen:
            raise ValueError("duplicate evidence item id")
        seen.add(item_id)
        if item["run_id"] != run_manifest["run_id"]:
            raise ValueError("evidence item run_id mismatch")
        if item["snapshot_id"] != run_manifest["snapshot_id"]:
            raise ValueError("evidence item snapshot_id mismatch")
        source_rows = item["source_row_ids"]
        if not isinstance(source_rows, list) or not source_rows:
            raise ValueError("evidence item requires source-row lineage")
        if source_row_universe is not None and not set(source_rows) <= (
            source_row_universe
        ):
            raise ValueError("evidence item references an unknown source row")
