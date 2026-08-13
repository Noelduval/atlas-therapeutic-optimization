# Atlas Challenge

## Alzheimer’s Aβ Metalloprotease Optimization

Atlas v1 contains exactly one flagship challenge. It begins with the published
DP622-S2 metalloprotease, uses Aβ42 as the target context and S2 as the cleavage
system, and performs constrained scaffold optimization followed by blinded
retrospective evaluation.

The primary scientific source is the VITA paper, “De novo design of
metalloproteases for targeted amyloid-β cleavage,” committed at
`references/vita_abeta_metalloprotease.pdf`. The publisher Supplementary
Information, RCSB 23WN coordinates, and EMDB EMD-69322 metadata were recovered
from their official public repositories on 2026-08-13.

## Recovered asset manifest

| Asset | Local file | Official source | Scientific use |
| --- | --- | --- | --- |
| VITA Supplementary Information | `references/vita_abeta_metalloprotease_supplementary.pdf` | VITA publisher article page | Assay constructs, supplementary figures, and cryo-EM validation metadata |
| PDB 23WN | `references/structures/23WN.cif` | RCSB PDB | Inactive DP622 E96Q/Aβ42 structural reference only |
| EMD-69322 metadata | `references/structures/EMD-69322_metadata.json` | EMDB API | Deposition, specimen, reconstruction, and map provenance; no map voxels |
| Sequence registry | `data/atlas_challenge/sequences.yaml` | RCSB/EMDB deposition plus exhausted official-source search | Exact deposited E96Q construct and Aβ42 sequence; explicit unavailability of active/optimized enzymes |
| Hidden labels | `data/atlas_challenge/hidden_labels.yaml` | VITA article Figures 3 and 5 and Supplementary Figures S5, S10, S20, and S21 | Post-lock kinetics, cleavage, selectivity, and mutant outcomes only |

Checksums, retrieval dates, direct URLs, the authors' repository revision, and
provenance notes are recorded in `data/atlas_challenge/manifest.yaml`. The
primary EMDB map was intentionally not downloaded because the current
implementation uses metadata and the RCSB atomic coordinates, not map voxels.

## Unavailable asset manifest

The following have explicit `UNAVAILABLE` records and are not inferred:

- exact active DP622-S2, OP609-S2, and OP669-S2 enzyme sequences in
  `data/atlas_challenge/sequences.yaml`;
- raw assay-level measurements;
- named optimized-variant coordinate/design files; and
- local EMD-69322 map voxels. The map is publicly hosted but intentionally not
  downloaded because no Atlas v1 execution path consumes it.

The latter three local availability records are in
`data/atlas_challenge/manifest.yaml`.

## Scientific contract

- Aβ42 sequence: `DAEFRHDSGYEVHHQKLVFFAEDVGSNKGAIIGLMVGGVVIA`
- S2 context: `GLMVGG|VVIA`
- DP622-S2 catalytic residues: Y91, E96, D126, H172
- PDB `23WN` / EMDB `EMD-69322` is an inactive DP622 E96Q pre-catalytic
  reference. Its distances establish a geometry baseline, not catalytic activity.
- The deposited entity-1 sequence is a 1,513-residue E96Q fusion construct;
  chain A residues 15–239 are modeled. It is not the active DP622-S2 seed.
- Substrate recognition and selectivity risk are independent evidence dimensions.
- No synthetic `kcat`, `Km`, or `kcat/Km` values are permitted.
- A recommendation and its Decision Trace are locked before hidden outcomes are
  revealed.
- Retaining DP622-S2 is a valid `scientifically_complete` result when no proposed
  candidate clears both the scientific gates and promotion margin.

## Campaign stages

The LangGraph campaign validates configuration and safety, loads visible
challenge facts, characterizes the seed, establishes a baseline, proposes
constrained variants, evaluates seven evidence dimensions, records disagreement,
ranks the Pareto set, runs the Scientific Critic, terminates, locks the
recommendation, reveals retrospective controls, and renders a final report.

Pre-lock state, prompts, evidence, ranking, Decision Trace, and Scientific
Notebook cannot access hidden retrospective outcomes. Reference controls are
anonymous until the recommendation lock exists.

## Evidence provenance

`demo_cached` is the only v1 runtime profile. It provides deterministic synthetic
demo evidence for sequence, structure, catalytic geometry, substrate recognition,
selectivity risk, developability, and simulation sanity checking. Every such
record is labeled `synthetic_demo`; none is presented as biological model output
or measured evidence.

After lock, Atlas can reveal paper-derived retrospective controls and report
alignment. Exact active DP622-S2, OP609-S2, and OP669-S2 enzyme sequences were
not found in the article, Supplementary Information, 23WN/EMD-69322 deposits, or
the authors' named repository. Atlas records that official-source search as a
negative result rather than inferring or reconstructing sequences.

## Visible-information manifest

Before lock, campaign state contains the canonical configuration, Aβ42 sequence,
S2 context, catalytic-residue identities, the inactive E96Q structure identifiers,
geometry-only interpretation, asset availability flags, and anonymous control
identifiers. It contains no published post-seed performance or ranking.

## Hidden-information manifest

Published seed/control `kcat`, `Km`, catalytic efficiencies, cleavage outcomes,
selectivity outcomes, optimized-variant identities and performance, mutant outcomes,
retrospective rankings, and post-seed optimization conclusions are post-lock only.
The hidden repository verifies a durable lock file and the canonical pre-lock
hash-chained ledger before reading `hidden_labels.yaml`. They remain absent from
AtlasState, candidate evidence, adapters, ranking, Decision Trace, and the
Scientific Notebook.

## What must not be inferred

- Do not back-mutate the deposited E96Q fusion construct and call the result the
  active DP622-S2 sequence.
- Do not reconstruct OP609-S2 or OP669-S2 from figures, prose, design examples,
  or sequence differences that are not explicitly deposited.
- Do not interpret the resolved Aβ42 residues 34–41 as a fully observed Aβ42
  structure; the deposition contains the full 42-residue entity sequence but
  models only that eight-residue segment.
- Do not infer unreported kinetics, raw assay measurements, selectivity against
  untested substrates, or catalytic activity from structural geometry.

## Autonomous search methodology

The cached v1 campaign proposes three constrained anonymous hypotheses, evaluates
them, detects cross-evaluator disagreement, and lets the Scientific Critic request
one bounded refinement. That refined hypothesis is reevaluated before Pareto
ranking, a second critic pass, termination, and lock. Exact sequences remain
unavailable, so hypotheses are abstract scientific fixtures rather than claimed
physical constructs.

## Blinded reference ranking

Pre-lock ranking uses only anonymous candidate IDs and the seven independent demo
dimensions. The Decision Trace includes the locked candidate decision. After the
lock is persisted, Atlas reveals reference identities and explicitly computes
whether the recommendation recovered a published optimized control.

## Supporting experiments

The single benchmark program includes a compute-matched single-pass calculation,
a Scientific Critic ablation, contribution ablations for all seven evaluators,
disagreement analysis, a negative-result fixture, and seed retention. These are
views of one challenge, not additional benchmark families.

## Retrospective contamination disclosure

The source is published and may occur in biological model training corpora. Atlas
therefore describes post-lock comparison as retrospective alignment, never as
prospective validation or independent discovery.

## Reproduce

```bash
uv sync --frozen
uv run atlas challenge run --profile demo_cached
uv run atlas benchmark run --profile demo_cached
uv run pytest
```

See `docs/reproducibility.md` for artifact-level checks.
