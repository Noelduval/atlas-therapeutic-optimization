# Limitations

- The starting structure is the inactive DP622 E96Q deposited complex. Q120E is
  an unrelaxed coordinate edit and not an experimentally determined active state.
- Only Aβ residues 34–41 are resolved. Metrics cannot represent the flexibility
  or contacts of full-length Aβ42.
- Heavy-atom mutation construction removes side-chain atoms deterministically;
  it does not repack side chains. Static mutant geometry is therefore a screening
  baseline, not a relaxed structural prediction.
- ThermoMPNN predicts stability change, not proteolytic rate, specificity,
  expression, aggregation, toxicity, delivery, or clinical benefit.
- The published controls are a very small retrospective benchmark. Passing them
  does not demonstrate prospective generalization, and model training-data
  overlap cannot be ruled out.
- ThermoMPNN-D's pinned epistatic script uses CUDA. CPU-only environments cannot
  complete the required double-mutant score.
- The 23WN fragments lack chemically completed termini, and zinc/substrate
  parameterization is nontrivial. Standard OpenMM templates can reject this
  system (locally, the truncated terminal ALA lacked the expected terminal OXT).
  Atlas records that failure and uses static geometry; it does not call skipped
  dynamics evidence stable.
- Position and zinc restraints make comparisons more interpretable but can hide
  larger conformational changes. Ten-picosecond dynamics is not converged MD.
- The composite ranking is an explicit heuristic rather than a learned catalytic
  model. Lower scores mean higher computational priority only.
- Novel outputs require expression, blinded kinetic assays, cleavage-site and
  selectivity characterization, and independent experimental review.

Reasonable future work includes a validated metal-center force field, terminal
completion reviewed by a structural biologist, replicate longer MD, QM/MM,
prospective mutation controls, optional orthogonal Rosetta refinement, and wet-
lab testing.
