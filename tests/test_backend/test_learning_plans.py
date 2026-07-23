from __future__ import annotations

import hashlib
import json
import sqlite3

import pytest

from backend.domain.coach_assessment import (
    answer_coach_assessment,
    start_coach_assessment,
)
from backend.domain.learning_plans import (
    CoachLearningPlanConflictError,
    CoachLearningPlanNotFoundError,
    build_current_learning_plan,
    confirm_learning_plan,
    generate_learning_plan,
    update_learning_plan,
)
from backend.domain.project_analysis import analyze_project
from backend.storage import KnowledgeStore


def _add_analyzed_project(store, tmp_path, name: str):
    root = tmp_path / name
    root.mkdir()
    project = store.create_project(name, root)
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
    analyze_project(store, project.id)
    return project, root


def _store_project(tmp_path):
    store = KnowledgeStore(tmp_path / "app.db")
    project, root = _add_analyzed_project(store, tmp_path, "project-a")
    return store, project, root


def test_rule_plan_is_deterministic_sourced_and_does_not_replace_confirmed(tmp_path):
    store, project, _ = _store_project(tmp_path)

    first = generate_learning_plan(store, project.id)
    confirmed = confirm_learning_plan(store, project.id, first["plan"]["id"])
    second = generate_learning_plan(store, project.id)
    current = build_current_learning_plan(store, project.id)

    assert first["generation_mode"] == "rule"
    assert first["warning"] == ""
    assert first["plan"]["revision"] == 1
    assert first["plan"]["items"]
    assert [item["sort_order"] for item in first["plan"]["items"]] == list(
        range(len(first["plan"]["items"]))
    )
    assert all(item["stable_key"].startswith("learn:") for item in first["plan"]["items"])
    assert all(item["source_ids"] for item in first["plan"]["items"])
    assert all(item["reading_sources"] for item in first["plan"]["items"])
    assert all(
        source_id in first["sources"]
        for item in first["plan"]["items"]
        for source_id in item["source_ids"]
    )
    assert confirmed["plan"]["status"] == "confirmed"
    assert second["plan"]["revision"] == 2
    assert current["draft"]["id"] == second["plan"]["id"]
    assert current["confirmed"]["id"] == confirmed["plan"]["id"]

    replacement = confirm_learning_plan(store, project.id, second["plan"]["id"])
    replaced_current = build_current_learning_plan(store, project.id)
    archived = store.get_coach_learning_plan(project.id, confirmed["plan"]["id"])
    assert replacement["plan"]["status"] == "confirmed"
    assert replaced_current["confirmed"]["id"] == second["plan"]["id"]
    assert archived is not None
    assert archived.status == "archived"


def test_draft_can_reorder_then_confirmed_plan_only_updates_progress(tmp_path):
    store, project, _ = _store_project(tmp_path)
    generated = generate_learning_plan(store, project.id)
    original = generated["plan"]
    original_ids = {
        item["stable_key"]: item["id"]
        for item in original["items"]
    }
    edited_items = list(reversed(original["items"]))
    edited_items[0]["objective"] = "先完成这个项目知识任务"
    edited_items[0]["status"] = "done"

    updated = update_learning_plan(
        store,
        project.id,
        original["id"],
        items=edited_items,
        expected_revision=original["revision"],
        expected_items_hash=original["items_hash"],
    )
    confirmed = confirm_learning_plan(
        store,
        project.id,
        original["id"],
        expected_revision=updated["plan"]["revision"],
        expected_items_hash=updated["plan"]["items_hash"],
    )
    repeated = confirm_learning_plan(store, project.id, original["id"])
    first_item = confirmed["plan"]["items"][0]
    progressed = update_learning_plan(
        store,
        project.id,
        original["id"],
        item_statuses={first_item["stable_key"]: "done"},
    )
    replayed_after_progress = confirm_learning_plan(
        store,
        project.id,
        original["id"],
        expected_revision=confirmed["plan"]["revision"],
        expected_items_hash=confirmed["plan"]["items_hash"],
    )

    assert updated["plan"]["items"][0]["objective"] == "先完成这个项目知识任务"
    assert updated["plan"]["items"][0]["status"] == "todo"
    assert [item["sort_order"] for item in updated["plan"]["items"]] == list(
        range(len(updated["plan"]["items"]))
    )
    assert {
        item["stable_key"]: item["id"]
        for item in updated["plan"]["items"]
    } == original_ids
    assert confirmed["replayed"] is False
    assert repeated["replayed"] is True
    assert replayed_after_progress["replayed"] is True
    assert progressed["plan"]["items"][0]["status"] == "done"
    with pytest.raises(
        CoachLearningPlanConflictError,
        match="learning_plan_progress_conflict",
    ):
        update_learning_plan(
            store,
            project.id,
            original["id"],
            item_statuses={first_item["stable_key"]: "in_progress"},
            expected_progress_hash=confirmed["plan"]["progress_hash"],
        )
    with pytest.raises(
        CoachLearningPlanConflictError,
        match="learning_plan_not_editable",
    ):
        update_learning_plan(
            store,
            project.id,
            original["id"],
            items=updated["plan"]["items"],
        )


def test_only_latest_draft_can_be_edited_or_confirmed(tmp_path):
    store, project, _ = _store_project(tmp_path)
    first = generate_learning_plan(store, project.id)
    second = generate_learning_plan(store, project.id)
    current = build_current_learning_plan(store, project.id)
    historical_first = next(
        plan for plan in current["history"] if plan["id"] == first["plan"]["id"]
    )

    assert historical_first["can_edit_structure"] is False
    assert historical_first["can_confirm"] is False
    with pytest.raises(
        CoachLearningPlanConflictError,
        match="learning_plan_not_current_draft",
    ):
        update_learning_plan(
            store,
            project.id,
            first["plan"]["id"],
            items=first["plan"]["items"],
        )
    with pytest.raises(
        CoachLearningPlanConflictError,
        match="learning_plan_not_current_draft",
    ):
        confirm_learning_plan(store, project.id, first["plan"]["id"])

    confirmed = confirm_learning_plan(store, project.id, second["plan"]["id"])
    assert confirmed["plan"]["status"] == "confirmed"


def test_stale_analysis_blocks_generation_and_confirmation_but_not_progress(tmp_path):
    store, project, root = _store_project(tmp_path)
    first = generate_learning_plan(store, project.id)
    confirmed = confirm_learning_plan(store, project.id, first["plan"]["id"])
    pending = generate_learning_plan(store, project.id)
    historical_source_hash = confirmed["plan"]["items"][0]["reading_sources"][0][
        "source_hash"
    ]
    changed = "from fastapi import FastAPI\napp = FastAPI(title='changed')\n"
    (root / "app.py").write_text(changed, encoding="utf-8")
    store.upsert_document(project.id, root / "app.py", "app.py", changed)

    current = build_current_learning_plan(store, project.id)
    progressed = update_learning_plan(
        store,
        project.id,
        confirmed["plan"]["id"],
        item_statuses={confirmed["plan"]["items"][0]["id"]: "in_progress"},
    )

    assert current["stale"] is True
    assert current["confirmed"]["analysis_status"] == "stale"
    assert current["confirmed"]["items"][0]["reading_sources"]
    assert progressed["plan"]["items"][0]["status"] == "in_progress"
    with pytest.raises(CoachLearningPlanConflictError, match="analysis_stale"):
        generate_learning_plan(store, project.id)
    with pytest.raises(CoachLearningPlanConflictError, match="analysis_stale"):
        confirm_learning_plan(store, project.id, pending["plan"]["id"])

    analyze_project(store, project.id)
    refreshed = build_current_learning_plan(store, project.id)
    assert refreshed["confirmed"]["analysis_status"] == "stale"
    assert (
        refreshed["confirmed"]["items"][0]["reading_sources"][0]["source_hash"]
        == historical_source_hash
    )


def test_plan_update_rejects_other_project_run_entities_and_stale_client_hash(tmp_path):
    store, project_a, _ = _store_project(tmp_path)
    project_b, _ = _add_analyzed_project(store, tmp_path, "project-b")
    plan_a = generate_learning_plan(store, project_a.id)
    plan_b = generate_learning_plan(store, project_b.id)
    injected = [dict(item) for item in plan_a["plan"]["items"]]
    injected[0]["source_ids"] = [plan_b["plan"]["items"][0]["source_ids"][0]]

    with pytest.raises(ValueError, match="plan analysis"):
        update_learning_plan(
            store,
            project_a.id,
            plan_a["plan"]["id"],
            items=injected,
        )
    with pytest.raises(CoachLearningPlanNotFoundError):
        update_learning_plan(
            store,
            project_b.id,
            plan_a["plan"]["id"],
            items=plan_a["plan"]["items"],
        )
    with pytest.raises(
        CoachLearningPlanConflictError,
        match="learning_plan_items_conflict",
    ):
        update_learning_plan(
            store,
            project_a.id,
            plan_a["plan"]["id"],
            items=plan_a["plan"]["items"],
            expected_items_hash="stale-client-hash",
        )


def test_source_gap_edit_is_allowed_only_without_invented_reading_sources(tmp_path):
    store, project, _ = _store_project(tmp_path)
    generated = generate_learning_plan(store, project.id)
    items = generated["plan"]["items"]
    original_source_id = items[0]["source_ids"][0]
    items[0]["item_type"] = "source_gap"
    items[0]["source_ids"] = []

    updated = update_learning_plan(
        store,
        project.id,
        generated["plan"]["id"],
        items=items,
    )
    assert updated["plan"]["items"][0]["item_type"] == "source_gap"
    assert updated["plan"]["items"][0]["reading_sources"] == []

    invalid = updated["plan"]["items"]
    invalid[0]["source_ids"] = [original_source_id]
    with pytest.raises(ValueError, match="must not invent"):
        update_learning_plan(
            store,
            project.id,
            generated["plan"]["id"],
            items=invalid,
        )


def test_model_can_only_enhance_text_and_invalid_output_falls_back(tmp_path):
    store, project, _ = _store_project(tmp_path)

    class TextModel:
        def generate_answer(self, prompt, hits):
            assert hits
            items = json.loads(prompt.split("\n", 1)[1])
            for item in items:
                item["objective"] = "模型润色：" + item["objective"]
            return json.dumps(items, ensure_ascii=False)

    class InvalidModel:
        def generate_answer(self, prompt, hits):
            return json.dumps(
                [
                    {
                        "stable_key": "invented",
                        "objective": "伪造任务",
                        "practice_question": "伪造问题",
                        "completion_criteria": "伪造标准",
                    }
                ],
                ensure_ascii=False,
            )

    enhanced = generate_learning_plan(
        store,
        project.id,
        llm_client=TextModel(),
    )
    fallback = generate_learning_plan(
        store,
        project.id,
        llm_client=InvalidModel(),
    )

    assert enhanced["generation_mode"] == "model"
    assert all(
        item["objective"].startswith("模型润色：")
        for item in enhanced["plan"]["items"]
    )
    assert fallback["generation_mode"] == "rule"
    assert "已回退规则草稿" in fallback["warning"]
    assert all(
        not item["objective"].startswith("伪造")
        for item in fallback["plan"]["items"]
    )


def test_generation_stops_when_all_project_points_are_mastered(tmp_path):
    store, project, _ = _store_project(tmp_path)
    for point in store.list_coach_knowledge_points(project.id):
        started = start_coach_assessment(
            store,
            project.id,
            "knowledge_point",
            point.id,
        )
        session = store.get_coach_assessment_session(
            project.id,
            started["id"],
        )
        assert session is not None
        question = session.questions[0]
        answer_coach_assessment(
            store,
            project.id,
            session.id,
            question.id,
            "；".join(question.expected_points),
            evaluation_mode="rule",
        )

    with pytest.raises(
        CoachLearningPlanConflictError,
        match="no_actionable_learning_gaps",
    ):
        generate_learning_plan(store, project.id)


def test_current_plan_is_empty_before_first_generation(tmp_path):
    store, project, _ = _store_project(tmp_path)

    current = build_current_learning_plan(store, project.id)

    assert current["draft"] is None
    assert current["confirmed"] is None
    assert current["history"] == []


def test_source_fingerprint_detects_change_when_stale_marker_was_missed(tmp_path):
    store = KnowledgeStore(tmp_path / "app.db")
    root = tmp_path / "project"
    root.mkdir()
    project = store.create_project("指纹项目", root)
    app = root / "app.py"
    ignored = root / "notes.log"
    app_content = "from fastapi import FastAPI\napp = FastAPI()\n"
    app.write_text(app_content, encoding="utf-8")
    ignored.write_text("first", encoding="utf-8")
    store.upsert_document(project.id, app, "app.py", app_content)
    document = store.upsert_document(
        project.id,
        ignored,
        "notes.log",
        "first",
    ).document
    analyze_project(store, project.id)
    changed = "second"
    checksum = hashlib.sha256(changed.encode("utf-8")).hexdigest()
    with sqlite3.connect(tmp_path / "app.db") as conn:
        conn.execute(
            "UPDATE documents SET content = ?, checksum = ? WHERE id = ?",
            (changed, checksum, document.id),
        )
    assert store.get_current_coach_analysis_run(project.id).status == "completed"

    with pytest.raises(CoachLearningPlanConflictError, match="analysis_stale"):
        generate_learning_plan(store, project.id)
    assert store.get_current_coach_analysis_run(project.id).status == "stale"
