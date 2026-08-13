"""Load source-backed Atlas Challenge assets from the repository data registry."""

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CHALLENGE_DATA_DIR = PROJECT_ROOT / "data" / "atlas_challenge"


def file_sha256(path: str | Path) -> str:
    """Return the lowercase SHA-256 checksum for a local asset."""
    digest = sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_yaml(name: str) -> dict[str, Any]:
    path = CHALLENGE_DATA_DIR / name
    content = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        raise ValueError(f"Challenge asset {path} must contain a mapping")
    return content


def load_asset_manifest() -> dict[str, Any]:
    """Load the visible source and file-provenance manifest."""
    return deepcopy(_load_yaml("manifest.yaml"))


def load_sequence_assets() -> tuple[dict[str, Any], ...]:
    """Load visible sequence availability records, normalizing exact sequences."""
    document = _load_yaml("sequences.yaml")
    records = deepcopy(document.get("sequences", []))
    for record in records:
        if record.get("sequence") is not None:
            record["sequence"] = "".join(record["sequence"].split()).upper()
    return tuple(records)


def load_hidden_label_asset() -> dict[str, Any]:
    """Load measured labels. Call only after a persisted lock is verified."""
    return deepcopy(_load_yaml("hidden_labels.yaml"))
