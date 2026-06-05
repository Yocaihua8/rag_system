from fastapi.testclient import TestClient

import backend.knowledge_island.server as server
from backend.knowledge_island.storage import KnowledgeStore


def _client(db_path):
    create_app = getattr(server, "create_app", None)
    assert create_app is not None, "backend.knowledge_island.server.create_app must expose the FastAPI app factory"
    return TestClient(create_app(db_path=db_path))


def test_fastapi_app_exposes_health_check(tmp_path):
    client = _client(tmp_path / "app.db")

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_fastapi_app_serves_static_index(tmp_path, monkeypatch):
    dist_dir = tmp_path / "static_dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text(
        "<!doctype html><title>知识岛</title>",
        encoding="utf-8",
    )
    monkeypatch.setattr(server, "STATIC_DIST_DIR", dist_dir, raising=False)
    client = _client(tmp_path / "app.db")

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "<title>知识岛</title>" in response.text


def test_fastapi_app_returns_json_not_found_for_unknown_api(tmp_path):
    client = _client(tmp_path / "app.db")

    response = client.get("/api/missing")

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == {"error": "not found"}


def test_fastapi_app_streams_answer_as_sse(tmp_path):
    db_path = tmp_path / "app.db"
    project_root = tmp_path / "project"
    project_root.mkdir()
    store = KnowledgeStore(db_path)
    project = store.create_project("知识岛", project_root)
    client = _client(db_path)

    response = client.get(
        "/api/answer/stream",
        params={"project_id": project.id, "question": "什么是知识岛？"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: token" in response.text
    assert "event: done" in response.text


def test_fastapi_openapi_metadata_and_summaries(tmp_path):
    client = _client(tmp_path / "app.db")

    schema = client.get("/openapi.json").json()

    assert schema["info"]["title"] == "知识岛 API"
    assert schema["info"]["version"] == "0.13.0"
    assert "本地优先" in schema["info"]["description"]
    operations = [
        operation
        for path_item in schema["paths"].values()
        for method, operation in path_item.items()
        if method.lower() in {"get", "post", "put", "patch", "delete"}
    ]
    assert operations
    assert all(operation.get("summary") for operation in operations)
