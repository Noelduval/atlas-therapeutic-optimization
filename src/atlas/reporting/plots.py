"""Compact, deterministic review figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


COLORS = {
    "pass": "#2a9d8f",
    "reference": "#457b9d",
    "separated": "#e9c46a",
    "fail": "#e76f51",
    "not_separated": "#e76f51",
}


def _save(fig, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_validation_dashboard(frame: pd.DataFrame, path: str | Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = [COLORS.get(str(value), "#6c757d") for value in frame["gate_outcome"]]
    ax.bar(frame["variant_id"], frame["predicted_ddg_or_score"], color=colors)
    ax.axhline(1.0, color="#6c757d", linestyle="--", label="non-regressive limit")
    ax.axhline(0.0, color="#222", linewidth=0.8)
    ax.set_ylabel("Predicted ΔΔG (kcal/mol; stability only)")
    ax.set_title("Published-control validation gate")
    ax.tick_params(axis="x", rotation=20)
    ax.legend(frameon=False)
    return _save(fig, path)


def plot_catalytic_geometry(frame: pd.DataFrame, path: str | Path) -> Path:
    columns = [
        column
        for column in (
            "zn_scissile_oxygen_distance_a",
            "e96_to_scissile_carbonyl_distance_a",
        )
        if column in frame
    ]
    fig, axes = plt.subplots(1, len(columns), figsize=(5 * len(columns), 4.5), squeeze=False)
    for ax, column in zip(axes[0], columns):
        groups = [
            group[column].dropna().astype(float).to_numpy()
            for _, group in frame.groupby("variant_id", sort=False)
        ]
        labels = list(frame["variant_id"].drop_duplicates())
        ax.boxplot(groups, tick_labels=labels, patch_artist=True)
        for patch in ax.patches:
            patch.set_facecolor("#457b9d")
            patch.set_alpha(0.75)
        ax.set_title(column.replace("_", " "))
        ax.set_ylabel("Distance (Å)")
        ax.tick_params(axis="x", rotation=25)
    fig.suptitle("Catalytic geometry distributions (static if dynamics unavailable)")
    return _save(fig, path)


def plot_candidate_ranking(frame: pd.DataFrame, path: str | Path) -> Path:
    shown = frame.head(15).sort_values("ranking_score", ascending=False)
    fig, ax = plt.subplots(figsize=(8, max(4.5, len(shown) * 0.32)))
    ax.barh(shown["variant_id"], shown["ranking_score"], color="#2a9d8f")
    ax.set_xlabel("Composite screening score (lower is preferred)")
    ax.set_title("Computational candidates requiring experimental validation")
    return _save(fig, path)
