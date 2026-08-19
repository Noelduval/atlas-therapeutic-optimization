# Atlas Colab T4 Execution-Readiness Design

## Objective

Prepare `codex/atlas-v1-dynamic-geometry` for the first genuine retrospective
benchmark on a standard Google Colab NVIDIA Tesla T4, publish it as an unmerged
draft pull request, and preserve the existing scientific gate unchanged.

## Execution model

The notebook remains a thin wrapper over `python -m atlas`. A visible
`ATLAS_REF = "codex/atlas-v1-dynamic-geometry"` selects the exact Git ref. Model
repositories remain pinned to the commits already enforced by Atlas. Each
expensive stage runs in a fresh subprocess so GPU allocations are released when
the stage exits.

The production CLI gains resumable, provenance-bound stages. Repeated
`atlas run` invocations use the same run ID with `--resume` and `--stop-after`.
Cached outputs are reused only when a context record matches the Atlas commit,
input SHA-256, model commits, dynamics mode, and validation-policy version.

## Preflight

`atlas preflight` must complete before model inference. It reports and validates
the NVIDIA device, free GPU memory, PyTorch CUDA visibility, Atlas/model commit
SHAs, 23WN existence and parseability, and Atlas import/version. Any failed
condition exits nonzero and writes no scientific prediction.

## T4 behavior

ThermoMPNN and ThermoMPNN-D execute in separate processes and therefore cannot
retain both models in GPU memory simultaneously. Upstream inference behavior,
weights, thresholds, and the fixed validation criteria are unchanged. Atlas
does not patch upstream scientific source. A standard T4 is the documented
baseline; no premium accelerator is assumed.

## OpenMM fragment treatment

23WN represents pieces of larger molecular chains and lacks terminal atoms at
coordinate truncation boundaries. OpenMM documents `ignoreExternalBonds=True`
as appropriate when a topology is one piece of a larger molecule and chains are
not terminated properly. Atlas may add hydrogens using OpenMM's built-in residue
definitions, then match standard Amber templates while ignoring unresolved
external bonds. It must not add heavy atoms, residues, caps, or sequence. Any
remaining setup failure retains `skipped_unparameterized_system` and zero fake
snapshots.

## Scientific state

Software readiness is distinct from scientific validation. Until the user runs
the real CUDA benchmark, the acceptable project status remains externally
blocked locally. The notebook must expose one of `VALIDATED`, `BENCHMARK FAILED`,
or `EXTERNALLY BLOCKED` from genuine outputs and cannot weaken the predefined
gate after results are observed.
