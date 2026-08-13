"""Append-only, hash-chained scientific event storage."""

import json
from hashlib import sha256
from pathlib import Path

from atlas.domain.models import ScientificEvent


class LedgerIntegrityError(RuntimeError):
    """Raised when event order or the ledger hash chain is invalid."""


def _canonical_event_bytes(event: ScientificEvent) -> bytes:
    payload = event.model_dump(mode="json", exclude={"event_hash"})
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _event_hash(event: ScientificEvent) -> str:
    return sha256(_canonical_event_bytes(event)).hexdigest()


def linked_events(events: tuple[ScientificEvent, ...]) -> tuple[ScientificEvent, ...]:
    """Return the canonical hash chain that would be persisted for ``events``."""
    linked: list[ScientificEvent] = []
    previous_hash: str | None = None
    for expected_sequence, event in enumerate(events, 1):
        if event.sequence != expected_sequence:
            raise LedgerIntegrityError(
                f"Invalid event sequence: expected {expected_sequence}, got {event.sequence}"
            )
        item = event.model_copy(
            update={"previous_hash": previous_hash, "event_hash": None}
        )
        item = item.model_copy(update={"event_hash": _event_hash(item)})
        linked.append(item)
        previous_hash = item.event_hash
    return tuple(linked)


def ledger_snapshot_digest(events: tuple[ScientificEvent, ...]) -> str:
    """Digest the exact canonical JSONL bytes for an in-memory ledger snapshot."""
    serialized = "".join(
        json.dumps(
            event.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        + "\n"
        for event in linked_events(events)
    )
    return sha256(serialized.encode("utf-8")).hexdigest()


class ScientificLedger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def read_all(self) -> tuple[ScientificEvent, ...]:
        if not self.path.exists():
            return ()
        events: list[ScientificEvent] = []
        for line_number, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                raise LedgerIntegrityError(f"Blank ledger line at {line_number}")
            try:
                events.append(ScientificEvent.model_validate_json(line))
            except Exception as exc:
                raise LedgerIntegrityError(f"Invalid event JSON at line {line_number}") from exc
        return tuple(events)

    def verify(self) -> bool:
        previous_hash: str | None = None
        for expected_sequence, event in enumerate(self.read_all(), 1):
            if event.sequence != expected_sequence:
                raise LedgerIntegrityError(
                    f"Invalid event sequence: expected {expected_sequence}, got {event.sequence}"
                )
            if event.previous_hash != previous_hash:
                raise LedgerIntegrityError(f"Broken previous hash at sequence {event.sequence}")
            calculated = _event_hash(event)
            if event.event_hash != calculated:
                raise LedgerIntegrityError(f"Hash mismatch at sequence {event.sequence}")
            previous_hash = event.event_hash
        return True

    def append(self, event: ScientificEvent) -> ScientificEvent:
        self.verify()
        current = self.read_all()
        expected_sequence = len(current) + 1
        if event.sequence != expected_sequence:
            raise LedgerIntegrityError(
                f"Invalid event sequence: expected {expected_sequence}, got {event.sequence}"
            )
        previous_hash = current[-1].event_hash if current else None
        linked = event.model_copy(
            update={"previous_hash": previous_hash, "event_hash": None}
        )
        linked = linked.model_copy(update={"event_hash": _event_hash(linked)})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(
            linked.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        with self.path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(serialized + "\n")
        return linked

    def digest(self) -> str:
        self.verify()
        return sha256(self.path.read_bytes() if self.path.exists() else b"").hexdigest()
