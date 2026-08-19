# Scientific decisions

## Claim boundary

Atlas is a computational prioritization workflow. Four evidence classes remain
separate in code and outputs:

1. **Published experimental data** label the retrospective controls.
2. **Computational reconstruction** describes the Q120E coordinate edit.
3. **Computational validation** describes performance on the known-control gate.
4. **Computationally predicted novel variants** exist only after that gate passes.

None of these imply experimental validation of a generated candidate.

## Structural reconstruction

PDB 23WN is retained byte-for-byte in `data/23WN.cif`. Author chain A residues
25–239 are extracted and mapped by `DP622 = deposited - 24`. The 215-residue
output is checked for contiguity. Deposited Q120 is GLN; its NE2 atom is renamed
OE2 and the residue becomes GLU A96. This preserves deposited coordinates and is
explicitly an isosteric model, not a relaxed or experimentally observed state.

The resolved Aβ chain B segment 34–41 and the single zinc ion are retained.
The deposited zinc connection identifies B38 O as the scissile carbonyl oxygen,
so Atlas uses B38 C/O without inventing a different cleavage assignment.

## Benchmark and stability models

The fixed controls are WT, Y91F, D126A, H172A, and Y91F/D126A. ThermoMPNN is
used for singles and ThermoMPNN-D epistatic mode for the double. WT ΔΔG is a
defined zero reference and is labeled as derived rather than inferred. The
adapters accept only expected official CSV schemas and requested mutation rows.

Predicted ΔΔG ≤ 1.0 kcal/mol is classified as non-regressive for this gate. That
threshold is a stability screen, not an activity threshold and was not fitted to
the four published values.

## Geometry and dynamics

Atom selectors are centralized in `atlas.geometry.selectors`. Required distances
are compared with WT using fixed tolerances: 0.40 Å for Zn–scissile O, 0.35 Å for
zinc ligand distances, and 0.50 Å for reconstructed E96 to the scissile carbonyl.
Aligned active-site RMSD must be ≤1.0 Å, substrate RMSD ≤1.0 Å, and substrate
centroid drift ≤0.75 Å. Loss of a required functional atom is a regression, not
an imputed favorable value.

OpenMM uses standard Amber templates, heavy-atom position restraints, and
explicit harmonic zinc-geometry restraints. Because 23WN contains coordinate
fragments of larger chains, hydrogens are added from OpenMM's built-in residue
definitions and Amber matching uses the documented `ignoreExternalBonds=True`
fragment mode. This does not add caps, heavy atoms, residues, or sequence. A
heavy-atom/residue-count integration test protects that boundary. A failed
system build still produces `skipped_unparameterized_system`, the original
exception, and zero snapshot rows. If real dynamic geometry exists it must also
pass; otherwise the gate transparently falls back to static geometry.

## Gate and design

Y91F and D126A must each have non-regressive stability and preserved geometry.
H172A and Y91F/D126A must each be separated by stability regression, geometry
regression, or required-atom loss. All four conditions must hold.

Post-gate design is intentionally small and interpretable: at most 24 nearest single alanine probes
within 8 Å of zinc or the resolved substrate. E96, zinc ligands, benchmark sites,
Gly/Pro, Cys, and existing Ala residues are excluded. Candidates lacking a real
stability score or complete geometry cannot be ranked. Small doubles are deferred
until real passing single-mutant evidence exists.

## Engineering choices

A direct pipeline is preferred over LangGraph because the sequence and failure
edge are fixed. External models remain pinned, separately licensed repositories
instead of vendored code. Fresh run directories prevent accidental overwrite.
Tests fake only the subprocess boundary; no production path substitutes scores.
