"""Restrained OpenMM minimization with explicit, non-fabricating fallback."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from atlas.dynamics.models import DynamicsConfig, DynamicsResult


def _load_openmm() -> SimpleNamespace:
    import openmm
    from openmm import app, unit

    return SimpleNamespace(openmm=openmm, app=app, unit=unit)


def _add_position_restraints(bundle, system, topology, positions, config) -> None:
    force = bundle.openmm.CustomExternalForce(
        "0.5*k*((x-x0)^2+(y-y0)^2+(z-z0)^2)"
    )
    force.addGlobalParameter(
        "k",
        config.restraint_k_kj_mol_nm2
        * bundle.unit.kilojoule_per_mole
        / bundle.unit.nanometer**2,
    )
    for name in ("x0", "y0", "z0"):
        force.addPerParticleParameter(name)
    for atom in topology.atoms():
        if atom.element is not None and atom.element.symbol != "H":
            xyz = positions[atom.index].value_in_unit(bundle.unit.nanometer)
            force.addParticle(atom.index, xyz)
    system.addForce(force)


def _add_zinc_geometry_restraints(bundle, system, topology, positions, config) -> None:
    zinc_index = None
    targets: list[int] = []
    for atom in topology.atoms():
        residue = atom.residue
        chain = residue.chain.id
        resid = int(residue.id)
        if atom.element is not None and atom.element.symbol.upper() == "ZN":
            zinc_index = atom.index
        if (chain, resid, atom.name) in {
            ("A", 95, "NE2"),
            ("A", 99, "NE2"),
            ("A", 122, "OE1"),
            ("A", 122, "OE2"),
            ("B", 38, "O"),
        }:
            targets.append(atom.index)
    if zinc_index is None:
        raise ValueError("Zinc atom was not found during OpenMM setup")
    force = bundle.openmm.HarmonicBondForce()
    zinc_position = positions[zinc_index]
    for index in targets:
        distance = bundle.openmm.Vec3.distance(zinc_position, positions[index])
        force.addBond(
            zinc_index,
            index,
            distance,
            config.zinc_restraint_k_kj_mol_nm2
            * bundle.unit.kilojoule_per_mole
            / bundle.unit.nanometer**2,
        )
    system.addForce(force)


def _prepare_system(pdb_path: Path, config: DynamicsConfig, bundle):
    pdb = bundle.app.PDBFile(str(pdb_path))
    forcefield = bundle.app.ForceField("amber14-all.xml", "amber14/tip3pfb.xml")
    modeller = bundle.app.Modeller(pdb.topology, pdb.positions)
    modeller.addHydrogens(forcefield)
    system = forcefield.createSystem(
        modeller.topology,
        nonbondedMethod=bundle.app.NoCutoff,
        constraints=bundle.app.HBonds,
    )
    _add_position_restraints(
        bundle, system, modeller.topology, modeller.positions, config
    )
    _add_zinc_geometry_restraints(
        bundle, system, modeller.topology, modeller.positions, config
    )
    return modeller, system


def minimize_variant(
    pdb_path: str | Path,
    output_dir: str | Path,
    config: DynamicsConfig,
) -> DynamicsResult:
    """Attempt restrained minimization; skipped results never contain fake snapshots."""
    source = Path(pdb_path)
    destination = Path(output_dir)
    try:
        bundle = _load_openmm()
    except (ImportError, ModuleNotFoundError) as exc:
        return DynamicsResult(
            "skipped_dependency_unavailable", None, (), f"OpenMM unavailable: {exc}"
        )
    try:
        modeller, system = _prepare_system(source, config, bundle)
        integrator = bundle.openmm.VerletIntegrator(
            config.timestep_fs * bundle.unit.femtoseconds
        )
        simulation = bundle.app.Simulation(modeller.topology, system, integrator)
        simulation.context.setPositions(modeller.positions)
        initial = simulation.context.getState(getEnergy=True).getPotentialEnergy()
        simulation.minimizeEnergy(
            tolerance=config.minimization_tolerance_kj_mol_nm
            * bundle.unit.kilojoule_per_mole
            / bundle.unit.nanometer,
            maxIterations=config.minimization_max_iterations,
        )
        state = simulation.context.getState(getPositions=True, getEnergy=True)
        destination.mkdir(parents=True, exist_ok=True)
        output_pdb = destination / "minimized.pdb"
        with output_pdb.open("w") as handle:
            bundle.app.PDBFile.writeFile(
                modeller.topology, state.getPositions(), handle, keepIds=True
            )
        record = {
            "stage": "minimized",
            "step": 0,
            "initial_potential_kj_mol": float(
                initial.value_in_unit(bundle.unit.kilojoule_per_mole)
            ),
            "potential_kj_mol": float(
                state.getPotentialEnergy().value_in_unit(
                    bundle.unit.kilojoule_per_mole
                )
            ),
        }
        return DynamicsResult("completed", output_pdb, (record,))
    except Exception as exc:  # OpenMM exposes several version-specific setup errors.
        return DynamicsResult(
            "skipped_unparameterized_system",
            None,
            (),
            f"OpenMM setup/minimization failed: {type(exc).__name__}: {exc}",
        )
