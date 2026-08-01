import json
from pathlib import Path
from urllib.error import URLError

from fastapi.testclient import TestClient

import backend.api.server as server
from backend.api.dispatch import dispatch
from backend.storage import KnowledgeStore


class _FakeOllamaResponse:
    def __init__(self, body: dict | None = None, lines: list[dict] | None = None) -> None:
        self._body = body or {}
        self._lines = lines or []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(self._body).encode("utf-8")

    def __iter__(self):
        for line in self._lines:
            yield (json.dumps(line) + "\n").encode("utf-8")


def _client(tmp_path: Path, monkeypatch) -> TestClient:
    dist_dir = tmp_path / "static_dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<!doctype html><title>Knowledge Island</title>", encoding="utf-8")
    monkeypatch.setattr(server, "STATIC_DIST_DIR", dist_dir, raising=False)
    return TestClient(server.create_app(db_path=tmp_path / "app.db"))


def test_ollama_status_returns_availability_models_and_recommendations(tmp_path: Path, monkeypatch):
    def opener(request, timeout):
        assert request.full_url == "http://localhost:11434/api/tags"
        return _FakeOllamaResponse(
            {
                "models": [
                    {"name": "qwen2.5:7b", "size": 4680000000},
                    {"name": "nomic-embed-text:latest", "size": 274000000},
                ]
            }
        )

    monkeypatch.setattr("backend.providers.llm.ollama.urlopen", opener)
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(store, "GET", "/api/ollama/status")

    assert response.status == 200
    assert response.body["available"] is True
    assert response.body["host"] == "http://localhost:11434"
    assert response.body["models"] == ["qwen2.5:7b", "nomic-embed-text:latest"]
    assert response.body["recommended_models"] == [
        {"model": "qwen2.5:3b", "label": "轻量 CPU 可用", "size_hint": "~2GB"},
        {"model": "qwen2.5:7b", "label": "均衡推荐", "size_hint": "~5GB"},
        {"model": "deepseek-r1:8b", "label": "推理增强", "size_hint": "~5GB"},
    ]


def test_ollama_status_handles_unavailable_service_without_crashing(tmp_path: Path, monkeypatch):
    def opener(request, timeout):
        raise URLError("connection refused")

    monkeypatch.setattr("backend.providers.llm.ollama.urlopen", opener)
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(store, "GET", "/api/ollama/status")

    assert response.status == 200
    assert response.body["available"] is False
    assert response.body["models"] == []
    assert "connection refused" in response.body["error"]


def test_ollama_pull_streams_progress_as_sse(tmp_path: Path, monkeypatch):
    def opener(request, timeout):
        assert request.full_url == "http://localhost:11434/api/pull"
        payload = json.loads(request.data.decode("utf-8"))
        assert payload == {"model": "qwen2.5:3b", "stream": True}
        return _FakeOllamaResponse(
            lines=[
                {"status": "pulling manifest"},
                {"status": "pulling layer", "total": 100, "completed": 25},
                {"status": "success"},
            ]
        )

    monkeypatch.setattr("backend.providers.llm.ollama.urlopen", opener)
    client = _client(tmp_path, monkeypatch)

    with client.stream("POST", "/api/ollama/pull", json={"model": "qwen2.5:3b"}) as response:
        body = response.read().decode("utf-8")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert 'event: progress\ndata: {"status": "pulling manifest", "model": "qwen2.5:3b"}' in body
    assert (
        'event: progress\ndata: {"status": "pulling layer", "model": "qwen2.5:3b", '
        '"completed": 25, "total": 100, "progress": 0.25}'
    ) in body
    assert 'event: done\ndata: {"status": "done", "model": "qwen2.5:3b"}' in body


def test_ollama_pull_rejects_models_outside_recommended_whitelist(tmp_path: Path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    response = client.post("/api/ollama/pull", json={"model": "unknown:latest"})

    assert response.status_code == 400
    assert response.json() == {"error": "model is not in the recommended first-run list"}
