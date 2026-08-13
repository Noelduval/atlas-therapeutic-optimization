from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from atlas.domain.enums import (
    Availability,
    CampaignStatus,
    EvidenceKind,
    Provenance,
)
from atlas.domain.models import (
    CampaignConfig,
    Candidate,
    DecisionTrace,
    EvidenceRecord,
    FinalReport,
    Measurement,
    ModelRunRecord,
    RecommendationLock,
    ScientificEvent,
)


def test_campaign_config_accepts_only_locked_canonical_context() -> None:
    config = CampaignConfig()
    assert config.seed == "DP622-S2"
    assert config.target_context == "Aβ42"
    assert config.cleavage_system == "S2"

    with pytest.raises(ValidationError):
        CampaignConfig(seed="another-seed")


def test_candidate_marks_missing_exact_sequence_unavailable() -> None:
    candidate = Candidate(
        candidate_id="DP622-S2",
        display_name="DP622-S2",
        is_seed=True,
        sequence=None,
        sequence_availability=Availability.UNAVAILABLE,
    )
    assert candidate.sequence is None

    with pytest.raises(ValidationError):
        Candidate(
            candidate_id="invalid",
            display_name="Invalid",
            sequence="ACD",
            sequence_availability=Availability.UNAVAILABLE,
        )


@pytest.mark.parametrize("metric", ["kcat", "Km", "kcat/Km", "kcat_per_km"])
def test_synthetic_kinetic_measurements_are_forbidden(metric: str) -> None:
    with pytest.raises(ValidationError, match="Synthetic kinetic measurements"):
        Measurement(
            metric=metric,
            value=1.0,
            unit="arbitrary",
            provenance=Provenance.SYNTHETIC_DEMO,
        )


def test_catalytic_geometry_is_distinct_from_activity() -> None:
    evidence = EvidenceRecord(
        evidence_id="geometry-1",
        candidate_id="DP622-S2",
        kind=EvidenceKind.CATALYTIC_GEOMETRY,
        provenance=Provenance.PUBLISHED_STRUCTURAL,
        summary="Inactive E96Q structural reference preserves the observed geometry.",
        score=None,
    )
    assert evidence.kind is EvidenceKind.CATALYTIC_GEOMETRY
    assert evidence.kind is not EvidenceKind.CATALYTIC_ACTIVITY


def test_all_required_models_are_frozen_and_serializable() -> None:
    now = datetime(2026, 8, 13, tzinfo=UTC)
    event = ScientificEvent(
        event_id="evt-0001",
        sequence=1,
        timestamp=now,
        kind="campaign_validated",
        stage="validate_campaign",
        summary="Canonical campaign validated.",
    )
    trace = DecisionTrace(
        campaign_id="atlas-vita-abeta-s2",
        generated_at=now,
        event_ids=(event.event_id,),
        stages=(event.stage,),
        candidate_decisions={"DP622-S2": "retained"},
        digest="a" * 64,
    )
    lock = RecommendationLock(
        lock_id="lock-0001",
        campaign_id="atlas-vita-abeta-s2",
        candidate_id="DP622-S2",
        locked_at=now,
        decision_trace_digest=trace.digest,
        ledger_digest="b" * 64,
        rationale="No constrained variant exceeded the seed evidence threshold.",
    )
    run = ModelRunRecord(
        run_id="run-0001",
        adapter="demo_cached",
        model_family="sequence_evaluator_interface",
        profile="demo_cached",
        started_at=now,
        finished_at=now,
        input_digest="c" * 64,
        output_digest="d" * 64,
        provenance=Provenance.SYNTHETIC_DEMO,
    )
    report = FinalReport(
        campaign_id="atlas-vita-abeta-s2",
        status=CampaignStatus.SCIENTIFICALLY_COMPLETE,
        summary="A deterministic retrospective prioritization run.",
        winning_candidate="DP622-S2",
        reasons_it_won=("Best supported option under demo evidence.",),
        reasons_alternatives_lost={"ATLAS-V001": ("Geometry concern.",)},
        confidence="bounded",
        assumptions=("Synthetic demo evidence is not measured evidence.",),
        known_unknowns=("Exact DP622-S2 sequence is unavailable.",),
        model_disagreements=("Sequence and geometry evaluators disagree.",),
        scientific_risks=("Computational evidence requires experimental validation.",),
        recommended_experimental_next_steps=("Express and assay the recommendation.",),
        evidence_summary=("No synthetic kinetics were generated.",),
    )

    assert lock.locked is True
    assert run.model_dump(mode="json")["provenance"] == "synthetic_demo"
    assert report.model_dump(mode="json")["winning_candidate"] == "DP622-S2"
    with pytest.raises(ValidationError):
        lock.locked = False


def test_final_report_exposes_exact_required_sections() -> None:
    required = {
        "summary",
        "winning_candidate",
        "reasons_it_won",
        "reasons_alternatives_lost",
        "confidence",
        "assumptions",
        "known_unknowns",
        "model_disagreements",
        "scientific_risks",
        "recommended_experimental_next_steps",
        "evidence_summary",
    }
    assert required <= set(FinalReport.model_fields)
