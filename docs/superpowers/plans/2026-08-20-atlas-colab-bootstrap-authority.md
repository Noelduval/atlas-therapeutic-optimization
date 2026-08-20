# Atlas Colab Bootstrap Authority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the next Atlas v1 Colab run use the checked-out Atlas code and one subprocess bootstrap authority through the boundary immediately before genuine ThermoMPNN inference.

**Architecture:** Add one subprocess specification for pinned upstream Python scripts; both readiness and the production ThermoMPNN/ThermoMPNN-D runners will obtain their Python executable, command, cwd, preserved environment, and checkout-first `PYTHONPATH` from it. Harden the notebook reinstall boundary so an Atlas module cached by an earlier run cannot survive a checkout update, and cover that exact stale-kernel failure with an installed-package regression.

**Tech Stack:** Python 3.12, subprocess, pytest, Jupyter notebook JSON, Git, ThermoMPNN, ThermoMPNN-D.

**Spec:** `/Users/noelduval/.codex/attachments/bfdf1e98-3c2c-4bcd-8ef1-a15eef9dee8f/pasted-text.txt`

## Global Constraints

- Preserve DP622 reconstruction assumptions, 23WN input, published mutation controls, pinned ThermoMPNN/ThermoMPNN-D revisions, scoring semantics, geometry definitions, OpenMM semantics, validation thresholds/gate, and candidate ranking.
- Do not run GPU inference or introduce fallback scores.
- Fix only demonstrated setup, import, environment, command-construction, and checkpoint/resume blockers.
- Both readiness and genuine model subprocesses must consume the same bootstrap authority.
- Readiness must fail closed on incorrect module provenance.

---

### Task 1: Shared upstream subprocess authority

**Files:**
- Create: `src/atlas/stability/upstream_execution.py`
- Modify: `src/atlas/stability/thermompnn_runner.py`
- Modify: `src/atlas/stability/thermompnn_d_runner.py`
- Test: `tests/stability/test_runners.py`

**Interfaces:**
- Consumes: Python executable, upstream repository path, upstream script path, optional inherited environment.
- Produces: `UpstreamPythonExecution.command(*arguments) -> list[str]`, `.cwd -> Path`, and `.environment() -> dict[str, str]` with checkout-first module resolution.

- [ ] **Step 1: Write failing runner tests**

Add tests that capture the actual command runner arguments for both official runners and assert literal values for `cwd`, Python executable, script path, preserved sentinel environment data, and a `PYTHONPATH` whose first entry is the corresponding checkout. The ThermoMPNN test must include a conflicting `datasets` package; the ThermoMPNN-D test must include a conflicting `thermompnn` package.

- [ ] **Step 2: Verify the tests fail for the missing shared contract**

Run: `/tmp/atlas-final-env.LeQ36g/bin/python -m pytest tests/stability/test_runners.py -q`

Expected: FAIL because ThermoMPNN-D does not pass an environment and no single execution authority constructs both runners.

- [ ] **Step 3: Implement the minimal authority and adopt it in both runners**

Implement an immutable execution object that resolves the repository/script/Python paths, copies the inherited environment, prepends the checkout to `PYTHONPATH` without discarding existing entries, and returns the exact script command. Replace the ThermoMPNN-specific environment helper and ThermoMPNN-D's default runner path with this object; do not change inference flags or output handling.

- [ ] **Step 4: Verify the runner tests pass**

Run: `/tmp/atlas-final-env.LeQ36g/bin/python -m pytest tests/stability/test_runners.py -q`

Expected: PASS.

### Task 2: Readiness consumes the production bootstrap authority

**Files:**
- Modify: `src/atlas/colab.py`
- Test: `tests/test_colab.py`

**Interfaces:**
- Consumes: `UpstreamPythonExecution` for each pinned checkout.
- Produces: cheap top-level bootstrap probes that use the same Python executable, cwd, environment, and script-path setup as production while stopping before `__main__` inference.

- [ ] **Step 1: Write failing readiness parity tests**

Add tests that monkeypatch the shared execution builder and assert readiness and each genuine runner receive equivalent checkout, Python, cwd, and environment settings. Extend provenance tests so both conflicting packages expose a compatible `Mutation`; readiness must still reject any non-checkout source.

- [ ] **Step 2: Verify the tests fail against separate readiness construction**

Run: `/tmp/atlas-final-env.LeQ36g/bin/python -m pytest tests/test_colab.py tests/stability/test_runners.py -q`

Expected: FAIL because readiness still builds commands/environments independently and ThermoMPNN-D readiness/production are not unified.

- [ ] **Step 3: Route bootstrap probes through the shared execution object**

Keep `runpy.run_path(..., run_name='_atlas_readiness_bootstrap')` so top-level imports/config loads execute without entering genuine inference. Build that probe from the shared object's Python, cwd, checkout-first environment, and script path, then verify the exact module files and `Mutation` symbols.

- [ ] **Step 4: Verify readiness tests pass**

Run: `/tmp/atlas-final-env.LeQ36g/bin/python -m pytest tests/test_colab.py tests/stability/test_runners.py -q`

Expected: PASS.

### Task 3: Eliminate stale Atlas modules after notebook reinstall

**Files:**
- Modify: `notebooks/Atlas_DP622_Colab.ipynb`
- Test: `tests/test_colab.py`

**Interfaces:**
- Consumes: the repository setup cell's completed Atlas installation and resolved `ATLAS_SHA`.
- Produces: a kernel whose subsequent `from atlas...` imports resolve from the newly installed checkout, even if an older Atlas version was already imported earlier in the runtime.

- [ ] **Step 1: Write the exact stale-kernel regression**

In a fresh Python 3.12 subprocess, install Atlas `a8ca15c` into an isolated target, import `atlas.colab`, reinstall the current checkout as the notebook does, execute the notebook's activation function, and assert a subsequent import exposes the new bootstrap API and current installed file. Then invoke the actual `validate_colab_readiness()` with a conflicting Hugging Face-style `datasets` package and checkout-local `Mutation`.

- [ ] **Step 2: Verify the regression reproduces the traceback**

Run the targeted regression with `/tmp/atlas-final-env.LeQ36g/bin/python -m pytest tests/test_colab.py -k stale -q`.

Expected: FAIL with the cached pre-f35 readiness function and `ImportError: cannot import name 'Mutation' from 'datasets'`.

- [ ] **Step 3: Make notebook installation and activation deterministic**

After dependency installation, force-reinstall only Atlas from `ATLAS_DIR` with `--no-deps --no-cache-dir`, invalidate import caches, remove existing `atlas` and `atlas.*` entries from `sys.modules`, and import Atlas again. Assert in-kernel package provenance/version after activation. Do not restart the runtime or alter scientific packages.

- [ ] **Step 4: Verify the stale-kernel regression passes**

Run the same targeted test and confirm the actual readiness entrypoint passes with checkout-local provenance.

### Task 4: Realistic installed-environment and cheap path verification

**Files:**
- Create: `tests/integration/test_colab_installed_readiness.py`
- Modify: `tests/test_colab.py` only if a reusable notebook-cell test utility is needed.

**Interfaces:**
- Consumes: environment variables naming a clean Python 3.12 interpreter and pinned real upstream checkouts.
- Produces: an opt-in regression that installs the current Atlas checkout normally, imports it from site-packages, runs `validate_colab_readiness()`, emits exact module provenance, and reaches the reconstruction stop boundary without model inference.

- [ ] **Step 1: Add the opt-in real-checkout integration test**

Require explicit paths to the Python 3.12 interpreter, ThermoMPNN commit `2b04fd370e399911b1fa5848112cc9013f084110`, and ThermoMPNN-D commit `df9a75aaddb674a7c4c193005031fc0536d325fb`. Skip only when those inputs are absent; fail on wrong revisions or wrong module files.

- [ ] **Step 2: Run the integration test in the prepared clean environment**

Run with the existing `/tmp/atlas-final-env.LeQ36g`, `/tmp/atlas-single-final.yizES4`, and `/tmp/atlas-double-final.1vLDbb` inputs. Confirm installed Atlas provenance, Hugging Face `datasets` presence, exact checkout-local model module provenance, successful CLI/preflight/readiness, and `stopped_after_structure`.

- [ ] **Step 3: Exercise command construction without inference**

Instantiate both shared execution objects using the real pinned scripts and assert the literal production command flags, cwd, Python executable, and environment. Do not execute either genuine inference command.

- [ ] **Step 4: Verify checkpoint/resume tests**

Run: `/tmp/atlas-final-env.LeQ36g/bin/python -m pytest tests/test_pipeline.py tests/test_run_context.py -q`

Expected: PASS, including reuse of valid single-model and later-stage checkpoints.

### Task 5: Final scoped verification and publication

**Files:**
- Review every modified path from Tasks 1-4 and this plan.

**Interfaces:**
- Consumes: completed implementation and tests.
- Produces: one scoped commit pushed to `codex/atlas-v1-dynamic-geometry` and verified by remote SHA.

- [ ] **Step 1: Run the complete relevant cheap suite**

Run the preflight, Colab, runner, pipeline, CLI, reconstruction, and run-context tests from a clean Python 3.12 process. Run the opt-in installed-environment regression separately with real pinned checkouts.

- [ ] **Step 2: Review scope and scientific invariants**

Inspect `git diff`, confirm no scoring/reconstruction/geometry/validation/ranking/checkpoint provenance semantics changed, and confirm no checkpoint/model revision changed.

- [ ] **Step 3: Stage only scoped paths and review the staged diff**

Use `git add -- <explicit paths>` and `git diff --cached --check`; never use a broad add command.

- [ ] **Step 4: Commit and push**

Commit with a concise Colab/ThermoMPNN bootstrap message, push `codex/atlas-v1-dynamic-geometry`, and query `refs/heads/codex/atlas-v1-dynamic-geometry` to prove the remote SHA equals HEAD.
