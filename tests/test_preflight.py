from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from atlas.preflight import PreflightError, run_preflight
from atlas.stability.thermompnn_d_runner import THERMOMPNN_D_REVISION
from atlas.stability.thermompnn_runner import THERMOMPNN_REVISION


def _repos(tmp_path: Path) -> tuple[Path, Path]:
    single = tmp_path / "ThermoMPNN"
    double = tmp_path / "ThermoMPNN-D"
    (single / "analysis").mkdir(parents=True)
    (single / "analysis/custom_inference.py").write_text("# boundary\n")
    double.mkdir()
    (double / "v2_ssm.py").write_text("# boundary\n")
    return single, double


def _commands(single: Path, double: Path):
    def run(command, **kwargs):
        if command[0] == "nvidia-smi":
            return subprocess.CompletedProcess(
                command, 0, "Tesla T4, 15360, 14500, 860\n", ""
            )
        repo = Path(command[2])
        revisions = {
            Path.cwd(): "a" * 40,
            single: THERMOMPNN_REVISION,
            double: THERMOMPNN_D_REVISION,
        }
        return subprocess.CompletedProcess(command, 0, revisions[repo] + "\n", "")

    return run


def test_t4_preflight_reports_gpu_sources_input_and_atlas_import(tmp_path: Path) -> None:
    single, double = _repos(tmp_path)
    report = run_preflight(
        Path("data/23WN.cif"),
        Path.cwd(),
        single,
        double,
        command_runner=_commands(single, double),
        torch_probe=lambda: {
            "cuda_available": True,
            "device_name": "Tesla T4",
            "torch_version": "2.8.0+cu128",
            "cuda_version": "12.8",
        },
    )
    assert report.passed
    assert report.gpu_name == "Tesla T4"
    assert report.gpu_memory_free_mib == 14_500
    assert report.atlas_commit == "a" * 40
    assert report.thermompnn_commit == THERMOMPNN_REVISION
    assert report.thermompnn_d_commit == THERMOMPNN_D_REVISION
    assert report.input_parsed
    assert report.atlas_version == "1.0.0"


def test_preflight_stops_when_pytorch_cannot_see_cuda(tmp_path: Path) -> None:
    single, double = _repos(tmp_path)
    with pytest.raises(PreflightError, match="PyTorch cannot see CUDA"):
        run_preflight(
            Path("data/23WN.cif"),
            Path.cwd(),
            single,
            double,
            command_runner=_commands(single, double),
            torch_probe=lambda: {
                "cuda_available": False,
                "device_name": "",
                "torch_version": "2.8.0",
                "cuda_version": None,
            },
        )


def test_preflight_rejects_wrong_model_revision(tmp_path: Path) -> None:
    single, double = _repos(tmp_path)

    def wrong_revision(command, **kwargs):
        completed = _commands(single, double)(command, **kwargs)
        if len(command) > 2 and Path(command[2]) == double:
            return subprocess.CompletedProcess(command, 0, "b" * 40 + "\n", "")
        return completed

    with pytest.raises(PreflightError, match=THERMOMPNN_D_REVISION):
        run_preflight(
            Path("data/23WN.cif"),
            Path.cwd(),
            single,
            double,
            command_runner=wrong_revision,
            torch_probe=lambda: {
                "cuda_available": True,
                "device_name": "Tesla T4",
                "torch_version": "2.8.0+cu128",
                "cuda_version": "12.8",
            },
        )
