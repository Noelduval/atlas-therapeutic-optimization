"""Centralized, deposition-backed atom selectors for the 23WN reconstruction."""

from __future__ import annotations

from dataclasses import dataclass


class AtomSelectionError(LookupError):
    """Raised when a scientifically required atom cannot be selected."""


@dataclass(frozen=True)
class AtomSelector:
    chain: str
    residue: int
    atom: str

    @property
    def label(self) -> str:
        return f"{self.chain}:{self.residue}:{self.atom}"


ZINC = AtomSelector("C", 1601, "ZN")
SCISSILE_CARBON = AtomSelector("B", 38, "C")
SCISSILE_OXYGEN = AtomSelector("B", 38, "O")
H95_NE2 = AtomSelector("A", 95, "NE2")
H99_NE2 = AtomSelector("A", 99, "NE2")
E122_OE1 = AtomSelector("A", 122, "OE1")
E122_OE2 = AtomSelector("A", 122, "OE2")
E96_OE1 = AtomSelector("A", 96, "OE1")
E96_OE2 = AtomSelector("A", 96, "OE2")
H172_NE2 = AtomSelector("A", 172, "NE2")
Y91_CZ = AtomSelector("A", 91, "CZ")


def select_residue(structure, chain_id: str, residue_number: int):
    model = next(structure.get_models())
    if chain_id not in model:
        raise AtomSelectionError(f"Missing chain {chain_id}")
    matches = [residue for residue in model[chain_id] if residue.id[1] == residue_number]
    if len(matches) != 1:
        raise AtomSelectionError(
            f"Expected one residue at {chain_id}:{residue_number}, found {len(matches)}"
        )
    return matches[0]


def select_atom(structure, selector: AtomSelector):
    residue = select_residue(structure, selector.chain, selector.residue)
    if selector.atom not in residue:
        raise AtomSelectionError(f"Missing atom {selector.label}")
    return residue[selector.atom]


def available_atoms(structure, chain: str, residue: int, names: tuple[str, ...]):
    selected_residue = select_residue(structure, chain, residue)
    return tuple(selected_residue[name] for name in names if name in selected_residue)
