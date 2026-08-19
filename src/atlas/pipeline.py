"""Direct, validation-gated Atlas execution pipeline."""

from __future__ import annotations

from dataclasses import dataclass
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
from atlas.run_context import prepare_run_directory
from atlas.reporting.plots import (
    plot_candidate_ranking,
    plot_catalytic_geometry,
    plot_validation_dashboard,
)
from atlas.stability.common import (
    NORMALIZED_COLUMNS,
    ScientificOutputError,
    StabilityVariant,
    normalized_frame,
    normalized_row,
)
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
    resume: bool = False
    stop_after: str | None = None


@dataclass(frozen=True)
class PipelineResult:
    status: str
    run_dir: Path
    validation: ValidationResult | None
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

    @staticmethod
    def _single_requests() -> list[StabilityVariant]:
        return [
            StabilityVariant("Y91F", "Y91F", "Y115F"),
            StabilityVariant("D126A", "D126A", "D150A"),
            StabilityVariant("H172A", "H172A", "H196A"),
        ]

    def score_known_singles(self, pdb_path: Path, output_dir: Path) -> pd.DataFrame:
        rows = [
            normalized_row(
                StabilityVariant("WT", "WT", "Q120E reconstruction"),
                "derived WT reference",
                0.0,
                "WT ΔΔG is defined as zero; no model inference was substituted.",
            )
        ]
        scores = self.single.run(
            pdb_path, self._single_requests(), output_dir / "single"
        )
        result = pd.concat([normalized_frame(rows), scores], ignore_index=True)
        result.to_csv(output_dir / "known_single_scores.csv", index=False)
        return result

    def score_known_double(self, pdb_path: Path, output_dir: Path) -> pd.DataFrame:
        request = StabilityVariant(
            "Y91F_D126A", "Y91F:D126A", "Y115F:D150A"
        )
        result = self.double.run(pdb_path, [request], output_dir / "double")
        result.to_csv(output_dir / "known_double_scores.csv", index=False)
        return result

    def score_known(self, pdb_path: Path, output_dir: Path) -> pd.DataFrame:
        result = pd.concat(
            [
                self.score_known_singles(pdb_path, output_dir),
                self.score_known_double(pdb_path, output_dir),
            ],
            ignore_index=True,
        )
        result.to_csv(output_dir / "thermompnn_scores.csv", index=False)
        return result

    def score_candidates(
        self,
        pdb_path: Path,
        variants: Sequence[StabilityVariant],
        output_dir: Path,
    ) -> pd.DataFrame:
        known_sweep = (
            output_dir.parent
            / "single"
            / f"ThermoMPNN_inference_{pdb_path.stem}.csv"
        )
        if known_sweep.is_file():
            print(f"Reusing genuine ThermoMPNN full sweep: {known_sweep}")
            return self.single.normalize_existing(
                known_sweep, variants, output_dir
            )
        return self.single.run(pdb_path, variants, output_dir)


def _variant_paths(manifest: pd.DataFrame) -> dict[str, Path]:
    return {
        str(row.variant_id): Path(row.pdb_path)
        for row in manifest.itertuples(index=False)
    }


def _read_stability_cache(path: Path, expected_ids: set[str]) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing_columns = set(NORMALIZED_COLUMNS).difference(frame.columns)
    if missing_columns:
        raise ScientificOutputError(
            f"Cached stability output {path} is missing columns: {sorted(missing_columns)}"
        )
    actual_ids = set(frame["variant_id"].astype(str))
    if actual_ids != expected_ids:
        raise ScientificOutputError(
            f"Cached stability output {path} has variants {sorted(actual_ids)}, "
            f"expected {sorted(expected_ids)}"
        )
    if frame["predicted_ddg_or_score"].isna().any():
        raise ScientificOutputError(f"Cached stability output {path} contains null scores")
    return frame


def _stopped(
    stage: str,
    run_dir: Path,
    *,
    scientific_conclusion: str = "NOT_EVALUATED",
    candidate_generation_decision: str = "blocked_until_validation",
) -> PipelineResult:
    _write_execution_status(
        run_dir,
        stage=stage,
        status=f"stopped_after_{stage}",
        scientific_conclusion=scientific_conclusion,
        candidate_generation_decision=candidate_generation_decision,
    )
    return PipelineResult(
        f"stopped_after_{stage}", run_dir, None, pd.DataFrame()
    )


def _write_execution_status(
    run_dir: Path,
    *,
    stage: str,
    status: str,
    scientific_conclusion: str,
    candidate_generation_decision: str,
) -> None:
    import json

    (run_dir / "execution_status.json").write_text(
        json.dumps(
            {
                "stage": stage,
                "status": status,
                "scientific_conclusion": scientific_conclusion,
                "candidate_generation_decision": candidate_generation_decision,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


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
            energies = snapshot_energy.get(variant_id, ({"stage": "final", "step": 0},))
            for snapshot in energies:
                snapshot_path = Path(str(snapshot.get("pdb_path", pdb_path)))
                record = measure_geometry(
                    snapshot_path, reference, variant_id
                ).csv_row()
                snapshot_rows.append({"variant_id": variant_id, **snapshot, **record})
            record = measure_geometry(pdb_path, reference, variant_id).csv_row()
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
    allowed_stops = {
        None,
        "structure",
        "thermompnn",
        "thermompnn-d",
        "geometry",
        "dynamics",
        "validation",
    }
    if config.stop_after not in allowed_stops:
        raise ValueError(
            "stop_after must be one of: structure, thermompnn, thermompnn-d, "
            "geometry, dynamics, validation"
        )
    run_dir = prepare_run_directory(config)
    warnings: list[str] = []
    if not (run_dir / "provenance.json").exists():
        write_provenance(
            config.input_structure,
            run_dir / "provenance.json",
            {"dynamics_mode": config.dynamics_mode},
        )

    print("[Atlas] Stage 1/9: active-like reconstruction and benchmark structures")
    reconstructed = run_dir / "DP622_active_like_reconstruction.pdb"
    mapping_path = run_dir / "residue_numbering_map.csv"
    manifest_path = run_dir / "known_mutants_manifest.csv"
    if config.resume and all(
        path.is_file() for path in (reconstructed, mapping_path, manifest_path)
    ):
        manifest = pd.read_csv(manifest_path)
        if not all(Path(path).is_file() for path in manifest["pdb_path"]):
            raise FileNotFoundError("A cached benchmark PDB listed in the manifest is missing")
    else:
        reconstruct_active_like(config.input_structure, reconstructed, mapping_path)
        manifest = build_known_mutants(reconstructed, run_dir / "known_mutant_pdbs")
    known_paths = _variant_paths(manifest)
    if config.stop_after == "structure":
        return _stopped("structure", run_dir)

    provider = stability_provider or OfficialStabilityProvider(
        config.thermompnn_repo, config.thermompnn_d_repo
    )
    stability_dir = run_dir / "stability"
    stability_dir.mkdir(exist_ok=True)
    stability_path = run_dir / "thermompnn_scores.csv"
    expected_known = {"WT", "Y91F", "D126A", "H172A", "Y91F_D126A"}
    try:
        stability = None
        if config.resume and stability_path.is_file():
            try:
                stability = _read_stability_cache(stability_path, expected_known)
                print("[Atlas] Reused validated known-mutation stability checkpoint")
            except ScientificOutputError:
                if not isinstance(provider, OfficialStabilityProvider):
                    raise
                print("[Atlas] Found a valid partial stability checkpoint; resuming")
        if stability is None and isinstance(provider, OfficialStabilityProvider):
            print("[Atlas] Stage 2/9: genuine ThermoMPNN single-mutant inference")
            single_path = stability_dir / "known_single_scores.csv"
            expected_singles = {"WT", "Y91F", "D126A", "H172A"}
            if config.resume and single_path.is_file():
                single_scores = _read_stability_cache(single_path, expected_singles)
                print("[Atlas] Reused ThermoMPNN single-mutant checkpoint")
            else:
                single_scores = provider.score_known_singles(
                    reconstructed, stability_dir
                )
            single_scores.to_csv(stability_path, index=False)
            if config.stop_after == "thermompnn":
                return _stopped("thermompnn", run_dir)

            print("[Atlas] Stage 3/9: genuine ThermoMPNN-D epistatic inference")
            double_path = stability_dir / "known_double_scores.csv"
            if config.resume and double_path.is_file():
                double_scores = _read_stability_cache(
                    double_path, {"Y91F_D126A"}
                )
                print("[Atlas] Reused ThermoMPNN-D checkpoint")
            else:
                double_scores = provider.score_known_double(
                    reconstructed, stability_dir
                )
            stability = pd.concat(
                [single_scores, double_scores], ignore_index=True
            )
        elif stability is None:
            print("[Atlas] Stage 2-3/9: injected stability boundary")
            stability = provider.score_known(reconstructed, stability_dir)
    except Exception as exc:
        warnings.append(f"Stability stage stopped: {type(exc).__name__}: {exc}")
        write_warnings(warnings, run_dir / "pipeline_warnings.md")
        _write_execution_status(
            run_dir,
            stage="stability",
            status="EXTERNALLY_BLOCKED",
            scientific_conclusion="EXTERNALLY_BLOCKED",
            candidate_generation_decision="blocked",
        )
        raise
    stability.to_csv(run_dir / "thermompnn_scores.csv", index=False)
    if config.stop_after == "thermompnn":
        return _stopped("thermompnn", run_dir)
    if config.stop_after == "thermompnn-d":
        return _stopped("thermompnn-d", run_dir)

    print("[Atlas] Stage 4/9: catalytic geometry")
    geometry_path = run_dir / "geometry_metrics.csv"
    if config.resume and geometry_path.is_file():
        geometry = pd.read_csv(geometry_path)
    else:
        geometry = measure_many(known_paths, reconstructed, geometry_path)
    for row in geometry.itertuples(index=False):
        if row.warnings:
            warnings.append(f"Static geometry {row.variant_id}: {row.warnings}")
    if config.stop_after == "geometry":
        write_warnings(warnings, run_dir / "pipeline_warnings.md")
        return _stopped("geometry", run_dir)

    print("[Atlas] Stage 5/9: restrained OpenMM attempt")
    known_dynamics_path = run_dir / "openmm" / "known_summary.csv"
    known_snapshots_path = run_dir / "openmm" / "known_snapshot_metrics.csv"
    if config.resume and known_dynamics_path.is_file() and known_snapshots_path.is_file():
        dynamics = pd.read_csv(known_dynamics_path)
        snapshots = pd.read_csv(known_snapshots_path)
        dynamics_warnings = [
            str(value)
            for value in dynamics.get("warning", pd.Series(dtype=str)).dropna()
            if str(value)
        ]
        print("[Atlas] Reused OpenMM benchmark checkpoint")
    else:
        dynamics, snapshots, dynamics_warnings = _run_dynamics_stage(
            known_paths,
            run_dir,
            config.dynamics_mode,
            config.dynamics_config,
            reconstructed,
        )
        known_dynamics_path.parent.mkdir(exist_ok=True)
        dynamics.to_csv(known_dynamics_path, index=False)
        snapshots.to_csv(known_snapshots_path, index=False)
    warnings.extend(dynamics_warnings)
    dynamics.to_csv(run_dir / "openmm_dynamics_summary.csv", index=False)
    snapshots.to_csv(run_dir / "openmm_snapshot_metrics.csv", index=False)
    if config.stop_after == "dynamics":
        write_warnings(warnings, run_dir / "pipeline_warnings.md")
        return _stopped("dynamics", run_dir)

    print("[Atlas] Stage 6/9: predefined published-control validation gate")
    validation = evaluate_validation(stability, geometry, dynamics)
    write_validation_outputs(validation, run_dir)
    plot_validation_dashboard(
        validation.table, run_dir / "figures" / "validation_dashboard.png"
    )
    plot_catalytic_geometry(
        snapshots if not snapshots.empty else geometry,
        run_dir / "figures" / "catalytic_geometry_boxplots.png",
    )
    write_warnings(warnings, run_dir / "pipeline_warnings.md")
    try:
        require_validation_pass(validation)
    except Exception:
        _write_execution_status(
            run_dir,
            stage="validation",
            status="BENCHMARK_FAILED",
            scientific_conclusion="BENCHMARK FAILED",
            candidate_generation_decision="blocked",
        )
        raise
    _write_execution_status(
        run_dir,
        stage="validation",
        status="VALIDATED",
        scientific_conclusion="VALIDATED",
        candidate_generation_decision="allowed",
    )
    if config.stop_after == "validation":
        return _stopped(
            "validation",
            run_dir,
            scientific_conclusion="VALIDATED",
            candidate_generation_decision="allowed",
        )

    ranked_path = run_dir / "novel_candidates_ranked.csv"
    if config.resume and ranked_path.is_file():
        ranking = pd.read_csv(ranked_path)
        _write_execution_status(
            run_dir,
            stage="complete",
            status="completed",
            scientific_conclusion="VALIDATED",
            candidate_generation_decision="completed",
        )
        return PipelineResult("completed", run_dir, validation, ranking)

    print("[Atlas] Stage 7/9: post-gate candidate generation")
    candidates = generate_candidates(reconstructed, validation)
    candidate_dir = run_dir / "novel_candidate_pdbs"
    candidate_manifest_path = run_dir / "novel_candidates_manifest.csv"
    if config.resume and candidate_manifest_path.is_file():
        candidate_manifest = pd.read_csv(candidate_manifest_path)
        candidate_paths = {
            str(row.variant_id): Path(row.pdb_path)
            for row in candidate_manifest.itertuples(index=False)
        }
        if not all(path.is_file() for path in candidate_paths.values()):
            raise FileNotFoundError("A cached novel-candidate PDB is missing")
    else:
        candidate_manifest = candidate_table(candidates)
        candidate_manifest["dp622_numbering"] = candidate_manifest["mutation_set"]
        candidate_manifest["deposited_numbering"] = candidate_manifest[
            "mutation_set"
        ].map(_deposited_label)
        candidate_manifest["evidence_class"] = "computationally_predicted_novel_variant"
        candidate_dir.mkdir(parents=True, exist_ok=True)
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
        candidate_manifest.to_csv(candidate_manifest_path, index=False)

    requests = [
        StabilityVariant(
            str(row.variant_id),
            str(row.mutation_set),
            str(row.deposited_numbering),
        )
        for row in candidate_manifest.itertuples(index=False)
    ]
    print("[Atlas] Stage 8/9: genuine candidate stability and geometry screening")
    candidate_stability_path = run_dir / "novel_thermompnn_scores.csv"
    expected_candidates = set(candidate_manifest["variant_id"].astype(str))
    if config.resume and candidate_stability_path.is_file():
        candidate_stability = _read_stability_cache(
            candidate_stability_path, expected_candidates
        )
    else:
        candidate_stability = provider.score_candidates(
            reconstructed, requests, run_dir / "stability" / "novel"
        )
        candidate_stability.to_csv(candidate_stability_path, index=False)
    candidate_geometry_path = run_dir / "novel_geometry_metrics.csv"
    if config.resume and candidate_geometry_path.is_file():
        candidate_geometry = pd.read_csv(candidate_geometry_path)
    else:
        candidate_geometry = measure_many(
            candidate_paths,
            reconstructed,
            candidate_geometry_path,
        )

    candidate_dynamics_path = run_dir / "openmm" / "candidate_summary.csv"
    candidate_snapshots_path = run_dir / "openmm" / "candidate_snapshot_metrics.csv"
    if config.resume and candidate_dynamics_path.is_file() and candidate_snapshots_path.is_file():
        candidate_dynamics = pd.read_csv(candidate_dynamics_path)
        candidate_snapshots = pd.read_csv(candidate_snapshots_path)
        candidate_dynamics_warnings = [
            str(value)
            for value in candidate_dynamics.get("warning", pd.Series(dtype=str)).dropna()
            if str(value)
        ]
    else:
        candidate_dynamics, candidate_snapshots, candidate_dynamics_warnings = (
            _run_dynamics_stage(
                candidate_paths,
                run_dir,
                config.dynamics_mode,
                config.dynamics_config,
                reconstructed,
            )
        )
        candidate_dynamics.to_csv(candidate_dynamics_path, index=False)
        candidate_snapshots.to_csv(candidate_snapshots_path, index=False)
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
    if not candidate_snapshots.empty:
        dispersion = (
            candidate_snapshots.groupby("variant_id")[[
                "zn_scissile_oxygen_distance_a",
                "substrate_pose_drift_a",
            ]]
            .std(ddof=0)
            .fillna(0.0)
            .sum(axis=1)
            .rename("dynamic_geometry_dispersion_a")
        )
        ranking_geometry = ranking_geometry.merge(
            dispersion, left_on="variant_id", right_index=True, how="left"
        )
    wt_geometry = geometry.set_index("variant_id").loc["WT"]
    ranking = rank_candidates(
        candidate_manifest,
        candidate_stability,
        ranking_geometry,
        reference_geometry=wt_geometry,
    )
    print("[Atlas] Stage 9/9: candidate ranking and report export")
    ranking.to_csv(ranked_path, index=False)
    top_dir = run_dir / "top_5_candidate_pdbs"
    top_dir.mkdir(exist_ok=True)
    for variant_id in ranking.head(5)["variant_id"]:
        shutil.copy2(candidate_paths[variant_id], top_dir / f"{variant_id}.pdb")
    plot_candidate_ranking(
        ranking, run_dir / "figures" / "candidate_ranking_summary.png"
    )
    write_warnings(warnings, run_dir / "pipeline_warnings.md")
    _write_execution_status(
        run_dir,
        stage="complete",
        status="completed",
        scientific_conclusion="VALIDATED",
        candidate_generation_decision="completed",
    )
    return PipelineResult("completed", run_dir, validation, ranking)
