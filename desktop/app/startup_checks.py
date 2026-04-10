from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StartupChecks:
    warnings: list[str] = field(default_factory=list)

    @property
    def has_warning(self) -> bool:
        return bool(self.warnings)


def run_startup_checks(*_args, **_kwargs) -> StartupChecks:
    root = Path(__file__).resolve().parents[2]
    runtime_dir = root / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    return StartupChecks()

