"""Post-lock-only published retrospective outcomes from the VITA paper."""

import json
from hashlib import sha256
from pathlib import Path
from typing import Literal

from atlas.domain.enums import Availability, EventKind, Provenance
from atlas.domain.models import AtlasModel, DecisionTrace, RecommendationLock
from atlas.ledger import ScientificLedger, ledger_snapshot_digest
from atlas.challenge.assets import load_hidden_label_asset


class HiddenControl(AtlasModel):
    identity: str
    provenance: Literal[Provenance.PUBLISHED_MEASURED] = Provenance.PUBLISHED_MEASURED
    exact_sequence: None = None
    sequence_availability: Literal[Availability.UNAVAILABLE] = Availability.UNAVAILABLE
    published_kcat_s_inverse: float
    published_km_micromolar: float
    published_efficiency_m_inverse_s: float
    published_finding: str
    published_cleavage_findings: tuple[str, ...]
    published_selectivity_findings: tuple[str, ...]
    source_location: str


class HiddenMutantOutcome(AtlasModel):
    identity: str
    provenance: Literal[Provenance.PUBLISHED_MEASURED] = Provenance.PUBLISHED_MEASURED
    published_finding: str
    source_location: str


class HiddenOutcomeBundle(AtlasModel):
    revealed_after_lock_id: str
    seed_control: HiddenControl
    controls: tuple[HiddenControl, ...]
    mutant_controls: tuple[HiddenMutantOutcome, ...]
    retrospective_disclosure: str


class HiddenLabelRepository:
    """A repository intentionally omitted from campaign construction and adapter inputs."""

    def reveal(
        self,
        lock: RecommendationLock | None,
        persisted_lock_path: str | Path | None,
    ) -> HiddenOutcomeBundle:
        if lock is None or not lock.locked:
            raise ValueError("A persisted recommendation lock is required before reveal")
        if persisted_lock_path is None:
            raise ValueError("A persisted recommendation lock path is required before reveal")
        lock_path = Path(persisted_lock_path)
        if not lock_path.is_file():
            raise ValueError("The persisted recommendation lock could not be verified")
        try:
            persisted = RecommendationLock.model_validate(
                json.loads(lock_path.read_text(encoding="utf-8"))
            )
        except Exception as exc:
            raise ValueError("The persisted recommendation lock is invalid") from exc
        if persisted != lock:
            raise ValueError("The persisted recommendation lock does not match campaign state")

        trace_path = lock_path.parent / "decision-trace.json"
        try:
            trace = DecisionTrace.model_validate(
                json.loads(trace_path.read_text(encoding="utf-8"))
            )
        except Exception as exc:
            raise ValueError("The persisted Decision Trace is invalid") from exc
        trace_digest = sha256(
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
            ).encode("utf-8")
        ).hexdigest()
        if trace.digest != trace_digest or trace.digest != lock.decision_trace_digest:
            raise ValueError("The persisted Decision Trace does not match the lock")

        ledger = ScientificLedger(lock_path.parent / "events.jsonl")
        try:
            events = ledger.read_all()
            ledger.verify()
        except Exception as exc:
            raise ValueError("The persisted pre-reveal ledger could not be verified") from exc
        if not events or events[-1].kind is not EventKind.RECOMMENDATION_LOCKED:
            raise ValueError("The persisted ledger does not end at recommendation lock")
        if ledger_snapshot_digest(events[:-1]) != lock.ledger_digest:
            raise ValueError("The persisted pre-lock ledger digest does not match the lock")
        expected_trace_decision = {lock.candidate_id: "recommended"}
        if (
            trace.campaign_id != lock.campaign_id
            or trace.event_ids != tuple(event.event_id for event in events[:-1])
            or trace.stages != tuple(event.stage for event in events[:-1])
            or trace.generated_at != events[-2].timestamp
            or trace.candidate_decisions != expected_trace_decision
        ):
            raise ValueError("The persisted Decision Trace contradicts the verified ledger or lock")
        lock_payload = events[-1].payload
        if (
            lock_payload.get("candidate_decision") != {lock.candidate_id: "recommended"}
            or lock_payload.get("lock_id") != lock.lock_id
            or lock_payload.get("decision_trace_digest") != lock.decision_trace_digest
            or lock_payload.get("prelock_ledger_digest") != lock.ledger_digest
        ):
            raise ValueError("The persisted recommendation event does not match the lock")

        hidden = load_hidden_label_asset()

        def control_from(record: dict) -> HiddenControl:
            return HiddenControl(
                identity=record["identity"],
                published_kcat_s_inverse=record["kcat_s_inverse"],
                published_km_micromolar=record["km_micromolar"],
                published_efficiency_m_inverse_s=record[
                    "catalytic_efficiency_m_inverse_s"
                ],
                published_finding=" ".join(
                    (*record["cleavage_findings"], *record["selectivity_findings"])
                ),
                published_cleavage_findings=tuple(record["cleavage_findings"]),
                published_selectivity_findings=tuple(record["selectivity_findings"]),
                source_location=record["source_location"],
            )

        return HiddenOutcomeBundle(
            revealed_after_lock_id=lock.lock_id,
            seed_control=control_from(hidden["seed_control"]),
            controls=tuple(control_from(record) for record in hidden["controls"]),
            mutant_controls=tuple(
                HiddenMutantOutcome(
                    identity=record["identity"],
                    published_finding=record["finding"],
                    source_location=record["source_location"],
                )
                for record in hidden["mutant_controls"]
            ),
            retrospective_disclosure=hidden["retrospective_disclosure"],
        )
