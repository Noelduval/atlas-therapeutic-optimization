from pathlib import Path

import pandas as pd
from Bio.PDB import PDBParser

from atlas.structure.reconstruct import reconstruct_active_like


SOURCE = Path(__file__).parents[2] / "data" / "23WN.cif"


def test_reconstruction_preserves_required_components_and_restores_e96(tmp_path) -> None:
    output = tmp_path / "DP622_active_like_reconstruction.pdb"
    mapping = tmp_path / "residue_numbering_map.csv"

    result = reconstruct_active_like(SOURCE, output, mapping)

    assert result.dp622_residue_count == 215
    assert result.substrate_residue_count == 8
    assert result.zinc_present is True
    structure = PDBParser(QUIET=True).get_structure("active_like", output)
    model = structure[0]
    assert [res.id[1] for res in model["A"]] == list(range(1, 216))
    e96 = model["A"][96]
    assert e96.resname == "GLU"
    assert {atom.id for atom in e96} >= {"CD", "OE1", "OE2"}
    assert [res.id[1] for res in model["B"]] == list(range(34, 42))
    zinc_atoms = [atom for atom in model.get_atoms() if atom.element == "ZN"]
    assert len(zinc_atoms) == 1

    table = pd.read_csv(mapping)
    assert list(table.columns) == [
        "dp622_residue",
        "deposited_residue",
        "deposited_resname",
        "reconstructed_resname",
        "source_chain",
        "output_chain",
    ]
    assert len(table) == 215
    catalytic = table.loc[table["dp622_residue"] == 96].iloc[0]
    assert catalytic.to_dict() == {
        "dp622_residue": 96,
        "deposited_residue": 120,
        "deposited_resname": "GLN",
        "reconstructed_resname": "GLU",
        "source_chain": "A",
        "output_chain": "A",
    }


def test_reconstruction_fails_loudly_for_missing_input(tmp_path) -> None:
    missing = tmp_path / "missing.cif"
    with __import__("pytest").raises(FileNotFoundError, match="23WN input"):
        reconstruct_active_like(missing, tmp_path / "out.pdb", tmp_path / "map.csv")
