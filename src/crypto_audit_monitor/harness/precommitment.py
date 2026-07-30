from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .canonical import sha256_file


def load_registered_precommitment(
    root: Path,
    relative_path: str,
) -> dict[str, Any]:
    path = root / relative_path
    config = json.loads(path.read_text(encoding="utf-8"))
    registry = json.loads(
        (root / "config" / "precommitment_registry.json").read_text(
            encoding="utf-8"
        )
    )
    version_id = config["configuration_version_id"]
    expected_hash = registry["configurations"].get(version_id)
    if expected_hash is None:
        raise ValueError("configuration version is not registered")
    if sha256_file(path) != expected_hash:
        raise ValueError("pre-commitment configuration hash mismatch")

    committed = datetime.fromisoformat(
        config["committed_at_utc"].replace("Z", "+00:00")
    )
    run_at = datetime.fromisoformat(
        config["logical_run_at_utc"].replace("Z", "+00:00")
    )
    if committed >= run_at:
        raise ValueError("pre-commitment must predate the logical run")

    declared_rules = (
        list(config["rules"].values())
        if "rules" in config
        else [config["rule"]]
    )
    for rule in declared_rules:
        actual = sha256_file(root / rule["sql_file"])
        if actual != rule["sql_sha256"]:
            raise ValueError(f"SQL hash mismatch for {rule['rule_version_id']}")
    return config


def verify_rule_override(
    config: dict[str, Any],
    sql_path: Path,
) -> None:
    rule = config["rule"]
    if sha256_file(sql_path) != rule["sql_sha256"]:
        raise ValueError(f"SQL hash mismatch for {rule['rule_version_id']}")
