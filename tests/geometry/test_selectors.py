from pathlib import Path

import pytest
from Bio.PDB import PDBParser

from atlas.geometry.selectors import (
    SCISSILE_OXYGEN,
    ZINC,
    AtomSelectionError,
    AtomSelector,
    select_atom,
)
from atlas.structure.reconstruct import reconstruct_active_like


SOURCE = Path(__file__).parents[2] / "data" / "23WN.cif"


@pytest.fixture()
def reconstructed(tmp_path):
    output = tmp_path / "active_like.pdb"
    reconstruct_active_like(SOURCE, output, tmp_path / "map.csv")
    return PDBParser(QUIET=True).get_structure("active_like", output)


def test_deposition_backed_selectors_find_zinc_and_scissile_oxygen(reconstructed) -> None:
    zinc = select_atom(reconstructed, ZINC)
    oxygen = select_atom(reconstructed, SCISSILE_OXYGEN)
    assert zinc.element == "ZN"
    assert oxygen.full_id[2:] == ("B", (" ", 38, " "), ("O", " "))
    assert zinc - oxygen == pytest.approx(2.287, abs=0.002)


def test_selector_error_names_missing_atom(reconstructed) -> None:
    with pytest.raises(AtomSelectionError, match="A:96:FAKE"):
        select_atom(reconstructed, AtomSelector("A", 96, "FAKE"))
