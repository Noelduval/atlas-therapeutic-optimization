# Atlas Colab Single-Interpreter Completion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the real DP622 Colab benchmark with one pinned, supported scientific interpreter and reviewer-grade run provenance.

**Architecture:** The Colab host kernel remains orchestration-only. A pinned uv release creates a managed CPython 3.10 environment because both pinned upstream repositories specify Python 3.10 and CUDA 11.7/11.8; every Atlas and model operation runs through that environment. The production pipeline writes `run_manifest.json` beside the existing provenance and checkpoint records.

**Tech Stack:** Google Colab T4, uv-managed CPython 3.10, PyTorch 2.5.1 CUDA 11.8, Python, pytest, Jupyter notebook JSON, ThermoMPNN, ThermoMPNN-D, OpenMM.

**Spec:** `/Users/noelduval/.codex/attachments/2d8437cc-27e5-4669-b1bb-586e3412e79e/pasted-text.txt`

## Global Constraints

- Preserve 23WN provenance, reconstruction assumptions, protected sites, mutation controls, upstream revisions, scoring semantics, geometry definitions, OpenMM semantics, validation thresholds, and ranking criteria.
- Use genuine pinned models; never add substitute, mock, random, heuristic, or fallback production scores.
- The Colab host may orchestrate, but it must not import or execute Atlas scientific code.
- Preflight, readiness, reconstruction, both model runners, geometry, OpenMM, validation, candidate generation, and ranking must use one scientific executable.
- Candidate generation remains physically downstream of the unchanged validation gate.

---

### Task 1: Single scientific interpreter contract

**Files:**
- Modify: `tests/test_colab.py`
- Modify: `notebooks/Atlas_DP622_Colab.ipynb`

**Interfaces:**
- Produces `SCIENTIFIC_PYTHON = /content/atlas-science/bin/python` from a uv-managed CPython 3.10 environment.
- All production subprocess commands consume `SCIENTIFIC_PYTHON`; `sys.executable` is host provenance only.

- [x] Add tests that execute the notebook's command builders with a distinct fake host and scientific executable and require all Atlas commands to use the scientific executable.
- [x] Run `python -m pytest tests/test_colab.py -q` and confirm the new contract fails because the notebook uses `sys.executable` and imports Atlas in the host kernel.
- [x] Replace the setup and activation cells with a pinned uv/CPython 3.10 bootstrap and an orchestration-only provenance cell.
- [x] Invoke upstream configuration and readiness inside the scientific interpreter; build staged CLI commands without host Atlas imports.
- [x] Re-run `python -m pytest tests/test_colab.py -q` and require a pass.

### Task 2: Reviewer-grade run manifest

**Files:**
- Modify: `src/atlas/reporting/csv_outputs.py`
- Modify: `src/atlas/pipeline.py`
- Modify: `tests/test_pipeline.py`

**Interfaces:**
- Produces `<run_dir>/run_manifest.json` containing run ID, checkpoint directory, Atlas commit, input SHA-256, both upstream commits, dynamics mode, validation policy, Python/runtime packages, and claim boundary.

- [x] Add failing pipeline tests requiring `run_manifest.json` for both a stopped reconstruction checkpoint and a completed validation run.
- [x] Run the focused tests and confirm failure because only `run_context.json` and `provenance.json` exist.
- [x] Write the manifest from the production pipeline using the existing run context and provenance writer; do not derive scientific outcomes or scores.
- [x] Re-run the focused tests and verify the manifest agrees with `run_context.json` and the actual run directory.

### Task 3: Documentation and scoped verification

**Files:**
- Modify: `README.md`
- Modify: `docs/reproduction.md`
- Review: all Task 1-2 paths.

**Interfaces:** None.

- [x] Document the pinned scientific interpreter/CUDA stack and host-orchestrator boundary.
- [x] Run notebook JSON parsing/code compilation plus Colab, pipeline, run-context, preflight, CLI, stability-runner, reconstruction, geometry, validation, and OpenMM tests.
- [x] Inspect the diff and verify no protected scientific constants or model revisions changed.
- [ ] Stage only scoped paths, commit, push `codex/atlas-v1-dynamic-geometry`, and verify the remote SHA.

### Task 4: Real Colab completion loop

**Files:**
- Observe/execute: `notebooks/Atlas_DP622_Colab.ipynb`
- Preserve: the run directory printed by the notebook.

**Interfaces:**
- Consumes a fresh Google Colab T4 runtime and the pushed branch SHA.
- Produces either a completed validated candidate run or a scientifically valid negative validation result with candidates withheld.

- [ ] Start a fresh T4, run configuration/hardware/setup, and verify the compact provenance block.
- [ ] Require preflight and readiness to prove checkout-first model namespaces from the pinned checkouts.
- [ ] Run reconstruction, ThermoMPNN, ThermoMPNN-D, geometry, OpenMM, and validation in order, reusing provenance-valid checkpoints after engineering fixes.
- [ ] If the unchanged gate passes, run conditional candidate generation and ranking; if it fails, stop without candidate artifacts.
- [ ] Inspect `DP622_active_like_reconstruction.pdb`, `known_mutation_validation.csv`, `validation_report.md`, `run_manifest.json`, checkpoints, status, and any gated candidate artifacts for internal agreement.
- [ ] Package the reviewer ZIP and record the final Atlas/model/input/runtime provenance and remote branch SHA.
