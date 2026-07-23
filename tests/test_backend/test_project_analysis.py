from __future__ import annotations

import json

from backend.domain.document_processing import process_local_file, process_uploaded_file
from backend.domain.project_analysis import (
    analyze_project,
    build_coach_overview,
    build_knowledge_points_view,
    build_skills_view,
)
from backend.storage import KnowledgeStore


def _project_store(tmp_path):
    store = KnowledgeStore(tmp_path / "app.db")
    root = tmp_path / "project"
    root.mkdir()
    project = store.create_project("示例项目", root)
    return store, project, root


def _add_document(store, project, root, path: str, content: str):
    source = root / path
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(content, encoding="utf-8")
    return store.upsert_document(project.id, source, path, content).document


def _point_keys(view):
    return {item["stable_key"] for item in view["items"]}


def _assert_sources_resolve(points_view, skills_view):
    sources = points_view["sources"]
    assert sources
    for point in points_view["items"]:
        assert point["source_ids"]
        for source_id in point["source_ids"]:
            source = sources[source_id]
            assert source["path"]
            assert source["source_hash"]
            assert source["excerpt"]
            assert source["locator"]
    for skill in skills_view["items"]:
        for mapping in skill["mappings"]:
            assert mapping["source_ids"]
            assert all(source_id in sources for source_id in mapping["source_ids"])


def test_python_project_analysis_has_stable_sourced_knowledge_and_skills(tmp_path):
    store, project, root = _project_store(tmp_path)
    _add_document(
        store,
        project,
        root,
        "pyproject.toml",
        """
[project]
name = "coach-api"
dependencies = ["fastapi", "sqlalchemy"]

[tool.pytest.ini_options]
testpaths = ["tests"]
""".strip(),
    )
    _add_document(
        store,
        project,
        root,
        "app.py",
        "from fastapi import FastAPI\nimport sqlite3\napp = FastAPI()\n",
    )
    _add_document(store, project, root, "tests/test_app.py", "def test_health():\n    assert True\n")

    analysis = analyze_project(store, project.id)
    points = build_knowledge_points_view(store, project.id)
    skills = build_skills_view(store, project.id)
    overview = build_coach_overview(store, project.id)

    assert analysis["status"] == "completed"
    assert analysis["enhancement_mode"] == "rule"
    assert analysis["source_count"] == 3
    assert {"language:python", "framework:fastapi", "testing:pytest", "data:sqlite"} <= _point_keys(points)
    assert any(key.startswith("entrypoint:") for key in _point_keys(points))
    assert overview["status"] == "completed"
    assert overview["source_ids"]
    _assert_sources_resolve(points, skills)


def test_vue_typescript_project_analysis_detects_manifest_signals(tmp_path):
    store, project, root = _project_store(tmp_path)
    _add_document(
        store,
        project,
        root,
        "package.json",
        json.dumps(
            {
                "dependencies": {"vue": "^3.5.0"},
                "devDependencies": {
                    "typescript": "^5.0.0",
                    "vite": "^7.0.0",
                    "vitest": "^3.0.0",
                    "@playwright/test": "^1.0.0",
                },
                "scripts": {"dev": "vite", "test": "vitest", "e2e": "playwright test"},
            }
        ),
    )
    _add_document(store, project, root, "src/main.ts", "import { createApp } from 'vue'\n")

    analyze_project(store, project.id)
    points = build_knowledge_points_view(store, project.id)
    skills = build_skills_view(store, project.id)

    assert {
        "language:javascript",
        "language:typescript",
        "framework:vue",
        "framework:vite",
        "testing:vitest",
        "testing:playwright",
        "workflow:package-scripts",
    } <= _point_keys(points)
    _assert_sources_resolve(points, skills)


def test_generic_text_project_uses_sourced_fallback_without_inventing_framework(tmp_path):
    store, project, root = _project_store(tmp_path)
    _add_document(store, project, root, "README.md", "# 审批说明\n\n本项目记录人工审批流程。")
    _add_document(store, project, root, "docs/architecture.txt", "输入经过校验后写入本地记录。")

    analyze_project(store, project.id)
    points = build_knowledge_points_view(store, project.id)
    skills = build_skills_view(store, project.id)

    keys = _point_keys(points)
    assert "project:overview" in keys
    assert "project:structure" in keys
    assert any(key.startswith("document:") for key in keys)
    assert not any(key.startswith("framework:") for key in keys)
    _assert_sources_resolve(points, skills)


def test_source_change_marks_old_analysis_stale_and_reanalysis_keeps_point_id(tmp_path):
    store, project, root = _project_store(tmp_path)
    document = _add_document(store, project, root, "README.md", "# 项目\n\n第一版说明。")
    first_analysis = analyze_project(store, project.id)
    first_points = build_knowledge_points_view(store, project.id)
    first_ids = {item["stable_key"]: item["id"] for item in first_points["items"]}

    store.upsert_document(
        project.id,
        root / "README.md",
        "README.md",
        "# 项目\n\n第二版说明。",
    )

    stale = build_coach_overview(store, project.id)
    assert stale["status"] == "stale"
    assert stale["analysis"]["id"] == first_analysis["id"]

    second_analysis = analyze_project(store, project.id)
    second_points = build_knowledge_points_view(store, project.id)
    second_ids = {item["stable_key"]: item["id"] for item in second_points["items"]}

    assert second_analysis["id"] != first_analysis["id"]
    assert second_analysis["source_fingerprint"] != first_analysis["source_fingerprint"]
    assert second_ids["project:overview"] == first_ids["project:overview"]
    assert second_ids["project:structure"] == first_ids["project:structure"]
    assert document.id == store.list_documents(project.id)[0].id


def test_llm_summary_enhancement_is_optional_and_falls_back_safely(tmp_path):
    class SuccessfulLlm:
        def generate_answer(self, question, hits):
            assert question
            assert hits
            return "模型增强摘要，但知识点与来源仍由规则确定。"

    class FailingLlm:
        def generate_answer(self, question, hits):
            raise RuntimeError("offline")

    store, project, root = _project_store(tmp_path)
    _add_document(store, project, root, "README.md", "# 项目\n\n本地项目资料。")

    enhanced = analyze_project(store, project.id, llm_client=SuccessfulLlm())
    assert enhanced["enhancement_mode"] == "model"
    assert enhanced["summary"]["overview"].startswith("模型增强摘要")

    fallback = analyze_project(store, project.id, llm_client=FailingLlm())
    assert fallback["enhancement_mode"] == "rule"
    assert "RuntimeError" in fallback["warning"]
    assert fallback["status"] == "completed"


def test_common_extensionless_manifests_and_toml_are_importable(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    dockerfile = root / "Dockerfile"
    makefile = root / "Makefile"
    pyproject = root / "pyproject.toml"
    dockerfile.write_text("FROM python:3.11", encoding="utf-8")
    makefile.write_text("test:\n\tpytest", encoding="utf-8")
    pyproject.write_text("[project]\nname='demo'", encoding="utf-8")

    assert process_local_file(dockerfile, root).is_importable
    assert process_local_file(makefile, root).is_importable
    assert process_local_file(pyproject, root).is_importable
    assert process_uploaded_file("Dockerfile", {"content": "FROM node:20"}).is_importable
