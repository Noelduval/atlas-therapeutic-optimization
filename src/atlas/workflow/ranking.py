"""Transparent multi-objective ranking for synthetic demo evidence."""

from statistics import fmean

from atlas.domain.enums import EvidenceKind
from atlas.domain.models import AtlasModel, Candidate, EvidenceRecord


_RANKING_KINDS = (
    EvidenceKind.SEQUENCE,
    EvidenceKind.STRUCTURE,
    EvidenceKind.CATALYTIC_GEOMETRY,
    EvidenceKind.SUBSTRATE_RECOGNITION,
    EvidenceKind.SELECTIVITY_RISK,
    EvidenceKind.DEVELOPABILITY,
    EvidenceKind.SIMULATION_SANITY,
)


class RankedCandidate(AtlasModel):
    candidate_id: str
    aggregate_score: float
    scientific_margin_over_seed: float
    dimension_scores: dict[str, float]
    pareto_front: bool
    rejection_reasons: tuple[str, ...]


def _dimensions(candidate_id: str, evidence: tuple[EvidenceRecord, ...]) -> dict[str, float]:
    dimensions = {
        record.kind.value: record.score
        for record in evidence
        if record.candidate_id == candidate_id
        and record.kind in _RANKING_KINDS
        and record.score is not None
    }
    missing = {kind.value for kind in _RANKING_KINDS} - set(dimensions)
    if missing:
        raise ValueError(f"Candidate {candidate_id} missing evidence: {sorted(missing)}")
    return {key: float(value) for key, value in dimensions.items()}


def _dominates(left: dict[str, float], right: dict[str, float]) -> bool:
    return all(left[key] >= right[key] for key in left) and any(
        left[key] > right[key] for key in left
    )


def pareto_rank(
    candidates: tuple[Candidate, ...],
    evidence: tuple[EvidenceRecord, ...],
) -> tuple[RankedCandidate, ...]:
    scores = {candidate.candidate_id: _dimensions(candidate.candidate_id, evidence) for candidate in candidates}
    aggregates = {
        candidate_id: round(fmean(dimensions.values()), 6)
        for candidate_id, dimensions in scores.items()
    }
    seed_id = next(candidate.candidate_id for candidate in candidates if candidate.is_seed)
    seed_score = aggregates[seed_id]
    ranked: list[RankedCandidate] = []
    for candidate in candidates:
        dimensions = scores[candidate.candidate_id]
        reasons: list[str] = []
        if dimensions[EvidenceKind.CATALYTIC_GEOMETRY.value] < 0.70:
            reasons.append("Catalytic geometry evidence fell below the preservation gate.")
        if dimensions[EvidenceKind.SELECTIVITY_RISK.value] < 0.60:
            reasons.append("Selectivity-risk evidence was weaker than the seed threshold.")
        if dimensions[EvidenceKind.DEVELOPABILITY.value] < 0.65:
            reasons.append("Developability evidence did not support promotion.")
        margin = round(aggregates[candidate.candidate_id] - seed_score, 6)
        if not candidate.is_seed and margin < 0.05:
            reasons.append("Aggregate evidence did not clear the 0.05 seed-promotion margin.")
        ranked.append(
            RankedCandidate(
                candidate_id=candidate.candidate_id,
                aggregate_score=aggregates[candidate.candidate_id],
                scientific_margin_over_seed=margin,
                dimension_scores=dimensions,
                pareto_front=not any(
                    other_id != candidate.candidate_id and _dominates(other, dimensions)
                    for other_id, other in scores.items()
                ),
                rejection_reasons=tuple(reasons),
            )
        )
    return tuple(
        sorted(
            ranked,
            key=lambda item: (
                bool(item.rejection_reasons),
                -item.aggregate_score,
                item.candidate_id,
            ),
        )
    )
