import json

from typer.testing import CliRunner

from atlas.cli import app


runner = CliRunner()


def test_challenge_command_writes_complete_reproducible_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    first = runner.invoke(app, ["challenge", "run", "--profile", "demo_cached"])
    second = runner.invoke(app, ["challenge", "run", "--profile", "demo_cached"])
    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output

    directories = sorted((tmp_path / "runs").glob("challenge-demo_cached*"))
    assert len(directories) == 2
    required = {
        "candidates.json",
        "evidence.json",
        "events.jsonl",
        "decision-trace.json",
        "model-runs.json",
        "rankings.json",
        "retrospective-outcomes.json",
        "scientific-notebook.md",
        "recommendation-lock.json",
        "final-report.json",
        "final-report.md",
    }
    assert required <= {path.name for path in directories[0].iterdir()}
    for filename in required:
        assert (directories[0] / filename).read_bytes() == (directories[1] / filename).read_bytes()

    events = [json.loads(line) for line in (directories[0] / "events.jsonl").read_text().splitlines()]
    kinds = [event["kind"] for event in events]
    assert kinds.index("recommendation_locked") < kinds.index("retrospective_labels_revealed")


def test_benchmark_command_writes_single_family_result(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["benchmark", "run", "--profile", "demo_cached"])
    assert result.exit_code == 0, result.output
    directory = next((tmp_path / "runs").glob("benchmark-demo_cached*"))
    payload = json.loads((directory / "benchmark-result.json").read_text())
    assert payload["benchmark_family"] == "atlas-vita-abeta-metalloprotease"
    assert payload["flagship_winner"] == "DP622-S2"
    assert (directory / "benchmark-report.md").exists()
    flagship = directory / "flagship"
    required_flagship = {
        "candidates.json",
        "evidence.json",
        "events.jsonl",
        "decision-trace.json",
        "model-runs.json",
        "rankings.json",
        "retrospective-outcomes.json",
        "scientific-notebook.md",
        "recommendation-lock.json",
        "final-report.json",
        "final-report.md",
    }
    assert required_flagship <= {path.name for path in flagship.iterdir()}
    events = [json.loads(line) for line in (flagship / "events.jsonl").read_text().splitlines()]
    kinds = [event["kind"] for event in events]
    assert kinds.index("recommendation_locked") < kinds.index(
        "retrospective_labels_revealed"
    )


def test_unknown_profile_fails_cleanly() -> None:
    result = runner.invoke(app, ["challenge", "run", "--profile", "unknown"])
    assert result.exit_code != 0
    assert "Unknown profile" in result.output
