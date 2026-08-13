"""Compile and run the complete deterministic Atlas v1 LangGraph."""

from pathlib import Path

from langgraph.graph import END, START, StateGraph

from atlas.domain.models import (
    AtlasModel,
    CampaignConfig,
    DecisionTrace,
    FinalReport,
    RecommendationLock,
    ScientificEvent,
    Candidate,
    EvidenceRecord,
    ModelRunRecord,
)
from atlas.challenge.hidden import HiddenOutcomeBundle
from atlas.ledger import ScientificLedger
from atlas.profiles import PROFILES
from atlas.workflow import nodes
from atlas.workflow.state import AtlasState
from atlas.workflow.ranking import RankedCandidate


class CampaignRun(AtlasModel):
    run_dir: str
    events: tuple[ScientificEvent, ...]
    decision_trace: DecisionTrace
    recommendation_lock: RecommendationLock
    final_report: FinalReport
    candidates: tuple[Candidate, ...]
    evidence: tuple[EvidenceRecord, ...]
    model_runs: tuple[ModelRunRecord, ...]
    ranked: tuple[RankedCandidate, ...]
    retrospective_outcomes: HiddenOutcomeBundle


_BEFORE_CRITIC = (
    ("validate_campaign", nodes.validate_campaign),
    ("safety_gate", nodes.safety_gate),
    ("load_challenge", nodes.load_challenge),
    ("characterize_seed", nodes.characterize_seed),
    ("establish_baseline", nodes.establish_baseline),
    ("propose_variants", nodes.propose_variants),
    ("evaluate_sequence", nodes.evaluate_sequence),
    ("evaluate_structure", nodes.evaluate_structure),
    ("evaluate_geometry", nodes.evaluate_geometry),
    ("evaluate_recognition", nodes.evaluate_recognition),
    ("evaluate_selectivity", nodes.evaluate_selectivity),
    ("evaluate_developability", nodes.evaluate_developability),
    ("evaluate_simulation", nodes.evaluate_simulation),
    ("detect_disagreement", nodes.detect_disagreement),
    ("pareto_rank", nodes.rank_candidates),
)

_REFINEMENT_SEQUENCE = (
    ("scientific_critic", nodes.scientific_critic),
    ("refine_variants", nodes.refine_variants),
    ("reevaluate_sequence", nodes.evaluate_sequence),
    ("reevaluate_structure", nodes.evaluate_structure),
    ("reevaluate_geometry", nodes.evaluate_geometry),
    ("reevaluate_recognition", nodes.evaluate_recognition),
    ("reevaluate_selectivity", nodes.evaluate_selectivity),
    ("reevaluate_developability", nodes.evaluate_developability),
    ("reevaluate_simulation", nodes.evaluate_simulation),
    ("redetect_disagreement", nodes.detect_disagreement),
    ("rerank", nodes.rank_candidates),
    ("final_scientific_critic", nodes.scientific_critic),
)

_AFTER_CRITIC = (
    ("iterate_or_terminate", nodes.iterate_or_terminate),
    ("lock_recommendation", nodes.lock_recommendation),
)

_NODE_SEQUENCE = (*_BEFORE_CRITIC, *_REFINEMENT_SEQUENCE, *_AFTER_CRITIC)


def build_campaign_graph(profile: str = "demo_cached"):
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}")
    builder = StateGraph(AtlasState)
    for name, node in _NODE_SEQUENCE:
        builder.add_node(name, node)
    builder.add_edge(START, _NODE_SEQUENCE[0][0])
    for (left, _), (right, _) in zip(_NODE_SEQUENCE, _NODE_SEQUENCE[1:], strict=False):
        builder.add_edge(left, right)
    builder.add_edge(_NODE_SEQUENCE[-1][0], END)
    return builder.compile()


def run_campaign(
    config: CampaignConfig,
    run_dir: str | Path,
    profile: str = "demo_cached",
) -> CampaignRun:
    directory = Path(run_dir)
    ledger_path = directory / "events.jsonl"
    if ledger_path.exists():
        raise FileExistsError(f"Refusing to overwrite append-only ledger: {ledger_path}")
    directory.mkdir(parents=True, exist_ok=True)
    result = build_campaign_graph(profile).invoke(
        {
            "config": config,
            "profile": profile,
            "run_dir": str(directory),
            "events": [],
            "evidence": [],
            "model_runs": [],
        }
    )
    persisted = nodes.persist_recommendation_artifacts(result)
    postlock = {**result, **persisted}
    revealed = nodes.reveal_hidden_labels(postlock)
    postlock.update(revealed)
    postlock["events"] = [*result["events"], *revealed["events"]]
    reported = nodes.produce_final_report(postlock)
    postlock_events = postlock["events"]
    postlock.update(reported)
    postlock["events"] = [*postlock_events, *reported["events"]]
    ledger = ScientificLedger(ledger_path)
    persisted_count = len(ledger.read_all())
    for event in postlock["events"][persisted_count:]:
        ledger.append(event)
    linked_events = ledger.read_all()
    return CampaignRun(
        run_dir=str(directory),
        events=linked_events,
        decision_trace=postlock["decision_trace"],
        recommendation_lock=postlock["recommendation_lock"],
        final_report=postlock["final_report"],
        candidates=tuple(postlock["candidates"]),
        evidence=tuple(postlock["evidence"]),
        model_runs=tuple(postlock["model_runs"]),
        ranked=tuple(postlock["ranked"]),
        retrospective_outcomes=postlock["postlock_reveal"],
    )
