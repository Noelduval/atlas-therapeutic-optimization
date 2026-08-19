from __future__ import annotations

import json
from pathlib import Path

from atlas.colab import build_stage_command


def test_stage_command_uses_production_cli_and_resume_checkpoint() -> None:
    command = build_stage_command(
        python_executable="python",
        input_structure=Path("/content/Atlas/data/23WN.cif"),
        output_root=Path("/content/drive/MyDrive/Atlas/checkpoints"),
        thermompnn_repo=Path("/content/Atlas/.external/ThermoMPNN"),
        thermompnn_d_repo=Path("/content/Atlas/.external/ThermoMPNN-D"),
        run_id="atlas-t4-abc123",
        dynamics_mode="minimize",
        stop_after="thermompnn-d",
        resume=True,
    )
    assert command == [
        "python",
        "-m",
        "atlas",
        "run",
        "--input",
        "/content/Atlas/data/23WN.cif",
        "--output-root",
        "/content/drive/MyDrive/Atlas/checkpoints",
        "--thermompnn-repo",
        "/content/Atlas/.external/ThermoMPNN",
        "--thermompnn-d-repo",
        "/content/Atlas/.external/ThermoMPNN-D",
        "--dynamics-mode",
        "minimize",
        "--run-id",
        "atlas-t4-abc123",
        "--resume",
        "--stop-after",
        "thermompnn-d",
    ]


def test_notebook_configuration_and_stage_cells_are_executable() -> None:
    notebook = json.loads(Path("notebooks/Atlas_DP622_Colab.ipynb").read_text())
    tagged = {
        tag: cell
        for cell in notebook["cells"]
        for tag in cell.get("metadata", {}).get("tags", [])
    }
    required = {
        "atlas-config",
        "hardware-check",
        "repository-setup",
        "full-preflight",
        "structure",
        "benchmark",
        "thermompnn",
        "thermompnn-d",
        "geometry",
        "openmm",
        "validation",
        "candidates",
        "export",
    }
    assert required <= tagged.keys()
    namespace: dict[str, object] = {}
    exec("".join(tagged["atlas-config"]["source"]), namespace)
    assert namespace["ATLAS_REF"] == "codex/atlas-v1-dynamic-geometry"
    assert namespace["DYNAMICS_MODE"] == "minimize"
    assert namespace["USE_GOOGLE_DRIVE"] is True
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"notebook-cell-{index}", "exec")
