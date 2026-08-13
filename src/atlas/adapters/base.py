"""Protocols for future real scientific model adapters."""

from typing import Protocol

from atlas.domain.models import AtlasModel, CampaignConfig, Candidate, EvidenceRecord, ModelRunRecord


class EvaluationBundle(AtlasModel):
    evidence: tuple[EvidenceRecord, ...]
    run_record: ModelRunRecord


class SequenceEvaluator(Protocol):
    def evaluate(self, candidate: Candidate, context: str) -> EvaluationBundle: ...


class ProposalAdapter(Protocol):
    def propose(self, seed: Candidate, config: CampaignConfig) -> tuple[Candidate, ...]: ...


class StructurePredictor(Protocol):
    def predict(self, candidate: Candidate, context: str) -> EvaluationBundle: ...


class ComplexInteractionPredictor(Protocol):
    def evaluate_complex(self, candidate: Candidate, substrate: str) -> EvaluationBundle: ...


class OpenMMSimulationAdapter(Protocol):
    def sanity_check(self, candidate: Candidate, context: str) -> EvaluationBundle: ...
