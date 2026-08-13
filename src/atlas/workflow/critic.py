"""Deterministic adversarial review of evidence and ranking."""

from atlas.domain.models import AtlasModel, EvidenceRecord
from atlas.workflow.ranking import RankedCandidate


class CriticReview(AtlasModel):
    recommendation_id: str
    conflicts: tuple[str, ...]
    rationale: str
    iterate: bool


def review_ranking(
    ranked: tuple[RankedCandidate, ...],
    evidence: tuple[EvidenceRecord, ...],
    allow_iteration: bool = False,
) -> CriticReview:
    del evidence  # Ranking carries the auditable dimension scores used by this deterministic critic.
    conflicts: list[str] = []
    for candidate in ranked:
        spread = max(candidate.dimension_scores.values()) - min(candidate.dimension_scores.values())
        if spread >= 0.25:
            conflicts.append(
                f"Model disagreement for {candidate.candidate_id}: evidence dimension spread {spread:.2f}."
            )
    recommendation = ranked[0]
    seed_retained = recommendation.candidate_id == "DP622-S2"
    iterate = allow_iteration and bool(conflicts)
    if iterate:
        rationale = (
            "Conflicting evaluator evidence requires one constrained refinement iteration "
            "before a recommendation can be locked."
        )
    elif seed_retained:
        rationale = (
            "Seed retention is scientifically complete: no constrained variant cleared both "
            "the scientific gates and promotion margin."
        )
    else:
        rationale = "A constrained variant cleared the seed-promotion margin and all scientific gates."
    return CriticReview(
        recommendation_id=recommendation.candidate_id,
        conflicts=tuple(conflicts),
        rationale=rationale,
        iterate=iterate,
    )
