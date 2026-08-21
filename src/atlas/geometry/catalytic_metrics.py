"""Deterministic comparative geometry metrics for DP622-Aβ coordinate models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd
from Bio.PDB import PDBParser
from Bio.SVDSuperimposer import SVDSuperimposer

from atlas.geometry.selectors import (
    E96_OE1,
    E96_OE2,
    E122_OE1,
    E122_OE2,
    H95_NE2,
    H99_NE2,
    H172_NE2,
    SCISSILE_CARBON,
    SCISSILE_OXYGEN,
    Y91_CZ,
    ZINC,
    AtomSelectionError,
    available_atoms,
    select_atom,
)


@dataclass(frozen=True)
class GeometryRecord:
    variant_id: str
    zn_scissile_oxygen_distance_a: float | None
    zn_h95_ne2_distance_a: float | None
    zn_h99_ne2_distance_a: float | None
    zn_e122_oxygen_distance_a: float | None
    e96_to_scissile_carbonyl_distance_a: float | None
    active_site_rmsd_a: float | None
    substrate_rmsd_a: float | None
    h172_to_scissile_oxygen_distance_a: float | None
    y91_d126_pocket_distance_a: float | None
    substrate_pose_drift_a: float | None
    clamp_distance_a: float | None
    geometry_complete: bool
    warnings: tuple[str, ...]

    def csv_row(self) -> dict[str, object]:
        row = asdict(self)
        row["warnings"] = " | ".join(self.warnings)
        return row


def _distance(left, right) -> float:
    return float(np.linalg.norm(np.asarray(left.coord) - np.asarray(right.coord)))


def _nearest_distance(left_atoms, right_atoms) -> float | None:
    distances = [_distance(left, right) for left in left_atoms for right in right_atoms]
    return min(distances) if distances else None


def _named_atoms(structure, chain_id: str, residue_numbers, atom_names=None):
    model = next(structure.get_models())
    if chain_id not in model:
        return {}
    result = {}
    for residue in model[chain_id]:
        if residue.id[1] not in residue_numbers:
            continue
        for atom in residue:
            if atom_names is None or atom.id in atom_names:
                result[(residue.id[1], atom.id)] = atom
    return result


def _alignment(reference, mobile):
    reference_ca = _named_atoms(reference, "A", range(1, 216), {"CA"})
    mobile_ca = _named_atoms(mobile, "A", range(1, 216), {"CA"})
    keys = sorted(set(reference_ca) & set(mobile_ca))
    if len(keys) < 3:
        raise AtomSelectionError("At least three common DP622 CA atoms are required for alignment")
    fixed = np.asarray([reference_ca[key].coord for key in keys], dtype=float)
    moving = np.asarray([mobile_ca[key].coord for key in keys], dtype=float)
    superimposer = SVDSuperimposer()
    superimposer.set(fixed, moving)
    superimposer.run()
    return superimposer.get_rotran()


def _aligned_rmsd(reference, mobile, chain, residues, atom_names, rotation, translation):
    fixed_atoms = _named_atoms(reference, chain, residues, atom_names)
    moving_atoms = _named_atoms(mobile, chain, residues, atom_names)
    keys = sorted(set(fixed_atoms) & set(moving_atoms))
    if not keys:
        return None
    fixed = np.asarray([fixed_atoms[key].coord for key in keys], dtype=float)
    moving = np.asarray([moving_atoms[key].coord for key in keys], dtype=float)
    transformed = np.dot(moving, rotation) + translation
    return float(np.sqrt(np.mean(np.sum((transformed - fixed) ** 2, axis=1))))


def _centroid_drift(reference, mobile, rotation, translation):
    fixed_atoms = _named_atoms(reference, "B", range(34, 42), {"N", "CA", "C", "O"})
    moving_atoms = _named_atoms(mobile, "B", range(34, 42), {"N", "CA", "C", "O"})
    keys = sorted(set(fixed_atoms) & set(moving_atoms))
    if not keys:
        return None
    fixed = np.asarray([fixed_atoms[key].coord for key in keys], dtype=float)
    moving = np.asarray([moving_atoms[key].coord for key in keys], dtype=float)
    transformed = np.dot(moving, rotation) + translation
    return float(np.linalg.norm(transformed.mean(axis=0) - fixed.mean(axis=0)))


def measure_geometry(
    pdb_path: str | Path,
    reference_pdb: str | Path | None = None,
    variant_id: str | None = None,
) -> GeometryRecord:
    """Measure catalytic geometry, returning nulls and warnings for missing atoms."""
    parser = PDBParser(QUIET=True)
    path = Path(pdb_path)
    structure = parser.get_structure(variant_id or path.stem, path)
    reference = (
        parser.get_structure("reference", Path(reference_pdb))
        if reference_pdb is not None
        else structure
    )
    warnings: list[str] = []

    def required(selector, human_name):
        try:
            return select_atom(structure, selector)
        except AtomSelectionError:
            warnings.append(f"Missing required {human_name} atom ({selector.label}).")
            return None

    zinc = required(ZINC, "zinc")
    scissile_o = required(SCISSILE_OXYGEN, "scissile carbonyl oxygen")
    scissile_c = required(SCISSILE_CARBON, "scissile carbonyl carbon")
    h95 = required(H95_NE2, "H95 NE2")
    h99 = required(H99_NE2, "H99 NE2")
    h172 = required(H172_NE2, "H172 NE2")
    e122 = available_atoms(structure, "A", 122, ("OE1", "OE2"))
    e96 = available_atoms(structure, "A", 96, ("OE1", "OE2"))
    if not e122:
        warnings.append("Missing required E122 carboxylate oxygen atoms.")
    if not e96:
        warnings.append("Missing required reconstructed E96 carboxylate oxygen atoms.")

    y91_atoms = available_atoms(structure, "A", 91, ("OH", "CZ"))
    d126_atoms = available_atoms(structure, "A", 126, ("OD1", "OD2", "CB"))
    if y91_atoms and y91_atoms[0].id != "OH":
        warnings.append("Y91 OH is absent; pocket metric uses aromatic CZ fallback.")
    if d126_atoms and d126_atoms[0].id == "CB":
        warnings.append("D126 carboxylate is absent; pocket metric uses CB fallback.")

    try:
        rotation, translation = _alignment(reference, structure)
        active_rmsd = _aligned_rmsd(
            reference,
            structure,
            "A",
            {91, 95, 96, 99, 122, 126, 172},
            None,
            rotation,
            translation,
        )
        substrate_rmsd = _aligned_rmsd(
            reference,
            structure,
            "B",
            range(34, 42),
            {"N", "CA", "C", "O"},
            rotation,
            translation,
        )
        pose_drift = _centroid_drift(reference, structure, rotation, translation)
    except AtomSelectionError as exc:
        warnings.append(str(exc))
        active_rmsd = substrate_rmsd = pose_drift = None

    y91_cz = required(Y91_CZ, "Y91 aromatic CZ")
    h172_clamp = h172 or next(iter(available_atoms(structure, "A", 172, ("CB",))), None)
    values = {
        "zn_scissile": _distance(zinc, scissile_o) if zinc and scissile_o else None,
        "zn_h95": _distance(zinc, h95) if zinc and h95 else None,
        "zn_h99": _distance(zinc, h99) if zinc and h99 else None,
        "zn_e122": _nearest_distance((zinc,), e122) if zinc else None,
        "e96_target": _nearest_distance(e96, (scissile_c,)) if scissile_c else None,
        "h172_target": _distance(h172, scissile_o) if h172 and scissile_o else None,
        "pocket": _nearest_distance(y91_atoms[:1], d126_atoms) if y91_atoms else None,
        "clamp": _distance(y91_cz, h172_clamp) if y91_cz and h172_clamp else None,
    }
    complete = all(value is not None for value in (*values.values(), active_rmsd, substrate_rmsd))
    return GeometryRecord(
        variant_id=variant_id or path.stem,
        zn_scissile_oxygen_distance_a=values["zn_scissile"],
        zn_h95_ne2_distance_a=values["zn_h95"],
        zn_h99_ne2_distance_a=values["zn_h99"],
        zn_e122_oxygen_distance_a=values["zn_e122"],
        e96_to_scissile_carbonyl_distance_a=values["e96_target"],
        active_site_rmsd_a=active_rmsd,
        substrate_rmsd_a=substrate_rmsd,
        h172_to_scissile_oxygen_distance_a=values["h172_target"],
        y91_d126_pocket_distance_a=values["pocket"],
        substrate_pose_drift_a=pose_drift,
        clamp_distance_a=values["clamp"],
        geometry_complete=complete,
        warnings=tuple(warnings),
    )


def measure_many(
    variants: Mapping[str, str | Path],
    reference_pdb: str | Path,
    output_csv: str | Path,
) -> pd.DataFrame:
    """Measure multiple structures and persist the stable geometry CSV schema."""
    records = [
        measure_geometry(path, reference_pdb=reference_pdb, variant_id=variant_id).csv_row()
        for variant_id, path in variants.items()
    ]
    table = pd.DataFrame(records)
    output = Path(output_csv)
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)
    return table
