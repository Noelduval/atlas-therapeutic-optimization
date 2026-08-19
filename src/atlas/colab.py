"""Small command builder shared by the Colab execution wrapper and tests."""

from __future__ import annotations

from pathlib import Path


def build_stage_command(
    *,
    python_executable: str,
    input_structure: str | Path,
    output_root: str | Path,
    thermompnn_repo: str | Path,
    thermompnn_d_repo: str | Path,
    run_id: str,
    dynamics_mode: str,
    stop_after: str | None = None,
    resume: bool = False,
) -> list[str]:
    """Build one staged invocation of the production Atlas CLI."""
    command = [
        python_executable,
        "-m",
        "atlas",
        "run",
        "--input",
        str(input_structure),
        "--output-root",
        str(output_root),
        "--thermompnn-repo",
        str(thermompnn_repo),
        "--thermompnn-d-repo",
        str(thermompnn_d_repo),
        "--dynamics-mode",
        dynamics_mode,
        "--run-id",
        run_id,
    ]
    if resume:
        command.append("--resume")
    if stop_after:
        command.extend(["--stop-after", stop_after])
    return command
