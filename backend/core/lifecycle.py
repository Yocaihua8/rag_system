from __future__ import annotations

from backend.core.config import ensure_storage_dirs
from backend.infra.storage.db.sqlite import init_runtime_db


def startup() -> None:
    ensure_storage_dirs()
    init_runtime_db()
