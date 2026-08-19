from __future__ import annotations

from pathlib import Path

import pytest

from atlas.pipeline import PipelineConfig
from atlas.run_context import RunContext, RunContextError, prepare_run_directory


def _context(input_sha: str = "1" * 64) -> RunContext:
    return RunContext(
        schema_version=1,
        atlas_commit="a" * 40,
        input_sha256=input_sha,
        thermompnn_commit="2b04fd370e399911b1fa5848112cc9013f084110",
        thermompnn_d_commit="df9a75aaddb674a7c4c193005031fc0536d325fb",
        dynamics_mode="minimize",
        validation_policy="atlas-v1-fixed-gate-2026-08-19",
    )


def test_identical_context_can_resume_existing_run(tmp_path: Path) -> None:
    initial = PipelineConfig(output_root=tmp_path, run_id="colab-run")
    run_dir = prepare_run_directory(initial, _context())
    resumed = prepare_run_directory(
        PipelineConfig(output_root=tmp_path, run_id="colab-run", resume=True),
        _context(),
    )
    assert resumed == run_dir
    assert (run_dir / "run_context.json").is_file()


def test_resume_rejects_stale_input_or_commit_context(tmp_path: Path) -> None:
    prepare_run_directory(
        PipelineConfig(output_root=tmp_path, run_id="colab-run"), _context()
    )
    with pytest.raises(RunContextError, match="input_sha256"):
        prepare_run_directory(
            PipelineConfig(output_root=tmp_path, run_id="colab-run", resume=True),
            _context("2" * 64),
        )


def test_resume_requires_explicit_run_id(tmp_path: Path) -> None:
    with pytest.raises(RunContextError, match="run_id"):
        prepare_run_directory(
            PipelineConfig(output_root=tmp_path, resume=True), _context()
        )
