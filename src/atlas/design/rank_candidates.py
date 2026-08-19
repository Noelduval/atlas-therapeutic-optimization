"""Transparent ranking of candidates with complete real evidence."""

from __future__ import annotations

import pandas as pd


def rank_candidates(
    candidates: pd.DataFrame,
    stability: pd.DataFrame,
    geometry: pd.DataFrame,
) -> pd.DataFrame:
    candidate_ids = set(candidates["variant_id"])
    scored_ids = set(stability["variant_id"])
    geometry_ids = set(geometry["variant_id"])
    missing = sorted(candidate_ids - scored_ids | candidate_ids - geometry_ids)
    if missing:
        raise ValueError(
            "Novel candidates cannot be ranked without real stability and geometry evidence: "
            + ", ".join(missing)
        )
    frame = candidates.merge(
        stability[["variant_id", "predicted_ddg_or_score"]], on="variant_id"
    ).merge(geometry, on="variant_id")
    incomplete = frame.loc[~frame["geometry_complete"].astype(bool), "variant_id"].tolist()
    if incomplete:
        raise ValueError("Incomplete candidate geometry: " + ", ".join(incomplete))
    frame["ranking_score"] = (
        frame["predicted_ddg_or_score"].astype(float)
        + frame["active_site_rmsd_a"].astype(float)
        + frame.get("substrate_pose_drift_a", 0.0)
    )
    frame = frame.sort_values(["ranking_score", "variant_id"]).reset_index(drop=True)
    frame.insert(0, "rank", range(1, len(frame) + 1))
    frame["claim_boundary"] = "computationally predicted novel variant; not experimentally validated"
    return frame
