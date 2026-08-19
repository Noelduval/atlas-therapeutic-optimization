# Atlas v1 Dynamic Geometry-Gated Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the synthetic Atlas demo with a runnable, Colab-compatible DP622 active-like reconstruction, stability triage, geometry screening, hard validation gate, and conditional candidate-ranking pipeline.

**Architecture:** A direct Python pipeline invokes focused modules for structure, external stability tools, geometry, OpenMM, validation, design, and reporting. Scientific dependencies are injected at their subprocess boundary so orchestration tests can use fakes while real runs either consume genuine outputs or fail explicitly.

**Tech Stack:** Python 3.12, Biopython, pandas, NumPy, matplotlib, Typer, optional OpenMM/PDBFixer, external ThermoMPNN and ThermoMPNN-D.

**Spec:** `docs/superpowers/specs/2026-08-19-atlas-v1-dynamic-geometry-design.md`

## Global Constraints

- Call the structure an `active-like reconstruction`, never active DP622-S2.
- ThermoMPNN predicts stability, not catalysis.
- Novel design cannot run or leave candidate artifacts after validation failure.
- Missing scientific dependencies or required atoms fail clearly; no synthetic scientific output is permitted.
- Preserve source papers, 23WN, the asset manifest, and published-label provenance.
- Rosetta, Docker, LangGraph, and Streamlit are not part of active v1 execution.

---

### Task 1: Focus the package and dependencies

**Files:** Modify `pyproject.toml`, `.gitignore`, `README.md`; move `references/structures/23WN.cif` to `data/23WN.cif`; remove obsolete active modules under `src/atlas/{adapters,challenge,domain,ui,workflow}` and their synthetic tests.

**Interfaces:** The console script remains `atlas = atlas.cli:app`; `atlas --help` exposes `run`, `reconstruct`, and `validate`.

- [x] Update dependency groups for Biopython, pandas, NumPy, matplotlib, and optional OpenMM/PDBFixer.
- [x] Preserve scientific assets and remove only obsolete executable scaffolding.
- [ ] Run `python -m pytest -q` and confirm failures refer only to not-yet-implemented new modules.

### Task 2: Reconstruct and mutate the complex with TDD

**Files:** Create `src/atlas/structure/{__init__,numbering,reconstruct,mutate}.py`; create `tests/structure/test_{numbering,reconstruct,mutate}.py`.

**Interfaces:** `dp622_to_deposited(int) -> int`; `deposited_to_dp622(int) -> int`; `reconstruct_active_like(Path, Path, Path) -> ReconstructionResult`; `apply_mutations(Path, tuple[Mutation, ...], Path) -> Path`; `build_known_mutants(Path, Path) -> pandas.DataFrame`.

- [x] Write literal numbering and committed-23WN reconstruction tests; run them and observe missing-module failures.
- [x] Implement extraction of A25-239, B34-41, zinc, Q120E, renumbering, mapping CSV, and invariant checks.
- [x] Write mutation tests for Y91F, D126A, H172A, and the double; observe failure.
- [x] Implement deterministic heavy-atom edits and known-mutant PDB/manifest output.
- [x] Run `python -m pytest tests/structure -q` and require all tests to pass.

### Task 3: Geometry selectors and metrics with TDD

**Files:** Create `src/atlas/geometry/{__init__,selectors,catalytic_metrics}.py`; create `tests/geometry/test_{selectors,catalytic_metrics}.py`.

**Interfaces:** `select_atom(structure, AtomSelector) -> Atom`; `measure_geometry(Path, Path | None = None) -> GeometryRecord`; `measure_many(dict[str, Path], Path, Path) -> pandas.DataFrame`.

- [x] Write tests with hand-calculated coordinates for distance, nearest oxygen, missing-atom warning, Kabsch RMSD, and committed-23WN scissile selector; observe failures.
- [x] Implement centralized selectors and finite/null metric serialization.
- [x] Run `python -m pytest tests/geometry -q` and require all tests to pass.

### Task 4: Real ThermoMPNN wrappers with TDD

**Files:** Create `src/atlas/stability/{__init__,common,thermompnn_runner,thermompnn_d_runner}.py`; create `tests/stability/test_runners.py`.

**Interfaces:** `ThermoMPNNRunner.run(Path, Sequence[Variant]) -> DataFrame`; `ThermoMPNNDRunner.run(Path, Sequence[Variant]) -> DataFrame`; both raise `DependencyUnavailableError` or `ScientificOutputError` on invalid execution.

- [x] Write subprocess-boundary tests for missing repository, nonzero exit, missing CSV columns, missing requested mutation, and normalized real-shaped output; observe failures.
- [x] Implement pinned-revision metadata, CLI commands, CSV schema validation, and stability-only interpretations.
- [x] Run `python -m pytest tests/stability -q` and require all tests to pass.

### Task 5: OpenMM attempt and honest fallback with TDD

**Files:** Create `src/atlas/dynamics/{__init__,models,openmm_minimize,openmm_short_md}.py`; create `tests/dynamics/test_openmm.py`.

**Interfaces:** `minimize_variant(Path, Path, DynamicsConfig) -> DynamicsResult`; `run_short_md(Path, Path, DynamicsConfig) -> DynamicsResult`; result status is `completed`, `skipped_dependency_unavailable`, or `skipped_unparameterized_system`.

- [x] Write tests proving dependency and parameterization failures produce empty snapshot records plus warnings; observe failures.
- [x] Implement lazy OpenMM imports, restrained setup, deterministic seeds, snapshot output, and exception-preserving fallback.
- [x] Run `python -m pytest tests/dynamics -q` and require all tests to pass.

### Task 6: Validation gate and design exclusion with TDD

**Files:** Create `src/atlas/validation/{__init__,known_mutants,validation_gate}.py`, `src/atlas/design/{__init__,candidate_generator,rank_candidates}.py`; create `tests/validation/test_gate.py`, `tests/design/test_candidates.py`.

**Interfaces:** `evaluate_validation(stability, geometry, dynamics) -> ValidationResult`; `require_validation_pass(result) -> None`; `generate_candidates(structure, validation) -> tuple[Candidate, ...]`; `rank_candidates(...) -> DataFrame`.

- [x] Write table-driven tests for full pass, each beneficial failure, harmful separation failure, and unavailable dynamics; observe failures.
- [x] Implement the fixed thresholds and Markdown/CSV validation report.
- [x] Write tests proving E96, zinc ligands, benchmark mutations, and pre-gate calls are excluded; observe failures.
- [x] Implement interpretable single candidates and no-score-no-ranking behavior. Conditional doubles remain intentionally deferred until real passing singles exist.
- [x] Run `python -m pytest tests/validation tests/design -q` and require all tests to pass.

### Task 7: Pipeline, reporting, CLI, and hard-stop integration

**Files:** Create `src/atlas/pipeline.py`, `src/atlas/reporting/{__init__,csv_outputs,plots}.py`; rewrite `src/atlas/cli.py`; create `tests/test_pipeline.py`, `tests/reporting/test_outputs.py`, `tests/test_cli.py`.

**Interfaces:** `run_pipeline(PipelineConfig, StabilityProvider | None = None, DynamicsProvider | None = None) -> PipelineResult`; CLI `atlas run --input data/23WN.cif --output-root outputs` exits 0 only on a completed validated run.

- [x] Write an integration test whose failed fake gate exits nonzero and leaves every novel-output path absent; observe failure.
- [x] Implement ordered phases, fresh run directories, warnings/provenance, schemas, and deterministic plots.
- [x] Write and pass successful-boundary tests using real structure/geometry plus external-tool fakes.
- [x] Run `python -m pytest tests/test_pipeline.py tests/reporting tests/test_cli.py -q`.

### Task 8: Colab and portfolio documentation

**Files:** Create `notebooks/Atlas_DP622_Colab.ipynb`; rewrite `README.md`, `docs/scientific_decisions.md`, `docs/limitations.md`, `docs/reproduction.md`.

**Interfaces:** Notebook pins both model repositories, installs Atlas/OpenMM, runs `atlas run`, displays CSVs/figures, and zips the selected run directory.

- [ ] Generate a valid notebook with separate setup, execution, inspection, and download cells.
- [ ] Document exact local structural-only and full Colab commands, all outputs, runtime ranges, fallback semantics, and claim boundaries.
- [ ] Execute notebook JSON validation and the CLI structural stages.
- [ ] Run the full local test suite and inspect generated figures and representative PDB/CSV artifacts.
