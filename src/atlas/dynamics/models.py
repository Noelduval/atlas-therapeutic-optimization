"""Typed OpenMM configuration and results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DynamicsConfig:
    temperature_k: float = 300.0
    timestep_fs: float = 2.0
    md_steps: int = 5_000
    restraint_k_kj_mol_nm2: float = 1_000.0
    zinc_restraint_k_kj_mol_nm2: float = 2_000.0
    minimization_tolerance_kj_mol_nm: float = 10.0
    minimization_max_iterations: int = 2_000
    random_seed: int = 622


@dataclass(frozen=True)
class DynamicsResult:
    status: str
    output_pdb: Path | None
    snapshot_records: tuple[dict[str, float | int | str], ...]
    warning: str = ""
