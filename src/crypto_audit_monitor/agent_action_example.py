from __future__ import annotations

import csv
import io
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .harness import (
    APPROVED_CONCLUSIONS,
    assurance_profile,
    build_artifact_manifest,
    canonical_json,
    initialize_review_chain,
    load_registered_precommitment,
    sha256_bytes,
    sha256_file,
    stable_id,
    validate_evidence_contract,
    verify_artifact_manifest,
    verify_review_chain,
    verify_rule_override,
    write_canonical_json,
)
from .showcase import render_agent_action_case


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _payload_hash(action_type: str, target: str) -> str:
    return sha256_bytes(
        canonical_json({"action_type": action_type, "target": target})
    )


def _rows(
    inject_unknown_reversibility: bool,
    inject_unknown_action_type: bool,
    inject_invalid_timestamp: bool,
    inject_unknown_approval_decision: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    approved_payload = _payload_hash("external_write", "vendor-ledger/42")
    mismatched_payload = _payload_hash("external_write", "vendor-ledger/77")
    expired_payload = _payload_hash("irreversible_change", "policy/threshold")
    denied_payload = _payload_hash("irreversible_change", "access/grant")
    actions = [
        {
            "source_row_id": "ACTION-ACT-001",
            "action_id": "ACT-001",
            "agent_id": "AGENT-DEMO-1",
            "action_type": "read_only",
            "payload_sha256": _payload_hash("read_only", "ledger/report"),
            "reversibility": "reversible",
            "executed_at_utc": "2026-07-30T14:20:00Z",
            "approval_id": "",
        },
        {
            "source_row_id": "ACTION-ACT-002",
            "action_id": "ACT-002",
            "agent_id": "AGENT-DEMO-1",
            "action_type": "external_write",
            "payload_sha256": approved_payload,
            "reversibility": "irreversible",
            "executed_at_utc": "2026-07-30T14:25:00Z",
            "approval_id": "APR-001",
        },
        {
            "source_row_id": "ACTION-ACT-003",
            "action_id": "ACT-003",
            "agent_id": "AGENT-DEMO-2",
            "action_type": "external_write",
            "payload_sha256": _payload_hash(
                "external_write", "payment/batch-2026-07"
            ),
            "reversibility": "irreversible",
            "executed_at_utc": "2026-07-30T14:30:00Z",
            "approval_id": "",
        },
        {
            "source_row_id": "ACTION-ACT-004",
            "action_id": "ACT-004",
            "agent_id": "AGENT-DEMO-2",
            "action_type": "external_write",
            "payload_sha256": _payload_hash(
                "external_write", "vendor-ledger/88"
            ),
            "reversibility": "irreversible",
            "executed_at_utc": "2026-07-30T14:35:00Z",
            "approval_id": "APR-002",
        },
        {
            "source_row_id": "ACTION-ACT-005",
            "action_id": "ACT-005",
            "agent_id": "AGENT-DEMO-3",
            "action_type": "irreversible_change",
            "payload_sha256": expired_payload,
            "reversibility": "irreversible",
            "executed_at_utc": "2026-07-30T14:40:00Z",
            "approval_id": "APR-003",
        },
        {
            "source_row_id": "ACTION-ACT-006",
            "action_id": "ACT-006",
            "agent_id": "AGENT-DEMO-3",
            "action_type": "irreversible_change",
            "payload_sha256": denied_payload,
            "reversibility": "irreversible",
            "executed_at_utc": "2026-07-30T14:45:00Z",
            "approval_id": "APR-004",
        },
    ]
    if inject_unknown_reversibility:
        actions[0]["reversibility"] = "unknown"
    if inject_unknown_action_type:
        actions[0]["action_type"] = "unknown"
    if inject_invalid_timestamp:
        actions[0]["executed_at_utc"] = "30-07-2026 14:20"
    approvals = [
        {
            "source_row_id": "APPROVAL-APR-001",
            "approval_id": "APR-001",
            "decision": "approved",
            "approved_payload_sha256": approved_payload,
            "valid_from_utc": "2026-07-30T14:00:00Z",
            "valid_to_utc": "2026-07-30T15:00:00Z",
            "reviewer_id": "reviewer-demo-a",
        },
        {
            "source_row_id": "APPROVAL-APR-002",
            "approval_id": "APR-002",
            "decision": "approved",
            "approved_payload_sha256": mismatched_payload,
            "valid_from_utc": "2026-07-30T14:00:00Z",
            "valid_to_utc": "2026-07-30T15:00:00Z",
            "reviewer_id": "reviewer-demo-b",
        },
        {
            "source_row_id": "APPROVAL-APR-003",
            "approval_id": "APR-003",
            "decision": "approved",
            "approved_payload_sha256": expired_payload,
            "valid_from_utc": "2026-07-30T12:00:00Z",
            "valid_to_utc": "2026-07-30T13:00:00Z",
            "reviewer_id": "reviewer-demo-c",
        },
        {
            "source_row_id": "APPROVAL-APR-004",
            "approval_id": "APR-004",
            "decision": "denied",
            "approved_payload_sha256": denied_payload,
            "valid_from_utc": "2026-07-30T14:00:00Z",
            "valid_to_utc": "2026-07-30T15:00:00Z",
            "reviewer_id": "reviewer-demo-d",
        },
    ]
    if inject_unknown_approval_decision:
        approvals[0]["decision"] = "maybe"
    return actions, approvals


def _csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(
        handle,
        fieldnames=list(rows[0]),
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_csv_bytes(rows))


def _parse_utc(value: Any, field: str) -> datetime:
    try:
        text = str(value)
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be ISO-8601 UTC") from exc
    if (
        parsed.tzinfo is None
        or parsed.utcoffset() != timedelta(0)
        or not text.endswith("Z")
    ):
        raise ValueError(f"{field} must be ISO-8601 UTC")
    return parsed


def _validate_source_rows(
    actions: list[dict[str, Any]],
    approvals: list[dict[str, Any]],
) -> None:
    for action in actions:
        _parse_utc(action["executed_at_utc"], "executed_at_utc")
    allowed_decisions = {"approved", "denied"}
    for approval in approvals:
        if approval["decision"] not in allowed_decisions:
            raise ValueError("unknown approval decision")
        valid_from = _parse_utc(
            approval["valid_from_utc"],
            "valid_from_utc",
        )
        valid_to = _parse_utc(
            approval["valid_to_utc"],
            "valid_to_utc",
        )
        if valid_from >= valid_to:
            raise ValueError("approval validity window must increase")


AGENT_STATIC_ARTIFACTS = {
    "action_approvals.csv",
    "agent_actions.csv",
    "context_items.json",
    "exception_queue.json",
    "index.html",
    "run_manifest.json",
    "snapshot_manifest.json",
}


def _load_existing_agent_run(
    output_dir: Path,
    *,
    expected_run_id: str,
    expected_snapshot_id: str,
    expected_precommitment_hash: str,
    source_universe: set[str],
) -> dict[str, Any]:
    required_files = AGENT_STATIC_ARTIFACTS | {
        "evidence_pack_manifest.json",
        "review_chain_manifest.json",
        "review_log.jsonl",
    }
    missing = sorted(
        name for name in required_files if not (output_dir / name).is_file()
    )
    if missing:
        raise RuntimeError(
            "existing agent evidence pack is incomplete: "
            + ", ".join(missing)
        )
    run_manifest = json.loads(
        (output_dir / "run_manifest.json").read_text(encoding="utf-8")
    )
    if run_manifest.get("run_id") != expected_run_id:
        raise RuntimeError("existing agent evidence run_id mismatch")
    if run_manifest.get("snapshot_id") != expected_snapshot_id:
        raise RuntimeError("existing agent evidence snapshot mismatch")
    if (
        run_manifest.get("precommitment_sha256")
        != expected_precommitment_hash
    ):
        raise RuntimeError("existing agent precommitment mismatch")
    evidence_manifest = json.loads(
        (output_dir / "evidence_pack_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    verify_artifact_manifest(
        output_dir,
        evidence_manifest,
        required_artifacts=AGENT_STATIC_ARTIFACTS,
    )
    exceptions = json.loads(
        (output_dir / "exception_queue.json").read_text(encoding="utf-8")
    )
    context_items = json.loads(
        (output_dir / "context_items.json").read_text(encoding="utf-8")
    )
    validate_evidence_contract(
        run_manifest,
        exceptions + context_items,
        source_universe,
    )
    review_chain = verify_review_chain(
        output_dir / "review_log.jsonl",
        output_dir / "exception_queue.json",
    )
    return {
        "output_dir": str(output_dir),
        "run_manifest": run_manifest,
        "exceptions": exceptions,
        "context_items": context_items,
        "evidence_pack_manifest": evidence_manifest,
        "review_chain_manifest": review_chain,
    }


def _load_sqlite(
    db_path: Path,
    actions: list[dict[str, Any]],
    approvals: list[dict[str, Any]],
) -> None:
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE agent_action (
                source_row_id TEXT PRIMARY KEY,
                action_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                reversibility TEXT NOT NULL,
                executed_at_utc TEXT NOT NULL,
                approval_id TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE action_approval (
                source_row_id TEXT PRIMARY KEY,
                approval_id TEXT UNIQUE NOT NULL,
                decision TEXT NOT NULL,
                approved_payload_sha256 TEXT NOT NULL,
                valid_from_utc TEXT NOT NULL,
                valid_to_utc TEXT NOT NULL,
                reviewer_id TEXT NOT NULL
            )
            """
        )
        connection.executemany(
            """
            INSERT INTO agent_action VALUES (
                :source_row_id, :action_id, :agent_id, :action_type,
                :payload_sha256, :reversibility, :executed_at_utc, :approval_id
            )
            """,
            actions,
        )
        connection.executemany(
            """
            INSERT INTO action_approval VALUES (
                :source_row_id, :approval_id, :decision,
                :approved_payload_sha256, :valid_from_utc, :valid_to_utc,
                :reviewer_id
            )
            """,
            approvals,
        )
        connection.commit()
    finally:
        connection.close()


def _source_row_ids(
    action: dict[str, Any],
    approvals_by_id: dict[str, dict[str, Any]],
) -> list[str]:
    rows = [action["source_row_id"]]
    approval = approvals_by_id.get(action["approval_id"])
    if approval:
        rows.append(approval["source_row_id"])
    return rows


def run_agent_action_case(
    output_dir: Path,
    *,
    sql_path_override: Path | None = None,
    inject_unknown_reversibility: bool = False,
    inject_unknown_action_type: bool = False,
    inject_invalid_timestamp: bool = False,
    inject_unknown_approval_decision: bool = False,
) -> dict[str, Any]:
    root = repository_root()
    config_path = root / "config" / "agent_action_precommitment.json"
    config = load_registered_precommitment(
        root,
        "config/agent_action_precommitment.json",
    )
    sql_path = sql_path_override or root / config["rule"]["sql_file"]
    verify_rule_override(config, sql_path)

    actions, approvals = _rows(
        inject_unknown_reversibility,
        inject_unknown_action_type,
        inject_invalid_timestamp,
        inject_unknown_approval_decision,
    )
    allowed_reversibility = {"reversible", "irreversible"}
    unknown = sorted(
        {
            action["reversibility"]
            for action in actions
            if action["reversibility"] not in allowed_reversibility
        }
    )
    if unknown:
        raise ValueError(f"unknown reversibility value: {', '.join(unknown)}")
    allowed_action_types = {
        "read_only",
        "external_write",
        "irreversible_change",
    }
    unknown_action_types = sorted(
        {
            action["action_type"]
            for action in actions
            if action["action_type"] not in allowed_action_types
        }
    )
    if unknown_action_types:
        raise ValueError(
            "unknown action type: " + ", ".join(unknown_action_types)
        )
    _validate_source_rows(actions, approvals)

    action_bytes = _csv_bytes(actions)
    approval_bytes = _csv_bytes(approvals)
    snapshot_manifest = {
        "schema_version": 1,
        "synthetic_only": True,
        "tables": {
            "agent_action": {
                "file": "agent_actions.csv",
                "row_count": len(actions),
                "sha256": sha256_bytes(action_bytes),
            },
            "action_approval": {
                "file": "action_approvals.csv",
                "row_count": len(approvals),
                "sha256": sha256_bytes(approval_bytes),
            },
        },
    }
    snapshot_id = stable_id(
        canonical_json(snapshot_manifest).decode("utf-8"),
        length=24,
    )
    precommitment_hash = sha256_file(config_path)
    run_id = f"RUN-AI-{stable_id(snapshot_id, precommitment_hash, length=16)}"
    source_universe = {
        row["source_row_id"] for row in actions + approvals
    }
    if output_dir.exists() and any(output_dir.iterdir()):
        return _load_existing_agent_run(
            output_dir,
            expected_run_id=run_id,
            expected_snapshot_id=snapshot_id,
            expected_precommitment_hash=precommitment_hash,
            source_universe=source_universe,
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    action_path = output_dir / "agent_actions.csv"
    approval_path = output_dir / "action_approvals.csv"
    action_path.write_bytes(action_bytes)
    approval_path.write_bytes(approval_bytes)
    snapshot_path = output_dir / "snapshot_manifest.json"
    write_canonical_json(snapshot_path, snapshot_manifest)

    db_path = output_dir / "agent_actions.sqlite"
    _load_sqlite(db_path, actions, approvals)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        signal_rows = [
            dict(row)
            for row in connection.execute(
                sql_path.read_text(encoding="utf-8")
            ).fetchall()
        ]
    finally:
        connection.close()

    actions_by_id = {row["action_id"]: row for row in actions}
    approvals_by_id = {row["approval_id"]: row for row in approvals}
    exceptions: list[dict[str, Any]] = []
    for signal in signal_rows:
        action = actions_by_id[signal["action_id"]]
        exceptions.append(
            {
                "evidence_item_id": (
                    f"EVI-AI-{stable_id(run_id, action['action_id'])}"
                ),
                "exception_id": (
                    f"EX-AI-{stable_id(run_id, action['action_id'])}"
                ),
                "control_objective": config["control_objective_id"],
                "rule_version_id": config["rule"]["rule_version_id"],
                "run_id": run_id,
                "snapshot_id": snapshot_id,
                "source_row_ids": _source_row_ids(
                    action,
                    approvals_by_id,
                ),
                "signal_statement": (
                    "approval evidence is missing, not approved, not bound "
                    "to the exact payload, or not valid at execution time"
                ),
                "signal_code": signal["signal_code"],
                "review_status": "pending_human_review",
                "bucket": "potential_exception",
                "action_id": action["action_id"],
                "agent_id": action["agent_id"],
                "action_type": action["action_type"],
                "reversibility": action["reversibility"],
                "approval_id": action["approval_id"] or None,
                "detection_timestamp_utc": config["logical_run_at_utc"],
                "human_question": (
                    "Is there a valid approval artifact for the exact action "
                    "payload, or should this evidence item remain open?"
                ),
            }
        )

    context_items: list[dict[str, Any]] = []
    for action in actions:
        if action["action_id"] in {item["action_id"] for item in exceptions}:
            continue
        context_items.append(
            {
                "evidence_item_id": (
                    f"CTX-AI-{stable_id(run_id, action['action_id'])}"
                ),
                "control_objective": config["control_objective_id"],
                "rule_version_id": config["rule"]["rule_version_id"],
                "run_id": run_id,
                "snapshot_id": snapshot_id,
                "source_row_ids": _source_row_ids(
                    action,
                    approvals_by_id,
                ),
                "signal_statement": (
                    "reversible context retained"
                    if action["reversibility"] == "reversible"
                    else "exact approval evidence bound"
                ),
                "review_status": "context_only",
                "bucket": (
                    "context_only"
                    if action["reversibility"] == "reversible"
                    else "evidence_bound_context"
                ),
                "action_id": action["action_id"],
                "agent_id": action["agent_id"],
                "action_type": action["action_type"],
                "reversibility": action["reversibility"],
                "approval_id": action["approval_id"] or None,
            }
        )

    objective_conclusions = {
        config["control_objective_id"]: (
            "exceptions_identified"
            if exceptions
            else "no_exceptions_detected"
        )
    }
    lineage_rows = {
        source_row
        for item in exceptions + context_items
        for source_row in item["source_row_ids"]
    }
    gate_checks = {
        "G1_snapshot_integrity": (
            snapshot_manifest["tables"]["agent_action"]["sha256"]
            == sha256_file(action_path)
            and snapshot_manifest["tables"]["action_approval"]["sha256"]
            == sha256_file(approval_path)
        ),
        "G2_population_completeness": (
            len({row["action_id"] for row in actions}) == len(actions)
            and len({row["approval_id"] for row in approvals})
            == len(approvals)
        ),
        "G3_precommitment": (
            precommitment_hash == sha256_file(config_path)
            and bool(config["configuration_version_id"])
        ),
        "G4_rule_validation": (
            sha256_file(sql_path) == config["rule"]["sql_sha256"]
        ),
        "G5_traceability": lineage_rows <= source_universe,
        "G8_bounded_conclusions": (
            set(objective_conclusions.values()) <= APPROVED_CONCLUSIONS
        ),
    }
    failed_checks = sorted(
        name for name, passed in gate_checks.items() if not passed
    )
    if failed_checks:
        raise ValueError(
            "agent evidence gate failed: " + ", ".join(failed_checks)
        )
    gates = {
        name: "passed" for name in gate_checks
    }
    gates.update({
        "G6_append_only_review_contract": "requires_release_test",
        "G7_determinism": "requires_release_test",
    })
    gate_evidence = {
        "G1_snapshot_integrity": {
            "snapshot_manifest_sha256": sha256_file(snapshot_path),
            "source_files": [action_path.name, approval_path.name],
        },
        "G2_population_completeness": {
            "action_rows": len(actions),
            "approval_rows": len(approvals),
            "unique_action_ids": len(
                {row["action_id"] for row in actions}
            ),
            "unique_approval_ids": len(
                {row["approval_id"] for row in approvals}
            ),
        },
        "G3_precommitment": {
            "configuration_version_id": config["configuration_version_id"],
            "precommitment_sha256": precommitment_hash,
        },
        "G4_rule_validation": {
            "rule_version_id": config["rule"]["rule_version_id"],
            "sql_sha256": sha256_file(sql_path),
        },
        "G5_traceability": {
            "referenced_source_rows": len(lineage_rows),
            "source_universe_rows": len(source_universe),
        },
        "G8_bounded_conclusions": {
            "conclusions": objective_conclusions,
            "automated_action": "none",
            "human_decision": "required",
        },
    }
    run_manifest = {
        "schema_version": 1,
        "case_id": "synthetic-agent-action-assurance-v1",
        "case_type": "controlled_synthetic_trial",
        "run_id": run_id,
        "run_timestamp_utc": config["logical_run_at_utc"],
        "synthetic_only": True,
        "snapshot_id": snapshot_id,
        "snapshot_manifest_sha256": sha256_file(snapshot_path),
        "precommitment_sha256": precommitment_hash,
        "configuration_version_id": config["configuration_version_id"],
        "harness_version": config["harness_version"],
        "rule_versions": {
            "AI_ACTION": {
                "rule_version_id": config["rule"]["rule_version_id"],
                "sql_sha256": config["rule"]["sql_sha256"],
            }
        },
        "population": {
            "actions": len(actions),
            "approvals": len(approvals),
        },
        "routing_counts": {
            "potential_exceptions": len(exceptions),
            "context_items": len(context_items),
        },
        "objective_conclusions": objective_conclusions,
        "gates": gates,
        "gate_evidence": gate_evidence,
        "assurance_profile": assurance_profile(
            "L1_deterministic_recomputation"
        ),
        "human_decision": "required",
        "automated_action": "none",
        "ai_role": (
            "AI agent activity is the audited subject. No AI performs "
            "detection, classification or conclusion."
        ),
    }
    validate_evidence_contract(
        run_manifest,
        exceptions + context_items,
        source_universe,
    )
    exception_path = output_dir / "exception_queue.json"
    context_path = output_dir / "context_items.json"
    run_path = output_dir / "run_manifest.json"
    write_canonical_json(exception_path, exceptions)
    write_canonical_json(context_path, context_items)
    write_canonical_json(run_path, run_manifest)
    review_path = output_dir / "review_log.jsonl"
    initialize_review_chain(review_path)
    review_chain = verify_review_chain(review_path, exception_path)
    html_path = output_dir / "index.html"
    html_path.write_text(
        render_agent_action_case(
            run_manifest,
            exceptions,
            context_items,
        ),
        encoding="utf-8",
        newline="\n",
    )
    artifact_paths = [
        action_path,
        approval_path,
        snapshot_path,
        exception_path,
        context_path,
        run_path,
        html_path,
    ]
    evidence_manifest = build_artifact_manifest(
        output_dir,
        artifact_paths,
    )
    manifest_path = output_dir / "evidence_pack_manifest.json"
    write_canonical_json(manifest_path, evidence_manifest)
    return {
        "output_dir": str(output_dir),
        "run_manifest": run_manifest,
        "exceptions": exceptions,
        "context_items": context_items,
        "evidence_pack_manifest": evidence_manifest,
        "review_chain_manifest": review_chain,
    }
