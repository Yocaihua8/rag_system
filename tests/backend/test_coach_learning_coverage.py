from __future__ import annotations

from pathlib import Path

from backend.domain.coach_assessment import (
    answer_coach_assessment,
    build_coach_coverage,
    start_coach_assessment,
)
from backend.domain.coach_learning import (
    start_coach_learning_session,
    submit_coach_learning_attempt,
    transition_coach_learning_session,
)
from backend.domain.project_analysis import analyze_project
from backend.domain.learning_plans import learning_plan_progress_hash
from backend.storage import KnowledgeStore


def _analyzed_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    root = tmp_path / "project"
    root.mkdir()
    project = store.create_project("学习覆盖", root)
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
    return store, project, root, run, points


def _awaiting_session(store, project_id: str, point_id: str):
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


def test_learning_weak_attempt_is_distinct_from_unanswered_coverage(tmp_path):
    store, project, _, _, points = _analyzed_project(tmp_path)
    started, awaiting, exercise = _awaiting_session(
        store,
        project.id,
        points[0].id,
    )

    submitted = submit_coach_learning_attempt(
        store,
        project.id,
        started["id"],
        exercise.id,
        "完全无关",
        awaiting["version"],
        "coverage-attempt-1",
    )
    coverage = build_coach_coverage(store, project.id)
    learned = next(
        item
        for item in coverage["knowledge_points"]
        if item["id"] == points[0].id
    )
    unanswered = [
        item
        for item in coverage["knowledge_points"]
        if item["id"] != points[0].id
    ]

    assert submitted["attempt"]["counts_for_mastery"] is True
    assert learned["status"] == "needs_work"
    assert learned["assessment_state"] == "verified"
    assert learned["evidence_type"] == "learning_attempt"
    assert all(item["status"] == "unassessed" for item in unanswered)


def test_revealed_answer_attempt_does_not_replace_independent_weak_evidence(
    tmp_path,
):
    store, project, _, _, points = _analyzed_project(tmp_path)
    started, awaiting, exercise = _awaiting_session(
        store,
        project.id,
        points[0].id,
    )
    first = submit_coach_learning_attempt(
        store,
        project.id,
        started["id"],
        exercise.id,
        "完全无关",
        awaiting["version"],
        "reveal-attempt-1",
    )
    revealed = transition_coach_learning_session(
        store,
        project.id,
        started["id"],
        "reveal",
        first["session"]["version"],
    )
    retrying = transition_coach_learning_session(
        store,
        project.id,
        started["id"],
        "retry",
        revealed["version"],
    )
    assisted = submit_coach_learning_attempt(
        store,
        project.id,
        started["id"],
        exercise.id,
        "；".join(exercise.expected_points),
        retrying["version"],
        "reveal-attempt-2",
    )
    coverage = build_coach_coverage(store, project.id)
    point_coverage = next(
        item
        for item in coverage["knowledge_points"]
        if item["id"] == points[0].id
    )

    assert assisted["attempt"]["score"] == 1
    assert assisted["attempt"]["counts_for_mastery"] is False
    assert assisted["session"]["current_exercise"]["reference_answer"]
    assert point_coverage["status"] == "needs_work"
    assert point_coverage["evidence_id"] == first["attempt"]["id"]


def test_latest_learning_attempt_supersedes_older_legacy_assessment(tmp_path):
    store, project, _, _, points = _analyzed_project(tmp_path)
    assessment = start_coach_assessment(
        store,
        project.id,
        "knowledge_point",
        points[0].id,
    )
    stored_assessment = store.get_coach_assessment_session(
        project.id,
        assessment["id"],
    )
    assert stored_assessment is not None
    question = stored_assessment.questions[0]
    answer_coach_assessment(
        store,
        project.id,
        stored_assessment.id,
        question.id,
        "；".join(question.expected_points),
        evaluation_mode="rule",
    )
    started, awaiting, exercise = _awaiting_session(
        store,
        project.id,
        points[0].id,
    )
    submitted = submit_coach_learning_attempt(
        store,
        project.id,
        started["id"],
        exercise.id,
        "完全无关",
        awaiting["version"],
        "coverage-latest-attempt",
    )

    coverage = build_coach_coverage(store, project.id)
    evidence = next(
        item
        for item in coverage["knowledge_points"]
        if item["id"] == points[0].id
    )

    assert submitted["attempt"]["score"] == 0
    assert evidence["status"] == "needs_work"
    assert evidence["evidence_type"] == "learning_attempt"
    assert evidence["evidence_id"] == submitted["attempt"]["id"]


def test_plan_link_updates_only_after_attempt_and_preserves_revision_hash_contract(
    tmp_path,
):
    store, project, _, run, points = _analyzed_project(tmp_path)
    point = points[0]
    source = point.sources[0]
    plan = store.create_coach_learning_plan(
        project.id,
        run["id"],
        [
            {
                "stable_key": f"learn:{point.stable_key}",
                "item_type": "learning",
                "objective": f"掌握 {point.title}",
                "knowledge_point_id": point.id,
                "skill_node_id": "",
                "source_ids": [source.id],
                "practice_question": "结合来源说明当前项目知识点。",
                "completion_criteria": "独立作答达到掌握阈值。",
                "estimated_minutes": 20,
                "status": "todo",
                "sort_order": 0,
            }
        ],
    )
    confirmed = store.confirm_coach_learning_plan(project.id, plan.id)
    original_hash = learning_plan_progress_hash(confirmed)
    started = start_coach_learning_session(
        store,
        project.id,
        plan_id=confirmed.id,
        plan_item_id=confirmed.items[0].id,
    )
    unopened = store.get_coach_learning_plan(project.id, confirmed.id)
    assert unopened is not None
    assert unopened.items[0].status == "todo"
    assert unopened.revision == confirmed.revision
    assert learning_plan_progress_hash(unopened) == original_hash

    learning = transition_coach_learning_session(
        store,
        project.id,
        started["id"],
        "begin_learning",
        started["version"],
    )
    awaiting = transition_coach_learning_session(
        store,
        project.id,
        started["id"],
        "begin_question",
        learning["version"],
    )
    session = store.get_coach_learning_session(project.id, started["id"])
    assert session is not None
    exercise = session.steps[0].exercises[0]
    weak = submit_coach_learning_attempt(
        store,
        project.id,
        started["id"],
        exercise.id,
        "完全无关",
        awaiting["version"],
        "plan-progress-attempt-1",
    )
    in_progress = store.get_coach_learning_plan(project.id, confirmed.id)
    assert in_progress is not None
    assert in_progress.items[0].status == "in_progress"
    assert in_progress.revision == confirmed.revision
    assert learning_plan_progress_hash(in_progress) != original_hash
    assert weak["plan_sync"]["item_status"] == "in_progress"

    retrying = transition_coach_learning_session(
        store,
        project.id,
        started["id"],
        "retry",
        weak["session"]["version"],
    )
    mastered = submit_coach_learning_attempt(
        store,
        project.id,
        started["id"],
        exercise.id,
        "；".join(exercise.expected_points),
        retrying["version"],
        "plan-progress-attempt-2",
    )
    done = store.get_coach_learning_plan(project.id, confirmed.id)
    assert done is not None
    assert done.items[0].status == "done"
    assert done.revision == confirmed.revision
    assert mastered["plan_sync"]["item_status"] == "done"
    assert mastered["plan_sync"]["progress_hash"] == (
        learning_plan_progress_hash(done)
    )


def test_direct_coach_learning_does_not_implicitly_update_confirmed_plan(
    tmp_path,
):
    store, project, _, run, points = _analyzed_project(tmp_path)
    point = points[0]
    plan = store.create_coach_learning_plan(
        project.id,
        run["id"],
        [
            {
                "stable_key": f"learn:{point.stable_key}",
                "item_type": "learning",
                "objective": f"掌握 {point.title}",
                "knowledge_point_id": point.id,
                "skill_node_id": "",
                "source_ids": [point.sources[0].id],
                "practice_question": "说明当前项目知识点。",
                "completion_criteria": "完成独立作答。",
                "estimated_minutes": 20,
                "status": "todo",
                "sort_order": 0,
            }
        ],
    )
    confirmed = store.confirm_coach_learning_plan(project.id, plan.id)
    started, awaiting, exercise = _awaiting_session(
        store,
        project.id,
        point.id,
    )
    submit_coach_learning_attempt(
        store,
        project.id,
        started["id"],
        exercise.id,
        "完全无关",
        awaiting["version"],
        "direct-coach-attempt",
    )

    unchanged = store.get_coach_learning_plan(project.id, confirmed.id)
    assert unchanged is not None
    assert unchanged.items[0].status == "todo"


def test_source_change_keeps_learning_evidence_only_as_history(tmp_path):
    store, project, root, _, points = _analyzed_project(tmp_path)
    started, awaiting, exercise = _awaiting_session(
        store,
        project.id,
        points[0].id,
    )
    submitted = submit_coach_learning_attempt(
        store,
        project.id,
        started["id"],
        exercise.id,
        "；".join(exercise.expected_points),
        awaiting["version"],
        "stale-coverage-attempt",
    )
    source_path = root / "app.py"
    changed = "from fastapi import FastAPI\napp = FastAPI(title='changed')\n"
    source_path.write_text(changed, encoding="utf-8")
    store.upsert_document(project.id, source_path, "app.py", changed)

    coverage = build_coach_coverage(store, project.id)
    historical = next(
        item
        for item in coverage["knowledge_points"]
        if item["id"] == points[0].id
    )

    assert submitted["attempt"]["score"] == 1
    assert coverage["stale"] is True
    assert historical["status"] == "unassessed"
    assert historical["historical_status"] == "mastered"
    assert historical["valid_for_current_sources"] is False
