"""Deterministic heavy-atom edits for the published DP622 benchmark mutations."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
import shutil

import pandas as pd
from Bio.PDB import PDBIO, PDBParser


@dataclass(frozen=True)
class Mutation:
    position: int
    wildtype: str
    mutant: str

    @property
    def label(self) -> str:
        return f"{self.wildtype}{self.position}{self.mutant}"


KNOWN_VARIANTS: "OrderedDict[str, tuple[Mutation, ...]]" = OrderedDict(
    (
        ("WT", ()),
        ("Y91F", (Mutation(91, "Y", "F"),)),
        ("D126A", (Mutation(126, "D", "A"),)),
        ("H172A", (Mutation(172, "H", "A"),)),
        (
            "Y91F_D126A",
            (Mutation(91, "Y", "F"), Mutation(126, "D", "A")),
        ),
    )
)

_ONE_TO_THREE = {"A": "ALA", "D": "ASP", "F": "PHE", "H": "HIS", "Y": "TYR"}


def _edit_residue(residue, mutation: Mutation) -> None:
    expected = _ONE_TO_THREE[mutation.wildtype]
    target = _ONE_TO_THREE[mutation.mutant]
    if residue.resname != expected:
        raise ValueError(
            f"Mutation {mutation.label} expected {expected} at DP622 {mutation.position}, "
            f"found {residue.resname}"
        )
    if mutation.mutant == "F":
        if mutation.wildtype != "Y" or "OH" not in residue:
            raise ValueError(f"Cannot apply complete aromatic edit {mutation.label}")
        residue.detach_child("OH")
    elif mutation.mutant == "A":
        for atom in tuple(residue):
            if atom.id not in {"N", "CA", "C", "O", "CB"}:
                residue.detach_child(atom.id)
    else:
        raise ValueError(f"Unsupported deterministic mutation: {mutation.label}")
    residue.resname = target


def apply_mutations(
    input_pdb: str | Path,
    mutations: tuple[Mutation, ...],
    output_pdb: str | Path,
) -> Path:
    """Apply supported heavy-atom mutations to DP622 chain A."""
    input_path = Path(input_pdb)
    output_path = Path(output_pdb)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not mutations:
        shutil.copyfile(input_path, output_path)
        return output_path
    structure = PDBParser(QUIET=True).get_structure(output_path.stem, input_path)
    chain = structure[0]["A"]
    for mutation in mutations:
        if mutation.position not in chain:
            raise ValueError(f"DP622 residue {mutation.position} is missing")
        _edit_residue(chain[mutation.position], mutation)
    writer = PDBIO()
    writer.set_structure(structure)
    writer.save(str(output_path))
    return output_path


def build_known_mutants(reconstructed_pdb: str | Path, output_dir: str | Path) -> pd.DataFrame:
    """Write the five known benchmark structures and their numbering manifest."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    deposited_labels = {
        "WT": "Q120E reconstruction",
        "Y91F": "Y115F",
        "D126A": "D150A",
        "H172A": "H196A",
        "Y91F_D126A": "Y115F/D150A",
    }
    rows: list[dict[str, str]] = []
    for variant_id, mutations in KNOWN_VARIANTS.items():
        pdb_path = apply_mutations(
            reconstructed_pdb, mutations, directory / f"{variant_id}.pdb"
        )
        rows.append(
            {
                "variant_id": variant_id,
                "mutation_set": ";".join(m.label for m in mutations) or "WT",
                "dp622_numbering": "/".join(m.label for m in mutations) or "WT",
                "deposited_numbering": deposited_labels[variant_id],
                "pdb_path": str(pdb_path),
                "evidence_class": "computational_reconstruction",
            }
        )
    manifest = pd.DataFrame(rows)
    manifest.to_csv(directory.parent / "known_mutants_manifest.csv", index=False)
    return manifest
