# 1. Modified Sections

## Final Scope Decision

Atlas v1 has exactly one flagship challenge:

# Atlas Challenge: Alzheimer’s Aβ Metalloprotease Optimization

```text
Seed:
DP622-S2

Target context:
Aβ42

Cleavage system:
S2

Scientific source:
“De novo design of metalloproteases for targeted amyloid-β cleavage.”
```

PHGDH placement:

**Future mechanism/modality case study only.**

Atlas v1 is not a general therapeutic-platform demonstration.

Atlas v1 is a focused research artifact built around one scientific test:

> **Starting from a published Alzheimer’s-relevant Aβ-cleaving metalloprotease, Atlas runs an autonomous, inspectable computational optimization campaign and tests whether its reasoning-and-computation loop can prioritize stronger candidates for experimental validation.**

This identity is locked for v1.

---

## Amendment to Section 54 — Benchmarking Philosophy

Atlas v1 contains exactly one flagship benchmark:

# Atlas Challenge: Alzheimer’s Aβ Metalloprotease Optimization

The Challenge evaluates whether autonomous scientific orchestration improves retrospective candidate prioritization when beginning from the published DP622-S2 metalloprotease in the Aβ42/S2 system.

The benchmark must preserve:

- constrained candidate generation;
- structural prediction;
- catalytic-geometry evaluation;
- substrate-recognition evaluation;
- selectivity-risk evaluation;
- developability evaluation;
- molecular-simulation sanity checks;
- model disagreement;
- Scientific Critic review;
- iterative refinement;
- blinded retrospective comparison.

Compute-matched baselines, Scientific Critic ablations, and biological-model contribution ablations remain supporting experiments **inside this single benchmark program**.

They do not constitute separate benchmark families or additional therapeutic-system implementations.

Atlas v1 must not broaden beyond the VITA-derived DP622-S2 / Aβ42 / S2 system before this Challenge is complete, tested, reproducible, documented, and benchmarked.

---

## Amendment to Section 55 — Atlas Challenge

# Atlas Challenge: Alzheimer’s Aβ Metalloprotease Optimization

Canonical configuration:

```yaml
challenge:
  seed: DP622-S2
  target_context: Aβ42
  cleavage_system: S2
  campaign_type: blinded_retrospective
  optimization_mode: constrained_scaffold_optimization
```

The VITA paper supplies:

- the starting candidate;
- target substrate context;
- cleavage objective;
- experimentally characterized mutants;
- structure-guided optimized variants;
- structural context;
- hidden retrospective kinetic, selectivity, cleavage, and structural outcomes.

Atlas does not reproduce the VITA paper.

Atlas begins from the published scientific system and executes its own autonomous optimization campaign.

All previously established VITA Challenge requirements remain intact, including:

- OP609-S2 and OP669-S2 as hidden retrospective controls where reproducible;
- experimentally characterized DP622 mutants as hidden controls where reproducible;
- catalytic-geometry evaluator;
- active DP622-S2 versus inactive DP622 E96Q structural-reference distinction;
- PDB `23WN` / EMDB `EMD-69322` provenance handling;
- no synthetic `kcat`, `Km`, or `kcat/Km`;
- selectivity risk as independent evidence;
- hidden-label firewall;
- recommendation locking;
- blinded candidate anonymization;
- retrospective contamination disclosure;
- negative-result support;
- seed retention as valid scientific success.

These requirements must not be weakened during implementation.

---

## Amendment to Section 56 — Benchmark Integrity

Before recommendation lock, hidden VITA outcomes must remain unavailable to:

- `AtlasState`;
- agent prompts;
- candidate evidence;
- Decision Trace;
- Scientific Notebook;
- model adapters;
- optimization policies;
- candidate ranking.

The hidden-label firewall includes:

```text
published kinetic outcomes
published cleavage outcomes
published selectivity outcomes
published optimized-variant performance
experimental retrospective rankings
post-seed optimization conclusions
```

Published reference candidates must remain anonymized during blinded ranking whenever their identities could expose outcome information.

The recommendation artifact and Decision Trace must be locked before retrospective outcomes are revealed.

Atlas Challenge remains explicitly retrospective.

Possible biological foundation-model training-data contamination must remain disclosed.

---

## Amendment to Section 45 — Streamlit Scope

Primary navigation remains:

```text
Atlas Challenge
Run Monitor
Candidates
Structures
Evidence
Scientific Notebook
Benchmarks
Methods
```

There is no challenge selector in Atlas v1.

There are no multiple challenge cards.

There are no alternative therapeutic-system options.

The `Benchmarks` page displays results, baselines, ablations, failures, and retrospective evaluation associated with the single Aβ metalloprotease Challenge.

---

## Revised Section 46 — Streamlit First-Run Experience

The first-run screen presents only:

# Atlas Challenge

## Alzheimer’s Aβ Metalloprotease Optimization

Description:

> Start from the published DP622-S2 Aβ-cleaving metalloprotease and run a blinded autonomous computational optimization campaign against Aβ42.

Display:

```text
Starting candidate:   DP622-S2
Target context:       Aβ42
Cleavage system:      S2
Campaign type:        Blinded retrospective benchmark
Experimental labels: Hidden
Optimization mode:    Constrained scaffold optimization
```

Primary action:

**Load Atlas Challenge**

Then:

**Start Campaign**

Do not present:

- a challenge selector;
- multiple challenge cards;
- antibody benchmark options;
- additional disease-specific campaigns;
- additional modality-specific campaigns.

The first-run experience must communicate one coherent scientific program.

---

## Revised Section 70 — README Requirement

The README must make Atlas v1's focus unmistakable.

Required scientific positioning:

> **Atlas was motivated by Alzheimer’s disease. Its flagship challenge begins from a published Alzheimer’s-relevant Aβ-cleaving metalloprotease because the VITA system provides the kind of real therapeutic-protein candidate, structural context, experimental measurements, selectivity tradeoffs, and optimization trajectory needed for a serious autonomous computational optimization benchmark.**

The README opening must focus on:

1. Alzheimer’s as the project motivation.
2. The coordination problem between modern biological models.
3. DP622-S2 / Aβ42 / S2 as the v1 scientific testbed.
4. Autonomous computational hypothesis generation and evaluation.
5. Experimental validation as the required downstream step.

The README must not imply that Atlas:

- discovers an Alzheimer’s cure;
- validates an Alzheimer’s therapeutic;
- proves Aβ cleavage modifies disease;
- predicts human efficacy;
- reproduces the VITA paper;
- experimentally improves DP622-S2;
- replaces experimental validation;
- is a general drug-discovery platform in v1.

Preferred terminology:

- computational hypothesis;
- computational candidate;
- retrospective candidate prioritization;
- evidence-supported recommendation;
- recommended for experimental validation;
- uncertainty;
- model disagreement;
- negative result.

No rejected alternative benchmark belongs in the main README narrative.

---

## Revised `docs/atlas-challenge.md`

This document describes only:

# Atlas Challenge: Alzheimer’s Aβ Metalloprotease Optimization

Required contents:

- DP622-S2 starting candidate;
- Aβ42 target context;
- S2 cleavage system;
- VITA source provenance;
- structural-reference provenance;
- catalytic-site constraints;
- optimization objectives;
- visible-information manifest;
- hidden-information manifest;
- autonomous search methodology;
- blinded reference-ranking methodology;
- recommendation locking;
- retrospective reveal;
- compute-matched baselines;
- ablations;
- contamination disclosure;
- negative-result interpretation;
- reproducibility commands.

No secondary therapeutic benchmark is documented in this file.

---

## Revised `docs/research-questions.md`

Every executable Atlas v1 research question must be answerable using the Aβ metalloprotease Challenge.

### RQ1 — Can autonomous optimization outperform a single-pass workflow?

### RQ2 — Does iterative refinement improve retrospective candidate prioritization?

### RQ3 — How valuable is adversarial scientific critique?

### RQ4 — How much does each biological foundation model contribute?

### RQ5 — How frequently do the models disagree?

### RQ6 — Is catalytic-geometry preservation necessary but insufficient?

### RQ7 — Can Atlas identify non-additive mutational behavior?

### RQ8 — Can Atlas distinguish stronger substrate interaction from useful substrate selectivity?

### RQ9 — Does molecular-simulation sanity checking materially alter candidate prioritization?

### RQ10 — When should Atlas retain DP622-S2 rather than promote a generated candidate?

These questions define the Atlas v1 research program.

They do not create requirements for additional therapeutic systems.

---

## PHGDH Mechanism Case Study — Future Research

PHGDH remains documentation-only future research.

# PHGDH Mechanism Case Study — Future Research

### Purpose

PHGDH demonstrates an Alzheimer’s mechanism and small-molecule/transcriptional-regulation therapeutic strategy.

It is scientifically relevant to Atlas's disease motivation, but it is not a v1 optimization benchmark because Atlas v1 is scoped around therapeutic protein candidate optimization.

The PHGDH case introduces scientific abstractions outside v1:

- transcriptional regulatory networks;
- small-molecule optimization;
- blood-brain-barrier pharmacology;
- organoid phenotype prediction;
- mouse behavioral outcome reasoning;
- causal disease-mechanism evaluation;
- therapeutic modality selection.

No PHGDH-specific adapter, evaluator, model, dataset, campaign, UI path, or test requirement belongs in Atlas v1.

The case strengthens the Alzheimer’s motivation without expanding the software scope.

---

## Replacement for SD-011 in `docs/SCIENTIFIC_DECISIONS.md`

# SD-011 — Why Atlas v1 Uses the VITA Aβ Metalloprotease System Rather Than Antibody Benchmarks

### Decision

Use the DP622-S2 / Aβ42 / S2 VITA system as Atlas's v1 flagship benchmark.

### Context

Atlas v1 is designed to demonstrate autonomous therapeutic protein optimization using constrained candidate generation, structural prediction, deterministic evidence evaluation, molecular simulation sanity checks, model disagreement handling, Scientific Critic review, and blinded retrospective comparison.

The VITA Aβ metalloprotease system directly exercises this architecture because it involves:

- an Alzheimer’s-relevant substrate;
- a real published protein-engineering candidate;
- enzyme–substrate structural context;
- catalytic geometry;
- zinc metalloprotease constraints;
- protein–peptide recognition;
- substrate selectivity;
- experimentally characterized mutants;
- structure-guided optimized variants;
- hidden retrospective kinetic, selectivity, and structural outcomes.

### Alternative Rejected

HER2/trastuzumab and other antibody-specific therapeutic benchmark systems.

### Why Rejected

The rejected alternative is scientifically valid, but it is not the correct v1 flagship.

It would shift Atlas v1 away from:

- the Alzheimer’s-centered motivation;
- the Aβ metalloprotease scientific system;
- catalytic-geometry reasoning;
- enzyme–substrate optimization;
- selectivity-risk reasoning;
- metal-site structural constraints;
- the specific VITA retrospective optimization trajectory.

Antibody-specific benchmarks may be scientifically useful later, but including them in v1 would dilute the first build.

### Future Revisit Trigger

Only after Atlas v1 is complete, tested, documented, and benchmarked on the Alzheimer’s Aβ Metalloprotease Challenge may a separate future benchmark suite evaluate additional therapeutic-protein modalities.

No Atlas v1 implementation requirement follows from that future possibility.

This is the only location in the v1 PRD/documentation set where the rejected flagship alternative may be named.

---

## Revised Section 74 — Demo Scenario A

# Demo Scenario A — Atlas Challenge: Alzheimer’s Aβ Metalloprotease Optimization

The primary and only flagship v1 demonstration begins:

```text
Load Atlas Challenge
↓
DP622-S2 / Aβ42 / S2 context loaded
↓
Start Campaign
```

The reviewer watches:

```text
seed characterization
↓
catalytic-geometry baseline
↓
optimization hypothesis
↓
candidate generation
↓
rejection gates
↓
structure prediction
↓
substrate-recognition evaluation
↓
selectivity-risk evaluation
↓
developability evaluation
↓
simulation sanity checking
↓
model disagreement
↓
Scientific Critic
↓
iteration
↓
termination
↓
recommendation lock
↓
hidden retrospective reveal
↓
benchmark evaluation
```

There are no other disease- or modality-specific v1 demo campaigns.

---

## Revised Section 75 — Demo Scenario B

# Demo Scenario B — Scientific Disagreement Within the Atlas Challenge

Use a deterministic Aβ metalloprotease fixture where evidence conflicts.

Examples:

```text
strong substrate-recognition evidence
+
degraded catalytic geometry
```

or:

```text
strong structural confidence
+
higher selectivity risk
```

The Scientific Critic must expose the conflict and its effect on candidate prioritization.

This is a fixture of the flagship Challenge, not a separate benchmark.

---

## Revised Section 76 — Demo Scenario C

# Demo Scenario C — Seed Retention

Use a deterministic Challenge fixture in which all generated variants fail to provide sufficiently stronger evidence than DP622-S2.

Expected conclusion:

```text
Winning Candidate:
Original VITA Seed — DP622-S2
```

The campaign terminates as:

`scientifically_complete`

not:

`optimization_failed`.

Atlas must demonstrate that autonomous optimization does not imply a requirement to produce novelty.

---

## Amendment to Section 79 — Scientific Limitations

Retain all existing Alzheimer’s metalloprotease limitations.

Add:

> **Atlas v1's scientific conclusions are limited to computational candidate prioritization within the DP622-S2 / Aβ42 / S2 Challenge and its supporting retrospective evaluations.**

Atlas v1 does not demonstrate:

- general therapeutic-modality selection;
- antibody optimization;
- small-molecule optimization;
- causal Alzheimer’s disease modeling;
- clinical outcome prediction.

The Alzheimer’s motivation must increase scientific specificity, not reduce scientific caution.

---

## Amendment to Section 80 — Research Program Positioning

Atlas v1 is intentionally narrow.

Its purpose is to determine whether the Atlas orchestration architecture adds measurable scientific value in one sufficiently rich therapeutic-protein engineering system.

The v1 progression is:

```text
DP622-S2 / Aβ42 / S2 Challenge
↓
execute autonomous optimization
↓
measure successes and failures
↓
compare against simpler workflows
↓
validate provenance and reproducibility
↓
evaluate blinded retrospective alignment
↓
only then consider future therapeutic-protein modalities
```

Architectural modularity exists to permit future model and domain extension.

It does not create a v1 obligation to demonstrate multiple therapeutic systems.

---

## Revised Section 84 — Definition of Done

Atlas v1 is not complete unless:

### Scope

- [ ] Exactly one flagship Challenge exists.
- [ ] The flagship is `Atlas Challenge: Alzheimer’s Aβ Metalloprotease Optimization`.
- [ ] DP622-S2 is the canonical seed.
- [ ] Aβ42 is the canonical target context.
- [ ] S2 is the canonical cleavage system.
- [ ] VITA is the Challenge source system.
- [ ] No active secondary therapeutic benchmark implementation exists.
- [ ] No antibody-specific adapter requirement exists.
- [ ] No antibody-specific dataset requirement exists.
- [ ] No antibody-specific demo exists.
- [ ] No antibody-specific test requirement exists.

### Benchmark

- [ ] VITA hidden-label firewall is implemented.
- [ ] Recommendation locking occurs before retrospective reveal.
- [ ] Catalytic geometry is evaluated without fabricating catalytic activity.
- [ ] Selectivity risk is distinct from substrate interaction.
- [ ] OP609-S2 and OP669-S2 controls are supported where reproducible.
- [ ] Experimentally characterized DP622 mutant controls are supported where reproducible.
- [ ] Compute-matched baselines run.
- [ ] Scientific Critic ablations run.
- [ ] Biological-model contribution ablations run.
- [ ] Negative-result fixture runs.
- [ ] Seed retention is supported as scientific success.

### Scope Consistency

- [ ] README describes one flagship Challenge.
- [ ] Streamlit first-run experience exposes one Challenge.
- [ ] Demo scenarios are fixtures or views of the same Challenge.
- [ ] Benchmark commands execute the VITA-centered benchmark.
- [ ] Active dataset manifests contain no additional therapeutic system.
- [ ] Tests contain no additional therapeutic-modality implementation requirements.
- [ ] PHGDH is documentation-only future research.
- [ ] All documentation reflects the same v1 scientific identity.

---

## Revised Section 86 — Codex Engineering Rules

Replace any active-v1 references to secondary therapeutic benchmarks with:

36. Atlas v1 implements exactly one flagship Challenge.

37. Do not implement a secondary therapeutic-protein benchmark in v1.

38. Do not add antibody-specific adapters, datasets, evaluators, UI, demos, fixtures, or campaign configurations.

39. Do not broaden the Challenge selector because no Challenge selector is needed in v1.

40. Do not expand PHGDH into implementation scope.

41. Complete the DP622-S2 / Aβ42 / S2 scientific workflow before considering future modalities.

42. Treat broader therapeutic-protein modality support exclusively as an adapter/interface extensibility concern, not a v1 deliverable.

43. Preserve all existing VITA benchmark-integrity requirements.

44. Preserve all existing scientific limitations and claim discipline.

45. Do not equate architectural modularity with an obligation to implement multiple biological systems.

---

# 2. Concise Summary of Changes

This correction locks Atlas v1 to a single scientific program:

**DP622-S2 → Aβ42 → S2 → autonomous computational optimization → blinded retrospective VITA evaluation.**

All secondary therapeutic-system implementation work is removed from active v1 scope.

The Streamlit first-run experience, README, benchmark requirements, demo scenarios, tests, Definition of Done, Codex rules, dataset expectations, and documentation now point to the same Challenge.

PHGDH remains future mechanism/modality research only.

All strong requirements from the Alzheimer’s amendment remain intact, including catalytic-geometry evaluation, structural-reference provenance, hidden-label isolation, recommendation locking, selectivity-risk evaluation, retrospective controls, compute-matched baselines, ablations, negative outcomes, and seed retention.

---

# 3. Scope-Purity Checklist

- [x] Atlas v1 has exactly one flagship Challenge.
- [x] The flagship is **Alzheimer’s Aβ Metalloprotease Optimization**.
- [x] DP622-S2 is the canonical seed.
- [x] Aβ42 is the canonical target context.
- [x] S2 is the canonical cleavage system.
- [x] VITA is the single active Challenge source system.
- [x] No active secondary therapeutic benchmark remains.
- [x] No antibody-specific adapter requirement remains.
- [x] No antibody-specific dataset requirement remains.
- [x] No antibody-specific evaluator requirement remains.
- [x] No antibody-specific UI requirement remains.
- [x] No antibody-specific demo requirement remains.
- [x] No antibody-specific test requirement remains.
- [x] No additional therapeutic system appears in active dataset manifests.
- [x] No multiple-challenge selector exists in Streamlit v1.
- [x] README communicates one Alzheimer’s-centered scientific narrative.
- [x] Demo Scenarios B and C remain fixtures of the flagship Challenge rather than separate benchmarks.
- [x] PHGDH remains future mechanism/modality research only.
- [x] Hidden-label firewall remains intact.
- [x] Recommendation lock remains intact.
- [x] Catalytic geometry remains distinct from catalytic activity.
- [x] No synthetic `kcat`, `Km`, or `kcat/Km` is introduced.
- [x] Selectivity risk remains distinct from substrate interaction.
- [x] Compute-matched baselines remain intact.
- [x] Scientific Critic ablations remain intact.
- [x] Biological-model contribution ablations remain intact.
- [x] Negative results remain first-class scientific outcomes.
- [x] Retaining DP622-S2 remains a valid successful conclusion.
- [x] No cure, clinical-success, or experimental-validation claim has been introduced.
- [x] The rejected antibody flagship appears only in `docs/SCIENTIFIC_DECISIONS.md`, SD-011.
- [x] HER2/trastuzumab is removed from all active v1 implementation scope.
- [x] **Final identity is locked: Atlas v1 = VITA Aβ metalloprotease challenge.**
