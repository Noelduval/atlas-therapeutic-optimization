"""Stable on-disk artifacts for challenge and benchmark runs."""

import json
from pathlib import Path

from atlas.benchmark import BenchmarkResult
from atlas.rendering import render_scientific_notebook
from atlas.reporting import render_final_report
from atlas.workflow.graph import CampaignRun


def _write_json(path: Path, value: object) -> None:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    elif isinstance(value, (tuple, list)):
        value = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in value
        ]
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _verify_or_write_json(path: Path, value: object) -> None:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    serialized = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != serialized:
            raise RuntimeError(f"Refusing to replace immutable artifact: {path}")
        return
    path.write_text(serialized, encoding="utf-8")


def next_run_dir(root: Path, stem: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    candidate = root / stem
    index = 2
    while candidate.exists():
        candidate = root / f"{stem}-{index:03d}"
        index += 1
    candidate.mkdir(parents=True)
    return candidate


def write_campaign_artifacts(run: CampaignRun, run_dir: Path) -> None:
    _verify_or_write_json(run_dir / "decision-trace.json", run.decision_trace)
    _verify_or_write_json(run_dir / "recommendation-lock.json", run.recommendation_lock)
    _write_json(run_dir / "final-report.json", run.final_report)
    _write_json(run_dir / "candidates.json", run.candidates)
    _write_json(run_dir / "evidence.json", run.evidence)
    _write_json(run_dir / "model-runs.json", run.model_runs)
    _write_json(run_dir / "rankings.json", run.ranked)
    _write_json(run_dir / "retrospective-outcomes.json", run.retrospective_outcomes)
    (run_dir / "scientific-notebook.md").write_text(
        render_scientific_notebook(run.events), encoding="utf-8"
    )
    (run_dir / "final-report.md").write_text(
        render_final_report(run.final_report), encoding="utf-8"
    )


def render_benchmark_report(result: BenchmarkResult) -> str:
    lines = [
        "# Atlas Benchmark Report",
        "",
        f"- Benchmark family: `{result.benchmark_family}`",
        f"- Profile: `{result.profile}`",
        f"- Flagship winner: `{result.flagship_winner}`",
        f"- Status: `{result.status}`",
        f"- Retrospective alignment: `{result.retrospective_alignment}`",
        "",
        "## Supporting Experiments",
        "",
    ]
    for experiment in result.experiments:
        lines.extend(
            [
                f"### {experiment.name}",
                "",
                f"- Winner: `{experiment.winner}`",
                f"- Provenance: `{experiment.provenance.value}`",
                f"- Conclusion: {experiment.conclusion}",
                f"- Evidence: {experiment.evidence_summary}",
                f"- Negative result: `{str(experiment.negative_result).lower()}`",
                f"- Calculation: `{json.dumps(experiment.calculation, sort_keys=True)}`",
                "",
            ]
        )
    lines.extend(["## Limitations", "", *[f"- {item}" for item in result.limitations], ""])
    return "\n".join(lines).rstrip() + "\n"


def write_benchmark_artifacts(result: BenchmarkResult, run_dir: Path) -> None:
    _write_json(run_dir / "benchmark-result.json", result)
    (run_dir / "benchmark-report.md").write_text(
        render_benchmark_report(result), encoding="utf-8"
    )
