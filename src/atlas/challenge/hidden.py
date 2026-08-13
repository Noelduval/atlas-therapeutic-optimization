"""Post-lock-only published retrospective outcomes from the VITA paper."""

import json
from hashlib import sha256
from pathlib import Path
from typing import Literal

from atlas.domain.enums import Availability, EventKind, Provenance
from atlas.domain.models import AtlasModel, DecisionTrace, RecommendationLock
from atlas.ledger import ScientificLedger, ledger_snapshot_digest


class HiddenControl(AtlasModel):
    identity: str
    provenance: Literal[Provenance.PUBLISHED_MEASURED] = Provenance.PUBLISHED_MEASURED
    exact_sequence: None = None
    sequence_availability: Literal[Availability.UNAVAILABLE] = Availability.UNAVAILABLE
    published_efficiency_m_inverse_s: float
    published_finding: str


class HiddenMutantOutcome(AtlasModel):
    identity: str
    provenance: Literal[Provenance.PUBLISHED_MEASURED] = Provenance.PUBLISHED_MEASURED
    published_finding: str


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

        return HiddenOutcomeBundle(
            revealed_after_lock_id=lock.lock_id,
            seed_control=HiddenControl(
                identity="DP622-S2",
                published_efficiency_m_inverse_s=325.26,
                published_finding=(
                    "Published seed achieved complete substrate degradation within four hours, "
                    "with measured catalytic efficiency used only for post-lock comparison."
                ),
            ),
            controls=(
                HiddenControl(
                    identity="OP609-S2",
                    published_efficiency_m_inverse_s=3045.14,
                    published_finding=(
                        "Published structure-guided variant with higher measured catalytic "
                        "efficiency than the DP622-S2 seed and S2 substrate selectivity."
                    ),
                ),
                HiddenControl(
                    identity="OP669-S2",
                    published_efficiency_m_inverse_s=452.49,
                    published_finding=(
                        "Published second-stage variant with higher measured efficiency than "
                        "the seed and cross-reactivity toward the S3 fusion substrate at S2."
                    ),
                ),
            ),
            mutant_controls=(
                HiddenMutantOutcome(
                    identity="DP622-S2 Y91F",
                    published_finding="Published single mutant with enhanced measured efficiency.",
                ),
                HiddenMutantOutcome(
                    identity="DP622-S2 D126A",
                    published_finding="Published single mutant with enhanced measured efficiency.",
                ),
                HiddenMutantOutcome(
                    identity="DP622-S2 H172A",
                    published_finding="Published mutant with decreased measured efficiency.",
                ),
                HiddenMutantOutcome(
                    identity="DP622-S2 Y91F/D126A",
                    published_finding="Published double mutant with decreased measured efficiency.",
                ),
            ),
            retrospective_disclosure=(
                "Retrospective comparison only; possible biological model training-data "
                "contamination cannot be excluded."
            ),
        )
