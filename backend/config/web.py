from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from backend.config.settings import load_backend_env, load_settings


APP_NAME = "Knowledge Island"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_CORS_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5174",
    "http://localhost:5174",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
    "http://127.0.0.1:4174",
    "http://localhost:4174",
    "tauri://localhost",
    "http://tauri.localhost",
)
CORS_ALLOWED_METHODS = ("GET", "POST", "OPTIONS")
CORS_ALLOWED_HEADERS = (
    "Authorization",
    "Content-Type",
    "Idempotency-Key",
    "Last-Event-ID",
    "X-API-Key",
    "X-Request-ID",
)


def cors_origins(environ: Mapping[str, str] | None = None) -> tuple[str, ...]:
    if environ is None:
        values: Mapping[str, str] = {**load_backend_env(), **os.environ}
    else:
        values = environ
    configured = str(values.get("KI_CORS_ORIGINS", "")).strip()
    if not configured:
        return DEFAULT_CORS_ORIGINS

    origins = tuple(
        dict.fromkeys(
            origin.strip().rstrip("/")
            for origin in configured.split(",")
            if origin.strip()
        )
    )
    if any("*" in origin for origin in origins):
        raise ValueError("KI_CORS_ORIGINS must list explicit origins; wildcard '*' is not allowed")
    return origins


def runtime_dir() -> Path:
    path = load_settings().runtime_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_db_path() -> Path:
    override = os.environ.get("KI_DB_PATH") or load_backend_env().get("KI_DB_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return load_settings().db_path
