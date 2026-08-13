"""Deterministic synthetic evidence used only to exercise Atlas orchestration."""

from datetime import UTC, datetime
from hashlib import sha256

from atlas.adapters.base import EvaluationBundle
from atlas.domain.enums import EvidenceKind, Provenance
from atlas.domain.models import Candidate, EvidenceRecord, ModelRunRecord


_KINDS = (
    EvidenceKind.SEQUENCE,
    EvidenceKind.STRUCTURE,
    EvidenceKind.CATALYTIC_GEOMETRY,
    EvidenceKind.SUBSTRATE_RECOGNITION,
    EvidenceKind.SELECTIVITY_RISK,
    EvidenceKind.DEVELOPABILITY,
    EvidenceKind.SIMULATION_SANITY,
)

_SEED_SCORES = (0.78, 0.82, 0.86, 0.74, 0.72, 0.77, 0.75)
_VARIANT_SCORES = {
    "ATLAS-V001": (0.84, 0.80, 0.58, 0.88, 0.47, 0.70, 0.61),
    "ATLAS-V002": (0.76, 0.79, 0.81, 0.79, 0.63, 0.55, 0.69),
    "ATLAS-V003": (0.81, 0.72, 0.77, 0.70, 0.68, 0.62, 0.57),
    "ATLAS-R001": (0.80, 0.81, 0.69, 0.82, 0.58, 0.68, 0.66),
}


class DemoCachedAdapter:
    profile = "demo_cached"

    def evaluate(self, candidate: Candidate, context: str) -> EvaluationBundle:
        scores = _VARIANT_SCORES.get(candidate.candidate_id, _SEED_SCORES)
        evidence = tuple(
            EvidenceRecord(
                evidence_id=f"demo-{candidate.candidate_id}-{kind.value}",
                candidate_id=candidate.candidate_id,
                kind=kind,
                provenance=Provenance.SYNTHETIC_DEMO,
                summary=(
                    f"Deterministic synthetic demo {kind.value.replace('_', ' ')} score; "
                    "not biological model output and not measured evidence."
                ),
                score=score,
                assumptions=("Cached fixture exercises orchestration only.",),
                limitations=("Cannot support a biological or therapeutic claim.",),
            )
            for kind, score in zip(_KINDS, scores, strict=True)
        )
        input_digest = sha256(f"{candidate.candidate_id}|{context}".encode()).hexdigest()
        output_digest = sha256(
            "|".join(f"{item.kind.value}:{item.score:.2f}" for item in evidence).encode()
        ).hexdigest()
        fixed_time = datetime(2026, 8, 13, tzinfo=UTC)
        return EvaluationBundle(
            evidence=evidence,
            run_record=ModelRunRecord(
                run_id=f"demo-{candidate.candidate_id}",
                adapter="demo_cached",
                model_family="multi_evaluator_demo_interface",
                profile=self.profile,
                started_at=fixed_time,
                finished_at=fixed_time,
                input_digest=input_digest,
                output_digest=output_digest,
                provenance=Provenance.SYNTHETIC_DEMO,
            ),
        )
