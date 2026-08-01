from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.dispatch import dispatch
from backend.api.server import create_app
from backend.storage import KnowledgeStore


def _analyzed_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    root = tmp_path / "project"
    root.mkdir()
    project = store.create_project("学习 API", root)
    source = root / "app.py"
    content = (
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "def health_check():\n"
        "    return {'status': 'ok'}\n"
    )
    source.write_text(content, encoding="utf-8")
    store.upsert_document(project.id, source, "app.py", content)
    analyzed = dispatch(
        store,
        "POST",
        "/api/coach/analyze",
        {"project_id": project.id},
    )
    assert analyzed.status == 200
    points = dispatch(
        store,
        "GET",
        f"/api/coach/knowledge-points?project_id={project.id}",
    ).body["knowledge_points"]["items"]
    assert points
    return store, project, root, points


def _post(store, path: str, payload: dict):
    return dispatch(store, "POST", path, payload)


def _analyzed_sql_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "sql-app.db")
    root = tmp_path / "sql-project"
    root.mkdir()
    project = store.create_project("SQL 学习 API", root)
    source = root / "schema.sql"
    content = (
        "CREATE TABLE tasks (\n"
        "    id INTEGER PRIMARY KEY,\n"
        "    title TEXT NOT NULL,\n"
        "    status TEXT\n"
        ");\n"
    )
    source.write_text(content, encoding="utf-8")
    store.upsert_document(project.id, source, "schema.sql", content)
    analyzed = dispatch(
        store,
        "POST",
        "/api/coach/analyze",
        {"project_id": project.id},
    )
    assert analyzed.status == 200
    points = dispatch(
        store,
        "GET",
        f"/api/coach/knowledge-points?project_id={project.id}",
    ).body["knowledge_points"]["items"]
    assert points
    return store, project, points[0]


def test_coach_learning_api_round_trip_only_exposes_current_exercise(tmp_path):
    store, project, _, points = _analyzed_project(tmp_path)
    started = _post(
        store,
        "/api/coach/learning-sessions/start",
        {
            "project_id": project.id,
            "target_type": "knowledge_point",
            "target_id": points[0]["id"],
        },
    )
    assert started.status == 200
    session = started.body["session"]
    assert session["status"] == "ready"
    assert session["current_exercise"] is None
    assert "steps" not in session

    learning = _post(
        store,
        "/api/coach/learning-sessions/transition",
        {
            "project_id": project.id,
            "session_id": session["id"],
            "expected_version": session["version"],
            "action": "begin_learning",
        },
    )
    awaiting = _post(
        store,
        "/api/coach/learning-sessions/transition",
        {
            "project_id": project.id,
            "session_id": session["id"],
            "expected_version": learning.body["session"]["version"],
            "action": "begin_question",
        },
    )
    assert awaiting.status == 200
    exercise_view = awaiting.body["session"]["current_exercise"]
    assert exercise_view["prompt"]
    assert "expected_points" not in exercise_view
    assert "reference_answer" not in exercise_view

    stored = store.get_coach_learning_session(project.id, session["id"])
    assert stored is not None
    exercise = stored.steps[0].exercises[0]
    answer = "；".join(exercise.expected_points)
    submitted = _post(
        store,
        "/api/coach/learning-sessions/attempts",
        {
            "project_id": project.id,
            "session_id": session["id"],
            "exercise_id": exercise.id,
            "answer": answer,
            "expected_version": awaiting.body["session"]["version"],
            "idempotency_key": "web-attempt-1",
        },
    )
    replayed = _post(
        store,
        "/api/coach/learning-sessions/attempts",
        {
            "project_id": project.id,
            "session_id": session["id"],
            "exercise_id": exercise.id,
            "answer": answer,
            "expected_version": awaiting.body["session"]["version"],
            "idempotency_key": "web-attempt-1",
        },
    )
    idempotency_conflict = _post(
        store,
        "/api/coach/learning-sessions/attempts",
        {
            "project_id": project.id,
            "session_id": session["id"],
            "exercise_id": exercise.id,
            "answer": f"{answer}；不同请求",
            "expected_version": awaiting.body["session"]["version"],
            "idempotency_key": "web-attempt-1",
        },
    )
    restored = dispatch(
        store,
        "GET",
        (
            "/api/coach/learning-sessions/current"
            f"?project_id={project.id}&session_id={session['id']}"
        ),
    )

    assert submitted.status == 200
    assert submitted.body["attempt"]["score"] == 1
    assert submitted.body["session"]["status"] == "evaluated"
    assert submitted.body["replayed"] is False
    assert replayed.status == 200
    assert replayed.body["replayed"] is True
    assert replayed.body["attempt"]["id"] == submitted.body["attempt"]["id"]
    assert idempotency_conflict.status == 409
    assert idempotency_conflict.body["error"] == "idempotency_payload_conflict"
    assert idempotency_conflict.body["session"]["id"] == session["id"]
    assert (
        idempotency_conflict.body["session"]["version"]
        == submitted.body["session"]["version"]
    )
    assert restored.status == 200
    assert restored.body["session"]["id"] == session["id"]
    assert restored.body["session"]["attempts"][0]["answer"] == answer


def test_coach_learning_api_validates_versions_and_stale_sources(tmp_path):
    store, project, root, points = _analyzed_project(tmp_path)
    invalid = _post(
        store,
        "/api/coach/learning-sessions/start",
        {
            "project_id": project.id,
            "target_type": "knowledge_point",
            "target_id": "missing",
        },
    )
    started = _post(
        store,
        "/api/coach/learning-sessions/start",
        {
            "project_id": project.id,
            "target_type": "knowledge_point",
            "target_id": points[0]["id"],
        },
    )
    session = started.body["session"]
    version_conflict = _post(
        store,
        "/api/coach/learning-sessions/transition",
        {
            "project_id": project.id,
            "session_id": session["id"],
            "expected_version": session["version"] + 1,
            "action": "begin_learning",
        },
    )

    changed = "from fastapi import FastAPI\napp = FastAPI(title='changed')\n"
    source = root / "app.py"
    source.write_text(changed, encoding="utf-8")
    store.upsert_document(project.id, source, "app.py", changed)
    stale = _post(
        store,
        "/api/coach/learning-sessions/transition",
        {
            "project_id": project.id,
            "session_id": session["id"],
            "expected_version": session["version"],
            "action": "begin_learning",
        },
    )

    assert invalid.status == 400
    assert invalid.body == {
        "error": "knowledge point does not belong to current analysis"
    }
    assert version_conflict.status == 409
    assert version_conflict.body["error"] == "learning_session_version_conflict"
    assert version_conflict.body["session"]["id"] == session["id"]
    assert stale.status == 409
    assert stale.body["error"] == "analysis_stale"


def test_fastapi_learning_session_completes_sql_retry_over_real_http(tmp_path):
    store, project, point = _analyzed_sql_project(tmp_path)
    client = TestClient(create_app(store=store))

    started_response = client.post(
        "/api/coach/learning-sessions/start",
        json={
            "project_id": project.id,
            "target_type": "knowledge_point",
            "target_id": point["id"],
        },
    )
    assert started_response.status_code == 200
    started = started_response.json()["session"]
    assert started["status"] == "ready"
    assert started["current_exercise"] is None

    learning_response = client.post(
        "/api/coach/learning-sessions/transition",
        json={
            "project_id": project.id,
            "session_id": started["id"],
            "expected_version": started["version"],
            "action": "begin_learning",
        },
    )
    assert learning_response.status_code == 200
    learning = learning_response.json()["session"]
    awaiting_response = client.post(
        "/api/coach/learning-sessions/transition",
        json={
            "project_id": project.id,
            "session_id": started["id"],
            "expected_version": learning["version"],
            "action": "begin_question",
        },
    )
    assert awaiting_response.status_code == 200
    awaiting = awaiting_response.json()["session"]
    exercise = awaiting["current_exercise"]
    assert awaiting["status"] == "awaiting_answer"
    assert exercise["question_type"] == "sql_query"
    assert exercise["sql_fixture"]["schema"][0]["name"] == "tasks"
    assert "expected_rows" not in exercise["sql_fixture"]
    assert "reference_answer" not in exercise

    weak_response = client.post(
        "/api/coach/learning-sessions/attempts",
        json={
            "project_id": project.id,
            "session_id": started["id"],
            "exercise_id": exercise["id"],
            "answer": "SELECT id, title FROM tasks",
            "expected_version": awaiting["version"],
            "idempotency_key": "http-sql-attempt-1",
        },
    )
    assert weak_response.status_code == 200
    weak = weak_response.json()
    assert weak["attempt"]["score"] == 0
    assert weak["attempt"]["feedback"]
    assert weak["session"]["status"] == "evaluated"

    retry_response = client.post(
        "/api/coach/learning-sessions/transition",
        json={
            "project_id": project.id,
            "session_id": started["id"],
            "expected_version": weak["session"]["version"],
            "action": "retry",
        },
    )
    assert retry_response.status_code == 200
    retrying = retry_response.json()["session"]
    assert retrying["status"] == "retrying"
    assert retrying["current_exercise"]["id"] == exercise["id"]

    mastered_response = client.post(
        "/api/coach/learning-sessions/attempts",
        json={
            "project_id": project.id,
            "session_id": started["id"],
            "exercise_id": exercise["id"],
            "answer": (
                "SELECT id, title\n"
                "FROM tasks\n"
                "WHERE status IS NULL"
            ),
            "expected_version": retrying["version"],
            "idempotency_key": "http-sql-attempt-2",
        },
    )
    assert mastered_response.status_code == 200
    mastered = mastered_response.json()
    assert mastered["attempt"]["score"] == 1
    assert mastered["attempt"]["evaluator"] == "sql"
    assert mastered["attempt"]["result_preview"]["rows"]

    completed_response = client.post(
        "/api/coach/learning-sessions/transition",
        json={
            "project_id": project.id,
            "session_id": started["id"],
            "expected_version": mastered["session"]["version"],
            "action": "next",
        },
    )
    assert completed_response.status_code == 200
    completed = completed_response.json()["session"]
    assert completed["status"] == "completed"
    assert completed["outcome"] == "mastered"
    assert completed["read_only"] is True
    assert completed["allowed_actions"] == []

    restored_response = client.get(
        "/api/coach/learning-sessions/current",
        params={
            "project_id": project.id,
            "session_id": started["id"],
        },
    )
    assert restored_response.status_code == 200
    restored = restored_response.json()["session"]
    assert restored["status"] == "completed"
    assert [attempt["attempt_no"] for attempt in restored["attempts"]] == [1, 2]
    assert restored["attempts"][1]["answer"].startswith("SELECT id, title\n")
