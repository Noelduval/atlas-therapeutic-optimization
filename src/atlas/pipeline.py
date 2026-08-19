"""Direct, validation-gated Atlas execution pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
from typing import Protocol, Sequence

import pandas as pd

from atlas.design.candidate_generator import candidate_table, generate_candidates
from atlas.design.rank_candidates import rank_candidates
from atlas.dynamics import DynamicsConfig, minimize_variant, run_short_md
from atlas.geometry.catalytic_metrics import GeometryRecord, measure_geometry, measure_many
from atlas.reporting.csv_outputs import write_provenance, write_warnings
from atlas.reporting.plots import (
    plot_candidate_ranking,
    plot_catalytic_geometry,
    plot_validation_dashboard,
)
from atlas.stability.common import StabilityVariant, normalized_frame, normalized_row
from atlas.stability.thermompnn_d_runner import ThermoMPNNDRunner
from atlas.stability.thermompnn_runner import ThermoMPNNRunner
from atlas.structure.mutate import Mutation, apply_mutations, build_known_mutants
from atlas.structure.reconstruct import reconstruct_active_like
from atlas.validation.validation_gate import (
    ValidationResult,
    evaluate_validation,
    require_validation_pass,
    write_validation_outputs,
)


@dataclass(frozen=True)
class PipelineConfig:
    input_structure: Path = Path("data/23WN.cif")
    output_root: Path = Path("outputs")
    run_id: str | None = None
    thermompnn_repo: Path = Path(".external/ThermoMPNN")
    thermompnn_d_repo: Path = Path(".external/ThermoMPNN-D")
    dynamics_mode: str = "minimize"
    dynamics_config: DynamicsConfig = DynamicsConfig()


@dataclass(frozen=True)
class PipelineResult:
    status: str
    run_dir: Path
    validation: ValidationResult
    candidate_ranking: pd.DataFrame


class StabilityProvider(Protocol):
    def score_known(self, pdb_path: Path, output_dir: Path) -> pd.DataFrame: ...

    def score_candidates(
        self,
        pdb_path: Path,
        variants: Sequence[StabilityVariant],
        output_dir: Path,
    ) -> pd.DataFrame: ...


class OfficialStabilityProvider:
    """Compose official single and epistatic predictors without hiding either."""

    def __init__(self, single_repo: Path, double_repo: Path) -> None:
        self.single = ThermoMPNNRunner(single_repo)
        self.double = ThermoMPNNDRunner(double_repo)

    def score_known(self, pdb_path: Path, output_dir: Path) -> pd.DataFrame:
        singles = [
            StabilityVariant("Y91F", "Y91F", "Y115F"),
            StabilityVariant("D126A", "D126A", "D150A"),
            StabilityVariant("H172A", "H172A", "H196A"),
        ]
        double = StabilityVariant(
            "Y91F_D126A", "Y91F:D126A", "Y115F:D150A"
        )
        rows = [
            normalized_row(
                StabilityVariant("WT", "WT", "Q120E reconstruction"),
                "derived WT reference",
                0.0,
                "WT ΔΔG is defined as zero; no model inference was substituted.",
            )
        ]
        single_scores = self.single.run(pdb_path, singles, output_dir / "single")
        double_scores = self.double.run(pdb_path, [double], output_dir / "double")
        result = pd.concat(
            [normalized_frame(rows), single_scores, double_scores], ignore_index=True
        )
        result.to_csv(output_dir / "thermompnn_scores.csv", index=False)
        return result

    def score_candidates(
        self,
        pdb_path: Path,
        variants: Sequence[StabilityVariant],
        output_dir: Path,
    ) -> pd.DataFrame:
        return self.single.run(pdb_path, variants, output_dir)


def _fresh_run_dir(config: PipelineConfig) -> Path:
    run_id = config.run_id or datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    destination = config.output_root / run_id
    if destination.exists():
        raise FileExistsError(f"Atlas never overwrites a run directory: {destination}")
    destination.mkdir(parents=True)
    return destination


def _variant_paths(manifest: pd.DataFrame) -> dict[str, Path]:
    return {
        str(row.variant_id): Path(row.pdb_path)
        for row in manifest.itertuples(index=False)
    }


def _empty_snapshot_frame() -> pd.DataFrame:
    metric_columns = [
        column
        for column in GeometryRecord.__annotations__
        if column not in {"variant_id", "warnings"}
    ]
    return pd.DataFrame(
        columns=["variant_id", "stage", "step", "time_ps", *metric_columns, "warnings"]
    )


def _run_dynamics_stage(
    variants: dict[str, Path],
    run_dir: Path,
    mode: str,
    config: DynamicsConfig,
    static_reference: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    if mode not in {"skip", "minimize", "short-md"}:
        raise ValueError("dynamics_mode must be one of: skip, minimize, short-md")
    summaries: list[dict[str, object]] = []
    completed: dict[str, Path] = {}
    snapshot_energy: dict[str, tuple[dict[str, object], ...]] = {}
    warnings: list[str] = []
    for variant_id, pdb_path in variants.items():
        if mode == "skip":
            summaries.append(
                {
                    "variant_id": variant_id,
                    "status": "skipped_by_configuration",
                    "output_pdb": "",
                    "snapshot_count": 0,
                    "warning": "OpenMM was disabled by configuration; static geometry is used.",
                }
            )
            continue
        output_dir = run_dir / "openmm" / variant_id
        result = (
            minimize_variant(pdb_path, output_dir, config)
            if mode == "minimize"
            else run_short_md(pdb_path, output_dir, config)
        )
        summaries.append(
            {
                "variant_id": variant_id,
                "status": result.status,
                "output_pdb": str(result.output_pdb or ""),
                "snapshot_count": len(result.snapshot_records),
                "warning": result.warning,
            }
        )
        if result.status == "completed" and result.output_pdb:
            completed[variant_id] = result.output_pdb
            snapshot_energy[variant_id] = result.snapshot_records
        elif result.warning:
            warnings.append(f"{variant_id}: {result.warning}")
    summary = pd.DataFrame(summaries)

    snapshot_rows: list[dict[str, object]] = []
    if completed:
        reference = completed.get("WT", static_reference)
        for variant_id, pdb_path in completed.items():
            record = measure_geometry(pdb_path, reference, variant_id).csv_row()
            energies = snapshot_energy.get(variant_id, ({"stage": "final", "step": 0},))
            final_energy = energies[-1]
            snapshot_rows.append({"variant_id": variant_id, **final_energy, **record})
            mask = summary["variant_id"] == variant_id
            for column, value in record.items():
                summary.loc[mask, column] = value
    snapshots = pd.DataFrame(snapshot_rows) if snapshot_rows else _empty_snapshot_frame()
    return summary, snapshots, warnings


def _deposited_label(label: str) -> str:
    match = re.fullmatch(r"([A-Z])(\d+)([A-Z])", label)
    if not match:
        return label
    return f"{match.group(1)}{int(match.group(2)) + 24}{match.group(3)}"


def run_pipeline(
    config: PipelineConfig,
    *,
    stability_provider: StabilityProvider | None = None,
) -> PipelineResult:
    """Execute fixed phases and raise before any novel output on gate failure."""
    run_dir = _fresh_run_dir(config)
    warnings: list[str] = []
    write_provenance(
        config.input_structure,
        run_dir / "provenance.json",
        {"dynamics_mode": config.dynamics_mode},
    )
    reconstructed = run_dir / "DP622_active_like_reconstruction.pdb"
    reconstruct_active_like(
        config.input_structure,
        reconstructed,
        run_dir / "residue_numbering_map.csv",
    )
    manifest = build_known_mutants(reconstructed, run_dir / "known_mutant_pdbs")
    known_paths = _variant_paths(manifest)
    geometry = measure_many(
        known_paths, reconstructed, run_dir / "geometry_metrics.csv"
    )
    for row in geometry.itertuples(index=False):
        if row.warnings:
            warnings.append(f"Static geometry {row.variant_id}: {row.warnings}")

    provider = stability_provider or OfficialStabilityProvider(
        config.thermompnn_repo, config.thermompnn_d_repo
    )
    try:
        stability = provider.score_known(reconstructed, run_dir / "stability")
    except Exception as exc:
        warnings.append(f"Stability stage stopped: {type(exc).__name__}: {exc}")
        write_warnings(warnings, run_dir / "pipeline_warnings.md")
        raise
    stability.to_csv(run_dir / "thermompnn_scores.csv", index=False)

    dynamics, snapshots, dynamics_warnings = _run_dynamics_stage(
        known_paths,
        run_dir,
        config.dynamics_mode,
        config.dynamics_config,
        reconstructed,
    )
    warnings.extend(dynamics_warnings)
    dynamics.to_csv(run_dir / "openmm_dynamics_summary.csv", index=False)
    snapshots.to_csv(run_dir / "openmm_snapshot_metrics.csv", index=False)

    validation = evaluate_validation(stability, geometry, dynamics)
    write_validation_outputs(validation, run_dir)
    plot_validation_dashboard(
        validation.table, run_dir / "figures" / "validation_dashboard.png"
    )
    plot_catalytic_geometry(
        geometry, run_dir / "figures" / "catalytic_geometry_boxplots.png"
    )
    write_warnings(warnings, run_dir / "pipeline_warnings.md")
    require_validation_pass(validation)

    candidates = generate_candidates(reconstructed, validation)
    candidate_manifest = candidate_table(candidates)
    candidate_manifest["dp622_numbering"] = candidate_manifest["mutation_set"]
    candidate_manifest["deposited_numbering"] = candidate_manifest[
        "mutation_set"
    ].map(_deposited_label)
    candidate_manifest["evidence_class"] = "computationally_predicted_novel_variant"
    candidate_dir = run_dir / "novel_candidate_pdbs"
    candidate_dir.mkdir(parents=True)
    candidate_paths: dict[str, Path] = {}
    for candidate in candidates:
        path = apply_mutations(
            reconstructed,
            (Mutation(candidate.position, candidate.wildtype, candidate.mutant),),
            candidate_dir / f"{candidate.variant_id}.pdb",
        )
        candidate_paths[candidate.variant_id] = path
    candidate_manifest["pdb_path"] = candidate_manifest["variant_id"].map(
        lambda name: str(candidate_paths[name])
    )
    candidate_manifest.to_csv(run_dir / "novel_candidates_manifest.csv", index=False)

    requests = [
        StabilityVariant(
            candidate.variant_id,
            candidate.mutation_set,
            _deposited_label(candidate.mutation_set),
        )
        for candidate in candidates
    ]
    candidate_stability = provider.score_candidates(
        reconstructed, requests, run_dir / "stability" / "novel"
    )
    candidate_stability.to_csv(run_dir / "novel_thermompnn_scores.csv", index=False)
    candidate_geometry = measure_many(
        candidate_paths,
        reconstructed,
        run_dir / "novel_geometry_metrics.csv",
    )
    candidate_dynamics, candidate_snapshots, candidate_dynamics_warnings = (
        _run_dynamics_stage(
            candidate_paths,
            run_dir,
            config.dynamics_mode,
            config.dynamics_config,
            reconstructed,
        )
    )
    warnings.extend(candidate_dynamics_warnings)
    dynamics = pd.concat([dynamics, candidate_dynamics], ignore_index=True)
    snapshots = pd.concat([snapshots, candidate_snapshots], ignore_index=True)
    dynamics.to_csv(run_dir / "openmm_dynamics_summary.csv", index=False)
    snapshots.to_csv(run_dir / "openmm_snapshot_metrics.csv", index=False)

    ranking_geometry = candidate_geometry.copy()
    completed_dynamic = candidate_dynamics[
        candidate_dynamics["status"] == "completed"
    ]
    if not completed_dynamic.empty:
        completed_dynamic = completed_dynamic.set_index("variant_id")
        ranking_geometry = ranking_geometry.set_index("variant_id")
        for variant_id, row in completed_dynamic.iterrows():
            for column in GeometryRecord.__annotations__:
                if column != "variant_id" and column in row and pd.notna(row[column]):
                    ranking_geometry.loc[variant_id, column] = row[column]
        ranking_geometry = ranking_geometry.reset_index()
    ranking = rank_candidates(candidate_manifest, candidate_stability, ranking_geometry)
    ranking.to_csv(run_dir / "novel_candidates_ranked.csv", index=False)
    top_dir = run_dir / "top_5_candidate_pdbs"
    top_dir.mkdir()
    for variant_id in ranking.head(5)["variant_id"]:
        shutil.copy2(candidate_paths[variant_id], top_dir / f"{variant_id}.pdb")
    plot_candidate_ranking(
        ranking, run_dir / "figures" / "candidate_ranking_summary.png"
    )
    write_warnings(warnings, run_dir / "pipeline_warnings.md")
    return PipelineResult("completed", run_dir, validation, ranking)
