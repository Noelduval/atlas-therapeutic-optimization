"""Optional restrained short MD after successful minimization."""

from __future__ import annotations

from pathlib import Path

from atlas.dynamics.models import DynamicsConfig, DynamicsResult
from atlas.dynamics.openmm_minimize import (
    _load_openmm,
    _prepare_system,
    minimize_variant,
)


def run_short_md(
    pdb_path: str | Path,
    output_dir: str | Path,
    config: DynamicsConfig,
) -> DynamicsResult:
    destination = Path(output_dir)
    minimized = minimize_variant(pdb_path, destination / "minimization", config)
    if minimized.status != "completed" or minimized.output_pdb is None:
        return minimized
    try:
        bundle = _load_openmm()
        modeller, system = _prepare_system(minimized.output_pdb, config, bundle)
        integrator = bundle.openmm.LangevinMiddleIntegrator(
            config.temperature_k * bundle.unit.kelvin,
            1.0 / bundle.unit.picosecond,
            config.timestep_fs * bundle.unit.femtoseconds,
        )
        integrator.setRandomNumberSeed(config.random_seed)
        simulation = bundle.app.Simulation(modeller.topology, system, integrator)
        simulation.context.setPositions(modeller.positions)
        simulation.context.setVelocitiesToTemperature(
            config.temperature_k * bundle.unit.kelvin, config.random_seed
        )
        destination.mkdir(parents=True, exist_ok=True)
        snapshot_dir = destination / "snapshots"
        snapshot_dir.mkdir(exist_ok=True)
        snapshot_count = max(1, min(config.snapshot_count, config.md_steps))
        base_steps, remainder = divmod(config.md_steps, snapshot_count)
        records: list[dict[str, float | int | str]] = []
        completed_steps = 0
        state = None
        for snapshot_index in range(1, snapshot_count + 1):
            steps = base_steps + (1 if snapshot_index <= remainder else 0)
            simulation.step(steps)
            completed_steps += steps
            state = simulation.context.getState(getPositions=True, getEnergy=True)
            snapshot_path = snapshot_dir / f"snapshot_{snapshot_index:03d}.pdb"
            with snapshot_path.open("w") as handle:
                bundle.app.PDBFile.writeFile(
                    modeller.topology, state.getPositions(), handle, keepIds=True
                )
            records.append(
                {
                    "stage": "short_md",
                    "step": completed_steps,
                    "time_ps": completed_steps * config.timestep_fs / 1_000.0,
                    "potential_kj_mol": float(
                        state.getPotentialEnergy().value_in_unit(
                            bundle.unit.kilojoule_per_mole
                        )
                    ),
                    "pdb_path": str(snapshot_path),
                }
            )
        assert state is not None
        output_pdb = destination / "short_md_final.pdb"
        with output_pdb.open("w") as handle:
            bundle.app.PDBFile.writeFile(
                modeller.topology, state.getPositions(), handle, keepIds=True
            )
        return DynamicsResult(
            "completed", output_pdb, minimized.snapshot_records + tuple(records)
        )
    except Exception as exc:
        return DynamicsResult(
            "skipped_unparameterized_system",
            None,
            (),
            f"OpenMM short MD failed: {type(exc).__name__}: {exc}",
        )
