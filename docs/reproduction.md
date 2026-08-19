# Reproduction

## Supported paths

The reviewer path is the GPU Colab notebook. Local CPU execution supports the
structure, geometry, gate logic, tests, and an honest OpenMM attempt, but the
pinned ThermoMPNN-D epistatic implementation requires CUDA.

## Docker strategy

Atlas v1 intentionally has no Dockerfile. The scientific pivot removes Rosetta,
so neither a custom Rosetta build nor an official Rosetta image is relevant to
the active workflow. The official ThermoMPNN projects publish Conda guidance and
Colab notebooks rather than a versioned Atlas-compatible container. A bespoke
image would add a CUDA/PyTorch maintenance surface without improving the primary
reviewer path. The committed Colab notebook, pinned Git revisions, bounded Python
dependencies, input checksum, and per-run provenance are the reproducibility
mechanism for v1. A future container should be added only after validating a
specific CUDA base image against both pinned predictors.

## Local setup

```bash
git clone https://github.com/Noelduval/atlas-therapeutic-optimization.git Atlas
cd Atlas
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,dynamics]'
python -m pytest -q
```

Structural-only command:

```bash
atlas reconstruct --input data/23WN.cif --output-dir outputs/reconstruction
```

## External stability models

Atlas does not vendor or silently install scientific models. Clone the official
repositories and check out the exact commits recorded in `provenance.json`:

```bash
mkdir -p .external
git clone https://github.com/Kuhlman-Lab/ThermoMPNN.git .external/ThermoMPNN
git -C .external/ThermoMPNN checkout 2b04fd370e399911b1fa5848112cc9013f084110
git clone https://github.com/Kuhlman-Lab/ThermoMPNN-D.git .external/ThermoMPNN-D
git -C .external/ThermoMPNN-D checkout df9a75aaddb674a7c4c193005031fc0536d325fb
python -m pip install omegaconf wandb pytorch-lightning scipy scikit-learn joblib
```

Confirm that the active Python environment sees CUDA before the full run:

```bash
python -c 'import torch; print(torch.__version__, torch.cuda.is_available())'
```

Exact full command:

```bash
atlas run --input data/23WN.cif --output-root outputs --thermompnn-repo .external/ThermoMPNN --thermompnn-d-repo .external/ThermoMPNN-D --dynamics-mode minimize
```

Use `--dynamics-mode short-md` for restrained 10 ps dynamics or
`--dynamics-mode skip` for an explicitly static-only run. Skipping OpenMM is not
the same as passing dynamic geometry. Every command creates a new UTC-stamped
directory and refuses to overwrite an existing run.

## Colab

1. Open `notebooks/Atlas_DP622_Colab.ipynb` in Google Colab.
2. Choose **Runtime → Change runtime type → GPU**.
3. Run all cells in order.
4. Inspect `known_mutation_validation.csv` before interpreting any novel files.
5. Download the generated ZIP from the final cell.

The notebook uses the repository's committed 23WN file. An optional cell can
mount Drive for persistent output; no Rosetta license, Docker image, or cloud VM
setup is involved.

## Expected runtime

| Stage | Typical reviewer-scale estimate |
| --- | --- |
| Environment/model installation | 5–15 min |
| Reconstruction + five static geometries | <1 min |
| ThermoMPNN single-site sweep | 1–5 min on GPU; hardware dependent |
| ThermoMPNN-D epistatic sweep | 1–10 min on GPU; hardware dependent |
| OpenMM minimization attempts | 1–10 min total; may skip during setup |
| Conditional candidate phase | 5–20 min, depending on candidate count |

These are operational estimates, not performance guarantees. `short-md` can add
10–60 minutes if all systems parameterize successfully.

## Reproducibility records

`provenance.json` records the input SHA-256, Python/platform details, model
commits, dynamics mode, UTC time, and claim boundary. `pipeline_warnings.md`
records missing evidence. Raw external CSVs remain under the run's `stability/`
subdirectories and normalized scores are copied to stable top-level schemas.
