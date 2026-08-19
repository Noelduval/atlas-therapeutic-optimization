# Atlas Colab T4 Execution-Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish an unmerged Atlas v1 draft PR whose notebook safely runs and resumes the genuine benchmark on a standard Colab T4.

**Architecture:** Add a lightweight production preflight and provenance-bound staged resume support to the existing CLI. Keep all scientific calculations in the package; the notebook calls successive `atlas run --resume --stop-after ...` checkpoints so model processes release GPU memory and completed evidence survives later failures.

**Tech Stack:** Python 3.10–3.12, Typer, Biopython, pandas, PyTorch/CUDA supplied by Colab, pinned ThermoMPNN repositories, OpenMM, Jupyter/Colab.

**Spec:** `docs/superpowers/specs/2026-08-20-atlas-colab-t4-execution-readiness.md`

## Global Constraints

- Baseline accelerator is NVIDIA Tesla T4 with approximately 15 GB VRAM.
- Keep ThermoMPNN `2b04fd370e399911b1fa5848112cc9013f084110` and ThermoMPNN-D `df9a75aaddb674a7c4c193005031fc0536d325fb`.
- Do not change the fixed benchmark thresholds or generate candidates before a genuine gate pass.
- Do not add notebook-only scientific calculations or fake production outputs.
- Do not merge the pull request.

---

### Task 1: Lightweight CUDA and source preflight

**Files:** Create `src/atlas/preflight.py`, `tests/test_preflight.py`; modify `src/atlas/cli.py`.

**Interfaces:** `run_preflight(input_structure, atlas_repo, thermompnn_repo, thermompnn_d_repo, command_runner=...) -> PreflightReport`; CLI `atlas preflight ... --output-json PATH`.

- [x] Write tests with injected NVIDIA/PyTorch probes proving a valid T4-shaped environment reports all SHAs and that missing CUDA or malformed 23WN fails before inference.
- [x] Run `pytest tests/test_preflight.py -q` and observe missing-module failure.
- [x] Implement commit resolution, `nvidia-smi` parsing, PyTorch CUDA checks, mmCIF parsing, Atlas import metadata, and JSON serialization.
- [x] Run `pytest tests/test_preflight.py -q` and require a pass.

### Task 2: Provenance-bound staged resume

**Files:** Create `src/atlas/run_context.py`, `tests/test_run_context.py`; modify `src/atlas/pipeline.py`, `src/atlas/cli.py`, stability provider code, and `tests/test_pipeline.py`.

**Interfaces:** `prepare_run_directory(config) -> Path`; `validate_run_context(path, expected) -> None`; `PipelineConfig.resume`; `PipelineConfig.stop_after`; CLI flags `--run-id`, `--resume`, `--stop-after`.

- [x] Write failing tests proving an identical context resumes, an Atlas/input/model mismatch is rejected, and a stopped/resumed run reuses real-shaped stage CSVs.
- [x] Implement `run_context.json` with Atlas SHA, input SHA-256, pinned model SHAs, dynamics mode, and gate-policy version.
- [x] Split official known scoring into cached single and double stages; validate schemas and requested IDs on every cache read.
- [x] Implement ordered stop points `structure`, `thermompnn`, `thermompnn-d`, `geometry`, `dynamics`, and `validation` without moving scientific logic into the notebook.
- [x] Run `pytest tests/test_run_context.py tests/test_pipeline.py tests/test_cli.py -q` and require a pass.

### Task 3: Scientifically defensible OpenMM fragment setup

**Files:** Modify `src/atlas/dynamics/openmm_minimize.py`, `tests/dynamics/test_openmm.py`, `docs/scientific_decisions.md`, `docs/limitations.md`.

**Interfaces:** `_prepare_system` adds hydrogens without fabricating heavy atoms and calls Amber template matching with `ignoreExternalBonds=True`.

- [ ] Add a failing test that records the heavy-atom count and requires the committed fragment to parameterize or preserve the explicit skip result.
- [ ] Run the test and reproduce the terminal ALA template failure.
- [ ] Apply OpenMM's documented fragment matching option without adding caps, residues, or heavy atoms.
- [ ] Run the real local minimization attempt and record whether it completes or the next exact scientific blocker.

### Task 4: Branch-aware staged Colab notebook

**Files:** Modify `notebooks/Atlas_DP622_Colab.ipynb`, `README.md`, `docs/reproduction.md`; create `tests/test_notebook_contract.py`.

**Interfaces:** Visible `ATLAS_REF`; configuration-derived `RUN_ID`; full `atlas preflight`; staged production CLI calls with `--resume` and `--stop-after`; optional Drive checkpoint root.

- [ ] Write a failing notebook-contract test for the configured branch, user instructions, preflight, stage headings, production CLI use, resume flags, and export cell.
- [ ] Rewrite notebook cells with short first-time-user instructions and clear progress messages.
- [ ] Use separate CLI processes for ThermoMPNN and ThermoMPNN-D and show each output before continuing.
- [ ] Validate notebook JSON, compile code cells, and run the contract test.

### Task 5: Verify and publish without merge

**Files:** Update this plan checklist only; no scientific source changes.

- [ ] Install the editable package and run the complete test suite in one persistent terminal session.
- [ ] Verify a clean diff against `main`, exact commit count/content, CLI help, notebook contract, and structural reconstruction.
- [ ] Commit the readiness changes, push `codex/atlas-v1-dynamic-geometry`, and confirm the remote SHA.
- [ ] Create a draft PR into `main` with scientific status and validation evidence; do not merge.
- [ ] Confirm the PR file list contains only intended Atlas v1 changes and report the PR URL plus first Colab action.
