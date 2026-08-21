"""Shared contracts for stability-only model results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Callable, Sequence

import pandas as pd


NORMALIZED_COLUMNS = [
    "variant_id",
    "mutation_set",
    "dp622_numbering",
    "deposited_numbering",
    "model_used",
    "predicted_ddg_or_score",
    "interpretation",
    "warnings",
]


class DependencyUnavailableError(RuntimeError):
    """A required external scientific dependency is absent."""


class ScientificOutputError(RuntimeError):
    """An external predictor failed or produced unverifiable output."""


@dataclass(frozen=True)
class StabilityVariant:
    """A mutation request in reconstructed and deposited numbering."""

    variant_id: str
    mutation_set: str
    deposited_numbering: str

    @property
    def dp622_numbering(self) -> str:
        return self.mutation_set


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]


def default_command_runner(
    command: Sequence[str], *, cwd: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def require_repository(repo: Path, script: str, name: str) -> Path:
    script_path = repo / script
    if not repo.is_dir() or not script_path.is_file():
        raise DependencyUnavailableError(
            f"{name} repository is unavailable or incomplete at {repo}. "
            "Clone the pinned official repository documented in docs/reproduction.md."
        )
    return script_path


def require_revision(repo: Path, expected: str, name: str) -> None:
    """Reject a wrong Git checkout while permitting exported source archives."""
    if not (repo / ".git").exists():
        return
    completed = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    actual = completed.stdout.strip()
    if completed.returncode or actual != expected:
        raise DependencyUnavailableError(
            f"{name} must be checked out at {expected}; found {actual or 'unknown revision'}"
        )


def require_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise ScientificOutputError(
            f"{name} output is missing required columns: {sorted(missing)}"
        )


def interpretation(ddg: float) -> str:
    trend = "stabilizing" if ddg < 0 else "destabilizing" if ddg > 0 else "neutral"
    return f"Predicted {trend} stability trend only; this is not a catalytic-activity prediction."


def normalized_row(
    variant: StabilityVariant, model: str, ddg: float, warning: str = ""
) -> dict[str, object]:
    return {
        "variant_id": variant.variant_id,
        "mutation_set": variant.mutation_set,
        "dp622_numbering": variant.dp622_numbering,
        "deposited_numbering": variant.deposited_numbering,
        "model_used": model,
        "predicted_ddg_or_score": float(ddg),
        "interpretation": interpretation(float(ddg)),
        "warnings": warning,
    }


def normalized_frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=NORMALIZED_COLUMNS)
