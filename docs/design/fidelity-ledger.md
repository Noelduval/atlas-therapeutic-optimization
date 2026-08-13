# UI Fidelity Ledger

Accepted visual references:

- `docs/design/atlas-first-run.png`
- `docs/design/atlas-run-monitor.png`

These are illustrative visual-language references, not scientific run records.
Their mock timestamps, values, and rationale are non-canonical; the implementation
uses only locked-PRD facts, persisted pre-reveal reasoning, and deterministic 2026
demo events.

Implementation comparison:

1. **Copy:** first-run heading, description, six metadata fields, and two-step
   actions match the locked PRD verbatim.
2. **Information hierarchy:** persistent navigation, challenge identity, timeline,
   recommendation, confidence disclosure, and disagreements follow the reference.
3. **Palette:** true white canvas, navy typography, teal active state, pale blue
   disclosure, and restrained amber warnings are preserved.
4. **Typography:** large high-contrast page titles, compact metadata, and monospaced
   scientific identifiers mirror the reference hierarchy.
5. **Containers:** light rules and open whitespace replace heavy card chrome, as in
   the reference.
6. **Responsive behavior:** the layout has no horizontal overflow at 1440 px or the
   browser’s 480 px minimum; Streamlit collapses navigation at the narrow width.

Intentional implementation differences: native Streamlit navigation omits the
reference-only decorative icons, and the full 20-stage deterministic ledger is
shown instead of the shorter illustrative timeline. These preserve semantics and
accessibility while keeping the reference visual language.
