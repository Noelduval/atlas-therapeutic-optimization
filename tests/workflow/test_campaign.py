import json

from atlas.domain.enums import CampaignStatus, EventKind
from atlas.domain.models import CampaignConfig
from atlas.ledger import ScientificLedger
from atlas.workflow.graph import build_campaign_graph, run_campaign


def test_campaign_emits_complete_ordered_workflow_and_locks_before_reveal(tmp_path) -> None:
    run = run_campaign(CampaignConfig(), tmp_path, profile="demo_cached")
    kinds = tuple(event.kind for event in run.events)
    assert set(EventKind) <= set(kinds)
    assert kinds.count(EventKind.VARIANTS_REFINED) == 1
    assert kinds.count(EventKind.SCIENTIFIC_CRITIC_REVIEWED) == 2
    assert kinds.index(EventKind.RECOMMENDATION_LOCKED) < kinds.index(
        EventKind.RETROSPECTIVE_LABELS_REVEALED
    )
    assert run.recommendation_lock.candidate_id == "DP622-S2"
    assert run.final_report.status is CampaignStatus.SCIENTIFICALLY_COMPLETE
    assert run.final_report.winning_candidate == "DP622-S2"
    assert run.decision_trace.candidate_decisions == {"DP622-S2": "recommended"}


def test_prelock_state_and_artifacts_do_not_contain_hidden_outcomes(tmp_path) -> None:
    run = run_campaign(CampaignConfig(), tmp_path, profile="demo_cached")
    lock_index = next(
        index
        for index, event in enumerate(run.events)
        if event.kind is EventKind.RECOMMENDATION_LOCKED
    )
    prelock = json.dumps(
        [event.model_dump(mode="json") for event in run.events[:lock_index]],
        ensure_ascii=False,
    )
    for forbidden in ("OP609", "OP669", "3045.14", "452.49"):
        assert forbidden not in prelock
    assert EventKind.RETROSPECTIVE_LABELS_REVEALED.value not in run.decision_trace.stages
    assert run.decision_trace.event_ids[-1] == run.events[lock_index - 1].event_id


def test_rejected_candidates_and_negative_evidence_remain_visible(tmp_path) -> None:
    run = run_campaign(CampaignConfig(), tmp_path, profile="demo_cached")
    assert set(run.final_report.reasons_alternatives_lost) == {
        "ATLAS-V001",
        "ATLAS-V002",
        "ATLAS-V003",
        "ATLAS-R001",
    }
    assert any("geometry" in reason.lower() for reason in run.final_report.reasons_alternatives_lost["ATLAS-V001"])
    assert run.final_report.status.value == "scientifically_complete"


def test_campaign_is_deterministic_across_fresh_run_directories(tmp_path) -> None:
    first = run_campaign(CampaignConfig(), tmp_path / "one", profile="demo_cached")
    second = run_campaign(CampaignConfig(), tmp_path / "two", profile="demo_cached")
    assert first.final_report == second.final_report
    assert first.decision_trace == second.decision_trace
    assert [event.model_dump(mode="json") for event in first.events] == [
        event.model_dump(mode="json") for event in second.events
    ]


def test_build_campaign_graph_returns_invokable_langgraph() -> None:
    graph = build_campaign_graph("demo_cached")
    assert callable(graph.invoke)


def test_campaign_run_retains_auditable_scientific_state(tmp_path) -> None:
    run = run_campaign(CampaignConfig(), tmp_path, profile="demo_cached")

    assert {candidate.candidate_id for candidate in run.candidates} == {
        "DP622-S2",
        "ATLAS-V001",
        "ATLAS-V002",
        "ATLAS-V003",
        "ATLAS-R001",
    }
    assert len(run.evidence) >= len(run.candidates) * 7
    assert len(run.model_runs) == 5
    assert len({record.evidence_id for record in run.evidence}) == len(run.evidence)
    assert len({record.run_id for record in run.model_runs}) == len(run.model_runs)
    assert run.ranked
    assert {control.identity for control in run.retrospective_outcomes.controls} == {
        "OP609-S2",
        "OP669-S2",
    }


def test_recommendation_lock_binds_exact_prelock_ledger_snapshot(tmp_path) -> None:
    run = run_campaign(CampaignConfig(), tmp_path / "run", profile="demo_cached")
    lock_index = next(
        index
        for index, event in enumerate(run.events)
        if event.kind is EventKind.RECOMMENDATION_LOCKED
    )
    prefix = ScientificLedger(tmp_path / "prelock.jsonl")
    for event in run.events[:lock_index]:
        prefix.append(event)

    assert run.recommendation_lock.ledger_digest == prefix.digest()


def test_lock_artifacts_are_persisted_before_hidden_reveal(tmp_path) -> None:
    run_dir = tmp_path / "run"
    run = run_campaign(CampaignConfig(), run_dir, profile="demo_cached")

    assert (run_dir / "recommendation-lock.json").is_file()
    assert (run_dir / "decision-trace.json").is_file()
    reveal = next(
        event
        for event in run.events
        if event.kind is EventKind.RETROSPECTIVE_LABELS_REVEALED
    )
    assert reveal.payload["verified_persisted_lock"] is True
