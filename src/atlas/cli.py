"""Atlas v1 command-line interface."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from atlas.artifacts import (
    next_run_dir,
    write_benchmark_artifacts,
    write_campaign_artifacts,
)
from atlas.benchmark import run_benchmark
from atlas.domain.models import CampaignConfig
from atlas.profiles import PROFILES
from atlas.workflow.graph import run_campaign


app = typer.Typer(no_args_is_help=True, help="Atlas v1 scientific optimization artifact.")
challenge_app = typer.Typer(no_args_is_help=True, help="Run the single Atlas Challenge.")
benchmark_app = typer.Typer(no_args_is_help=True, help="Run the VITA benchmark program.")
app.add_typer(challenge_app, name="challenge")
app.add_typer(benchmark_app, name="benchmark")
console = Console()


def _validate_profile(profile: str) -> None:
    if profile not in PROFILES:
        raise typer.BadParameter(
            f"Unknown profile '{profile}'. Available profiles: {', '.join(PROFILES)}"
        )


@challenge_app.command("run")
def challenge_run(
    profile: Annotated[str, typer.Option(help="Runtime adapter profile.")] = "demo_cached",
    output_root: Annotated[
        Path, typer.Option(help="Parent directory for non-overwriting run artifacts.")
    ] = Path("runs"),
) -> None:
    """Run the DP622-S2 / Aβ42 / S2 blinded retrospective challenge."""
    _validate_profile(profile)
    run_dir = next_run_dir(output_root, f"challenge-{profile}")
    run = run_campaign(CampaignConfig(profile=profile), run_dir, profile=profile)
    write_campaign_artifacts(run, run_dir)
    console.print(f"Run directory: {run_dir}")
    console.print(f"Status: {run.final_report.status.value}")
    console.print(f"Winning candidate: {run.final_report.winning_candidate}")


@benchmark_app.command("run")
def benchmark_run(
    profile: Annotated[str, typer.Option(help="Runtime adapter profile.")] = "demo_cached",
    output_root: Annotated[
        Path, typer.Option(help="Parent directory for non-overwriting benchmark artifacts.")
    ] = Path("runs"),
) -> None:
    """Run supporting experiments inside the single VITA benchmark family."""
    _validate_profile(profile)
    run_dir = next_run_dir(output_root, f"benchmark-{profile}")
    result = run_benchmark(profile, run_dir)
    write_benchmark_artifacts(result, run_dir)
    console.print(f"Run directory: {run_dir}")
    console.print(f"Benchmark family: {result.benchmark_family}")
    console.print(f"Status: {result.status}")
    console.print(f"Flagship winner: {result.flagship_winner}")
