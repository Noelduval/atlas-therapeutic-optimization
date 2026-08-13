# Atlas v1

Atlas v1 is a focused, inspectable research artifact for one scientific program:

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

Challenge and benchmark runs write immutable, non-overwriting artifacts under
`runs/`. The challenge output includes a hash-chained event ledger, Decision
Trace, Scientific Notebook, pre-reveal recommendation lock, and final report.

## Verification

```bash
uv run pytest
```

The scientific contract, benchmark design, limitations, and exact reproduction
steps are documented in [`docs/atlas-challenge.md`](docs/atlas-challenge.md),
[`docs/limitations.md`](docs/limitations.md), and
[`docs/reproducibility.md`](docs/reproducibility.md).
