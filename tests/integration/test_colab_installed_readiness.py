from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest


THERMOMPNN_REVISION = "2b04fd370e399911b1fa5848112cc9013f084110"
THERMOMPNN_D_REVISION = "df9a75aaddb674a7c4c193005031fc0536d325fb"


def _required_external_path(name: str, *, resolve: bool = True) -> Path:
    value = os.environ.get(name)
    if not value:
        pytest.skip(f"{name} is required for the real installed-Colab regression")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    if resolve:
        path = path.resolve()
    if not path.exists():
        pytest.fail(f"{name} does not exist: {path}")
    return path


def _revision(repository: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def test_installed_colab_path_reaches_model_inference_boundary(
    tmp_path: Path,
) -> None:
    python = _required_external_path("ATLAS_COLAB_PYTHON", resolve=False)
    single = _required_external_path("ATLAS_THERMOMPNN_REPO")
    double = _required_external_path("ATLAS_THERMOMPNN_D_REPO")
    assert _revision(single) == THERMOMPNN_REVISION
    assert _revision(double) == THERMOMPNN_D_REVISION

    repository = Path.cwd().resolve()
    installed = tmp_path / "site-packages"
    installation = subprocess.run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--quiet",
            "--no-deps",
            "--no-cache-dir",
            "--target",
            str(installed),
            str(repository),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert installation.returncode == 0, installation.stderr

    output = tmp_path / "outputs"
    output.mkdir()
    driver = f"""
import os
from pathlib import Path
import subprocess
import sys

installed = Path({str(installed)!r})
repository = Path({str(repository)!r})
single = Path({str(single)!r})
double = Path({str(double)!r})
output = Path({str(output)!r})
sys.path.insert(0, str(installed))
os.environ['PYTHONPATH'] = os.pathsep.join([
    str(installed), os.environ.get('PYTHONPATH', '')
]).rstrip(os.pathsep)

import atlas
import atlas.colab as colab
import datasets as hugging_face_datasets
from atlas.stability.common import ScientificOutputError, StabilityVariant
from atlas.stability.thermompnn_runner import ThermoMPNNRunner
from atlas.stability.thermompnn_d_runner import ThermoMPNNDRunner
from atlas.stability.upstream_execution import UpstreamPythonExecution

atlas_file = Path(atlas.__file__).resolve()
assert installed in atlas_file.parents, atlas_file
hf_datasets_file = Path(hugging_face_datasets.__file__).resolve()
assert 'site-packages' in hf_datasets_file.parts, hf_datasets_file
colab.configure_upstream_runtime_paths(single, double)

report = colab.validate_colab_readiness(
    python_executable=sys.executable,
    atlas_repo=repository,
    input_structure=repository / 'data/23WN.cif',
    thermompnn_repo=single,
    thermompnn_d_repo=double,
    output_root=output,
    run_dir=output / 'installed-colab',
)
assert report['passed'] is True

single_execution = UpstreamPythonExecution.create(
    single, 'analysis/custom_inference.py', python_executable=sys.executable
)
single_probe = subprocess.run(
    colab._bootstrap_probe_command(
        single_execution,
        'datasets',
        single / 'datasets.py',
        'Mutation',
        (single / 'local.yaml',),
    ),
    cwd=single_execution.cwd,
    env=single_execution.environment(),
    text=True,
    capture_output=True,
    check=False,
)
assert single_probe.returncode == 0, single_probe.stderr

double_execution = UpstreamPythonExecution.create(
    double, 'v2_ssm.py', python_executable=sys.executable
)
double_probe = subprocess.run(
    colab._bootstrap_probe_command(
        double_execution,
        'thermompnn.datasets.dataset_utils',
        double / 'thermompnn/datasets/dataset_utils.py',
        'Mutation',
        (double / 'examples/configs/local.yaml', double / 'examples/configs/epistatic.yaml'),
    ),
    cwd=double_execution.cwd,
    env=double_execution.environment(),
    text=True,
    capture_output=True,
    check=False,
)
assert double_probe.returncode == 0, double_probe.stderr

run_id = 'installed-colab'
structure_command = [
    sys.executable, '-m', 'atlas', 'run',
    '--input', str(repository / 'data/23WN.cif'),
    '--output-root', str(output),
    '--atlas-repo', str(repository),
    '--thermompnn-repo', str(single),
    '--thermompnn-d-repo', str(double),
    '--dynamics-mode', 'minimize',
    '--run-id', run_id,
    '--stop-after', 'structure',
]
structure = subprocess.run(
    structure_command,
    cwd=output,
    env=os.environ.copy(),
    text=True,
    capture_output=True,
    check=False,
)
assert structure.returncode == 0, structure.stderr
assert 'stopped_after_structure' in structure.stdout
reconstructed = output / run_id / 'DP622_active_like_reconstruction.pdb'
before_resume = reconstructed.stat().st_mtime_ns
resumed = subprocess.run(
    [*structure_command, '--resume'],
    cwd=output,
    env=os.environ.copy(),
    text=True,
    capture_output=True,
    check=False,
)
assert resumed.returncode == 0, resumed.stderr
assert reconstructed.stat().st_mtime_ns == before_resume

captured = {{}}
def stop_single(command, **kwargs):
    captured['single'] = (command, kwargs)
    return subprocess.CompletedProcess(command, 86, '', 'intentional pre-inference stop')
try:
    ThermoMPNNRunner(single, command_runner=stop_single).run(
        reconstructed,
        [StabilityVariant('Y91F', 'Y91F', 'Y115F')],
        output / 'single-command',
    )
except ScientificOutputError as exc:
    assert 'intentional pre-inference stop' in str(exc)
else:
    raise AssertionError('ThermoMPNN command did not stop at the capture boundary')

def stop_double(command, **kwargs):
    captured['double'] = (command, kwargs)
    return subprocess.CompletedProcess(command, 86, '', 'intentional pre-inference stop')
try:
    ThermoMPNNDRunner(double, command_runner=stop_double).run(
        reconstructed,
        [StabilityVariant('Y91F_D126A', 'Y91F:D126A', 'Y115F:D150A')],
        output / 'double-command',
    )
except ScientificOutputError as exc:
    assert 'intentional pre-inference stop' in str(exc)
else:
    raise AssertionError('ThermoMPNN-D command did not stop at the capture boundary')

single_command, single_kwargs = captured['single']
double_command, double_kwargs = captured['double']
assert single_command[:2] == [sys.executable, str((single / 'analysis/custom_inference.py').resolve())]
assert double_command[:2] == [sys.executable, str((double / 'v2_ssm.py').resolve())]
assert single_kwargs['cwd'] == single.resolve()
assert double_kwargs['cwd'] == double.resolve()
assert single_kwargs['env']['PYTHONPATH'].split(os.pathsep)[0] == str(single.resolve())
assert double_kwargs['env']['PYTHONPATH'].split(os.pathsep)[0] == str(double.resolve())

print('ATLAS_PACKAGE=' + str(atlas_file))
print('HF_DATASETS=' + str(hf_datasets_file))
print('THERMOMPNN_PROVENANCE=' + single_probe.stdout.strip())
print('THERMOMPNN_D_PROVENANCE=' + double_probe.stdout.strip())
print('STRUCTURE_BOUNDARY=stopped_after_structure')
print('RESUME_REUSED=true')
print('COMMANDS_BUILT=true')
"""
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [str(python), "-c", driver],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert f"ATLAS_PACKAGE={installed / 'atlas/__init__.py'}" in completed.stdout
    assert "HF_DATASETS=" in completed.stdout
    assert (
        "THERMOMPNN_PROVENANCE=Bootstrap imported datasets from "
        f"{single / 'datasets.py'}"
    ) in completed.stdout
    assert (
        "THERMOMPNN_D_PROVENANCE=Bootstrap imported "
        "thermompnn.datasets.dataset_utils from "
        f"{double / 'thermompnn/datasets/dataset_utils.py'}"
    ) in completed.stdout
    assert "STRUCTURE_BOUNDARY=stopped_after_structure" in completed.stdout
    assert "RESUME_REUSED=true" in completed.stdout
    assert "COMMANDS_BUILT=true" in completed.stdout
