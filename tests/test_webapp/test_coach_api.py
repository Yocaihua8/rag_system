from pathlib import Path

import backend.routes.coach as coach_route_module
from backend.api.dispatch import dispatch
from backend.routes.coach import handle_coach_route
from backend.storage import KnowledgeStore


def _project(store: KnowledgeStore, tmp_path: Path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    return store.create_project("知识岛", project_root)


def test_coach_routes_return_analysis_and_views(tmp_path: Path, monkeypatch):
    store = KnowledgeStore(tmp_path / "app.db")
    project = _project(store, tmp_path)
    llm_client = object()
    captured: dict[str, object] = {}

    def fake_analyze(target_store, project_id, llm_client=None):
        captured["store"] = target_store
        captured["project_id"] = project_id
        captured["llm_client"] = llm_client
        return {
            "id": "analysis-1",
            "project_id": project_id,
            "status": "completed",
        }

    monkeypatch.setattr(coach_route_module, "analyze_project", fake_analyze)
    monkeypatch.setattr(
        coach_route_module,
        "build_coach_overview",
        lambda target_store, project_id: {
            "project_id": project_id,
            "analysis": {"id": "analysis-1", "status": "completed"},
        },
    )
    monkeypatch.setattr(
        coach_route_module,
        "build_knowledge_points_view",
        lambda target_store, project_id: {
            "project_id": project_id,
            "analysis": {"id": "analysis-1", "status": "completed"},
            "status": "completed",
            "stale": False,
            "items": [],
            "sources": {},
        },
    )
    monkeypatch.setattr(
        coach_route_module,
        "build_skills_view",
        lambda target_store, project_id: {
            "project_id": project_id,
            "analysis": {"id": "analysis-1", "status": "completed"},
            "status": "completed",
            "stale": False,
            "items": [],
            "sources": {},
        },
    )

    analyze_response = dispatch(
        store,
        "POST",
        "/api/coach/analyze",
        {"project_id": project.id},
        llm_client=llm_client,
    )
    overview_response = dispatch(store, "GET", f"/api/coach/overview?project_id={project.id}")
    points_response = dispatch(store, "GET", f"/api/coach/knowledge-points?project_id={project.id}")
    skills_response = dispatch(store, "GET", f"/api/coach/skills?project_id={project.id}")

    assert analyze_response.status == 200
    assert analyze_response.body["analysis"]["id"] == "analysis-1"
    assert captured == {
        "store": store,
        "project_id": project.id,
        "llm_client": llm_client,
    }
    assert overview_response.status == 200
    assert overview_response.body["overview"]["project_id"] == project.id
    assert points_response.status == 200
    assert points_response.body["knowledge_points"]["items"] == []
    assert skills_response.status == 200
    assert skills_response.body["skills"]["items"] == []


def test_coach_routes_validate_project_id(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    requests = [
        ("POST", "/api/coach/analyze", {}, {}),
        ("GET", "/api/coach/overview", {}, {}),
        ("GET", "/api/coach/knowledge-points", {}, {}),
        ("GET", "/api/coach/skills", {}, {}),
        ("POST", "/api/coach/assessments/start", {}, {}),
        ("POST", "/api/coach/assessments/answer", {}, {}),
        ("GET", "/api/coach/coverage", {}, {}),
    ]
    for method, path, query, payload in requests:
        response = handle_coach_route(store, method, path, query, payload)
        assert response is not None
        assert response.status == 400
        assert response.body == {"error": "project_id is required"}

    unknown_requests = [
        ("POST", "/api/coach/analyze", {}, {"project_id": "missing"}),
        ("GET", "/api/coach/overview", {"project_id": ["missing"]}, {}),
        ("GET", "/api/coach/knowledge-points", {"project_id": ["missing"]}, {}),
        ("GET", "/api/coach/skills", {"project_id": ["missing"]}, {}),
        (
            "POST",
            "/api/coach/assessments/start",
            {},
            {"project_id": "missing"},
        ),
        (
            "POST",
            "/api/coach/assessments/answer",
            {},
            {"project_id": "missing"},
        ),
        ("GET", "/api/coach/coverage", {"project_id": ["missing"]}, {}),
    ]
    for method, path, query, payload in unknown_requests:
        response = handle_coach_route(store, method, path, query, payload)
        assert response is not None
        assert response.status == 404
        assert response.body == {"error": "project not found"}


def test_coach_analyze_uses_configured_default_profile_when_not_injected(
    tmp_path: Path,
    monkeypatch,
):
    store = KnowledgeStore(tmp_path / "app.db")
    project = _project(store, tmp_path)
    configured_client = object()
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        coach_route_module,
        "default_model_profile_client",
        lambda target_store: configured_client,
    )

    def fake_analyze(target_store, project_id, llm_client=None):
        captured.update(
            store=target_store,
            project_id=project_id,
            llm_client=llm_client,
        )
        return {"id": "analysis-1", "status": "completed", "source_ids": [], "sources": {}}

    monkeypatch.setattr(coach_route_module, "analyze_project", fake_analyze)

    response = dispatch(
        store,
        "POST",
        "/api/coach/analyze",
        {"project_id": project.id},
    )

    assert response.status == 200
    assert captured == {
        "store": store,
        "project_id": project.id,
        "llm_client": configured_client,
    }


def test_coach_get_routes_return_not_found_before_analysis(tmp_path: Path, monkeypatch):
    store = KnowledgeStore(tmp_path / "app.db")
    project = _project(store, tmp_path)

    def missing_analysis(target_store, project_id):
        raise ValueError("coach analysis not found")

    monkeypatch.setattr(coach_route_module, "build_coach_overview", missing_analysis)
    monkeypatch.setattr(coach_route_module, "build_knowledge_points_view", missing_analysis)
    monkeypatch.setattr(coach_route_module, "build_skills_view", missing_analysis)

    for path in [
        "/api/coach/overview",
        "/api/coach/knowledge-points",
        "/api/coach/skills",
    ]:
        response = dispatch(store, "GET", f"{path}?project_id={project.id}")
        assert response.status == 404
        assert response.body == {"error": "coach analysis not found"}


def test_coach_get_route_keeps_stale_analysis_available(tmp_path: Path, monkeypatch):
    store = KnowledgeStore(tmp_path / "app.db")
    project = _project(store, tmp_path)
    monkeypatch.setattr(
        coach_route_module,
        "build_coach_overview",
        lambda target_store, project_id: {
            "project_id": project_id,
            "analysis": {"id": "analysis-1", "status": "stale"},
        },
    )

    response = dispatch(store, "GET", f"/api/coach/overview?project_id={project.id}")

    assert response.status == 200
    assert response.body["overview"]["analysis"]["status"] == "stale"


def test_coach_route_only_handles_exact_method_and_path(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    assert handle_coach_route(store, "GET", "/api/coach/analyze", {}, {}) is None
    assert handle_coach_route(store, "POST", "/api/coach/overview", {}, {}) is None
    assert handle_coach_route(store, "GET", "/api/coach/unknown", {}, {}) is None


def test_coach_api_runs_real_analysis_and_returns_resolvable_sources(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = _project(store, tmp_path)
    source = project.root_path / "app.py"
    content = "from fastapi import FastAPI\napp = FastAPI()\n"
    source.write_text(content, encoding="utf-8")
    store.upsert_document(project.id, source, "app.py", content)

    analyze_response = dispatch(
        store,
        "POST",
        "/api/coach/analyze",
        {"project_id": project.id},
    )
    points_response = dispatch(
        store,
        "GET",
        f"/api/coach/knowledge-points?project_id={project.id}",
    )
    skills_response = dispatch(
        store,
        "GET",
        f"/api/coach/skills?project_id={project.id}",
    )

    assert analyze_response.status == 200
    assert analyze_response.body["analysis"]["status"] == "completed"
    assert analyze_response.body["analysis"]["source_ids"]
    assert analyze_response.body["analysis"]["sources"]
    points_view = points_response.body["knowledge_points"]
    assert points_view["status"] == "completed"
    assert points_view["stale"] is False
    assert points_view["items"]
    assert all(item["source_ids"] for item in points_view["items"])
    assert all(
        source_id in points_view["sources"]
        for item in points_view["items"]
        for source_id in item["source_ids"]
    )
    skills_view = skills_response.body["skills"]
    assert skills_view["status"] == "completed"
    assert skills_view["stale"] is False
    mapped = [
        mapping
        for skill in skills_view["items"]
        for mapping in skill["mappings"]
    ]
    assert mapped
    assert all(
        source_id in skills_view["sources"]
        for mapping in mapped
        for source_id in mapping["source_ids"]
    )
