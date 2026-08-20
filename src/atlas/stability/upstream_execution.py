"""Subprocess-scoped Python execution for pinned upstream model checkouts."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys
from typing import Mapping, Sequence


@dataclass(frozen=True)
class UpstreamPythonExecution:
    """Define one checkout-first Python subprocess boundary."""

    repository: Path
    script: Path
    python_executable: Path

    @classmethod
    def create(
        cls,
        repository: str | Path,
        script: str | Path,
        *,
        python_executable: str | Path = sys.executable,
    ) -> UpstreamPythonExecution:
        checkout = Path(repository).resolve()
        script_path = Path(script)
        if not script_path.is_absolute():
            script_path = checkout / script_path
        python_path = Path(python_executable).expanduser()
        if not python_path.is_absolute():
            python_path = Path.cwd() / python_path
        return cls(
            repository=checkout,
            script=script_path.resolve(),
            python_executable=python_path,
        )

    @property
    def cwd(self) -> Path:
        return self.repository

    def environment(
        self, inherited: Mapping[str, str] | None = None
    ) -> dict[str, str]:
        environment = dict(os.environ if inherited is None else inherited)
        existing = environment.get("PYTHONPATH", "")
        existing_entries = [entry for entry in existing.split(os.pathsep) if entry]
        checkout = str(self.repository)
        environment["PYTHONPATH"] = os.pathsep.join(
            [checkout, *(entry for entry in existing_entries if entry != checkout)]
        )
        return environment

    def python_command(self, arguments: Sequence[str]) -> list[str]:
        return [str(self.python_executable), *(str(argument) for argument in arguments)]

    def script_command(self, arguments: Sequence[str]) -> list[str]:
        return self.python_command([str(self.script), *arguments])
