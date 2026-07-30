from __future__ import annotations

import csv
import json
import random
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from .generator import generate_snapshot, load_snapshot_to_sqlite
from .harness import (
    APPROVED_CONCLUSIONS,
    assurance_profile,
    build_artifact_manifest,
    load_registered_precommitment,
    validate_evidence_contract,
    verify_artifact_manifest,
)
from .integrity import canonical_json, sha256_file, stable_id, write_canonical_json
from .renderer import render_html
from .review_log import initialize_review_chain, verify_review_chain

def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


COMMISSION_STATIC_ARTIFACTS = {
    "exception_queue.json",
    "exception_queue.csv",
    "run_manifest.json",
    "sample_comparison.json",
    "review_record_template.json",
    "index.html",
    "snapshot_manifest.json",
    "ground_truth.json",
}


def load_precommitment(root: Path) -> dict[str, Any]:
    return load_registered_precommitment(
        root,
        "config/rule_precommitment.json",
    )


def verify_snapshot(output_dir: Path) -> dict[str, Any]:
    manifest_path = output_dir / "snapshot_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for table, details in manifest["tables"].items():
        path = output_dir / details["file"]
        if sha256_file(path) != details["sha256"]:
            raise ValueError(f"snapshot hash mismatch: {table}")
        with path.open("r", encoding="utf-8", newline="") as handle:
            row_count = sum(1 for _ in csv.DictReader(handle))
        if row_count != details["row_count"]:
            raise ValueError(f"snapshot row count mismatch: {table}")
    fixture = manifest.get("validation_fixture", {})
    fixture_path = output_dir / fixture.get("file", "")
    if not fixture.get("sha256") or not fixture_path.is_file():
        raise ValueError("validation fixture is not bound to the snapshot")
    if sha256_file(fixture_path) != fixture["sha256"]:
        raise ValueError("validation fixture hash mismatch")

    with (output_dir / "source_data" / "commission_payment.csv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        payments = list(csv.DictReader(handle))
    with (output_dir / "source_data" / "payout_wallet.csv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        wallets = list(csv.DictReader(handle))
    actual_totals = {
        "commission_amount_minor": sum(int(row["amount_minor"]) for row in payments),
        "distinct_wallets": len({row["wallet_id"] for row in wallets}),
        "distinct_affiliates": manifest["tables"]["affiliate"]["row_count"],
    }
    if actual_totals != manifest["control_totals"]:
        raise ValueError("snapshot control totals do not reconcile")
    return manifest


def validate_data_quality(db_path: Path) -> dict[str, int]:
    checks = {
        "unknown_wallet_type": """
            SELECT COUNT(*) FROM payout_wallet
            WHERE wallet_type NOT IN (
                'self_custody', 'exchange_deposit', 'internal_treasury'
            )
        """,
        "invalid_entity_type": """
            SELECT COUNT(*) FROM entity_wallet_link
            WHERE entity_type NOT IN ('employee', 'affiliate')
        """,
        "orphan_wallet_link": """
            SELECT COUNT(*) FROM entity_wallet_link l
            LEFT JOIN payout_wallet w ON w.wallet_id = l.wallet_id
            WHERE w.wallet_id IS NULL
        """,
        "orphan_entity_link": """
            SELECT COUNT(*) FROM entity_wallet_link l
            LEFT JOIN employee e
              ON l.entity_type = 'employee' AND e.employee_id = l.entity_id
            LEFT JOIN affiliate a
              ON l.entity_type = 'affiliate' AND a.affiliate_id = l.entity_id
            WHERE (l.entity_type = 'employee' AND e.employee_id IS NULL)
               OR (l.entity_type = 'affiliate' AND a.affiliate_id IS NULL)
        """,
        "invalid_link_dates": """
            SELECT COUNT(*) FROM entity_wallet_link
            WHERE date(valid_from) IS NULL
               OR (
                   valid_to IS NOT NULL
                   AND (
                       date(valid_to) IS NULL
                       OR date(valid_to) < date(valid_from)
                   )
               )
        """,
        "invalid_affiliate_status": """
            SELECT COUNT(*) FROM affiliate
            WHERE status NOT IN ('active', 'inactive')
        """,
        "invalid_payment_domain": """
            SELECT COUNT(*) FROM commission_payment p
            LEFT JOIN affiliate a ON a.affiliate_id = p.affiliate_id
            WHERE a.affiliate_id IS NULL
               OR p.amount_minor <= 0
               OR TRIM(p.source_ref) = ''
               OR date(p.payment_date) IS NULL
               OR p.payment_status NOT IN ('completed', 'reversed')
        """,
        "duplicate_wallet_address_hash": """
            SELECT COUNT(*) FROM (
                SELECT address_hash
                FROM payout_wallet
                GROUP BY address_hash
                HAVING COUNT(DISTINCT wallet_id) > 1
            )
        """,
    }
    connection = sqlite3.connect(db_path)
    try:
        results = {
            name: int(connection.execute(sql).fetchone()[0])
            for name, sql in checks.items()
        }
    finally:
        connection.close()
    failed = {name: count for name, count in results.items() if count}
    if failed:
        raise ValueError(f"data quality gate failed: {failed}")
    return results


def _prepare_sample_table(
    connection: sqlite3.Connection, affiliate_ids: list[str] | None
) -> None:
    connection.execute("DROP TABLE IF EXISTS sample_affiliate")
    connection.execute("CREATE TEMP TABLE sample_affiliate (affiliate_id TEXT PRIMARY KEY)")
    if affiliate_ids:
        connection.executemany(
            "INSERT INTO sample_affiliate (affiliate_id) VALUES (?)",
            [(affiliate_id,) for affiliate_id in affiliate_ids],
        )


def _row_to_signal(
    row: sqlite3.Row,
    config: dict[str, Any],
    run_id: str,
    snapshot_id: str,
) -> dict[str, Any]:
    item = {key: row[key] for key in row.keys()}
    branch = item["rule_branch"]
    rule_key = "A" if branch == "A" else "B"
    source_ids = sorted(set(item.pop("source_row_ids").split("|")))
    identity = [
        branch,
        item.get("wallet_id", ""),
        item.get("affiliate_id", ""),
        item.get("accrual_period", ""),
        *source_ids,
    ]
    bucket = item["bucket"]
    if bucket == "data_quality_block":
        raise ValueError("unknown wallet type must not be routed as expected shared")
    item.update(
        {
            "signal_id": f"SIG-{stable_id(*identity)}",
            "run_id": run_id,
            "snapshot_id": snapshot_id,
            "rule_version_id": config["rules"][rule_key]["rule_version_id"],
            "source_row_ids": source_ids,
            "control_objective": "CO-01" if branch == "A" else "CO-02",
            "detection_timestamp_utc": config["logical_run_at_utc"],
            "threshold_status": config["status"],
            "review_threshold_minor": config["review_threshold_minor"]
            if branch == "B2"
            else None,
            "window_days_inclusive": config["window_days_inclusive"]
            if branch == "B2"
            else None,
            "signal_statement": "exception requiring explanation",
            "review_status": "pending_human_review"
            if bucket == "potential_exception"
            else "context_only",
        }
    )
    if bucket == "expected_shared":
        item["severity"] = "informational"
    return item


def consolidate_review_cases(
    signals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for signal in signals:
        if signal["rule_branch"] == "A":
            grouped.setdefault(f"A|{signal['wallet_id']}", []).append(signal)

    b_signals = [signal for signal in signals if signal["rule_branch"] != "A"]
    components: list[list[dict[str, Any]]] = []
    for signal in b_signals:
        signal_sources = set(signal["source_row_ids"])
        matching = [
            index
            for index, component in enumerate(components)
            if signal_sources
            & {
                source_id
                for existing in component
                for source_id in existing["source_row_ids"]
            }
        ]
        if not matching:
            components.append([signal])
            continue
        target = matching[0]
        components[target].append(signal)
        for index in reversed(matching[1:]):
            components[target].extend(components.pop(index))
    for component in components:
        source_ids = sorted(
            {
                source_id
                for signal in component
                for source_id in signal["source_row_ids"]
            }
        )
        grouped[f"B|{'|'.join(source_ids)}"] = component

    cases: list[dict[str, Any]] = []
    severity_rank = {"informational": 0, "medium": 1, "high": 2}
    for group_key, group in sorted(grouped.items()):
        first = dict(group[0])
        source_ids = sorted(
            {
                source_id
                for signal in group
                for source_id in signal["source_row_ids"]
            }
        )
        branches = sorted({signal["rule_branch"] for signal in group})
        bucket = (
            "potential_exception"
            if any(signal["bucket"] == "potential_exception" for signal in group)
            else "expected_shared"
        )
        severity = max(
            (signal["severity"] for signal in group),
            key=lambda value: severity_rank[value],
        )
        if bucket == "expected_shared":
            severity = "informational"
        first.update(
            {
                "exception_id": f"EX-{stable_id(group_key, *source_ids)}",
                "assertion_hits": branches,
                "rule_branch": "+".join(branches),
                "signal_hit_count": len(group),
                "signal_details": [
                    {
                        key: signal.get(key)
                        for key in (
                            "signal_id",
                            "rule_branch",
                            "affiliate_id",
                            "affiliate_id_a",
                            "affiliate_id_b",
                            "accrual_period",
                            "payment_id_a",
                            "payment_id_b",
                            "source_ref_a",
                            "source_ref_b",
                            "payment_count",
                            "qualifying_window_count",
                            "total_amount_minor",
                            "first_payment_date",
                            "last_payment_date",
                            "source_row_ids",
                        )
                        if signal.get(key) is not None
                    }
                    for signal in sorted(group, key=lambda item: item["signal_id"])
                ],
                "source_row_ids": source_ids,
                "bucket": bucket,
                "severity": severity,
                "review_status": "pending_human_review"
                if bucket == "potential_exception"
                else "context_only",
            }
        )
        if first["control_objective"] == "CO-02":
            affected_affiliates = sorted(
                {
                    affiliate_id
                    for signal in group
                    for affiliate_id in (
                        signal.get("affiliate_id_a"),
                        signal.get("affiliate_id_b"),
                    )
                    if affiliate_id
                }
            )
            if not affected_affiliates:
                affected_affiliates = sorted(
                    {
                        signal["affiliate_id"]
                        for signal in group
                        if signal.get("affiliate_id")
                    }
                )
            first["affected_affiliate_ids"] = affected_affiliates
            first["affiliate_id"] = (
                affected_affiliates[0]
                if len(affected_affiliates) == 1
                else "multiple"
            )
            accrual_periods = sorted(
                {
                    signal["accrual_period"]
                    for signal in group
                    if signal.get("accrual_period")
                }
            )
            first["accrual_period"] = (
                accrual_periods[0] if len(accrual_periods) == 1 else "multiple"
            )
            for field in (
                "qualifying_window_count",
                "payment_count",
                "total_amount_minor",
                "first_payment_date",
                "last_payment_date",
                "review_threshold_minor",
                "window_days_inclusive",
            ):
                values = {
                    signal[field]
                    for signal in group
                    if signal.get(field) is not None
                }
                first[field] = next(iter(values)) if len(values) == 1 else None
        cases.append(first)
    return sorted(cases, key=lambda item: item["exception_id"])


def execute_rule_signals(
    db_path: Path,
    root: Path,
    config: dict[str, Any],
    run_id: str,
    snapshot_id: str,
    affiliate_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    scope = "sample" if affiliate_ids is not None else "population"
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        _prepare_sample_table(connection, affiliate_ids)
        parameters = {
            "scope": scope,
            "review_threshold_minor": config["review_threshold_minor"],
            "window_days": config["window_days_inclusive"],
        }
        rows: list[sqlite3.Row] = []
        for rule_key in ("A", "B"):
            sql = (root / config["rules"][rule_key]["sql_file"]).read_text(
                encoding="utf-8"
            )
            rows.extend(connection.execute(sql, parameters).fetchall())
        signals = [
            _row_to_signal(row, config, run_id, snapshot_id) for row in rows
        ]
        return sorted(signals, key=lambda item: item["signal_id"])
    finally:
        connection.close()


def _matches(item: dict[str, Any], expected: dict[str, Any]) -> bool:
    return item["rule_branch"] == expected["rule_branch"] and all(
        item.get(key) == value for key, value in expected["match"].items()
    )


def validate_rules(
    exceptions: list[dict[str, Any]], truth: dict[str, Any]
) -> dict[str, Any]:
    potential = [
        item for item in exceptions if item["bucket"] == "potential_exception"
    ]
    positives = {
        case["case_id"]: any(_matches(item, case) for item in potential)
        for case in truth["positive_controls"]
    }
    negatives = {
        case["case_id"]: not any(_matches(item, case) for item in potential)
        for case in truth["negative_controls"]
    }
    expected_shared = {
        wallet_id: any(
            item.get("wallet_id") == wallet_id and item["bucket"] == "expected_shared"
            for item in exceptions
        )
        for wallet_id in truth["expected_shared"]
    }
    designed_false_positives = {
        case["case_id"]: any(_matches(item, case) for item in potential)
        for case in truth["designed_false_positives"]
    }
    passed = (
        all(positives.values())
        and all(negatives.values())
        and all(expected_shared.values())
        and all(designed_false_positives.values())
    )
    return {
        "passed": passed,
        "positive_controls": positives,
        "negative_controls": negatives,
        "expected_shared_visible": expected_shared,
        "designed_false_positives_visible": designed_false_positives,
    }


def _source_row_universe(output_dir: Path) -> set[str]:
    ids: set[str] = set()
    id_fields = {
        "employee": "employee_id",
        "affiliate": "affiliate_id",
        "payout_wallet": "wallet_id",
        "entity_wallet_link": "link_id",
        "commission_payment": "payment_id",
    }
    for table, id_field in id_fields.items():
        with (output_dir / "source_data" / f"{table}.csv").open(
            "r", encoding="utf-8", newline=""
        ) as handle:
            ids.update(row[id_field] for row in csv.DictReader(handle))
    return ids


def traceability_passes(
    output_dir: Path, exceptions: list[dict[str, Any]]
) -> bool:
    universes: dict[str, set[str]] = {}
    id_fields = {
        "payout_wallet": "wallet_id",
        "entity_wallet_link": "link_id",
        "commission_payment": "payment_id",
    }
    for table, id_field in id_fields.items():
        with (output_dir / "source_data" / f"{table}.csv").open(
            "r", encoding="utf-8", newline=""
        ) as handle:
            universes[table] = {row[id_field] for row in csv.DictReader(handle)}
    for item in exceptions:
        if not item["source_row_ids"]:
            return False
        branches = set(item.get("assertion_hits", [item["rule_branch"]]))
        if branches == {"A"}:
            if not set(item["source_row_ids"]) <= universes["entity_wallet_link"]:
                return False
            if item.get("wallet_id") not in universes["payout_wallet"]:
                return False
        elif not set(item["source_row_ids"]) <= universes["commission_payment"]:
            return False
    return True


def sample_affiliates(
    affiliate_ids: list[str], size: int, seed: int
) -> list[str]:
    return sorted(random.Random(seed).sample(affiliate_ids, size))


def _write_exception_csv(path: Path, exceptions: list[dict[str, Any]]) -> None:
    fields = [
        "exception_id",
        "rule_branch",
        "bucket",
        "severity",
        "signal_statement",
        "review_status",
        "rule_version_id",
        "snapshot_id",
        "source_row_ids",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for item in exceptions:
            row = {key: item.get(key) for key in fields}
            row["source_row_ids"] = "|".join(item["source_row_ids"])
            writer.writerow(row)


def _artifact_manifest(output_dir: Path, files: list[Path]) -> dict[str, Any]:
    return build_artifact_manifest(output_dir, files)


def _affected_entity_ids(exceptions: list[dict[str, Any]]) -> set[str]:
    affected: set[str] = set()
    for item in exceptions:
        if item["bucket"] != "potential_exception":
            continue
        if item["control_objective"] == "CO-01" and item.get("wallet_id"):
            affected.add(item["wallet_id"])
            continue
        affiliate_ids = item.get("affected_affiliate_ids") or []
        if affiliate_ids:
            affected.update(affiliate_ids)
        elif item.get("affiliate_id") and item["affiliate_id"] != "multiple":
            affected.add(item["affiliate_id"])
    return affected


def _derive_run_identity(
    root: Path, config: dict[str, Any]
) -> tuple[str, str, str]:
    with TemporaryDirectory(prefix="audit-monitor-preflight-") as temporary:
        staging_dir = Path(temporary)
        generate_snapshot(staging_dir, config["dataset_seed"])
        manifest = verify_snapshot(staging_dir)
    snapshot_id = stable_id(canonical_json(manifest).decode("utf-8"), length=24)
    precommitment_hash = sha256_file(root / "config" / "rule_precommitment.json")
    run_id = f"RUN-{stable_id(snapshot_id, precommitment_hash, length=20)}"
    return snapshot_id, precommitment_hash, run_id


def _load_existing_run(
    output_dir: Path,
    root: Path,
    config: dict[str, Any],
    expected_snapshot_id: str,
    expected_precommitment_hash: str,
    expected_run_id: str,
) -> dict[str, Any]:
    run_path = output_dir / "run_manifest.json"
    run_manifest = json.loads(run_path.read_text(encoding="utf-8"))
    if run_manifest.get("run_id") != expected_run_id:
        raise RuntimeError("existing run directory belongs to a different run_id")
    if run_manifest.get("snapshot_id") != expected_snapshot_id:
        raise RuntimeError("existing run snapshot_id mismatch")
    if run_manifest.get("precommitment_sha256") != expected_precommitment_hash:
        raise RuntimeError("existing run pre-commitment mismatch")

    snapshot_manifest = verify_snapshot(output_dir)
    actual_snapshot_id = stable_id(
        canonical_json(snapshot_manifest).decode("utf-8"), length=24
    )
    if actual_snapshot_id != expected_snapshot_id:
        raise RuntimeError("existing snapshot content does not match run_id")
    db_path = output_dir / "audit_population.sqlite"
    if not db_path.is_file():
        raise RuntimeError("existing run database is missing")
    validate_data_quality(db_path)
    signals = execute_rule_signals(
        db_path,
        root,
        config,
        expected_run_id,
        expected_snapshot_id,
        affiliate_ids=None,
    )
    exceptions = consolidate_review_cases(signals)
    stored_exceptions = json.loads(
        (output_dir / "exception_queue.json").read_text(encoding="utf-8")
    )
    if canonical_json(exceptions) != canonical_json(stored_exceptions):
        raise RuntimeError("existing exception queue is not reproducible")

    evidence_manifest = json.loads(
        (output_dir / "evidence_pack_manifest.json").read_text(encoding="utf-8")
    )
    try:
        verify_artifact_manifest(
            output_dir,
            evidence_manifest,
            required_artifacts=COMMISSION_STATIC_ARTIFACTS,
        )
    except ValueError as exc:
        raise RuntimeError(f"existing evidence artifact invalid: {exc}") from exc
    review_chain = verify_review_chain(
        output_dir / "review_log.jsonl",
        output_dir / "exception_queue.json",
    )
    comparison = json.loads(
        (output_dir / "sample_comparison.json").read_text(encoding="utf-8")
    )
    return {
        "output_dir": str(output_dir),
        "run_manifest": run_manifest,
        "exceptions": exceptions,
        "signals": signals,
        "comparison": comparison,
        "evidence_pack_manifest": evidence_manifest,
        "review_chain_manifest": review_chain,
    }


def run_demo(output_dir: Path | None = None) -> dict[str, Any]:
    root = repository_root()
    config = load_precommitment(root)
    snapshot_id, precommitment_hash, run_id = _derive_run_identity(root, config)
    output_dir = output_dir or (root / "outputs" / "runs" / run_id)
    run_path = output_dir / "run_manifest.json"
    if run_path.exists():
        return _load_existing_run(
            output_dir,
            root,
            config,
            snapshot_id,
            precommitment_hash,
            run_id,
        )
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError(
            "output directory contains unversioned or partial artifacts; refusing overwrite"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    generate_snapshot(output_dir, config["dataset_seed"])
    snapshot_manifest = verify_snapshot(output_dir)
    generated_snapshot_id = stable_id(
        canonical_json(snapshot_manifest).decode("utf-8"), length=24
    )
    if generated_snapshot_id != snapshot_id:
        raise RuntimeError("generated snapshot differs from preflight snapshot")
    db_path = output_dir / "audit_population.sqlite"
    load_snapshot_to_sqlite(output_dir, db_path)
    data_quality = validate_data_quality(db_path)
    signals = execute_rule_signals(
        db_path, root, config, run_id, snapshot_id, affiliate_ids=None
    )
    exceptions = consolidate_review_cases(signals)
    truth = json.loads((output_dir / "ground_truth.json").read_text(encoding="utf-8"))
    rule_validation = validate_rules(signals, truth)
    traceable = traceability_passes(output_dir, exceptions)
    if not rule_validation["passed"]:
        raise RuntimeError("rule validation gate failed")
    if not traceable:
        raise RuntimeError("source-row traceability gate failed")

    with (output_dir / "source_data" / "affiliate.csv").open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        affiliate_ids = [row["affiliate_id"] for row in csv.DictReader(handle)]
    population_potential = {
        item["exception_id"]
        for item in exceptions
        if item["bucket"] == "potential_exception"
    }
    sample_runs = []
    for seed in config["sample"]["seeds"]:
        selected = sample_affiliates(
            affiliate_ids, config["sample"]["size"], seed
        )
        sample_signals = execute_rule_signals(
            db_path, root, config, run_id, snapshot_id, affiliate_ids=selected
        )
        sample_exceptions = consolidate_review_cases(sample_signals)
        sample_potential = {
            item["exception_id"]
            for item in sample_exceptions
            if item["bucket"] == "potential_exception"
        }
        sample_runs.append(
            {
                "seed": seed,
                "sample_unit": config["sample"]["unit"],
                "sample_size": len(selected),
                "selected_affiliate_ids": selected,
                "observed_potential_exceptions": len(sample_potential),
                "observed_missed_population_cases": len(
                    population_potential - sample_potential
                ),
                "population_exceptions_in_sample_frame": len(
                    population_potential & sample_potential
                ),
                "observed_population_coverage_percent": round(
                    len(selected) / len(affiliate_ids) * 100, 2
                ),
                "observed_exception_ids": sorted(sample_potential),
            }
        )

    potential_count = sum(
        item["bucket"] == "potential_exception" for item in exceptions
    )
    potential_signal_hits = sum(
        item["bucket"] == "potential_exception" for item in signals
    )
    objective_conclusions = {
        "CO-01": "exceptions_identified"
        if any(
            item["rule_branch"] == "A" and item["bucket"] == "potential_exception"
            for item in exceptions
        )
        else "no_exceptions_detected",
        "CO-02": "exceptions_identified"
        if any(
            item["control_objective"] == "CO-02"
            and item["bucket"] == "potential_exception"
            for item in exceptions
        )
        else "no_exceptions_detected",
    }
    if not set(objective_conclusions.values()) <= APPROVED_CONCLUSIONS:
        raise RuntimeError("bounded conclusion gate failed")

    gates = {
        "G1_snapshot_integrity": "passed",
        "G2_population_completeness": "passed",
        "G3_precommitment": "passed",
        "G4_rule_validation": "passed",
        "G5_traceability": "passed",
        "G6_append_only_review_contract": "implemented_requires_release_test",
        "G7_determinism": "requires_release_test",
        "G8_bounded_conclusions": "passed",
    }
    run_manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "run_timestamp_utc": config["logical_run_at_utc"],
        "synthetic_only": True,
        "reviewer_identity_status": "self_attested_prototype",
        "snapshot_id": snapshot_id,
        "snapshot_manifest_sha256": sha256_file(
            output_dir / "snapshot_manifest.json"
        ),
        "precommitment_sha256": precommitment_hash,
        "configuration_version_id": config["configuration_version_id"],
        "pipeline_version": config["pipeline_version"],
        "rule_versions": {
            key: {
                "rule_version_id": value["rule_version_id"],
                "sql_sha256": value["sql_sha256"],
            }
            for key, value in config["rules"].items()
        },
        "population": snapshot_manifest,
        "routing_counts": {
            "assertion_hits": len(signals),
            "potential_assertion_hits": potential_signal_hits,
            "review_cases": potential_count,
            "context_items": sum(
                item["bucket"] == "expected_shared" for item in exceptions
            ),
        },
        "objective_conclusions": objective_conclusions,
        "rule_validation": rule_validation,
        "data_quality_validation": data_quality,
        "gates": gates,
        "assurance_profile": assurance_profile(
            "L1_deterministic_recomputation"
        ),
        "review_chain_control": (
            "separate append-only tamper-evident chain; not externally immutable"
        ),
        "human_decision": "required",
        "automated_action": "none",
    }
    validate_evidence_contract(
        run_manifest,
        exceptions,
        _source_row_universe(output_dir),
    )
    comparison = {
        "statement": (
            "Observed synthetic results only. No probability, confidence, "
            "recall or real-population inference."
        ),
        "population_affiliates": len(affiliate_ids),
        "population_potential_exceptions": len(population_potential),
        "population_signal_hits": len(signals),
        "sample_method": config["sample"]["method"],
        "sample_unit": config["sample"]["unit"],
        "sample_size": config["sample"]["size"],
        "sampling_frame_exclusions": (
            "Employee-only wallet signals are outside the affiliate sampling "
            "frame. The population run still tests them."
        ),
        "sample_runs": sample_runs,
    }
    review_template = {
        "identity_status": "self_attested_prototype",
        "review_id": None,
        "run_id": run_id,
        "snapshot_id": snapshot_id,
        "exception_id": None,
        "reviewer_id": None,
        "review_timestamp_utc": None,
        "question_presented": None,
        "conclusion": None,
        "disposition": None,
        "rationale": None,
        "evidence_viewed": [],
        "supersedes_review_id": None,
        "ai_assistance_used": None,
    }

    exception_path = output_dir / "exception_queue.json"
    csv_path = output_dir / "exception_queue.csv"
    comparison_path = output_dir / "sample_comparison.json"
    review_path = output_dir / "review_record_template.json"
    review_log_path = output_dir / "review_log.jsonl"
    review_chain_path = output_dir / "review_chain_manifest.json"
    write_canonical_json(exception_path, exceptions)
    _write_exception_csv(csv_path, exceptions)
    write_canonical_json(run_path, run_manifest)
    write_canonical_json(comparison_path, comparison)
    write_canonical_json(review_path, review_template)
    if not review_log_path.exists():
        initialize_review_chain(review_log_path)
    review_chain = verify_review_chain(review_log_path, exception_path)
    if not review_chain_path.exists():
        write_canonical_json(review_chain_path, review_chain)
    html_path = output_dir / "index.html"
    html_path.write_text(
        render_html(run_manifest, exceptions, comparison),
        encoding="utf-8",
        newline="\n",
    )
    artifact_paths = [
        exception_path,
        csv_path,
        run_path,
        comparison_path,
        review_path,
        html_path,
        output_dir / "snapshot_manifest.json",
        output_dir / "ground_truth.json",
    ]
    evidence_manifest = _artifact_manifest(output_dir, artifact_paths)
    evidence_manifest_path = output_dir / "evidence_pack_manifest.json"
    write_canonical_json(evidence_manifest_path, evidence_manifest)
    return {
        "output_dir": str(output_dir),
        "run_manifest": run_manifest,
        "exceptions": exceptions,
        "signals": signals,
        "comparison": comparison,
        "evidence_pack_manifest": evidence_manifest,
        "review_chain_manifest": review_chain,
    }
