from __future__ import annotations

import pandas as pd
import pytest

from atlas.validation.validation_gate import (
    ValidationGateError,
    evaluate_validation,
    require_validation_pass,
)


VARIANTS = ["WT", "Y91F", "D126A", "H172A", "Y91F_D126A"]


def _stability(overrides=None):
    values = {"WT": 0.0, "Y91F": -0.2, "D126A": 0.3, "H172A": 0.1, "Y91F_D126A": 1.8}
    values.update(overrides or {})
    return pd.DataFrame(
        {
            "variant_id": VARIANTS,
            "predicted_ddg_or_score": [values[name] for name in VARIANTS],
        }
    )


def _geometry(overrides=None):
    base = {
        "zn_scissile_oxygen_distance_a": 2.30,
        "zn_h95_ne2_distance_a": 2.30,
        "zn_h99_ne2_distance_a": 2.30,
        "zn_e122_oxygen_distance_a": 2.02,
        "e96_to_scissile_carbonyl_distance_a": 3.0,
        "active_site_rmsd_a": 0.1,
        "substrate_rmsd_a": 0.1,
        "substrate_pose_drift_a": 0.1,
        "geometry_complete": True,
    }
    rows = []
    for name in VARIANTS:
        row = {"variant_id": name, **base}
        row.update((overrides or {}).get(name, {}))
        rows.append(row)
    # H172A is separated by required functional-atom loss in the real static model.
    rows[3]["geometry_complete"] = False
    return pd.DataFrame(rows)


def test_full_known_mutation_gate_passes() -> None:
    result = evaluate_validation(_stability(), _geometry())
    assert result.passed
    assert result.dynamics_status == "unavailable"
    assert result.table.set_index("variant_id").loc["Y91F", "gate_outcome"] == "pass"
    assert result.table.set_index("variant_id").loc["H172A", "gate_outcome"] == "separated"
    require_validation_pass(result)


@pytest.mark.parametrize("variant", ["Y91F", "D126A"])
def test_each_beneficial_control_must_be_nonregressive(variant: str) -> None:
    result = evaluate_validation(_stability({variant: 1.1}), _geometry())
    assert not result.passed
    with pytest.raises(ValidationGateError, match=variant):
        require_validation_pass(result)


def test_h172a_must_be_separated() -> None:
    geometry = _geometry()
    geometry.loc[geometry.variant_id == "H172A", "geometry_complete"] = True
    result = evaluate_validation(_stability(), geometry)
    assert not result.passed
    assert "H172A" in " ".join(result.reasons)


def test_double_must_be_separated() -> None:
    result = evaluate_validation(_stability({"Y91F_D126A": 0.5}), _geometry())
    assert not result.passed
    assert "Y91F_D126A" in " ".join(result.reasons)


def test_regressed_zinc_geometry_rejects_beneficial_control() -> None:
    result = evaluate_validation(
        _stability(), _geometry({"Y91F": {"zn_scissile_oxygen_distance_a": 3.0}})
    )
    assert not result.passed
    assert not result.table.set_index("variant_id").loc["Y91F", "geometry_preserved"]


def test_completed_dynamic_geometry_can_reject_beneficial_control() -> None:
    dynamics = _geometry({"Y91F": {"zn_scissile_oxygen_distance_a": 3.0}})
    dynamics["status"] = "completed"
    result = evaluate_validation(_stability(), _geometry(), dynamics)
    assert not result.passed
    row = result.table.set_index("variant_id").loc["Y91F"]
    assert not row["dynamic_geometry_preserved"]
