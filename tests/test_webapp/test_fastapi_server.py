from fastapi.testclient import TestClient

import webapp.server as server
from webapp.storage import KnowledgeStore


def _client(db_path):
    create_app = getattr(server, "create_app", None)
    assert create_app is not None, "webapp.server.create_app must expose the FastAPI app factory"
    return TestClient(create_app(db_path=db_path))


def test_fastapi_app_exposes_health_check(tmp_path):
    client = _client(tmp_path / "app.db")

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_fastapi_app_serves_static_index(tmp_path):
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


def test_fastapi_openapi_schema_documents_web_mvp_api_paths(tmp_path):
    client = _client(tmp_path / "app.db")

    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["openapi"].startswith("3.")
    assert schema["info"]["title"] == "Knowledge Island"
    operations = {
        (path, method)
        for path, methods in schema["paths"].items()
        for method in methods
        if method in {"get", "post"}
    }
    assert len(operations) >= 63
    for operation in [
        ("/api/health", "get"),
        ("/api/projects", "get"),
        ("/api/projects", "post"),
        ("/api/model-profiles", "get"),
        ("/api/model-profiles", "post"),
        ("/api/search", "post"),
        ("/api/answer", "post"),
        ("/api/answer/compare", "post"),
        ("/api/answer/stream", "get"),
        ("/api/agent/tools/run", "post"),
        ("/api/assessment/library", "get"),
        ("/api/assessment/start", "post"),
    ]:
        assert operation in operations
    compare_operation = schema["paths"]["/api/answer/compare"]["post"]
    assert compare_operation["summary"] == "Compare answers from two model profiles"
    assert "requestBody" in compare_operation
    assert "responses" in compare_operation


def test_fastapi_swagger_ui_loads_local_openapi_schema(tmp_path):
    client = _client(tmp_path / "app.db")

    response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text
    assert "/openapi.json" in response.text
