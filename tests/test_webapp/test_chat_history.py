from pathlib import Path

from webapp.api import dispatch
from webapp.storage import KnowledgeStore


def test_answer_api_persists_project_chat_message_with_sources(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "stack.md",
        "stack.md",
        "默认入口是 app.py，本地 Web 服务负责页面和 API。",
    )

    answer_response = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project.id, "question": "默认入口是什么？"},
    )
    history_response = dispatch(store, "GET", f"/api/chat/messages?project_id={project.id}")

    assert answer_response.status == 200
    assert history_response.status == 200
    assert len(history_response.body["messages"]) == 1
    message = history_response.body["messages"][0]
    assert message["project_id"] == project.id
    assert message["question"] == "默认入口是什么？"
    assert "app.py" in message["answer"]
    assert message["mode"] == "local"
    assert message["provider"] == "local"
    assert message["warning"] == ""
    assert message["sources"][0]["path"] == "stack.md"
    assert message["sources"][0]["score"] > 0
    assert message["created_at"]


def test_chat_history_api_rejects_missing_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(store, "GET", "/api/chat/messages?project_id=missing")

    assert response.status == 404
    assert response.body["error"] == "project not found"
