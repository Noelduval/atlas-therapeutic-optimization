"""Fast Colab GPU/source/input checks before scientific inference."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import subprocess
from typing import Callable

from Bio.PDB import MMCIFParser

import atlas
from atlas.stability.common import require_repository
from atlas.stability.thermompnn_d_runner import THERMOMPNN_D_REVISION
from atlas.stability.thermompnn_runner import THERMOMPNN_REVISION


class PreflightError(RuntimeError):
    """The environment cannot safely begin an expensive scientific stage."""


@dataclass(frozen=True)
class PreflightReport:
    passed: bool
    gpu_name: str
    gpu_memory_total_mib: int
    gpu_memory_free_mib: int
    gpu_memory_used_mib: int
    pytorch_cuda_available: bool
    torch_version: str
    torch_cuda_version: str | None
    atlas_version: str
    atlas_commit: str
    thermompnn_commit: str
    thermompnn_d_commit: str
    input_structure: str
    input_parsed: bool
    protein_chain_present: bool
    substrate_chain_present: bool

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(asdict(self), indent=2, sort_keys=True) + "\n")
        return output


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
TorchProbe = Callable[[], dict[str, object]]


def _default_command_runner(command, **kwargs):
    return subprocess.run(
        command, text=True, capture_output=True, check=False, **kwargs
    )


def _default_torch_probe() -> dict[str, object]:
    try:
        import torch
    except ImportError as exc:
        raise PreflightError(f"PyTorch is not installed: {exc}") from exc
    available = bool(torch.cuda.is_available())
    return {
        "cuda_available": available,
        "device_name": torch.cuda.get_device_name(0) if available else "",
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
    }


def _git_revision(repo: Path, command_runner: CommandRunner, name: str) -> str:
    completed = command_runner(
        ["git", "-C", str(repo), "rev-parse", "HEAD"]
    )
    revision = completed.stdout.strip()
    if completed.returncode or len(revision) != 40:
        detail = (completed.stderr or completed.stdout or "unknown error").strip()
        raise PreflightError(f"Cannot resolve {name} checkout SHA at {repo}: {detail}")
    return revision


def _gpu_metadata(command_runner: CommandRunner) -> tuple[str, int, int, int]:
    completed = command_runner(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.free,memory.used",
            "--format=csv,noheader,nounits",
        ]
    )
    if completed.returncode:
        detail = (completed.stderr or completed.stdout or "nvidia-smi failed").strip()
        raise PreflightError(f"NVIDIA GPU is unavailable: {detail}")
    first = completed.stdout.strip().splitlines()[0]
    fields = [field.strip() for field in first.split(",")]
    if len(fields) != 4:
        raise PreflightError(f"Unexpected nvidia-smi output: {first}")
    try:
        return fields[0], int(fields[1]), int(fields[2]), int(fields[3])
    except ValueError as exc:
        raise PreflightError(f"Invalid nvidia-smi memory values: {first}") from exc


def run_preflight(
    input_structure: str | Path,
    atlas_repo: str | Path,
    thermompnn_repo: str | Path,
    thermompnn_d_repo: str | Path,
    *,
    command_runner: CommandRunner = _default_command_runner,
    torch_probe: TorchProbe = _default_torch_probe,
) -> PreflightReport:
    """Verify cheap failure modes before loading either stability model."""
    input_path = Path(input_structure).resolve()
    atlas_path = Path(atlas_repo).resolve()
    single_path = Path(thermompnn_repo).resolve()
    double_path = Path(thermompnn_d_repo).resolve()
    if not input_path.is_file():
        raise PreflightError(f"Required 23WN input does not exist: {input_path}")
    require_repository(single_path, "analysis/custom_inference.py", "ThermoMPNN")
    require_repository(double_path, "v2_ssm.py", "ThermoMPNN-D")

    gpu_name, total_mib, free_mib, used_mib = _gpu_metadata(command_runner)
    torch_data = torch_probe()
    if not bool(torch_data.get("cuda_available", False)):
        raise PreflightError(
            "PyTorch cannot see CUDA. Select Runtime → Change runtime type → T4 GPU, "
            "reconnect, and rerun preflight."
        )
    torch_device = str(torch_data.get("device_name", ""))
    if torch_device and "T4" in gpu_name and "T4" not in torch_device:
        raise PreflightError(
            f"GPU mismatch: nvidia-smi reports {gpu_name}, PyTorch reports {torch_device}"
        )

    atlas_commit = _git_revision(atlas_path, command_runner, "Atlas")
    single_commit = _git_revision(single_path, command_runner, "ThermoMPNN")
    double_commit = _git_revision(double_path, command_runner, "ThermoMPNN-D")
    if single_commit != THERMOMPNN_REVISION:
        raise PreflightError(
            f"ThermoMPNN must be {THERMOMPNN_REVISION}; found {single_commit}"
        )
    if double_commit != THERMOMPNN_D_REVISION:
        raise PreflightError(
            f"ThermoMPNN-D must be {THERMOMPNN_D_REVISION}; found {double_commit}"
        )

    try:
        model = MMCIFParser(
            QUIET=True, auth_chains=True, auth_residues=True
        ).get_structure("23WN", input_path)[0]
    except Exception as exc:
        raise PreflightError(f"23WN could not be parsed: {type(exc).__name__}: {exc}") from exc
    protein_present = "A" in model
    substrate_present = "B" in model
    if not protein_present or not substrate_present:
        raise PreflightError("23WN must contain author chains A (DP622) and B (Aβ)")

    return PreflightReport(
        passed=True,
        gpu_name=gpu_name,
        gpu_memory_total_mib=total_mib,
        gpu_memory_free_mib=free_mib,
        gpu_memory_used_mib=used_mib,
        pytorch_cuda_available=True,
        torch_version=str(torch_data.get("torch_version", "unknown")),
        torch_cuda_version=(
            None
            if torch_data.get("cuda_version") is None
            else str(torch_data["cuda_version"])
        ),
        atlas_version=atlas.__version__,
        atlas_commit=atlas_commit,
        thermompnn_commit=single_commit,
        thermompnn_d_commit=double_commit,
        input_structure=str(input_path),
        input_parsed=True,
        protein_chain_present=True,
        substrate_chain_present=True,
    )
