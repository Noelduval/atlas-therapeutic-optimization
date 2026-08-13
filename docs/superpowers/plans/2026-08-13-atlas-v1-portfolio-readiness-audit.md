# Atlas v1 Portfolio Readiness Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** Completed on 2026-08-13. The final release gates passed with 71 tests, a `scientifically_complete` challenge run, a `scientifically_complete` benchmark run, and a rendered desktop/mobile Streamlit audit.

**Goal:** Verify and minimally polish Atlas v1 as a reproducible, scientifically disciplined AI-for-science research-engineering portfolio project.

**Architecture:** Audit the existing locked VITA Aβ metalloprotease system without changing its LangGraph topology or scientific scope. Use an isolated clean checkout for reproducibility, source and rendered-UI inspections for claim quality, and the existing deterministic CLI workflows as release gates.

**Tech Stack:** Python 3.12, uv, pytest, LangGraph, Streamlit, YAML scientific-asset registries, Git.

## Global Constraints

- Do not add new scientific scope, HER2/trastuzumab implementation, PHGDH implementation, or secondary benchmarks.
- Do not infer missing sequences or fabricate measurements.
- Do not redesign the architecture or UI; permit only minimal portfolio-readiness copy or validation changes.
- Preserve the inactive DP622 E96Q versus active DP622-S2 distinction and the post-lock hidden-label firewall.

---

### Task 1: Clean-checkout reproducibility

**Files:**
- Inspect: `pyproject.toml`, `uv.lock`, `.gitignore`
- Verify: clean temporary checkout outside the working tree

**Interfaces:**
- Consumes: committed `main` tree and uv lockfile
- Produces: command-by-command setup, test, CLI, and Streamlit startup evidence

- [x] Verify `uv sync` from a clean checkout.
- [x] Verify `uv run pytest` from that checkout.
- [x] Verify both `demo_cached` CLI workflows and their artifact directories.
- [x] Start Streamlit headlessly and confirm its health endpoint before stopping it.

### Task 2: Scientific and portfolio narrative audit

**Files:**
- Modify if justified: `README.md`
- Modify if justified: `docs/atlas-challenge.md`
- Modify if justified: `docs/research-questions.md`
- Modify if justified: `docs/SCIENTIFIC_DECISIONS.md`
- Modify if justified: `docs/limitations.md`
- Modify if justified: `docs/reproducibility.md`

**Interfaces:**
- Consumes: locked PRD, recovered-asset manifest, sequence registry, hidden-label registry
- Produces: consistent motivation, provenance vocabulary, claim boundaries, and unavailable-asset disclosure

- [x] Review the README from an AI-for-science hiring-manager perspective.
- [x] Search risky clinical/efficacy language and classify every match.
- [x] Cross-check all five scientific documents against the locked scope.
- [x] Cross-check every unavailable scientific asset against data and documentation.
- [x] Apply only wording corrections supported by existing sources and tests.

### Task 3: Rendered Streamlit audit

**Files:**
- Inspect: `src/atlas/ui/app.py`, `src/atlas/ui/views.py`, `src/atlas/ui/styles.py`
- Modify if justified: UI copy in those files
- Test: `tests/ui/test_ui_contract.py`

**Interfaces:**
- Consumes: running local Streamlit app and deterministic `demo_cached` workflow
- Produces: desktop/mobile visual evidence plus first-run and completed-run interaction evidence

- [x] Verify page identity, meaningful first screen, console health, and absence of error overlays.
- [x] Exercise challenge start and verify the completed campaign state.
- [x] Inspect navigation to evidence, Decision Trace, Scientific Notebook, benchmark, and limitations views.
- [x] Verify desktop and mobile clarity and confirm no fake progress or out-of-scope executable systems.
- [x] If copy changes are needed, add or update a UI contract test before the minimal edit.

### Task 4: Repository hygiene and release gate

**Files:**
- Inspect: all tracked paths, Git object sizes, Markdown links, TODO markers, generated artifacts, and absolute paths
- Modify: only files implicated by concrete audit findings

**Interfaces:**
- Consumes: completed audit findings
- Produces: clean, pushed `main` commit and final readiness decision

- [x] Validate internal Markdown links and local-path hygiene.
- [x] Verify generated run artifacts are ignored and intended large references are documented.
- [x] Run the full pytest, challenge, and benchmark gates after all edits.
- [x] Mark this plan complete, stage the scoped diff, commit with `Polish Atlas v1 portfolio readiness`, and push.
