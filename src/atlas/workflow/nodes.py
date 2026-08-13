"""Deterministic nodes for the Atlas v1 LangGraph."""

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Callable

from atlas.adapters.demo_cached import DemoCachedAdapter
from atlas.challenge.hidden import HiddenLabelRepository
from atlas.challenge.vita import load_visible_challenge
from atlas.domain.enums import (
    Availability,
    CampaignStatus,
    CandidateStatus,
    EvidenceKind,
    EventKind,
    Provenance,
)
from atlas.domain.models import (
    Candidate,
    EvidenceRecord,
    FinalReport,
    RecommendationLock,
    ScientificEvent,
)
from atlas.firewall import assert_prelock_state_clean
from atlas.ledger import ScientificLedger, ledger_snapshot_digest
from atlas.rendering import build_decision_trace
from atlas.workflow.critic import review_ranking
from atlas.workflow.ranking import pareto_rank
from atlas.workflow.state import AtlasState


_BASE_TIME = datetime(2026, 8, 13, tzinfo=UTC)


def _event(
    state: AtlasState,
    kind: EventKind,
    stage: str,
    summary: str,
    payload: dict | None = None,
) -> ScientificEvent:
    sequence = len(state.get("events", [])) + 1
    return ScientificEvent(
        event_id=f"evt-{sequence:04d}",
        sequence=sequence,
        timestamp=_BASE_TIME + timedelta(minutes=sequence),
        kind=kind,
        stage=stage,
        summary=summary,
        payload=payload or {},
    )


def validate_campaign(state: AtlasState) -> dict:
    assert_prelock_state_clean(state)
    config = state["config"]
    return {
        "events": [
            _event(
                state,
                EventKind.CAMPAIGN_VALIDATED,
                "validate_campaign",
                "Canonical DP622-S2 / Aβ42 / S2 campaign validated.",
                {"profile": state["profile"]},
            )
        ],
        "status": CampaignStatus.RUNNING,
        "config": config,
    }


def safety_gate(state: AtlasState) -> dict:
    assert_prelock_state_clean(state)
    return {
        "events": [
            _event(
                state,
                EventKind.SAFETY_GATE_PASSED,
                "safety_gate",
                "Claim discipline and hidden-label firewall accepted.",
                {"synthetic_demo_only": True, "kinetic_synthesis_forbidden": True},
            )
        ]
    }


def load_challenge(state: AtlasState) -> dict:
    assert_prelock_state_clean(state)
    dataset = load_visible_challenge()
    return {
        "dataset": dataset,
        "events": [
            _event(
                state,
                EventKind.CHALLENGE_LOADED,
                "load_challenge",
                "Visible VITA challenge manifest loaded; retrospective labels remain isolated.",
            )
        ],
    }


def characterize_seed(state: AtlasState) -> dict:
    assert_prelock_state_clean(state)
    seed = state["dataset"].seed
    return {
        "candidates": (seed,),
        "events": [
            _event(
                state,
                EventKind.SEED_CHARACTERIZED,
                "characterize_seed",
                "DP622-S2 seed registered with exact sequence marked unavailable.",
                {"candidate_id": seed.candidate_id, "sequence": "UNAVAILABLE"},
            )
        ],
    }


def establish_baseline(state: AtlasState) -> dict:
    assert_prelock_state_clean(state)
    evidence = EvidenceRecord(
        evidence_id="published-geometry-DP622-S2",
        candidate_id="DP622-S2",
        kind=EvidenceKind.CATALYTIC_GEOMETRY,
        provenance=Provenance.PUBLISHED_STRUCTURAL,
        summary=(
            "The inactive E96Q cryo-EM reference reports preserved P1 oxygen-zinc and "
            "oxyanion-hole geometry; this is structural evidence, not catalytic activity."
        ),
        score=None,
        limitations=("PDB 23WN is the inactive E96Q pre-catalytic construct.",),
    )
    return {
        "evidence": [evidence],
        "events": [
            _event(
                state,
                EventKind.BASELINE_ESTABLISHED,
                "establish_baseline",
                "Published structural geometry baseline established without importing hidden outcomes.",
            )
        ],
    }


def propose_variants(state: AtlasState) -> dict:
    assert_prelock_state_clean(state)
    variants = tuple(
        Candidate(
            candidate_id=f"ATLAS-V00{index}",
            display_name=f"Anonymous constrained variant {index}",
            sequence=None,
            sequence_availability=Availability.UNAVAILABLE,
            status=CandidateStatus.PROPOSED,
        )
        for index in range(1, 4)
    )
    candidates = (state["dataset"].seed, *variants)
    return {
        "candidates": candidates,
        "iteration": 1,
        "events": [
            _event(
                state,
                EventKind.VARIANTS_PROPOSED,
                "propose_constrained_variants",
                "Three abstract constrained demo hypotheses proposed; exact sequences were not fabricated.",
                {"candidate_ids": [candidate.candidate_id for candidate in variants]},
            )
        ],
    }


def _evaluate(kind: EvidenceKind, event_kind: EventKind, stage: str) -> Callable[[AtlasState], dict]:
    def node(state: AtlasState) -> dict:
        assert_prelock_state_clean(state)
        adapter = DemoCachedAdapter()
        candidates = (
            tuple(
                candidate
                for candidate in state["candidates"]
                if candidate.candidate_id.startswith("ATLAS-R")
            )
            if state.get("iteration", 1) > 1
            else state["candidates"]
        )
        bundles = [
            adapter.evaluate(candidate, state["config"].campaign_id)
            for candidate in candidates
        ]
        evidence = [
            record
            for bundle in bundles
            for record in bundle.evidence
            if record.kind is kind
        ]
        result: dict = {
            "evidence": evidence,
            "events": [
                _event(
                    state,
                    event_kind,
                    stage,
                    f"Deterministic synthetic demo {kind.value.replace('_', ' ')} evidence evaluated.",
                    {"provenance": "synthetic_demo", "candidate_count": len(evidence)},
                )
            ],
        }
        if kind is EvidenceKind.SEQUENCE:
            result["model_runs"] = [bundle.run_record for bundle in bundles]
        return result

    return node


evaluate_sequence = _evaluate(
    EvidenceKind.SEQUENCE, EventKind.SEQUENCE_EVALUATED, "evaluate_sequence_evidence"
)
evaluate_structure = _evaluate(
    EvidenceKind.STRUCTURE, EventKind.STRUCTURE_EVALUATED, "evaluate_structure_evidence"
)
evaluate_geometry = _evaluate(
    EvidenceKind.CATALYTIC_GEOMETRY,
    EventKind.CATALYTIC_GEOMETRY_EVALUATED,
    "evaluate_catalytic_geometry",
)
evaluate_recognition = _evaluate(
    EvidenceKind.SUBSTRATE_RECOGNITION,
    EventKind.SUBSTRATE_RECOGNITION_EVALUATED,
    "evaluate_substrate_recognition",
)
evaluate_selectivity = _evaluate(
    EvidenceKind.SELECTIVITY_RISK,
    EventKind.SELECTIVITY_RISK_EVALUATED,
    "evaluate_selectivity_risk",
)
evaluate_developability = _evaluate(
    EvidenceKind.DEVELOPABILITY,
    EventKind.DEVELOPABILITY_EVALUATED,
    "evaluate_developability",
)
evaluate_simulation = _evaluate(
    EvidenceKind.SIMULATION_SANITY,
    EventKind.SIMULATION_SANITY_CHECKED,
    "simulation_sanity_check",
)


def detect_disagreement(state: AtlasState) -> dict:
    assert_prelock_state_clean(state)
    disagreements: list[EvidenceRecord] = []
    candidates = (
        tuple(
            candidate
            for candidate in state["candidates"]
            if candidate.candidate_id.startswith("ATLAS-R")
        )
        if state.get("iteration", 1) > 1
        else state["candidates"]
    )
    for candidate in candidates:
        scores = [
            record.score
            for record in state["evidence"]
            if record.candidate_id == candidate.candidate_id and record.score is not None
        ]
        spread = max(scores) - min(scores)
        if spread >= 0.25:
            disagreements.append(
                EvidenceRecord(
                    evidence_id=f"demo-{candidate.candidate_id}-disagreement",
                    candidate_id=candidate.candidate_id,
                    kind=EvidenceKind.MODEL_DISAGREEMENT,
                    provenance=Provenance.SYNTHETIC_DEMO,
                    summary=(
                        f"Deterministic evaluator disagreement spread {spread:.2f}; "
                        "not biological model output."
                    ),
                    score=round(spread, 2),
                )
            )
    return {
        "evidence": disagreements,
        "events": [
            _event(
                state,
                EventKind.MODEL_DISAGREEMENT_DETECTED,
                "detect_model_disagreement",
                "Cross-evaluator disagreement was retained as first-class evidence.",
                {"flagged_candidates": [item.candidate_id for item in disagreements]},
            )
        ],
    }


def rank_candidates(state: AtlasState) -> dict:
    assert_prelock_state_clean(state)
    ranked = pareto_rank(state["candidates"], tuple(state["evidence"]))
    return {
        "ranked": ranked,
        "events": [
            _event(
                state,
                EventKind.PARETO_RANKED,
                "pareto_rank",
                "Candidates ranked across seven independent evidence dimensions.",
                {"ordered_candidate_ids": [item.candidate_id for item in ranked]},
            )
        ],
    }


def scientific_critic(state: AtlasState) -> dict:
    assert_prelock_state_clean(state)
    review = review_ranking(
        state["ranked"],
        tuple(state["evidence"]),
        allow_iteration=state.get("iteration", 1) < 2,
    )
    return {
        "critic_review": review,
        "events": [
            _event(
                state,
                EventKind.SCIENTIFIC_CRITIC_REVIEWED,
                "scientific_critic",
                review.rationale,
                {"conflicts": list(review.conflicts)},
            )
        ],
    }


def refine_variants(state: AtlasState) -> dict:
    assert_prelock_state_clean(state)
    refined = Candidate(
        candidate_id="ATLAS-R001",
        display_name="Anonymous critic-guided refinement 1",
        sequence=None,
        sequence_availability=Availability.UNAVAILABLE,
        status=CandidateStatus.PROPOSED,
    )
    candidates = tuple(state["candidates"])
    if all(candidate.candidate_id != refined.candidate_id for candidate in candidates):
        candidates = (*candidates, refined)
    return {
        "candidates": candidates,
        "iteration": state.get("iteration", 1) + 1,
        "events": [
            _event(
                state,
                EventKind.VARIANTS_REFINED,
                "refine_constrained_variants",
                "Scientific Critic requested one abstract constrained refinement; no sequence was fabricated.",
                {"candidate_ids": [refined.candidate_id], "iteration": 2},
            )
        ],
    }


def iterate_or_terminate(state: AtlasState) -> dict:
    assert_prelock_state_clean(state)
    return {
        "status": CampaignStatus.SCIENTIFICALLY_COMPLETE,
        "events": [
            _event(
                state,
                EventKind.ITERATION_TERMINATED,
                "iterate_or_terminate",
                "Campaign terminated scientifically_complete after the deterministic critic review.",
                {
                    "iteration": state.get("iteration", 1),
                    "reason": "no_variant_cleared_seed_promotion_margin",
                },
            )
        ],
    }


def lock_recommendation(state: AtlasState) -> dict:
    assert_prelock_state_clean(state)
    events = tuple(state["events"])
    trace = build_decision_trace(
        state["config"].campaign_id,
        events,
        candidate_decisions={state["critic_review"].recommendation_id: "recommended"},
    )
    event_digest = ledger_snapshot_digest(events)
    sequence = len(events) + 1
    review = state["critic_review"]
    lock = RecommendationLock(
        lock_id="lock-atlas-vita-demo-cached",
        campaign_id=state["config"].campaign_id,
        candidate_id=review.recommendation_id,
        locked_at=_BASE_TIME + timedelta(minutes=sequence),
        decision_trace_digest=trace.digest,
        ledger_digest=event_digest,
        rationale=review.rationale,
    )
    return {
        "decision_trace": trace,
        "recommendation_lock": lock,
        "events": [
            _event(
                state,
                EventKind.RECOMMENDATION_LOCKED,
                "lock_recommendation",
                "Recommendation and pre-reveal Decision Trace locked.",
                {
                    "candidate_decision": {lock.candidate_id: "recommended"},
                    "lock_id": lock.lock_id,
                    "decision_trace_digest": lock.decision_trace_digest,
                    "prelock_ledger_digest": lock.ledger_digest,
                },
            )
        ],
    }


def _persist_frozen_json(path: Path, value: object) -> None:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    serialized = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    with path.open("x", encoding="utf-8") as stream:
        stream.write(serialized)
        stream.flush()
        os.fsync(stream.fileno())


def persist_recommendation_artifacts(state: AtlasState) -> dict:
    """Durably establish the recommendation boundary before label reveal."""
    directory = Path(state["run_dir"])
    directory.mkdir(parents=True, exist_ok=True)
    ledger = ScientificLedger(directory / "events.jsonl")
    if ledger.read_all():
        raise FileExistsError("Refusing to replace an existing scientific ledger")
    for event in state["events"]:
        ledger.append(event)

    trace_path = directory / "decision-trace.json"
    lock_path = directory / "recommendation-lock.json"
    _persist_frozen_json(trace_path, state["decision_trace"])
    _persist_frozen_json(lock_path, state["recommendation_lock"])
    return {"persisted_lock_path": str(lock_path)}


def reveal_hidden_labels(state: AtlasState) -> dict:
    outcomes = HiddenLabelRepository().reveal(
        state["recommendation_lock"], state.get("persisted_lock_path")
    )
    return {
        "postlock_reveal": outcomes,
        "events": [
            _event(
                state,
                EventKind.RETROSPECTIVE_LABELS_REVEALED,
                "reveal_hidden_retrospective_labels",
                "Published retrospective controls revealed only after recommendation lock.",
                {
                    "control_identities": [control.identity for control in outcomes.controls],
                    "verified_persisted_lock": True,
                },
            )
        ],
    }


def produce_final_report(state: AtlasState) -> dict:
    ranked = state["ranked"]
    alternatives = {
        item.candidate_id: item.rejection_reasons
        for item in ranked
        if item.candidate_id != state["recommendation_lock"].candidate_id
    }
    revealed_identities = {
        control.identity for control in state["postlock_reveal"].controls
    }
    retrospective_alignment = (
        "recovered_published_optimized_control"
        if state["recommendation_lock"].candidate_id in revealed_identities
        else "did_not_recover_published_optimized_control"
    )
    seed_efficiency = state["postlock_reveal"].seed_control.published_efficiency_m_inverse_s
    best_control = max(
        state["postlock_reveal"].controls,
        key=lambda control: control.published_efficiency_m_inverse_s,
    )
    published_fold_over_seed = round(
        best_control.published_efficiency_m_inverse_s / seed_efficiency, 2
    )
    report = FinalReport(
        campaign_id=state["config"].campaign_id,
        status=CampaignStatus.SCIENTIFICALLY_COMPLETE,
        summary=(
            "The deterministic demo campaign retained DP622-S2 because no abstract constrained "
            "variant cleared the promotion margin and scientific gates."
        ),
        winning_candidate=state["recommendation_lock"].candidate_id,
        reasons_it_won=(
            "Balanced synthetic demo evidence across all seven evaluation dimensions.",
            "No proposed variant provided sufficiently stronger evidence than the seed.",
            "Seed retention avoids rewarding novelty for novelty’s sake.",
        ),
        reasons_alternatives_lost=alternatives,
        confidence="Bounded confidence in deterministic orchestration behavior only.",
        assumptions=(
            "Cached scores are synthetic demo evidence, not biological model outputs.",
            "The inactive E96Q structure supports geometry interpretation only.",
        ),
        known_unknowns=(
            "Exact active DP622-S2, OP609-S2, and OP669-S2 sequences are unavailable.",
            "Raw assay-level measurements and named optimized-variant coordinate/design files are unavailable.",
            "Full EMDB map voxels are not present locally because the current workflow does not consume them.",
        ),
        model_disagreements=state["critic_review"].conflicts,
        scientific_risks=(
            "Catalytic geometry does not establish catalytic activity.",
            "Aβ cleavage does not establish disease modification or therapeutic benefit.",
            "Retrospective reference data may be represented in model training corpora.",
        ),
        recommended_experimental_next_steps=(
            "Recover exact sequence and structural assets before physical variant design.",
            "Express the locked recommendation and blinded comparators.",
            "Measure cleavage, kinetics, selectivity, stability, and aggregation experimentally.",
        ),
        evidence_summary=(
            "Seven deterministic synthetic demo dimensions were evaluated without synthetic kinetics.",
            (
                "Published optimized controls were revealed only after recommendation lock; "
                f"retrospective comparison: {retrospective_alignment}."
            ),
        ),
    )
    return {
        "final_report": report,
        "events": [
            _event(
                state,
                EventKind.FINAL_REPORT_PRODUCED,
                "produce_final_report",
                "Final report produced with claim boundaries and negative results intact.",
                {
                    "winning_candidate": report.winning_candidate,
                    "retrospective_alignment": retrospective_alignment,
                    "best_published_control": best_control.identity,
                    "published_fold_over_seed": published_fold_over_seed,
                },
            )
        ],
    }
