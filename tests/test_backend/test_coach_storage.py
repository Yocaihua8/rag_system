from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from backend.config.settings import load_settings
from backend.storage import DataGenerationMismatchError, KnowledgeStore


def _isolate_settings(monkeypatch, tmp_path):
    import backend.config.settings as settings_module

    monkeypatch.setattr(settings_module, "_project_root", lambda: tmp_path)
    monkeypatch.setattr(settings_module, "app_data_dir", lambda: tmp_path / "appdata")
    monkeypatch.setattr(settings_module, "_persistent_env", lambda: {})
    monkeypatch.delenv("RAG_RUNTIME_DIR", raising=False)


def _analysis_draft(document, chunk):
    points = [
        {
            "stable_key": "architecture:web-entry",
            "title": "Web 入口",
            "category": "architecture",
            "summary": "项目由 app.py 启动 Web 服务。",
            "sources": [
                {
                    "document_id": document.id,
                    "chunk_id": chunk.id,
                    "source_path": document.relative_path,
                    "source_hash": document.checksum,
                    "excerpt": "默认入口是 app.py。",
                    "locator": {"line_start": 1, "line_end": 1},
                }
            ],
        }
    ]
    nodes = [
        {
            "stable_key": "delivery",
            "name": "交付",
            "category": "delivery",
            "sort_order": 1,
        },
        {
            "stable_key": "delivery:web-runtime",
            "parent_key": "delivery",
            "name": "Web 运行时",
            "category": "delivery",
            "sort_order": 2,
        },
    ]
    mappings = [
        {
            "knowledge_point_key": "architecture:web-entry",
            "skill_key": "delivery:web-runtime",
            "confidence": 0.9,
            "rationale": "入口文件直接说明服务启动方式。",
            "source_path": document.relative_path,
            "source_hash": document.checksum,
        }
    ]
    return points, nodes, mappings


def test_v2_defaults_use_isolated_runtime_and_qdrant_paths(tmp_path, monkeypatch):
    _isolate_settings(monkeypatch, tmp_path)
    settings = load_settings({})

    assert settings.runtime_dir == (tmp_path / "runtime" / "v2").resolve()
    assert settings.db_path == settings.runtime_dir / "app.db"
    assert settings.vector_dir == settings.runtime_dir / "vectors"
    assert settings.logs_dir == settings.runtime_dir / "logs"
    assert settings.outputs_dir == settings.runtime_dir / "outputs"


def test_new_database_has_v2_generation_marker_and_coach_tables(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    with sqlite3.connect(store.db_path) as conn:
        marker = conn.execute(
            "SELECT value FROM app_metadata WHERE key = 'data_generation'"
        ).fetchone()
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert marker == ("v2",)
    assert {
        "coach_analysis_runs",
        "coach_knowledge_points",
        "coach_knowledge_sources",
        "coach_skill_taxonomies",
        "coach_skill_nodes",
        "coach_knowledge_skill_mappings",
    } <= tables


def test_strict_v2_generation_rejects_unmarked_database_without_writing_or_vector_init(
    tmp_path: Path,
    monkeypatch,
):
    import backend.storage.knowledge_store as store_module

    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE projects (id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO projects (id) VALUES ('legacy')")
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()
    vector_initialized = False

    def unexpected_vector_init():
        nonlocal vector_initialized
        vector_initialized = True
        raise AssertionError("vector store must not initialize before generation validation")

    monkeypatch.setattr(store_module, "get_default_vector_store", unexpected_vector_init)

    with pytest.raises(DataGenerationMismatchError, match="unmarked database"):
        KnowledgeStore(db_path, expected_generation="v2")

    assert hashlib.sha256(db_path.read_bytes()).hexdigest() == before
    assert vector_initialized is False


def test_default_v2_store_does_not_touch_existing_v1_runtime_files(
    tmp_path: Path,
    monkeypatch,
):
    _isolate_settings(monkeypatch, tmp_path)
    old_runtime = tmp_path / "runtime"
    old_runtime.mkdir()
    old_db = old_runtime / "app.db"
    old_vectors = old_runtime / "vectors"
    old_outputs = old_runtime / "outputs"
    old_db.write_bytes(b"legacy-database-sentinel")
    old_vectors.mkdir()
    old_outputs.mkdir()
    (old_vectors / "index.bin").write_bytes(b"legacy-vector")
    (old_outputs / "answer.md").write_text("legacy output", encoding="utf-8")
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (
            old_db,
            old_vectors / "index.bin",
            old_outputs / "answer.md",
        )
    }

    settings = load_settings({})
    KnowledgeStore(settings.db_path, expected_generation="v2")

    assert settings.db_path == old_runtime / "v2" / "app.db"
    assert {
        path: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in before
    } == before


def test_coach_analysis_save_is_atomic_and_preserves_stable_ids(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", tmp_path / "project")
    document = store.upsert_document(
        project.id,
        tmp_path / "project" / "README.md",
        "README.md",
        "默认入口是 app.py。",
    ).document
    chunk = store.list_chunks(project.id)[0]
    points, nodes, mappings = _analysis_draft(document, chunk)
    run = store.create_coach_analysis_run(project.id, "rules-v1", "fingerprint-1")

    completed = store.save_coach_analysis_result(
        run.id,
        {
            "source_count": 1,
            "knowledge_point_count": 1,
            "skill_mapping_count": 1,
            "enhancement_mode": "rule",
            "warning": "",
        },
        points,
        {"version": "v1", "name": "通用开发技能树", "status": "active"},
        nodes,
        mappings,
    )

    first_point = store.list_coach_knowledge_points(project.id)[0]
    assert completed.status == "completed"
    assert completed.to_dict()["knowledge_point_count"] == 1
    assert first_point.stable_key == "architecture:web-entry"
    assert first_point.sources[0].document_id == document.id
    assert first_point.sources[0].source_hash == document.checksum
    assert [node.stable_key for node in store.list_coach_skill_nodes()] == [
        "delivery",
        "delivery:web-runtime",
    ]
    assert store.list_coach_skill_mappings(project.id)[0].source_id == first_point.sources[0].id

    second_run = store.create_coach_analysis_run(project.id, "rules-v1", "fingerprint-2")
    second_points, second_nodes, second_mappings = _analysis_draft(document, chunk)
    second_points[0]["summary"] = "更新后的项目入口说明。"
    store.save_coach_analysis_result(
        second_run.id,
        {"knowledge_point_count": 1},
        second_points,
        {"version": "v1", "name": "通用开发技能树", "status": "active"},
        second_nodes,
        second_mappings,
    )

    second_point = store.list_coach_knowledge_points(project.id)[0]
    assert second_point.id == first_point.id
    assert second_point.current_run_id == second_run.id


def test_source_update_and_delete_mark_analysis_stale_but_keep_snapshot(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", tmp_path / "project")
    document = store.upsert_document(
        project.id,
        tmp_path / "project" / "README.md",
        "README.md",
        "默认入口是 app.py。",
    ).document
    chunk = store.list_chunks(project.id)[0]
    points, nodes, mappings = _analysis_draft(document, chunk)
    run = store.create_coach_analysis_run(project.id, "rules-v1", "fingerprint-1")
    store.save_coach_analysis_result(
        run.id,
        {"knowledge_point_count": 1},
        points,
        {"version": "v1", "name": "通用开发技能树", "status": "active"},
        nodes,
        mappings,
    )

    store.upsert_document(
        project.id,
        tmp_path / "project" / "README.md",
        "README.md",
        "默认入口改为 backend.api.server。",
    )

    assert store.get_latest_coach_analysis_run(project.id).status == "stale"
    source_before_delete = store.list_coach_knowledge_points(
        project.id,
        run_id=run.id,
    )[0].sources[0]
    assert source_before_delete.document_id == document.id
    assert source_before_delete.source_hash == document.checksum

    store.delete_document(document.id)

    source_after_delete = store.list_coach_knowledge_points(
        project.id,
        run_id=run.id,
    )[0].sources[0]
    assert source_after_delete.document_id == ""
    assert source_after_delete.chunk_id == ""
    assert source_after_delete.source_path == "README.md"
    assert source_after_delete.source_hash == document.checksum
    assert source_after_delete.excerpt == "默认入口是 app.py。"


def test_new_document_marks_completed_project_analysis_stale(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", tmp_path / "project")
    document = store.upsert_document(
        project.id,
        tmp_path / "project" / "README.md",
        "README.md",
        "默认入口是 app.py。",
    ).document
    chunk = store.list_chunks(project.id)[0]
    points, nodes, mappings = _analysis_draft(document, chunk)
    run = store.create_coach_analysis_run(project.id, "rules-v1", "fingerprint-1")
    store.save_coach_analysis_result(
        run.id,
        {"knowledge_point_count": 1},
        points,
        {"version": "v1", "name": "通用开发技能树", "status": "active"},
        nodes,
        mappings,
    )

    store.upsert_document(
        project.id,
        tmp_path / "project" / "pyproject.toml",
        "pyproject.toml",
        "[project]\nname='knowledge-island'",
    )

    assert store.get_latest_coach_analysis_run(project.id).status == "stale"


def test_coach_source_requires_non_empty_excerpt(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", tmp_path / "project")
    document = store.upsert_document(
        project.id,
        tmp_path / "project" / "README.md",
        "README.md",
        "默认入口是 app.py。",
    ).document
    chunk = store.list_chunks(project.id)[0]
    points, nodes, mappings = _analysis_draft(document, chunk)
    points[0]["sources"][0]["excerpt"] = ""
    run = store.create_coach_analysis_run(project.id, "rules-v1", "fingerprint-1")

    with pytest.raises(ValueError, match="source excerpt is required"):
        store.save_coach_analysis_result(
            run.id,
            {},
            points,
            {"version": "v1", "name": "通用开发技能树", "status": "active"},
            nodes,
            mappings,
        )

    failed = store.get_latest_coach_analysis_run(project.id)
    assert failed.status == "failed"
    assert failed.finished_at
    assert failed.summary == {"error_type": "ValueError"}
    assert store.get_current_coach_analysis_run(project.id) is None


def test_invalid_coach_mapping_rolls_back_result_transaction(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", tmp_path / "project")
    document = store.upsert_document(
        project.id,
        tmp_path / "project" / "README.md",
        "README.md",
        "默认入口是 app.py。",
    ).document
    chunk = store.list_chunks(project.id)[0]
    points, nodes, mappings = _analysis_draft(document, chunk)
    mappings[0]["skill_key"] = "unknown"
    run = store.create_coach_analysis_run(project.id, "rules-v1", "fingerprint-1")

    with pytest.raises(ValueError, match="unknown skill key"):
        store.save_coach_analysis_result(
            run.id,
            {},
            points,
            {"version": "v1", "name": "通用开发技能树", "status": "active"},
            nodes,
            mappings,
        )

    assert store.get_latest_coach_analysis_run(project.id).status == "failed"
    assert store.get_current_coach_analysis_run(project.id) is None
    assert store.list_coach_knowledge_points(project.id) == []
    assert store.list_coach_skill_nodes() == []


def test_failed_reanalysis_does_not_hide_previous_completed_result(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", tmp_path / "project")
    document = store.upsert_document(
        project.id,
        tmp_path / "project" / "README.md",
        "README.md",
        "默认入口是 app.py。",
    ).document
    chunk = store.list_chunks(project.id)[0]
    points, nodes, mappings = _analysis_draft(document, chunk)
    completed_run = store.create_coach_analysis_run(
        project.id,
        "rules-v1",
        "fingerprint-1",
    )
    store.save_coach_analysis_result(
        completed_run.id,
        {"knowledge_point_count": 1},
        points,
        {"version": "v1", "name": "通用开发技能树", "status": "active"},
        nodes,
        mappings,
    )
    invalid_points, invalid_nodes, invalid_mappings = _analysis_draft(document, chunk)
    invalid_mappings[0]["skill_key"] = "unknown"
    failed_run = store.create_coach_analysis_run(
        project.id,
        "rules-v1",
        "fingerprint-2",
    )

    with pytest.raises(ValueError, match="unknown skill key"):
        store.save_coach_analysis_result(
            failed_run.id,
            {},
            invalid_points,
            {"version": "v1", "name": "通用开发技能树", "status": "active"},
            invalid_nodes,
            invalid_mappings,
        )

    assert store.get_latest_coach_analysis_run(project.id).id == failed_run.id
    assert store.get_latest_coach_analysis_run(project.id).status == "failed"
    assert store.get_current_coach_analysis_run(project.id).id == completed_run.id
    assert store.list_coach_knowledge_points(project.id)[0].stable_key == "architecture:web-entry"


def test_coach_source_rejects_document_from_another_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    first = store.create_project("项目 A", tmp_path / "project-a")
    second = store.create_project("项目 B", tmp_path / "project-b")
    foreign_document = store.upsert_document(
        second.id,
        tmp_path / "project-b" / "README.md",
        "README.md",
        "项目 B 的入口是 main.py。",
    ).document
    foreign_chunk = store.list_chunks(second.id)[0]
    points, nodes, mappings = _analysis_draft(foreign_document, foreign_chunk)
    run = store.create_coach_analysis_run(first.id, "rules-v1", "fingerprint-1")

    with pytest.raises(ValueError, match="does not belong to the analysis project"):
        store.save_coach_analysis_result(
            run.id,
            {},
            points,
            {"version": "v1", "name": "通用开发技能树", "status": "active"},
            nodes,
            mappings,
        )

    assert store.get_latest_coach_analysis_run(first.id).status == "failed"
    assert store.get_current_coach_analysis_run(first.id) is None
    assert store.list_coach_knowledge_points(first.id) == []


@pytest.mark.parametrize(
    ("source_changes", "message"),
    [
        ({"document_id": "", "chunk_id": ""}, "must reference an imported document"),
        ({"source_path": "forged.md"}, "source_path does not match"),
        ({"source_hash": "forged-checksum"}, "source_hash does not match"),
    ],
)
def test_coach_source_must_resolve_to_imported_document(
    tmp_path: Path,
    source_changes: dict[str, str],
    message: str,
):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", tmp_path / "project")
    document = store.upsert_document(
        project.id,
        tmp_path / "project" / "README.md",
        "README.md",
        "默认入口是 app.py。",
    ).document
    chunk = store.list_chunks(project.id)[0]
    points, nodes, mappings = _analysis_draft(document, chunk)
    points[0]["sources"][0].update(source_changes)
    run = store.create_coach_analysis_run(project.id, "rules-v1", "fingerprint-1")

    with pytest.raises(ValueError, match=message):
        store.save_coach_analysis_result(
            run.id,
            {},
            points,
            {"version": "v1", "name": "通用开发技能树", "status": "active"},
            nodes,
            mappings,
        )

    assert store.get_latest_coach_analysis_run(project.id).status == "failed"
