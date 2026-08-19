from pathlib import Path

import pandas as pd
from Bio.PDB import PDBParser

from atlas.structure.mutate import KNOWN_VARIANTS, build_known_mutants
from atlas.structure.reconstruct import reconstruct_active_like


SOURCE = Path(__file__).parents[2] / "data" / "23WN.cif"


def test_known_mutants_have_expected_sidechains_and_manifest(tmp_path) -> None:
    reconstructed = tmp_path / "reconstructed.pdb"
    reconstruct_active_like(SOURCE, reconstructed, tmp_path / "map.csv")

    manifest = build_known_mutants(reconstructed, tmp_path / "known")

    assert manifest["variant_id"].tolist() == [
        "WT",
        "Y91F",
        "D126A",
        "H172A",
        "Y91F_D126A",
    ]
    assert manifest["dp622_numbering"].tolist() == [
        "WT",
        "Y91F",
        "D126A",
        "H172A",
        "Y91F/D126A",
    ]
    assert manifest["deposited_numbering"].tolist() == [
        "Q120E reconstruction",
        "Y115F",
        "D150A",
        "H196A",
        "Y115F/D150A",
    ]
    assert manifest["evidence_class"].eq("computational_reconstruction").all()

    parser = PDBParser(QUIET=True)
    y91f = parser.get_structure("y91f", manifest.iloc[1]["pdb_path"])[0]["A"][91]
    assert y91f.resname == "PHE"
    assert "OH" not in y91f
    d126a = parser.get_structure("d126a", manifest.iloc[2]["pdb_path"])[0]["A"][126]
    assert d126a.resname == "ALA"
    assert {atom.id for atom in d126a} == {"N", "CA", "C", "O", "CB"}
    h172a = parser.get_structure("h172a", manifest.iloc[3]["pdb_path"])[0]["A"][172]
    assert h172a.resname == "ALA"
    assert {atom.id for atom in h172a} == {"N", "CA", "C", "O", "CB"}


def test_known_variant_definitions_use_dp622_numbering() -> None:
    assert tuple(KNOWN_VARIANTS) == ("WT", "Y91F", "D126A", "H172A", "Y91F_D126A")
