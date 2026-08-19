from __future__ import annotations

from pathlib import Path

import pandas as pd

from atlas.reporting.plots import (
    plot_candidate_ranking,
    plot_catalytic_geometry,
    plot_validation_dashboard,
)


def test_required_plots_are_nonempty_pngs(tmp_path: Path) -> None:
    validation = pd.DataFrame(
        {
            "variant_id": ["WT", "Y91F"],
            "predicted_ddg_or_score": [0.0, -0.2],
            "gate_outcome": ["reference", "pass"],
        }
    )
    geometry = pd.DataFrame(
        {
            "variant_id": ["WT", "Y91F"],
            "zn_scissile_oxygen_distance_a": [2.3, 2.4],
            "e96_to_scissile_carbonyl_distance_a": [3.0, 3.1],
        }
    )
    ranking = pd.DataFrame(
        {"variant_id": ["L10A", "V11A"], "ranking_score": [-0.1, 0.2]}
    )
    paths = [
        plot_validation_dashboard(validation, tmp_path / "validation.png"),
        plot_catalytic_geometry(geometry, tmp_path / "geometry.png"),
        plot_candidate_ranking(ranking, tmp_path / "ranking.png"),
    ]
    assert all(path.stat().st_size > 1_000 for path in paths)
