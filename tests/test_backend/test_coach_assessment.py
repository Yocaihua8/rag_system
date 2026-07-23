from __future__ import annotations

import json

import pytest

from backend.domain.coach_assessment import (
    CoachAssessmentConflictError,
    answer_coach_assessment,
    assessment_status,
    build_coach_coverage,
    score_coach_answer,
    start_coach_assessment,
)
from backend.domain.project_analysis import analyze_project
from backend.storage import KnowledgeStore


def _analyzed_project(tmp_path):
    store = KnowledgeStore(tmp_path / "app.db")
    root = tmp_path / "project"
    root.mkdir()
    project = store.create_project("示例项目", root)
    source = root / "app.py"
    content = (
        "from fastapi import FastAPI\n"
        "import sqlite3\n"
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


def _all_expected_points(store, project_id: str, session_id: str) -> tuple[str, str]:
    session = store.get_coach_assessment_session(project_id, session_id)
    assert session is not None
    question = session.questions[0]
    return question.id, "；".join(question.expected_points)


def test_assessment_start_resumes_restarts_and_hides_scoring_basis(tmp_path):
    store, project, _, _, points = _analyzed_project(tmp_path)
    point = points[0]

    first = start_coach_assessment(
        store,
        project.id,
        "knowledge_point",
        point.id,
    )
    resumed = start_coach_assessment(
        store,
        project.id,
        "knowledge_point",
        point.id,
    )
    restarted = start_coach_assessment(
        store,
        project.id,
        "knowledge_point",
        point.id,
        restart=True,
    )

    assert first["resumed"] is False
    assert resumed["resumed"] is True
    assert resumed["id"] == first["id"]
    assert restarted["id"] != first["id"]
    assert all("expected_points" not in item for item in restarted["questions"])
    assert store.get_coach_assessment_session(project.id, first["id"]).status == "abandoned"


def test_assessment_rule_thresholds_and_evidence_are_deterministic(tmp_path):
    store, project, _, _, points = _analyzed_project(tmp_path)
    started = start_coach_assessment(
        store,
        project.id,
        "knowledge_point",
        points[0].id,
    )
    stored = store.get_coach_assessment_session(project.id, started["id"])
    assert stored is not None
    question = stored.questions[0]
    partial_answer = " ".join(question.expected_points[:1])

    grading = score_coach_answer(question, partial_answer)
    copied_prompt = score_coach_answer(question, question.prompt)

    assert grading["evaluator"] == "rule"
    assert grading["score"] == round(1 / len(question.expected_points), 4)
    assert grading["matched_evidence"][0]["evidence"] in partial_answer
    assert copied_prompt["score"] == 0
    assert assessment_status(0.49) == "needs_work"
    assert assessment_status(0.50) == "developing"
    assert assessment_status(0.74) == "developing"
    assert assessment_status(0.75) == "mastered"


def test_answer_persists_result_and_updates_project_and_skill_coverage(tmp_path):
    store, project, _, _, points = _analyzed_project(tmp_path)
    started = start_coach_assessment(
        store,
        project.id,
        "knowledge_point",
        points[0].id,
    )
    question_id, complete_answer = _all_expected_points(
        store,
        project.id,
        started["id"],
    )

    answered = answer_coach_assessment(
        store,
        project.id,
        started["id"],
        question_id,
        complete_answer,
        evaluation_mode="rule",
    )
    coverage = build_coach_coverage(store, project.id)

    assert answered["result"]["status"] == "mastered"
    assert answered["result"]["evaluator"] == "rule"
    assert answered["session"]["status"] == "completed"
    assert coverage["summary"]["assessed_count"] == 1
    assert coverage["summary"]["status_counts"]["mastered"] == 1
    point_coverage = next(
        item for item in coverage["knowledge_points"] if item["id"] == points[0].id
    )
    assert point_coverage["assessment_state"] == "verified"
    assert point_coverage["valid_for_current_sources"] is True
    related_skills = [
        item
        for item in coverage["skills"]
        if points[0].id in item["knowledge_point_ids"]
    ]
    assert related_skills
    assert any(item["assessment_state"] != "unverified" for item in related_skills)
    assert coverage["scope_notice"]


def test_model_assessment_requires_exact_basis_and_verbatim_evidence(tmp_path):
    store, project, _, _, points = _analyzed_project(tmp_path)
    started = start_coach_assessment(
        store,
        project.id,
        "knowledge_point",
        points[0].id,
    )
    stored = store.get_coach_assessment_session(project.id, started["id"])
    assert stored is not None
    question = stored.questions[0]
    complete_answer = "；".join(question.expected_points)

    class Model:
        def generate_answer(self, prompt, hits):
            assert "expected_points" in prompt
            assert hits
            return json.dumps(
                {
                    "matched": [
                        {"point": point, "evidence": point}
                        for point in question.expected_points
                    ],
                    "missing_points": [],
                    "confidence": 0.96,
                },
                ensure_ascii=False,
            )

    answered = answer_coach_assessment(
        store,
        project.id,
        started["id"],
        question.id,
        complete_answer,
        llm_client=Model(),
    )

    assert answered["result"]["evaluator"] == "model"
    assert answered["result"]["confidence"] == 0.85
    assert answered["result"]["status"] == "mastered"
    assert answered["result"]["evaluation_warning"] == ""


def test_invalid_model_result_falls_back_to_low_confidence_rule_score(tmp_path):
    store, project, _, _, points = _analyzed_project(tmp_path)
    started = start_coach_assessment(
        store,
        project.id,
        "knowledge_point",
        points[0].id,
    )
    question_id, complete_answer = _all_expected_points(
        store,
        project.id,
        started["id"],
    )

    class InvalidModel:
        def generate_answer(self, prompt, hits):
            return '{"matched": [{"point": "invented", "evidence": "invented"}]}'

    answered = answer_coach_assessment(
        store,
        project.id,
        started["id"],
        question_id,
        complete_answer,
        llm_client=InvalidModel(),
    )

    assert answered["result"]["evaluator"] == "rule"
    assert answered["result"]["confidence"] <= 0.49
    assert "已回退规则评分" in answered["result"]["evaluation_warning"]


def test_source_change_makes_active_assessment_read_only_and_coverage_stale(tmp_path):
    store, project, root, _, points = _analyzed_project(tmp_path)
    started = start_coach_assessment(
        store,
        project.id,
        "knowledge_point",
        points[0].id,
    )
    question_id, complete_answer = _all_expected_points(
        store,
        project.id,
        started["id"],
    )
    changed = "from fastapi import FastAPI\napp = FastAPI(title='changed')\n"
    (root / "app.py").write_text(changed, encoding="utf-8")
    store.upsert_document(project.id, root / "app.py", "app.py", changed)

    with pytest.raises(CoachAssessmentConflictError, match="analysis_stale"):
        answer_coach_assessment(
            store,
            project.id,
            started["id"],
            question_id,
            complete_answer,
        )

    restored = start_coach_assessment(
        store,
        project.id,
        session_id=started["id"],
    )
    coverage = build_coach_coverage(store, project.id)
    assert restored["read_only"] is True
    assert restored["can_answer"] is False
    assert coverage["stale"] is True
    assert coverage["can_assess"] is False


def test_skill_target_can_generate_questions_from_mapped_descendants(tmp_path):
    store, project, _, _, _ = _analyzed_project(tmp_path)
    mappings = store.list_coach_skill_mappings(project.id)
    assert mappings
    nodes = {node.id: node for node in store.list_coach_skill_nodes()}
    mapped_node = nodes[mappings[0].skill_node_id]
    target_id = mapped_node.parent_id or mapped_node.id

    started = start_coach_assessment(
        store,
        project.id,
        "skill",
        target_id,
    )

    assert started["target_type"] == "skill"
    assert started["questions"]
    assert len(started["questions"]) <= 3
    assert all(question["source_ids"] for question in started["questions"])
