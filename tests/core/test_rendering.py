from datetime import UTC, datetime, timedelta

from atlas.domain.models import ScientificEvent
from atlas.rendering import build_decision_trace, render_scientific_notebook


def _events() -> tuple[ScientificEvent, ...]:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    return (
        ScientificEvent(
            event_id="evt-0001",
            sequence=1,
            timestamp=base,
            kind="campaign_validated",
            stage="validate_campaign",
            summary="Canonical campaign validated.",
            payload={"decision": "continue"},
        ),
        ScientificEvent(
            event_id="evt-0002",
            sequence=2,
            timestamp=base + timedelta(minutes=1),
            kind="safety_gate_passed",
            stage="safety_gate",
            summary="Scientific claim boundary accepted.",
            payload={"candidate_decision": {"DP622-S2": "retain"}},
        ),
    )


def test_decision_trace_is_complete_and_deterministic() -> None:
    first = build_decision_trace("atlas-vita-abeta-s2", _events())
    second = build_decision_trace("atlas-vita-abeta-s2", tuple(reversed(_events())))
    assert first == second
    assert first.event_ids == ("evt-0001", "evt-0002")
    assert first.stages == ("validate_campaign", "safety_gate")
    assert first.candidate_decisions == {"DP622-S2": "retain"}
    assert len(first.digest) == 64


def test_scientific_notebook_rendering_is_byte_deterministic() -> None:
    first = render_scientific_notebook(_events())
    second = render_scientific_notebook(tuple(reversed(_events())))
    assert first == second
    assert "# Atlas Scientific Notebook" in first
    assert "Canonical campaign validated." in first
    assert "candidate_decision" in first
