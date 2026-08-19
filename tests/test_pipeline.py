from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from atlas.pipeline import PipelineConfig, run_pipeline
from atlas.validation.validation_gate import ValidationGateError


class FakeStabilityProvider:
    def __init__(self, double_score: float) -> None:
        self.double_score = double_score
        self.candidates_called = False

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
