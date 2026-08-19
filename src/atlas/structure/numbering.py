"""Authoritative conversion between deposited 23WN and DP622 numbering."""

DP622_FIRST = 1
DP622_LAST = 215
DEPOSITED_FIRST = 25
DEPOSITED_LAST = 239
NUMBERING_OFFSET = 24


def deposited_to_dp622(residue: int) -> int:
    """Convert chain-A deposited numbering (25..239) to DP622 (1..215)."""
    if not DEPOSITED_FIRST <= residue <= DEPOSITED_LAST:
        raise ValueError(f"Deposited DP622-domain residue must be in 25..239, got {residue}")
    return residue - NUMBERING_OFFSET


def dp622_to_deposited(residue: int) -> int:
    """Convert DP622 numbering (1..215) to chain-A deposited numbering."""
    if not DP622_FIRST <= residue <= DP622_LAST:
        raise ValueError(f"DP622 residue must be in 1..215, got {residue}")
    return residue + NUMBERING_OFFSET
