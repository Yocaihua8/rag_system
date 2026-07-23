from __future__ import annotations

import os
from pathlib import Path

from backend.config.settings import load_settings


APP_NAME = "Knowledge Island"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def runtime_dir() -> Path:
    path = load_settings().runtime_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_db_path() -> Path:
    override = os.environ.get("KI_DB_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return load_settings().db_path
