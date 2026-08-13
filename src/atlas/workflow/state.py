"""LangGraph state contains no retrospective outcomes before recommendation lock."""

import operator
from typing import Annotated, TypedDict

from atlas.challenge.vita import ChallengeDataset
from atlas.domain.enums import CampaignStatus
from atlas.domain.models import (
    CampaignConfig,
    Candidate,
    DecisionTrace,
    EvidenceRecord,
    ModelRunRecord,
    RecommendationLock,
    ScientificEvent,
)
from atlas.workflow.critic import CriticReview
from atlas.workflow.ranking import RankedCandidate


class AtlasState(TypedDict, total=False):
    config: CampaignConfig
    profile: str
    run_dir: str
    iteration: int
    dataset: ChallengeDataset
    candidates: tuple[Candidate, ...]
    evidence: Annotated[list[EvidenceRecord], operator.add]
    model_runs: Annotated[list[ModelRunRecord], operator.add]
    events: Annotated[list[ScientificEvent], operator.add]
    ranked: tuple[RankedCandidate, ...]
    critic_review: CriticReview
    status: CampaignStatus
    decision_trace: DecisionTrace
    recommendation_lock: RecommendationLock
