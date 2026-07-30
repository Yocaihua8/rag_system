from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.dispatch import dispatch
from backend.api.server import create_app
from backend.storage import KnowledgeStore


def test_v2_project_coach_to_obsidian_publication_round_trip(tmp_path: Path):
    project_root = tmp_path / "coach-project"
    project_root.mkdir()
    (project_root / "app.py").write_text(
        "from fastapi import FastAPI\n"
        "app = FastAPI(title='Knowledge Island Coach')\n",
        encoding="utf-8",
    )
    (project_root / "README.md").write_text(
        "# 项目说明\n\n项目入口是 app.py，FastAPI 提供本地知识教练接口。",
        encoding="utf-8",
    )
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)

    created = dispatch(
        store,
        "POST",
        "/api/projects",
        {"name": "教练 E2E", "path": str(project_root)},
    )
    assert created.status == 201
    project_id = created.body["project"]["id"]

    imported = dispatch(
        store,
        "POST",
        "/api/import",
        {"project_id": project_id},
    )
    assert imported.status == 200
    assert imported.body["result"]["imported"] == 2

    analyzed = dispatch(
        store,
        "POST",
        "/api/coach/analyze",
        {"project_id": project_id},
    )
    assert analyzed.status == 200
    assert analyzed.body["analysis"]["status"] == "completed"
    assert analyzed.body["analysis"]["source_ids"]

    answered = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project_id, "question": "项目入口和框架是什么？"},
    )
    assert answered.status == 200
    assert answered.body["mode"] == "local"
    assert answered.body["sources"]
    with TestClient(create_app(store=store)) as client:
        streamed = client.get(
            "/api/answer/stream",
            params={
                "project_id": project_id,
                "question": "项目入口和框架是什么？",
            },
        )
    assert streamed.status_code == 200
    assert streamed.headers["content-type"].startswith("text/event-stream")
    assert "event: token" in streamed.text
    assert "event: done" in streamed.text

    knowledge_points = dispatch(
        store,
        "GET",
        f"/api/coach/knowledge-points?project_id={project_id}",
    ).body["knowledge_points"]["items"]
    assert knowledge_points
    started = dispatch(
        store,
        "POST",
        "/api/coach/assessments/start",
        {
            "project_id": project_id,
            "target_type": "knowledge_point",
            "target_id": knowledge_points[0]["id"],
        },
    )
    assert started.status == 200
    session = started.body["session"]
    assert session["questions"]
    assert all("expected_points" not in item for item in session["questions"])

    stored_session = store.get_coach_assessment_session(project_id, session["id"])
    assert stored_session is not None
    question = stored_session.questions[0]
    assessment = dispatch(
        store,
        "POST",
        "/api/coach/assessments/answer",
        {
            "project_id": project_id,
            "session_id": session["id"],
            "question_id": question.id,
            "answer": "；".join(question.expected_points),
            "evaluation_mode": "rule",
        },
    )
    assert assessment.status == 200
    assert assessment.body["result"]["status"] == "mastered"
    assert assessment.body["result"]["evaluator"] == "rule"
    assert assessment.body["replayed"] is False
    assert assessment.body["result"]["source_ids"]
    assert all(
        source_id in assessment.body["session"]["sources"]
        for source_id in assessment.body["result"]["source_ids"]
    )

    coverage = dispatch(
        store,
        "GET",
        f"/api/coach/coverage?project_id={project_id}",
    )
    assert coverage.status == 200
    assert coverage.body["coverage"]["summary"]["assessed_count"] == 1
    related_skills = [
        item
        for item in coverage.body["coverage"]["skills"]
        if knowledge_points[0]["id"] in item["knowledge_point_ids"]
    ]
    assert related_skills
    assert any(
        item["assessment_state"] != "unverified" for item in related_skills
    )
    assert coverage.body["coverage"]["scope_notice"]

    generated = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/generate",
        {"project_id": project_id},
    )
    assert generated.status == 200
    plan = generated.body["plan"]
    assert plan["items"]
    edited_items = [dict(item) for item in reversed(plan["items"])]
    edited_items[0]["objective"] = "先理解项目入口与 FastAPI 边界"
    updated_plan = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/update",
        {
            "project_id": project_id,
            "plan_id": plan["id"],
            "items": edited_items,
            "expected_revision": plan["revision"],
            "expected_items_hash": plan["items_hash"],
        },
    )
    assert updated_plan.status == 200
    assert (
        updated_plan.body["plan"]["items"][0]["objective"]
        == "先理解项目入口与 FastAPI 边界"
    )
    confirmed_plan = dispatch(
        store,
        "POST",
        "/api/coach/learning-plans/confirm",
        {
            "project_id": project_id,
            "plan_id": plan["id"],
            "expected_items_hash": updated_plan.body["plan"]["items_hash"],
        },
    )
    assert confirmed_plan.status == 200
    assert confirmed_plan.body["plan"]["status"] == "confirmed"

    pairing = dispatch(
        store,
        "POST",
        "/api/obsidian/pairing/start",
        {
            "project_id": project_id,
            "output_root": "Knowledge Island/教练 E2E",
        },
    )
    assert pairing.status == 200
    connected = dispatch(
        store,
        "POST",
        "/api/obsidian/pairing/complete",
        {
            "code": pairing.body["pairing"]["code"],
            "vault_id": "e2e-vault",
            "vault_name": "E2E Vault",
        },
    )
    assert connected.status == 200
    plugin_context = {
        "authorization": f"Bearer {connected.body['token']}",
    }

    preview = dispatch(
        store,
        "POST",
        "/api/obsidian/publications/preview",
        {"project_id": project_id},
    )
    assert preview.status == 200
    publication = preview.body["publication"]
    assert publication["status"] == "draft"
    artifact_types = {
        artifact["artifact_type"]
        for artifact in publication["artifacts"]
    }
    assert {
        "project_understanding",
        "knowledge_coverage",
        "learning_plan",
        "assessment_record",
    } <= artifact_types
    assert all(
        "knowledge_island_managed:" in artifact["content"]
        for artifact in publication["artifacts"]
    )

    confirmed_publication = dispatch(
        store,
        "POST",
        "/api/obsidian/publications/confirm",
        {
            "project_id": project_id,
            "publication_id": publication["id"],
        },
    )
    assert confirmed_publication.status == 200
    assert confirmed_publication.body["replayed"] is False
    assert confirmed_publication.body["publication"]["status"] == "queued"
    pending = dispatch(
        store,
        "GET",
        "/api/obsidian/publications/pending",
        request_context=plugin_context,
    )
    assert pending.status == 200
    assert pending.body["publications"][0]["id"] == publication["id"]

    applied = dispatch(
        store,
        "POST",
        "/api/obsidian/publications/result",
        {
            "publication_id": publication["id"],
            "results": [
                {
                    "revision_id": artifact["revision_id"],
                    "status": "applied",
                    "actual_hash": artifact["content_hash"],
                }
                for artifact in publication["artifacts"]
            ],
        },
        request_context=plugin_context,
    )
    assert applied.status == 200
    assert applied.body["publication"]["status"] == "applied"
