from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from backend.storage import KnowledgeStore


def _add_coach_fixture(store: KnowledgeStore, tmp_path: Path, name: str):
    project_root = tmp_path / name
    project_root.mkdir()
    project = store.create_project(name, project_root)
    document = store.upsert_document(
        project.id,
        project_root / "README.md",
        "README.md",
        "默认入口是 app.py，并由 FastAPI 提供本地服务。",
    ).document
    chunk = store.list_chunks(project.id)[0]
    run = store.create_coach_analysis_run(
        project.id,
        "rules-v1",
        f"fingerprint-{name}",
    )
    store.save_coach_analysis_result(
        run.id,
        {
            "source_count": 1,
            "knowledge_point_count": 1,
            "skill_mapping_count": 1,
        },
        [
            {
                "stable_key": "architecture:web-entry",
                "title": "Web 入口",
                "category": "architecture",
                "summary": "app.py 启动 FastAPI 服务。",
                "sources": [
                    {
                        "document_id": document.id,
                        "chunk_id": chunk.id,
                        "source_path": document.relative_path,
                        "source_hash": document.checksum,
                        "excerpt": "默认入口是 app.py",
                        "locator": {"line_start": 1, "line_end": 1},
                    }
                ],
            }
        ],
        {"version": "v1", "name": "通用开发技能树", "status": "active"},
        [
            {
                "stable_key": "delivery",
                "name": "交付",
                "category": "delivery",
                "sort_order": 0,
            },
            {
                "stable_key": "delivery:web-runtime",
                "parent_key": "delivery",
                "name": "Web 运行时",
                "category": "delivery",
                "sort_order": 1,
            },
        ],
        [
            {
                "knowledge_point_key": "architecture:web-entry",
                "skill_key": "delivery:web-runtime",
                "confidence": 0.9,
                "rationale": "入口说明运行方式。",
                "source_path": document.relative_path,
                "source_hash": document.checksum,
            }
        ],
    )
    point = store.list_coach_knowledge_points(project.id)[0]
    skill = next(
        node
        for node in store.list_coach_skill_nodes()
        if node.stable_key == "delivery:web-runtime"
    )
    return project, run, point, skill, point.sources[0]


def _step_draft(point_id: str, source_id: str) -> dict[str, object]:
    return {
        "knowledge_point_id": point_id,
        "title": "理解 Web 入口",
        "explanation": "结合项目入口说明 FastAPI 的启动位置。",
        "source_ids": [source_id],
        "completion_threshold": 0.75,
        "max_attempts": 3,
        "sort_order": 0,
        "exercises": [
            {
                "variant": "primary",
                "question_type": "concept",
                "prompt": "项目默认入口和服务框架是什么？",
                "expected_points": ["app.py", "FastAPI"],
                "reference_answer": "默认入口是 app.py，服务框架是 FastAPI。",
                "sort_order": 0,
            },
            {
                "variant": "reinforcement",
                "question_type": "sql_query",
                "prompt": "查询启用的服务名称。",
                "expected_points": [],
                "reference_answer": "SELECT name FROM services WHERE enabled = 1",
                "sort_order": 1,
                "sql_fixture": {
                    "schema": [
                        {
                            "name": "services",
                            "columns": [
                                {"name": "name", "type": "TEXT"},
                                {"name": "enabled", "type": "INTEGER"},
                            ],
                        }
                    ],
                    "seed_rows": {
                        "services": [
                            {"name": "api", "enabled": 1},
                            {"name": "worker", "enabled": 0},
                        ]
                    },
                    "expected_columns": ["name"],
                    "expected_rows": [["api"]],
                    "order_sensitive": False,
                    "required_semantics": {
                        "tables": ["services"],
                        "clauses": ["where"],
                    },
                    "limits": {"max_rows": 200, "max_bytes": 262144},
                    "fixture_hash": "fixture-web-entry-v1",
                },
            },
        ],
    }


def test_learning_schema_adds_six_tables_without_changing_legacy_tables(
    tmp_path: Path,
):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)

    with sqlite3.connect(store.db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        active_index_sql = conn.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type = 'index' AND name = 'uq_coach_learning_active_run'
            """
        ).fetchone()[0]
        answer_columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(coach_assessment_answers)"
            ).fetchall()
        }

    assert {
        "coach_learning_sessions",
        "coach_learning_steps",
        "coach_learning_step_sources",
        "coach_learning_exercises",
        "coach_sql_exercise_fixtures",
        "coach_learning_attempts",
    } <= tables
    assert {
        "coach_assessment_sessions",
        "coach_assessment_questions",
        "coach_assessment_answers",
        "coach_assessment_results",
        "coach_learning_plans",
        "coach_learning_plan_items",
    } <= tables
    assert "status IN" in active_index_sql
    assert answer_columns == {
        "id",
        "session_id",
        "question_id",
        "answer",
        "created_at",
    }


def test_learning_session_round_trip_uses_structured_snapshots_and_hides_scoring(
    tmp_path: Path,
):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    project, run, point, _, source = _add_coach_fixture(store, tmp_path, "A")

    created = store.create_coach_learning_session(
        project.id,
        run.id,
        "knowledge_point",
        point.id,
        [_step_draft(point.id, source.id)],
        origin_type="learning_map",
    )
    loaded = store.get_coach_learning_session(project.id, created.id)
    active = store.get_active_coach_learning_session(project.id, run.id)

    assert loaded == created
    assert active == created
    assert created.status == "ready"
    assert created.version == 1
    assert created.current_step_id == created.steps[0].id
    assert created.steps[0].source_ids == (source.id,)
    assert [item.variant for item in created.steps[0].exercises] == [
        "primary",
        "reinforcement",
    ]
    sql_fixture = created.steps[0].exercises[1].sql_fixture
    assert sql_fixture is not None
    assert sql_fixture.schema[0]["name"] == "services"
    assert sql_fixture.seed_rows["services"][0]["name"] == "api"
    assert sql_fixture.expected_rows == (("api",),)

    public = created.to_dict()
    public_fixture = sql_fixture.to_dict()
    assert public["current_exercise"] is None
    assert "expected_columns" not in public_fixture
    assert "expected_rows" not in public_fixture

    scoring = created.to_dict(include_scoring_basis=True)
    scoring_sql = scoring["steps"][0]["exercises"][1]
    assert scoring_sql["reference_answer"].startswith("SELECT")
    assert scoring_sql["sql_fixture"]["expected_rows"] == [["api"]]


def test_learning_attempts_are_append_only_idempotent_and_versioned(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    project, run, point, _, source = _add_coach_fixture(store, tmp_path, "A")
    session = store.create_coach_learning_session(
        project.id,
        run.id,
        "knowledge_point",
        point.id,
        [_step_draft(point.id, source.id)],
    )
    exercise = session.steps[0].exercises[0]

    first, reserved, replayed = store.reserve_coach_learning_attempt(
        project.id,
        session.id,
        exercise.id,
        "app.py 使用 FastAPI",
        session.version,
        "submission-1",
        "hash-1",
    )
    replay, replay_session, replayed_again = store.reserve_coach_learning_attempt(
        project.id,
        session.id,
        exercise.id,
        "app.py 使用 FastAPI",
        session.version,
        "submission-1",
        "hash-1",
    )

    assert first.attempt_no == 1
    assert first.status == "grading"
    assert reserved.version == 2
    assert replay.id == first.id
    assert replay_session.version == reserved.version
    assert replayed is False
    assert replayed_again is True

    with pytest.raises(ValueError, match="learning_attempt_idempotency_conflict"):
        store.reserve_coach_learning_attempt(
            project.id,
            session.id,
            exercise.id,
            "different payload",
            reserved.version,
            "submission-1",
            "different-hash",
        )

    evaluated, finalized, plan_sync = store.finalize_coach_learning_attempt(
        project.id,
        session.id,
        first.id,
        reserved.version,
        evaluator="rule",
        score=0.4,
        confidence=1.0,
        feedback="缺少完整入口说明。",
        scoring_details={"missing_points": ["FastAPI"]},
        counts_for_mastery=True,
    )
    second, second_reserved, second_replayed = store.reserve_coach_learning_attempt(
        project.id,
        session.id,
        exercise.id,
        "默认入口是 app.py，框架是 FastAPI。",
        finalized.version,
        "submission-2",
        "hash-2",
    )

    assert evaluated.status == "evaluated"
    assert evaluated.score == 0.4
    assert evaluated.scoring_details == {"missing_points": ["FastAPI"]}
    assert finalized.status == "evaluated"
    assert plan_sync == "not_linked"
    assert second.attempt_no == 2
    assert second_reserved.version == finalized.version + 1
    assert second_replayed is False
    assert [item.id for item in store.list_coach_learning_attempts(
        project.id,
        session.id,
    )] == [first.id, second.id]


def test_learning_storage_rejects_stale_versions_and_cross_scope_references(
    tmp_path: Path,
):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    project_a, run_a, point_a, _, source_a = _add_coach_fixture(
        store,
        tmp_path,
        "A",
    )
    project_b, _, point_b, _, source_b = _add_coach_fixture(
        store,
        tmp_path,
        "B",
    )

    with pytest.raises(ValueError, match="knowledge point does not belong"):
        store.create_coach_learning_session(
            project_a.id,
            run_a.id,
            "knowledge_point",
            point_a.id,
            [_step_draft(point_b.id, source_b.id)],
        )
    with pytest.raises(ValueError, match="source.*analysis run"):
        store.create_coach_learning_session(
            project_a.id,
            run_a.id,
            "knowledge_point",
            point_a.id,
            [_step_draft(point_a.id, source_b.id)],
        )
    with sqlite3.connect(store.db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            INSERT INTO coach_analysis_runs
                (id, project_id, analyzer_version, source_fingerprint,
                 status, summary_json, started_at, finished_at)
            VALUES (
                'other-run', ?, 'rules-v1', 'other-fingerprint',
                'completed', '{}', '2026-01-01T00:00:00+00:00',
                '2026-01-01T00:00:01+00:00'
            )
            """,
            (project_a.id,),
        )
        conn.execute(
            """
            INSERT INTO coach_knowledge_sources
                (id, run_id, knowledge_point_id, document_id, source_path,
                 chunk_id, source_hash, excerpt, locator_json)
            VALUES (
                'other-run-source', 'other-run', ?, NULL, 'README.md',
                NULL, 'other-hash', '另一次分析来源', '{}'
            )
            """,
            (point_a.id,),
        )
    with pytest.raises(ValueError, match="source.*analysis run"):
        store.create_coach_learning_session(
            project_a.id,
            run_a.id,
            "knowledge_point",
            point_a.id,
            [_step_draft(point_a.id, "other-run-source")],
        )

    session = store.create_coach_learning_session(
        project_a.id,
        run_a.id,
        "knowledge_point",
        point_a.id,
        [_step_draft(point_a.id, source_a.id)],
    )
    with pytest.raises(ValueError, match="learning_session_version_conflict"):
        store.transition_coach_learning_session(
            project_a.id,
            session.id,
            session.version + 1,
            "learning",
        )
    assert store.get_coach_learning_session(project_b.id, session.id) is None


def test_only_one_non_terminal_learning_session_exists_per_project_run(
    tmp_path: Path,
):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    project, run, point, skill, source = _add_coach_fixture(store, tmp_path, "A")
    created = store.create_coach_learning_session(
        project.id,
        run.id,
        "knowledge_point",
        point.id,
        [_step_draft(point.id, source.id)],
    )

    with pytest.raises(ValueError, match="learning_session_active_conflict"):
        store.create_coach_learning_session(
            project.id,
            run.id,
            "skill",
            skill.id,
            [_step_draft(point.id, source.id)],
        )

    abandoned = store.transition_coach_learning_session(
        project.id,
        created.id,
        created.version,
        "abandoned",
    )
    restarted = store.create_coach_learning_session(
        project.id,
        run.id,
        "skill",
        skill.id,
        [_step_draft(point.id, source.id)],
    )

    assert abandoned.abandoned_at
    assert restarted.id != created.id


def test_learning_session_listing_is_project_scoped_and_newest_first(
    tmp_path: Path,
):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    project_a, run_a, point_a, _, source_a = _add_coach_fixture(
        store,
        tmp_path,
        "A",
    )
    project_b, _, _, _, _ = _add_coach_fixture(store, tmp_path, "B")
    first = store.create_coach_learning_session(
        project_a.id,
        run_a.id,
        "knowledge_point",
        point_a.id,
        [_step_draft(point_a.id, source_a.id)],
    )
    store.transition_coach_learning_session(
        project_a.id,
        first.id,
        first.version,
        "abandoned",
    )
    second = store.create_coach_learning_session(
        project_a.id,
        run_a.id,
        "knowledge_point",
        point_a.id,
        [_step_draft(point_a.id, source_a.id)],
    )

    listed = store.list_coach_learning_sessions(project_a.id)

    assert [session.id for session in listed] == [second.id, first.id]
    assert store.list_coach_learning_sessions(project_a.id, limit=1) == [second]
    assert store.list_coach_learning_sessions(project_b.id) == []


def test_learning_session_rows_follow_project_cascade_delete(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    project, run, point, _, source = _add_coach_fixture(store, tmp_path, "A")
    store.create_coach_learning_session(
        project.id,
        run.id,
        "knowledge_point",
        point.id,
        [_step_draft(point.id, source.id)],
    )

    assert store.delete_project(project.id) is True
    with sqlite3.connect(store.db_path) as conn:
        counts = [
            conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "coach_learning_sessions",
                "coach_learning_steps",
                "coach_learning_step_sources",
                "coach_learning_exercises",
                "coach_learning_attempts",
            )
        ]
    assert counts == [0, 0, 0, 0, 0]


def test_attempt_finalization_advances_only_the_linked_confirmed_plan_item(
    tmp_path: Path,
):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    project, run, point, skill, source = _add_coach_fixture(
        store,
        tmp_path,
        "A",
    )
    plan = store.create_coach_learning_plan(
        project.id,
        run.id,
        [
            {
                "stable_key": "learn:web-entry",
                "item_type": "learning",
                "objective": "掌握 Web 入口",
                "knowledge_point_id": point.id,
                "skill_node_id": skill.id,
                "source_ids": [source.id],
                "practice_question": "说明入口。",
                "completion_criteria": "正确说明入口。",
                "estimated_minutes": 20,
                "status": "todo",
                "sort_order": 0,
            }
        ],
    )
    confirmed = store.confirm_coach_learning_plan(project.id, plan.id)
    session = store.create_coach_learning_session(
        project.id,
        run.id,
        "knowledge_point",
        point.id,
        [_step_draft(point.id, source.id)],
        origin_type="learning_plan",
        plan_id=confirmed.id,
        plan_item_id=confirmed.items[0].id,
    )
    primary = session.steps[0].exercises[0]
    first, reserved, _ = store.reserve_coach_learning_attempt(
        project.id,
        session.id,
        primary.id,
        "不完整",
        session.version,
        "plan-attempt-1",
        "plan-hash-1",
    )
    _, evaluated, first_sync = store.finalize_coach_learning_attempt(
        project.id,
        session.id,
        first.id,
        reserved.version,
        evaluator="rule",
        score=0.0,
        plan_item_status="in_progress",
    )
    second, reserved_again, _ = store.reserve_coach_learning_attempt(
        project.id,
        session.id,
        primary.id,
        "app.py 与 FastAPI",
        evaluated.version,
        "plan-attempt-2",
        "plan-hash-2",
    )
    _, mastered, second_sync = store.finalize_coach_learning_attempt(
        project.id,
        session.id,
        second.id,
        reserved_again.version,
        evaluator="rule",
        score=1.0,
        counts_for_mastery=True,
        plan_item_status="done",
    )
    reinforcement = session.steps[0].exercises[1]
    third, third_reserved, _ = store.reserve_coach_learning_attempt(
        project.id,
        session.id,
        reinforcement.id,
        "练习答案",
        mastered.version,
        "plan-attempt-3",
        "plan-hash-3",
    )
    _, _, third_sync = store.finalize_coach_learning_attempt(
        project.id,
        session.id,
        third.id,
        third_reserved.version,
        evaluator="rule",
        score=0.0,
        plan_item_status="in_progress",
    )

    current_plan = store.get_coach_learning_plan(project.id, confirmed.id)
    assert current_plan is not None
    assert first_sync == "updated"
    assert second_sync == "updated"
    assert third_sync == "unchanged"
    assert current_plan.items[0].status == "done"


def test_skipped_or_archived_plan_item_is_never_reopened_by_learning_attempt(
    tmp_path: Path,
):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    project, run, point, skill, source = _add_coach_fixture(
        store,
        tmp_path,
        "A",
    )
    plan = store.create_coach_learning_plan(
        project.id,
        run.id,
        [
            {
                "stable_key": "learn:web-entry",
                "item_type": "learning",
                "objective": "掌握 Web 入口",
                "knowledge_point_id": point.id,
                "skill_node_id": skill.id,
                "source_ids": [source.id],
                "practice_question": "说明入口。",
                "completion_criteria": "正确说明入口。",
                "estimated_minutes": 20,
                "status": "todo",
                "sort_order": 0,
            }
        ],
    )
    confirmed = store.confirm_coach_learning_plan(project.id, plan.id)
    skipped = store.update_coach_learning_plan_progress(
        project.id,
        confirmed.id,
        {confirmed.items[0].id: "skipped"},
    )
    session = store.create_coach_learning_session(
        project.id,
        run.id,
        "knowledge_point",
        point.id,
        [_step_draft(point.id, source.id)],
        origin_type="learning_plan",
        plan_id=skipped.id,
        plan_item_id=skipped.items[0].id,
    )
    exercise = session.steps[0].exercises[0]
    first, reserved, _ = store.reserve_coach_learning_attempt(
        project.id,
        session.id,
        exercise.id,
        "不完整",
        session.version,
        "skipped-attempt-1",
        "skipped-hash-1",
    )
    _, evaluated, skipped_sync = store.finalize_coach_learning_attempt(
        project.id,
        session.id,
        first.id,
        reserved.version,
        evaluator="rule",
        score=0.0,
        plan_item_status="in_progress",
    )
    archived = store.archive_coach_learning_plan(project.id, skipped.id)
    second, reserved_again, _ = store.reserve_coach_learning_attempt(
        project.id,
        session.id,
        exercise.id,
        "仍不完整",
        evaluated.version,
        "archived-attempt-2",
        "archived-hash-2",
    )
    _, _, archived_sync = store.finalize_coach_learning_attempt(
        project.id,
        session.id,
        second.id,
        reserved_again.version,
        evaluator="rule",
        score=0.0,
        plan_item_status="in_progress",
    )
    historical = store.get_coach_learning_plan(project.id, archived.id)
    assert historical is not None

    assert skipped_sync == "unchanged"
    assert archived_sync == "detached"
    assert historical.status == "archived"
    assert historical.items[0].status == "skipped"
