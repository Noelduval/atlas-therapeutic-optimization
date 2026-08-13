# Atlas v1

Atlas v1 is a focused, inspectable AI-for-science research-engineering artifact
for one scientific program.

Alzheimer’s disease remains a defining motivation for more precise and auditable
therapeutic research. Modern biological models can score sequences, structures,
interactions, and simulations, but coordinating their evidence—and surfacing when
they disagree—is itself a scientific problem.

## Atlas Challenge: Alzheimer’s Aβ Metalloprotease Optimization

Starting from the published DP622-S2 Aβ-cleaving metalloprotease, Atlas runs an
autonomous computational optimization campaign in the Aβ42/S2 system and locks
its recommendation before revealing retrospective VITA controls.

The system autonomously generates constrained hypotheses, evaluates them across
independent evidence dimensions, and sends only a locked recommendation forward
for experimental validation; it never substitutes computation for that validation.

Atlas v1 performs **computational candidate prioritization**, not experimental
validation. The `demo_cached` profile uses deterministic synthetic demo evidence
to exercise orchestration and reporting; it does not fabricate kinetic constants
or represent measured biological results.

Official-source recovery supplies the VITA Supplementary Information, RCSB 23WN
coordinates, and EMD-69322 metadata. The structure is the inactive DP622 E96Q
fusion construct; exact active DP622-S2 and optimized-control sequences remain
unavailable and are never inferred.

## What Atlas does

Atlas coordinates a typed, deterministic LangGraph campaign that:

1. loads only the challenge information permitted before recommendation lock;
2. proposes constrained, abstract candidate hypotheses;
3. evaluates seven independent evidence dimensions;
4. records disagreement instead of collapsing every score into false consensus;
5. applies Pareto ranking and a bounded Scientific Critic refinement;
6. persists a hash-chained event ledger, Decision Trace, Scientific Notebook,
   and recommendation lock; and
7. reveals published retrospective controls only after that lock exists.

The default demo reaches a valid negative result: it retains DP622-S2 because no
abstract candidate clears the scientific gates and promotion margin. Seed
retention is an intentional research outcome, not a failed software run.

## Evidence and provenance

| Class | Atlas v1 meaning | Present in `demo_cached` |
| --- | --- | --- |
| Official source asset | Publisher or repository material stored with URL, retrieval date, and checksum | VITA article and supplement, RCSB 23WN coordinates, EMDB EMD-69322 metadata |
| Published measured | Experimental values reported by VITA; inaccessible until the recommendation lock is persisted | Post-lock kinetics, cleavage, selectivity, and mutant outcomes |
| Cached / synthetic demo | Deterministic fixtures that exercise orchestration; not biological model output | All seven pre-lock candidate-evaluation dimensions |
| Predicted | Output from a production biological model or simulation adapter | None; no production model is invoked in v1 |
| Derived | Deterministic calculations over clearly identified inputs | Rankings, disagreement flags, Decision Trace, benchmark ablations, and post-lock retrospective comparison |
| Unavailable | Asset not present locally and never inferred | Exact active/optimized enzyme sequences, raw assays, optimized structures/design files, and map voxels |

Every candidate evidence record carries explicit provenance. Published measured
labels remain excluded from AtlasState, model adapters, candidate evidence,
ranking, the Decision Trace, and the Scientific Notebook before lock.

## Recovered and unavailable scientific assets

Recovered official assets are registered in
[`data/atlas_challenge/manifest.yaml`](data/atlas_challenge/manifest.yaml), with
sequence status in
[`data/atlas_challenge/sequences.yaml`](data/atlas_challenge/sequences.yaml).
PDB 23WN is the **inactive DP622 E96Q fusion construct**, not active DP622-S2.

The following remain explicitly `UNAVAILABLE` locally:

- exact active DP622-S2 sequence;
- exact OP609-S2 sequence;
- exact OP669-S2 sequence;
- raw assay-level measurements underlying published aggregate values;
- named optimized-variant coordinate/design files; and
- full EMD-69322 map voxels, which are publicly hosted but intentionally not
  downloaded because the current workflow does not consume them.

Atlas does not back-mutate E96Q, reconstruct optimized sequences from prose, or
invent missing measurements.

### Canonical configuration

| Field | Value |
| --- | --- |
| Starting candidate | DP622-S2 |
| Target context | Aβ42 |
| Cleavage system | S2 |
| Campaign type | Blinded retrospective benchmark |
| Optimization mode | Constrained scaffold optimization |
| Source | VITA, “De novo design of metalloproteases for targeted amyloid-β cleavage” |

## Quick start

Prerequisites: Python 3.12 and
[uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv sync
uv run atlas challenge run --profile demo_cached
uv run atlas benchmark run --profile demo_cached
uv run streamlit run src/atlas/ui/app.py
```

In the UI, select **Load Atlas Challenge**, then **Start Campaign**. The completed
run exposes the recommendation, candidates, recovered structural context,
evidence ledger, Decision Trace, Scientific Notebook, benchmark results, methods,
and limitations.

Challenge and benchmark runs write immutable, non-overwriting artifacts under
`runs/`. The challenge output includes a hash-chained event ledger, Decision
Trace, Scientific Notebook, pre-reveal recommendation lock, and final report.

## Verification

```bash
uv run pytest
```

## What Atlas does not claim

Atlas v1 does not claim to discover an Alzheimer’s cure, validate a therapeutic,
predict clinical success, or experimentally improve DP622-S2. Its retrospective
published controls cannot establish prospective generalization, and model
training-data contamination cannot be excluded.

This is a research-engineering project about scientific orchestration: typed
state, provenance, hidden-label isolation, disagreement, negative results,
immutable artifacts, reproducibility, and disciplined claim boundaries. Any
physical candidate would still require sequence recovery, expression, blinded
assays, selectivity testing, safety work, and independent experimental review.

The scientific contract, benchmark design, limitations, and exact reproduction
steps are documented in [`docs/atlas-challenge.md`](docs/atlas-challenge.md),
[`docs/research-questions.md`](docs/research-questions.md),
[`docs/SCIENTIFIC_DECISIONS.md`](docs/SCIENTIFIC_DECISIONS.md),
[`docs/limitations.md`](docs/limitations.md), and
[`docs/reproducibility.md`](docs/reproducibility.md).
