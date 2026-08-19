"""Interpretable stability-plus-geometry benchmark gate."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from atlas.validation.known_mutants import published_benchmark_table


BENEFICIAL = ("Y91F", "D126A")
REGRESSIVE = ("H172A", "Y91F_D126A")
STABILITY_LIMIT_KCAL_MOL = 1.0
DISTANCE_TOLERANCES = {
    "zn_scissile_oxygen_distance_a": 0.40,
    "zn_h95_ne2_distance_a": 0.35,
    "zn_h99_ne2_distance_a": 0.35,
    "zn_e122_oxygen_distance_a": 0.35,
    "e96_to_scissile_carbonyl_distance_a": 0.50,
}
ABSOLUTE_TOLERANCES = {
    "active_site_rmsd_a": 1.0,
    "substrate_rmsd_a": 1.0,
    "substrate_pose_drift_a": 0.75,
}


class ValidationGateError(RuntimeError):
    """Known-control performance is insufficient to enter novel design."""


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    table: pd.DataFrame
    reasons: tuple[str, ...]
    dynamics_status: str


def _geometry_preserved(row: pd.Series, reference: pd.Series) -> tuple[bool, str]:
    if not bool(row.get("geometry_complete", False)):
        return False, "required catalytic geometry is incomplete"
    failures: list[str] = []
    for column, tolerance in DISTANCE_TOLERANCES.items():
        value, baseline = row.get(column), reference.get(column)
        if pd.isna(value) or pd.isna(baseline) or abs(float(value) - float(baseline)) > tolerance:
            failures.append(column)
    for column, tolerance in ABSOLUTE_TOLERANCES.items():
        value = row.get(column)
        if pd.isna(value) or float(value) > tolerance:
            failures.append(column)
    if failures:
        return False, "geometry threshold failed: " + ", ".join(failures)
    return True, "geometry preserved"


def evaluate_validation(
    stability: pd.DataFrame,
    geometry: pd.DataFrame,
    dynamics: pd.DataFrame | None = None,
) -> ValidationResult:
    """Evaluate all four published mutation controls before novel design."""
    required = {"WT", *BENEFICIAL, *REGRESSIVE}
    stable_ids = set(stability.get("variant_id", ()))
    geometry_ids = set(geometry.get("variant_id", ()))
    missing = sorted(required - stable_ids | required - geometry_ids)
    if missing:
        raise ValidationGateError(
            "Validation evidence is incomplete for: " + ", ".join(missing)
        )
    scores = stability[["variant_id", "predicted_ddg_or_score"]].copy()
    joined = published_benchmark_table().merge(scores, on="variant_id", how="left")
    joined = joined.merge(geometry, on="variant_id", how="left")
    reference = joined.set_index("variant_id").loc["WT"]

    preserved: list[bool] = []
    geometry_reason: list[str] = []
    stability_class: list[str] = []
    outcomes: list[str] = []
    reasons: list[str] = []
    for _, row in joined.iterrows():
        variant = str(row["variant_id"])
        geometry_ok, geometry_note = _geometry_preserved(row, reference)
        ddg = float(row["predicted_ddg_or_score"])
        stable = ddg <= STABILITY_LIMIT_KCAL_MOL
        preserved.append(geometry_ok)
        geometry_reason.append(geometry_note)
        stability_class.append("non_regressive" if stable else "regressive")
        if variant == "WT":
            outcomes.append("reference")
        elif variant in BENEFICIAL:
            passed = stable and geometry_ok
            outcomes.append("pass" if passed else "fail")
            if not passed:
                reasons.append(
                    f"{variant} did not reproduce the beneficial-control class "
                    f"(stability={stable}, geometry={geometry_ok})."
                )
        else:
            separated = (not stable) or (not geometry_ok)
            outcomes.append("separated" if separated else "not_separated")
            if not separated:
                reasons.append(
                    f"{variant} was not separated from non-regressive variants."
                )
    joined["stability_class"] = stability_class
    joined["geometry_preserved"] = pd.Series(preserved, dtype=bool)
    joined["geometry_gate_reason"] = geometry_reason
    joined["gate_outcome"] = outcomes

    dynamics_status = "unavailable"
    if dynamics is not None and not dynamics.empty:
        statuses = set(dynamics.get("status", ()))
        if "completed" in statuses:
            dynamics_status = "completed"
        elif statuses:
            dynamics_status = "unavailable"

    return ValidationResult(not reasons, joined, tuple(reasons), dynamics_status)


def require_validation_pass(result: ValidationResult) -> None:
    if not result.passed:
        raise ValidationGateError(
            "Known-mutation validation failed; novel design is blocked. "
            + " ".join(result.reasons)
        )


def write_validation_outputs(result: ValidationResult, output_dir: str | Path) -> None:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    result.table.to_csv(destination / "known_mutation_validation.csv", index=False)
    status = "PASS" if result.passed else "FAIL — NOVEL DESIGN BLOCKED"
    reasons = "\n".join(f"- {reason}" for reason in result.reasons) or "- All fixed gate conditions passed."
    (destination / "validation_report.md").write_text(
        "# Known-mutation validation\n\n"
        f"**Gate status:** {status}\n\n"
        "ThermoMPNN scores are computational stability predictions, not activity predictions.\n\n"
        "## Gate findings\n\n"
        f"{reasons}\n\n"
        f"Dynamics evidence: `{result.dynamics_status}`. Static geometry remains explicit.\n"
    )
