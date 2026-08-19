# Atlas v1 Dynamic Geometry-Gated Design

## Objective

Atlas v1 is a validation-gated computational pipeline for prioritizing DP622-S2
mutations. It reconstructs an active-like DP622-Aβ complex from the inactive
23WN E96Q cryo-EM structure, evaluates published mutation controls, and permits
novel computational candidates only when the combined stability and catalytic-
geometry gate succeeds.

Atlas produces computational predictions only. It does not claim an active
DP622-S2 structure, improved catalysis, therapeutic benefit, or experimental
validation.

## Active architecture

The active product is a Python 3.12 CLI and Colab notebook. A direct, explicit
pipeline is used instead of LangGraph because the phase order and stop condition
are fixed scientific invariants.

The pipeline has these modules:

- `structure`: extract 23WN chain A residues 25-239, renumber them 1-215,
  preserve chain B residues 34-41 and zinc, restore Q120E, and build variants.
- `stability`: run the official ThermoMPNN single-mutant and ThermoMPNN-D
  epistatic double-mutant command-line tools and normalize their real CSV output.
- `geometry`: centralize atom selectors and calculate static or snapshot metrics.
- `dynamics`: attempt restrained OpenMM minimization or short dynamics and return
  an explicit skipped result when the zinc complex cannot be parameterized.
- `validation`: join stability, geometry, and dynamics evidence for the known
  controls and enforce the hard pre-design gate.
- `design`: enumerate interpretable second-shell candidates only after a pass and
  exclude catalytic, zinc-coordinating, and benchmark mutations.
- `reporting`: write stable CSV schemas, Markdown warnings/reports, and figures.

The prior synthetic `demo_cached` campaign, abstract candidates, LangGraph
critic loop, and Streamlit UI are removed from the active package. Git history
preserves them; no user scientific data is deleted.

## Structural contract

The committed input is `data/23WN.cif`, copied byte-for-byte from the recovered
RCSB asset. The input checksum remains recorded in the asset manifest.

- Deposited chain A residues 25-239 map to DP622 residues 1-215.
- `dp622_number = deposited_number - 24`.
- Deposited Q120 is restored to DP622 E96 by the isosteric heavy-atom edit
  `GLN NE2 -> GLU OE2`; coordinates are not represented as experimentally
  observed E96 coordinates.
- Deposited chain B residues 34-41 are the resolved Aβ segment.
- Chain B GLY38 O is the scissile carbonyl oxygen because the deposited metal
  connection explicitly records its contact to zinc.
- Chain C zinc is retained.
- The reconstructed output must contain exactly 215 DP622 residues, GLU A96,
  the eight-residue substrate segment, and zinc or reconstruction fails.

DP622 and deposited numbering are both emitted for every mutation.

## Known validation controls

| Variant | DP622 numbering | Deposited numbering | Published trend |
| --- | --- | --- | --- |
| WT | reconstructed WT | Q120E restoration only | reference |
| Y91F | Y91F | Y115F | beneficial-looking |
| D126A | D126A | D150A | beneficial-looking |
| H172A | H172A | H196A | regressive |
| Y91F_D126A | Y91F/D126A | Y115F/D150A | strongly regressive |

Published trends are used only by the validation gate. ThermoMPNN values remain
labeled as predicted stability effects and are never described as catalytic
predictions.

## Geometry contract

Selectors live in one module and identify:

- zinc: chain C, residue 1601, atom ZN;
- scissile carbonyl: chain B, residue 38, atoms C and O;
- zinc ligands: DP622 H95 NE2, H99 NE2, and E122 OE1/OE2;
- restored catalytic residue: DP622 E96 OE1/OE2;
- oxyanion-hole metric: DP622 H172 NE2 to the scissile O;
- second-shell metric: DP622 Y91 OH/CZ to D126 OD1/OD2/CB;
- clamp metric: DP622 Y91 CZ to H172 NE2/CB.

Missing mutation-specific atoms yield null metrics plus warnings, never silently
imputed values. RMSDs use Kabsch alignment over common named atoms. The emitted
metrics include zinc-scissile distance, zinc coordination distances, E96 target
distance, active-site RMSD, substrate RMSD, H172 geometry, Y91/D126 geometry,
substrate pose drift, and clamp distance.

## Stability and dynamics boundaries

Atlas wraps pinned revisions of the official Kuhlman Lab repositories:

- ThermoMPNN `2b04fd370e399911b1fa5848112cc9013f084110`
- ThermoMPNN-D `df9a75aaddb674a7c4c193005031fc0536d325fb`

The wrappers validate executable paths, subprocess exit codes, output files,
required CSV columns, requested mutation rows, and numeric scores. Missing
dependencies raise an actionable `DependencyUnavailableError`. Scientific
execution never substitutes fixture values.

OpenMM uses standard force-field templates, positional restraints, and explicit
zinc-geometry restraints only when system creation succeeds. A setup failure
returns `skipped_unparameterized_system`, leaves snapshot tables empty, records
the original exception in `pipeline_warnings.md`, and preserves static geometry
as the only geometry evidence.

## Validation gate

The gate is deliberately interpretable rather than fitted to four controls.
Each variant receives:

- a stability classification from predicted ΔΔG (`non_regressive` at <= 1.0
  kcal/mol, otherwise `regressive`);
- a geometry classification based on WT-relative hard tolerances for zinc,
  catalytic target, active-site RMSD, substrate RMSD, and required-atom loss;
- a dynamics classification when real snapshots exist, otherwise `unavailable`.

A known beneficial-looking variant passes if stability is non-regressive and
geometry is preserved. A known harmful-looking variant is correctly separated
if stability is regressive, geometry regresses, or a required functional atom is
lost. The full validation passes only when Y91F and D126A pass and H172A and
Y91F/D126A are separated as regressive. Failure exits nonzero and no novel
manifest, ranking, top-five directory, or candidate figure may exist.

## Candidate generation and ranking

Candidate positions are protein residues within 8 Å of the resolved substrate
or zinc and outside E96, H95, H99, E122, the benchmark positions, and glycine/
proline backbone-sensitive exclusions. Candidate substitutions are a small,
documented conservative alphabet. Singles are evaluated first; doubles are only
formed from passing singles within 8 Å of each other.

Ranking combines real stability predictions, geometry preservation, dynamics
dispersion when available, and explicit warning penalties. A missing required
scientific score prevents ranking rather than receiving a favorable default.

## Reproducibility and outputs

The local package installs with `python -m pip install -e '.[dev,dynamics]'`.
ThermoMPNN is intentionally external; the full reviewer path is the committed
Colab notebook, which clones pinned revisions, installs dependencies, runs the
pipeline, displays tables and figures, and creates a ZIP archive.

Every run writes to a fresh directory beneath `outputs/`. Required reconstruction,
manifest, geometry, validation, warnings, and provenance artifacts are written
even when the scientific gate stops later phases. Empty or unavailable stages
use schema-valid files and explicit status fields, not fabricated numbers.

## Verification

Unit tests cover numbering, reconstruction invariants, mutations, atom selectors,
hand-calculated distances/RMSDs, gate branches, candidate exclusions, schemas,
and dependency failure. Integration tests use subprocess fakes only at the
external-tool boundary and assert that a failed validation cannot call design.
The committed 23WN asset is exercised by a real reconstruction integration test.
