from __future__ import annotations

import os
import subprocess
import sys
import time

import pytest
import requests


@pytest.fixture(scope="session")
def live_server(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("e2e") / "test.db"
    env = {
        **os.environ,
        "KI_DB_PATH": str(db_path),
        "KI_VECTOR_BACKEND": "sqlite",
        "PYTHONPATH": os.getcwd(),
    }
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.knowledge_island.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            "18765",
        ],
        env=env,
    )
    base_url = "http://127.0.0.1:18765"
    try:
        for _ in range(30):
            try:
                response = requests.get(f"{base_url}/api/health", timeout=1)
                if response.status_code == 200:
                    break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("live server did not start")
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
