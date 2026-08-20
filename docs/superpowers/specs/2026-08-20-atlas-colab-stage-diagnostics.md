# Atlas Colab Stage Diagnostics Specification

## Problem

The first genuine Colab T4 execution passed the GPU/source preflight but the
Stage 3 production CLI exited with status 2. The notebook used
`subprocess.run(check=True)` without capturing output, so it displayed only a
`CalledProcessError`. A local normal-install reproduction showed the hidden
error:

```text
Atlas stopped: RunContextError: Atlas commit cannot be resolved at
.../site-packages; run from a Git checkout
```

`atlas.run_context` inferred the Git checkout from the installed module's
`__file__`. That is valid for an editable developer install and invalid for the
normal install required by a live Colab kernel.

## Required behavior

- The production CLI must receive the Atlas checkout explicitly and record its
  exact Git SHA independently of package installation layout.
- The notebook must run the unchanged production scientific pipeline and retain
  every validation gate and model stage.
- Before Stage 3, a cheap readiness check must verify the Atlas CLI/imports,
  required Python modules, upstream scripts and model files, repository/input
  layout, and writable checkpoint root.
- Every notebook stage failure must print the stage, shell-safe exact command,
  working directory, complete stdout, complete stderr, a safe environment
  whitelist, and a suggested next action before raising a hard exception.
- A clean normal installation must complete the structure-only checkpoint from
  the Git checkout without cached state.

## Claim boundary

This work changes engineering, provenance, and diagnostics only. It must not
change model invocation semantics, structural reconstruction, OpenMM behavior,
benchmark controls or thresholds, the validation gate, or candidate policy.
