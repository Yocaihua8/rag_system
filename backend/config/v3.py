"""Configuration for the isolated v3 Agent runtime."""
from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from backend.config.settings import load_backend_env


V3_DATA_GENERATION = "v3"
DEFAULT_MAX_CONCURRENCY = 2
DEFAULT_LEASE_SECONDS = 30
DEFAULT_POLL_INTERVAL_MS = 100
DEFAULT_BACKUP_RETENTION = 7


@dataclass(frozen=True)
class V3RuntimeSettings:
    data_root: Path
    db_path: Path
    vector_dir: Path
    artifacts_dir: Path
    logs_dir: Path
    backups_dir: Path
    max_concurrency: int
    lease_seconds: int
    poll_interval_ms: int
    backup_retention: int = DEFAULT_BACKUP_RETENTION


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_v3_settings(
    override_env: Mapping[str, str] | None = None,
) -> V3RuntimeSettings:
    """Load v3-only settings without consulting legacy RAG runtime paths."""

    values: dict[str, str] = {}
    values.update(load_backend_env())
    values.update(os.environ)
    if override_env:
        values.update({str(key): str(value) for key, value in override_env.items()})

    data_root = Path(
        _non_empty(values.get("KI_DATA_ROOT"))
        or _project_root() / "runtime" / "v3"
    ).expanduser().resolve()
    db_override = _non_empty(values.get("KI_V3_DB_PATH"))
    db_path = (
        Path(db_override).expanduser().resolve()
        if db_override
        else data_root / "app.db"
    )

    max_concurrency = _bounded_int(
        values.get("KI_AGENT_MAX_CONCURRENCY"),
        default=DEFAULT_MAX_CONCURRENCY,
        minimum=1,
        maximum=2,
        name="KI_AGENT_MAX_CONCURRENCY",
    )
    lease_seconds = _bounded_int(
        values.get("KI_AGENT_LEASE_SECONDS"),
        default=DEFAULT_LEASE_SECONDS,
        minimum=5,
        maximum=3600,
        name="KI_AGENT_LEASE_SECONDS",
    )
    poll_interval_ms = _bounded_int(
        values.get("KI_AGENT_POLL_INTERVAL_MS"),
        default=DEFAULT_POLL_INTERVAL_MS,
        minimum=10,
        maximum=60_000,
        name="KI_AGENT_POLL_INTERVAL_MS",
    )
    backup_retention = _bounded_int(
        values.get("KI_V3_BACKUP_RETENTION"),
        default=DEFAULT_BACKUP_RETENTION,
        minimum=1,
        maximum=100,
        name="KI_V3_BACKUP_RETENTION",
    )

    return V3RuntimeSettings(
        data_root=data_root,
        db_path=db_path,
        vector_dir=data_root / "vectors",
        artifacts_dir=data_root / "artifacts",
        logs_dir=data_root / "logs",
        backups_dir=data_root / "backups",
        max_concurrency=max_concurrency,
        lease_seconds=lease_seconds,
        poll_interval_ms=poll_interval_ms,
        backup_retention=backup_retention,
    )


def ensure_v3_runtime_dirs(settings: V3RuntimeSettings) -> None:
    for path in (
        settings.data_root,
        settings.db_path.parent,
        settings.vector_dir,
        settings.artifacts_dir,
        settings.logs_dir,
        settings.backups_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def _non_empty(value: object) -> str:
    return str(value or "").strip()


def _bounded_int(
    value: object,
    *,
    default: int,
    minimum: int,
    maximum: int,
    name: str,
) -> int:
    raw = str(value or "").strip()
    if not raw:
        return default
    try:
        parsed = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed < minimum or parsed > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed


__all__ = [
    "DEFAULT_LEASE_SECONDS",
    "DEFAULT_BACKUP_RETENTION",
    "DEFAULT_MAX_CONCURRENCY",
    "DEFAULT_POLL_INTERVAL_MS",
    "V3_DATA_GENERATION",
    "V3RuntimeSettings",
    "ensure_v3_runtime_dirs",
    "load_v3_settings",
]
