from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

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


def test_notebook_install_is_importable_without_kernel_restart(
    tmp_path: Path,
) -> None:
    """Catch editable installs whose new .pth is invisible to a live kernel."""

    notebook = json.loads(Path("notebooks/Atlas_DP622_Colab.ipynb").read_text())
    setup_cell = next(
        cell
        for cell in notebook["cells"]
        if "repository-setup" in cell.get("metadata", {}).get("tags", [])
    )
    tree = ast.parse("".join(setup_cell["source"]))
    pip_arguments = next(
        node.args[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.args[0] if node.args else None, ast.List)
        and any(
            isinstance(element, ast.Constant) and element.value == "pip"
            for element in node.args[0].elts
        )
    )

    package = tmp_path / "package"
    (package / "src" / "atlas").mkdir(parents=True)
    (package / "src" / "atlas" / "__init__.py").write_text("")
    (package / "src" / "atlas" / "colab.py").write_text("READY = True\n")
    (package / "setup.py").write_text(
        "from setuptools import setup\n"
        "setup(name='atlas-clean-kernel-test', version='1', "
        "package_dir={'': 'src'}, packages=['atlas'], "
        "extras_require={'dynamics': []})\n"
    )
    arguments = eval(
        compile(ast.Expression(pip_arguments), "notebook-pip-command", "eval"),
        {
            "ATLAS_DIR": package,
            "sys": SimpleNamespace(executable=sys.executable),
        },
    )
    package_index = next(
        index
        for index, value in enumerate(arguments)
        if str(value).startswith(str(package))
    )
    command = arguments[: package_index + 1]
    target = tmp_path / "site-packages"
    install_index = command.index("install") + 1
    command[install_index:install_index] = [
        "--quiet",
        "--no-deps",
        "--target",
        str(target),
    ]
    driver = (
        "import subprocess, sys\n"
        f"sys.path.insert(0, {str(target)!r})\n"
        f"subprocess.run({command!r}, check=True)\n"
        "from atlas.colab import READY\n"
        "assert READY is True\n"
    )
    completed = subprocess.run(
        [sys.executable, "-S", "-c", driver],
        cwd=tmp_path,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
