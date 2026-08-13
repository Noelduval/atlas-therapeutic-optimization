"""Regression tests for the locked Atlas v1 scientific and product scope."""

from pathlib import Path

from atlas.challenge.vita import load_visible_challenge
from atlas.profiles import PROFILES


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_DOCS = (
    "README.md",
    "docs/atlas-challenge.md",
    "docs/research-questions.md",
    "docs/SCIENTIFIC_DECISIONS.md",
    "docs/limitations.md",
    "docs/reproducibility.md",
)


def test_v1_has_exactly_one_canonical_challenge_and_profile() -> None:
    challenge = load_visible_challenge()

    assert challenge.config.seed == "DP622-S2"
    assert challenge.config.target_context == "Aβ42"
    assert challenge.config.cleavage_system == "S2"
    assert tuple(PROFILES) == ("demo_cached",)


def test_rejected_scope_is_absent_from_executable_source() -> None:
    source = "\n".join(path.read_text() for path in (ROOT / "src").rglob("*.py"))
    lowered = source.lower()

    assert "her2" not in lowered
    assert "trastuzumab" not in lowered
    assert "phgdh" not in lowered


def test_locked_documentation_set_exists_and_names_future_scope() -> None:
    for relative_path in REQUIRED_DOCS:
        assert (ROOT / relative_path).is_file(), relative_path

    decisions = (ROOT / "docs/SCIENTIFIC_DECISIONS.md").read_text()
    assert "SD-011" in decisions
    assert "HER2/trastuzumab" in decisions
    assert "PHGDH" in decisions
    assert "future mechanism/modality case study only" in decisions


def test_readme_documents_the_supported_demo_commands() -> None:
    readme = (ROOT / "README.md").read_text()

    assert "Atlas Challenge: Alzheimer’s Aβ Metalloprotease Optimization" in readme
    assert "uv run atlas challenge run --profile demo_cached" in readme
    assert "uv run atlas benchmark run --profile demo_cached" in readme
    assert "uv run streamlit run src/atlas/ui/app.py" in readme
    assert "synthetic demo evidence" in readme.lower()
