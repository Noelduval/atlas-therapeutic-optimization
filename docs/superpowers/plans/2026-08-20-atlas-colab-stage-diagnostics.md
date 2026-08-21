# Atlas Colab Stage Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a clean normal-installed Atlas checkout complete Colab Stage 3 and expose complete evidence for every future CLI failure.

**Architecture:** Pass the checkout path explicitly through the notebook command, Typer CLI, `PipelineConfig`, and run-context builder instead of inferring it from installed package files. Keep Colab orchestration in `atlas.colab`: a read-only readiness validator checks cheap boundaries before Stage 3, and one fail-closed stage runner captures and reports complete subprocess evidence.

**Tech Stack:** Python 3.10–3.12, Typer, subprocess, pathlib, pytest, Jupyter/Colab.

**Spec:** `docs/superpowers/specs/2026-08-20-atlas-colab-stage-diagnostics.md`

## Global Constraints

- Do not change the scientific workflow, controls, thresholds, models, OpenMM policy, validation gate, or candidate gate.
- Use the exact pinned ThermoMPNN and ThermoMPNN-D revisions already committed.
- All failures remain hard failures; diagnostics must never continue downstream.
- The supported reviewer baseline remains a clean standard Colab T4 runtime.

---

### Task 1: Installation-independent Atlas provenance

**Files:**
- Modify: `src/atlas/run_context.py`
- Modify: `src/atlas/pipeline.py`
- Modify: `src/atlas/cli.py`
- Modify: `src/atlas/colab.py`
- Test: `tests/test_run_context.py`
- Test: `tests/test_colab.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Add `PipelineConfig.atlas_repo: Path` with default `Path(".")`.
- Add CLI option `atlas run --atlas-repo PATH`.
- Add required `atlas_repo` to `build_stage_command(...)`.
- Resolve `RunContext.atlas_commit` using the explicit checkout path.

- [x] Add a failing normal-install integration test that executes the real
  structure checkpoint from the checkout and expects exit code 0.
- [x] Add failing unit tests for the explicit `--atlas-repo` command and
  checkout SHA resolution.
- [x] Run the focused tests and confirm the failure is the reproduced
  site-packages provenance error or missing interface.
- [x] Implement the explicit checkout path through all layers.
- [x] Run focused tests and the normal-install Stage 3 reproduction green.

### Task 2: Fail-closed stage diagnostics

**Files:**
- Modify: `src/atlas/colab.py`
- Modify: `notebooks/Atlas_DP622_Colab.ipynb`
- Test: `tests/test_colab.py`

**Interfaces:**
- Add `StageExecutionError`.
- Add `run_stage_command(stage_name, command, cwd, *, environment=None,
  suggested_next_action=...) -> subprocess.CompletedProcess[str]`.

- [x] Add a failing real-subprocess test whose command writes distinct stdout
  and stderr and exits 2; assert the diagnostic contains every required field.
- [x] Implement capture, complete diagnostic printing, safe environment
  whitelisting, and a raised `StageExecutionError` after evidence is emitted.
- [x] Replace notebook `subprocess.run(check=True)` stage execution with the
  production helper; keep all stage order and hard-stop behavior unchanged.
- [x] Run diagnostic tests green.

### Task 3: Pre-Stage-3 Colab readiness gate

**Files:**
- Modify: `src/atlas/colab.py`
- Modify: `notebooks/Atlas_DP622_Colab.ipynb`
- Test: `tests/test_colab.py`

**Interfaces:**
- Add `ColabReadinessError` and `validate_colab_readiness(...) -> dict[str,
  object]`.
- Validate exact checkout layout, input/model scripts and weights, importable
  runtime modules, `python -m atlas --help`, upstream script `--help` imports,
  writable output root, and absence of an invalid partial run directory.

- [x] Add failing tests using real temporary files/processes for missing layout,
  non-writable/invalid checkpoint state, failed CLI entrypoint, and a passing
  local boundary.
- [x] Implement the read-only validator with aggregated human-readable errors.
- [x] Invoke it after the GPU/source preflight and before defining/running Stage
  3; print its machine-readable report.
- [x] Run readiness and notebook-contract tests green.

### Task 4: Clean-runtime compatibility audit and publication

**Files:**
- Modify only documentation if the audit finds a proven requirement.

**Interfaces:** None.

- [x] Audit the two pinned upstream inference scripts and committed model files
  against notebook-installed packages without changing scientific behavior.
- [x] Execute a clean normal-install Stage 3, notebook JSON/code compilation,
  CLI help, focused regressions, and the full test suite.
- [x] Inspect the final diff for scientific changes and confirm a clean worktree
  after commit.
- [ ] Commit and push the narrow engineering fix to the existing draft PR; do
  not merge.
