from __future__ import annotations

from pathlib import Path

from backend.api.dispatch import dispatch
from backend.storage import KnowledgeStore


def _analyzed_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    root = tmp_path / "project"
    root.mkdir()
    project = store.create_project("学习计划", root)
    source = root / "app.py"
    content = (
        "from fastapi import FastAPI\n"
        "import sqlite3\n"
        "app = FastAPI()\n"
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
    return store, project, root


def test_learning_plan_api_round_trip_preserves_confirmed_plan(tmp_path):
    store, project, _ = _analyzed_project(tmp_path)
    generated = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/generate",
        {"project_id": project.id},
    )
    plan = generated.body["plan"]
    edited = list(reversed(plan["items"]))
    edited[0]["objective"] = "优先完成的学习任务"
    updated = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/update",
        {
            "project_id": project.id,
            "plan_id": plan["id"],
            "items": edited,
            "expected_revision": plan["revision"],
            "expected_items_hash": plan["items_hash"],
        },
    )
    confirmed = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/confirm",
        {
            "project_id": project.id,
            "plan_id": plan["id"],
            "expected_items_hash": updated.body["plan"]["items_hash"],
        },
    )
    progressed = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/update",
        {
            "project_id": project.id,
            "plan_id": plan["id"],
            "item_statuses": {
                confirmed.body["plan"]["items"][0]["stable_key"]: "done"
            },
        },
    )
    next_draft = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/generate",
        {"project_id": project.id},
    )
    current = dispatch(
        store,
        "GET",
        f"/api/coach/learning-plans/current?project_id={project.id}",
    )

    assert generated.status == 200
    assert generated.body["generation_mode"] == "rule"
    assert updated.status == 200
    assert updated.body["plan"]["items"][0]["objective"] == "优先完成的学习任务"
    assert confirmed.status == 200
    assert confirmed.body["plan"]["status"] == "confirmed"
    assert progressed.body["plan"]["items"][0]["status"] == "done"
    assert next_draft.body["plan"]["revision"] == plan["revision"] + 1
    assert current.status == 200
    assert current.body["current"]["draft"]["id"] == next_draft.body["plan"]["id"]
    assert current.body["current"]["confirmed"]["id"] == plan["id"]


def test_learning_plan_api_current_returns_empty_state_after_analysis(tmp_path):
    store, project, _ = _analyzed_project(tmp_path)

    response = dispatch(
        store,
        "GET",
        f"/api/coach/learning-plans/current?project_id={project.id}",
    )

    assert response.status == 200
    assert response.body["current"]["draft"] is None
    assert response.body["current"]["confirmed"] is None


def test_learning_plan_api_rejects_invalid_update_modes_and_plan_states(tmp_path):
    store, project, _ = _analyzed_project(tmp_path)
    generated = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/generate",
        {"project_id": project.id},
    )
    plan = generated.body["plan"]
    both_modes = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/update",
        {
            "project_id": project.id,
            "plan_id": plan["id"],
            "items": plan["items"],
            "item_statuses": {plan["items"][0]["id"]: "done"},
        },
    )
    draft_progress = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/update",
        {
            "project_id": project.id,
            "plan_id": plan["id"],
            "item_statuses": {plan["items"][0]["id"]: "done"},
        },
    )
    dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/confirm",
        {"project_id": project.id, "plan_id": plan["id"]},
    )
    confirmed_structure = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/update",
        {
            "project_id": project.id,
            "plan_id": plan["id"],
            "items": plan["items"],
        },
    )

    assert both_modes.status == 400
    assert both_modes.body == {
        "error": "provide exactly one of items or item_statuses"
    }
    assert draft_progress.status == 409
    assert draft_progress.body == {
        "error": "learning_plan_progress_not_editable"
    }
    assert confirmed_structure.status == 409
    assert confirmed_structure.body == {"error": "learning_plan_not_editable"}


def test_learning_plan_api_maps_missing_analysis_stale_and_cross_project(tmp_path):
    store = KnowledgeStore(tmp_path / "app.db")
    empty_root = tmp_path / "empty"
    empty_root.mkdir()
    empty = store.create_project("空项目", empty_root)
    no_analysis = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/generate",
        {"project_id": empty.id},
    )

    root = tmp_path / "project"
    root.mkdir()
    project = store.create_project("项目 A", root)
    source = root / "app.py"
    content = "from fastapi import FastAPI\napp = FastAPI()\n"
    source.write_text(content, encoding="utf-8")
    store.upsert_document(project.id, source, "app.py", content)
    dispatch(store, "POST", "/api/coach/analyze", {"project_id": project.id})
    generated = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/generate",
        {"project_id": project.id},
    )
    changed = "from fastapi import FastAPI\napp = FastAPI(title='changed')\n"
    source.write_text(changed, encoding="utf-8")
    store.upsert_document(project.id, source, "app.py", changed)
    stale_generate = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/generate",
        {"project_id": project.id},
    )
    stale_confirm = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/confirm",
        {"project_id": project.id, "plan_id": generated.body["plan"]["id"]},
    )
    cross_project = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/confirm",
        {"project_id": empty.id, "plan_id": generated.body["plan"]["id"]},
    )

    assert no_analysis.status == 404
    assert no_analysis.body == {"error": "coach analysis not found"}
    assert stale_generate.status == 409
    assert stale_generate.body == {"error": "analysis_stale"}
    assert stale_confirm.status == 409
    assert stale_confirm.body == {"error": "analysis_stale"}
    assert cross_project.status == 404
    assert cross_project.body == {"error": "learning plan not found"}
