"""Controlled vocabularies that keep scientific claims explicit."""

from enum import StrEnum


class Availability(StrEnum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class Provenance(StrEnum):
    PUBLISHED_MEASURED = "published_measured"
    PUBLISHED_STRUCTURAL = "published_structural"
    PREDICTED = "predicted"
    SYNTHETIC_DEMO = "synthetic_demo"
    UNAVAILABLE = "unavailable"


class EvidenceKind(StrEnum):
    SEQUENCE = "sequence"
    STRUCTURE = "structure"
    CATALYTIC_GEOMETRY = "catalytic_geometry"
    CATALYTIC_ACTIVITY = "catalytic_activity"
    SUBSTRATE_RECOGNITION = "substrate_recognition"
    SELECTIVITY_RISK = "selectivity_risk"
    DEVELOPABILITY = "developability"
    SIMULATION_SANITY = "simulation_sanity"
    MODEL_DISAGREEMENT = "model_disagreement"
    PUBLISHED_RETROSPECTIVE = "published_retrospective"


class CampaignStatus(StrEnum):
    INITIALIZED = "initialized"
    RUNNING = "running"
    SCIENTIFICALLY_COMPLETE = "scientifically_complete"
    FAILED = "failed"


class CandidateStatus(StrEnum):
    SEED = "seed"
    PROPOSED = "proposed"
    REJECTED = "rejected"
    RECOMMENDED = "recommended"


class EventKind(StrEnum):
    CAMPAIGN_VALIDATED = "campaign_validated"
    SAFETY_GATE_PASSED = "safety_gate_passed"
    CHALLENGE_LOADED = "challenge_loaded"
    SEED_CHARACTERIZED = "seed_characterized"
    BASELINE_ESTABLISHED = "baseline_established"
    VARIANTS_PROPOSED = "variants_proposed"
    VARIANTS_REFINED = "variants_refined"
    SEQUENCE_EVALUATED = "sequence_evaluated"
    STRUCTURE_EVALUATED = "structure_evaluated"
    CATALYTIC_GEOMETRY_EVALUATED = "catalytic_geometry_evaluated"
    SUBSTRATE_RECOGNITION_EVALUATED = "substrate_recognition_evaluated"
    SELECTIVITY_RISK_EVALUATED = "selectivity_risk_evaluated"
    DEVELOPABILITY_EVALUATED = "developability_evaluated"
    SIMULATION_SANITY_CHECKED = "simulation_sanity_checked"
    MODEL_DISAGREEMENT_DETECTED = "model_disagreement_detected"
    PARETO_RANKED = "pareto_ranked"
    SCIENTIFIC_CRITIC_REVIEWED = "scientific_critic_reviewed"
    ITERATION_TERMINATED = "iteration_terminated"
    RECOMMENDATION_LOCKED = "recommendation_locked"
    RETROSPECTIVE_LABELS_REVEALED = "retrospective_labels_revealed"
    FINAL_REPORT_PRODUCED = "final_report_produced"
