from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from crypto_audit_monitor.engine import (
    APPROVED_CONCLUSIONS,
    _affected_entity_ids,
    consolidate_review_cases,
    execute_rule_signals,
    load_precommitment,
    repository_root,
    run_demo,
    traceability_passes,
    validate_data_quality,
    verify_snapshot,
)
from crypto_audit_monitor.integrity import sha256_file
from crypto_audit_monitor.renderer import render_html
from crypto_audit_monitor.run_demo import seed_worked_reviews
from crypto_audit_monitor.review_log import (
    append_review_record,
    read_review_log,
    verify_review_chain,
)


@pytest.fixture()
def completed_run(tmp_path: Path) -> tuple[Path, dict]:
    output_dir = tmp_path / "demo"
    return output_dir, run_demo(output_dir)


def test_one_command_builds_complete_offline_pack(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, result = completed_run
    expected = {
        "index.html",
        "exception_queue.json",
        "exception_queue.csv",
        "run_manifest.json",
        "sample_comparison.json",
        "review_record_template.json",
        "review_log.jsonl",
        "evidence_pack_manifest.json",
        "snapshot_manifest.json",
        "audit_population.sqlite",
    }
    assert expected <= {path.name for path in output_dir.iterdir()}
    assert result["run_manifest"]["automated_action"] == "none"
    assert result["run_manifest"]["human_decision"] == "required"


def test_committed_demo_uses_registered_configuration_version() -> None:
    root = repository_root()
    config = load_precommitment(root)
    committed_demo = (root / "demo" / "commission_case.html").read_text(
        encoding="utf-8"
    )
    assert (
        f'"configuration_version_id": '
        f'"{config["configuration_version_id"]}"'
    ) in committed_demo


def test_committed_demo_matches_fresh_render(tmp_path: Path) -> None:
    root = repository_root()
    result = run_demo(tmp_path / "release")
    reviews = seed_worked_reviews(result)
    expected = render_html(
        result["run_manifest"],
        result["exceptions"],
        result["comparison"],
        reviews,
        back_href="index.html",
    )
    assert (
        root / "demo" / "commission_case.html"
    ).read_text(encoding="utf-8") == expected


def test_routing_metrics_reconcile_without_overlapping_synonyms(
    completed_run: tuple[Path, dict],
) -> None:
    _, result = completed_run
    counts = result["run_manifest"]["routing_counts"]
    assert set(counts) == {
        "assertion_hits",
        "potential_assertion_hits",
        "review_cases",
        "context_items",
    }
    assert counts["assertion_hits"] == (
        counts["potential_assertion_hits"] + counts["context_items"]
    )
    assert counts == {
        "assertion_hits": 13,
        "potential_assertion_hits": 11,
        "review_cases": 6,
        "context_items": 2,
    }


def test_all_integrity_gates_and_seeded_controls_pass(
    completed_run: tuple[Path, dict],
) -> None:
    _, result = completed_run
    manifest = result["run_manifest"]
    assert set(manifest["gates"].values()) <= {
        "passed",
        "implemented_requires_release_test",
        "requires_release_test",
    }
    validation = manifest["rule_validation"]
    assert validation["passed"] is True
    assert all(validation["positive_controls"].values())
    assert all(validation["negative_controls"].values())
    assert all(validation["expected_shared_visible"].values())
    assert all(validation["designed_false_positives_visible"].values())


def test_snapshot_tampering_blocks_verification(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, _ = completed_run
    employee_path = output_dir / "source_data" / "employee.csv"
    with employee_path.open("a", encoding="utf-8") as handle:
        handle.write("E9999,0\n")
    with pytest.raises(ValueError, match="snapshot hash mismatch"):
        verify_snapshot(output_dir)


def test_validation_fixture_tampering_blocks_verification(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, _ = completed_run
    fixture_path = output_dir / "ground_truth.json"
    fixture_path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="validation fixture hash mismatch"):
        verify_snapshot(output_dir)


def test_sql_change_without_versioned_hash_is_blocked(tmp_path: Path) -> None:
    root = repository_root()
    isolated = tmp_path / "repo"
    (isolated / "config").mkdir(parents=True)
    (isolated / "sql").mkdir()
    shutil.copy(root / "config" / "rule_precommitment.json", isolated / "config")
    shutil.copy(root / "config" / "precommitment_registry.json", isolated / "config")
    for filename in ("rule_a_shared_wallet.sql", "rule_b_duplicate_split.sql"):
        shutil.copy(root / "sql" / filename, isolated / "sql")
    with (isolated / "sql" / "rule_a_shared_wallet.sql").open(
        "a", encoding="utf-8"
    ) as handle:
        handle.write("\n-- uncommitted change\n")
    with pytest.raises(ValueError, match="SQL hash mismatch"):
        load_precommitment(isolated)


def test_rule_a_is_clustered_and_expected_shared_is_not_silently_removed(
    completed_run: tuple[Path, dict],
) -> None:
    _, result = completed_run
    rule_a = [item for item in result["exceptions"] if item["rule_branch"] == "A"]
    assert {item["wallet_id"] for item in rule_a} == {
        "W_CASE_A1",
        "W_CASE_A2",
        "W_EXPECTED_EXCHANGE",
        "W_EXPECTED_TREASURY",
    }
    exchange = next(
        item for item in rule_a if item["wallet_id"] == "W_EXPECTED_EXCHANGE"
    )
    assert exchange["bucket"] == "expected_shared"
    assert exchange["overlapping_pair_count"] == 780
    assert len(exchange["source_row_ids"]) == 40


def test_non_overlap_and_reversal_negative_controls_do_not_alert(
    completed_run: tuple[Path, dict],
) -> None:
    _, result = completed_run
    potential = [
        item
        for item in result["exceptions"]
        if item["bucket"] == "potential_exception"
    ]
    assert all(item.get("wallet_id") != "W_NEAR_A1" for item in potential)
    assert not any(
        item["rule_branch"] == "B1" and item.get("affiliate_id") == "A0103"
        for item in potential
    )


def test_threshold_equality_and_inclusive_seven_day_boundary_are_declared(
    completed_run: tuple[Path, dict],
) -> None:
    _, result = completed_run
    match = [
        item
        for item in result["exceptions"]
        if "B2" in item["assertion_hits"] and item.get("affiliate_id") == "A0102"
    ]
    assert len(match) == 1
    assert match[0]["total_amount_minor"] == 1_000_000
    assert match[0]["first_payment_date"] == "2026-03-01"
    assert match[0]["last_payment_date"] == "2026-03-08"


def test_every_exception_resolves_to_source_rows(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, result = completed_run
    assert traceability_passes(output_dir, result["exceptions"]) is True


def test_canonical_exception_set_is_byte_stable(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    run_demo(first)
    run_demo(second)
    assert (first / "exception_queue.json").read_bytes() == (
        second / "exception_queue.json"
    ).read_bytes()
    assert sha256_file(first / "exception_queue.json") == sha256_file(
        second / "exception_queue.json"
    )


def test_generated_html_is_byte_stable(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    run_demo(first)
    run_demo(second)
    assert (first / "index.html").read_bytes() == (
        second / "index.html"
    ).read_bytes()


def test_five_precommitted_samples_are_bounded_and_observed_only(
    completed_run: tuple[Path, dict],
) -> None:
    _, result = completed_run
    comparison = result["comparison"]
    assert len(comparison["sample_runs"]) == 5
    assert {run["sample_size"] for run in comparison["sample_runs"]} == {60}
    observed = [
        run["observed_potential_exceptions"] for run in comparison["sample_runs"]
    ]
    assert min(observed) == 0
    assert max(observed) > 0
    assert "no probability" in comparison["statement"].lower()
    assert not {
        "detection_probability",
        "confidence_interval",
        "recall_rate",
    } & set(comparison)


def test_objective_conclusions_are_bounded(
    completed_run: tuple[Path, dict],
) -> None:
    _, result = completed_run
    conclusions = set(
        result["run_manifest"]["objective_conclusions"].values()
    )
    assert conclusions <= APPROVED_CONCLUSIONS
    assert any(
        set(item["assertion_hits"]) == {"B1", "B2"}
        for item in result["exceptions"]
    )
    assert (
        result["run_manifest"]["objective_conclusions"]["CO-02"]
        == "exceptions_identified"
    )


def test_neutral_language_and_human_boundary(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, result = completed_run
    for item in result["exceptions"]:
        assert item["signal_statement"] == "exception requiring explanation"
        if item["bucket"] == "potential_exception":
            assert item["review_status"] == "pending_human_review"
        else:
            assert item["review_status"] == "context_only"
            assert item["severity"] == "informational"
    html = (output_dir / "index.html").read_text(encoding="utf-8").lower()
    assert "not proof of misconduct" in html
    assert "不作欺诈结论" in html
    assert "automated_action=none" in html


def test_review_record_is_self_attested_and_append_only_ready(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, _ = completed_run
    record = json.loads(
        (output_dir / "review_record_template.json").read_text(encoding="utf-8")
    )
    assert record["identity_status"] == "self_attested_prototype"
    assert record["supersedes_review_id"] is None
    assert record["ai_assistance_used"] is None


def test_worked_reviews_cover_three_cases_and_one_correction(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, result = completed_run
    records = seed_worked_reviews(result)
    assert len(records) == 4
    assert len({record["exception_id"] for record in records}) == 3
    assert {record["conclusion"] for record in records} >= {
        "supported_explanation",
        "control_exception_confirmed",
        "more_evidence_required",
    }
    corrections = [
        record for record in records if record.get("supersedes_review_id")
    ]
    assert len(corrections) == 1
    assert corrections[0]["supersedes_review_id"] == records[2]["review_id"]
    assert verify_review_chain(
        output_dir / "review_log.jsonl",
        output_dir / "exception_queue.json",
    )["record_count"] == 4


def test_review_log_appends_and_corrections_supersede(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, result = completed_run
    path = output_dir / "review_log.jsonl"
    queue_path = output_dir / "exception_queue.json"
    exception = next(
        item
        for item in result["exceptions"]
        if item["bucket"] == "potential_exception"
    )
    base = {
        "exception_id": exception["exception_id"],
        "run_id": exception["run_id"],
        "snapshot_id": exception["snapshot_id"],
        "reviewer_id": "reviewer-demo-1",
        "review_timestamp_utc": "2026-07-30T13:00:00Z",
        "question_presented": "Is the relationship explained?",
        "conclusion": "more_evidence_required",
        "disposition": "keep_open",
        "rationale": "Supporting approval evidence is not present.",
        "evidence_viewed": exception["source_row_ids"],
        "identity_status": "self_attested_prototype",
        "ai_assistance_used": False,
        "supersedes_review_id": None,
    }
    first = append_review_record(path, base, queue_path)
    correction = dict(base)
    correction.update(
        {
            "review_timestamp_utc": "2026-07-30T14:00:00Z",
            "rationale": "Correction: custody evidence remains pending.",
            "supersedes_review_id": first["review_id"],
        }
    )
    second = append_review_record(path, correction, queue_path)
    records = read_review_log(path)
    assert [item["review_id"] for item in records] == [
        first["review_id"],
        second["review_id"],
    ]
    assert records[1]["supersedes_review_id"] == records[0]["review_id"]
    assert verify_review_chain(path, queue_path)["record_count"] == 2
    with pytest.raises(ValueError, match="cannot be overwritten"):
        append_review_record(path, first, queue_path)


def test_review_correction_cannot_cross_exception_or_move_back_in_time(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, result = completed_run
    path = output_dir / "review_log.jsonl"
    queue_path = output_dir / "exception_queue.json"
    exceptions = [
        item
        for item in result["exceptions"]
        if item["bucket"] == "potential_exception"
    ]
    first_exception, second_exception = exceptions[:2]
    base = {
        "exception_id": first_exception["exception_id"],
        "run_id": first_exception["run_id"],
        "snapshot_id": first_exception["snapshot_id"],
        "reviewer_id": "reviewer-demo-1",
        "review_timestamp_utc": "2026-07-30T13:00:00Z",
        "question_presented": "Is the relationship explained?",
        "conclusion": "more_evidence_required",
        "disposition": "keep_open",
        "rationale": "Supporting evidence is pending.",
        "evidence_viewed": first_exception["source_row_ids"],
        "identity_status": "self_attested_prototype",
        "ai_assistance_used": False,
        "supersedes_review_id": None,
    }
    first = append_review_record(path, base, queue_path)
    cross_exception = dict(base)
    cross_exception.update(
        {
            "exception_id": second_exception["exception_id"],
            "run_id": second_exception["run_id"],
            "snapshot_id": second_exception["snapshot_id"],
            "evidence_viewed": second_exception["source_row_ids"],
            "review_timestamp_utc": "2026-07-30T14:00:00Z",
            "supersedes_review_id": first["review_id"],
        }
    )
    with pytest.raises(ValueError, match="must match superseded review exception_id"):
        append_review_record(path, cross_exception, queue_path)

    naive_timestamp = dict(base)
    naive_timestamp.update(
        {
            "review_timestamp_utc": "2026-07-30T14:00:00",
            "supersedes_review_id": first["review_id"],
        }
    )
    with pytest.raises(ValueError, match="timezone-aware UTC"):
        append_review_record(path, naive_timestamp, queue_path)

    earlier_timestamp = dict(base)
    earlier_timestamp.update(
        {
            "review_timestamp_utc": "2026-07-30T12:00:00Z",
            "supersedes_review_id": first["review_id"],
        }
    )
    with pytest.raises(ValueError, match="increase monotonically"):
        append_review_record(path, earlier_timestamp, queue_path)


def test_first_review_cannot_predate_exception_detection(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, result = completed_run
    path = output_dir / "review_log.jsonl"
    queue_path = output_dir / "exception_queue.json"
    exception = next(
        item
        for item in result["exceptions"]
        if item["bucket"] == "potential_exception"
    )
    record = {
        "exception_id": exception["exception_id"],
        "run_id": exception["run_id"],
        "snapshot_id": exception["snapshot_id"],
        "reviewer_id": "reviewer-demo-1",
        "review_timestamp_utc": "2020-01-01T00:00:00Z",
        "question_presented": "Is the relationship explained?",
        "conclusion": "more_evidence_required",
        "disposition": "keep_open",
        "rationale": "Supporting evidence is pending.",
        "evidence_viewed": exception["source_row_ids"],
        "identity_status": "self_attested_prototype",
        "ai_assistance_used": False,
        "supersedes_review_id": None,
    }
    with pytest.raises(ValueError, match="cannot predate exception detection"):
        append_review_record(path, record, queue_path)


def test_review_log_survives_same_run_regeneration(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, result = completed_run
    queue_path = output_dir / "exception_queue.json"
    exception = next(
        item
        for item in result["exceptions"]
        if item["bucket"] == "potential_exception"
    )
    record = {
        "exception_id": exception["exception_id"],
        "run_id": exception["run_id"],
        "snapshot_id": exception["snapshot_id"],
        "reviewer_id": "reviewer-demo-1",
        "review_timestamp_utc": "2026-07-30T13:00:00Z",
        "question_presented": "Is the relationship explained?",
        "conclusion": "more_evidence_required",
        "disposition": "keep_open",
        "rationale": "Supporting approval evidence is not present.",
        "evidence_viewed": exception["source_row_ids"],
        "identity_status": "self_attested_prototype",
        "ai_assistance_used": False,
        "supersedes_review_id": None,
    }
    append_review_record(output_dir / "review_log.jsonl", record, queue_path)
    run_demo(output_dir)
    assert len(read_review_log(output_dir / "review_log.jsonl")) == 1


def test_evidence_pack_manifest_binds_exported_artifacts(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, result = completed_run
    for relative_path, expected_hash in result["evidence_pack_manifest"][
        "artifacts"
    ].items():
        assert sha256_file(output_dir / relative_path) == expected_hash


def test_threshold_change_without_new_configuration_version_is_blocked(
    tmp_path: Path,
) -> None:
    root = repository_root()
    isolated = tmp_path / "repo"
    shutil.copytree(root / "config", isolated / "config")
    shutil.copytree(root / "sql", isolated / "sql")
    config_path = isolated / "config" / "rule_precommitment.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["review_threshold_minor"] += 1
    config_path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError, match="configuration hash mismatch"):
        load_precommitment(isolated)


def test_unknown_wallet_type_fails_closed(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, _ = completed_run
    db_path = output_dir / "audit_population.sqlite"
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            INSERT INTO payout_wallet (wallet_id, address_hash, wallet_type)
            VALUES ('W_UNKNOWN', 'fabricated', 'novel_unclassified')
            """
        )
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(ValueError, match="unknown_wallet_type"):
        validate_data_quality(db_path)


def test_duplicate_wallet_address_hash_fails_closed(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, _ = completed_run
    db_path = output_dir / "audit_population.sqlite"
    connection = sqlite3.connect(db_path)
    try:
        address_hash = connection.execute(
            "SELECT address_hash FROM payout_wallet LIMIT 1"
        ).fetchone()[0]
        connection.execute(
            """
            INSERT INTO payout_wallet (wallet_id, address_hash, wallet_type)
            VALUES ('W_DUPLICATE_MASTER', ?, 'self_custody')
            """,
            (address_hash,),
        )
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(ValueError, match="duplicate_wallet_address_hash"):
        validate_data_quality(db_path)


def test_branch_aware_traceability_rejects_wrong_table_row(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, result = completed_run
    fake = dict(result["exceptions"][0])
    fake["assertion_hits"] = ["B1"]
    fake["source_row_ids"] = ["E0001"]
    assert traceability_passes(output_dir, [fake]) is False


def test_independent_edge_scenarios_cover_cross_period_duplicate_and_sliding_window(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, result = completed_run
    db_path = output_dir / "audit_population.sqlite"
    connection = sqlite3.connect(db_path)
    try:
        connection.executemany(
            """
            INSERT INTO commission_payment (
                payment_id, affiliate_id, accrual_period, amount_minor,
                payment_date, source_ref, payment_status
            ) VALUES (?, ?, ?, ?, ?, ?, 'completed')
            """,
            [
                ("EDGE_B1_1", "A0999", "2026-07", 210000, "2026-07-02", "EDGE_DUP",),
                ("EDGE_B1_2", "A0999", "2026-08", 330000, "2026-08-03", "EDGE_DUP",),
                ("EDGE_B2_1", "A0998", "EDGE-Q1", 100000, "2026-03-01", "EDGE_OLD",),
                ("EDGE_B2_2", "A0998", "EDGE-Q1", 600000, "2026-03-20", "EDGE_SPLIT_A",),
                ("EDGE_B2_3", "A0998", "EDGE-Q1", 500000, "2026-03-23", "EDGE_SPLIT_B",),
                ("EDGE_B2_N1", "A0997", "EDGE-Q2", 300000, "2026-04-02", "EDGE_SMALL_A",),
                ("EDGE_B2_N2", "A0997", "EDGE-Q2", 300000, "2026-04-02", "EDGE_SMALL_B",),
            ],
        )
        connection.commit()
    finally:
        connection.close()
    config = load_precommitment(repository_root())
    signals = execute_rule_signals(
        db_path,
        repository_root(),
        config,
        result["run_manifest"]["run_id"],
        result["run_manifest"]["snapshot_id"],
    )
    assert any(
        item["rule_branch"] == "B1"
        and item.get("affiliate_id") == "A0999"
        for item in signals
    )
    assert any(
        item["rule_branch"] == "B2"
        and item.get("affiliate_id") == "A0998"
        for item in signals
    )
    assert not any(
        item["rule_branch"] == "B2"
        and item.get("affiliate_id") == "A0997"
        for item in signals
    )
    cases = consolidate_review_cases(signals)
    assert any(
        item.get("affiliate_id") == "A0998"
        and "B2" in item["assertion_hits"]
        for item in cases
    )


def test_cross_affiliate_reference_and_multi_period_pairs_cluster_once(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, result = completed_run
    db_path = output_dir / "audit_population.sqlite"
    connection = sqlite3.connect(db_path)
    try:
        connection.executemany(
            """
            INSERT INTO commission_payment (
                payment_id, affiliate_id, accrual_period, amount_minor,
                payment_date, source_ref, payment_status
            ) VALUES (?, ?, ?, ?, ?, ?, 'completed')
            """,
            [
                ("EDGE_CROSS_1", "A0995", "2026-01", 210000, "2026-01-02", "CROSS_REF"),
                ("EDGE_CROSS_2", "A0994", "2026-02", 330000, "2026-02-03", "CROSS_REF"),
                ("EDGE_CLUSTER_1", "A0993", "2026-01", 210000, "2026-01-02", "CLUSTER_REF"),
                ("EDGE_CLUSTER_2", "A0993", "2026-02", 330000, "2026-02-03", "CLUSTER_REF"),
                ("EDGE_CLUSTER_3", "A0993", "2026-03", 450000, "2026-03-04", "CLUSTER_REF"),
            ],
        )
        connection.commit()
    finally:
        connection.close()
    config = load_precommitment(repository_root())
    signals = execute_rule_signals(
        db_path,
        repository_root(),
        config,
        result["run_manifest"]["run_id"],
        result["run_manifest"]["snapshot_id"],
    )
    assert any(
        item["rule_branch"] == "B1"
        and item.get("source_ref_a") == "CROSS_REF"
        for item in signals
    )
    cases = consolidate_review_cases(signals)
    clustered = [
        item
        for item in cases
        if {"EDGE_CLUSTER_1", "EDGE_CLUSTER_2", "EDGE_CLUSTER_3"}
        <= set(item["source_row_ids"])
    ]
    assert len(clustered) == 1


def test_b2_uses_one_coherent_canonical_window(
    completed_run: tuple[Path, dict],
) -> None:
    output_dir, result = completed_run
    db_path = output_dir / "audit_population.sqlite"
    connection = sqlite3.connect(db_path)
    try:
        connection.executemany(
            """
            INSERT INTO commission_payment (
                payment_id, affiliate_id, accrual_period, amount_minor,
                payment_date, source_ref, payment_status
            ) VALUES (?, 'A0996', 'EDGE-WINDOW', ?, ?, ?, 'completed')
            """,
            [
                ("EDGE_WINDOW_1", 600000, "2026-01-01", "WINDOW_1"),
                ("EDGE_WINDOW_2", 500000, "2026-01-02", "WINDOW_2"),
                ("EDGE_WINDOW_3", 700000, "2026-01-20", "WINDOW_3"),
                ("EDGE_WINDOW_4", 600000, "2026-01-21", "WINDOW_4"),
            ],
        )
        connection.commit()
    finally:
        connection.close()
    config = load_precommitment(repository_root())
    signals = execute_rule_signals(
        db_path,
        repository_root(),
        config,
        result["run_manifest"]["run_id"],
        result["run_manifest"]["snapshot_id"],
    )
    signal = next(
        item
        for item in signals
        if item["rule_branch"] == "B2"
        and item.get("affiliate_id") == "A0996"
        and item.get("accrual_period") == "EDGE-WINDOW"
    )
    assert signal["qualifying_window_count"] == 2
    assert signal["total_amount_minor"] == 1_100_000
    assert signal["first_payment_date"] == "2026-01-01"
    assert signal["last_payment_date"] == "2026-01-02"
    assert signal["source_row_ids"] == ["EDGE_WINDOW_1", "EDGE_WINDOW_2"]


def test_existing_or_partial_run_directory_is_never_overwritten(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "occupied"
    output_dir.mkdir()
    run_path = output_dir / "run_manifest.json"
    run_path.write_text('{"run_id":"RUN-OLD"}', encoding="utf-8")
    sentinel = output_dir / "sentinel.txt"
    sentinel.write_text("preserve me", encoding="utf-8")
    with pytest.raises(RuntimeError, match="different run_id"):
        run_demo(output_dir)
    assert run_path.read_text(encoding="utf-8") == '{"run_id":"RUN-OLD"}'
    assert sentinel.read_text(encoding="utf-8") == "preserve me"

    partial_dir = tmp_path / "partial"
    partial_dir.mkdir()
    partial = partial_dir / "partial.txt"
    partial.write_text("preserve me too", encoding="utf-8")
    with pytest.raises(RuntimeError, match="refusing overwrite"):
        run_demo(partial_dir)
    assert partial.read_text(encoding="utf-8") == "preserve me too"


def test_connected_case_preserves_per_signal_evidence_details() -> None:
    common = {
        "run_id": "RUN-X",
        "snapshot_id": "SNAP-X",
        "rule_version_id": "commission-integrity-v1",
        "control_objective": "CO-02",
        "bucket": "potential_exception",
        "severity": "medium",
        "review_status": "pending_human_review",
    }
    signals = [
        {
            **common,
            "signal_id": "SIG-1",
            "rule_branch": "B2",
            "affiliate_id": "A1990",
            "affiliate_id_a": "A1990",
            "affiliate_id_b": "A1990",
            "accrual_period": "P1",
            "total_amount_minor": 1_100_000,
            "first_payment_date": "2026-01-01",
            "last_payment_date": "2026-01-02",
            "source_row_ids": ["CC1", "CC3"],
        },
        {
            **common,
            "signal_id": "SIG-2",
            "rule_branch": "B1",
            "severity": "high",
            "affiliate_id": "A1990 / A1991",
            "affiliate_id_a": "A1990",
            "affiliate_id_b": "A1991",
            "accrual_period": "P1 / P2",
            "source_row_ids": ["CC1", "CC2"],
        },
        {
            **common,
            "signal_id": "SIG-3",
            "rule_branch": "B2",
            "affiliate_id": "A1991",
            "affiliate_id_a": "A1991",
            "affiliate_id_b": "A1991",
            "accrual_period": "P2",
            "total_amount_minor": 1_300_000,
            "first_payment_date": "2026-02-01",
            "last_payment_date": "2026-02-02",
            "source_row_ids": ["CC2", "CC4"],
        },
    ]
    case = consolidate_review_cases(signals)[0]
    assert case["affected_affiliate_ids"] == ["A1990", "A1991"]
    assert case["affiliate_id"] == "multiple"
    assert case["accrual_period"] == "multiple"
    assert case["total_amount_minor"] is None
    assert len(case["signal_details"]) == 3
    assert {
        tuple(detail["source_row_ids"]) for detail in case["signal_details"]
    } == {("CC1", "CC3"), ("CC1", "CC2"), ("CC2", "CC4")}
    assert _affected_entity_ids([case]) == {"A1990", "A1991"}


def test_affected_entity_metric_does_not_collapse_multiple_cases() -> None:
    cases = [
        {
            "bucket": "potential_exception",
            "control_objective": "CO-02",
            "affiliate_id": "multiple",
            "affected_affiliate_ids": ["A1", "A2"],
        },
        {
            "bucket": "potential_exception",
            "control_objective": "CO-02",
            "affiliate_id": "multiple",
            "affected_affiliate_ids": ["A3", "A4"],
        },
        {
            "bucket": "potential_exception",
            "control_objective": "CO-01",
            "wallet_id": "W1",
        },
    ]
    assert _affected_entity_ids(cases) == {"A1", "A2", "A3", "A4", "W1"}
