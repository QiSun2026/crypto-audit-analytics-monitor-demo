from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .canonical import canonical_json, sha256_bytes, stable_id, write_canonical_json


REQUIRED_REVIEW_FIELDS = {
    "exception_id",
    "run_id",
    "snapshot_id",
    "reviewer_id",
    "review_timestamp_utc",
    "question_presented",
    "conclusion",
    "disposition",
    "rationale",
    "evidence_viewed",
    "identity_status",
    "ai_assistance_used",
}

ALLOWED_REVIEW_CONCLUSIONS = {
    "supported_explanation",
    "more_evidence_required",
    "control_exception_confirmed",
    "data_quality_issue",
}

ALLOWED_DISPOSITIONS = {
    "keep_open",
    "close_with_explanation",
    "escalate_for_investigation",
}

GENESIS_HASH = "0" * 64


def read_review_log(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _chain_manifest_path(path: Path) -> Path:
    return path.with_name("review_chain_manifest.json")


def _load_exception_queue(path: Path) -> dict[str, dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return {row["exception_id"]: row for row in rows}


def _parse_review_timestamp(value: Any) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError("review timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValueError("review timestamp must be timezone-aware UTC")
    return parsed


def _validate_review_semantics(
    record: dict[str, Any],
    queue: dict[str, dict[str, Any]],
    prior_records: list[dict[str, Any]],
) -> None:
    missing = sorted(
        field
        for field in REQUIRED_REVIEW_FIELDS
        if record.get(field) is None or record.get(field) == ""
    )
    if missing:
        raise ValueError(f"missing review fields: {', '.join(missing)}")
    if record["identity_status"] != "self_attested_prototype":
        raise ValueError("prototype reviewer identity must be explicitly self-attested")
    timestamp = _parse_review_timestamp(record["review_timestamp_utc"])
    if record["conclusion"] not in ALLOWED_REVIEW_CONCLUSIONS:
        raise ValueError("review conclusion is not allowed")
    if record["disposition"] not in ALLOWED_DISPOSITIONS:
        raise ValueError("review disposition is not allowed")
    if not isinstance(record["ai_assistance_used"], bool):
        raise ValueError("ai_assistance_used must be explicitly true or false")
    if not isinstance(record["evidence_viewed"], list) or not record["evidence_viewed"]:
        raise ValueError("review evidence_viewed must contain source rows")

    exception = queue.get(record["exception_id"])
    if exception is None:
        raise ValueError("review references an unknown exception")
    if record["run_id"] != exception["run_id"]:
        raise ValueError("review run_id does not match the exception")
    if record["snapshot_id"] != exception["snapshot_id"]:
        raise ValueError("review snapshot_id does not match the exception")
    if not set(record["evidence_viewed"]) <= set(exception["source_row_ids"]):
        raise ValueError("review evidence is outside exception lineage")
    detection_timestamp = _parse_review_timestamp(
        exception["detection_timestamp_utc"]
    )
    if timestamp < detection_timestamp:
        raise ValueError("review timestamp cannot predate exception detection")

    prior_by_id = {item["review_id"]: item for item in prior_records}
    review_id = record.get("review_id")
    if review_id is not None and review_id in prior_by_id:
        raise ValueError("review record already exists; records cannot be overwritten")
    if prior_records:
        previous_timestamp = _parse_review_timestamp(
            prior_records[-1]["review_timestamp_utc"]
        )
        if timestamp <= previous_timestamp:
            raise ValueError("review timestamps must increase monotonically")

    supersedes = record.get("supersedes_review_id")
    if supersedes is None:
        return
    superseded = prior_by_id.get(supersedes)
    if superseded is None:
        raise ValueError("superseded review record does not exist")
    for field in ("exception_id", "run_id", "snapshot_id"):
        if record[field] != superseded[field]:
            raise ValueError(
                f"correction must match superseded review {field}"
            )
    if timestamp <= _parse_review_timestamp(superseded["review_timestamp_utc"]):
        raise ValueError("correction must postdate the superseded review")


def verify_review_chain(
    path: Path, exception_queue_path: Path
) -> dict[str, Any]:
    records = read_review_log(path)
    queue = _load_exception_queue(exception_queue_path)
    previous = GENESIS_HASH
    prior_records: list[dict[str, Any]] = []
    for record in records:
        stored_hash = record.get("record_sha256")
        if not stored_hash:
            raise ValueError("review record hash is missing")
        payload = dict(record)
        payload.pop("record_sha256")
        if payload.get("previous_record_sha256") != previous:
            raise ValueError("review chain previous hash mismatch")
        actual_hash = sha256_bytes(canonical_json(payload))
        if actual_hash != stored_hash:
            raise ValueError("review record hash mismatch")
        _validate_review_semantics(record, queue, prior_records)
        prior_records.append(record)
        previous = stored_hash
    manifest = {
        "schema_version": 1,
        "record_count": len(records),
        "head_record_sha256": previous,
        "chain_status": "valid",
        "mutable_log_note": (
            "Review records are append-only within this Prototype helper. "
            "The chain is tamper-evident, not externally immutable."
        ),
    }
    existing_manifest_path = _chain_manifest_path(path)
    if existing_manifest_path.exists():
        stored = json.loads(existing_manifest_path.read_text(encoding="utf-8"))
        if (
            stored.get("record_count") != manifest["record_count"]
            or stored.get("head_record_sha256") != manifest["head_record_sha256"]
        ):
            raise ValueError("review chain manifest mismatch")
    return manifest


def initialize_review_chain(path: Path) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(b"")
    manifest = {
        "schema_version": 1,
        "record_count": 0,
        "head_record_sha256": GENESIS_HASH,
        "chain_status": "valid",
        "mutable_log_note": (
            "Review records are append-only within this Prototype helper. "
            "The chain is tamper-evident, not externally immutable."
        ),
    }
    if not _chain_manifest_path(path).exists():
        write_canonical_json(_chain_manifest_path(path), manifest)
    return manifest


def append_review_record(
    path: Path,
    record: dict[str, Any],
    exception_queue_path: Path,
) -> dict[str, Any]:
    queue = _load_exception_queue(exception_queue_path)

    if not path.exists():
        initialize_review_chain(path)
    verify_review_chain(path, exception_queue_path)
    existing = read_review_log(path)
    supplied = dict(record)
    supplied.setdefault(
        "review_id",
        f"REV-{stable_id(canonical_json(record).decode('utf-8'))}",
    )
    _validate_review_semantics(supplied, queue, existing)
    supplied["previous_record_sha256"] = (
        existing[-1]["record_sha256"] if existing else GENESIS_HASH
    )
    supplied["record_sha256"] = sha256_bytes(canonical_json(supplied))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write(canonical_json(supplied))
    manifest = {
        "schema_version": 1,
        "record_count": len(existing) + 1,
        "head_record_sha256": supplied["record_sha256"],
        "chain_status": "valid",
        "mutable_log_note": (
            "Review records are append-only within this Prototype helper. "
            "The chain is tamper-evident, not externally immutable."
        ),
    }
    write_canonical_json(_chain_manifest_path(path), manifest)
    verify_review_chain(path, exception_queue_path)
    return supplied
