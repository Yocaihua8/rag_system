import sqlite3
from pathlib import Path
from urllib.parse import quote

from webapp.api import answer_stream_events, dispatch
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


def test_chat_message_delete_api_removes_only_requested_message(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", tmp_path)
    first = store.create_chat_message(project.id, "问题一", "回答一", "local", "local", "", [])
    second = store.create_chat_message(project.id, "问题二", "回答二", "local", "local", "", [])

    response = dispatch(store, "POST", "/api/chat/messages/delete", {"message_id": first.id})

    assert response.status == 200
    assert response.body["deleted"] is True
    assert [message["id"] for message in response.body["messages"]] == [second.id]
    assert [message.id for message in store.list_chat_messages(project.id)] == [second.id]


def test_chat_message_delete_api_rejects_missing_or_unknown_message(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    missing_id_response = dispatch(store, "POST", "/api/chat/messages/delete", {})
    unknown_response = dispatch(store, "POST", "/api/chat/messages/delete", {"message_id": "missing"})

    assert missing_id_response.status == 400
    assert missing_id_response.body["error"] == "message_id is required"
    assert unknown_response.status == 404
    assert unknown_response.body["error"] == "chat message not found"


def test_chat_messages_clear_api_removes_only_current_project_messages(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", tmp_path / "a")
    other_project = store.create_project("其他项目", tmp_path / "b")
    store.create_chat_message(project.id, "问题一", "回答一", "local", "local", "", [])
    store.create_chat_message(project.id, "问题二", "回答二", "local", "local", "", [])
    other_message = store.create_chat_message(other_project.id, "其他问题", "其他回答", "local", "local", "", [])

    response = dispatch(store, "POST", "/api/chat/messages/clear", {"project_id": project.id})

    assert response.status == 200
    assert response.body == {"deleted": 2, "messages": []}
    assert store.list_chat_messages(project.id) == []
    assert [message.id for message in store.list_chat_messages(other_project.id)] == [other_message.id]


def test_chat_messages_clear_api_rejects_missing_or_unknown_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    missing_id_response = dispatch(store, "POST", "/api/chat/messages/clear", {})
    unknown_response = dispatch(store, "POST", "/api/chat/messages/clear", {"project_id": "missing"})

    assert missing_id_response.status == 400
    assert missing_id_response.body["error"] == "project_id is required"
    assert unknown_response.status == 404
    assert unknown_response.body["error"] == "project not found"


def test_chat_sessions_api_creates_lists_renames_and_deletes_sessions(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    create_response = dispatch(
        store,
        "POST",
        "/api/chat/sessions",
        {"project_id": project.id, "title": "架构说明"},
    )
    session_id = create_response.body["session"]["id"]
    list_response = dispatch(store, "GET", f"/api/chat/sessions?project_id={project.id}")
    rename_response = dispatch(
        store,
        "POST",
        "/api/chat/sessions/rename",
        {"session_id": session_id, "title": "接口排查"},
    )
    delete_response = dispatch(
        store,
        "POST",
        "/api/chat/sessions/delete",
        {"session_id": session_id},
    )

    assert create_response.status == 200
    assert create_response.body["session"]["project_id"] == project.id
    assert create_response.body["session"]["title"] == "架构说明"
    assert list_response.body["sessions"][0]["id"] == session_id
    assert rename_response.body["session"]["title"] == "接口排查"
    assert delete_response.status == 200
    assert delete_response.body["deleted"] is True
    assert delete_response.body["sessions"] == []


def test_chat_session_messages_are_scoped_and_legacy_messages_remain_default(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, project_dir / "stack.md", "stack.md", "继续说明架构。")
    session = store.create_chat_session(project.id, "架构说明")
    legacy = store.create_chat_message(project.id, "旧问题", "旧回答", "local", "local", "", [])
    scoped = store.create_chat_message(
        project.id,
        "会话问题",
        "会话回答",
        "local",
        "local",
        "",
        [],
        session_id=session.id,
    )

    default_response = dispatch(store, "GET", f"/api/chat/messages?project_id={project.id}")
    session_response = dispatch(
        store,
        "GET",
        f"/api/chat/messages?project_id={project.id}&session_id={session.id}",
    )

    assert [message["id"] for message in default_response.body["messages"]] == [legacy.id]
    assert [message["id"] for message in session_response.body["messages"]] == [scoped.id]
    assert session_response.body["messages"][0]["session_id"] == session.id


def test_answer_api_writes_to_chat_session_and_uses_session_history(tmp_path: Path):
    class FakeLlmClient:
        provider = "deepseek"

        def __init__(self):
            self.history_questions = []

        def generate_answer(self, question, hits, history_messages=None):
            self.history_questions = [message.question for message in history_messages or []]
            return "会话回答"

    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, project_dir / "stack.md", "stack.md", "继续说明架构。")
    session = store.create_chat_session(project.id, "架构说明")
    other_session = store.create_chat_session(project.id, "接口排查")
    store.create_chat_message(project.id, "默认旧问题", "默认旧回答", "local", "local", "", [])
    store.create_chat_message(project.id, "会话旧问题", "会话旧回答", "local", "local", "", [], session_id=session.id)
    store.create_chat_message(project.id, "其他会话问题", "其他会话回答", "local", "local", "", [], session_id=other_session.id)
    client = FakeLlmClient()

    response = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project.id, "question": "继续说明", "session_id": session.id},
        llm_client=client,
    )

    assert response.status == 200
    assert response.body["message"]["session_id"] == session.id
    assert client.history_questions == ["会话旧问题"]


def test_chat_session_api_rejects_cross_project_session(tmp_path: Path):
    project_dir = tmp_path / "notes"
    other_dir = tmp_path / "other"
    project_dir.mkdir()
    other_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    other_project = store.create_project("其他项目", other_dir)
    other_session = store.create_chat_session(other_project.id, "其他会话")

    response = dispatch(
        store,
        "GET",
        f"/api/chat/messages?project_id={project.id}&session_id={other_session.id}",
    )

    assert response.status == 404
    assert response.body["error"] == "chat session not found"


def test_chat_message_delete_returns_current_session_messages(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", tmp_path)
    session = store.create_chat_session(project.id, "架构说明")
    first = store.create_chat_message(project.id, "问题一", "回答一", "local", "local", "", [], session_id=session.id)
    second = store.create_chat_message(project.id, "问题二", "回答二", "local", "local", "", [], session_id=session.id)
    store.create_chat_message(project.id, "默认问题", "默认回答", "local", "local", "", [])

    response = dispatch(store, "POST", "/api/chat/messages/delete", {"message_id": first.id})

    assert response.status == 200
    assert [message["id"] for message in response.body["messages"]] == [second.id]


def test_chat_message_branch_fields_are_persisted_and_listed(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", tmp_path)
    session = store.create_chat_session(project.id, "架构说明")
    parent = store.create_chat_message(
        project.id,
        "默认入口是什么？",
        "默认入口是 app.py。",
        "local",
        "local",
        "",
        [],
        session_id=session.id,
    )

    first_branch = store.create_chat_message(
        project.id,
        "默认入口和 FastAPI 的关系是什么？",
        "app.py 启动 FastAPI 服务。",
        "local",
        "local",
        "",
        [],
        session_id=session.id,
        parent_message_id=parent.id,
    )
    second_branch = store.create_chat_message(
        project.id,
        "默认入口和 Vue 的关系是什么？",
        "app.py 托管 Vue 构建产物。",
        "local",
        "local",
        "",
        [],
        session_id=session.id,
        parent_message_id=parent.id,
    )

    messages = store.list_chat_messages(project.id, session.id)

    assert first_branch.parent_message_id == parent.id
    assert first_branch.branch_index == 1
    assert second_branch.parent_message_id == parent.id
    assert second_branch.branch_index == 2
    assert messages[1].to_dict()["parent_message_id"] == parent.id
    assert messages[1].to_dict()["branch_index"] == 1


def test_chat_message_branch_columns_are_backfilled_for_existing_database(tmp_path: Path):
    db_path = tmp_path / "app.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE chat_messages (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                session_id TEXT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                mode TEXT NOT NULL,
                provider TEXT NOT NULL,
                warning TEXT NOT NULL DEFAULT '',
                sources_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )

    store = KnowledgeStore(db_path)
    project = store.create_project("知识岛", tmp_path)
    message = store.create_chat_message(project.id, "问题", "回答", "local", "local", "", [])

    assert message.parent_message_id == ""
    assert message.branch_index == 0


def test_answer_api_persists_branch_message_when_parent_message_id_is_sent(tmp_path: Path):
    class FakeLlmClient:
        provider = "deepseek"

        def generate_answer(self, question, hits, history_messages=None, prompt_preset=None):
            assert question == "默认入口和 FastAPI 的关系是什么？"
            return "DeepSeek 回答：app.py 启动 FastAPI 服务。"

    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "stack.md",
        "stack.md",
        "默认入口是 app.py，本地 Web 服务使用 FastAPI 并托管 Vue 构建产物。",
    )
    session = store.create_chat_session(project.id, "架构说明")
    parent = store.create_chat_message(
        project.id,
        "默认入口是什么？",
        "默认入口是 app.py。",
        "local",
        "local",
        "",
        [],
        session_id=session.id,
    )

    response = dispatch(
        store,
        "POST",
        "/api/answer",
        {
            "project_id": project.id,
            "session_id": session.id,
            "parent_message_id": parent.id,
            "question": "默认入口和 FastAPI 的关系是什么？",
        },
        llm_client=FakeLlmClient(),
    )

    assert response.status == 200
    assert response.body["message"]["parent_message_id"] == parent.id
    assert response.body["message"]["branch_index"] == 1
    assert response.body["message"]["question"] == "默认入口和 FastAPI 的关系是什么？"
    assert store.get_chat_message(response.body["message"]["id"]).parent_message_id == parent.id


def test_answer_api_rejects_parent_message_from_other_session(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, project_dir / "stack.md", "stack.md", "默认入口是 app.py。")
    session = store.create_chat_session(project.id, "架构说明")
    other_session = store.create_chat_session(project.id, "接口排查")
    parent = store.create_chat_message(
        project.id,
        "其他会话问题",
        "其他会话回答",
        "local",
        "local",
        "",
        [],
        session_id=other_session.id,
    )

    response = dispatch(
        store,
        "POST",
        "/api/answer",
        {
            "project_id": project.id,
            "session_id": session.id,
            "parent_message_id": parent.id,
            "question": "重发问题",
        },
    )

    assert response.status == 404
    assert response.body["error"] == "parent chat message not found"


def test_answer_stream_done_payload_includes_branch_message_fields(tmp_path: Path):
    class FakeStreamingLlmClient:
        provider = "deepseek"

        def stream_answer(self, question, hits, history_messages=None, prompt_preset=None):
            yield "流式"
            yield "回答"

    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "stack.md",
        "stack.md",
        "默认入口是 app.py，本地 Web 服务使用 FastAPI 并托管 Vue 构建产物。",
    )
    session = store.create_chat_session(project.id, "架构说明")
    parent = store.create_chat_message(
        project.id,
        "默认入口是什么？",
        "默认入口是 app.py。",
        "local",
        "local",
        "",
        [],
        session_id=session.id,
    )

    events = list(
        answer_stream_events(
            store,
            (
                f"/api/answer/stream?project_id={project.id}"
                f"&session_id={session.id}"
                f"&parent_message_id={parent.id}"
                f"&question={quote('默认入口和 FastAPI 的关系是什么？')}"
            ),
            llm_client=FakeStreamingLlmClient(),
        )
    )
    done = [event for event in events if event.event == "done"][0]

    assert done.data["message"]["parent_message_id"] == parent.id
    assert done.data["message"]["branch_index"] == 1
