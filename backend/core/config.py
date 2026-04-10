from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = PROJECT_ROOT / "runtime"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = DATA_DIR / "outputs"
LOGS_DIR = RUNTIME_DIR / "logs"
TEMP_DIR = RUNTIME_DIR / "temp"

REQUIRED_DIRS = [
    RUNTIME_DIR,
    DATA_DIR,
    OUTPUTS_DIR,
    LOGS_DIR,
    TEMP_DIR,
]


def ensure_storage_dirs() -> None:
    for path in REQUIRED_DIRS:
        path.mkdir(parents=True, exist_ok=True)
