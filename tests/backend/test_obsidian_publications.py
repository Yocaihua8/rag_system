from __future__ import annotations

import pytest

from backend.domain.coach_assessment import (
    answer_coach_assessment,
    start_coach_assessment,
)
from backend.domain.learning_plans import (
    confirm_learning_plan,
    generate_learning_plan,
)
from backend.domain.obsidian_bridge import (
    authenticate_obsidian_connection,
    complete_obsidian_pairing,
    start_obsidian_pairing,
)
from backend.domain.obsidian_protocol import text_sha256
from backend.domain.obsidian_publications import (
    ObsidianPublicationConflictError,
    ObsidianPublicationNotFoundError,
    confirm_obsidian_publication,
    pending_obsidian_publications,
    preview_obsidian_publication,
    record_obsidian_publication_result,
)
from backend.domain.project_analysis import analyze_project
from backend.storage import KnowledgeStore


def _ready_project(tmp_path):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    root = tmp_path / "project"
    root.mkdir()
    project = store.create_project("发布项目", root)
    source = root / "app.py"
    content = (
        "from fastapi import FastAPI\n"
        "import sqlite3\n"
        "app = FastAPI()\n"
    )
    source.write_text(content, encoding="utf-8")
    store.upsert_document(project.id, source, "app.py", content)
    analyze_project(store, project.id)
    started = start_obsidian_pairing(store, project.id)
    completed = complete_obsidian_pairing(
        store,
        started["pairing"]["code"],
        "vault-id",
        "学习 Vault",
    )
    connection = authenticate_obsidian_connection(
        store,
        {"authorization": f"Bearer {completed['token']}"},
    )
    return store, project, root, connection


def _apply_all(store, connection, publication):
    return record_obsidian_publication_result(
        store,
        connection,
        publication["id"],
        [
            {
                "revision_id": artifact["revision_id"],
                "status": "applied",
                "actual_hash": text_sha256(
                    f"plugin-final:{artifact['revision_id']}"
                ),
            }
            for artifact in publication["artifacts"]
        ],
    )


def test_preview_confirm_pending_and_result_keep_three_phase_boundary(tmp_path):
    store, project, _, connection = _ready_project(tmp_path)
    preview = preview_obsidian_publication(
        store,
        project.id,
        artifact_types=[
            "project_understanding",
            "knowledge_coverage",
        ],
    )
    publication = preview["publication"]

    assert publication["status"] == "draft"
    assert len(publication["artifacts"]) == 2
    for artifact in publication["artifacts"]:
        assert artifact["target_path"].startswith(
            f"{connection.output_root}/"
        )
        assert "knowledge_island_managed: true" in artifact["content"]
        assert (
            f"knowledge_island_revision: {publication['revision']}"
            in artifact["content"]
        )
        assert text_sha256(artifact["content"]) == artifact["content_hash"]
        assert artifact["expected_vault_hash"] == ""
    assert pending_obsidian_publications(store, connection)[
        "publications"
    ] == []

    confirmed = confirm_obsidian_publication(
        store,
        project.id,
        publication["id"],
    )
    pending = pending_obsidian_publications(store, connection)

    assert confirmed["publication"]["status"] == "queued"
    assert confirmed["replayed"] is False
    assert confirm_obsidian_publication(
        store,
        project.id,
        publication["id"],
    )["replayed"] is True
    assert [item["id"] for item in pending["publications"]] == [
        publication["id"]
    ]

    applied = _apply_all(store, connection, publication)
    assert applied["publication"]["status"] == "applied"
    assert pending_obsidian_publications(store, connection)[
        "publications"
    ] == []


def test_new_preview_uses_plugin_actual_hash_as_conflict_baseline(tmp_path):
    store, project, _, connection = _ready_project(tmp_path)
    first = preview_obsidian_publication(
        store,
        project.id,
        artifact_types=["project_understanding"],
    )["publication"]
    confirm_obsidian_publication(store, project.id, first["id"])
    applied = _apply_all(store, connection, first)
    actual_hash = applied["results"][0]["actual_hash"]

    second = preview_obsidian_publication(
        store,
        project.id,
        artifact_types=["project_understanding"],
    )["publication"]

    assert second["revision"] == first["revision"] + 1
    assert second["artifacts"][0]["stable_id"] == first["artifacts"][0][
        "stable_id"
    ]
    assert second["artifacts"][0]["expected_vault_hash"] == actual_hash


def test_full_preview_renders_confirmed_plan_and_assessment_without_scoring_basis(
    tmp_path,
):
    store, project, _, _ = _ready_project(tmp_path)
    points = store.list_coach_knowledge_points(project.id)
    session_view = start_coach_assessment(
        store,
        project.id,
        "knowledge_point",
        points[0].id,
    )
    stored_session = store.get_coach_assessment_session(
        project.id,
        session_view["id"],
    )
    question = stored_session.questions[0]
    answer_coach_assessment(
        store,
        project.id,
        stored_session.id,
        question.id,
        "；".join(question.expected_points),
        evaluation_mode="rule",
    )
    draft = generate_learning_plan(store, project.id)
    confirm_learning_plan(store, project.id, draft["plan"]["id"])

    preview = preview_obsidian_publication(store, project.id)
    artifacts = preview["publication"]["artifacts"]
    by_type = {}
    for artifact in artifacts:
        by_type.setdefault(artifact["artifact_type"], []).append(artifact)

    assert {
        "project_understanding",
        "knowledge_coverage",
        "learning_plan",
        "assessment_record",
    } <= set(by_type)
    assessment_content = by_type["assessment_record"][0]["content"]
    assert question.prompt in assessment_content
    assert "评分方式" in assessment_content
    assert "置信度" in assessment_content
    assert "expected_points" not in assessment_content
    assert "/评估记录/" in by_type["assessment_record"][0]["target_path"]


def test_stale_analysis_blocks_current_preview_but_history_can_be_rolled_back(
    tmp_path,
):
    store, project, root, connection = _ready_project(tmp_path)
    first = preview_obsidian_publication(
        store,
        project.id,
        artifact_types=["project_understanding"],
    )["publication"]
    confirm_obsidian_publication(store, project.id, first["id"])
    _apply_all(store, connection, first)
    changed = "from fastapi import FastAPI\napp = FastAPI(title='changed')\n"
    (root / "app.py").write_text(changed, encoding="utf-8")
    store.upsert_document(project.id, root / "app.py", "app.py", changed)

    with pytest.raises(ObsidianPublicationConflictError, match="analysis_stale"):
        preview_obsidian_publication(
            store,
            project.id,
            artifact_types=["project_understanding"],
        )

    rollback = preview_obsidian_publication(
        store,
        project.id,
        source_publication_id=first["id"],
    )
    rolled = rollback["publication"]
    assert rollback["source_mode"] == "rollback"
    assert rolled["revision"] == first["revision"] + 1
    assert "# 项目理解" in rolled["artifacts"][0]["content"]
    assert (
        f"knowledge_island_revision: {rolled['revision']}"
        in rolled["artifacts"][0]["content"]
    )


def test_publication_result_rejects_cross_connection_and_invalid_success_hash(
    tmp_path,
):
    store, project, _, connection = _ready_project(tmp_path)
    publication = preview_obsidian_publication(
        store,
        project.id,
        artifact_types=["project_understanding"],
    )["publication"]
    confirm_obsidian_publication(store, project.id, publication["id"])
    artifact = publication["artifacts"][0]

    with pytest.raises(ValueError, match="valid actual_hash"):
        record_obsidian_publication_result(
            store,
            connection,
            publication["id"],
            [
                {
                    "revision_id": artifact["revision_id"],
                    "status": "applied",
                    "actual_hash": "not-a-hash",
                }
            ],
        )

    store.revoke_obsidian_connection(project.id, connection.id)
    started = start_obsidian_pairing(store, project.id)
    completed = complete_obsidian_pairing(
        store,
        started["pairing"]["code"],
        "new-vault",
        "New Vault",
    )
    new_connection = authenticate_obsidian_connection(
        store,
        {"authorization": f"Bearer {completed['token']}"},
    )
    with pytest.raises(
        ObsidianPublicationNotFoundError,
        match="not found",
    ):
        record_obsidian_publication_result(
            store,
            new_connection,
            publication["id"],
            [
                {
                    "revision_id": artifact["revision_id"],
                    "status": "conflict",
                    "error_code": "connection_changed",
                }
            ],
        )
