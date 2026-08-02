from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.server import create_app  # noqa: E402


server: uvicorn.Server | None = None


def create_e2e_app(v2_db_path: Path, v3_db_path: Path) -> FastAPI:
    test_app = create_app(
        db_path=v2_db_path,
        v3_db_path=v3_db_path,
        enable_v3=True,
    )

    @test_app.post('/__e2e__/shutdown')
    async def shutdown() -> dict[str, str]:
        if server is not None:
            server.should_exit = True
        return {'status': 'shutting_down'}

    return test_app


if __name__ == '__main__':
    v2_db_path = Path(os.environ['KI_V3_E2E_V2_DB_PATH']).resolve()
    v3_db_path = Path(os.environ['KI_V3_E2E_DB_PATH']).resolve()
    v2_db_path.parent.mkdir(parents=True, exist_ok=True)
    v3_db_path.parent.mkdir(parents=True, exist_ok=True)
    port = int(os.environ.get('KI_V3_E2E_PORT', '18766'))
    target_app = create_e2e_app(v2_db_path, v3_db_path)
    config = uvicorn.Config(
        target_app,
        host='127.0.0.1',
        port=port,
        timeout_graceful_shutdown=5,
    )
    server = uvicorn.Server(config)
    print(f'Knowledge Island v3 E2E is running at http://127.0.0.1:{port}')
    raise SystemExit(0 if server.run() is None else 1)
