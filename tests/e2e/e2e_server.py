from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

default_runtime = Path(tempfile.gettempdir()) / "knowledge-island-e2e"
default_runtime.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("KI_DB_PATH", str(default_runtime / "knowledge_island_e2e.db"))

from backend.api.server import run_server  # noqa: E402


if __name__ == "__main__":
    db_path = Path(os.environ["KI_DB_PATH"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    port = int(os.environ.get("KI_E2E_PORT", "18765"))
    raise SystemExit(run_server(host="127.0.0.1", port=port, db_path=db_path))
