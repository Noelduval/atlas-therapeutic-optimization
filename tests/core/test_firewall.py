import pytest

from atlas.challenge.vita import load_visible_challenge
from atlas.firewall import HiddenLabelLeakError, assert_prelock_state_clean


def test_visible_challenge_passes_recursive_firewall() -> None:
    assert_prelock_state_clean({"dataset": load_visible_challenge(), "iteration": 1})


@pytest.mark.parametrize(
    "contaminated",
    [
        {"hidden_outcomes": {"winner": "control"}},
        {"candidate": {"published_efficiency_m_inverse_s": 3045.14}},
        {"ranking": [{"identity": "OP609-S2"}]},
        {"nested": ({"retrospective_rank": 1},)},
        {"published_kinetic_outcomes": {"value": 1}},
        {"published_cleavage_outcomes": {"value": 1}},
        {"published_selectivity_outcomes": {"value": 1}},
        {"post_seed_optimization_conclusions": {"winner": "control"}},
        {"ranking": [{"identity": "op669-s2"}]},
    ],
)
def test_firewall_rejects_hidden_fields_and_identifiers(contaminated) -> None:
    with pytest.raises(HiddenLabelLeakError):
        assert_prelock_state_clean(contaminated)


def test_firewall_allows_retrospective_campaign_type_without_outcomes() -> None:
    assert_prelock_state_clean({"campaign_type": "blinded_retrospective"})
