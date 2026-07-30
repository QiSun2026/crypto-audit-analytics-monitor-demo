from __future__ import annotations

import json
from pathlib import Path

import pytest

from crypto_audit_monitor.agent_action_example import run_agent_action_case
from crypto_audit_monitor.engine import run_demo
from crypto_audit_monitor.harness import (
    append_review_record,
    load_registered_precommitment,
    sha256_file,
    validate_evidence_contract,
    verify_artifact_manifest,
    verify_review_chain,
)
from crypto_audit_monitor.showcase import (
    render_agent_action_case,
    render_showcase,
)


def test_existing_audit_case_passes_domain_neutral_contract(tmp_path: Path) -> None:
    result = run_demo(tmp_path / "audit")

    validate_evidence_contract(
        result["run_manifest"],
        result["exceptions"],
    )

    profile = result["run_manifest"]["assurance_profile"]
    assert profile["achieved_level"] == "L0_declaration_consistency"
    assert profile["target_level"] == "L1_deterministic_recomputation"
    assert profile["claim_status"] == "release_candidate"
    assert profile["pending_release_gates"] == [
        "G6_append_only_review_contract",
        "G7_determinism",
    ]
    assert profile["not_achieved"] == [
        "L2_source_authenticated",
        "L3_external_validation",
    ]


def test_agent_action_case_builds_hash_bound_evidence_pack(
    tmp_path: Path,
) -> None:
    result = run_agent_action_case(tmp_path / "agent")

    assert len(result["exceptions"]) == 4
    assert {item["signal_code"] for item in result["exceptions"]} == {
        "approval_evidence_missing",
        "approval_not_approved",
        "approval_payload_mismatch",
        "approval_outside_valid_window",
    }
    assert result["run_manifest"]["automated_action"] == "none"
    assert result["run_manifest"]["human_decision"] == "required"
    gates = result["run_manifest"]["gates"]
    assert {
        gates["G1_snapshot_integrity"],
        gates["G2_population_completeness"],
        gates["G3_precommitment"],
        gates["G4_rule_validation"],
        gates["G5_traceability"],
        gates["G8_bounded_conclusions"],
    } == {"passed"}
    assert gates["G6_append_only_review_contract"] == "requires_release_test"
    assert gates["G7_determinism"] == "requires_release_test"
    gate_evidence = result["run_manifest"]["gate_evidence"]
    assert set(gate_evidence) == {
        "G1_snapshot_integrity",
        "G2_population_completeness",
        "G3_precommitment",
        "G4_rule_validation",
        "G5_traceability",
        "G8_bounded_conclusions",
    }
    assert verify_artifact_manifest(
        tmp_path / "agent",
        result["evidence_pack_manifest"],
    )


def test_agent_action_case_is_byte_stable(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    run_agent_action_case(first)
    run_agent_action_case(second)

    for name in (
        "agent_actions.csv",
        "action_approvals.csv",
        "exception_queue.json",
        "run_manifest.json",
        "snapshot_manifest.json",
        "evidence_pack_manifest.json",
        "index.html",
    ):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_agent_action_rule_change_without_precommitment_is_blocked(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[1]
    changed_sql = tmp_path / "changed.sql"
    changed_sql.write_text(
        (root / "sql" / "rule_c_agent_action_approval.sql").read_text(
            encoding="utf-8"
        )
        + "\n-- unregistered change\n",
        encoding="utf-8",
        newline="\n",
    )

    with pytest.raises(ValueError, match="SQL hash mismatch"):
        run_agent_action_case(
            tmp_path / "blocked",
            sql_path_override=changed_sql,
        )


def test_unknown_agent_action_reversibility_fails_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="unknown reversibility"):
        run_agent_action_case(
            tmp_path / "blocked",
            inject_unknown_reversibility=True,
        )


def test_unknown_agent_action_type_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown action type"):
        run_agent_action_case(
            tmp_path / "blocked",
            inject_unknown_action_type=True,
        )


def test_invalid_agent_timestamp_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must be ISO-8601 UTC"):
        run_agent_action_case(
            tmp_path / "blocked",
            inject_invalid_timestamp=True,
        )


def test_unknown_approval_decision_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown approval decision"):
        run_agent_action_case(
            tmp_path / "blocked",
            inject_unknown_approval_decision=True,
        )


def test_reversible_agent_action_remains_visible_context(
    tmp_path: Path,
) -> None:
    result = run_agent_action_case(tmp_path / "agent")

    reversible = [
        item
        for item in result["context_items"]
        if item["reversibility"] == "reversible"
    ]
    assert len(reversible) == 1
    assert reversible[0]["bucket"] == "context_only"


def test_exactly_approved_irreversible_action_remains_visible_context(
    tmp_path: Path,
) -> None:
    result = run_agent_action_case(tmp_path / "agent")

    approved = [
        item
        for item in result["context_items"]
        if item["action_id"] == "ACT-002"
    ]
    assert len(approved) == 1
    assert approved[0]["bucket"] == "evidence_bound_context"
    assert approved[0]["signal_statement"] == "exact approval evidence bound"


def test_artifact_tampering_is_detected(tmp_path: Path) -> None:
    output_dir = tmp_path / "agent"
    result = run_agent_action_case(output_dir)
    (output_dir / "exception_queue.json").write_text(
        "tampered",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="artifact hash mismatch"):
        verify_artifact_manifest(
            output_dir,
            result["evidence_pack_manifest"],
        )
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        run_agent_action_case(output_dir)


def test_agent_action_review_chain_supports_append_only_review(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "agent"
    result = run_agent_action_case(output_dir)
    exception = result["exceptions"][0]
    review = append_review_record(
        output_dir / "review_log.jsonl",
        {
            "exception_id": exception["exception_id"],
            "run_id": exception["run_id"],
            "snapshot_id": exception["snapshot_id"],
            "reviewer_id": "reviewer-demo",
            "review_timestamp_utc": "2026-07-30T16:00:00Z",
            "question_presented": exception["human_question"],
            "conclusion": "more_evidence_required",
            "disposition": "keep_open",
            "rationale": "The fabricated approval evidence remains open.",
            "evidence_viewed": exception["source_row_ids"],
            "identity_status": "self_attested_prototype",
            "ai_assistance_used": False,
        },
        output_dir / "exception_queue.json",
    )

    assert review["previous_record_sha256"] == "0" * 64
    chain = verify_review_chain(
        output_dir / "review_log.jsonl",
        output_dir / "exception_queue.json",
    )
    assert chain["record_count"] == 1


def test_agent_action_partial_existing_pack_is_not_overwritten(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "agent"
    output_dir.mkdir()
    sentinel = output_dir / "sentinel.txt"
    sentinel.write_text("preserve", encoding="utf-8")

    with pytest.raises(RuntimeError, match="incomplete"):
        run_agent_action_case(output_dir)
    assert sentinel.read_text(encoding="utf-8") == "preserve"


def test_failed_runtime_gate_blocks_evidence_contract(
    tmp_path: Path,
) -> None:
    result = run_agent_action_case(tmp_path / "agent")
    result["run_manifest"]["gates"]["G4_rule_validation"] = "failed"

    with pytest.raises(ValueError, match="runtime evidence gate"):
        validate_evidence_contract(
            result["run_manifest"],
            result["exceptions"],
        )


def test_late_precommitment_is_rejected(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    changed = json.loads(
        (root / "config" / "agent_action_precommitment.json").read_text(
            encoding="utf-8"
        )
    )
    changed["configuration_version_id"] = "late-policy-v1"
    changed["committed_at_utc"] = changed["logical_run_at_utc"]

    config_dir = tmp_path / "config"
    sql_dir = tmp_path / "sql"
    config_dir.mkdir()
    sql_dir.mkdir()
    sql_name = Path(changed["rule"]["sql_file"]).name
    sql_copy = sql_dir / sql_name
    sql_copy.write_bytes(
        (root / changed["rule"]["sql_file"]).read_bytes()
    )
    changed["rule"]["sql_file"] = f"sql/{sql_name}"
    changed_path = config_dir / "late.json"
    changed_path.write_text(
        json.dumps(changed, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (config_dir / "precommitment_registry.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "configurations": {
                    "late-policy-v1": sha256_file(changed_path),
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    with pytest.raises(ValueError, match="must predate"):
        load_registered_precommitment(tmp_path, "config/late.json")


def test_agent_action_copy_stays_bounded(tmp_path: Path) -> None:
    result = run_agent_action_case(tmp_path / "agent")
    visible = json.dumps(
        {
            "manifest": result["run_manifest"],
            "exceptions": result["exceptions"],
            "html": (tmp_path / "agent" / "index.html").read_text(
                encoding="utf-8"
            ),
        },
        ensure_ascii=False,
    ).lower()

    for prohibited in (
        "fraud committed",
        "misconduct confirmed",
        "unauthorized actor",
        "control effective",
    ):
        assert prohibited not in visible
    assert "0 human review records" in visible
    assert "no disposition recorded" in visible
    assert "does not test approval uniqueness" in visible
    assert "0 条人工复核记录" in visible
    assert "approval does not match the action" in visible
    assert "批准内容与实际操作不一致" in visible
    assert "what happened:" in visible
    assert "发生了什么：" in visible
    assert "next check:" in visible
    assert "下一步核验：" in visible


def test_showcase_is_bilingual_and_links_both_cases() -> None:
    html = render_showcase()

    assert "One product. Two cases. One shared method." in html
    assert "一个产品，两个案例，同一套方法。" in html
    assert "Wallet and commission review" in html
    assert "钱包与佣金复核" in html
    assert "Agent action approval review" in html
    assert "Agent 行为批准复核" in html
    assert "The workflow view belongs to Case 1" in html
    assert "工作流视图属于案例 1" in html
    assert "commission_case.html" in html
    assert "agent_action_case.html" in html
    assert "bounded_workflow_case.html" in html
    assert "RiskFirewall AI — Risk Control Assurance" in html
    assert "Transactions, Processes &amp; AI Actions · Third Line" in html
    assert "交易、流程与 AI 行为 · 第三道防线" in html
    assert "not full Operational Risk or AML coverage" in html
    assert "不声称覆盖完整的操作风险或反洗钱职能" in html


def test_committed_showcase_and_agent_case_match_fresh_render(
    tmp_path: Path,
) -> None:
    root = Path(__file__).resolve().parents[1]
    result = run_agent_action_case(tmp_path / "agent")

    assert (root / "demo" / "index.html").read_text(
        encoding="utf-8"
    ) == render_showcase()
    assert (root / "demo" / "agent_action_case.html").read_text(
        encoding="utf-8"
    ) == render_agent_action_case(
        result["run_manifest"],
        result["exceptions"],
        result["context_items"],
        back_href="index.html",
    )
