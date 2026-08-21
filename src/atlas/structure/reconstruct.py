"""Build the explicitly labeled active-like DP622-Aβ coordinate reconstruction."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from Bio.PDB import MMCIFParser, PDBIO
from Bio.PDB.Chain import Chain
from Bio.PDB.Model import Model
from Bio.PDB.Structure import Structure

from atlas.structure.numbering import deposited_to_dp622


class ReconstructionError(RuntimeError):
    """Raised when 23WN cannot satisfy the active-like reconstruction contract."""


@dataclass(frozen=True)
class ReconstructionResult:
    structure_path: Path
    numbering_map_path: Path
    dp622_residue_count: int
    substrate_residue_count: int
    zinc_present: bool
    warnings: tuple[str, ...]


def _restore_q120e(residue) -> None:
    if residue.resname != "GLN" or "OE1" not in residue or "NE2" not in residue:
        raise ReconstructionError("Deposited chain A residue 120 is not complete GLN/Q120")
    residue.resname = "GLU"
    atom = residue["NE2"]
    residue.detach_child("NE2")
    atom.id = "OE2"
    atom.name = "OE2"
    atom.fullname = " OE2"
    atom.element = "O"
    residue.add(atom)


def reconstruct_active_like(
    source_cif: str | Path,
    output_pdb: str | Path,
    numbering_map_csv: str | Path,
) -> ReconstructionResult:
    """Extract DP622/Aβ/Zn from 23WN and restore the Q120E active-like model.

    The Q-to-E edit is an isosteric coordinate reconstruction. It is not an
    experimentally observed active DP622-S2 structure.
    """
    source = Path(source_cif)
    output = Path(output_pdb)
    mapping_path = Path(numbering_map_csv)
    if not source.is_file():
        raise FileNotFoundError(f"23WN input does not exist: {source}")

    source_model = MMCIFParser(QUIET=True, auth_chains=True, auth_residues=True).get_structure(
        "23WN", source
    )[0]
    for required_chain in ("A", "B"):
        if required_chain not in source_model:
            raise ReconstructionError(f"Required 23WN chain {required_chain} is missing")

    reconstructed = Structure("DP622_active_like_reconstruction")
    model = Model(0)
    reconstructed.add(model)
    protein = Chain("A")
    substrate = Chain("B")
    metal = Chain("C")
    model.add(protein)
    model.add(substrate)
    model.add(metal)

    rows: list[dict[str, object]] = []
    for source_residue in source_model["A"]:
        deposited = source_residue.id[1]
        if not 25 <= deposited <= 239:
            continue
        residue = deepcopy(source_residue)
        residue.detach_parent()
        residue.id = (" ", deposited_to_dp622(deposited), " ")
        deposited_name = residue.resname
        if deposited == 120:
            _restore_q120e(residue)
        protein.add(residue)
        rows.append(
            {
                "dp622_residue": deposited_to_dp622(deposited),
                "deposited_residue": deposited,
                "deposited_resname": deposited_name,
                "reconstructed_resname": residue.resname,
                "source_chain": "A",
                "output_chain": "A",
            }
        )

    for source_residue in source_model["B"]:
        if 34 <= source_residue.id[1] <= 41:
            residue = deepcopy(source_residue)
            residue.detach_parent()
            substrate.add(residue)

    zinc_residues = [
        residue
        for chain in source_model
        for residue in chain
        if residue.resname == "ZN" and any(atom.element == "ZN" for atom in residue)
    ]
    if len(zinc_residues) == 1:
        residue = deepcopy(zinc_residues[0])
        residue.detach_parent()
        metal.add(residue)

    protein_residues = list(protein.get_residues())
    substrate_residues = list(substrate.get_residues())
    if len(protein_residues) != 215:
        raise ReconstructionError(
            f"Expected 215 DP622 residues after extraction, found {len(protein_residues)}"
        )
    if [res.id[1] for res in protein_residues] != list(range(1, 216)):
        raise ReconstructionError("DP622 extraction is not contiguous from residues 1..215")
    if protein[96].resname != "GLU" or not {"OE1", "OE2"} <= {
        atom.id for atom in protein[96]
    }:
        raise ReconstructionError("Active-like reconstruction does not contain complete GLU E96")
    if len(substrate_residues) != 8:
        raise ReconstructionError(
            f"Expected eight resolved Aβ residues (34..41), found {len(substrate_residues)}"
        )
    if len(zinc_residues) != 1:
        raise ReconstructionError(f"Expected one zinc ion, found {len(zinc_residues)}")

    output.parent.mkdir(parents=True, exist_ok=True)
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    writer = PDBIO()
    writer.set_structure(reconstructed)
    writer.save(str(output))
    pd.DataFrame(rows).to_csv(mapping_path, index=False)
    return ReconstructionResult(
        structure_path=output,
        numbering_map_path=mapping_path,
        dp622_residue_count=len(protein_residues),
        substrate_residue_count=len(substrate_residues),
        zinc_present=True,
        warnings=(
            "Q120E is an isosteric computational edit of the inactive E96Q structure; "
            "it is not an experimentally observed active DP622-S2 structure.",
        ),
    )
