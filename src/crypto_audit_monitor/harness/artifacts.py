from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .canonical import sha256_file


def build_artifact_manifest(
    output_dir: Path,
    files: Iterable[Path],
) -> dict[str, Any]:
    artifacts = {
        path.relative_to(output_dir).as_posix(): sha256_file(path)
        for path in sorted(files, key=lambda item: item.as_posix())
    }
    return {
        "schema_version": 1,
        "hash_algorithm": "sha256",
        "artifacts": artifacts,
        "integrity_boundary": (
            "Self-attested local artifact hashes. This manifest is not an "
            "external signature, timestamp or immutable record."
        ),
    }


def verify_artifact_manifest(
    output_dir: Path,
    manifest: dict[str, Any],
    *,
    required_artifacts: set[str] | None = None,
) -> bool:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("artifact manifest is empty")
    if required_artifacts is not None and set(artifacts) != required_artifacts:
        raise ValueError("artifact manifest does not match the required set")
    for relative_path, expected_hash in artifacts.items():
        path = output_dir / relative_path
        if not path.is_file():
            raise ValueError(f"artifact is missing: {relative_path}")
        if sha256_file(path) != expected_hash:
            raise ValueError(f"artifact hash mismatch: {relative_path}")
    return True
