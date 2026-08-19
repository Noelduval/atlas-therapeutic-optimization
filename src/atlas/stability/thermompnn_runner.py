"""Official ThermoMPNN single-mutant inference adapter."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Sequence

import pandas as pd

from atlas.stability.common import (
    CommandRunner,
    ScientificOutputError,
    StabilityVariant,
    default_command_runner,
    normalized_frame,
    normalized_row,
    require_columns,
    require_repository,
    require_revision,
)


THERMOMPNN_REVISION = "2b04fd370e399911b1fa5848112cc9013f084110"


class ThermoMPNNRunner:
    """Run the official exhaustive single-site model and select requested rows."""

    def __init__(
        self,
        repository: str | Path,
        *,
        command_runner: CommandRunner = default_command_runner,
    ) -> None:
        self.repository = Path(repository)
        self.command_runner = command_runner

    def run(
        self,
        pdb_path: str | Path,
        variants: Sequence[StabilityVariant],
        output_dir: str | Path,
    ) -> pd.DataFrame:
        script = require_repository(
            self.repository, "analysis/custom_inference.py", "ThermoMPNN"
        )
        require_revision(self.repository, THERMOMPNN_REVISION, "ThermoMPNN")
        pdb = Path(pdb_path).resolve()
        destination = Path(output_dir).resolve()
        destination.mkdir(parents=True, exist_ok=True)
        command = [
            sys.executable,
            str(script),
            "--pdb",
            str(pdb),
            "--chain",
            "A",
            "--out_dir",
            str(destination),
        ]
        completed = self.command_runner(command, cwd=self.repository)
        if completed.returncode:
            detail = (completed.stderr or completed.stdout or "unknown error").strip()
            raise ScientificOutputError(f"ThermoMPNN inference failed: {detail}")

        csv_path = destination / f"ThermoMPNN_inference_{pdb.stem}.csv"
        if not csv_path.is_file():
            raise ScientificOutputError(
                f"ThermoMPNN completed without expected output {csv_path}"
            )
        frame = pd.read_csv(csv_path)
        require_columns(
            frame, {"ddG_pred", "position", "wildtype", "mutation"}, "ThermoMPNN"
        )

        lookup: dict[str, float] = {}
        for row in frame.itertuples(index=False):
            label = f"{row.wildtype}{int(row.position)}{row.mutation}"
            lookup[label] = float(row.ddG_pred)
        rows: list[dict[str, object]] = []
        for variant in variants:
            if ":" in variant.mutation_set or ";" in variant.mutation_set:
                raise ScientificOutputError(
                    f"ThermoMPNN single-mutant adapter cannot score {variant.mutation_set}"
                )
            if variant.mutation_set not in lookup:
                raise ScientificOutputError(
                    f"ThermoMPNN output does not contain requested mutation {variant.mutation_set}"
                )
            rows.append(
                normalized_row(
                    variant, "ThermoMPNN", lookup[variant.mutation_set]
                )
            )
        result = normalized_frame(rows)
        result.to_csv(destination / "thermompnn_scores_normalized.csv", index=False)
        return result
