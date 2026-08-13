from atlas.adapters.demo_cached import DemoCachedAdapter
from atlas.challenge.vita import load_visible_challenge
from atlas.domain.enums import Availability, CandidateStatus
from atlas.domain.models import Candidate
from atlas.workflow.critic import review_ranking
from atlas.workflow.ranking import pareto_rank


def _candidates() -> tuple[Candidate, ...]:
    seed = load_visible_challenge().seed
    variants = tuple(
        Candidate(
            candidate_id=f"ATLAS-V00{index}",
            display_name=f"Anonymous constrained variant {index}",
            sequence_availability=Availability.UNAVAILABLE,
            status=CandidateStatus.PROPOSED,
        )
        for index in range(1, 4)
    )
    return (seed, *variants)


def _evidence():
    adapter = DemoCachedAdapter()
    return tuple(
        record
        for candidate in _candidates()
        for record in adapter.evaluate(candidate, "atlas-vita-abeta-s2").evidence
    )


def test_pareto_ranking_retains_seed_when_variants_do_not_clear_margin() -> None:
    ranked = pareto_rank(_candidates(), _evidence())
    assert ranked[0].candidate_id == "DP622-S2"
    assert ranked[0].scientific_margin_over_seed == 0.0
    assert any(item.rejection_reasons for item in ranked[1:])


def test_scientific_critic_exposes_model_disagreement() -> None:
    ranked = pareto_rank(_candidates(), _evidence())
    review = review_ranking(ranked, _evidence())
    assert review.recommendation_id == "DP622-S2"
    assert review.iterate is False
    assert any("disagreement" in conflict.lower() for conflict in review.conflicts)
    assert "seed retention" in review.rationale.lower()
