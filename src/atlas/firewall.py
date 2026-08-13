"""Recursive pre-lock hidden-label contamination checks."""

from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any

from pydantic import BaseModel


class HiddenLabelLeakError(RuntimeError):
    """Raised when a post-lock field or identity appears in pre-lock state."""


_FORBIDDEN_KEYS = {
    "hidden_outcomes",
    "hidden_labels",
    "retrospective_rank",
    "published_efficiency_m_inverse_s",
    "published_finding",
    "published_outcome",
    "published_kinetic_outcomes",
    "published_cleavage_outcomes",
    "published_selectivity_outcomes",
    "published_optimized_variant_performance",
    "experimental_retrospective_rankings",
    "post_seed_optimization_conclusions",
    "postlock_reveal",
    "retrospective_outcomes",
}
_FORBIDDEN_IDENTITIES = {"op609-s2", "op669-s2", "op609", "op669"}


def assert_prelock_state_clean(value: Any, path: str = "state") -> None:
    if isinstance(value, BaseModel):
        assert_prelock_state_clean(value.model_dump(mode="python"), path)
        return
    if isinstance(value, Enum):
        assert_prelock_state_clean(value.value, path)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text.lower() in _FORBIDDEN_KEYS or key_text.lower().startswith("hidden_"):
                raise HiddenLabelLeakError(f"Hidden field at {path}.{key_text}")
            assert_prelock_state_clean(item, f"{path}.{key_text}")
        return
    if isinstance(value, str):
        lowered = value.lower()
        if any(identity in lowered for identity in _FORBIDDEN_IDENTITIES):
            raise HiddenLabelLeakError(f"Hidden reference identity at {path}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            assert_prelock_state_clean(item, f"{path}[{index}]")
