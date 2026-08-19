"""Atlas v1 command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import pandas as pd
import typer

from atlas.pipeline import PipelineConfig, run_pipeline
from atlas.structure.reconstruct import reconstruct_active_like
from atlas.validation.validation_gate import (
    evaluate_validation,
    require_validation_pass,
    write_validation_outputs,
)


app = typer.Typer(
    no_args_is_help=True,
    help="Validation-gated stability and catalytic-geometry screening for DP622.",
)


@app.command()
def reconstruct(
    input_path: Annotated[
        Path, typer.Option("--input", help="Committed 23WN mmCIF/PDB input.")
    ] = Path("data/23WN.cif"),
    output_dir: Annotated[
        Path, typer.Option(help="Directory for structural-only outputs.")
    ] = Path("outputs/reconstruction"),
) -> None:
    """Build the active-like DP622–Aβ reconstruction without model dependencies."""
    output_dir.mkdir(parents=True, exist_ok=True)
    result = reconstruct_active_like(
        input_path,
        output_dir / "DP622_active_like_reconstruction.pdb",
        output_dir / "residue_numbering_map.csv",
    )
    typer.echo(f"Active-like reconstruction: {result.structure_path}")
    typer.echo(f"Residue map: {result.numbering_map_path}")


@app.command()
def validate(
    stability_csv: Annotated[Path, typer.Option(help="Normalized stability CSV.")],
    geometry_csv: Annotated[Path, typer.Option(help="Catalytic geometry CSV.")],
    output_dir: Annotated[
        Path, typer.Option(help="Directory for gate CSV and Markdown report.")
    ] = Path("outputs/validation"),
    dynamics_csv: Annotated[
        Path | None, typer.Option(help="Optional OpenMM summary CSV.")
    ] = None,
) -> None:
    """Evaluate precomputed real scientific outputs through the hard gate."""
    stability = pd.read_csv(stability_csv)
    geometry = pd.read_csv(geometry_csv)
    dynamics = pd.read_csv(dynamics_csv) if dynamics_csv else None
    result = evaluate_validation(stability, geometry, dynamics)
    write_validation_outputs(result, output_dir)
    try:
        require_validation_pass(result)
    except Exception as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(3) from exc
    typer.echo(f"Validation passed: {output_dir / 'validation_report.md'}")


@app.command()
def run(
    input_path: Annotated[
        Path, typer.Option("--input", help="Committed 23WN mmCIF/PDB input.")
    ] = Path("data/23WN.cif"),
    output_root: Annotated[
        Path, typer.Option(help="Parent for fresh, non-overwriting run directories.")
    ] = Path("outputs"),
    thermompnn_repo: Annotated[
        Path, typer.Option(help="Pinned official ThermoMPNN repository.")
    ] = Path(".external/ThermoMPNN"),
    thermompnn_d_repo: Annotated[
        Path, typer.Option(help="Pinned official ThermoMPNN-D repository.")
    ] = Path(".external/ThermoMPNN-D"),
    dynamics_mode: Annotated[
        str,
        typer.Option(help="OpenMM stage: minimize, short-md, or skip."),
    ] = "minimize",
) -> None:
    """Run reconstruction, benchmarks, hard validation, then conditional design."""
    try:
        result = run_pipeline(
            PipelineConfig(
                input_structure=input_path,
                output_root=output_root,
                thermompnn_repo=thermompnn_repo,
                thermompnn_d_repo=thermompnn_d_repo,
                dynamics_mode=dynamics_mode,
            )
        )
    except Exception as exc:
        typer.echo(f"Atlas stopped: {type(exc).__name__}: {exc}", err=True)
        raise typer.Exit(2) from exc
    typer.echo(f"Atlas completed: {result.run_dir}")
    typer.echo("Novel candidates are computational predictions requiring experimental validation.")
