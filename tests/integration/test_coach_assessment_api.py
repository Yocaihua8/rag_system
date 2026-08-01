from __future__ import annotations

from pathlib import Path

from backend.api.dispatch import dispatch
from backend.storage import KnowledgeStore


def _analyzed_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    root = tmp_path / "project"
    root.mkdir()
    project = store.create_project("知识教练", root)
    source = root / "app.py"
    content = "from fastapi import FastAPI\napp = FastAPI()\n"
    source.write_text(content, encoding="utf-8")
    store.upsert_document(project.id, source, "app.py", content)
    analyze = dispatch(
        store,
        "POST",
        "/api/coach/analyze",
        {"project_id": project.id},
    )
    assert analyze.status == 200
    return store, project, root


def test_coach_assessment_api_round_trip_keeps_scoring_basis_server_side(tmp_path):
    store, project, _ = _analyzed_project(tmp_path)
    points = dispatch(
        store,
        "GET",
        f"/api/coach/knowledge-points?project_id={project.id}",
    ).body["knowledge_points"]["items"]
    start = dispatch(
        store,
        "POST",
        "/api/coach/assessments/start",
        {
            "project_id": project.id,
            "target_type": "knowledge_point",
            "target_id": points[0]["id"],
        },
    )

    assert start.status == 200
    session = start.body["session"]
    assert session["questions"]
    assert all("expected_points" not in item for item in session["questions"])
    stored = store.get_coach_assessment_session(project.id, session["id"])
    assert stored is not None
    question = stored.questions[0]
    answer = dispatch(
        store,
        "POST",
        "/api/coach/assessments/answer",
        {
            "project_id": project.id,
            "session_id": session["id"],
            "question_id": question.id,
            "answer": "；".join(question.expected_points),
            "evaluation_mode": "rule",
        },
    )
    coverage = dispatch(
        store,
        "GET",
        f"/api/coach/coverage?project_id={project.id}",
    )
    restored = dispatch(
        store,
        "POST",
        "/api/coach/assessments/start",
        {"project_id": project.id, "session_id": session["id"]},
    )

    assert answer.status == 200
    assert answer.body["result"]["status"] == "mastered"
    assert answer.body["result"]["evaluator"] == "rule"
    assert answer.body["replayed"] is False
    assert coverage.status == 200
    assert coverage.body["coverage"]["summary"]["assessed_count"] == 1
    assert restored.status == 200
    assert restored.body["session"]["resumed"] is True


def test_coach_assessment_api_maps_validation_not_found_and_conflict_statuses(tmp_path):
    store, project, root = _analyzed_project(tmp_path)
    points = store.list_coach_knowledge_points(project.id)
    start = dispatch(
        store,
        "POST",
        "/api/coach/assessments/start",
        {
            "project_id": project.id,
            "target_type": "knowledge_point",
            "target_id": points[0].id,
        },
    )
    session = start.body["session"]
    stored = store.get_coach_assessment_session(project.id, session["id"])
    assert stored is not None

    missing_project = dispatch(
        store,
        "GET",
        "/api/coach/coverage",
    )
    unknown_session = dispatch(
        store,
        "POST",
        "/api/coach/assessments/start",
        {"project_id": project.id, "session_id": "missing"},
    )
    invalid_restart = dispatch(
        store,
        "POST",
        "/api/coach/assessments/start",
        {
            "project_id": project.id,
            "target_type": "knowledge_point",
            "target_id": points[0].id,
            "restart": "yes",
        },
    )
    changed = "from fastapi import FastAPI\napp = FastAPI(title='changed')\n"
    (root / "app.py").write_text(changed, encoding="utf-8")
    store.upsert_document(project.id, root / "app.py", "app.py", changed)
    stale_answer = dispatch(
        store,
        "POST",
        "/api/coach/assessments/answer",
        {
            "project_id": project.id,
            "session_id": session["id"],
            "question_id": stored.questions[0].id,
            "answer": "任意答案",
            "evaluation_mode": "rule",
        },
    )

    assert missing_project.status == 400
    assert missing_project.body == {"error": "project_id is required"}
    assert unknown_session.status == 404
    assert unknown_session.body == {"error": "coach assessment session not found"}
    assert invalid_restart.status == 400
    assert invalid_restart.body == {"error": "restart must be a boolean"}
    assert stale_answer.status == 409
    assert stale_answer.body == {"error": "analysis_stale"}
