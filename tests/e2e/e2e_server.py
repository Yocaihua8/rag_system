from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import uvicorn
from fastapi import FastAPI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

default_runtime = Path(tempfile.gettempdir()) / "knowledge-island-e2e"
default_runtime.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("KI_DB_PATH", str(default_runtime / "knowledge_island_e2e.db"))

from backend.api.server import create_app  # noqa: E402


server: uvicorn.Server | None = None


def create_e2e_app(db_path: Path) -> FastAPI:
    test_app = FastAPI()

    @test_app.post("/__e2e__/shutdown")
    async def shutdown() -> dict[str, str]:
        if server is not None:
            server.should_exit = True
        return {"status": "shutting_down"}

    test_app.mount("/", create_app(db_path=db_path))
    return test_app


if __name__ == "__main__":
    db_path = Path(os.environ["KI_DB_PATH"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    port = int(os.environ.get("KI_E2E_PORT", "18765"))
    target_app = create_e2e_app(db_path)
    config = uvicorn.Config(target_app, host="127.0.0.1", port=port)
    server = uvicorn.Server(config)
    print(f"Knowledge Island E2E Web is running at http://127.0.0.1:{port}")
    raise SystemExit(0 if server.run() is None else 1)
