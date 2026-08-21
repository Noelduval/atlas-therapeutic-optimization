import pytest

from atlas.structure.numbering import deposited_to_dp622, dp622_to_deposited


def test_numbering_maps_domain_endpoints_and_catalytic_residue() -> None:
    assert deposited_to_dp622(25) == 1
    assert deposited_to_dp622(120) == 96
    assert deposited_to_dp622(239) == 215
    assert dp622_to_deposited(1) == 25
    assert dp622_to_deposited(96) == 120
    assert dp622_to_deposited(215) == 239


@pytest.mark.parametrize("invalid", [0, 24, 240, 999])
def test_deposited_numbering_rejects_residues_outside_dp622_domain(invalid: int) -> None:
    with pytest.raises(ValueError, match="25..239"):
        deposited_to_dp622(invalid)


@pytest.mark.parametrize("invalid", [0, 216, 999])
def test_dp622_numbering_rejects_residues_outside_domain(invalid: int) -> None:
    with pytest.raises(ValueError, match="1..215"):
        dp622_to_deposited(invalid)
