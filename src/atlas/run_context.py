"""Provenance-bound run directories and safe checkpoint reuse."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Protocol

from atlas.stability.thermompnn_d_runner import THERMOMPNN_D_REVISION
from atlas.stability.thermompnn_runner import THERMOMPNN_REVISION


VALIDATION_POLICY = "atlas-v1-fixed-gate-2026-08-19"


class RunContextError(RuntimeError):
    """A checkpoint cannot be reused without risking stale scientific output."""


class RunConfig(Protocol):
    input_structure: Path
    output_root: Path
    run_id: str | None
    dynamics_mode: str
    resume: bool


@dataclass(frozen=True)
class RunContext:
    schema_version: int
    atlas_commit: str
    input_sha256: str
    thermompnn_commit: str
    thermompnn_d_commit: str
    dynamics_mode: str
    validation_policy: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atlas_commit() -> str:
    repository = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    revision = completed.stdout.strip()
    if completed.returncode or len(revision) != 40:
        raise RunContextError(
            f"Atlas commit cannot be resolved at {repository}; run from a Git checkout"
        )
    return revision


def build_run_context(config: RunConfig) -> RunContext:
    input_path = Path(config.input_structure)
    if not input_path.is_file():
        raise FileNotFoundError(f"23WN input does not exist: {input_path}")
    return RunContext(
        schema_version=1,
        atlas_commit=_atlas_commit(),
        input_sha256=_sha256(input_path),
        thermompnn_commit=THERMOMPNN_REVISION,
        thermompnn_d_commit=THERMOMPNN_D_REVISION,
        dynamics_mode=config.dynamics_mode,
        validation_policy=VALIDATION_POLICY,
    )


def prepare_run_directory(config: RunConfig, context: RunContext | None = None) -> Path:
    """Create or safely reopen a run directory with an exact context match."""
    expected = context or build_run_context(config)
    if config.resume and not config.run_id:
        raise RunContextError("--resume requires an explicit run_id")
    run_id = config.run_id or datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    destination = Path(config.output_root) / run_id
    context_path = destination / "run_context.json"
    if not destination.exists():
        if config.resume:
            raise RunContextError(f"Cannot resume missing run directory: {destination}")
        destination.mkdir(parents=True)
        context_path.write_text(
            json.dumps(asdict(expected), indent=2, sort_keys=True) + "\n"
        )
        return destination
    if not config.resume:
        raise FileExistsError(f"Atlas never overwrites a run directory: {destination}")
    if not context_path.is_file():
        raise RunContextError(f"Existing run has no context record: {context_path}")
    try:
        recorded = json.loads(context_path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise RunContextError(f"Run context is unreadable: {context_path}: {exc}") from exc
    current = asdict(expected)
    mismatches = [
        key for key, value in current.items() if recorded.get(key) != value
    ]
    if mismatches:
        detail = ", ".join(
            f"{key}: recorded={recorded.get(key)!r}, current={current[key]!r}"
            for key in mismatches
        )
        raise RunContextError(f"Refusing stale checkpoint reuse ({detail})")
    return destination
