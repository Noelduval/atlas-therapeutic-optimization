"""Deterministic human- and machine-readable scientific artifacts."""

import json
from hashlib import sha256

from atlas.domain.models import DecisionTrace, ScientificEvent


def _ordered(events: tuple[ScientificEvent, ...]) -> tuple[ScientificEvent, ...]:
    return tuple(sorted(events, key=lambda event: (event.sequence, event.event_id)))


def build_decision_trace(
    campaign_id: str,
    events: tuple[ScientificEvent, ...],
    candidate_decisions: dict[str, str] | None = None,
) -> DecisionTrace:
    ordered = _ordered(events)
    if not ordered:
        raise ValueError("A Decision Trace requires at least one event")
    decisions: dict[str, str] = dict(candidate_decisions or {})
    for event in ordered:
        candidate_decision = event.payload.get("candidate_decision")
        if isinstance(candidate_decision, dict):
            decisions.update({str(key): str(value) for key, value in candidate_decision.items()})
    digest_input = {
        "campaign_id": campaign_id,
        "event_ids": [event.event_id for event in ordered],
        "stages": [event.stage for event in ordered],
        "candidate_decisions": decisions,
    }
    digest = sha256(
        json.dumps(
            digest_input,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    return DecisionTrace(
        campaign_id=campaign_id,
        generated_at=ordered[-1].timestamp,
        event_ids=tuple(event.event_id for event in ordered),
        stages=tuple(event.stage for event in ordered),
        candidate_decisions=decisions,
        digest=digest,
    )


def render_scientific_notebook(events: tuple[ScientificEvent, ...]) -> str:
    sections = [
        "# Atlas Scientific Notebook",
        "",
        "This notebook is deterministically rendered from the append-only scientific event ledger.",
        "",
    ]
    for event in _ordered(events):
        sections.extend(
            [
                f"## {event.sequence:02d}. {event.stage}",
                "",
                f"- Event: `{event.kind.value}`",
                f"- Time: `{event.timestamp.isoformat().replace('+00:00', 'Z')}`",
                f"- Summary: {event.summary}",
            ]
        )
        if event.candidate_id:
            sections.append(f"- Candidate: `{event.candidate_id}`")
        if event.payload:
            sections.extend(
                [
                    "- Payload:",
                    "",
                    "```json",
                    json.dumps(
                        event.payload,
                        sort_keys=True,
                        indent=2,
                        ensure_ascii=False,
                    ),
                    "```",
                ]
            )
        sections.append("")
    return "\n".join(sections).rstrip() + "\n"
