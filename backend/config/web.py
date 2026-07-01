from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "Knowledge Island"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def runtime_dir() -> Path:
    path = Path(__file__).resolve().parents[2] / "runtime" / "webapp"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_db_path() -> Path:
    override = os.environ.get("KI_DB_PATH")
    if override:
        return Path(override).expanduser()
    return runtime_dir() / "knowledge_island.db"
