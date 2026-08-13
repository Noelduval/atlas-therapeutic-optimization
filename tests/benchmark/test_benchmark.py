from atlas.benchmark import run_benchmark
from atlas.domain.enums import Provenance


def test_benchmark_is_one_vita_family_with_required_supporting_experiments(tmp_path) -> None:
    result = run_benchmark("demo_cached", tmp_path)
    assert result.benchmark_family == "atlas-vita-abeta-metalloprotease"
    names = {experiment.name for experiment in result.experiments}
    assert {
        "atlas_iterative",
        "compute_matched_single_pass",
        "scientific_critic_ablation",
        "sequence_evaluator_ablation",
        "structure_evaluator_ablation",
        "catalytic_geometry_evaluator_ablation",
        "substrate_recognition_evaluator_ablation",
        "selectivity_risk_evaluator_ablation",
        "developability_evaluator_ablation",
        "simulation_sanity_evaluator_ablation",
        "disagreement_fixture",
        "negative_result_fixture",
        "seed_retention_fixture",
    } <= names
    assert all(experiment.provenance is Provenance.SYNTHETIC_DEMO for experiment in result.experiments)


def test_benchmark_records_negative_retrospective_result_without_synthetic_kinetics(tmp_path) -> None:
    result = run_benchmark("demo_cached", tmp_path)
    assert result.flagship_winner == "DP622-S2"
    assert result.retrospective_alignment == "did_not_recover_published_optimized_control"
    assert result.status == "scientifically_complete"
    serialized = result.model_dump_json().lower()
    assert "kcat" not in serialized
    assert '"metric":"km"' not in serialized
    assert "negative result" in serialized


def test_benchmark_is_deterministic(tmp_path) -> None:
    first = run_benchmark("demo_cached", tmp_path / "one")
    second = run_benchmark("demo_cached", tmp_path / "two")
    assert first == second


def test_benchmark_experiments_are_computed_from_campaign_evidence(tmp_path) -> None:
    result = run_benchmark("demo_cached", tmp_path)
    experiments = {experiment.name: experiment for experiment in result.experiments}

    assert experiments["atlas_iterative"].calculation["completed_iterations"] == 2
    assert (
        experiments["compute_matched_single_pass"].calculation[
            "evaluated_candidate_count"
        ]
        == 4
    )
    assert (
        experiments["compute_matched_single_pass"].calculation[
            "executed_deterministic_calibration_evaluations"
        ]
        == 7
    )
    assert len(
        experiments["compute_matched_single_pass"].calculation[
            "calibration_output_digest"
        ]
    ) == 64
    assert experiments["scientific_critic_ablation"].calculation["removed_stage"] == (
        "scientific_critic"
    )
    assert experiments["disagreement_fixture"].calculation["flagged_candidate_count"] > 0
    assert experiments["negative_result_fixture"].calculation["promotable_variant_count"] == 0
