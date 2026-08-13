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
single-pass baseline, Scientific Critic ablation, contribution ablations for all
seven evaluator dimensions, disagreement, a negative-result fixture, and seed
retention.

## Run the UI

```bash
uv run streamlit run src/atlas/ui/app.py
```

Select **Load Atlas Challenge**, then **Start Campaign**. The UI and CLI invoke
the same deterministic workflow. No external network service, credential, or
uncommitted model asset is required for `demo_cached`.

## Source provenance

The locked requirements are in `docs/PRD.md`. The scientific reference is
`references/vita_abeta_metalloprotease.pdf`. Recovered scientific assets are:

- `references/vita_abeta_metalloprotease_supplementary.pdf`, downloaded from the
  VITA publisher's supplementary-information link;
- `references/structures/23WN.cif`, downloaded from RCSB;
- `references/structures/EMD-69322_metadata.json`, downloaded from the EMDB API;
- `data/atlas_challenge/manifest.yaml`, the retrieval/checksum/provenance record;
- `data/atlas_challenge/sequences.yaml`, the exact deposition sequences and
  explicit unavailable records; and
- `data/atlas_challenge/hidden_labels.yaml`, loaded only after lock verification.

Verify local asset integrity with:

```bash
shasum -a 256 \
  references/vita_abeta_metalloprotease.pdf \
  references/vita_abeta_metalloprotease_supplementary.pdf \
  references/structures/23WN.cif \
  references/structures/EMD-69322_metadata.json
```

Compare the output with `data/atlas_challenge/manifest.yaml`. The recovered 23WN
sequence is the inactive E96Q fusion construct. Exact active DP622-S2, OP609-S2,
and OP669-S2 sequences remain unavailable after the official-source search and
must not be inferred. The EMDB map itself was not downloaded because no current
`demo_cached` path consumes map voxels.

The manifest also records raw assay-level measurements, named optimized-variant
coordinate/design files, and local full-map voxels as `UNAVAILABLE`. The EMDB
map remains publicly hosted; `UNAVAILABLE` here describes the local Atlas asset
state, not public repository availability.
