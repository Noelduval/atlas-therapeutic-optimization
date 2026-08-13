# VITA Challenge Scientific Asset Recovery Plan

**Goal:** Recover only official, public source-backed assets for the locked Atlas Challenge and integrate them without changing Atlas v1 product scope or scientific claims.

**Scope constraints:** Preserve the existing LangGraph architecture and `demo_cached` behavior. Treat PDB 23WN as the inactive DP622 E96Q structural construct, never as the active DP622-S2 seed. Do not infer missing enzyme sequences or numerical experimental values. Leave unsupported assets explicitly `UNAVAILABLE`.

## Task 1: Inventory and verify official sources

- Inspect the committed VITA paper and the publisher-hosted supplementary PDF.
- Query the official RCSB 23WN deposition, EMDB EMD-69322 entry, and the authors' data-availability repository.
- Record direct source URLs, retrieval date, SHA-256 checksums, evidence class, chain/entity mappings, and scientific caveats.
- Stop searching once these official routes are exhausted.

## Task 2: Specify recovery behavior with tests

- Add tests that require source-backed structure and EMDB metadata assets and validate their checksums.
- Add tests that distinguish the inactive E96Q structural construct from the unavailable active DP622-S2 sequence.
- Add or strengthen tests proving hidden labels are loaded only after a valid persisted recommendation lock and never appear in pre-lock state, evidence, events, Decision Trace, or Scientific Notebook.

## Task 3: Recover assets and add minimal loaders

- Store the RCSB coordinate file at `references/structures/23WN.cif`.
- Store official EMDB entry metadata at `references/structures/EMD-69322_metadata.json`.
- Store the publisher supplementary PDF under `references/` if its integrity is verified.
- Create `data/atlas_challenge/manifest.yaml`, `sequences.yaml`, and `hidden_labels.yaml` with only exact source-backed content.
- Make the smallest necessary challenge-data loading change; do not change graph topology or ranking behavior.

## Task 4: Document recovered and unavailable assets

- Update `docs/atlas-challenge.md`, `docs/reproducibility.md`, and `docs/limitations.md`.
- Update `README.md` only if needed for factual consistency.
- State precisely what was recovered, what remains unavailable, where it came from, and what must not be inferred.

## Task 5: Verify and publish

- Run `uv run pytest`.
- Run `uv run atlas challenge run --profile demo_cached`.
- Run `uv run atlas benchmark run --profile demo_cached`.
- If all pass, stage the scoped recovery changes, commit with `Recover VITA challenge source assets`, and push the current branch.
