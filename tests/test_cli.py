from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from atlas.cli import app


runner = CliRunner()


def test_reconstruct_command_runs_without_external_models(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "reconstruct",
            "--input",
            "data/23WN.cif",
            "--output-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "DP622_active_like_reconstruction.pdb").is_file()
    assert (tmp_path / "residue_numbering_map.csv").is_file()


def test_run_missing_models_exits_nonzero_with_action(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "run",
            "--input",
            "data/23WN.cif",
            "--output-root",
            str(tmp_path),
            "--thermompnn-repo",
            str(tmp_path / "missing-single"),
            "--thermompnn-d-repo",
            str(tmp_path / "missing-double"),
            "--dynamics-mode",
            "skip",
        ],
    )
    assert result.exit_code != 0
    assert "repository" in result.output.lower()
