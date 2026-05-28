from __future__ import annotations

from pathlib import Path


APP_NAME = "Knowledge Island"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def runtime_dir() -> Path:
    path = Path(__file__).resolve().parents[2] / "runtime" / "knowledge_island"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_db_path() -> Path:
    return runtime_dir() / "knowledge_island.db"
