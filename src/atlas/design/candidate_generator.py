"""Generate interpretable near-pocket alanine probes after validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from Bio.PDB import PDBParser
from Bio.SeqUtils import seq1

from atlas.validation.validation_gate import ValidationResult, require_validation_pass


PROTECTED_POSITIONS = frozenset({91, 95, 96, 99, 122, 126, 172})
EXCLUDED_WILDTYPES = frozenset({"A", "C", "G", "P", "X"})


@dataclass(frozen=True)
class Candidate:
    variant_id: str
    mutation_set: str
    position: int
    wildtype: str
    mutant: str
    distance_to_focus_a: float
    rationale: str

    def row(self) -> dict[str, object]:
        return asdict(self)


def generate_candidates(
    pdb_path: str | Path,
    validation: ValidationResult,
    *,
    cutoff_a: float = 8.0,
    max_candidates: int = 24,
) -> tuple[Candidate, ...]:
    require_validation_pass(validation)
    structure = PDBParser(QUIET=True).get_structure("candidates", Path(pdb_path))
    model = structure[0]
    focus = [atom for atom in model["B"].get_atoms()]
    focus.extend(
        atom
        for chain in model
        for atom in chain.get_atoms()
        if atom.element and atom.element.upper() == "ZN"
    )
    focus_coords = np.asarray([atom.coord for atom in focus], dtype=float)
    candidates: list[Candidate] = []
    for residue in model["A"]:
        position = residue.id[1]
        wildtype = seq1(residue.resname, custom_map={"MSE": "M"})
        if position in PROTECTED_POSITIONS or wildtype in EXCLUDED_WILDTYPES:
            continue
        coords = np.asarray([atom.coord for atom in residue if atom.element != "H"])
        distance = float(
            np.linalg.norm(coords[:, None, :] - focus_coords[None, :, :], axis=2).min()
        )
        if distance <= cutoff_a:
            label = f"{wildtype}{position}A"
            candidates.append(
                Candidate(
                    label,
                    label,
                    position,
                    wildtype,
                    "A",
                    distance,
                    "Second-shell alanine probe within 8 Å of resolved substrate or zinc; "
                    "catalytic, coordinating, benchmark, Gly/Pro, and Cys sites excluded.",
                )
            )
    ordered = sorted(candidates, key=lambda item: (item.distance_to_focus_a, item.position))
    return tuple(ordered[:max_candidates])


def candidate_table(candidates: tuple[Candidate, ...]) -> pd.DataFrame:
    return pd.DataFrame([candidate.row() for candidate in candidates])
