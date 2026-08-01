from __future__ import annotations

from pathlib import Path

import pytest

from backend.domain.coach_learning import (
    CoachLearningConflictError,
    get_current_coach_learning_session,
    start_coach_learning_session,
    submit_coach_learning_attempt,
    transition_coach_learning_session,
)
from backend.domain.project_analysis import analyze_project
from backend.storage import KnowledgeStore


def _analyzed_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    root = tmp_path / "project"
    root.mkdir()
    project = store.create_project("交互学习", root)
    source = root / "app.py"
    content = (
        "from fastapi import FastAPI\n"
        "app = FastAPI()\n"
        "def health_check():\n"
        "    return {'status': 'ok'}\n"
    )
    source.write_text(content, encoding="utf-8")
    store.upsert_document(project.id, source, "app.py", content)
    run = analyze_project(store, project.id)
    points = store.list_coach_knowledge_points(project.id)
    assert points
    return store, project, root, run, points


def _stored_exercise(store: KnowledgeStore, project_id: str, session_id: str):
    session = store.get_coach_learning_session(project_id, session_id)
    assert session is not None
    assert session.steps
    assert session.steps[0].exercises
    return session.steps[0].exercises[0]


def test_learning_session_runs_one_step_through_explicit_states(tmp_path):
    store, project, _, _, points = _analyzed_project(tmp_path)

    ready = start_coach_learning_session(
        store,
        project.id,
        target_type="knowledge_point",
        target_id=points[0].id,
    )
    learning = transition_coach_learning_session(
        store,
        project.id,
        ready["id"],
        "begin_learning",
        ready["version"],
    )
    awaiting = transition_coach_learning_session(
        store,
        project.id,
        ready["id"],
        "begin_question",
        learning["version"],
    )
    exercise = _stored_exercise(store, project.id, ready["id"])
    answer = "；".join(exercise.expected_points)
    evaluated = submit_coach_learning_attempt(
        store,
        project.id,
        ready["id"],
        exercise.id,
        answer,
        awaiting["version"],
        "attempt-1",
    )
    completed = transition_coach_learning_session(
        store,
        project.id,
        ready["id"],
        "next",
        evaluated["session"]["version"],
    )

    assert ready["status"] == "ready"
    assert ready["current_exercise"] is None
    assert learning["status"] == "learning"
    assert learning["current_step"]["knowledge_point_id"] == points[0].id
    assert awaiting["status"] == "awaiting_answer"
    assert awaiting["current_exercise"]["id"] == exercise.id
    assert evaluated["attempt"]["score"] == 1
    assert evaluated["attempt"]["counts_for_mastery"] is True
    assert evaluated["session"]["status"] == "evaluated"
    assert completed["status"] == "completed"
    assert completed["outcome"] == "mastered"


def test_learning_attempt_is_idempotent_and_rejects_payload_reuse(tmp_path):
    store, project, _, _, points = _analyzed_project(tmp_path)
    ready = start_coach_learning_session(
        store,
        project.id,
        target_type="knowledge_point",
        target_id=points[0].id,
    )
    learning = transition_coach_learning_session(
        store,
        project.id,
        ready["id"],
        "begin_learning",
        ready["version"],
    )
    awaiting = transition_coach_learning_session(
        store,
        project.id,
        ready["id"],
        "begin_question",
        learning["version"],
    )
    exercise = _stored_exercise(store, project.id, ready["id"])
    answer = "；".join(exercise.expected_points)

    first = submit_coach_learning_attempt(
        store,
        project.id,
        ready["id"],
        exercise.id,
        answer,
        awaiting["version"],
        "stable-key",
    )
    replay = submit_coach_learning_attempt(
        store,
        project.id,
        ready["id"],
        exercise.id,
        answer,
        awaiting["version"],
        "stable-key",
    )

    assert first["replayed"] is False
    assert replay["replayed"] is True
    assert replay["attempt"]["id"] == first["attempt"]["id"]
    with pytest.raises(
        CoachLearningConflictError,
        match="idempotency_payload_conflict",
    ):
        submit_coach_learning_attempt(
            store,
            project.id,
            ready["id"],
            exercise.id,
            "另一个答案",
            awaiting["version"],
            "stable-key",
        )


def test_learning_retries_twice_then_uses_one_reinforcement_exercise(tmp_path):
    store, project, _, _, points = _analyzed_project(tmp_path)
    ready = start_coach_learning_session(
        store,
        project.id,
        target_type="knowledge_point",
        target_id=points[0].id,
    )
    learning = transition_coach_learning_session(
        store,
        project.id,
        ready["id"],
        "begin_learning",
        ready["version"],
    )
    awaiting = transition_coach_learning_session(
        store,
        project.id,
        ready["id"],
        "begin_question",
        learning["version"],
    )
    primary = _stored_exercise(store, project.id, ready["id"])

    first = submit_coach_learning_attempt(
        store,
        project.id,
        ready["id"],
        primary.id,
        "完全无关",
        awaiting["version"],
        "attempt-1",
    )
    retrying = transition_coach_learning_session(
        store,
        project.id,
        ready["id"],
        "retry",
        first["session"]["version"],
    )
    second = submit_coach_learning_attempt(
        store,
        project.id,
        ready["id"],
        primary.id,
        "仍然无关",
        retrying["version"],
        "attempt-2",
    )
    reinforcement = transition_coach_learning_session(
        store,
        project.id,
        ready["id"],
        "retry",
        second["session"]["version"],
    )

    assert first["attempt"]["attempt_no"] == 1
    assert retrying["status"] == "retrying"
    assert retrying["current_exercise"]["variant_no"] == 1
    assert second["attempt"]["attempt_no"] == 2
    assert reinforcement["status"] == "retrying"
    assert reinforcement["current_exercise"]["variant_no"] == 2
    stored = store.get_coach_learning_session(project.id, ready["id"])
    assert stored is not None
    assert len(stored.steps[0].exercises) == 2


def test_learning_session_resumes_and_becomes_read_only_when_sources_stale(tmp_path):
    store, project, root, _, points = _analyzed_project(tmp_path)
    started = start_coach_learning_session(
        store,
        project.id,
        target_type="knowledge_point",
        target_id=points[0].id,
    )
    resumed = start_coach_learning_session(
        store,
        project.id,
        target_type="knowledge_point",
        target_id=points[0].id,
    )

    changed = "from fastapi import FastAPI\napp = FastAPI(title='changed')\n"
    source = root / "app.py"
    source.write_text(changed, encoding="utf-8")
    store.upsert_document(project.id, source, "app.py", changed)
    historical = get_current_coach_learning_session(
        store,
        project.id,
        session_id=started["id"],
    )

    assert resumed["resumed"] is True
    assert resumed["id"] == started["id"]
    assert historical is not None
    assert historical["read_only"] is True
    assert historical["allowed_actions"] == []
    with pytest.raises(CoachLearningConflictError, match="analysis_stale"):
        transition_coach_learning_session(
            store,
            project.id,
            started["id"],
            "begin_learning",
            historical["version"],
        )


def test_different_target_conflicts_until_active_session_is_abandoned(tmp_path):
    store, project, _, run, points = _analyzed_project(tmp_path)
    started = start_coach_learning_session(
        store,
        project.id,
        target_type="knowledge_point",
        target_id=points[0].id,
    )
    mapping = store.list_coach_skill_mappings(project.id, run_id=run["id"])[0]

    with pytest.raises(
        CoachLearningConflictError,
        match="learning_session_active_conflict",
    ):
        start_coach_learning_session(
            store,
            project.id,
            target_type="skill",
            target_id=mapping.skill_node_id,
        )

    abandoned = transition_coach_learning_session(
        store,
        project.id,
        started["id"],
        "abandon",
        started["version"],
    )
    restarted = start_coach_learning_session(
        store,
        project.id,
        target_type="skill",
        target_id=mapping.skill_node_id,
    )

    assert abandoned["status"] == "abandoned"
    assert abandoned["read_only"] is True
    assert restarted["id"] != started["id"]
    assert restarted["target_type"] == "skill"
