# Reproducibility

Atlas v1 uses Python 3.12, a committed `uv.lock`, deterministic cached adapters,
canonical JSON serialization, and a SHA-256 hash-chained append-only event ledger.
Run directories are numbered and never overwritten.

## Environment and tests

```bash
uv sync --frozen
uv run pytest
```

## Reproduce the cached challenge

```bash
uv run atlas challenge run --profile demo_cached
```

The new `runs/challenge-*` directory contains:

- `events.jsonl` — hash-chained scientific event ledger
- `decision-trace.json` — deterministic pre-reveal reasoning trace
- `scientific-notebook.md` — rendered scientific notebook
- `recommendation-lock.json` — immutable recommendation lock
- `final-report.json` and `final-report.md` — post-reveal report

Running the command twice creates a second directory rather than modifying the
first. Event payloads, rankings, lock contents, and reports are deterministic;
run identifiers and artifact paths distinguish invocations.

## Reproduce the benchmark

```bash
uv run atlas benchmark run --profile demo_cached
```

The single benchmark family includes iterative Atlas, a compute-matched
single-pass baseline, Scientific Critic ablation, sequence/structure evaluator
ablations, disagreement, a negative-result fixture, and seed retention.

## Run the UI

```bash
uv run streamlit run src/atlas/ui/app.py
```

Select **Load Atlas Challenge**, then **Start Campaign**. The UI and CLI invoke
the same deterministic workflow. No external network service, credential, or
uncommitted model asset is required for `demo_cached`.

## Source provenance

The locked requirements are in `docs/PRD.md`. The scientific reference is
`references/vita_abeta_metalloprotease.pdf`. The source set lacks exact DP622 and
optimized-control sequences and the paper’s supplementary design assets; Atlas
marks those inputs unavailable and does not infer them.
