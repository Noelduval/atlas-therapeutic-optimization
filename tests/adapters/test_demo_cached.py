from atlas.adapters.demo_cached import DemoCachedAdapter
from atlas.challenge.vita import load_visible_challenge
from atlas.domain.enums import EvidenceKind, Provenance


def test_demo_cached_outputs_are_deterministic_and_labeled() -> None:
    adapter = DemoCachedAdapter()
    seed = load_visible_challenge().seed
    first = adapter.evaluate(seed, "atlas-vita-abeta-s2")
    second = adapter.evaluate(seed, "atlas-vita-abeta-s2")

    assert first == second
    assert all(record.provenance is Provenance.SYNTHETIC_DEMO for record in first.evidence)
    assert all("not biological model output" in record.summary for record in first.evidence)
    assert first.run_record.provenance is Provenance.SYNTHETIC_DEMO


def test_demo_cached_has_distinct_evidence_dimensions_without_kinetics() -> None:
    result = DemoCachedAdapter().evaluate(
        load_visible_challenge().seed,
        "atlas-vita-abeta-s2",
    )
    assert {record.kind for record in result.evidence} == {
        EvidenceKind.SEQUENCE,
        EvidenceKind.STRUCTURE,
        EvidenceKind.CATALYTIC_GEOMETRY,
        EvidenceKind.SUBSTRATE_RECOGNITION,
        EvidenceKind.SELECTIVITY_RISK,
        EvidenceKind.DEVELOPABILITY,
        EvidenceKind.SIMULATION_SANITY,
    }
    serialized = result.model_dump_json().lower()
    assert "kcat" not in serialized
    assert '"metric":"km"' not in serialized


def test_profile_registry_contains_only_demo_cached() -> None:
    from atlas.profiles import PROFILES

    assert tuple(PROFILES) == ("demo_cached",)
