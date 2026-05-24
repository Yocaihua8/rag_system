from pathlib import Path

from webapp.api import dispatch
from webapp.ingestion import import_directory
from webapp.storage import KnowledgeStore


def test_prompt_preset_api_crud_and_project_default(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    create_response = dispatch(
        store,
        "POST",
        "/api/prompt-presets",
        {
            "project_id": project.id,
            "name": "项目问答",
            "description": "回答项目资料问题",
            "system_prompt": "优先说明依据文件。",
            "answer_format": "按要点回答。",
        },
    )

    assert create_response.status == 200
    preset = create_response.body["preset"]
    assert preset["project_id"] == project.id
    assert preset["name"] == "项目问答"
    assert preset["system_prompt"] == "优先说明依据文件。"

    list_response = dispatch(store, "GET", f"/api/prompt-presets?project_id={project.id}")
    assert list_response.status == 200
    assert list_response.body["default_preset_id"] == ""
    assert list_response.body["presets"][0]["id"] == preset["id"]
    assert {template["name"] for template in list_response.body["templates"]} >= {"项目问答", "代码解释", "学习复盘"}

    default_response = dispatch(
        store,
        "POST",
        "/api/prompt-presets/default",
        {"project_id": project.id, "preset_id": preset["id"]},
    )
    assert default_response.status == 200
    assert default_response.body["default_preset_id"] == preset["id"]

    update_response = dispatch(
        store,
        "POST",
        "/api/prompt-presets/update",
        {
            "preset_id": preset["id"],
            "name": "代码解释",
            "description": "解释文件职责",
            "system_prompt": "说明模块职责。",
            "answer_format": "先结论后依据。",
        },
    )
    assert update_response.status == 200
    assert update_response.body["preset"]["name"] == "代码解释"

    clear_response = dispatch(
        store,
        "POST",
        "/api/prompt-presets/default",
        {"project_id": project.id, "preset_id": ""},
    )
    assert clear_response.status == 200
    assert clear_response.body["default_preset_id"] == ""

    delete_response = dispatch(
        store,
        "POST",
        "/api/prompt-presets/delete",
        {"preset_id": preset["id"]},
    )
    assert delete_response.status == 200
    assert delete_response.body["deleted"] is True
    assert delete_response.body["presets"] == []


def test_prompt_preset_api_rejects_missing_project_cross_project_default_and_invalid_payload(tmp_path: Path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    first = store.create_project("项目 A", first_dir)
    second = store.create_project("项目 B", second_dir)
    preset = store.create_prompt_preset(
        first.id,
        "项目问答",
        "说明",
        "只基于来源回答。",
        "",
    )

    missing_project = dispatch(store, "GET", "/api/prompt-presets")
    unknown_project = dispatch(store, "GET", "/api/prompt-presets?project_id=missing")
    blank_name = dispatch(
        store,
        "POST",
        "/api/prompt-presets",
        {"project_id": first.id, "name": "", "system_prompt": "只基于来源回答。"},
    )
    cross_project_default = dispatch(
        store,
        "POST",
        "/api/prompt-presets/default",
        {"project_id": second.id, "preset_id": preset.id},
    )
    missing_preset_update = dispatch(
        store,
        "POST",
        "/api/prompt-presets/update",
        {"preset_id": "missing", "name": "x", "system_prompt": "y"},
    )

    assert missing_project.status == 400
    assert missing_project.body["error"] == "project_id is required"
    assert unknown_project.status == 404
    assert unknown_project.body["error"] == "project not found"
    assert blank_name.status == 400
    assert blank_name.body["error"] == "name is required"
    assert cross_project_default.status == 404
    assert cross_project_default.body["error"] == "prompt preset not found"
    assert missing_preset_update.status == 404
    assert missing_preset_update.body["error"] == "prompt preset not found"


def test_answer_api_passes_project_default_prompt_preset_to_llm_client(tmp_path: Path):
    class FakeLlmClient:
        provider = "deepseek"

        def __init__(self):
            self.prompt_preset = None

        def generate_answer(self, question, hits, history_messages=None, prompt_preset=None):
            self.prompt_preset = prompt_preset
            return "按项目问答预设生成的回答。"

    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    preset = store.create_prompt_preset(
        project.id,
        "项目问答",
        "回答项目资料问题",
        "优先说明依据文件。",
        "按要点回答。",
    )
    store.set_default_prompt_preset(project.id, preset.id)
    store.upsert_document(project.id, project_dir / "stack.md", "stack.md", "默认入口是 app.py。")
    client = FakeLlmClient()

    response = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project.id, "question": "默认入口是什么？"},
        llm_client=client,
    )

    assert response.status == 200
    assert response.body["answer"] == "按项目问答预设生成的回答。"
    assert client.prompt_preset is not None
    assert client.prompt_preset.id == preset.id
    assert client.prompt_preset.system_prompt == "优先说明依据文件。"


def test_api_import_search_and_answer_flow(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    (project_dir / "stack.md").write_text(
        "# 技术栈\n\n默认入口改为本地 Web 服务，使用 SQLite 保存项目资料。",
        encoding="utf-8",
    )
    store = KnowledgeStore(tmp_path / "app.db")

    create_response = dispatch(
        store,
        "POST",
        "/api/projects",
        {"name": "知识岛", "path": str(project_dir)},
    )
    assert create_response.status == 201

    project_id = create_response.body["project"]["id"]
    import_result = import_directory(store, project_id, project_dir)
    assert import_result.imported == 1

    answer_response = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project_id, "question": "默认入口是什么？"},
    )

    assert answer_response.status == 200
    assert "本地 Web 服务" in answer_response.body["answer"]
    assert answer_response.body["mode"] == "local"
    assert answer_response.body["sources"][0]["path"] == "stack.md"
    assert "tool_suggestion" not in answer_response.body


def test_answer_api_suggests_readonly_source_search_when_sources_are_missing(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project.id, "question": "默认入口是什么？"},
    )

    assert response.status == 200
    assert response.body["sources"] == []
    assert response.body["observability"]["retrieval"]["hit_count"] == 0
    assert response.body["observability"]["model"] == {
        "mode": "local",
        "provider": "local",
    }
    assert response.body["tool_suggestion"] == {
        "tool": "search_sources",
        "arguments": {"query": "默认入口是什么？"},
        "reason": "当前回答没有可用来源，可先用只读来源检索工具扩大召回。",
    }
    assert store.list_agent_tool_runs(project.id) == []
    assert response.body["source_quality"] == {
        "level": "none",
        "label": "没有找到可用来源",
        "reason": "当前问题没有命中已导入资料，回答不应视为确定结论。",
        "hit_count": 0,
        "max_score": 0.0,
    }


def test_answer_api_uses_injected_llm_client_when_available(tmp_path: Path):
    class FakeLlmClient:
        provider = "deepseek"

        def generate_answer(self, question, hits, history_messages=None):
            assert question == "默认入口是什么？"
            assert hits[0].document.relative_path == "stack.md"
            assert history_messages == []
            return "DeepSeek 回答：默认入口是 app.py。"

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

    response = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project.id, "question": "默认入口是什么？"},
        llm_client=FakeLlmClient(),
    )

    assert response.status == 200
    assert response.body["answer"] == "DeepSeek 回答：默认入口是 app.py。"
    assert response.body["mode"] == "api"
    assert response.body["provider"] == "deepseek"
    assert response.body["observability"]["model"] == {
        "mode": "api",
        "provider": "deepseek",
    }
    assert response.body["source_quality"]["level"] == "good"


def test_answer_api_returns_observability_metadata(tmp_path: Path):
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

    response = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project.id, "question": "默认入口是什么？"},
    )

    assert response.status == 200
    assert response.body["observability"]["retrieval"] == {
        "top_k": 5,
        "min_score": 0.0,
        "use_keyword": True,
        "use_vector": True,
        "hit_count": 1,
    }
    assert response.body["observability"]["model"] == {
        "mode": "local",
        "provider": "local",
    }
    assert response.body["observability"]["elapsed_ms"] >= 0
    assert response.body["observability"]["model"]["mode"] == response.body["mode"]
    assert response.body["observability"]["model"]["provider"] == response.body["provider"]


def test_project_retrieval_settings_api_saves_defaults_for_answer_and_debug(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, project_dir / "a.md", "a.md", "Alpha default entry")
    store.upsert_document(project.id, project_dir / "b.md", "b.md", "Alpha second entry")

    save_response = dispatch(
        store,
        "POST",
        "/api/projects/retrieval-settings",
        {
            "project_id": project.id,
            "top_k": 1,
            "min_score": 0.1,
            "use_keyword": True,
            "use_vector": False,
        },
    )
    get_response = dispatch(store, "GET", f"/api/projects/retrieval-settings?project_id={project.id}")
    answer_response = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project.id, "question": "Alpha"},
    )
    debug_response = dispatch(
        store,
        "POST",
        "/api/search/debug",
        {"project_id": project.id, "query": "Alpha"},
    )

    expected_settings = {
        "project_id": project.id,
        "top_k": 1,
        "min_score": 0.1,
        "use_keyword": True,
        "use_vector": False,
    }
    assert save_response.status == 200
    assert save_response.body["settings"] == expected_settings
    assert get_response.body["settings"] == expected_settings
    assert answer_response.body["observability"]["retrieval"] == {
        "top_k": 1,
        "min_score": 0.1,
        "use_keyword": True,
        "use_vector": False,
        "hit_count": 1,
    }
    assert debug_response.body["debug"]["parameters"] == {
        "top_k": 1,
        "min_score": 0.1,
        "use_keyword": True,
        "use_vector": False,
    }
    assert len(debug_response.body["hits"]) == 1


def test_project_retrieval_settings_api_rejects_missing_or_unknown_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    missing_get = dispatch(store, "GET", "/api/projects/retrieval-settings")
    unknown_get = dispatch(store, "GET", "/api/projects/retrieval-settings?project_id=missing")
    missing_post = dispatch(
        store,
        "POST",
        "/api/projects/retrieval-settings",
        {"top_k": 5, "min_score": 0, "use_keyword": True, "use_vector": True},
    )

    assert missing_get.status == 400
    assert missing_get.body["error"] == "project_id is required"
    assert unknown_get.status == 404
    assert unknown_get.body["error"] == "project not found"
    assert missing_post.status == 400
    assert missing_post.body["error"] == "project_id is required"


def test_answer_api_reports_weak_source_quality_for_single_low_score_tool_context(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    write_result = store.upsert_document(
        project.id,
        project_dir / "note.md",
        "note.md",
        "只有一个补充片段。",
    )
    run = store.create_agent_tool_run(
        project.id,
        "search_sources",
        {"query": "补充"},
        {
            "query": "补充",
            "hits": [
                {
                    "document_id": write_result.document.id,
                    "path": "note.md",
                    "snippet": "只有一个补充片段。",
                    "score": 1.0,
                }
            ],
        },
        "success",
    )

    response = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project.id, "question": "无直接命中的问题", "tool_run_id": run.id},
    )

    assert response.status == 200
    assert response.body["source_quality"]["level"] == "weak"
    assert response.body["source_quality"]["hit_count"] == 1
    assert response.body["source_quality"]["max_score"] == 1.0


def test_answer_api_passes_recent_chat_history_to_llm_client(tmp_path: Path):
    class FakeLlmClient:
        provider = "deepseek"

        def generate_answer(self, question, hits, history_messages=None):
            assert question == "默认入口在哪里？"
            assert len(history_messages) == 1
            assert history_messages[0].question == "这个项目叫什么？"
            assert history_messages[0].answer == "项目叫知识岛。"
            return "DeepSeek 回答：默认入口是 app.py。"

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
    store.create_chat_message(
        project_id=project.id,
        question="这个项目叫什么？",
        answer="项目叫知识岛。",
        mode="local",
        provider="local",
        warning="",
        sources=[],
    )

    response = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project.id, "question": "默认入口在哪里？"},
        llm_client=FakeLlmClient(),
    )

    assert response.status == 200
    assert response.body["message"]["answer"] == "DeepSeek 回答：默认入口是 app.py。"


def test_answer_api_can_use_search_sources_tool_run_as_explicit_context(tmp_path: Path):
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
    tool_response = dispatch(
        store,
        "POST",
        "/api/agent/tools/run",
        {"project_id": project.id, "tool": "search_sources", "arguments": {"query": "默认入口"}},
    )

    response = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project.id, "question": "它在哪里？", "tool_run_id": tool_response.body["run"]["id"]},
    )

    assert response.status == 200
    assert "app.py" in response.body["answer"]
    assert response.body["tool_context"]["tool_run_id"] == tool_response.body["run"]["id"]
    assert response.body["tool_context"]["query"] == "默认入口"
    assert response.body["sources"][0]["path"] == "stack.md"


def test_answer_feedback_api_saves_local_feedback_for_project_message(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    message = store.create_chat_message(
        project_id=project.id,
        question="默认入口是什么？",
        answer="默认入口是 app.py。",
        mode="local",
        provider="local",
        warning="",
        sources=[],
    )

    response = dispatch(
        store,
        "POST",
        "/api/answer/feedback",
        {
            "project_id": project.id,
            "message_id": message.id,
            "rating": "source_wrong",
            "note": "引用的来源不对应",
        },
    )

    assert response.status == 200
    assert response.body["feedback"]["project_id"] == project.id
    assert response.body["feedback"]["message_id"] == message.id
    assert response.body["feedback"]["rating"] == "source_wrong"
    assert response.body["feedback"]["note"] == "引用的来源不对应"
    assert response.body["feedback"]["id"]
    assert response.body["feedback"]["created_at"]
    assert store.list_answer_feedback(project.id)[0].id == response.body["feedback"]["id"]


def test_answer_feedback_api_rejects_missing_or_invalid_fields(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    message = store.create_chat_message(project.id, "问题", "回答", "local", "local", "", [])

    missing_project = dispatch(
        store,
        "POST",
        "/api/answer/feedback",
        {"message_id": message.id, "rating": "useful"},
    )
    missing_message = dispatch(
        store,
        "POST",
        "/api/answer/feedback",
        {"project_id": project.id, "rating": "useful"},
    )
    invalid_rating = dispatch(
        store,
        "POST",
        "/api/answer/feedback",
        {"project_id": project.id, "message_id": message.id, "rating": "ok"},
    )

    assert missing_project.status == 400
    assert missing_project.body["error"] == "project_id is required"
    assert missing_message.status == 400
    assert missing_message.body["error"] == "message_id is required"
    assert invalid_rating.status == 400
    assert invalid_rating.body["error"] == "rating is invalid"
    assert store.list_answer_feedback(project.id) == []


def test_answer_feedback_api_rejects_missing_project_or_message_from_other_project(tmp_path: Path):
    project_dir = tmp_path / "notes"
    other_dir = tmp_path / "other"
    project_dir.mkdir()
    other_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    other_project = store.create_project("其他项目", other_dir)
    other_message = store.create_chat_message(other_project.id, "其他问题", "其他回答", "local", "local", "", [])

    missing_project = dispatch(
        store,
        "POST",
        "/api/answer/feedback",
        {"project_id": "missing", "message_id": other_message.id, "rating": "useful"},
    )
    missing_message = dispatch(
        store,
        "POST",
        "/api/answer/feedback",
        {"project_id": project.id, "message_id": "missing", "rating": "useful"},
    )
    other_project_message = dispatch(
        store,
        "POST",
        "/api/answer/feedback",
        {"project_id": project.id, "message_id": other_message.id, "rating": "useful"},
    )

    assert missing_project.status == 404
    assert missing_project.body["error"] == "project not found"
    assert missing_message.status == 404
    assert missing_message.body["error"] == "chat message not found"
    assert other_project_message.status == 404
    assert other_project_message.body["error"] == "chat message not found"
    assert store.list_answer_feedback(project.id) == []


def test_answer_api_rejects_tool_context_from_other_project(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    other_project = store.create_project("其他项目", other_dir)
    tool_response = dispatch(
        store,
        "POST",
        "/api/agent/tools/run",
        {"project_id": other_project.id, "tool": "search_sources", "arguments": {"query": "默认入口"}},
    )

    response = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project.id, "question": "它在哪里？", "tool_run_id": tool_response.body["run"]["id"]},
    )

    assert response.status == 400
    assert response.body["error"] == "tool context is not available"


def test_agent_tool_run_detail_api_returns_single_run(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    run = store.create_agent_tool_run(
        project_id=project.id,
        tool_name="project_overview",
        arguments={"scope": "current"},
        result={"document_count": 0},
        status="success",
    )

    response = dispatch(store, "GET", f"/api/agent/tools/runs/detail?run_id={run.id}")

    assert response.status == 200
    assert response.body == {"run": run.to_dict()}


def test_agent_tool_run_detail_api_requires_run_id(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(store, "GET", "/api/agent/tools/runs/detail")

    assert response.status == 400
    assert response.body["error"] == "run_id is required"


def test_agent_tool_run_detail_api_returns_404_for_missing_run(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(store, "GET", "/api/agent/tools/runs/detail?run_id=missing")

    assert response.status == 404
    assert response.body["error"] == "tool run not found"


def test_answer_api_falls_back_to_local_answer_when_llm_fails(tmp_path: Path):
    class FailingLlmClient:
        provider = "deepseek"

        def generate_answer(self, question, hits, history_messages=None):
            raise RuntimeError("network down")

    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "stack.md",
        "stack.md",
        "默认入口改为本地 Web 服务。",
    )

    response = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project.id, "question": "默认入口是什么？"},
        llm_client=FailingLlmClient(),
    )

    assert response.status == 200
    assert "本地 Web 服务" in response.body["answer"]
    assert response.body["mode"] == "fallback"
    assert response.body["provider"] == "deepseek"
    assert response.body["warning"] == "network down"


def test_llm_settings_api_returns_masked_current_config(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RAG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("RAG_LLM_PROVIDER", "api")
    monkeypatch.setenv("RAG_LLM_API_BASE", "https://api.deepseek.com/v1")
    monkeypatch.setenv("RAG_LLM_API_KEY", "sk-secret")
    monkeypatch.setenv("RAG_LLM_API_MODEL", "deepseek-chat")
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(store, "GET", "/api/settings/llm")

    assert response.status == 200
    assert response.body["settings"] == {
        "provider": "api",
        "api_base": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "has_api_key": True,
        "api_key_source": "environment",
    }
    assert "sk-secret" not in str(response.body)


def test_llm_settings_api_saves_config_without_echoing_key(tmp_path: Path, monkeypatch):
    appdata = tmp_path / "appdata"
    monkeypatch.setenv("APPDATA", str(appdata))
    monkeypatch.setenv("RAG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.delenv("RAG_LLM_API_KEY", raising=False)
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(
        store,
        "POST",
        "/api/settings/llm",
        {
            "provider": "api",
            "api_base": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "api_key": "sk-new-secret",
        },
    )

    saved_env = (appdata / "KnowledgeIsland" / ".env").read_text(encoding="utf-8")
    assert response.status == 200
    assert response.body["settings"]["has_api_key"] is True
    assert response.body["settings"]["api_key_source"] == "saved"
    assert "sk-new-secret" in saved_env
    assert "sk-new-secret" not in str(response.body)


def test_llm_settings_test_api_requires_configured_key(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RAG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.delenv("RAG_LLM_API_KEY", raising=False)
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(store, "POST", "/api/settings/llm/test")

    assert response.status == 400
    assert response.body["error"] == "LLM provider is not configured"


def test_import_api_returns_current_document_list(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    (project_dir / "b.md").write_text("Beta content", encoding="utf-8")
    (project_dir / "a.md").write_text("Alpha content", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(store, "POST", "/api/import", {"project_id": project.id})

    assert response.status == 200
    assert response.body["result"]["imported"] == 2
    assert response.body["result"]["created"] == 2
    assert response.body["result"]["deleted"] == 0
    assert [doc["relative_path"] for doc in response.body["documents"]] == ["a.md", "b.md"]


def test_import_preview_api_returns_counts_without_writing_documents(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    (project_dir / "a.md").write_text("Alpha content", encoding="utf-8")
    (project_dir / "image.png").write_text("not supported", encoding="utf-8")
    ignored_dir = project_dir / "node_modules"
    ignored_dir.mkdir()
    (ignored_dir / "skip.md").write_text("ignored", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(store, "GET", f"/api/import/preview?project_id={project.id}")

    assert response.status == 200
    assert response.body["preview"]["importable"] == 1
    assert response.body["preview"]["skipped"] == 1
    assert response.body["preview"]["skipped_details"] == [
        {"path": "image.png", "reason": "unsupported file type"}
    ]
    assert store.list_documents(project.id) == []


def test_import_preview_api_rejects_missing_unknown_or_missing_root(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("丢失目录", tmp_path / "missing")

    missing_id_response = dispatch(store, "GET", "/api/import/preview")
    unknown_project_response = dispatch(store, "GET", "/api/import/preview?project_id=missing")
    missing_root_response = dispatch(store, "GET", f"/api/import/preview?project_id={project.id}")

    assert missing_id_response.status == 400
    assert missing_id_response.body["error"] == "project_id is required"
    assert unknown_project_response.status == 404
    assert unknown_project_response.body["error"] == "project not found"
    assert missing_root_response.status == 400
    assert missing_root_response.body["error"] == "project root path does not exist"


def test_project_summary_api_returns_current_project_health_counts(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    document_result = store.upsert_document(
        project.id,
        project_dir / "stack.md",
        "stack.md",
        "默认入口是 app.py，本地 Web 服务负责页面和 API。",
    )
    chat_message = store.create_chat_message(
        project_id=project.id,
        question="默认入口是什么？",
        answer="默认入口是 app.py。",
        mode="local",
        provider="local",
        warning="",
        sources=[],
    )
    tool_run = store.create_agent_tool_run(
        project_id=project.id,
        tool_name="project_overview",
        arguments={},
        result={},
        status="success",
    )
    retrieval_review = store.create_retrieval_review(
        project_id=project.id,
        query="默认入口",
        parameters={"top_k": 5},
        hits=[],
        source_quality={"level": "none"},
        note="",
    )

    response = dispatch(store, "GET", f"/api/projects/summary?project_id={project.id}")

    assert response.status == 200
    assert response.body["summary"]["project_id"] == project.id
    assert response.body["summary"]["project_name"] == "知识岛"
    assert response.body["summary"]["document_count"] == 1
    assert response.body["summary"]["chunk_count"] == 1
    assert response.body["summary"]["vector_count"] == 1
    assert response.body["summary"]["chat_message_count"] == 1
    assert response.body["summary"]["agent_tool_run_count"] == 1
    assert response.body["summary"]["retrieval_review_count"] == 1
    assert response.body["summary"]["last_activity_at"] == max(
        project.created_at,
        document_result.document.updated_at,
        chat_message.created_at,
        tool_run.created_at,
        retrieval_review.created_at,
    )


def test_project_summary_api_counts_only_requested_project(tmp_path: Path):
    project_a_dir = tmp_path / "project-a"
    project_b_dir = tmp_path / "project-b"
    project_a_dir.mkdir()
    project_b_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project_a = store.create_project("项目 A", project_a_dir)
    project_b = store.create_project("项目 B", project_b_dir)

    store.upsert_document(project_a.id, project_a_dir / "a.md", "a.md", "A 项目资料")
    store.create_chat_message(project_a.id, "A 问题", "A 回答", "local", "local", "", [])

    store.upsert_document(project_b.id, project_b_dir / "b1.md", "b1.md", "B 项目资料一")
    store.upsert_document(project_b.id, project_b_dir / "b2.md", "b2.md", "B 项目资料二")
    store.create_chat_message(project_b.id, "B 问题一", "B 回答一", "local", "local", "", [])
    store.create_chat_message(project_b.id, "B 问题二", "B 回答二", "local", "local", "", [])
    store.create_agent_tool_run(project_b.id, "project_overview", {}, {}, "success")
    store.create_retrieval_review(
        project_b.id,
        query="B 项目",
        parameters={"top_k": 5},
        hits=[],
        source_quality={"level": "none"},
        note="",
    )

    response = dispatch(store, "GET", f"/api/projects/summary?project_id={project_a.id}")

    assert response.status == 200
    assert response.body["summary"]["project_id"] == project_a.id
    assert response.body["summary"]["document_count"] == 1
    assert response.body["summary"]["chunk_count"] == 1
    assert response.body["summary"]["vector_count"] == 1
    assert response.body["summary"]["chat_message_count"] == 1
    assert response.body["summary"]["agent_tool_run_count"] == 0
    assert response.body["summary"]["retrieval_review_count"] == 0


def test_project_summary_api_rejects_missing_or_unknown_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    missing_id_response = dispatch(store, "GET", "/api/projects/summary")
    unknown_project_response = dispatch(store, "GET", "/api/projects/summary?project_id=missing")

    assert missing_id_response.status == 400
    assert missing_id_response.body["error"] == "project_id is required"
    assert unknown_project_response.status == 404
    assert unknown_project_response.body["error"] == "project not found"


def test_project_export_api_returns_project_documents_chat_and_settings_summary(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setenv("RAG_RUNTIME_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("RAG_LLM_PROVIDER", "api")
    monkeypatch.setenv("RAG_LLM_API_BASE", "https://api.deepseek.com/v1")
    monkeypatch.setenv("RAG_LLM_API_MODEL", "deepseek-chat")
    monkeypatch.setenv("RAG_LLM_API_KEY", "sk-export-secret")
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    document = store.upsert_document(
        project.id,
        project_dir / "stack.md",
        "stack.md",
        "默认入口是 app.py，本地 Web 服务负责页面和 API。",
    ).document
    message = store.create_chat_message(
        project_id=project.id,
        question="默认入口是什么？",
        answer="默认入口是 app.py。",
        mode="local",
        provider="local",
        warning="",
        sources=[{"path": "stack.md", "document_id": document.id}],
    )

    response = dispatch(store, "GET", f"/api/export/project?project_id={project.id}")

    assert response.status == 200
    assert response.body["export"]["version"] == 1
    assert response.body["export"]["project"] == project.to_dict()
    assert response.body["export"]["documents"] == [
        {
            "id": document.id,
            "relative_path": "stack.md",
            "source_path": str(project_dir / "stack.md"),
            "checksum": document.checksum,
            "updated_at": document.updated_at,
        }
    ]
    assert response.body["export"]["chat_messages"] == [message.to_dict()]
    assert response.body["export"]["settings_summary"] == {
        "provider": "api",
        "api_base": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "key_configured": True,
    }
    assert "content" not in response.body["export"]["documents"][0]
    assert "api_key" not in str(response.body).lower()
    assert "sk-export-secret" not in str(response.body)


def test_project_export_api_includes_session_chat_messages(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    session = store.create_chat_session(project.id, "架构说明")
    default_message = store.create_chat_message(project.id, "默认问题", "默认回答", "local", "local", "", [])
    session_message = store.create_chat_message(
        project.id,
        "会话问题",
        "会话回答",
        "local",
        "local",
        "",
        [],
        session_id=session.id,
    )

    response = dispatch(store, "GET", f"/api/export/project?project_id={project.id}")

    assert response.status == 200
    assert [message["id"] for message in response.body["export"]["chat_messages"]] == [
        default_message.id,
        session_message.id,
    ]


def test_project_export_api_rejects_missing_or_unknown_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    missing_id_response = dispatch(store, "GET", "/api/export/project")
    unknown_project_response = dispatch(store, "GET", "/api/export/project?project_id=missing")

    assert missing_id_response.status == 400
    assert missing_id_response.body["error"] == "project_id is required"
    assert unknown_project_response.status == 404
    assert unknown_project_response.body["error"] == "project not found"


def test_upload_import_api_creates_project_without_host_directory(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(
        store,
        "POST",
        "/api/import/upload",
        {
            "project_name": "浏览器项目",
            "files": [
                {"relative_path": "README.md", "content": "浏览器选择文件夹导入"},
                {"relative_path": "src/app.py", "content": "print('hello')"},
            ],
        },
    )

    assert response.status == 200
    assert response.body["project"]["name"] == "浏览器项目"
    assert response.body["project"]["root_path"] == "browser-upload:浏览器项目"
    assert response.body["project"]["root_exists"] is True
    assert response.body["result"]["created"] == 2
    assert [doc["relative_path"] for doc in response.body["documents"]] == ["README.md", "src/app.py"]


def test_upload_import_api_reuses_selected_project_and_applies_import_rules(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("已有项目", Path("browser-upload:已有项目"))

    response = dispatch(
        store,
        "POST",
        "/api/import/upload",
        {
            "project_id": project.id,
            "files": [
                {"relative_path": "README.md", "content": "可导入"},
                {"relative_path": "node_modules/pkg/index.js", "content": "跳过依赖"},
                {"relative_path": "image.png", "content": "跳过图片"},
                {"relative_path": "../escape.md", "content": "跳过非法路径"},
            ],
        },
    )

    assert response.status == 200
    assert response.body["project"]["id"] == project.id
    assert response.body["result"]["imported"] == 1
    assert response.body["result"]["skipped"] == 3
    assert response.body["result"]["skipped_details"] == [
        {"path": "node_modules/pkg/index.js", "reason": "ignored directory"},
        {"path": "image.png", "reason": "unsupported file type"},
        {"path": "../escape.md", "reason": "invalid relative path"},
    ]
    assert [doc["relative_path"] for doc in response.body["documents"]] == ["README.md"]


def test_import_note_api_creates_searchable_document(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(
        store,
        "POST",
        "/api/import/note",
        {
            "project_id": project.id,
            "title": "会议记录",
            "content": "这里记录了知识岛的文本笔记导入方案。",
        },
    )
    search_response = dispatch(
        store,
        "POST",
        "/api/search",
        {"project_id": project.id, "query": "文本笔记导入"},
    )

    assert response.status == 200
    assert response.body["result"]["created"] == 1
    assert response.body["document"]["relative_path"].startswith("notes/")
    assert response.body["document"]["relative_path"].endswith(".txt")
    assert response.body["document"]["source_path"].startswith("note:")
    assert [doc["relative_path"] for doc in response.body["documents"]] == [
        response.body["document"]["relative_path"]
    ]
    assert search_response.body["hits"][0]["document_id"] == response.body["document"]["id"]


def test_import_note_api_updates_same_title_without_duplicate_document(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    first = dispatch(
        store,
        "POST",
        "/api/import/note",
        {"project_id": project.id, "title": "会议记录", "content": "第一版内容"},
    )
    second = dispatch(
        store,
        "POST",
        "/api/import/note",
        {"project_id": project.id, "title": "会议记录", "content": "第二版内容"},
    )

    assert first.status == 200
    assert second.status == 200
    assert second.body["result"]["updated"] == 1
    assert second.body["document"]["id"] == first.body["document"]["id"]
    assert len(store.list_documents(project.id)) == 1
    assert "第二版内容" in store.get_document(first.body["document"]["id"]).content


def test_import_note_api_rejects_invalid_payload(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    blank_title = dispatch(
        store,
        "POST",
        "/api/import/note",
        {"project_id": project.id, "title": " ", "content": "正文"},
    )
    blank_content = dispatch(
        store,
        "POST",
        "/api/import/note",
        {"project_id": project.id, "title": "标题", "content": " "},
    )
    null_title = dispatch(
        store,
        "POST",
        "/api/import/note",
        {"project_id": project.id, "title": None, "content": "正文"},
    )
    non_string_content = dispatch(
        store,
        "POST",
        "/api/import/note",
        {"project_id": project.id, "title": "标题", "content": 123},
    )
    missing_project = dispatch(
        store,
        "POST",
        "/api/import/note",
        {"project_id": "missing", "title": "标题", "content": "正文"},
    )

    assert blank_title.status == 400
    assert blank_title.body["error"] == "title is required"
    assert blank_content.status == 400
    assert blank_content.body["error"] == "content is required"
    assert null_title.status == 400
    assert null_title.body["error"] == "title is required"
    assert non_string_content.status == 400
    assert non_string_content.body["error"] == "content is required"
    assert missing_project.status == 404
    assert missing_project.body["error"] == "project not found"


def test_import_note_api_rejects_oversized_content(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(
        store,
        "POST",
        "/api/import/note",
        {"project_id": project.id, "title": "长笔记", "content": "x" * 1_000_001},
    )

    assert response.status == 400
    assert response.body["error"] == "content is too large"


def test_import_url_excerpt_api_creates_searchable_virtual_source(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(
        store,
        "POST",
        "/api/import/url",
        {
            "project_id": project.id,
            "url": "https://example.com/article",
            "title": "网页摘录",
            "content": "这里是人工粘贴的网页正文，不会自动抓取。",
        },
    )
    search_response = dispatch(
        store,
        "POST",
        "/api/search",
        {"project_id": project.id, "query": "人工粘贴"},
    )

    assert response.status == 200
    assert response.body["result"]["created"] == 1
    assert response.body["document"]["relative_path"].startswith("urls/")
    assert response.body["document"]["relative_path"].endswith(".txt")
    assert response.body["document"]["source_path"].startswith("url:")
    assert "来源 URL：https://example.com/article" in response.body["document"]["content"]
    assert search_response.body["hits"][0]["document_id"] == response.body["document"]["id"]


def test_import_url_excerpt_api_updates_same_url_without_duplicate_document(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    first = dispatch(
        store,
        "POST",
        "/api/import/url",
        {
            "project_id": project.id,
            "url": "https://example.com/article",
            "title": "网页摘录",
            "content": "第一版正文",
        },
    )
    second = dispatch(
        store,
        "POST",
        "/api/import/url",
        {
            "project_id": project.id,
            "url": "https://example.com/article",
            "title": "网页摘录更新",
            "content": "第二版正文",
        },
    )

    assert first.status == 200
    assert second.status == 200
    assert second.body["result"]["updated"] == 1
    assert second.body["document"]["id"] == first.body["document"]["id"]
    assert len(store.list_documents(project.id)) == 1
    assert "第二版正文" in store.get_document(first.body["document"]["id"]).content


def test_import_url_excerpt_api_rejects_invalid_payload(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", tmp_path)

    missing_url = dispatch(
        store,
        "POST",
        "/api/import/url",
        {"project_id": project.id, "url": " ", "title": "标题", "content": "正文"},
    )
    invalid_url = dispatch(
        store,
        "POST",
        "/api/import/url",
        {"project_id": project.id, "url": "ftp://example.com/a", "title": "标题", "content": "正文"},
    )
    blank_title = dispatch(
        store,
        "POST",
        "/api/import/url",
        {"project_id": project.id, "url": "https://example.com/a", "title": " ", "content": "正文"},
    )
    blank_content = dispatch(
        store,
        "POST",
        "/api/import/url",
        {"project_id": project.id, "url": "https://example.com/a", "title": "标题", "content": " "},
    )
    missing_project = dispatch(
        store,
        "POST",
        "/api/import/url",
        {"project_id": "missing", "url": "https://example.com/a", "title": "标题", "content": "正文"},
    )

    assert missing_url.status == 400
    assert missing_url.body["error"] == "url is required"
    assert invalid_url.status == 400
    assert invalid_url.body["error"] == "url must start with http:// or https://"
    assert blank_title.status == 400
    assert blank_title.body["error"] == "title is required"
    assert blank_content.status == 400
    assert blank_content.body["error"] == "content is required"
    assert missing_project.status == 404
    assert missing_project.body["error"] == "project not found"


def test_directory_import_does_not_delete_url_excerpt_documents(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    (project_dir / "README.md").write_text("本地文件", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    url_response = dispatch(
        store,
        "POST",
        "/api/import/url",
        {
            "project_id": project.id,
            "url": "https://example.com/article",
            "title": "网页摘录",
            "content": "虚拟 URL 来源内容",
        },
    )

    import_response = dispatch(store, "POST", "/api/import", {"project_id": project.id})

    assert import_response.status == 200
    relative_paths = [doc.relative_path for doc in store.list_documents(project.id)]
    assert url_response.body["document"]["relative_path"] in relative_paths
    assert "README.md" in relative_paths


def test_directory_import_does_not_delete_note_documents(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    (project_dir / "README.md").write_text("本地文件", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    note_response = dispatch(
        store,
        "POST",
        "/api/import/note",
        {"project_id": project.id, "title": "保留笔记", "content": "虚拟来源内容"},
    )

    import_response = dispatch(store, "POST", "/api/import", {"project_id": project.id})

    assert import_response.status == 200
    relative_paths = [doc.relative_path for doc in store.list_documents(project.id)]
    assert note_response.body["document"]["relative_path"] in relative_paths
    assert "README.md" in relative_paths


def test_upload_import_does_not_delete_url_excerpt_documents(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("浏览器项目", Path("browser-upload:浏览器项目"))
    url_response = dispatch(
        store,
        "POST",
        "/api/import/url",
        {
            "project_id": project.id,
            "url": "https://example.com/article",
            "title": "网页摘录",
            "content": "虚拟 URL 来源内容",
        },
    )

    upload_response = dispatch(
        store,
        "POST",
        "/api/import/upload",
        {
            "project_id": project.id,
            "files": [{"relative_path": "README.md", "content": "浏览器文件"}],
        },
    )

    assert upload_response.status == 200
    relative_paths = [doc["relative_path"] for doc in upload_response.body["documents"]]
    assert url_response.body["document"]["relative_path"] in relative_paths
    assert "README.md" in relative_paths


def test_directory_import_does_not_overwrite_note_path_collision(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    note_response = dispatch(
        store,
        "POST",
        "/api/import/note",
        {"project_id": project.id, "title": "保留笔记", "content": "虚拟来源内容"},
    )
    relative_path = note_response.body["document"]["relative_path"]
    collision_path = project_dir / relative_path
    collision_path.parent.mkdir(parents=True, exist_ok=True)
    collision_path.write_text("真实文件不应覆盖笔记", encoding="utf-8")

    import_response = dispatch(store, "POST", "/api/import", {"project_id": project.id})
    document = store.get_document(note_response.body["document"]["id"])

    assert import_response.status == 200
    assert import_response.body["result"]["imported"] == 0
    assert import_response.body["result"]["skipped_details"] == [
        {"path": relative_path, "reason": "reserved note path"}
    ]
    assert document.source_path.as_posix().startswith("note:")
    assert document.content == "虚拟来源内容"


def test_upload_import_does_not_delete_note_documents(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("浏览器项目", Path("browser-upload:浏览器项目"))
    note_response = dispatch(
        store,
        "POST",
        "/api/import/note",
        {"project_id": project.id, "title": "保留笔记", "content": "虚拟来源内容"},
    )

    upload_response = dispatch(
        store,
        "POST",
        "/api/import/upload",
        {
            "project_id": project.id,
            "files": [{"relative_path": "README.md", "content": "浏览器文件"}],
        },
    )

    assert upload_response.status == 200
    relative_paths = [doc["relative_path"] for doc in upload_response.body["documents"]]
    assert note_response.body["document"]["relative_path"] in relative_paths
    assert "README.md" in relative_paths


def test_upload_import_does_not_overwrite_note_path_collision(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("浏览器项目", Path("browser-upload:浏览器项目"))
    note_response = dispatch(
        store,
        "POST",
        "/api/import/note",
        {"project_id": project.id, "title": "保留笔记", "content": "虚拟来源内容"},
    )
    relative_path = note_response.body["document"]["relative_path"]

    upload_response = dispatch(
        store,
        "POST",
        "/api/import/upload",
        {
            "project_id": project.id,
            "files": [{"relative_path": relative_path, "content": "真实上传不应覆盖笔记"}],
        },
    )
    document = store.get_document(note_response.body["document"]["id"])

    assert upload_response.status == 200
    assert upload_response.body["result"]["imported"] == 0
    assert upload_response.body["result"]["skipped_details"] == [
        {"path": relative_path, "reason": "reserved note path"}
    ]
    assert document.source_path.as_posix().startswith("note:")
    assert document.content == "虚拟来源内容"


def test_import_api_ignores_local_tool_config_directories(tmp_path: Path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "README.md").write_text("public project note", encoding="utf-8")
    for dirname in [".agents", ".claude", ".codex", ".idea", ".vscode"]:
        config_dir = project_dir / dirname
        config_dir.mkdir()
        (config_dir / "settings.json").write_text("local tool setting", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(store, "POST", "/api/import", {"project_id": project.id})

    assert response.status == 200
    assert response.body["result"]["imported"] == 1
    assert [doc["relative_path"] for doc in response.body["documents"]] == ["README.md"]


def test_import_api_returns_read_errors(tmp_path: Path, monkeypatch):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    bad_file = project_dir / "bad.md"
    bad_file.write_text("bad", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    original_read_text = Path.read_text

    def fail_bad_file(path: Path, *args, **kwargs):
        if path == bad_file:
            raise OSError("permission denied")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_bad_file)

    response = dispatch(store, "POST", "/api/import", {"project_id": project.id})

    assert response.status == 200
    assert response.body["result"]["imported"] == 0
    assert response.body["result"]["skipped"] == 1
    assert response.body["result"]["errors"] == ["bad.md: permission denied"]
    assert response.body["documents"] == []


def test_projects_api_reports_missing_root_path(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    project_dir.rmdir()

    response = dispatch(store, "GET", "/api/projects")

    assert response.status == 200
    assert response.body["projects"][0]["id"] == project.id
    assert response.body["projects"][0]["root_exists"] is False


def test_import_api_rejects_project_with_missing_root_path(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    project_dir.rmdir()

    response = dispatch(store, "POST", "/api/import", {"project_id": project.id})

    assert response.status == 400
    assert response.body["error"] == "project root path does not exist"


def test_document_preview_api_returns_single_document_content(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    (project_dir / "a.md").write_text("# Alpha\n\nPreview body", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    import_response = dispatch(store, "POST", "/api/import", {"project_id": project.id})
    document_id = import_response.body["documents"][0]["id"]

    list_response = dispatch(store, "GET", f"/api/documents?project_id={project.id}")
    preview_response = dispatch(store, "GET", f"/api/document?document_id={document_id}")

    assert "content" not in list_response.body["documents"][0]
    assert preview_response.status == 200
    assert preview_response.body["document"]["relative_path"] == "a.md"
    assert preview_response.body["document"]["content"] == "# Alpha\n\nPreview body"


def test_document_preview_api_returns_404_for_missing_document(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(store, "GET", "/api/document?document_id=missing")

    assert response.status == 404
    assert response.body["error"] == "document not found"


def test_delete_document_api_removes_single_document_and_returns_remaining_list(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    (project_dir / "a.md").write_text("Alpha", encoding="utf-8")
    (project_dir / "b.md").write_text("Beta", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    import_response = dispatch(store, "POST", "/api/import", {"project_id": project.id})
    document_id = import_response.body["documents"][0]["id"]

    response = dispatch(store, "POST", "/api/documents/delete", {"document_id": document_id})
    preview_response = dispatch(store, "GET", f"/api/document?document_id={document_id}")

    assert response.status == 200
    assert response.body["deleted"] is True
    assert len(response.body["documents"]) == 1
    assert response.body["documents"][0]["relative_path"] == "b.md"
    assert preview_response.status == 404


def test_delete_document_api_returns_404_for_missing_document(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(store, "POST", "/api/documents/delete", {"document_id": "missing"})

    assert response.status == 404
    assert response.body["error"] == "document not found"


def test_search_api_returns_ranked_hits_without_answer_generation(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, project_dir / "api.md", "api.md", "HTTP search endpoint snippet")
    store.upsert_document(project.id, project_dir / "ui.md", "ui.md", "button preview panel")

    response = dispatch(store, "POST", "/api/search", {"project_id": project.id, "query": "search endpoint"})
    empty_response = dispatch(store, "POST", "/api/search", {"project_id": project.id, "query": ""})

    assert response.status == 200
    assert response.body["hits"][0]["path"] == "api.md"
    assert response.body["hits"][0]["score"] > 0
    assert "endpoint snippet" in response.body["hits"][0]["snippet"]
    assert empty_response.status == 200
    assert empty_response.body["hits"] == []


def test_search_debug_api_returns_rag_diagnostics(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, project_dir / "api.md", "api.md", "HTTP search endpoint snippet")
    store.upsert_document(project.id, project_dir / "ui.md", "ui.md", "button preview panel")

    response = dispatch(
        store,
        "POST",
        "/api/search/debug",
        {
            "project_id": project.id,
            "query": "search endpoint",
            "top_k": 1,
            "min_score": 0.1,
            "use_keyword": True,
            "use_vector": False,
        },
    )

    assert response.status == 200
    assert len(response.body["hits"]) == 1
    assert response.body["hits"][0]["path"] == "api.md"
    assert response.body["hits"][0]["retrieval"] == "keyword"
    assert response.body["hits"][0]["vector_score"] == 0.0
    assert response.body["debug"]["query"] == "search endpoint"
    assert response.body["debug"]["document_count"] == 2
    assert response.body["debug"]["chunk_count"] == 2
    assert response.body["debug"]["parameters"] == {
        "top_k": 1,
        "min_score": 0.1,
        "use_keyword": True,
        "use_vector": False,
    }
    assert response.body["debug"]["quality"]["level"] == "good"
    assert response.body["debug"]["context_preview"][0]["path"] == "api.md"


def test_search_debug_api_can_disable_keyword_or_all_retrieval(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, project_dir / "api.md", "api.md", "HTTP search endpoint snippet")

    vector_response = dispatch(
        store,
        "POST",
        "/api/search/debug",
        {
            "project_id": project.id,
            "query": "search endpoint",
            "use_keyword": False,
            "use_vector": True,
        },
    )
    disabled_response = dispatch(
        store,
        "POST",
        "/api/search/debug",
        {
            "project_id": project.id,
            "query": "search endpoint",
            "use_keyword": False,
            "use_vector": False,
        },
    )

    assert vector_response.status == 200
    assert vector_response.body["hits"]
    assert vector_response.body["hits"][0]["retrieval"] == "vector"
    assert vector_response.body["hits"][0]["keyword_score"] == 0.0
    assert disabled_response.status == 200
    assert disabled_response.body["hits"] == []
    assert disabled_response.body["debug"]["quality"]["level"] == "none"


def test_retrieval_review_api_saves_current_query_metrics(tmp_path: Path):
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

    response = dispatch(
        store,
        "POST",
        "/api/retrieval/reviews",
        {
            "project_id": project.id,
            "query": "默认入口",
            "note": "命中正确",
            "top_k": 3,
            "min_score": 0.1,
            "use_keyword": True,
            "use_vector": False,
        },
    )
    list_response = dispatch(
        store,
        "GET",
        f"/api/retrieval/reviews?project_id={project.id}",
    )

    assert response.status == 200
    assert response.body["review"]["query"] == "默认入口"
    assert response.body["review"]["note"] == "命中正确"
    assert response.body["review"]["hit_count"] == 1
    assert response.body["review"]["source_quality"]["level"] == "good"
    assert response.body["review"]["parameters"] == {
        "top_k": 3,
        "min_score": 0.1,
        "use_keyword": True,
        "use_vector": False,
    }
    assert response.body["review"]["hits"][0]["path"] == "stack.md"
    assert list_response.status == 200
    assert list_response.body["reviews"][0]["id"] == response.body["review"]["id"]


def test_retrieval_review_detail_api_returns_single_review_with_snapshot(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    review = store.create_retrieval_review(
        project_id=project.id,
        query="默认入口",
        parameters={"top_k": 3, "min_score": 0.1, "use_keyword": True, "use_vector": False},
        hits=[{"path": "stack.md", "snippet": "默认入口是 app.py", "score": 2.0}],
        source_quality={"level": "good", "label": "来源较充分"},
        note="命中正确",
    )

    response = dispatch(store, "GET", f"/api/retrieval/reviews/detail?review_id={review.id}")

    assert response.status == 200
    assert response.body == {"review": review.to_dict()}
    assert response.body["review"]["query"] == "默认入口"
    assert response.body["review"]["parameters"]["top_k"] == 3
    assert response.body["review"]["hits"][0]["path"] == "stack.md"
    assert response.body["review"]["note"] == "命中正确"


def test_retrieval_review_detail_api_rejects_missing_or_unknown_review_id(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    missing_id_response = dispatch(store, "GET", "/api/retrieval/reviews/detail")
    unknown_response = dispatch(store, "GET", "/api/retrieval/reviews/detail?review_id=missing")

    assert missing_id_response.status == 400
    assert missing_id_response.body["error"] == "review_id is required"
    assert unknown_response.status == 404
    assert unknown_response.body["error"] == "retrieval review not found"


def test_delete_retrieval_review_api_removes_only_requested_review(tmp_path: Path):
    project_dir = tmp_path / "notes"
    other_dir = tmp_path / "other"
    project_dir.mkdir()
    other_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    other_project = store.create_project("其他项目", other_dir)
    store.upsert_document(project.id, project_dir / "stack.md", "stack.md", "默认入口是 app.py")
    store.create_chat_message(project.id, "问题", "回答", "local", "local", "", [])
    first_review = store.create_retrieval_review(
        project_id=project.id,
        query="默认入口",
        parameters={"top_k": 5},
        hits=[],
        source_quality={"level": "none"},
        note="删除这条",
    )
    remaining_review = store.create_retrieval_review(
        project_id=project.id,
        query="SQLite",
        parameters={"top_k": 5},
        hits=[],
        source_quality={"level": "none"},
        note="保留这条",
    )
    other_review = store.create_retrieval_review(
        project_id=other_project.id,
        query="其他项目",
        parameters={"top_k": 5},
        hits=[],
        source_quality={"level": "none"},
        note="不受影响",
    )

    response = dispatch(store, "POST", "/api/retrieval/reviews/delete", {"review_id": first_review.id})

    assert response.status == 200
    assert response.body["deleted"] is True
    assert [review["id"] for review in response.body["reviews"]] == [remaining_review.id]
    assert dispatch(store, "GET", f"/api/retrieval/reviews/detail?review_id={first_review.id}").status == 404
    assert store.list_documents(project.id)
    assert store.list_chat_messages(project.id)
    assert store.list_retrieval_reviews(other_project.id)[0].id == other_review.id


def test_delete_retrieval_review_api_rejects_missing_or_unknown_review_id(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    missing_id_response = dispatch(store, "POST", "/api/retrieval/reviews/delete", {})
    unknown_response = dispatch(store, "POST", "/api/retrieval/reviews/delete", {"review_id": "missing"})

    assert missing_id_response.status == 400
    assert missing_id_response.body["error"] == "review_id is required"
    assert unknown_response.status == 404
    assert unknown_response.body["error"] == "retrieval review not found"


def test_retrieval_review_api_records_no_source_review(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(
        store,
        "POST",
        "/api/retrieval/reviews",
        {"project_id": project.id, "query": "不存在的资料"},
    )

    assert response.status == 200
    assert response.body["review"]["hit_count"] == 0
    assert response.body["review"]["source_quality"]["level"] == "none"
    assert response.body["review"]["hits"] == []


def test_retrieval_review_api_rejects_invalid_payload(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    blank_query = dispatch(
        store,
        "POST",
        "/api/retrieval/reviews",
        {"project_id": project.id, "query": " "},
    )
    missing_project = dispatch(
        store,
        "POST",
        "/api/retrieval/reviews",
        {"project_id": "missing", "query": "默认入口"},
    )
    missing_project_id = dispatch(store, "GET", "/api/retrieval/reviews")

    assert blank_query.status == 400
    assert blank_query.body["error"] == "query is required"
    assert missing_project.status == 404
    assert missing_project.body["error"] == "project not found"
    assert missing_project_id.status == 400
    assert missing_project_id.body["error"] == "project_id is required"


def test_delete_project_api_removes_project_and_documents(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    (project_dir / "a.md").write_text("Alpha", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    dispatch(store, "POST", "/api/import", {"project_id": project.id})

    response = dispatch(store, "POST", "/api/projects/delete", {"project_id": project.id})

    assert response.status == 200
    assert response.body == {"deleted": True}
    assert store.get_project(project.id) is None
    assert store.list_documents(project.id) == []


def test_delete_project_api_returns_404_for_missing_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(store, "POST", "/api/projects/delete", {"project_id": "missing"})

    assert response.status == 404
    assert response.body["error"] == "project not found"


def test_rename_project_api_updates_project_name(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("旧名称", project_dir)

    response = dispatch(
        store,
        "POST",
        "/api/projects/rename",
        {"project_id": project.id, "name": "新名称"},
    )

    assert response.status == 200
    assert response.body["project"]["id"] == project.id
    assert response.body["project"]["name"] == "新名称"
    assert store.get_project(project.id).name == "新名称"


def test_rename_project_api_rejects_blank_name(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(
        store,
        "POST",
        "/api/projects/rename",
        {"project_id": project.id, "name": "   "},
    )

    assert response.status == 400
    assert response.body["error"] == "name is required"
    assert store.get_project(project.id).name == "知识岛"
