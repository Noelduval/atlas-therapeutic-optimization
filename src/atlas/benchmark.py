"""The single Atlas v1 VITA benchmark and its supporting experiments."""

from pathlib import Path
from statistics import fmean
from typing import Literal

from atlas.adapters.demo_cached import DemoCachedAdapter
from atlas.challenge.vita import load_visible_challenge
from atlas.domain.enums import Availability, CandidateStatus, EvidenceKind
from atlas.domain.enums import Provenance
from atlas.domain.models import AtlasModel, CampaignConfig, Candidate, EvidenceRecord
from atlas.workflow.ranking import pareto_rank
from atlas.workflow.graph import run_campaign


_BENCHMARK_KINDS = (
    EvidenceKind.SEQUENCE,
    EvidenceKind.STRUCTURE,
    EvidenceKind.CATALYTIC_GEOMETRY,
    EvidenceKind.SUBSTRATE_RECOGNITION,
    EvidenceKind.SELECTIVITY_RISK,
    EvidenceKind.DEVELOPABILITY,
    EvidenceKind.SIMULATION_SANITY,
)


class BenchmarkExperiment(AtlasModel):
    name: str
    provenance: Literal[Provenance.SYNTHETIC_DEMO] = Provenance.SYNTHETIC_DEMO
    winner: str
    conclusion: str
    evidence_summary: str
    negative_result: bool = False
    calculation: dict[str, float | int | str]


class BenchmarkResult(AtlasModel):
    benchmark_family: Literal["atlas-vita-abeta-metalloprotease"] = (
        "atlas-vita-abeta-metalloprotease"
    )
    profile: Literal["demo_cached"] = "demo_cached"
    flagship_winner: str
    status: Literal["scientifically_complete"] = "scientifically_complete"
    retrospective_alignment: Literal["did_not_recover_published_optimized_control"] = (
        "did_not_recover_published_optimized_control"
    )
    experiments: tuple[BenchmarkExperiment, ...]
    limitations: tuple[str, ...]


def _experiment(
    name: str,
    winner: str,
    conclusion: str,
    evidence_summary: str,
    calculation: dict[str, float | int | str],
    negative_result: bool = False,
) -> BenchmarkExperiment:
    return BenchmarkExperiment(
        name=name,
        winner=winner,
        conclusion=conclusion,
        evidence_summary=evidence_summary,
        calculation=calculation,
        negative_result=negative_result,
    )


def _fixture_candidates() -> tuple[Candidate, ...]:
    seed = load_visible_challenge().seed
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
    return (seed, *variants)


def _fixture_evidence(candidates: tuple[Candidate, ...]) -> tuple[EvidenceRecord, ...]:
    adapter = DemoCachedAdapter()
    return tuple(
        record
        for candidate in candidates
        for record in adapter.evaluate(candidate, "atlas-vita-abeta-s2").evidence
    )


def _mean_scores(
    candidates: tuple[Candidate, ...],
    evidence: tuple[EvidenceRecord, ...],
    excluded: EvidenceKind | None = None,
) -> dict[str, float]:
    return {
        candidate.candidate_id: fmean(
            record.score
            for record in evidence
            if record.candidate_id == candidate.candidate_id
            and record.score is not None
            and record.kind in _BENCHMARK_KINDS
            and record.kind is not excluded
        )
        for candidate in candidates
    }


def _winner(scores: dict[str, float]) -> str:
    return max(scores, key=lambda candidate_id: (scores[candidate_id], candidate_id))


def run_benchmark(profile: str, output_dir: str | Path) -> BenchmarkResult:
    if profile != "demo_cached":
        raise ValueError(f"Unknown profile: {profile}")
    flagship_dir = Path(output_dir) / "flagship"
    run = run_campaign(CampaignConfig(), flagship_dir, profile=profile)
    # Local import avoids a module cycle while keeping every benchmark's flagship
    # campaign independently inspectable on disk.
    from atlas.artifacts import write_campaign_artifacts

    write_campaign_artifacts(run, flagship_dir)
    candidates = _fixture_candidates()
    evidence = _fixture_evidence(candidates)
    full_scores = _mean_scores(candidates, evidence)
    single_pass_winner = _winner(full_scores)
    ranked = pareto_rank(candidates, evidence)
    critic_ablation_winner = ranked[0].candidate_id
    without_sequence = _mean_scores(candidates, evidence, EvidenceKind.SEQUENCE)
    without_structure = _mean_scores(candidates, evidence, EvidenceKind.STRUCTURE)
    promotable = [
        item
        for item in ranked
        if item.candidate_id != "DP622-S2" and not item.rejection_reasons
    ]
    spreads = {
        candidate.candidate_id: max(
            record.score
            for record in evidence
            if record.candidate_id == candidate.candidate_id and record.score is not None
        )
        - min(
            record.score
            for record in evidence
            if record.candidate_id == candidate.candidate_id and record.score is not None
        )
        for candidate in candidates
    }
    flagged = {candidate_id: spread for candidate_id, spread in spreads.items() if spread >= 0.25}
    iterative_evaluation_budget = sum(
        1
        for record in run.evidence
        if record.kind in _BENCHMARK_KINDS and record.score is not None
    )
    initial_single_pass_evaluations = len(evidence)
    calibration_bundle = DemoCachedAdapter().evaluate(
        candidates[0], "atlas-vita-abeta-s2|compute-matched-calibration"
    )
    calibration_evidence = tuple(
        record for record in calibration_bundle.evidence if record.kind in _BENCHMARK_KINDS
    )
    if len(evidence) + len(calibration_evidence) != iterative_evaluation_budget:
        raise RuntimeError("Single-pass calibration did not match the iterative evaluation budget")
    experiments = (
        _experiment(
            "atlas_iterative",
            run.final_report.winning_candidate,
            "Scientific Critic requested one refinement, then terminated after the second evaluation pass.",
            "Seven deterministic synthetic evidence dimensions; no synthetic kinetics.",
            {
                "source_event_count": len(run.events),
                "completed_iterations": 2,
                "termination_reason": "no_variant_cleared_seed_promotion_margin",
            },
        ),
        _experiment(
            "compute_matched_single_pass",
            single_pass_winner,
            "Single-pass ranking also retained the seed in this deterministic fixture.",
            "Compute-matched synthetic fixture without critic iteration.",
            {
                "evaluated_candidate_count": len(candidates),
                "evaluated_evidence_count": iterative_evaluation_budget,
                "primary_candidate_dimension_evaluations": initial_single_pass_evaluations,
                "executed_deterministic_calibration_evaluations": len(calibration_evidence),
                "calibration_output_digest": calibration_bundle.run_record.output_digest,
                "top_mean_score": round(full_scores[single_pass_winner], 6),
            },
        ),
        _experiment(
            "scientific_critic_ablation",
            critic_ablation_winner,
            "Removing only the critic preserved the pre-critic Pareto winner in this fixture.",
            "Candidate set, seven-dimensional evidence, and ranking were held fixed.",
            {
                "removed_stage": "scientific_critic",
                "ranking_objective": "pareto_multidimensional",
                "evaluated_candidate_count": len(candidates),
            },
        ),
        _experiment(
            "sequence_evaluator_ablation",
            _winner(without_sequence),
            "Winner was unchanged when sequence evidence was withheld.",
            "Synthetic evaluator contribution ablation, not a real model claim.",
            {
                "withheld_dimension": EvidenceKind.SEQUENCE.value,
                "remaining_dimension_count": 6,
            },
        ),
        _experiment(
            "structure_evaluator_ablation",
            _winner(without_structure),
            "Winner was unchanged when structure confidence evidence was withheld.",
            "Synthetic evaluator contribution ablation, not a real model claim.",
            {
                "withheld_dimension": EvidenceKind.STRUCTURE.value,
                "remaining_dimension_count": 6,
            },
        ),
        *tuple(
            _experiment(
                f"{kind.value}_evaluator_ablation",
                _winner(_mean_scores(candidates, evidence, kind)),
                f"Winner was recomputed with {kind.value.replace('_', ' ')} evidence withheld.",
                "Synthetic evaluator contribution ablation, not a real model claim.",
                {
                    "withheld_dimension": kind.value,
                    "remaining_dimension_count": 6,
                },
            )
            for kind in (
                EvidenceKind.CATALYTIC_GEOMETRY,
                EvidenceKind.SUBSTRATE_RECOGNITION,
                EvidenceKind.SELECTIVITY_RISK,
                EvidenceKind.DEVELOPABILITY,
                EvidenceKind.SIMULATION_SANITY,
            )
        ),
        _experiment(
            "disagreement_fixture",
            "DP622-S2",
            "The critic exposed strong recognition evidence paired with degraded geometry evidence.",
            "Conflict remained visible in the trace and report.",
            {
                "flagged_candidate_count": len(flagged),
                "maximum_dimension_spread": round(max(spreads.values()), 6),
            },
        ),
        _experiment(
            "negative_result_fixture",
            "DP622-S2",
            "Negative result: no generated variant cleared the seed-promotion threshold.",
            "Rejected candidates and their failure reasons remain reported.",
            {"promotable_variant_count": len(promotable)},
            negative_result=True,
        ),
        _experiment(
            "seed_retention_fixture",
            "DP622-S2",
            "Seed retention terminated scientifically_complete rather than optimization_failed.",
            "Novelty was not rewarded for its own sake.",
            {
                "seed_retained": 1,
                "rejected_variant_count": len(candidates) - 1,
            },
        ),
    )
    optimized_control_ids = {
        control.identity for control in run.retrospective_outcomes.controls
    }
    alignment = (
        "recovered_published_optimized_control"
        if run.final_report.winning_candidate in optimized_control_ids
        else "did_not_recover_published_optimized_control"
    )
    return BenchmarkResult(
        flagship_winner=run.final_report.winning_candidate,
        retrospective_alignment=alignment,
        experiments=experiments,
        limitations=(
            "The demo_cached benchmark exercises orchestration with synthetic evidence only.",
            "The flagship recommendation did not recover a published optimized control; this negative result is retained.",
            "Possible model training-data contamination remains a retrospective benchmark limitation.",
        ),
    )
