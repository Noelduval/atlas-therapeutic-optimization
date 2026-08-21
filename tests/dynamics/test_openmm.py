from __future__ import annotations

from pathlib import Path

import pytest
from Bio.PDB import PDBParser

from atlas.dynamics.models import DynamicsConfig
from atlas.dynamics.openmm_minimize import _load_openmm, _prepare_system, minimize_variant
from atlas.dynamics.openmm_short_md import run_short_md
from atlas.structure.reconstruct import reconstruct_active_like


def test_minimization_dependency_failure_has_no_snapshots(
    tmp_path: Path, monkeypatch
) -> None:
    def missing():
        raise ImportError("openmm unavailable")

    monkeypatch.setattr("atlas.dynamics.openmm_minimize._load_openmm", missing)
    result = minimize_variant(
        tmp_path / "variant.pdb", tmp_path / "out", DynamicsConfig()
    )
    assert result.status == "skipped_dependency_unavailable"
    assert result.snapshot_records == ()
    assert not result.output_pdb
    assert "openmm unavailable" in result.warning


def test_parameterization_failure_has_no_fake_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "atlas.dynamics.openmm_minimize._load_openmm", lambda: object()
    )

    def unparameterized(*args, **kwargs):
        raise ValueError("No template found for residue ZN")

    monkeypatch.setattr(
        "atlas.dynamics.openmm_minimize._prepare_system", unparameterized
    )
    result = minimize_variant(
        tmp_path / "variant.pdb", tmp_path / "out", DynamicsConfig()
    )
    assert result.status == "skipped_unparameterized_system"
    assert result.snapshot_records == ()
    assert not (tmp_path / "out" / "minimized.pdb").exists()
    assert "No template" in result.warning


def test_short_md_propagates_minimization_skip(tmp_path: Path, monkeypatch) -> None:
    from atlas.dynamics.models import DynamicsResult

    skipped = DynamicsResult(
        status="skipped_unparameterized_system",
        output_pdb=None,
        snapshot_records=(),
        warning="parameterization failed",
    )
    monkeypatch.setattr(
        "atlas.dynamics.openmm_short_md.minimize_variant", lambda *args: skipped
    )
    result = run_short_md(tmp_path / "variant.pdb", tmp_path / "out", DynamicsConfig())
    assert result == skipped
    assert not list(tmp_path.glob("**/*.pdb"))


def test_committed_coordinate_fragments_parameterize_without_new_heavy_atoms(
    tmp_path: Path,
) -> None:
    pytest.importorskip("openmm")
    pdb_path = tmp_path / "active_like.pdb"
    reconstruct_active_like(
        Path("data/23WN.cif"), pdb_path, tmp_path / "numbering.csv"
    )
    source = PDBParser(QUIET=True).get_structure("source", pdb_path)
    source_heavy = sum(1 for atom in source.get_atoms() if atom.element != "H")
    source_residues = sum(1 for _ in source.get_residues())

    bundle = _load_openmm()
    modeller, system = _prepare_system(pdb_path, DynamicsConfig(), bundle)
    topology_heavy = sum(
        1
        for atom in modeller.topology.atoms()
        if atom.element is not None and atom.element.symbol != "H"
    )
    assert topology_heavy == source_heavy
    assert modeller.topology.getNumResidues() == source_residues
    assert system.getNumParticles() == modeller.topology.getNumAtoms()
