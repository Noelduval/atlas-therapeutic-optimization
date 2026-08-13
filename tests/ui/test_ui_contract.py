from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).parents[2] / "src" / "atlas" / "ui" / "app.py"
NAVIGATION = (
    "Atlas Challenge",
    "Run Monitor",
    "Candidates",
    "Structures",
    "Evidence",
    "Scientific Notebook",
    "Benchmarks",
    "Methods",
)


def _app() -> AppTest:
    return AppTest.from_file(str(APP), default_timeout=10).run()


def _rendered_values(at: AppTest) -> str:
    collections = (
        at.title,
        at.header,
        at.subheader,
        at.markdown,
        at.caption,
        at.info,
        at.warning,
        at.success,
        at.text,
    )
    return "\n".join(
        str(element.value)
        for collection in collections
        for element in collection
        if getattr(element, "value", None) is not None
    )


def test_first_run_screen_has_locked_single_challenge_copy_only() -> None:
    at = _app()
    rendered = _rendered_values(at)
    assert at.title[0].value == "Atlas Challenge"
    assert at.subheader[0].value == "Alzheimer’s Aβ Metalloprotease Optimization"
    assert at.button[0].label == "Load Atlas Challenge"
    assert "DP622-S2" in rendered
    assert "Aβ42" in rendered
    assert "Blinded retrospective benchmark" in rendered
    for forbidden in ("challenge selector", "multiple challenges", "HER2", "trastuzumab", "PHGDH"):
        assert forbidden not in rendered


def test_load_then_start_campaign_transition_completes() -> None:
    at = _app()
    at.button[0].click().run()
    assert at.button[0].label == "Start Campaign"
    at.button[0].click().run(timeout=10)
    rendered = _rendered_values(at)
    assert "scientifically_complete" in rendered
    assert "DP622-S2" in rendered
    assert tuple(at.sidebar.radio[0].options) == NAVIGATION


def test_completed_run_exposes_structure_and_evidence_claim_boundaries() -> None:
    at = _app()
    at.button[0].click().run()
    at.button[0].click().run(timeout=10)

    at.sidebar.radio[0].set_value("Structures").run()
    structures = _rendered_values(at)
    assert "inactive E96Q" in structures
    assert "not catalytic activity" in structures
    assert "23WN" in structures

    at.sidebar.radio[0].set_value("Evidence").run()
    evidence = _rendered_values(at)
    assert "Synthetic demo evidence" in evidence
    assert "not biological model output" in evidence
    assert "kcat" not in evidence
