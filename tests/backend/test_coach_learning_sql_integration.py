from __future__ import annotations

from pathlib import Path

import pytest

from backend.domain.coach_learning import (
    start_coach_learning_session,
    submit_coach_learning_attempt,
    transition_coach_learning_session,
)
from backend.domain.project_analysis import analyze_project
from backend.storage import KnowledgeStore


def _project_with_source(tmp_path: Path, content: str, filename: str = "schema.sql"):
    store = KnowledgeStore(tmp_path / "app.db")
    root = tmp_path / "project"
    root.mkdir()
    project = store.create_project("SQL 项目学习", root)
    source = root / filename
    source.write_text(content, encoding="utf-8")
    store.upsert_document(project.id, source, filename, content)
    analyze_project(store, project.id)
    point = next(
        point
        for point in store.list_coach_knowledge_points(project.id)
        if any(item.source_path == filename for item in point.sources)
    )
    return store, project, point


def _awaiting(store, project_id: str, point_id: str):
    started = start_coach_learning_session(
        store,
        project_id,
        target_type="knowledge_point",
        target_id=point_id,
    )
    learning = transition_coach_learning_session(
        store,
        project_id,
        started["id"],
        "begin_learning",
        started["version"],
    )
    awaiting = transition_coach_learning_session(
        store,
        project_id,
        started["id"],
        "begin_question",
        learning["version"],
    )
    session = store.get_coach_learning_session(project_id, started["id"])
    assert session is not None
    return started, awaiting, session.steps[0].exercises[0]


def test_parseable_sqlite_ddl_generates_and_grades_project_linked_sql_exercise(
    tmp_path,
):
    store, project, point = _project_with_source(
        tmp_path,
        """
        CREATE TABLE orders (
            id INTEGER NOT NULL,
            customer TEXT NOT NULL,
            total REAL
        );
        """,
    )
    started, awaiting, exercise = _awaiting(store, project.id, point.id)

    assert awaiting["current_exercise"]["question_type"] == "sql_query"
    assert awaiting["current_exercise"]["sql_fixture"]["schema"][0]["name"] == (
        "orders"
    )
    assert awaiting["current_exercise"]["sql_fixture"]["seed_rows"]["orders"]
    assert "expected_rows" not in awaiting["current_exercise"]["sql_fixture"]
    assert "IS NULL" in exercise.reference_answer
    stored = store.get_coach_learning_session(project.id, started["id"])
    assert stored is not None
    assert "COUNT(*)" in stored.steps[0].exercises[1].reference_answer
    answer = exercise.reference_answer
    submitted = submit_coach_learning_attempt(
        store,
        project.id,
        started["id"],
        exercise.id,
        answer,
        awaiting["version"],
        "sql-integration-1",
    )

    assert submitted["attempt"]["score"] == 1
    assert submitted["attempt"]["evaluator"] == "sql"
    assert submitted["attempt"]["result_preview"]["rows"]
    assert len(
        store.list_coach_learning_attempts(project.id, started["id"])
    ) == 1


def test_sql_keywords_without_ddl_do_not_generate_a_sql_course(tmp_path):
    store, project, point = _project_with_source(
        tmp_path,
        "项目可以使用 SQLite 和 SQLAlchemy，但这里没有数据库表结构证据。",
        filename="README.md",
    )
    _, awaiting, _ = _awaiting(store, project.id, point.id)

    assert awaiting["current_exercise"]["question_type"] != "sql_query"
    assert "sql_fixture" not in awaiting["current_exercise"]


def test_text_only_schema_generates_an_order_sensitive_reinforcement(tmp_path):
    store, project, point = _project_with_source(
        tmp_path,
        """
        CREATE TABLE tags (
            code TEXT NOT NULL,
            label TEXT NOT NULL
        );
        """,
    )
    started, _, _ = _awaiting(store, project.id, point.id)
    session = store.get_coach_learning_session(project.id, started["id"])
    assert session is not None
    reinforcement = session.steps[0].exercises[1]
    assert reinforcement.sql_fixture is not None

    assert "ORDER BY" in reinforcement.reference_answer
    assert reinforcement.sql_fixture.order_sensitive is True
    assert "order_by" in reinforcement.sql_fixture.required_semantics["clauses"]


def test_relationship_evidence_generates_a_two_table_join_exercise(tmp_path):
    store, project, point = _project_with_source(
        tmp_path,
        """
        CREATE TABLE teams (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY,
            team_id INTEGER NOT NULL REFERENCES teams(id),
            points INTEGER NOT NULL
        );
        """,
    )
    started, awaiting, exercise = _awaiting(store, project.id, point.id)

    assert "JOIN" in exercise.reference_answer
    assert "GROUP BY" in exercise.reference_answer
    assert exercise.sql_fixture is not None
    assert len(exercise.sql_fixture.schema) == 2
    submitted = submit_coach_learning_attempt(
        store,
        project.id,
        started["id"],
        exercise.id,
        exercise.reference_answer,
        awaiting["version"],
        "sql-join-integration-1",
    )
    assert submitted["attempt"]["score"] == 1


@pytest.mark.parametrize(
    "ddl",
    (
        "CREATE TABLE assets (id INTEGER, payload BLOB);",
        "CREATE TABLE sqlite_shadow (id INTEGER);",
        f"CREATE TABLE {'t' * 65} (id INTEGER);",
    ),
)
def test_unsupported_schema_fails_closed_to_non_sql_exercise(tmp_path, ddl):
    store, project, point = _project_with_source(
        tmp_path,
        ddl,
    )
    _, awaiting, _ = _awaiting(store, project.id, point.id)

    assert awaiting["current_exercise"]["question_type"] != "sql_query"
