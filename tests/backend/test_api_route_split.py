from pathlib import Path

from backend.knowledge_island.api import dispatch
from backend.knowledge_island.routes import dispatch_to_routes
from backend.knowledge_island.routes.agent import handle_agent_route
from backend.knowledge_island.routes.admin import handle_admin_route
from backend.knowledge_island.routes.answers import handle_answer_route
from backend.knowledge_island.routes.assessment import handle_assessment_route
from backend.knowledge_island.routes.chat import handle_chat_route
from backend.knowledge_island.routes.documents import handle_documents_route
from backend.knowledge_island.routes.export import handle_export_route
from backend.knowledge_island.routes.health import handle_health_route
from backend.knowledge_island.routes.imports import handle_imports_route
from backend.knowledge_island.routes.projects import handle_projects_route
from backend.knowledge_island.routes.search import handle_search_route
from backend.knowledge_island.routes.settings import handle_settings_route
from backend.knowledge_island.storage import KnowledgeStore


class RouteSplitFakeLlmClient:
    def generate_answer(self, question, hits, history_messages=None, prompt_preset=None):
        return f"测试回答：{question}"


def test_health_route_module_handles_get_health():
    response = handle_health_route("GET", "/api/health")

    assert response is not None
    assert response.status == 200
    assert response.body == {"status": "ok"}
    assert handle_health_route("POST", "/api/health") is None


def test_route_registry_dispatches_health_route(tmp_path):
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch_to_routes(store, "GET", "/api/health", {}, {}, llm_client=None)

    assert response is not None
    assert response.status == 200
    assert response.body == {"status": "ok"}


def test_dispatch_keeps_health_api_contract(tmp_path):
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(store, "GET", "/api/health")

    assert response.status == 200
    assert response.body == {"status": "ok"}


def test_admin_route_module_handles_stats_and_rebuild_index(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, project_dir / "stack.md", "stack.md", "默认入口是 app.py。")

    stats_response = handle_admin_route(store, "GET", "/api/admin/stats", {}, {})
    rebuild_response = handle_admin_route(store, "POST", "/api/admin/rebuild-index", {}, {})

    assert stats_response is not None
    assert stats_response.status == 200
    assert stats_response.body["project_count"] == 1
    assert stats_response.body["chunk_count"] == 1
    assert stats_response.body["vector_count"] == 1
    assert stats_response.body["db_size_bytes"] > 0
    assert rebuild_response is not None
    assert rebuild_response.status == 200
    assert rebuild_response.body == {"status": "rebuild complete"}
    assert handle_admin_route(store, "GET", "/api/admin/unknown", {}, {}) is None


def test_route_registry_dispatches_admin_stats(tmp_path):
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch_to_routes(store, "GET", "/api/admin/stats", {}, {}, llm_client=None)

    assert response is not None
    assert response.status == 200
    assert "chunk_count" in response.body


def test_projects_route_module_handles_project_summary(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, project_dir / "stack.md", "stack.md", "默认入口是 app.py。")

    response = handle_projects_route(
        store,
        "GET",
        "/api/projects/summary",
        {"project_id": [project.id]},
        {},
    )
    missing_id_response = handle_projects_route(store, "GET", "/api/projects/summary", {}, {})
    unknown_project_response = handle_projects_route(
        store,
        "GET",
        "/api/projects/summary",
        {"project_id": ["missing"]},
        {},
    )

    assert response is not None
    assert response.status == 200
    assert response.body["summary"]["project_id"] == project.id
    assert response.body["summary"]["document_count"] == 1
    assert response.body["summary"]["chunk_count"] == 1
    assert response.body["summary"]["vector_count"] == 1
    assert missing_id_response is not None
    assert missing_id_response.status == 400
    assert missing_id_response.body["error"] == "project_id is required"
    assert unknown_project_response is not None
    assert unknown_project_response.status == 404
    assert unknown_project_response.body["error"] == "project not found"
    assert handle_projects_route(store, "POST", "/api/projects/summary", {}, {}) is None


def test_projects_route_module_handles_quality_summary(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    first = store.create_chat_message(
        project.id,
        "问题一",
        "回答一",
        "local",
        "local",
        "",
        [],
        quality_metrics={
            "source_coverage": 0.5,
            "retrieval_top_score": 0.9,
            "has_sources": True,
            "answer_length": 3,
        },
    )
    store.create_chat_message(
        project.id,
        "问题二",
        "回答二",
        "local",
        "local",
        "",
        [],
        quality_metrics={
            "source_coverage": 0.0,
            "retrieval_top_score": 0.0,
            "has_sources": False,
            "answer_length": 3,
        },
    )
    store.create_answer_feedback(project.id, first.id, "useful")

    response = handle_projects_route(
        store,
        "GET",
        "/api/projects/quality-summary",
        {"project_id": [project.id]},
        {},
    )
    missing_id_response = handle_projects_route(store, "GET", "/api/projects/quality-summary", {}, {})
    unknown_project_response = handle_projects_route(
        store,
        "GET",
        "/api/projects/quality-summary",
        {"project_id": ["missing"]},
        {},
    )

    assert response is not None
    assert response.status == 200
    assert response.body == {
        "total_questions": 2,
        "has_sources_rate": 0.5,
        "user_useful_rate": 0.5,
        "avg_source_coverage": 0.25,
        "avg_retrieval_top_score": 0.45,
    }
    assert missing_id_response is not None
    assert missing_id_response.status == 400
    assert missing_id_response.body["error"] == "project_id is required"
    assert unknown_project_response is not None
    assert unknown_project_response.status == 404
    assert unknown_project_response.body["error"] == "project not found"


def test_projects_route_module_handles_project_crud(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")

    create_response = handle_projects_route(
        store,
        "POST",
        "/api/projects",
        {},
        {"name": "知识岛", "path": str(project_dir)},
    )
    invalid_create_response = handle_projects_route(
        store,
        "POST",
        "/api/projects",
        {},
        {"name": "坏路径", "path": str(tmp_path / "missing")},
    )
    list_response = handle_projects_route(store, "GET", "/api/projects", {}, {})
    project_id = create_response.body["project"]["id"]
    rename_response = handle_projects_route(
        store,
        "POST",
        "/api/projects/rename",
        {},
        {"project_id": project_id, "name": "新名称"},
    )
    blank_name_response = handle_projects_route(
        store,
        "POST",
        "/api/projects/rename",
        {},
        {"project_id": project_id, "name": "   "},
    )
    delete_response = handle_projects_route(
        store,
        "POST",
        "/api/projects/delete",
        {},
        {"project_id": project_id},
    )
    missing_delete_response = handle_projects_route(
        store,
        "POST",
        "/api/projects/delete",
        {},
        {"project_id": "missing"},
    )

    assert create_response is not None
    assert create_response.status == 201
    assert create_response.body["project"]["name"] == "知识岛"
    assert invalid_create_response is not None
    assert invalid_create_response.status == 400
    assert invalid_create_response.body["error"] == "path must be an existing directory"
    assert list_response is not None
    assert [project["id"] for project in list_response.body["projects"]] == [project_id]
    assert rename_response is not None
    assert rename_response.status == 200
    assert rename_response.body["project"]["name"] == "新名称"
    assert blank_name_response is not None
    assert blank_name_response.status == 400
    assert blank_name_response.body["error"] == "name is required"
    assert delete_response is not None
    assert delete_response.status == 200
    assert delete_response.body == {"deleted": True}
    assert missing_delete_response is not None
    assert missing_delete_response.status == 404
    assert missing_delete_response.body["error"] == "project not found"


def test_projects_route_module_handles_retrieval_settings(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    save_response = handle_projects_route(
        store,
        "POST",
        "/api/projects/retrieval-settings",
        {},
        {
            "project_id": project.id,
            "top_k": "2",
            "min_score": "0.25",
            "use_keyword": "true",
            "use_vector": "false",
        },
    )
    get_response = handle_projects_route(
        store,
        "GET",
        "/api/projects/retrieval-settings",
        {"project_id": [project.id]},
        {},
    )
    missing_get_response = handle_projects_route(
        store,
        "GET",
        "/api/projects/retrieval-settings",
        {},
        {},
    )
    unknown_post_response = handle_projects_route(
        store,
        "POST",
        "/api/projects/retrieval-settings",
        {},
        {"project_id": "missing"},
    )

    expected_settings = {
        "project_id": project.id,
        "top_k": 2,
        "min_score": 0.25,
        "use_keyword": True,
        "use_vector": False,
    }
    assert save_response is not None
    assert save_response.status == 200
    assert save_response.body["settings"] == expected_settings
    assert get_response is not None
    assert get_response.body["settings"] == expected_settings
    assert missing_get_response is not None
    assert missing_get_response.status == 400
    assert missing_get_response.body["error"] == "project_id is required"
    assert unknown_post_response is not None
    assert unknown_post_response.status == 404
    assert unknown_post_response.body["error"] == "project not found"


def test_agent_route_module_handles_readonly_tool_metadata(tmp_path):
    store = KnowledgeStore(tmp_path / "app.db")

    response = handle_agent_route(store, "GET", "/api/agent/tools", {}, {})

    assert response is not None
    assert response.status == 200
    tools = {tool["name"]: tool for tool in response.body["tools"]}
    assert set(tools) == {"project_overview", "search_sources"}
    assert all(tool["read_only"] is True for tool in tools.values())
    assert "shell" not in tools
    assert handle_agent_route(store, "POST", "/api/agent/tools", {}, {}) is None


def test_agent_route_module_handles_tool_run_history_and_detail(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    run_response = handle_agent_route(
        store,
        "POST",
        "/api/agent/tools/run",
        {},
        {"project_id": project.id, "tool": "project_overview", "arguments": {}},
    )
    assert run_response is not None
    run_id = run_response.body["run"]["id"]

    list_response = handle_agent_route(
        store,
        "GET",
        "/api/agent/tools/runs",
        {"project_id": [project.id]},
        {},
    )
    detail_response = handle_agent_route(
        store,
        "GET",
        "/api/agent/tools/runs/detail",
        {"run_id": [run_id]},
        {},
    )
    missing_project_response = handle_agent_route(store, "GET", "/api/agent/tools/runs", {}, {})
    missing_detail_response = handle_agent_route(
        store,
        "GET",
        "/api/agent/tools/runs/detail",
        {"run_id": ["missing"]},
        {},
    )

    assert run_response.status == 200
    assert run_response.body["result"]["project_name"] == "知识岛"
    assert run_response.body["run"]["tool_name"] == "project_overview"
    assert list_response is not None
    assert [run["id"] for run in list_response.body["runs"]] == [run_id]
    assert detail_response is not None
    assert detail_response.body["run"]["id"] == run_id
    assert missing_project_response is not None
    assert missing_project_response.status == 400
    assert missing_project_response.body["error"] == "project_id is required"
    assert missing_detail_response is not None
    assert missing_detail_response.status == 404
    assert missing_detail_response.body["error"] == "tool run not found"


def test_chat_route_module_handles_sessions_and_messages(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    create_session_response = handle_chat_route(
        store,
        "POST",
        "/api/chat/sessions",
        {},
        {"project_id": project.id, "title": "架构说明"},
    )
    session_id = create_session_response.body["session"]["id"]
    message = store.create_chat_message(
        project_id=project.id,
        question="默认入口是什么？",
        answer="默认入口是 app.py。",
        mode="local",
        provider="local",
        warning="",
        sources=[],
        session_id=session_id,
    )

    list_sessions_response = handle_chat_route(
        store,
        "GET",
        "/api/chat/sessions",
        {"project_id": [project.id]},
        {},
    )
    rename_session_response = handle_chat_route(
        store,
        "POST",
        "/api/chat/sessions/rename",
        {},
        {"session_id": session_id, "title": "新的标题"},
    )
    list_messages_response = handle_chat_route(
        store,
        "GET",
        "/api/chat/messages",
        {"project_id": [project.id], "session_id": [session_id]},
        {},
    )
    delete_message_response = handle_chat_route(
        store,
        "POST",
        "/api/chat/messages/delete",
        {},
        {"message_id": message.id},
    )
    clear_messages_response = handle_chat_route(
        store,
        "POST",
        "/api/chat/messages/clear",
        {},
        {"project_id": project.id},
    )

    assert create_session_response is not None
    assert create_session_response.status == 200
    assert list_sessions_response is not None
    assert [session["id"] for session in list_sessions_response.body["sessions"]] == [session_id]
    assert rename_session_response is not None
    assert rename_session_response.body["session"]["title"] == "新的标题"
    assert list_messages_response is not None
    assert [entry["id"] for entry in list_messages_response.body["messages"]] == [message.id]
    assert delete_message_response is not None
    assert delete_message_response.body == {"deleted": True, "messages": []}
    assert clear_messages_response is not None
    assert clear_messages_response.body == {"deleted": 0, "messages": []}


def test_chat_route_module_handles_message_branching(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    session = store.create_chat_session(project.id, "架构说明")
    first = store.create_chat_message(project.id, "问题一", "回答一", "local", "local", "", [], session_id=session.id)
    second = store.create_chat_message(project.id, "问题二", "回答二", "local", "local", "", [], session_id=session.id)

    branch_response = handle_chat_route(
        store,
        "POST",
        "/api/chat/messages/branch",
        {},
        {"session_id": session.id, "parent_message_id": first.id, "question": "重新问问题一"},
    )
    active_response = handle_chat_route(
        store,
        "GET",
        "/api/chat/messages",
        {"project_id": [project.id], "session_id": [session.id]},
        {},
    )
    all_response = handle_chat_route(
        store,
        "GET",
        "/api/chat/messages",
        {"project_id": [project.id], "session_id": [session.id], "include_branches": ["true"]},
        {},
    )
    invalid_response = handle_chat_route(
        store,
        "POST",
        "/api/chat/messages/branch",
        {},
        {"session_id": session.id, "parent_message_id": "missing", "question": "重新问"},
    )

    assert branch_response is not None
    assert branch_response.status == 200
    assert branch_response.body["status"] == "branched"
    new_message_id = branch_response.body["new_message_id"]
    assert [message["id"] for message in active_response.body["messages"]] == [first.id, new_message_id]
    assert [message["id"] for message in all_response.body["messages"]] == [first.id, second.id, new_message_id]
    assert all_response.body["messages"][1]["is_active"] is False
    assert invalid_response is not None
    assert invalid_response.status == 404
    assert invalid_response.body["error"] == "chat message not found"


def test_assessment_route_module_handles_start_and_answer(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "stack.md",
        "stack.md",
        "app.py 启动 Web 服务，并使用 SQLite 保存项目资料。",
    )

    start_response = handle_assessment_route(
        store,
        "POST",
        "/api/assessment/start",
        {},
        {"project_id": project.id},
    )
    question = start_response.body["session"]["questions"][0]
    answer_response = handle_assessment_route(
        store,
        "POST",
        "/api/assessment/answer",
        {},
        {
            "project_id": project.id,
            "question": question,
            "answer": "app.py 启动 Web 服务，并使用 SQLite 保存项目资料。",
        },
    )
    missing_project_response = handle_assessment_route(
        store,
        "POST",
        "/api/assessment/start",
        {},
        {"project_id": "missing"},
    )

    assert start_response is not None
    assert start_response.status == 200
    assert start_response.body["session"]["project_id"] == project.id
    assert answer_response is not None
    assert answer_response.status == 200
    assert answer_response.body["result"]["answer_id"]
    assert answer_response.body["result"]["result_id"]
    assert missing_project_response is not None
    assert missing_project_response.status == 404
    assert missing_project_response.body["error"] == "project not found"


def test_export_route_module_handles_project_export_and_restore(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, project_dir / "stack.md", "stack.md", "默认入口是 app.py。")
    store.create_chat_session(project.id, "架构说明")

    export_response = handle_export_route(
        store,
        "GET",
        "/api/export/project",
        {"project_id": [project.id]},
        {},
    )
    restore_response = handle_export_route(
        store,
        "POST",
        "/api/export/project/restore",
        {},
        {"export": export_response.body["export"], "name": "知识岛恢复"},
    )
    missing_project_response = handle_export_route(store, "GET", "/api/export/project", {}, {})

    assert export_response is not None
    assert export_response.status == 200
    assert export_response.body["export"]["project"]["id"] == project.id
    assert export_response.body["export"]["documents"][0]["relative_path"] == "stack.md"
    assert restore_response is not None
    assert restore_response.status == 200
    assert restore_response.body["project"]["name"] == "知识岛恢复"
    assert restore_response.body["restored"]["documents"] == 1
    assert missing_project_response is not None
    assert missing_project_response.status == 400
    assert missing_project_response.body["error"] == "project_id is required"


def test_answer_route_module_handles_answer_and_feedback(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, project_dir / "stack.md", "stack.md", "默认入口是 app.py。")

    answer_response = handle_answer_route(
        store,
        "POST",
        "/api/answer",
        {},
        {"project_id": project.id, "question": "默认入口是什么？"},
        llm_client=RouteSplitFakeLlmClient(),
    )
    message_id = answer_response.body["message"]["id"]
    feedback_response = handle_answer_route(
        store,
        "POST",
        "/api/answer/feedback",
        {},
        {"project_id": project.id, "message_id": message_id, "rating": "useful", "note": "准确"},
        llm_client=None,
    )
    invalid_feedback_response = handle_answer_route(
        store,
        "POST",
        "/api/answer/feedback",
        {},
        {"project_id": project.id, "message_id": message_id, "rating": "bad"},
        llm_client=None,
    )

    assert answer_response is not None
    assert answer_response.status == 200
    assert answer_response.body["answer"] == "测试回答：默认入口是什么？"
    assert answer_response.body["message"]["question"] == "默认入口是什么？"
    assert feedback_response is not None
    assert feedback_response.status == 200
    assert feedback_response.body["feedback"]["rating"] == "useful"
    assert invalid_feedback_response is not None
    assert invalid_feedback_response.status == 400
    assert invalid_feedback_response.body["error"] == "rating is invalid"


def test_settings_route_module_handles_llm_settings(tmp_path, monkeypatch):
    appdata = tmp_path / "appdata"
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setenv("RAG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.delenv("RAG_LLM_API_KEY", raising=False)
    store = KnowledgeStore(tmp_path / "app.db")

    test_response = handle_settings_route(store, "POST", "/api/settings/llm/test", {}, {})
    save_response = handle_settings_route(
        store,
        "POST",
        "/api/settings/llm",
        {},
        {
            "provider": "api",
            "api_base": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "api_key": "sk-new-secret",
        },
    )
    get_response = handle_settings_route(store, "GET", "/api/settings/llm", {}, {})

    assert test_response is not None
    assert test_response.status == 400
    assert test_response.body["error"] == "LLM provider is not configured"
    assert save_response is not None
    assert save_response.status == 200
    assert save_response.body["settings"]["api_key_source"] == "saved"
    assert "sk-new-secret" not in str(save_response.body)
    assert get_response is not None
    assert get_response.status == 200
    assert get_response.body["settings"]["has_api_key"] is True


def test_settings_route_module_handles_model_profiles(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_LLM_API_KEY", "sk-profile-secret")
    store = KnowledgeStore(tmp_path / "app.db")

    create_response = handle_settings_route(
        store,
        "POST",
        "/api/model-profiles",
        {},
        {
            "name": "DeepSeek 默认",
            "provider": "api",
            "api_base": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "api_key_ref": "env:RAG_LLM_API_KEY",
        },
    )
    profile_id = create_response.body["profile"]["id"]
    default_response = handle_settings_route(
        store,
        "POST",
        "/api/model-profiles/default",
        {},
        {"profile_id": profile_id},
    )
    list_response = handle_settings_route(store, "GET", "/api/model-profiles", {}, {})
    missing_update_response = handle_settings_route(
        store,
        "POST",
        "/api/model-profiles/update",
        {},
        {"name": "x"},
    )

    assert create_response is not None
    assert create_response.status == 200
    assert create_response.body["profile"]["has_api_key"] is True
    assert "sk-profile-secret" not in str(create_response.body)
    assert default_response is not None
    assert default_response.body["default_profile_id"] == profile_id
    assert list_response is not None
    assert list_response.body["profiles"][0]["is_default"] is True
    assert missing_update_response is not None
    assert missing_update_response.status == 400
    assert missing_update_response.body["error"] == "profile_id is required"


def test_settings_route_module_handles_prompt_presets(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    create_response = handle_settings_route(
        store,
        "POST",
        "/api/prompt-presets",
        {},
        {
            "project_id": project.id,
            "name": "项目问答",
            "description": "回答项目资料问题",
            "system_prompt": "优先说明依据文件。",
            "answer_format": "按要点回答。",
        },
    )
    preset_id = create_response.body["preset"]["id"]
    default_response = handle_settings_route(
        store,
        "POST",
        "/api/prompt-presets/default",
        {},
        {"project_id": project.id, "preset_id": preset_id},
    )
    list_response = handle_settings_route(
        store,
        "GET",
        "/api/prompt-presets",
        {"project_id": [project.id]},
        {},
    )
    delete_response = handle_settings_route(
        store,
        "POST",
        "/api/prompt-presets/delete",
        {},
        {"preset_id": preset_id},
    )

    assert create_response is not None
    assert create_response.status == 200
    assert default_response is not None
    assert default_response.body["default_preset_id"] == preset_id
    assert list_response is not None
    assert list_response.body["default_preset_id"] == preset_id
    assert {template["name"] for template in list_response.body["templates"]} >= {"项目问答", "代码解释", "学习复盘"}
    assert delete_response is not None
    assert delete_response.body["deleted"] is True


def test_documents_route_module_handles_document_list_preview_and_delete(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    first = store.upsert_document(project.id, project_dir / "a.md", "a.md", "Alpha").document
    second = store.upsert_document(project.id, project_dir / "b.md", "b.md", "Beta").document

    list_response = handle_documents_route(
        store,
        "GET",
        "/api/documents",
        {"project_id": [project.id]},
        {},
    )
    preview_response = handle_documents_route(
        store,
        "GET",
        "/api/document",
        {"document_id": [first.id]},
        {},
    )
    delete_response = handle_documents_route(
        store,
        "POST",
        "/api/documents/delete",
        {},
        {"document_id": first.id},
    )
    missing_preview_response = handle_documents_route(
        store,
        "GET",
        "/api/document",
        {"document_id": ["missing"]},
        {},
    )

    assert list_response is not None
    assert [doc["relative_path"] for doc in list_response.body["documents"]] == ["a.md", "b.md"]
    assert "content" not in list_response.body["documents"][0]
    assert preview_response is not None
    assert preview_response.body["document"]["content"] == "Alpha"
    assert delete_response is not None
    assert delete_response.status == 200
    assert [doc["id"] for doc in delete_response.body["documents"]] == [second.id]
    assert missing_preview_response is not None
    assert missing_preview_response.status == 404
    assert missing_preview_response.body["error"] == "document not found"


def test_documents_route_module_handles_document_collections(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    document = store.upsert_document(project.id, project_dir / "api.md", "api.md", "接口文档").document

    create_response = handle_documents_route(
        store,
        "POST",
        "/api/document-collections",
        {},
        {"project_id": project.id, "name": "接口资料", "description": "接口相关文档", "color": "#0f766e"},
    )
    collection_id = create_response.body["collection"]["id"]
    add_response = handle_documents_route(
        store,
        "POST",
        "/api/document-collections/items/add",
        {},
        {"collection_id": collection_id, "document_ids": [document.id]},
    )
    filtered_response = handle_documents_route(
        store,
        "GET",
        "/api/documents",
        {"project_id": [project.id], "collection_id": [collection_id]},
        {},
    )
    update_response = handle_documents_route(
        store,
        "POST",
        "/api/document-collections/update",
        {},
        {
            "collection_id": collection_id,
            "name": "API 资料",
            "description": "更新后的说明",
            "color": "#4f46e5",
        },
    )
    remove_response = handle_documents_route(
        store,
        "POST",
        "/api/document-collections/items/remove",
        {},
        {"collection_id": collection_id, "document_ids": [document.id]},
    )
    list_response = handle_documents_route(
        store,
        "GET",
        "/api/document-collections",
        {"project_id": [project.id]},
        {},
    )

    assert create_response is not None
    assert create_response.body["collection"]["name"] == "接口资料"
    assert add_response is not None
    assert add_response.body["collection"]["document_count"] == 1
    assert filtered_response is not None
    assert [doc["id"] for doc in filtered_response.body["documents"]] == [document.id]
    assert update_response is not None
    assert update_response.body["collection"]["name"] == "API 资料"
    assert remove_response is not None
    assert remove_response.body["collection"]["document_count"] == 0
    assert list_response is not None
    assert list_response.body["collections"][0]["document_count"] == 0


def test_imports_route_module_handles_directory_preview_import_and_batches(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    (project_dir / "a.md").write_text("Alpha", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    preview_response = handle_imports_route(
        store,
        "GET",
        "/api/import/preview",
        {"project_id": [project.id]},
        {},
    )
    import_response = handle_imports_route(store, "POST", "/api/import", {}, {"project_id": project.id})
    list_response = handle_imports_route(
        store,
        "GET",
        "/api/import/batches",
        {"project_id": [project.id]},
        {},
    )
    batch_id = import_response.body["batch"]["id"]
    detail_response = handle_imports_route(
        store,
        "GET",
        "/api/import/batches/detail",
        {"batch_id": [batch_id]},
        {},
    )

    assert preview_response is not None
    assert preview_response.body["preview"]["importable"] == 1
    assert import_response is not None
    assert import_response.body["result"]["imported"] == 1
    assert import_response.body["batch"]["source_type"] == "directory_sync"
    assert list_response is not None
    assert [batch["id"] for batch in list_response.body["batches"]] == [batch_id]
    assert detail_response is not None
    assert detail_response.body["batch"]["id"] == batch_id


def test_imports_route_module_handles_upload_note_and_url_sources(tmp_path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", Path("browser-upload:知识岛"))

    upload_response = handle_imports_route(
        store,
        "POST",
        "/api/import/upload",
        {},
        {
            "project_id": project.id,
            "source_type": "file_upload",
            "files": [{"relative_path": "README.md", "content": "上传文件"}],
        },
    )
    note_response = handle_imports_route(
        store,
        "POST",
        "/api/import/note",
        {},
        {"project_id": project.id, "title": "会议记录", "content": "文本笔记"},
    )
    url_response = handle_imports_route(
        store,
        "POST",
        "/api/import/url",
        {},
        {
            "project_id": project.id,
            "url": "https://example.com/article",
            "title": "网页摘录",
            "content": "人工粘贴正文",
        },
    )

    assert upload_response is not None
    assert upload_response.body["batch"]["source_type"] == "file_upload"
    assert note_response is not None
    assert note_response.body["batch"]["source_type"] == "text_note"
    assert url_response is not None
    assert url_response.body["batch"]["source_type"] == "url_excerpt"
    relative_paths = [doc["relative_path"] for doc in url_response.body["documents"]]
    assert "README.md" in relative_paths
    assert any(path.startswith("notes/会议记录-") and path.endswith(".txt") for path in relative_paths)
    assert any(path.startswith("urls/") and path.endswith(".txt") for path in relative_paths)


def test_search_route_module_handles_search_and_debug(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, project_dir / "api.md", "api.md", "HTTP search endpoint snippet")
    store.upsert_document(project.id, project_dir / "ui.md", "ui.md", "button preview panel")

    search_response = handle_search_route(
        store,
        "POST",
        "/api/search",
        {},
        {"project_id": project.id, "query": "search endpoint"},
    )
    debug_response = handle_search_route(
        store,
        "POST",
        "/api/search/debug",
        {},
        {
            "project_id": project.id,
            "query": "search endpoint",
            "top_k": 1,
            "min_score": 0.1,
            "use_keyword": True,
            "use_vector": False,
        },
    )

    assert search_response is not None
    assert search_response.body["hits"][0]["path"] == "api.md"
    assert debug_response is not None
    assert debug_response.body["debug"]["parameters"] == {
        "top_k": 1,
        "min_score": 0.1,
        "use_keyword": True,
        "use_vector": False,
    }
    assert debug_response.body["debug"]["quality"]["level"] == "good"


def test_search_route_module_handles_retrieval_reviews(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, project_dir / "stack.md", "stack.md", "默认入口是 app.py")

    create_response = handle_search_route(
        store,
        "POST",
        "/api/retrieval/reviews",
        {},
        {"project_id": project.id, "query": "默认入口", "use_keyword": True, "use_vector": False},
    )
    review_id = create_response.body["review"]["id"]
    list_response = handle_search_route(
        store,
        "GET",
        "/api/retrieval/reviews",
        {"project_id": [project.id]},
        {},
    )
    detail_response = handle_search_route(
        store,
        "GET",
        "/api/retrieval/reviews/detail",
        {"review_id": [review_id]},
        {},
    )
    delete_response = handle_search_route(
        store,
        "POST",
        "/api/retrieval/reviews/delete",
        {},
        {"review_id": review_id},
    )

    assert create_response is not None
    assert create_response.body["review"]["hit_count"] == 1
    assert list_response is not None
    assert list_response.body["reviews"][0]["id"] == review_id
    assert detail_response is not None
    assert detail_response.body["review"]["id"] == review_id
    assert delete_response is not None
    assert delete_response.body == {"deleted": True, "reviews": []}


def test_route_registry_dispatches_project_summary_and_agent_tools(tmp_path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    summary_response = dispatch_to_routes(
        store,
        "GET",
        "/api/projects/summary",
        {"project_id": [project.id]},
        {},
        llm_client=None,
    )
    tools_response = dispatch_to_routes(store, "GET", "/api/agent/tools", {}, {}, llm_client=None)

    assert summary_response is not None
    assert summary_response.status == 200
    assert summary_response.body["summary"]["project_id"] == project.id
    assert tools_response is not None
    assert tools_response.status == 200
    assert {tool["name"] for tool in tools_response.body["tools"]} == {"project_overview", "search_sources"}


def test_migrated_routes_are_removed_from_legacy_dispatch():
    api_source = Path("backend/knowledge_island/api.py").read_text(encoding="utf-8")

    assert 'path == "/api/health"' not in api_source
    assert 'path == "/api/projects"' not in api_source
    assert 'path == "/api/projects/summary"' not in api_source
    assert 'path == "/api/projects/retrieval-settings"' not in api_source
    assert 'path == "/api/projects/rename"' not in api_source
    assert 'path == "/api/projects/delete"' not in api_source
    assert 'path == "/api/agent/tools"' not in api_source
    assert 'path == "/api/settings/llm"' not in api_source
    assert 'path == "/api/model-profiles"' not in api_source
    assert 'path == "/api/model-profiles/update"' not in api_source
    assert 'path == "/api/model-profiles/delete"' not in api_source
    assert 'path == "/api/model-profiles/default"' not in api_source
    assert 'path == "/api/model-profiles/test"' not in api_source
    assert 'path == "/api/prompt-presets"' not in api_source
    assert 'path == "/api/prompt-presets/update"' not in api_source
    assert 'path == "/api/prompt-presets/delete"' not in api_source
    assert 'path == "/api/prompt-presets/default"' not in api_source
    assert 'path == "/api/documents"' not in api_source
    assert 'path == "/api/document"' not in api_source
    assert 'path == "/api/documents/delete"' not in api_source
    assert 'path == "/api/document-collections"' not in api_source
    assert 'path == "/api/document-collections/update"' not in api_source
    assert 'path == "/api/document-collections/delete"' not in api_source
    assert 'path == "/api/document-collections/items/add"' not in api_source
    assert 'path == "/api/document-collections/items/remove"' not in api_source
    assert 'path == "/api/import"' not in api_source
    assert 'path == "/api/import/preview"' not in api_source
    assert 'path == "/api/import/upload"' not in api_source
    assert 'path == "/api/import/note"' not in api_source
    assert 'path == "/api/import/url"' not in api_source
    assert 'path == "/api/import/batches"' not in api_source
    assert 'path == "/api/import/batches/detail"' not in api_source
    assert 'path == "/api/search"' not in api_source
    assert 'path == "/api/search/debug"' not in api_source
    assert 'path == "/api/retrieval/reviews"' not in api_source
    assert 'path == "/api/retrieval/reviews/detail"' not in api_source
    assert 'path == "/api/retrieval/reviews/delete"' not in api_source
    assert 'path == "/api/agent/tools/run"' not in api_source
    assert 'path == "/api/agent/tools/runs"' not in api_source
    assert 'path == "/api/agent/tools/runs/detail"' not in api_source
    assert 'path == "/api/chat/messages"' not in api_source
    assert 'path == "/api/chat/sessions"' not in api_source
    assert 'path == "/api/chat/sessions/rename"' not in api_source
    assert 'path == "/api/chat/sessions/delete"' not in api_source
    assert 'path == "/api/chat/messages/delete"' not in api_source
    assert 'path == "/api/chat/messages/clear"' not in api_source
    assert 'path == "/api/assessment/start"' not in api_source
    assert 'path == "/api/assessment/answer"' not in api_source
    assert 'path == "/api/export/project"' not in api_source
    assert 'path == "/api/export/project/restore"' not in api_source
    assert 'path == "/api/answer"' not in api_source
    assert 'path == "/api/answer/feedback"' not in api_source
