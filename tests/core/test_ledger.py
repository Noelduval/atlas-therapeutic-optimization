import json
from datetime import UTC, datetime, timedelta

import pytest

from atlas.domain.models import ScientificEvent
from atlas.ledger import LedgerIntegrityError, ScientificLedger


def _event(sequence: int, stage: str) -> ScientificEvent:
    return ScientificEvent(
        event_id=f"evt-{sequence:04d}",
        sequence=sequence,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=sequence),
        kind="campaign_validated" if sequence == 1 else "safety_gate_passed",
        stage=stage,
        summary=f"Completed {stage}.",
    )


def test_ledger_appends_hash_chained_canonical_jsonl(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    ledger = ScientificLedger(path)
    first = ledger.append(_event(1, "validate_campaign"))
    second = ledger.append(_event(2, "safety_gate"))

    lines = path.read_text().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["event_hash"] == first.event_hash
    assert second.previous_hash == first.event_hash
    assert ledger.verify() is True
    assert ledger.read_all() == (first, second)


def test_ledger_detects_tampering_before_next_append(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    ledger = ScientificLedger(path)
    ledger.append(_event(1, "validate_campaign"))
    path.write_text(path.read_text().replace("Completed", "Altered"))

    with pytest.raises(LedgerIntegrityError):
        ledger.verify()
    with pytest.raises(LedgerIntegrityError):
        ledger.append(_event(2, "safety_gate"))


def test_ledger_rejects_out_of_order_sequence(tmp_path) -> None:
    ledger = ScientificLedger(tmp_path / "events.jsonl")
    ledger.append(_event(1, "validate_campaign"))
    with pytest.raises(LedgerIntegrityError, match="sequence"):
        ledger.append(_event(3, "load_challenge"))
