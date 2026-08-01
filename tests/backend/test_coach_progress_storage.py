from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from backend.storage import KnowledgeStore


def _coach_fixture(tmp_path: Path, name: str = "项目 A"):
    store = KnowledgeStore(tmp_path / f"{name}.db")
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
    run = store.create_coach_analysis_run(project.id, "rules-v1", f"fingerprint-{name}")
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
            }
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
    source = point.sources[0]
    return store, project, run, point, skill, source


def _questions(point_id: str, source_id: str):
    return [
        {
            "knowledge_point_id": point_id,
            "prompt": "项目默认入口和服务框架是什么？",
            "question_type": "concept",
            "expected_points": ["app.py", "FastAPI"],
            "source_ids": [source_id],
            "sort_order": 0,
        }
    ]


def _learning_item(point_id: str, skill_id: str, source_id: str, **overrides):
    item = {
        "stable_key": "learn:web-entry",
        "item_type": "learning",
        "objective": "掌握项目 Web 入口",
        "knowledge_point_id": point_id,
        "skill_node_id": skill_id,
        "source_ids": [source_id],
        "practice_question": "说明 app.py 与 FastAPI 的关系。",
        "completion_criteria": "能够结合来源完整说明启动链路。",
        "estimated_minutes": 30,
        "status": "todo",
        "sort_order": 0,
    }
    item.update(overrides)
    return item


def test_progress_schema_contains_six_tables_and_constraints(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    with sqlite3.connect(store.db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert {
        "coach_assessment_sessions",
        "coach_assessment_questions",
        "coach_assessment_answers",
        "coach_assessment_results",
        "coach_learning_plans",
        "coach_learning_plan_items",
    } <= tables


def test_assessment_session_is_resumable_and_hides_scoring_basis(tmp_path: Path):
    store, project, run, point, _, source = _coach_fixture(tmp_path)

    first = store.create_coach_assessment_session(
        project.id,
        run.id,
        "knowledge_point",
        point.id,
        _questions(point.id, source.id),
    )
    resumed = store.create_coach_assessment_session(
        project.id,
        run.id,
        "knowledge_point",
        point.id,
        _questions(point.id, source.id),
    )
    active = store.get_active_coach_assessment_session(
        project.id,
        run.id,
        "knowledge_point",
        point.id,
    )

    assert resumed.id == first.id
    assert active and active.id == first.id
    assert first.analysis_run_id == run.id
    assert first.questions[0].knowledge_point_id == point.id
    assert "expected_points" not in first.to_dict()["questions"][0]
    assert first.to_dict(include_scoring_basis=True)["questions"][0][
        "expected_points"
    ] == ["app.py", "FastAPI"]


@pytest.mark.parametrize(
    ("score", "expected_status"),
    [(0.49, "needs_work"), (0.50, "developing"), (0.75, "mastered")],
)
def test_assessment_result_uses_fixed_thresholds_and_context(
    tmp_path: Path,
    score: float,
    expected_status: str,
):
    store, project, run, point, _, source = _coach_fixture(
        tmp_path,
        f"score-{score}",
    )
    session = store.create_coach_assessment_session(
        project.id,
        run.id,
        "knowledge_point",
        point.id,
        _questions(point.id, source.id),
    )
    question = session.questions[0]

    answer, result, completed = store.create_coach_assessment_answer_result(
        project.id,
        session.id,
        question.id,
        "项目默认入口是 app.py，并使用 FastAPI。",
        "rule",
        score,
        0.8,
        [
            {"point": "app.py", "evidence": "app.py"},
            {"point": "FastAPI", "evidence": "FastAPI"},
        ],
        [],
        [source.id],
        evaluation_warning="规则评分置信度有限",
        feedback="入口识别正确。",
    )

    assert answer.question_id == question.id
    assert result.status == expected_status
    assert result.session_id == session.id
    assert result.question_id == question.id
    assert result.knowledge_point_id == point.id
    assert result.evaluation_warning == "规则评分置信度有限"
    assert result.feedback == "入口识别正确。"
    assert completed.status == "completed"
    assert completed.completed_at


def test_assessment_answer_replay_is_idempotent_but_conflict_is_rejected(tmp_path: Path):
    store, project, run, point, _, source = _coach_fixture(tmp_path)
    session = store.create_coach_assessment_session(
        project.id,
        run.id,
        "knowledge_point",
        point.id,
        _questions(point.id, source.id),
    )
    question = session.questions[0]
    call = (
        project.id,
        session.id,
        question.id,
        "项目默认入口是 app.py，并使用 FastAPI。",
        "rule",
        0.8,
        0.9,
        [{"point": "app.py", "evidence": "app.py"}],
        ["FastAPI"],
        [source.id],
    )

    first_answer, first_result, _ = store.create_coach_assessment_answer_result(*call)
    replay_answer, replay_result, _ = store.create_coach_assessment_answer_result(*call)

    assert replay_answer.id == first_answer.id
    assert replay_result.id == first_result.id
    with pytest.raises(ValueError, match="different answer"):
        store.create_coach_assessment_answer_result(
            *(
                call[:3]
                + ("不同回答",)
                + call[4:]
            )
        )


def test_abandoned_session_is_preserved_and_restart_creates_new_session(tmp_path: Path):
    store, project, run, point, _, source = _coach_fixture(tmp_path)
    first = store.create_coach_assessment_session(
        project.id,
        run.id,
        "knowledge_point",
        point.id,
        _questions(point.id, source.id),
    )

    abandoned = store.abandon_coach_assessment_session(project.id, first.id)
    restarted = store.create_coach_assessment_session(
        project.id,
        run.id,
        "knowledge_point",
        point.id,
        _questions(point.id, source.id),
    )

    assert abandoned.status == "abandoned"
    assert restarted.id != first.id
    assert [item.status for item in store.list_coach_assessment_sessions(project.id)] == [
        "active",
        "abandoned",
    ]


def test_skill_assessment_accepts_descendant_knowledge_mapping(tmp_path: Path):
    store, project, run, point, _, source = _coach_fixture(tmp_path)
    parent_skill = next(
        node
        for node in store.list_coach_skill_nodes()
        if node.stable_key == "delivery"
    )

    session = store.create_coach_assessment_session(
        project.id,
        run.id,
        "skill",
        parent_skill.id,
        _questions(point.id, source.id),
    )

    assert session.target_id == parent_skill.id
    assert session.questions[0].knowledge_point_id == point.id


def test_assessment_rejects_cross_project_target_and_sources(tmp_path: Path):
    store, project_a, run_a, point_a, _, source_a = _coach_fixture(tmp_path, "A")
    _, project_b, run_b, point_b, _, source_b = _coach_fixture(tmp_path, "B")

    with pytest.raises(ValueError, match="does not belong to project"):
        store.create_coach_assessment_session(
            project_a.id,
            run_a.id,
            "knowledge_point",
            point_b.id,
            _questions(point_b.id, source_b.id),
        )
    with pytest.raises(ValueError, match="question source"):
        store.create_coach_assessment_session(
            project_a.id,
            run_a.id,
            "knowledge_point",
            point_a.id,
            _questions(point_a.id, source_b.id),
        )
    assert store.list_coach_assessment_sessions(project_b.id) == []
    assert run_b.project_id == project_b.id
    assert source_a.id != source_b.id


def test_learning_plan_draft_update_confirm_and_new_revision(tmp_path: Path):
    store, project, run, point, skill, source = _coach_fixture(tmp_path)
    first = store.create_coach_learning_plan(
        project.id,
        run.id,
        [_learning_item(point.id, skill.id, source.id)],
    )
    original_item_id = first.items[0].id

    updated = store.update_coach_learning_plan(
        project.id,
        first.id,
        [
            {
                "stable_key": "source-gap:web-entry",
                "item_type": "source_gap",
                "objective": "补充入口启动链路资料",
                "source_ids": [],
                "practice_question": "还缺少哪些启动信息？",
                "completion_criteria": "补充至少一个可追溯来源。",
                "estimated_minutes": 15,
                "status": "in_progress",
                "sort_order": 0,
            },
            _learning_item(
                point.id,
                skill.id,
                source.id,
                status="todo",
                sort_order=1,
            ),
        ],
    )
    confirmed = store.confirm_coach_learning_plan(project.id, first.id)
    progressed = store.update_coach_learning_plan_progress(
        project.id,
        first.id,
        {confirmed.items[0].stable_key: "done"},
    )
    second = store.create_coach_learning_plan(
        project.id,
        run.id,
        [_learning_item(point.id, skill.id, source.id)],
    )
    second_confirmed = store.confirm_coach_learning_plan(project.id, second.id)
    repeated_confirm = store.confirm_coach_learning_plan(project.id, second.id)

    assert first.revision == 1
    assert updated.items[1].id == original_item_id
    assert [item.item_type for item in updated.items] == ["source_gap", "learning"]
    assert confirmed.status == "confirmed"
    assert confirmed.confirmed_at
    assert progressed.items[0].status == "done"
    assert second.revision == 2
    assert second.status == "draft"
    assert second_confirmed.status == "confirmed"
    assert repeated_confirm.id == second_confirmed.id
    assert store.get_coach_learning_plan(project.id, first.id).status == "archived"
    with pytest.raises(ValueError, match="only draft"):
        store.update_coach_learning_plan(
            project.id,
            confirmed.id,
            [_learning_item(point.id, skill.id, source.id)],
        )


def test_learning_plan_confirmation_rejects_stale_run_and_cross_project_data(
    tmp_path: Path,
):
    store, project_a, run_a, point_a, skill_a, source_a = _coach_fixture(tmp_path, "A")
    _, project_b, _, point_b, _, source_b = _coach_fixture(tmp_path, "B")

    with pytest.raises(ValueError, match="does not belong to project"):
        store.create_coach_learning_plan(
            project_a.id,
            run_a.id,
            [_learning_item(point_b.id, skill_a.id, source_a.id)],
        )
    with pytest.raises(ValueError, match="source does not belong"):
        store.create_coach_learning_plan(
            project_a.id,
            run_a.id,
            [_learning_item(point_a.id, skill_a.id, source_b.id)],
        )

    plan = store.create_coach_learning_plan(
        project_a.id,
        run_a.id,
        [_learning_item(point_a.id, skill_a.id, source_a.id)],
    )
    store.mark_coach_analysis_stale(project_a.id)

    with pytest.raises(ValueError, match="stale analysis"):
        store.confirm_coach_learning_plan(project_a.id, plan.id)
    assert store.get_coach_learning_plan(project_b.id, plan.id) is None
