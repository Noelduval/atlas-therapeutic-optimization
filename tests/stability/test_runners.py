from __future__ import annotations

from pathlib import Path
import subprocess

import pandas as pd
import pytest

from atlas.stability.common import (
    DependencyUnavailableError,
    ScientificOutputError,
    StabilityVariant,
)
from atlas.stability.thermompnn_d_runner import ThermoMPNNDRunner
from atlas.stability.thermompnn_runner import ThermoMPNNRunner


SINGLE = StabilityVariant("Y91F", "Y91F", "Y115F")
DOUBLE = StabilityVariant("Y91F_D126A", "Y91F:D126A", "Y115F:D150A")


def _repo(tmp_path: Path, script: str) -> Path:
    repo = tmp_path / "repo"
    (repo / Path(script).parent).mkdir(parents=True)
    (repo / script).write_text("# test boundary\n")
    return repo


def test_missing_thermompnn_repository_is_actionable(tmp_path: Path) -> None:
    runner = ThermoMPNNRunner(tmp_path / "missing")
    with pytest.raises(DependencyUnavailableError, match="ThermoMPNN repository"):
        runner.run(tmp_path / "input.pdb", [SINGLE], tmp_path / "scores")


def test_nonzero_external_exit_is_preserved(tmp_path: Path) -> None:
    repo = _repo(tmp_path, "analysis/custom_inference.py")

    def fail(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 2, "stdout", "model failed")

    runner = ThermoMPNNRunner(repo, command_runner=fail)
    with pytest.raises(ScientificOutputError, match="model failed"):
        runner.run(tmp_path / "input.pdb", [SINGLE], tmp_path / "scores")


def test_thermompnn_normalizes_real_shaped_output(tmp_path: Path) -> None:
    repo = _repo(tmp_path, "analysis/custom_inference.py")

    def succeed(command, **kwargs):
        out_dir = Path(command[command.index("--out_dir") + 1])
        out_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            [{"ddG_pred": -0.42, "position": 91, "wildtype": "Y", "mutation": "F"}]
        ).to_csv(out_dir / "ThermoMPNN_inference_input.csv", index=False)
        return subprocess.CompletedProcess(command, 0, "ok", "")

    scores = ThermoMPNNRunner(repo, command_runner=succeed).run(
        tmp_path / "input.pdb", [SINGLE], tmp_path / "scores"
    )
    assert scores.loc[0, "variant_id"] == "Y91F"
    assert scores.loc[0, "predicted_ddg_or_score"] == pytest.approx(-0.42)
    assert scores.loc[0, "model_used"] == "ThermoMPNN"
    assert "stability" in scores.loc[0, "interpretation"].lower()


def test_thermompnn_rejects_missing_columns(tmp_path: Path) -> None:
    repo = _repo(tmp_path, "analysis/custom_inference.py")

    def malformed(command, **kwargs):
        out_dir = Path(command[command.index("--out_dir") + 1])
        out_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([{"score": 1.0}]).to_csv(
            out_dir / "ThermoMPNN_inference_input.csv", index=False
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    with pytest.raises(ScientificOutputError, match="columns"):
        ThermoMPNNRunner(repo, command_runner=malformed).run(
            tmp_path / "input.pdb", [SINGLE], tmp_path / "scores"
        )


def test_thermompnn_rejects_missing_requested_mutation(tmp_path: Path) -> None:
    repo = _repo(tmp_path, "analysis/custom_inference.py")

    def wrong_mutation(command, **kwargs):
        out_dir = Path(command[command.index("--out_dir") + 1])
        out_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            [{"ddG_pred": 0.1, "position": 10, "wildtype": "A", "mutation": "G"}]
        ).to_csv(out_dir / "ThermoMPNN_inference_input.csv", index=False)
        return subprocess.CompletedProcess(command, 0, "", "")

    with pytest.raises(ScientificOutputError, match="Y91F"):
        ThermoMPNNRunner(repo, command_runner=wrong_mutation).run(
            tmp_path / "input.pdb", [SINGLE], tmp_path / "scores"
        )


def test_thermompnn_reuses_genuine_full_sweep_for_later_selection(
    tmp_path: Path,
) -> None:
    repo = _repo(tmp_path, "analysis/custom_inference.py")
    raw = tmp_path / "ThermoMPNN_inference_input.csv"
    pd.DataFrame(
        [
            {"ddG_pred": -0.42, "position": 91, "wildtype": "Y", "mutation": "F"},
            {"ddG_pred": -0.31, "position": 40, "wildtype": "D", "mutation": "A"},
        ]
    ).to_csv(raw, index=False)
    novel = StabilityVariant("D40A", "D40A", "D64A")
    scores = ThermoMPNNRunner(repo).normalize_existing(
        raw, [novel], tmp_path / "normalized"
    )
    assert scores.loc[0, "variant_id"] == "D40A"
    assert scores.loc[0, "predicted_ddg_or_score"] == pytest.approx(-0.31)


def test_thermompnn_d_normalizes_double_output(tmp_path: Path) -> None:
    repo = _repo(tmp_path, "v2_ssm.py")

    def succeed(command, **kwargs):
        prefix = Path(command[command.index("--out") + 1])
        prefix.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            [{"ddG (kcal/mol)": 1.7, "Mutation": "Y91F:D126A", "CA-CA Distance": 9.0}]
        ).to_csv(prefix.with_suffix(".csv"), index=False)
        return subprocess.CompletedProcess(command, 0, "ok", "")

    scores = ThermoMPNNDRunner(repo, command_runner=succeed).run(
        tmp_path / "input.pdb", [DOUBLE], tmp_path / "scores"
    )
    assert scores.loc[0, "model_used"] == "ThermoMPNN-D epistatic"
    assert scores.loc[0, "predicted_ddg_or_score"] == pytest.approx(1.7)
    assert scores.loc[0, "mutation_set"] == "Y91F:D126A"
