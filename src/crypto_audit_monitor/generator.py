from __future__ import annotations

import csv
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

from .integrity import sha256_file, stable_id, write_canonical_json


TABLE_FIELDS = {
    "employee": ["employee_id", "has_affiliate_program_access"],
    "affiliate": ["affiliate_id", "status"],
    "payout_wallet": ["wallet_id", "address_hash", "wallet_type"],
    "entity_wallet_link": [
        "link_id",
        "entity_type",
        "entity_id",
        "wallet_id",
        "valid_from",
        "valid_to",
    ],
    "commission_payment": [
        "payment_id",
        "affiliate_id",
        "accrual_period",
        "amount_minor",
        "payment_date",
        "source_ref",
        "payment_status",
    ],
}


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _wallet_for_entity(entity_type: str, entity_id: str) -> str:
    return f"W_{entity_type[0].upper()}_{entity_id}"


def build_rows(seed: int = 20260730) -> tuple[dict[str, list[dict]], dict]:
    rng = random.Random(seed)
    employees = [
        {
            "employee_id": f"E{i:04d}",
            "has_affiliate_program_access": 1 if i <= 120 else 0,
        }
        for i in range(1, 501)
    ]
    affiliates = [
        {"affiliate_id": f"A{i:04d}", "status": "active"}
        for i in range(1, 2001)
    ]

    wallet_override = {
        ("employee", "E0001"): ("W_CASE_A1", "self_custody", "2026-01-01", ""),
        ("affiliate", "A0001"): ("W_CASE_A1", "self_custody", "2026-02-01", ""),
        ("affiliate", "A0002"): ("W_CASE_A2", "self_custody", "2026-01-01", ""),
        ("affiliate", "A0003"): ("W_CASE_A2", "self_custody", "2026-01-01", ""),
        ("affiliate", "A0004"): ("W_CASE_A2", "self_custody", "2026-01-01", ""),
        ("employee", "E0002"): ("W_NEAR_A1", "self_custody", "2025-01-01", "2025-06-30"),
        ("affiliate", "A0005"): ("W_NEAR_A1", "self_custody", "2025-07-01", ""),
        ("employee", "E0003"): ("W_EXPECTED_TREASURY", "internal_treasury", "2026-01-01", ""),
        ("employee", "E0004"): ("W_EXPECTED_TREASURY", "internal_treasury", "2026-01-01", ""),
    }
    for i in range(10, 50):
        wallet_override[("affiliate", f"A{i:04d}")] = (
            "W_EXPECTED_EXCHANGE",
            "exchange_deposit",
            "2026-01-01",
            "",
        )

    links: list[dict] = []
    wallets_by_id: dict[str, dict] = {}
    entities = [
        ("employee", row["employee_id"]) for row in employees
    ] + [("affiliate", row["affiliate_id"]) for row in affiliates]
    for entity_type, entity_id in entities:
        wallet_id, wallet_type, valid_from, valid_to = wallet_override.get(
            (entity_type, entity_id),
            (
                _wallet_for_entity(entity_type, entity_id),
                "self_custody",
                "2026-01-01",
                "",
            ),
        )
        wallets_by_id.setdefault(
            wallet_id,
            {
                "wallet_id": wallet_id,
                "address_hash": stable_id("fabricated-wallet", wallet_id, length=24),
                "wallet_type": wallet_type,
            },
        )
        links.append(
            {
                "link_id": f"L_{entity_type[0].upper()}_{entity_id}",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "wallet_id": wallet_id,
                "valid_from": valid_from,
                "valid_to": valid_to,
            }
        )

    payments: list[dict] = []
    months = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
    for affiliate in affiliates:
        affiliate_id = affiliate["affiliate_id"]
        for month_index, month in enumerate(months, start=1):
            amount = rng.randrange(120_000, 850_000, 10_000)
            payments.append(
                {
                    "payment_id": f"P_{affiliate_id}_{month_index}",
                    "affiliate_id": affiliate_id,
                    "accrual_period": month,
                    "amount_minor": amount,
                    "payment_date": f"2026-{month_index:02d}-15",
                    "source_ref": f"SRC_{affiliate_id}_{month}",
                    "payment_status": "completed",
                }
            )

    by_id = {row["payment_id"]: row for row in payments}

    def set_payment(affiliate_id: str, index: int, **changes: object) -> str:
        payment_id = f"P_{affiliate_id}_{index}"
        by_id[payment_id].update(changes)
        return payment_id

    set_payment(
        "A0100",
        1,
        accrual_period="2026-Q1",
        amount_minor=750_000,
        payment_date="2026-03-01",
        source_ref="SRC_T_B1",
    )
    set_payment(
        "A0100",
        2,
        accrual_period="2026-Q1",
        amount_minor=750_000,
        payment_date="2026-03-02",
        source_ref="SRC_T_B1",
    )
    for idx, day in zip((1, 2, 3), (1, 3, 5), strict=True):
        set_payment(
            "A0101",
            idx,
            accrual_period="2026-Q1",
            amount_minor=400_000,
            payment_date=f"2026-03-{day:02d}",
            source_ref=f"SRC_T_B2_{idx}",
        )
    for idx, day in zip((1, 2), (1, 8), strict=True):
        set_payment(
            "A0102",
            idx,
            accrual_period="2026-Q1",
            amount_minor=500_000,
            payment_date=f"2026-03-{day:02d}",
            source_ref=f"SRC_T_B3_{idx}",
        )
    set_payment(
        "A0103",
        1,
        accrual_period="2026-Q1",
        amount_minor=700_000,
        payment_date="2026-03-01",
        source_ref="SRC_F_B1",
        payment_status="completed",
    )
    set_payment(
        "A0103",
        2,
        accrual_period="2026-Q1",
        amount_minor=700_000,
        payment_date="2026-03-02",
        source_ref="SRC_F_B1",
        payment_status="reversed",
    )
    set_payment(
        "A0104",
        1,
        accrual_period="2026-Q1",
        amount_minor=600_000,
        payment_date="2026-03-01",
        source_ref="SRC_F_B2_A",
    )
    set_payment(
        "A0104",
        2,
        accrual_period="2026-Q1",
        amount_minor=500_000,
        payment_date="2026-03-04",
        source_ref="SRC_F_B2_B",
    )
    set_payment(
        "A0105",
        1,
        accrual_period="2026-Q1",
        amount_minor=600_000,
        payment_date="2026-03-01",
        source_ref="SRC_F_B3_A",
    )
    set_payment(
        "A0105",
        2,
        accrual_period="2026-Q1",
        amount_minor=500_000,
        payment_date="2026-03-10",
        source_ref="SRC_F_B3_B",
    )

    truth = {
        "positive_controls": [
            {"case_id": "T-A1", "rule_branch": "A", "match": {"wallet_id": "W_CASE_A1"}},
            {"case_id": "T-A2", "rule_branch": "A", "match": {"wallet_id": "W_CASE_A2"}},
            {"case_id": "T-B1", "rule_branch": "B1", "match": {"affiliate_id": "A0100"}},
            {"case_id": "T-B2", "rule_branch": "B2", "match": {"affiliate_id": "A0101"}},
            {"case_id": "T-B3", "rule_branch": "B2", "match": {"affiliate_id": "A0102"}},
        ],
        "negative_controls": [
            {"case_id": "N-A1", "rule_branch": "A", "match": {"wallet_id": "W_NEAR_A1"}},
            {"case_id": "N-B1", "rule_branch": "B1", "match": {"affiliate_id": "A0103"}},
            {"case_id": "N-B3", "rule_branch": "B2", "match": {"affiliate_id": "A0105"}},
        ],
        "designed_false_positives": [
            {"case_id": "F-B2", "rule_branch": "B2", "match": {"affiliate_id": "A0104"}}
        ],
        "expected_shared": ["W_EXPECTED_EXCHANGE", "W_EXPECTED_TREASURY"],
    }

    return (
        {
            "employee": employees,
            "affiliate": affiliates,
            "payout_wallet": sorted(wallets_by_id.values(), key=lambda row: row["wallet_id"]),
            "entity_wallet_link": sorted(links, key=lambda row: row["link_id"]),
            "commission_payment": sorted(payments, key=lambda row: row["payment_id"]),
        },
        truth,
    )


def generate_snapshot(output_dir: Path, seed: int = 20260730) -> dict:
    rows_by_table, truth = build_rows(seed)
    source_dir = output_dir / "source_data"
    source_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict] = {}
    for table, rows in rows_by_table.items():
        path = source_dir / f"{table}.csv"
        _write_csv(path, TABLE_FIELDS[table], rows)
        files[table] = {
            "file": str(path.relative_to(output_dir)).replace("\\", "/"),
            "row_count": len(rows),
            "sha256": sha256_file(path),
        }
    payments = rows_by_table["commission_payment"]
    manifest = {
        "schema_version": 1,
        "synthetic_only": True,
        "generator_seed": seed,
        "tables": files,
        "validation_fixture": {"file": "ground_truth.json", "sha256": None},
        "control_totals": {
            "commission_amount_minor": sum(int(row["amount_minor"]) for row in payments),
            "distinct_wallets": len(rows_by_table["payout_wallet"]),
            "distinct_affiliates": len(rows_by_table["affiliate"]),
        },
    }
    write_canonical_json(output_dir / "ground_truth.json", truth)
    manifest["validation_fixture"]["sha256"] = sha256_file(
        output_dir / "ground_truth.json"
    )
    write_canonical_json(output_dir / "snapshot_manifest.json", manifest)
    return manifest


def load_snapshot_to_sqlite(output_dir: Path, db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(
            """
            CREATE TABLE employee (
                employee_id TEXT PRIMARY KEY,
                has_affiliate_program_access INTEGER NOT NULL
            );
            CREATE TABLE affiliate (
                affiliate_id TEXT PRIMARY KEY,
                status TEXT NOT NULL
            );
            CREATE TABLE payout_wallet (
                wallet_id TEXT PRIMARY KEY,
                address_hash TEXT NOT NULL,
                wallet_type TEXT NOT NULL
            );
            CREATE TABLE entity_wallet_link (
                link_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                wallet_id TEXT NOT NULL,
                valid_from TEXT NOT NULL,
                valid_to TEXT
            );
            CREATE TABLE commission_payment (
                payment_id TEXT PRIMARY KEY,
                affiliate_id TEXT NOT NULL,
                accrual_period TEXT NOT NULL,
                amount_minor INTEGER NOT NULL,
                payment_date TEXT NOT NULL,
                source_ref TEXT NOT NULL,
                payment_status TEXT NOT NULL
            );
            """
        )
        for table, fields in TABLE_FIELDS.items():
            path = output_dir / "source_data" / f"{table}.csv"
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            placeholders = ",".join("?" for _ in fields)
            columns = ",".join(fields)
            connection.executemany(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                [[row[field] or None for field in fields] for row in rows],
            )
        connection.commit()
    finally:
        connection.close()
