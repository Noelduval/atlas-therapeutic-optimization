import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import pytest

from atlas.challenge.hidden import HiddenLabelRepository
from atlas.challenge.assets import file_sha256, load_asset_manifest, load_sequence_assets
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


def test_active_candidate_sequences_remain_unavailable_but_supplement_was_recovered() -> None:
    dataset = load_visible_challenge()
    assert dataset.seed.sequence is None
    assert dataset.seed.sequence_availability is Availability.UNAVAILABLE
    assert dataset.supplementary_assets is Availability.AVAILABLE


def test_recovered_structure_assets_match_manifest_checksums() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = load_asset_manifest()
    expected = {
        "pdb_23wn": root / "references/structures/23WN.cif",
        "emdb_69322_metadata": root / "references/structures/EMD-69322_metadata.json",
        "vita_supplementary": root / "references/vita_abeta_metalloprotease_supplementary.pdf",
    }
    for asset_id, path in expected.items():
        assert path.is_file()
        assert manifest["assets"][asset_id]["availability"] == "AVAILABLE"
        assert manifest["assets"][asset_id]["retrieved_on"] == "2026-08-13"
        assert manifest["assets"][asset_id]["sha256"] == file_sha256(path)


def test_sequence_registry_never_substitutes_inactive_e96q_for_active_seed() -> None:
    records = {record["candidate_name"]: record for record in load_sequence_assets()}
    active = records["DP622-S2"]
    inactive = records["DP622 E96Q deposited construct"]

    assert active["availability"] == "UNAVAILABLE"
    assert active["sequence"] is None
    assert active["checksum"] is None
    assert inactive["availability"] == "AVAILABLE"
    assert inactive["active_seed"] is False
    assert inactive["active_site_variant"] == "E96Q"
    assert inactive["chain_source_mapping"]["pdb_id"] == "23WN"
    assert inactive["chain_source_mapping"]["auth_chain_id"] == "A"
    assert inactive["chain_source_mapping"]["entity_id"] == 1
    assert inactive["chain_source_mapping"]["observed_label_seq_range"] == "15-239"
    assert len(inactive["sequence"]) == 1513
    assert inactive["checksum"] == f"sha256:{sha256(inactive['sequence'].encode()).hexdigest()}"


def test_optimized_enzyme_sequences_remain_unavailable_after_official_search() -> None:
    records = {record["candidate_name"]: record for record in load_sequence_assets()}
    for name in ("OP609-S2", "OP669-S2"):
        assert records[name]["availability"] == "UNAVAILABLE"
        assert records[name]["sequence"] is None
        assert records[name]["checksum"] is None


def test_visible_manifest_does_not_contain_hidden_outcomes_or_control_identities() -> None:
    serialized = load_visible_challenge().model_dump_json()
    for forbidden in (
        "OP609",
        "OP669",
        "325.26",
        "3045.14",
        "452.49",
        "0.02395",
        "kcat",
        "retrospective_rank",
    ):
        assert forbidden not in serialized


def test_hidden_asset_is_not_loaded_until_lock_validation_completes(monkeypatch) -> None:
    def fail_if_loaded():
        raise AssertionError("hidden asset was loaded before lock validation")

    monkeypatch.setattr("atlas.challenge.hidden.load_hidden_label_asset", fail_if_loaded)
    with pytest.raises(ValueError, match="recommendation lock"):
        HiddenLabelRepository().reveal(None, None)


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


def test_source_backed_kinetics_are_revealed_only_after_persisted_lock(tmp_path) -> None:
    run_dir = tmp_path / "run"
    run = run_campaign(CampaignConfig(), run_dir, profile="demo_cached")
    revealed = run.retrospective_outcomes
    controls = {control.identity: control for control in revealed.controls}

    assert revealed.seed_control.published_kcat_s_inverse == 0.00191
    assert revealed.seed_control.published_km_micromolar == 5.87
    assert revealed.seed_control.published_efficiency_m_inverse_s == 325.26
    assert controls["OP609-S2"].published_kcat_s_inverse == 0.02395
    assert controls["OP609-S2"].published_km_micromolar == 7.86
    assert controls["OP609-S2"].published_efficiency_m_inverse_s == 3045.14
    assert controls["OP669-S2"].published_kcat_s_inverse == 0.00172
    assert controls["OP669-S2"].published_km_micromolar == 3.80
    assert controls["OP669-S2"].published_efficiency_m_inverse_s == 452.49
