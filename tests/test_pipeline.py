from __future__ import annotations

from pathlib import Path
import json

import pandas as pd
import pytest

from atlas.pipeline import OfficialStabilityProvider, PipelineConfig, run_pipeline
from atlas.stability.common import StabilityVariant, normalized_frame, normalized_row
from atlas.validation.validation_gate import ValidationGateError


class FakeStabilityProvider:
    def __init__(self, double_score: float) -> None:
        self.double_score = double_score
        self.candidates_called = False
        self.known_calls = 0

    @staticmethod
    def _rows(values):
        return pd.DataFrame(
            [
                {
                    "variant_id": name,
                    "mutation_set": name,
                    "dp622_numbering": name,
                    "deposited_numbering": name,
                    "model_used": "test boundary",
                    "predicted_ddg_or_score": score,
                    "interpretation": "test fixture; never emitted by real provider",
                    "warnings": "",
                }
                for name, score in values.items()
            ]
        )

    def score_known(self, pdb_path, output_dir):
        self.known_calls += 1
        return self._rows(
            {
                "WT": 0.0,
                "Y91F": -0.2,
                "D126A": 0.2,
                "H172A": 0.1,
                "Y91F_D126A": self.double_score,
            }
        )

    def score_candidates(self, pdb_path, variants, output_dir):
        self.candidates_called = True
        return self._rows({variant.variant_id: -0.1 for variant in variants})


def test_structure_checkpoint_writes_reproducible_run_manifest(tmp_path: Path) -> None:
    result = run_pipeline(
        PipelineConfig(
            input_structure=Path("data/23WN.cif"),
            output_root=tmp_path,
            atlas_repo=Path.cwd(),
            run_id="manifest-checkpoint",
            dynamics_mode="minimize",
            stop_after="structure",
        )
    )

    context = json.loads((result.run_dir / "run_context.json").read_text())
    manifest = json.loads((result.run_dir / "run_manifest.json").read_text())

    assert manifest["run_id"] == "manifest-checkpoint"
    assert manifest["checkpoint_directory"] == str(result.run_dir.resolve())
    assert manifest["atlas_commit"] == context["atlas_commit"]
    assert manifest["input_sha256"] == context["input_sha256"]
    assert manifest["thermompnn_commit"] == context["thermompnn_commit"]
    assert manifest["thermompnn_d_commit"] == context["thermompnn_d_commit"]
    assert manifest["dynamics_mode"] == "minimize"
    assert manifest["validation_policy"] == context["validation_policy"]
    assert manifest["python_executable"]
    assert manifest["packages"]["torch"]
    assert manifest["claim_boundary"] == (
        "computational predictions requiring experimental validation"
    )


def test_failed_gate_hard_stops_before_novel_artifacts(tmp_path: Path) -> None:
    provider = FakeStabilityProvider(double_score=0.5)
    config = PipelineConfig(
        input_structure=Path("data/23WN.cif"),
        output_root=tmp_path,
        run_id="run-fail",
        dynamics_mode="skip",
    )
    with pytest.raises(ValidationGateError):
        run_pipeline(config, stability_provider=provider)
    run_dir = tmp_path / "run-fail"
    assert (run_dir / "known_mutation_validation.csv").is_file()
    assert (run_dir / "run_manifest.json").is_file()
    assert not provider.candidates_called
    assert not (run_dir / "novel_candidates_manifest.csv").exists()
    assert not (run_dir / "novel_candidates_ranked.csv").exists()
    assert not (run_dir / "top_5_candidate_pdbs").exists()
    assert not (run_dir / "figures" / "candidate_ranking_summary.png").exists()


def test_successful_boundary_produces_ranked_computational_candidates(
    tmp_path: Path,
) -> None:
    provider = FakeStabilityProvider(double_score=1.8)
    result = run_pipeline(
        PipelineConfig(
            input_structure=Path("data/23WN.cif"),
            output_root=tmp_path,
            run_id="run-pass",
            dynamics_mode="skip",
        ),
        stability_provider=provider,
    )
    assert result.validation.passed
    assert result.status == "completed"
    assert provider.candidates_called
    assert (result.run_dir / "novel_candidates_manifest.csv").is_file()
    assert (result.run_dir / "novel_candidates_ranked.csv").is_file()
    dynamics = pd.read_csv(result.run_dir / "openmm_dynamics_summary.csv")
    assert len(dynamics) > 5
    assert len(list((result.run_dir / "top_5_candidate_pdbs").glob("*.pdb"))) == 5
    assert (result.run_dir / "figures" / "candidate_ranking_summary.png").is_file()


def test_resume_reuses_completed_stability_and_finishes_later_stage(
    tmp_path: Path,
) -> None:
    provider = FakeStabilityProvider(double_score=1.8)
    stopped = run_pipeline(
        PipelineConfig(
            input_structure=Path("data/23WN.cif"),
            output_root=tmp_path,
            run_id="run-resume",
            dynamics_mode="skip",
            stop_after="thermompnn-d",
        ),
        stability_provider=provider,
    )
    assert stopped.status == "stopped_after_thermompnn-d"
    assert provider.known_calls == 1
    result = run_pipeline(
        PipelineConfig(
            input_structure=Path("data/23WN.cif"),
            output_root=tmp_path,
            run_id="run-resume",
            dynamics_mode="skip",
            resume=True,
        ),
        stability_provider=provider,
    )
    assert result.status == "completed"
    assert provider.known_calls == 1


def test_official_stability_stages_resume_between_single_and_double(
    tmp_path: Path,
) -> None:
    class FakeRunner:
        def __init__(self, model: str, scores: dict[str, float]) -> None:
            self.model = model
            self.scores = scores
            self.calls = 0

        def run(self, pdb_path, variants, output_dir):
            self.calls += 1
            return normalized_frame(
                [
                    normalized_row(variant, self.model, self.scores[variant.variant_id])
                    for variant in variants
                ]
            )

    provider = OfficialStabilityProvider(tmp_path / "single", tmp_path / "double")
    provider.single = FakeRunner(
        "ThermoMPNN", {"Y91F": -0.2, "D126A": 0.2, "H172A": 0.1}
    )
    provider.double = FakeRunner(
        "ThermoMPNN-D epistatic", {"Y91F_D126A": 1.8}
    )
    base = dict(
        input_structure=Path("data/23WN.cif"),
        output_root=tmp_path,
        run_id="official-stages",
        dynamics_mode="skip",
    )
    single = run_pipeline(
        PipelineConfig(**base, stop_after="thermompnn"),
        stability_provider=provider,
    )
    assert single.status == "stopped_after_thermompnn"
    assert provider.single.calls == 1
    assert provider.double.calls == 0

    double = run_pipeline(
        PipelineConfig(**base, resume=True, stop_after="thermompnn-d"),
        stability_provider=provider,
    )
    assert double.status == "stopped_after_thermompnn-d"
    assert provider.single.calls == 1
    assert provider.double.calls == 1
    scores = pd.read_csv(double.run_dir / "thermompnn_scores.csv")
    assert set(scores.variant_id) == {
        "WT", "Y91F", "D126A", "H172A", "Y91F_D126A"
    }


def test_stop_after_validation_records_real_gate_decision(tmp_path: Path) -> None:
    result = run_pipeline(
        PipelineConfig(
            input_structure=Path("data/23WN.cif"),
            output_root=tmp_path,
            run_id="validation-only",
            dynamics_mode="skip",
            stop_after="validation",
        ),
        stability_provider=FakeStabilityProvider(double_score=1.8),
    )
    status = json.loads((result.run_dir / "execution_status.json").read_text())
    assert result.status == "stopped_after_validation"
    assert status["scientific_conclusion"] == "VALIDATED"
    assert status["candidate_generation_decision"] == "allowed"
