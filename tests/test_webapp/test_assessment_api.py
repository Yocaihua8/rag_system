from pathlib import Path

from webapp.api import dispatch
from webapp.storage import KnowledgeStore


def test_assessment_start_generates_questions_from_imported_documents(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "README.md",
        "README.md",
        "# 默认入口\n\napp.py 启动本地 Web 服务，SQLite 保存项目资料。",
    )

    response = dispatch(
        store,
        "POST",
        "/api/assessment/start",
        {"project_id": project.id},
    )

    assert response.status == 200
    assert response.body["session"]["project_id"] == project.id
    assert response.body["session"]["questions"][0]["source_path"] == "README.md"
    assert "README.md" in response.body["session"]["questions"][0]["prompt"]
    assert response.body["session"]["questions"][0]["expected_points"]


def test_assessment_start_rejects_project_without_documents(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(
        store,
        "POST",
        "/api/assessment/start",
        {"project_id": project.id},
    )

    assert response.status == 400
    assert response.body["error"] == "assessment requires imported documents"


def test_assessment_answer_returns_feedback_and_reading_source(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "README.md",
        "README.md",
        "app.py 启动本地 Web 服务，SQLite 保存项目资料。",
    )
    start = dispatch(store, "POST", "/api/assessment/start", {"project_id": project.id})
    question = start.body["session"]["questions"][0]

    response = dispatch(
        store,
        "POST",
        "/api/assessment/answer",
        {
            "project_id": project.id,
            "question": question,
            "answer": "app.py 启动 Web 服务，并使用 SQLite 保存项目资料。",
        },
    )

    assert response.status == 200
    assert response.body["result"]["status"] in {"已掌握", "基本理解", "需要补充"}
    assert response.body["result"]["source_path"] == "README.md"
    assert response.body["result"]["feedback"]
