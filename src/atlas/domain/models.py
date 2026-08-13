"""Pydantic contracts for Atlas scientific state and artifacts."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from atlas.domain.enums import (
    Availability,
    CampaignStatus,
    CandidateStatus,
    EvidenceKind,
    EventKind,
    Provenance,
)


class AtlasModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CampaignConfig(AtlasModel):
    campaign_id: Literal["atlas-vita-abeta-s2"] = "atlas-vita-abeta-s2"
    challenge_name: Literal["Alzheimer’s Aβ Metalloprotease Optimization"] = (
        "Alzheimer’s Aβ Metalloprotease Optimization"
    )
    seed: Literal["DP622-S2"] = "DP622-S2"
    target_context: Literal["Aβ42"] = "Aβ42"
    cleavage_system: Literal["S2"] = "S2"
    campaign_type: Literal["blinded_retrospective"] = "blinded_retrospective"
    optimization_mode: Literal["constrained_scaffold_optimization"] = (
        "constrained_scaffold_optimization"
    )
    profile: Literal["demo_cached"] = "demo_cached"


class Candidate(AtlasModel):
    candidate_id: str
    display_name: str
    is_seed: bool = False
    sequence: str | None = None
    sequence_availability: Availability = Availability.UNAVAILABLE
    mutations: tuple[str, ...] = ()
    status: CandidateStatus = CandidateStatus.PROPOSED
    anonymized_reference: bool = False

    @model_validator(mode="after")
    def sequence_matches_availability(self) -> "Candidate":
        if self.sequence_availability is Availability.UNAVAILABLE and self.sequence is not None:
            raise ValueError("Unavailable sequences must not contain inferred residues")
        if self.sequence_availability is Availability.AVAILABLE and not self.sequence:
            raise ValueError("Available sequences require an exact sequence")
        return self


class Measurement(AtlasModel):
    metric: str
    value: float | int | str
    unit: str
    provenance: Provenance
    uncertainty: str | None = None

    @model_validator(mode="after")
    def reject_synthetic_kinetics(self) -> "Measurement":
        normalized = self.metric.lower().replace("_", "").replace("/", "")
        if self.provenance is Provenance.SYNTHETIC_DEMO and normalized in {
            "kcat",
            "km",
            "kcatkm",
            "kcatperkm",
        }:
            raise ValueError("Synthetic kinetic measurements are forbidden")
        return self


class EvidenceRecord(AtlasModel):
    evidence_id: str
    candidate_id: str
    kind: EvidenceKind
    provenance: Provenance
    summary: str
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    measurements: tuple[Measurement, ...] = ()
    assumptions: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


class ModelRunRecord(AtlasModel):
    run_id: str
    adapter: str
    model_family: str
    profile: str
    started_at: datetime
    finished_at: datetime
    input_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    output_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    provenance: Provenance

    @model_validator(mode="after")
    def finish_not_before_start(self) -> "ModelRunRecord":
        if self.finished_at < self.started_at:
            raise ValueError("Model run cannot finish before it starts")
        return self


class ScientificEvent(AtlasModel):
    event_id: str
    sequence: int = Field(ge=1)
    timestamp: datetime
    kind: EventKind
    stage: str
    summary: str
    candidate_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    previous_hash: str | None = None
    event_hash: str | None = None


class DecisionTrace(AtlasModel):
    campaign_id: str
    generated_at: datetime
    event_ids: tuple[str, ...]
    stages: tuple[str, ...]
    candidate_decisions: dict[str, str]
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class RecommendationLock(AtlasModel):
    lock_id: str
    campaign_id: str
    candidate_id: str
    locked_at: datetime
    decision_trace_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    ledger_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    rationale: str
    locked: Literal[True] = True


class FinalReport(AtlasModel):
    campaign_id: str
    status: CampaignStatus
    summary: str
    winning_candidate: str
    reasons_it_won: tuple[str, ...]
    reasons_alternatives_lost: dict[str, tuple[str, ...]]
    confidence: str
    assumptions: tuple[str, ...]
    known_unknowns: tuple[str, ...]
    model_disagreements: tuple[str, ...]
    scientific_risks: tuple[str, ...]
    recommended_experimental_next_steps: tuple[str, ...]
    evidence_summary: tuple[str, ...]
