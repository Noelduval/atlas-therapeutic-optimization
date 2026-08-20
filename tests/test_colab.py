from __future__ import annotations

import ast
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

import atlas.colab as colab
from atlas.colab import build_stage_command


def test_stage_command_uses_production_cli_and_resume_checkpoint() -> None:
    command = build_stage_command(
        python_executable="python",
        input_structure=Path("/content/Atlas/data/23WN.cif"),
        output_root=Path("/content/drive/MyDrive/Atlas/checkpoints"),
        atlas_repo=Path("/content/Atlas"),
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
        "--atlas-repo",
        "/content/Atlas",
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
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.List)
        and any(
            isinstance(element, ast.Constant) and element.value == "pip"
            for element in node.elts
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


def test_normal_install_can_run_structure_checkpoint_from_checkout(
    tmp_path: Path,
) -> None:
    """Protect the Colab wheel install from site-packages provenance failures."""

    repository = Path.cwd().resolve()
    installed = tmp_path / "installed"
    installation = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--quiet",
            "--no-deps",
            "--target",
            str(installed),
            str(repository),
        ],
        text=True,
        capture_output=True,
    )
    assert installation.returncode == 0, installation.stderr
    command = build_stage_command(
        python_executable=sys.executable,
        input_structure=repository / "data/23WN.cif",
        output_root=tmp_path / "outputs",
        atlas_repo=repository,
        thermompnn_repo=repository / ".external/ThermoMPNN",
        thermompnn_d_repo=repository / ".external/ThermoMPNN-D",
        run_id="normal-install-stage-3",
        dynamics_mode="minimize",
        stop_after="structure",
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(installed), environment.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    completed = subprocess.run(
        command,
        cwd=repository,
        env=environment,
        text=True,
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "stopped_after_structure" in completed.stdout


def test_failed_stage_prints_complete_subprocess_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    command = [
        sys.executable,
        "-c",
        (
            "import sys; print('complete stdout evidence'); "
            "print('complete stderr evidence', file=sys.stderr); raise SystemExit(2)"
        ),
    ]
    environment = os.environ.copy()
    environment["CUDA_VISIBLE_DEVICES"] = "0"
    environment["ATLAS_TEST_SECRET"] = "must-not-be-printed"

    with pytest.raises(colab.StageExecutionError, match="Structure checkpoint"):
        colab.run_stage_command(
            "Structure checkpoint",
            command,
            tmp_path,
            environment=environment,
            suggested_next_action="Inspect the first Atlas error and fix it.",
        )

    diagnostic = capsys.readouterr().out
    assert "Stage: Structure checkpoint" in diagnostic
    assert f"Working directory: {tmp_path}" in diagnostic
    assert "Exact command:" in diagnostic
    assert "complete stdout evidence" in diagnostic
    assert "complete stderr evidence" in diagnostic
    assert "Exit status: 2" in diagnostic
    assert "CUDA_VISIBLE_DEVICES='0'" in diagnostic
    assert "Suggested next action: Inspect the first Atlas error and fix it." in diagnostic
    assert "must-not-be-printed" not in diagnostic


def test_notebook_stage_wrapper_uses_evidence_preserving_runner(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    notebook = json.loads(Path("notebooks/Atlas_DP622_Colab.ipynb").read_text())
    preflight_cell = next(
        cell
        for cell in notebook["cells"]
        if "full-preflight" in cell.get("metadata", {}).get("tags", [])
    )
    tree = ast.parse("".join(preflight_cell["source"]))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_atlas_stage"
    )
    namespace = {
        "RUN_DIR": tmp_path / "run",
        "INPUT_STRUCTURE": tmp_path / "23WN.cif",
        "OUTPUT_ROOT": tmp_path / "outputs",
        "ATLAS_DIR": tmp_path,
        "EXTERNAL": tmp_path / ".external",
        "DYNAMICS_MODE": "minimize",
        "RUN_ID": "diagnostic-run",
        "sys": SimpleNamespace(executable=sys.executable),
        "subprocess": subprocess,
        "build_stage_command": lambda **kwargs: [
            sys.executable,
            "-c",
            "import sys; print('notebook stderr', file=sys.stderr); raise SystemExit(2)",
        ],
        "run_stage_command": colab.run_stage_command,
    }
    exec(
        compile(
            ast.Module(body=[function], type_ignores=[]),
            "notebook-stage-wrapper",
            "exec",
        ),
        namespace,
    )

    with pytest.raises(colab.StageExecutionError):
        namespace["run_atlas_stage"]("Structure stage", "structure")

    diagnostic = capsys.readouterr().out
    assert "Stage: Structure stage" in diagnostic
    assert "notebook stderr" in diagnostic


def _readiness_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    single = tmp_path / "ThermoMPNN"
    double = tmp_path / "ThermoMPNN-D"
    output = tmp_path / "outputs"
    for path in (
        single / ".git",
        single / "analysis",
        single / "models",
        single / "vanilla_model_weights",
        double / ".git",
        double / "examples/configs",
        double / "model_weights",
        double / "thermompnn/datasets",
        double / "vanilla_model_weights",
    ):
        path.mkdir(parents=True, exist_ok=True)
    fake_omegaconf = (
        "from pathlib import Path\n"
        "class OmegaConf:\n"
        "    @staticmethod\n"
        "    def load(path):\n"
        "        content = Path(path).read_text()\n"
        "        if content.rstrip().endswith('['):\n"
        "            raise ValueError(f'Malformed YAML: {path}')\n"
        "        return content\n"
        "    @staticmethod\n"
        "    def merge(*configs):\n"
        "        return configs\n"
    )
    (single / "omegaconf.py").write_text(fake_omegaconf)
    (double / "omegaconf.py").write_text(fake_omegaconf)
    (single / "datasets.py").write_text("class Mutation:\n    pass\n")
    (single / "analysis/custom_inference.py").write_text(
        "import argparse\n"
        "from datasets import Mutation\n"
        "argparse.ArgumentParser().parse_args()\n"
    )
    (single / "local.yaml").write_text(
        f"platform:\n  thermompnn_dir: {single.resolve()}\n"
    )
    (single / "models/thermoMPNN_default.pt").write_bytes(b"test")
    (single / "vanilla_model_weights/v_48_020.pt").write_bytes(b"test")
    (double / "v2_ssm.py").write_text(
        "import argparse\n"
        "from thermompnn.datasets.dataset_utils import Mutation\n"
        "argparse.ArgumentParser().parse_args()\n"
    )
    (double / "thermompnn/datasets/dataset_utils.py").write_text(
        "class Mutation:\n    pass\n"
    )
    (double / "examples/configs/local.yaml").write_text(
        f"platform:\n  thermompnn_dir: {double.resolve()}\n"
    )
    (double / "examples/configs/epistatic.yaml").write_text("model: {}\n")
    (double / "model_weights/ThermoMPNN-D-ens1.ckpt").write_bytes(b"test")
    (double / "vanilla_model_weights/v_48_020.pt").write_bytes(b"test")
    output.mkdir()
    return single, double, output


def test_colab_readiness_executes_cli_and_checks_real_boundaries(
    tmp_path: Path,
) -> None:
    single, double, output = _readiness_fixture(tmp_path)
    repository = Path.cwd().resolve()
    report = colab.validate_colab_readiness(
        python_executable=sys.executable,
        atlas_repo=repository,
        input_structure=repository / "data/23WN.cif",
        thermompnn_repo=single,
        thermompnn_d_repo=double,
        output_root=output,
        run_dir=output / "new-run",
        required_modules=("atlas", "atlas.cli", "atlas.colab"),
    )
    assert report["passed"] is True
    assert report["cli_entrypoint"] == "passed"
    assert report["output_writable"] is True


def test_colab_readiness_prefers_thermompnn_checkout_over_installed_datasets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    single, double, output = _readiness_fixture(tmp_path)
    repository = Path.cwd().resolve()
    conflicting = tmp_path / "site-packages"
    (conflicting / "datasets").mkdir(parents=True)
    (conflicting / "datasets/__init__.py").write_text("# unrelated package\n")
    (single / "datasets.py").write_text("class Mutation:\n    pass\n")
    (single / "analysis/custom_inference.py").write_text(
        "import argparse\n"
        "import os\n"
        "import sys\n"
        "root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))\n"
        "sys.path.append(root)\n"
        "from datasets import Mutation\n"
        "argparse.ArgumentParser().parse_args()\n"
    )
    monkeypatch.setenv("PYTHONPATH", str(conflicting))

    report = colab.validate_colab_readiness(
        python_executable=sys.executable,
        atlas_repo=repository,
        input_structure=repository / "data/23WN.cif",
        thermompnn_repo=single,
        thermompnn_d_repo=double,
        output_root=output,
        run_dir=output / "new-run",
        required_modules=("atlas", "atlas.cli", "atlas.colab"),
    )

    assert report["thermompnn_imports"] == "passed"


def test_colab_readiness_rejects_wrong_thermompnn_datasets_source(
    tmp_path: Path,
) -> None:
    single, double, output = _readiness_fixture(tmp_path)
    repository = Path.cwd().resolve()
    conflicting = tmp_path / "site-packages"
    (conflicting / "datasets").mkdir(parents=True)
    (conflicting / "datasets/__init__.py").write_text(
        "class Mutation:\n    pass\n"
    )
    (single / "analysis/custom_inference.py").write_text(
        "import argparse\n"
        "import sys\n"
        f"sys.path.insert(0, {str(conflicting)!r})\n"
        "from datasets import Mutation\n"
        "argparse.ArgumentParser().parse_args()\n"
    )

    with pytest.raises(colab.ColabReadinessError, match="datasets.*expected"):
        colab.validate_colab_readiness(
            python_executable=sys.executable,
            atlas_repo=repository,
            input_structure=repository / "data/23WN.cif",
            thermompnn_repo=single,
            thermompnn_d_repo=double,
            output_root=output,
            run_dir=output / "new-run",
            required_modules=("atlas", "atlas.cli", "atlas.colab"),
        )


def test_colab_readiness_rejects_wrong_thermompnn_d_bootstrap_source(
    tmp_path: Path,
) -> None:
    single, double, output = _readiness_fixture(tmp_path)
    repository = Path.cwd().resolve()
    conflicting = tmp_path / "site-packages"
    wrong_module = conflicting / "thermompnn/datasets/dataset_utils.py"
    wrong_module.parent.mkdir(parents=True)
    wrong_module.write_text("class Mutation:\n    pass\n")
    (double / "v2_ssm.py").write_text(
        "import argparse\n"
        "import sys\n"
        f"sys.path.insert(0, {str(conflicting)!r})\n"
        "from thermompnn.datasets.dataset_utils import Mutation\n"
        "argparse.ArgumentParser().parse_args()\n"
    )

    with pytest.raises(colab.ColabReadinessError, match="dataset_utils.*expected"):
        colab.validate_colab_readiness(
            python_executable=sys.executable,
            atlas_repo=repository,
            input_structure=repository / "data/23WN.cif",
            thermompnn_repo=single,
            thermompnn_d_repo=double,
            output_root=output,
            run_dir=output / "new-run",
            required_modules=("atlas", "atlas.cli", "atlas.colab"),
        )


@pytest.mark.parametrize(
    ("configuration", "message"),
    (("single", "ThermoMPNN inference bootstrap"), ("double", "ThermoMPNN-D inference bootstrap")),
)
def test_colab_readiness_rejects_malformed_upstream_configuration(
    tmp_path: Path, configuration: str, message: str
) -> None:
    single, double, output = _readiness_fixture(tmp_path)
    repository = Path.cwd().resolve()
    if configuration == "single":
        path = single / "local.yaml"
        checkout = single.resolve()
    else:
        path = double / "examples/configs/epistatic.yaml"
        checkout = double.resolve()
    path.write_text(
        f"platform:\n  thermompnn_dir: {checkout}\ninvalid: [\n"
    )

    with pytest.raises(colab.ColabReadinessError, match=message):
        colab.validate_colab_readiness(
            python_executable=sys.executable,
            atlas_repo=repository,
            input_structure=repository / "data/23WN.cif",
            thermompnn_repo=single,
            thermompnn_d_repo=double,
            output_root=output,
            run_dir=output / "new-run",
            required_modules=("atlas", "atlas.cli", "atlas.colab"),
        )


def test_colab_readiness_aggregates_missing_layout_and_writability(
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "not-a-directory"
    output_file.write_text("occupied")
    with pytest.raises(colab.ColabReadinessError) as error:
        colab.validate_colab_readiness(
            python_executable=sys.executable,
            atlas_repo=tmp_path / "missing-atlas",
            input_structure=tmp_path / "missing-23WN.cif",
            thermompnn_repo=tmp_path / "missing-single",
            thermompnn_d_repo=tmp_path / "missing-double",
            output_root=output_file,
            run_dir=output_file / "run",
            required_modules=("atlas",),
        )
    message = str(error.value)
    assert "Atlas repository layout" in message
    assert "23WN input" in message
    assert "ThermoMPNN required file" in message
    assert "ThermoMPNN-D required file" in message
    assert "Checkpoint root is not a writable directory" in message


def test_colab_readiness_rejects_partial_checkpoint_directory(
    tmp_path: Path,
) -> None:
    single, double, output = _readiness_fixture(tmp_path)
    repository = Path.cwd().resolve()
    run_dir = output / "partial-run"
    run_dir.mkdir()
    with pytest.raises(colab.ColabReadinessError, match="run_context.json"):
        colab.validate_colab_readiness(
            python_executable=sys.executable,
            atlas_repo=repository,
            input_structure=repository / "data/23WN.cif",
            thermompnn_repo=single,
            thermompnn_d_repo=double,
            output_root=output,
            run_dir=run_dir,
            required_modules=("atlas", "atlas.cli", "atlas.colab"),
        )


def test_upstream_runtime_paths_are_configured_to_exact_checkouts(
    tmp_path: Path,
) -> None:
    single, double, _ = _readiness_fixture(tmp_path)
    (single / "local.yaml").write_text(
        "platform:\n  accel: gpu\n  thermompnn_dir: /proj/kuhl_lab/ThermoMPNN\n"
    )
    (double / "examples/configs/local.yaml").write_text(
        "platform:\n  accel: gpu\n  thermompnn_dir: /proj/kuhl_lab/ThermoMPNN-D\n"
    )

    changed = colab.configure_upstream_runtime_paths(single, double)

    assert changed == [
        single / "local.yaml",
        double / "examples/configs/local.yaml",
    ]
    assert f'thermompnn_dir: "{single.resolve()}"' in changed[0].read_text()
    assert f'thermompnn_dir: "{double.resolve()}"' in changed[1].read_text()
    assert "accel: gpu" in changed[0].read_text()


def test_colab_readiness_rejects_unconfigured_upstream_runtime_path(
    tmp_path: Path,
) -> None:
    single, double, output = _readiness_fixture(tmp_path)
    repository = Path.cwd().resolve()
    (single / "local.yaml").write_text(
        "platform:\n  thermompnn_dir: /nonexistent/upstream/path\n"
    )
    with pytest.raises(colab.ColabReadinessError, match="thermompnn_dir"):
        colab.validate_colab_readiness(
            python_executable=sys.executable,
            atlas_repo=repository,
            input_structure=repository / "data/23WN.cif",
            thermompnn_repo=single,
            thermompnn_d_repo=double,
            output_root=output,
            run_dir=output / "new-run",
            required_modules=("atlas", "atlas.cli", "atlas.colab"),
        )


def test_notebook_runs_runtime_readiness_before_structure(tmp_path: Path) -> None:
    notebook = json.loads(Path("notebooks/Atlas_DP622_Colab.ipynb").read_text())
    tagged_indexes = {
        tag: index
        for index, cell in enumerate(notebook["cells"])
        for tag in cell.get("metadata", {}).get("tags", [])
    }
    assert tagged_indexes["runtime-readiness"] < tagged_indexes["structure"]


def test_notebook_configures_upstream_paths_before_preflight(tmp_path: Path) -> None:
    single, double, _ = _readiness_fixture(tmp_path)
    (single / "local.yaml").write_text(
        "platform:\n  thermompnn_dir: /authors/machine/ThermoMPNN\n"
    )
    (double / "examples/configs/local.yaml").write_text(
        "platform:\n  thermompnn_dir: /authors/machine/ThermoMPNN-D\n"
    )
    notebook = json.loads(Path("notebooks/Atlas_DP622_Colab.ipynb").read_text())
    tagged = {
        tag: (index, cell)
        for index, cell in enumerate(notebook["cells"])
        for tag in cell.get("metadata", {}).get("tags", [])
    }
    config_index, config_cell = tagged["upstream-runtime-config"]
    assert tagged["repository-setup"][0] < config_index < tagged["full-preflight"][0]

    exec("".join(config_cell["source"]), {"EXTERNAL": tmp_path})

    assert str(single.resolve()) in (single / "local.yaml").read_text()
    assert str(double.resolve()) in (
        double / "examples/configs/local.yaml"
    ).read_text()


def test_notebook_bootstrap_failure_prints_complete_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    notebook = json.loads(Path("notebooks/Atlas_DP622_Colab.ipynb").read_text())
    hardware_cell = next(
        cell
        for cell in notebook["cells"]
        if "hardware-check" in cell.get("metadata", {}).get("tags", [])
    )
    tree = ast.parse("".join(hardware_cell["source"]))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_bootstrap_command"
    )
    namespace = {"subprocess": subprocess}
    exec(
        compile(
            ast.Module(body=[function], type_ignores=[]),
            "notebook-bootstrap-wrapper",
            "exec",
        ),
        namespace,
    )
    command = [
        sys.executable,
        "-c",
        (
            "import sys; print('bootstrap stdout'); "
            "print('bootstrap stderr', file=sys.stderr); raise SystemExit(9)"
        ),
    ]
    with pytest.raises(RuntimeError, match="Repository setup"):
        namespace["run_bootstrap_command"](
            "Repository setup", command, cwd=tmp_path
        )
    diagnostic = capsys.readouterr().out
    assert "Stage: Repository setup" in diagnostic
    assert "bootstrap stdout" in diagnostic
    assert "bootstrap stderr" in diagnostic
    assert f"Working directory: {tmp_path}" in diagnostic
    assert "Suggested next action:" in diagnostic
