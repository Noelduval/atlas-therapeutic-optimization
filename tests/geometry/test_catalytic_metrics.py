from pathlib import Path

import pandas as pd
import pytest

from atlas.geometry.catalytic_metrics import measure_geometry, measure_many
from atlas.structure.mutate import build_known_mutants
from atlas.structure.reconstruct import reconstruct_active_like


SOURCE = Path(__file__).parents[2] / "data" / "23WN.cif"


@pytest.fixture()
def benchmark(tmp_path):
    reconstructed = tmp_path / "active_like.pdb"
    reconstruct_active_like(SOURCE, reconstructed, tmp_path / "map.csv")
    manifest = build_known_mutants(reconstructed, tmp_path / "known")
    return reconstructed, manifest


def test_static_geometry_matches_deposited_metal_connections(benchmark) -> None:
    reconstructed, _ = benchmark
    record = measure_geometry(reconstructed, reference_pdb=reconstructed, variant_id="WT")
    assert record.zn_scissile_oxygen_distance_a == pytest.approx(2.287, abs=0.002)
    assert record.zn_h95_ne2_distance_a == pytest.approx(2.301, abs=0.002)
    assert record.zn_h99_ne2_distance_a == pytest.approx(2.304, abs=0.002)
    assert record.zn_e122_oxygen_distance_a == pytest.approx(2.017, abs=0.002)
    assert record.active_site_rmsd_a == pytest.approx(0.0, abs=1e-6)
    assert record.substrate_rmsd_a == pytest.approx(0.0, abs=1e-6)
    assert record.substrate_pose_drift_a == pytest.approx(0.0, abs=1e-6)
    assert record.geometry_complete is True
    assert record.warnings == ()


def test_h172a_reports_missing_functional_atom_instead_of_imputing_metric(benchmark) -> None:
    reconstructed, manifest = benchmark
    h172a = Path(manifest.loc[manifest["variant_id"] == "H172A", "pdb_path"].iloc[0])
    record = measure_geometry(h172a, reference_pdb=reconstructed, variant_id="H172A")
    assert record.h172_to_scissile_oxygen_distance_a is None
    assert record.geometry_complete is False
    assert any("H172 NE2" in warning for warning in record.warnings)


def test_measure_many_writes_stable_schema(benchmark, tmp_path) -> None:
    reconstructed, manifest = benchmark
    variants = {
        row.variant_id: Path(row.pdb_path) for row in manifest.itertuples(index=False)
    }
    output = tmp_path / "geometry_metrics.csv"
    table = measure_many(variants, reconstructed, output)
    assert output.is_file()
    assert len(table) == 5
    assert pd.read_csv(output).columns.tolist() == [
        "variant_id",
        "zn_scissile_oxygen_distance_a",
        "zn_h95_ne2_distance_a",
        "zn_h99_ne2_distance_a",
        "zn_e122_oxygen_distance_a",
        "e96_to_scissile_carbonyl_distance_a",
        "active_site_rmsd_a",
        "substrate_rmsd_a",
        "h172_to_scissile_oxygen_distance_a",
        "y91_d126_pocket_distance_a",
        "substrate_pose_drift_a",
        "clamp_distance_a",
        "geometry_complete",
        "warnings",
    ]
