import json
from datetime import UTC, datetime
from hashlib import sha256

import pytest

from atlas.challenge.hidden import HiddenLabelRepository
from atlas.challenge.vita import load_visible_challenge
from atlas.domain.enums import Availability, EventKind
from atlas.domain.models import CampaignConfig, RecommendationLock
from atlas.ledger import ScientificLedger
from atlas.workflow.graph import run_campaign


def _lock() -> RecommendationLock:
    return RecommendationLock(
        lock_id="lock-0001",
        campaign_id="atlas-vita-abeta-s2",
        candidate_id="DP622-S2",
        locked_at=datetime(2026, 8, 13, tzinfo=UTC),
        decision_trace_digest="a" * 64,
        ledger_digest="b" * 64,
        rationale="Seed retained before retrospective reveal.",
    )


def test_visible_challenge_contains_only_canonical_prelock_facts() -> None:
    dataset = load_visible_challenge()
    assert dataset.config.seed == "DP622-S2"
    assert dataset.abeta42_sequence == "DAEFRHDSGYEVHHQKLVFFAEDVGSNKGAIIGLMVGGVVIA"
    assert dataset.s2_context == "GLMVGG|VVIA"
    assert dataset.catalytic_residues == ("Y91", "E96", "D126", "H172")
    assert dataset.structural_reference.pdb_id == "23WN"
    assert dataset.structural_reference.emdb_id == "EMD-69322"
    assert dataset.structural_reference.active_site_variant == "E96Q"
    assert dataset.structural_reference.is_active_enzyme is False


def test_exact_candidate_sequences_and_supplementary_assets_are_unavailable() -> None:
    dataset = load_visible_challenge()
    assert dataset.seed.sequence is None
    assert dataset.seed.sequence_availability is Availability.UNAVAILABLE
    assert dataset.supplementary_assets is Availability.UNAVAILABLE


def test_visible_manifest_does_not_contain_hidden_outcomes_or_control_identities() -> None:
    serialized = load_visible_challenge().model_dump_json()
    for forbidden in ("OP609", "OP669", "325.26", "3045.14", "kcat", "retrospective_rank"):
        assert forbidden not in serialized


def test_hidden_labels_require_a_persisted_recommendation_lock(tmp_path) -> None:
    repository = HiddenLabelRepository()
    with pytest.raises(ValueError, match="recommendation lock"):
        repository.reveal(None, None)

    with pytest.raises(ValueError, match="persisted"):
        repository.reveal(_lock(), tmp_path / "missing-lock.json")


def test_hidden_reveal_rejects_tampered_trace_and_candidate_lock(tmp_path) -> None:
    run_dir = tmp_path / "run"
    run = run_campaign(CampaignConfig(), run_dir, profile="demo_cached")
    repository = HiddenLabelRepository()
    trace_path = run_dir / "decision-trace.json"
    original_trace = trace_path.read_text()
    trace_path.write_text("{}")
    with pytest.raises(ValueError, match="Decision Trace"):
        repository.reveal(run.recommendation_lock, run_dir / "recommendation-lock.json")

    trace_path.write_text(original_trace)
    false_lock = run.recommendation_lock.model_copy(update={"candidate_id": "ATLAS-V001"})
    (run_dir / "recommendation-lock.json").write_text(
        false_lock.model_dump_json(indent=2) + "\n"
    )
    with pytest.raises(ValueError, match="ledger|recommendation event"):
        repository.reveal(false_lock, run_dir / "recommendation-lock.json")


def test_hidden_reveal_rejects_self_consistent_trace_that_contradicts_lock(tmp_path) -> None:
    source = run_campaign(CampaignConfig(), tmp_path / "source", profile="demo_cached")
    forged_dir = tmp_path / "forged"
    forged_dir.mkdir()
    lock_index = next(
        index
        for index, event in enumerate(source.events)
        if event.kind is EventKind.RECOMMENDATION_LOCKED
    )
    trace = source.decision_trace.model_copy(
        update={"candidate_decisions": {"ATLAS-V001": "recommended"}}
    )
    digest = sha256(
        json.dumps(
            {
                "campaign_id": trace.campaign_id,
                "event_ids": list(trace.event_ids),
                "stages": list(trace.stages),
                "candidate_decisions": trace.candidate_decisions,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()
    trace = trace.model_copy(update={"digest": digest})
    lock = source.recommendation_lock.model_copy(update={"decision_trace_digest": digest})
    ledger = ScientificLedger(forged_dir / "events.jsonl")
    for event in source.events[:lock_index]:
        ledger.append(event)
    lock_event = source.events[lock_index].model_copy(
        update={
            "previous_hash": None,
            "event_hash": None,
            "payload": {
                **source.events[lock_index].payload,
                "decision_trace_digest": digest,
            },
        }
    )
    ledger.append(lock_event)
    (forged_dir / "decision-trace.json").write_text(
        json.dumps(trace.model_dump(mode="json"), sort_keys=True, indent=2) + "\n"
    )
    (forged_dir / "recommendation-lock.json").write_text(
        json.dumps(lock.model_dump(mode="json"), sort_keys=True, indent=2) + "\n"
    )

    with pytest.raises(ValueError, match="Decision Trace contradicts"):
        HiddenLabelRepository().reveal(lock, forged_dir / "recommendation-lock.json")
