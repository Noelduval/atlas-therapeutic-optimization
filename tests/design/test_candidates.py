from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from atlas.design.candidate_generator import generate_candidates
from atlas.design.rank_candidates import rank_candidates
from atlas.structure.reconstruct import reconstruct_active_like
from atlas.validation.validation_gate import ValidationGateError, ValidationResult


def _result(passed: bool) -> ValidationResult:
    return ValidationResult(
        passed=passed,
        table=pd.DataFrame(),
        reasons=() if passed else ("gate failed",),
        dynamics_status="unavailable",
    )


def test_candidate_generation_requires_passed_gate(tmp_path: Path) -> None:
    pdb = tmp_path / "active_like.pdb"
    reconstruct_active_like(
        Path("data/23WN.cif"), pdb, tmp_path / "map.csv"
    )
    with pytest.raises(ValidationGateError):
        generate_candidates(pdb, _result(False))


def test_candidates_are_near_pocket_and_exclude_protected_sites(tmp_path: Path) -> None:
    pdb = tmp_path / "active_like.pdb"
    reconstruct_active_like(
        Path("data/23WN.cif"), pdb, tmp_path / "map.csv"
    )
    candidates = generate_candidates(pdb, _result(True))
    assert candidates
    protected = {91, 95, 96, 99, 122, 126, 172}
    assert not protected.intersection(candidate.position for candidate in candidates)
    assert all(candidate.distance_to_focus_a <= 8.0 for candidate in candidates)
    assert all(candidate.mutant == "A" for candidate in candidates)


def test_ranking_requires_real_score_for_every_candidate() -> None:
    candidates = pd.DataFrame(
        [
            {"variant_id": "L10A", "mutation_set": "L10A"},
            {"variant_id": "V11A", "mutation_set": "V11A"},
        ]
    )
    stability = pd.DataFrame(
        [{"variant_id": "L10A", "predicted_ddg_or_score": -0.3}]
    )
    geometry = pd.DataFrame(
        [
            {"variant_id": "L10A", "geometry_complete": True, "active_site_rmsd_a": 0.2},
            {"variant_id": "V11A", "geometry_complete": True, "active_site_rmsd_a": 0.1},
        ]
    )
    with pytest.raises(ValueError, match="V11A"):
        rank_candidates(candidates, stability, geometry)
