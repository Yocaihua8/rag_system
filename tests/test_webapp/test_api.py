import base64
import hashlib
import io
import sqlite3
from pathlib import Path
from urllib.parse import quote
from zipfile import ZipFile

import webapp.answer_api as answer_api_module
import webapp.api as api_module
import webapp.routes.imports as imports_route_module
from webapp.api import dispatch
from webapp.ingestion import import_directory
from webapp.storage import KnowledgeStore
from webapp.web_fetch import WebFetchPreview


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


def test_answer_stream_api_yields_token_events_and_done_payload(tmp_path: Path):
    class FakeStreamingClient:
        provider = "deepseek"

        def __init__(self):
            self.calls = []

        def stream_answer(self, question, hits, history_messages=None, prompt_preset=None):
            self.calls.append(
                {
                    "question": question,
                    "hit_paths": [hit.document.relative_path for hit in hits],
                    "history": history_messages or [],
                    "prompt_preset": prompt_preset,
                }
            )
            yield "第一段"
            yield "第二段"

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
    session = store.create_chat_session(project.id, "默认会话")
    client = FakeStreamingClient()

    events = list(
        api_module.answer_stream_events(
            store,
            f"/api/answer/stream?project_id={project.id}&session_id={session.id}&question={quote('默认入口是什么？')}",
            llm_client=client,
        )
    )

    assert [event.event for event in events] == ["token", "token", "done"]
    assert [event.data for event in events[:2]] == [{"text": "第一段"}, {"text": "第二段"}]
    done = events[-1].data
    assert done["answer"] == "第一段第二段"
    assert done["mode"] == "api"
    assert done["provider"] == "deepseek"
    assert done["sources"][0]["document_id"] == document.id
    assert done["pipeline_trace"]["reranker_used"] is False
    assert done["message"]["answer"] == "第一段第二段"
    assert done["message"]["session_id"] == session.id
    assert store.list_chat_messages(project.id, session.id)[0].answer == "第一段第二段"
    assert client.calls[0]["question"] == "默认入口是什么？"
    assert client.calls[0]["hit_paths"] == ["stack.md"]


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


def test_model_profile_api_crud_default_and_key_status(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RAG_LLM_API_KEY", "sk-profile-secret")
    store = KnowledgeStore(tmp_path / "app.db")

    create_response = dispatch(
        store,
        "POST",
        "/api/model-profiles",
        {
            "name": "DeepSeek 默认",
            "provider": "api",
            "api_base": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "temperature": 0.3,
            "max_tokens": 1024,
            "api_key_ref": "env:RAG_LLM_API_KEY",
        },
    )

    assert create_response.status == 200
    profile = create_response.body["profile"]
    assert profile["name"] == "DeepSeek 默认"
    assert profile["provider"] == "api"
    assert profile["has_api_key"] is True
    assert profile["api_key_source"] == "environment"
    assert profile["is_default"] is False
    assert "sk-profile-secret" not in str(create_response.body)

    default_response = dispatch(
        store,
        "POST",
        "/api/model-profiles/default",
        {"profile_id": profile["id"]},
    )
    list_response = dispatch(store, "GET", "/api/model-profiles")
    update_response = dispatch(
        store,
        "POST",
        "/api/model-profiles/update",
        {
            "profile_id": profile["id"],
            "name": "OpenAI 轻量",
            "provider": "api",
            "api_base": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "max_tokens": 512,
            "api_key_ref": "env:RAG_LLM_API_KEY",
        },
    )

    assert default_response.status == 200
    assert default_response.body["default_profile_id"] == profile["id"]
    assert list_response.status == 200
    assert list_response.body["default_profile_id"] == profile["id"]
    assert list_response.body["profiles"][0]["is_default"] is True
    assert update_response.status == 200
    assert update_response.body["profile"]["name"] == "OpenAI 轻量"
    assert update_response.body["profile"]["model"] == "gpt-4o-mini"

    clear_default_response = dispatch(store, "POST", "/api/model-profiles/default", {"profile_id": ""})
    delete_response = dispatch(store, "POST", "/api/model-profiles/delete", {"profile_id": profile["id"]})

    assert clear_default_response.status == 200
    assert clear_default_response.body["default_profile_id"] == ""
    assert delete_response.status == 200
    assert delete_response.body["deleted"] is True
    assert delete_response.body["profiles"] == []


def test_model_profile_api_rejects_invalid_payload_and_missing_profile(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    blank_name = dispatch(
        store,
        "POST",
        "/api/model-profiles",
        {"name": "", "provider": "api", "model": "deepseek-chat"},
    )
    invalid_key_ref = dispatch(
        store,
        "POST",
        "/api/model-profiles",
        {
            "name": "误填 Key",
            "provider": "api",
            "api_base": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "api_key_ref": "sk-real-key-should-not-save",
        },
    )
    missing_update_id = dispatch(store, "POST", "/api/model-profiles/update", {"name": "x"})
    missing_delete_id = dispatch(store, "POST", "/api/model-profiles/delete", {})
    unknown_default = dispatch(store, "POST", "/api/model-profiles/default", {"profile_id": "missing"})

    assert blank_name.status == 400
    assert blank_name.body["error"] == "name is required"
    assert invalid_key_ref.status == 400
    assert invalid_key_ref.body["error"] == "api_key_ref is invalid"
    assert missing_update_id.status == 400
    assert missing_update_id.body["error"] == "profile_id is required"
    assert missing_delete_id.status == 400
    assert missing_delete_id.body["error"] == "profile_id is required"
    assert unknown_default.status == 404
    assert unknown_default.body["error"] == "model profile not found"


def test_answer_api_uses_default_model_profile_when_no_client_is_injected(tmp_path: Path, monkeypatch):
    class FakeProfileClient:
        instances = []

        def __init__(self, config, timeout=60.0):
            self.config = config
            self.provider = "openai"
            FakeProfileClient.instances.append(self)

        def is_configured(self):
            return True

        def generate_answer(self, question, hits, history_messages=None, prompt_preset=None):
            return f"{self.config.model} 回答：{question}"

    monkeypatch.setenv("RAG_LLM_API_KEY", "sk-profile-secret")
    monkeypatch.setattr(api_module, "OpenAICompatibleChatClient", FakeProfileClient)
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, project_dir / "stack.md", "stack.md", "默认入口是 app.py。")
    profile = store.create_model_profile(
        name="OpenAI 轻量",
        provider="api",
        api_base="https://api.openai.com/v1",
        model="gpt-4o-mini",
        temperature=0.2,
        max_tokens=512,
        api_key_ref="env:RAG_LLM_API_KEY",
    )
    store.set_default_model_profile(profile.id)

    response = dispatch(
        store,
        "POST",
        "/api/answer",
        {"project_id": project.id, "question": "默认入口是什么？"},
    )

    assert response.status == 200
    assert response.body["answer"] == "gpt-4o-mini 回答：默认入口是什么？"
    assert response.body["mode"] == "api"
    assert response.body["provider"] == "openai"
    assert FakeProfileClient.instances[0].config.api_base == "https://api.openai.com/v1"
    assert FakeProfileClient.instances[0].config.api_key == "sk-profile-secret"
    assert FakeProfileClient.instances[0].config.temperature == 0.2
    assert FakeProfileClient.instances[0].config.max_tokens == 512


def test_answer_compare_api_runs_same_context_against_two_model_profiles(tmp_path: Path, monkeypatch):
    class FakeProfileClient:
        instances = []

        def __init__(self, config, timeout=60.0):
            self.config = config
            self.provider = config.model
            self.calls = []
            FakeProfileClient.instances.append(self)

        def is_configured(self):
            return True

        def generate_answer(self, question, hits, history_messages=None, prompt_preset=None):
            self.calls.append(
                {
                    "question": question,
                    "hit_paths": [hit.document.relative_path for hit in hits],
                    "history": history_messages or [],
                    "prompt_preset": prompt_preset,
                }
            )
            return f"{self.config.model} 回答：{hits[0].document.relative_path}"

    monkeypatch.setenv("RAG_LLM_API_KEY", "sk-profile-secret")
    monkeypatch.setattr(
        answer_api_module,
        "build_llm_client",
        lambda config, timeout=60.0: FakeProfileClient(config, timeout=timeout),
        raising=False,
    )
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    preset = store.create_prompt_preset(
        project.id,
        "项目问答",
        "说明",
        "优先说明依据文件。",
        "按要点回答。",
    )
    store.set_default_prompt_preset(project.id, preset.id)
    store.upsert_document(project.id, project_dir / "stack.md", "stack.md", "默认入口是 app.py。")
    first_profile = store.create_model_profile(
        name="OpenAI 轻量",
        provider="api",
        api_base="https://api.openai.com/v1",
        model="gpt-4o-mini",
        temperature=0.2,
        max_tokens=512,
        api_key_ref="env:RAG_LLM_API_KEY",
    )
    second_profile = store.create_model_profile(
        name="DeepSeek 默认",
        provider="api",
        api_base="https://api.deepseek.com/v1",
        model="deepseek-chat",
        temperature=0.3,
        max_tokens=1024,
        api_key_ref="env:RAG_LLM_API_KEY",
    )

    response = dispatch(
        store,
        "POST",
        "/api/answer/compare",
        {
            "project_id": project.id,
            "question": "默认入口是什么？",
            "profile_ids": [first_profile.id, second_profile.id],
        },
    )

    assert response.status == 200
    assert response.body["question"] == "默认入口是什么？"
    assert response.body["sources"][0]["path"] == "stack.md"
    assert response.body["source_quality"]["level"] == "good"
    assert response.body["observability"]["model_comparison"]["profile_count"] == 2
    assert "message" not in response.body
    assert store.list_chat_messages(project.id) == []
    assert [result["profile_id"] for result in response.body["results"]] == [first_profile.id, second_profile.id]
    assert [result["profile_name"] for result in response.body["results"]] == ["OpenAI 轻量", "DeepSeek 默认"]
    assert [result["model"] for result in response.body["results"]] == ["gpt-4o-mini", "deepseek-chat"]
    assert [result["answer"] for result in response.body["results"]] == [
        "gpt-4o-mini 回答：stack.md",
        "deepseek-chat 回答：stack.md",
    ]
    assert all(result["mode"] == "api" for result in response.body["results"])
    assert FakeProfileClient.instances[0].calls[0]["prompt_preset"].id == preset.id
    assert FakeProfileClient.instances[1].calls[0]["hit_paths"] == ["stack.md"]
    assert "sk-profile-secret" not in str(response.body)


def test_answer_compare_api_validates_two_distinct_existing_profiles(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    profile = store.create_model_profile(
        name="OpenAI 轻量",
        provider="api",
        api_base="https://api.openai.com/v1",
        model="gpt-4o-mini",
        temperature=0.2,
        max_tokens=512,
        api_key_ref="",
    )

    missing_count = dispatch(
        store,
        "POST",
        "/api/answer/compare",
        {"project_id": "project", "question": "问题", "profile_ids": [profile.id]},
    )
    duplicate_profiles = dispatch(
        store,
        "POST",
        "/api/answer/compare",
        {"project_id": "project", "question": "问题", "profile_ids": [profile.id, profile.id]},
    )
    missing_profile = dispatch(
        store,
        "POST",
        "/api/answer/compare",
        {"project_id": "project", "question": "问题", "profile_ids": [profile.id, "missing"]},
    )

    assert missing_count.status == 400
    assert missing_count.body["error"] == "profile_ids must contain exactly 2 model profile ids"
    assert duplicate_profiles.status == 400
    assert duplicate_profiles.body["error"] == "profile_ids must contain 2 different model profile ids"
    assert missing_profile.status == 404
    assert missing_profile.body["error"] == "model profile not found"


def test_model_profile_test_api_requires_resolvable_key_without_changing_default(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("RAG_LLM_API_KEY", raising=False)
    store = KnowledgeStore(tmp_path / "app.db")
    profile = store.create_model_profile(
        name="DeepSeek 默认",
        provider="api",
        api_base="https://api.deepseek.com/v1",
        model="deepseek-chat",
        temperature=0.3,
        max_tokens=1024,
        api_key_ref="env:RAG_LLM_API_KEY",
    )

    response = dispatch(store, "POST", "/api/model-profiles/test", {"profile_id": profile.id})

    assert response.status == 400
    assert response.body["error"] == "LLM provider is not configured"
    assert store.get_default_model_profile_id() == ""


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


def test_import_api_creates_batch_history_with_detail(tmp_path: Path, monkeypatch):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    (project_dir / "a.md").write_text("Alpha content", encoding="utf-8")
    (project_dir / "bad.md").write_text("bad", encoding="utf-8")
    protected_path = project_dir / "notes" / "protected.txt"
    protected_path.parent.mkdir()
    protected_path.write_text("real file should be skipped", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(project.id, Path("note:protected"), "notes/protected.txt", "virtual note")
    original_read_text = Path.read_text

    def fail_bad_file(path: Path, *args, **kwargs):
        if path == project_dir / "bad.md":
            raise OSError("permission denied")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_bad_file)

    response = dispatch(store, "POST", "/api/import", {"project_id": project.id})
    list_response = dispatch(store, "GET", f"/api/import/batches?project_id={project.id}")

    assert response.status == 200
    assert response.body["batch"]["source_type"] == "directory_sync"
    assert response.body["batch"]["status"] == "partial"
    assert response.body["batch"]["summary"]["created"] == 1
    assert response.body["batch"]["summary"]["skipped"] == 2
    assert list_response.status == 200
    assert len(list_response.body["batches"]) == 1
    batch = list_response.body["batches"][0]
    assert batch["id"] == response.body["batch"]["id"]
    assert batch["project_id"] == project.id
    assert batch["summary"]["errors"] == 1

    detail_response = dispatch(store, "GET", f"/api/import/batches/detail?batch_id={batch['id']}")

    assert detail_response.status == 200
    assert detail_response.body["batch"]["id"] == batch["id"]
    assert detail_response.body["items"] == [
        {
            "kind": "skipped",
            "relative_path": "bad.md",
            "document_id": "",
            "reason": "permission denied",
        },
        {
            "kind": "skipped",
            "relative_path": "notes/protected.txt",
            "document_id": "",
            "reason": "reserved note path",
        },
        {
            "kind": "error",
            "relative_path": "bad.md",
            "document_id": "",
            "reason": "bad.md: permission denied",
        },
    ]


def test_import_sources_create_project_scoped_batches(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", Path("browser-upload:知识岛"))

    upload_response = dispatch(
        store,
        "POST",
        "/api/import/upload",
        {
            "project_id": project.id,
            "source_type": "file_upload",
            "files": [{"relative_path": "README.md", "content": "上传文件"}],
        },
    )
    note_response = dispatch(
        store,
        "POST",
        "/api/import/note",
        {"project_id": project.id, "title": "会议记录", "content": "文本笔记"},
    )
    url_response = dispatch(
        store,
        "POST",
        "/api/import/url",
        {
            "project_id": project.id,
            "url": "https://example.com/article",
            "title": "网页摘录",
            "content": "人工粘贴正文",
        },
    )
    other_project = store.create_project("其他项目", Path("browser-upload:其他项目"))

    list_response = dispatch(store, "GET", f"/api/import/batches?project_id={project.id}")
    other_list_response = dispatch(store, "GET", f"/api/import/batches?project_id={other_project.id}")

    assert upload_response.status == 200
    assert note_response.status == 200
    assert url_response.status == 200
    assert {response.body["batch"]["source_type"] for response in [upload_response, note_response, url_response]} == {
        "file_upload",
        "text_note",
        "url_excerpt",
    }
    assert [batch["source_type"] for batch in list_response.body["batches"]] == [
        "url_excerpt",
        "text_note",
        "file_upload",
    ]
    assert other_list_response.body["batches"] == []


def test_import_preview_does_not_create_batch_history(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    (project_dir / "a.md").write_text("Alpha content", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    preview_response = dispatch(store, "GET", f"/api/import/preview?project_id={project.id}")
    list_response = dispatch(store, "GET", f"/api/import/batches?project_id={project.id}")

    assert preview_response.status == 200
    assert list_response.status == 200
    assert list_response.body["batches"] == []


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
    assessment_question = store.create_assessment_question(
        project_id=project.id,
        source_path="stack.md",
        prompt="默认入口是什么？",
        expected_points=["app.py"],
        reference_snippet="默认入口是 app.py",
        question_type="concept",
        knowledge_point="默认入口",
    )
    assessment_answer = store.create_assessment_answer(project.id, assessment_question.id, "app.py")
    assessment_result = store.create_assessment_result(
        project_id=project.id,
        question_id=assessment_question.id,
        answer_id=assessment_answer.id,
        status="已掌握",
        score=1.0,
        matched_points=["app.py"],
        missing_points=[],
        feedback="回答命中主要依据。",
        source_path="stack.md",
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
    assert response.body["summary"]["assessment_question_count"] == 1
    assert response.body["summary"]["assessment_result_count"] == 1
    assert response.body["summary"]["last_activity_at"] == max(
        project.created_at,
        document_result.document.updated_at,
        chat_message.created_at,
        tool_run.created_at,
        retrieval_review.created_at,
        assessment_result.created_at,
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
    question_b = store.create_assessment_question(
        project_id=project_b.id,
        source_path="b1.md",
        prompt="B 项目资料是什么？",
        expected_points=["B 项目"],
        reference_snippet="B 项目资料一",
        question_type="concept",
        knowledge_point="B 项目资料",
    )
    answer_b = store.create_assessment_answer(project_b.id, question_b.id, "B 项目")
    store.create_assessment_result(
        project_id=project_b.id,
        question_id=question_b.id,
        answer_id=answer_b.id,
        status="基本理解",
        score=0.5,
        matched_points=["B 项目"],
        missing_points=[],
        feedback="回答覆盖部分关键点。",
        source_path="b1.md",
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
    assert response.body["summary"]["assessment_question_count"] == 0
    assert response.body["summary"]["assessment_result_count"] == 0


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
    chunk = store.list_chunks(project.id)[0]
    vector_record = store.list_chunk_vector_records(project.id)[0]

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
            "content": "默认入口是 app.py，本地 Web 服务负责页面和 API。",
            "chunks": [
                {
                    "id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "token_count": chunk.token_count,
                    "created_at": chunk.created_at,
                    "vector": {
                        "values": vector_record["vector"],
                        "provider": vector_record["provider"],
                        "model": vector_record["model"],
                        "updated_at": vector_record["updated_at"],
                    },
                }
            ],
        }
    ]
    assert response.body["export"]["chat_messages"] == [message.to_dict()]
    assert response.body["export"]["settings_summary"] == {
        "provider": "api",
        "api_base": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "key_configured": True,
    }
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


def test_result_export_api_writes_markdown_file_for_chat_message(tmp_path: Path, monkeypatch):
    output_dir = tmp_path / "outputs"
    monkeypatch.setenv("KI_OUTPUT_DIR", str(output_dir))
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    document = store.upsert_document(project.id, project_dir / "stack.md", "stack.md", "默认入口是 app.py。").document
    chunk = store.list_chunks(project.id)[0]
    message = store.create_chat_message(
        project_id=project.id,
        question="默认入口是什么？",
        answer="默认入口是 app.py。",
        mode="local",
        provider="local",
        warning="",
        sources=[
            {
                "path": "stack.md",
                "snippet": "默认入口是 app.py。",
                "document_id": document.id,
                "chunk_id": chunk.id,
            }
        ],
    )

    response = dispatch(
        store,
        "POST",
        "/api/export/result",
        {
            "project_id": project.id,
            "message_id": message.id,
            "format": "markdown",
            "title": "默认入口回答",
        },
    )

    assert response.status == 200
    export = response.body["export"]
    exported_path = Path(export["path"])
    assert export["format"] == "markdown"
    assert export["mime_type"] == "text/markdown; charset=utf-8"
    assert export["filename"].endswith(".md")
    assert exported_path.parent == output_dir
    assert exported_path.name == export["filename"]
    content = exported_path.read_text(encoding="utf-8")
    assert "# 默认入口回答" in content
    assert "## 问题" in content
    assert "默认入口是什么？" in content
    assert "## 回答" in content
    assert "默认入口是 app.py。" in content
    assert "## 来源" in content
    assert "stack.md" in content
    assert export["bytes"] == exported_path.stat().st_size


def test_result_export_api_writes_pdf_file_for_chat_message(tmp_path: Path, monkeypatch):
    output_dir = tmp_path / "outputs"
    monkeypatch.setenv("KI_OUTPUT_DIR", str(output_dir))
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
        "/api/export/result",
        {"project_id": project.id, "message_id": message.id, "format": "pdf"},
    )

    assert response.status == 200
    export = response.body["export"]
    exported_path = Path(export["path"])
    assert export["format"] == "pdf"
    assert export["mime_type"] == "application/pdf"
    assert export["filename"].endswith(".pdf")
    assert exported_path.parent == output_dir
    assert exported_path.read_bytes().startswith(b"%PDF-")
    assert export["bytes"] == exported_path.stat().st_size


def test_result_export_api_rejects_invalid_format_and_cross_project_message(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KI_OUTPUT_DIR", str(tmp_path / "outputs"))
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    first_project = store.create_project("项目 A", first_dir)
    second_project = store.create_project("项目 B", second_dir)
    message = store.create_chat_message(
        project_id=first_project.id,
        question="默认入口是什么？",
        answer="默认入口是 app.py。",
        mode="local",
        provider="local",
        warning="",
        sources=[],
    )

    invalid_format = dispatch(
        store,
        "POST",
        "/api/export/result",
        {"project_id": first_project.id, "message_id": message.id, "format": "docx"},
    )
    cross_project = dispatch(
        store,
        "POST",
        "/api/export/result",
        {"project_id": second_project.id, "message_id": message.id, "format": "markdown"},
    )

    assert invalid_format.status == 400
    assert invalid_format.body["error"] == "format must be markdown or pdf"
    assert cross_project.status == 404
    assert cross_project.body["error"] == "chat message not found"


def test_project_restore_api_restores_backup_as_new_project_with_document_content_chunks_and_vectors(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    embedding_client = FakeEmbeddingClient()
    store = KnowledgeStore(tmp_path / "app.db", embedding_client=embedding_client)
    project = store.create_project("知识岛", project_dir)
    document = store.upsert_document(
        project.id,
        project_dir / "stack.md",
        "stack.md",
        "DeepSeek API Key 用于模型配置。\n\n本地 Web 服务负责页面和 API。",
    ).document
    original_chunks = store.list_chunks(project.id)
    original_vectors = {
        record["chunk_id"]: record
        for record in store.list_chunk_vector_records(project.id)
    }
    session = store.create_chat_session(project.id, "架构说明")
    message = store.create_chat_message(
        project.id,
        "默认入口是什么？",
        "默认入口是 app.py。",
        "local",
        "local",
        "",
        [
            {
                "path": "stack.md",
                "document_id": document.id,
                "chunk_id": original_chunks[0].id,
            }
        ],
        session_id=session.id,
    )
    assert embedding_client.calls == [["DeepSeek API Key 用于模型配置。", "本地 Web 服务负责页面和 API。"]]
    export_response = dispatch(store, "GET", f"/api/export/project?project_id={project.id}")

    restore_response = dispatch(
        store,
        "POST",
        "/api/export/project/restore",
        {"export": export_response.body["export"], "name": "知识岛恢复"},
    )

    assert restore_response.status == 200
    restored_project = restore_response.body["project"]
    assert restored_project["id"] != project.id
    assert restored_project["name"] == "知识岛恢复"
    assert restored_project["root_path"] == "browser-upload:知识岛恢复"
    assert restore_response.body["restored"] == {
        "documents": 1,
        "chunks": 2,
        "vectors": 2,
        "chat_sessions": 1,
        "chat_messages": 1,
    }
    assert embedding_client.calls == [["DeepSeek API Key 用于模型配置。", "本地 Web 服务负责页面和 API。"]]

    restored_documents = store.list_documents(restored_project["id"])
    assert len(restored_documents) == 1
    assert restored_documents[0].id != document.id
    assert restored_documents[0].relative_path == "stack.md"
    assert restored_documents[0].checksum == document.checksum
    assert restored_documents[0].content == "DeepSeek API Key 用于模型配置。\n\n本地 Web 服务负责页面和 API。"

    restored_chunks = store.list_chunks(restored_project["id"])
    assert [chunk.content for chunk in restored_chunks] == [chunk.content for chunk in original_chunks]
    assert [chunk.id for chunk in restored_chunks] != [chunk.id for chunk in original_chunks]
    assert [chunk.document.id for chunk in restored_chunks] == [restored_documents[0].id, restored_documents[0].id]

    restored_vectors = {
        record["chunk_id"]: record
        for record in store.list_chunk_vector_records(restored_project["id"])
    }
    assert len(restored_vectors) == 2
    assert {record["provider"] for record in restored_vectors.values()} == {"api"}
    assert {record["model"] for record in restored_vectors.values()} == {"fake-embedding"}
    assert {
        chunk.chunk_index: restored_vectors[chunk.id]["vector"]
        for chunk in restored_chunks
    } == {
        chunk.chunk_index: original_vectors[chunk.id]["vector"]
        for chunk in original_chunks
    }

    restored_sessions = store.list_chat_sessions(restored_project["id"])
    assert len(restored_sessions) == 1
    assert restored_sessions[0].title == "架构说明"

    restored_messages = store.list_all_chat_messages(restored_project["id"])
    assert len(restored_messages) == 1
    assert restored_messages[0].id != message.id
    assert restored_messages[0].question == "默认入口是什么？"
    assert restored_messages[0].session_id == restored_sessions[0].id
    assert restored_messages[0].sources[0]["document_id"] == restored_documents[0].id
    assert restored_messages[0].sources[0]["document_id"] != document.id
    assert restored_messages[0].sources[0]["chunk_id"] == restored_chunks[0].id
    assert restored_messages[0].sources[0]["chunk_id"] != original_chunks[0].id
    assert store.list_documents(project.id)[0].content.startswith("DeepSeek API Key")


def test_project_restore_api_rejects_missing_invalid_or_unsupported_backup(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    missing_export = dispatch(store, "POST", "/api/export/project/restore", {})
    missing_project = dispatch(
        store,
        "POST",
        "/api/export/project/restore",
        {"export": {"version": 1, "documents": [], "chat_messages": []}},
    )
    unsupported_version = dispatch(
        store,
        "POST",
        "/api/export/project/restore",
        {"export": {"version": 999, "project": {"name": "旧备份"}}},
    )

    assert missing_export.status == 400
    assert missing_export.body["error"] == "export is required"
    assert missing_project.status == 400
    assert missing_project.body["error"] == "export project is required"
    assert unsupported_version.status == 400
    assert unsupported_version.body["error"] == "unsupported export version"


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


def test_notion_zip_import_api_imports_markdown_export_and_records_batch(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", Path("browser-upload:知识岛"))
    export_content = _build_zip_base64({
        "Product Wiki.md": "# 产品知识库\n\n知识岛路线图来自 Notion 导出。",
        "Archive/Meeting Notes.md": "会议记录包含 RAG MVP 决策。",
        "assets/logo.png": "not a real image",
    })

    response = dispatch(
        store,
        "POST",
        "/api/import/notion-zip",
        {
            "project_id": project.id,
            "filename": "notion-export.zip",
            "content_base64": export_content,
        },
    )
    search_response = dispatch(
        store,
        "POST",
        "/api/search",
        {"project_id": project.id, "query": "Notion 导出"},
    )

    assert response.status == 200
    assert response.body["result"]["imported"] == 2
    assert response.body["result"]["created"] == 2
    assert response.body["result"]["skipped"] == 1
    assert response.body["result"]["skipped_details"] == [
        {"path": "assets/logo.png", "reason": "unsupported file type"}
    ]
    assert response.body["batch"]["source_type"] == "notion_zip"
    assert [doc["relative_path"] for doc in response.body["documents"]] == [
        "notion/Archive/Meeting Notes.md",
        "notion/Product Wiki.md",
    ]
    assert all(doc["source_path"].startswith("notion-zip:notion-export.zip#") for doc in response.body["documents"])
    assert search_response.body["hits"][0]["path"] == "notion/Product Wiki.md"


def test_obsidian_vault_import_api_imports_markdown_vault_and_records_batch(tmp_path: Path):
    vault = tmp_path / "obsidian-vault"
    vault.mkdir()
    (vault / "README.md").write_text("# Vault\n\nObsidian vault 保存长期笔记。", encoding="utf-8")
    daily_dir = vault / "Daily"
    daily_dir.mkdir()
    (daily_dir / "2026-06-28.md").write_text("今日记录 Knowledge Island 同步方案。", encoding="utf-8")
    obsidian_config = vault / ".obsidian"
    obsidian_config.mkdir()
    (obsidian_config / "app.json").write_text("{}", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", Path("browser-upload:知识岛"))

    response = dispatch(
        store,
        "POST",
        "/api/import/obsidian-vault",
        {
            "project_id": project.id,
            "vault_path": str(vault),
        },
    )
    search_response = dispatch(
        store,
        "POST",
        "/api/search",
        {"project_id": project.id, "query": "长期笔记"},
    )

    assert response.status == 200
    assert response.body["result"]["imported"] == 2
    assert response.body["result"]["created"] == 2
    assert response.body["result"]["skipped"] == 0
    assert response.body["batch"]["source_type"] == "obsidian_vault"
    assert [doc["relative_path"] for doc in response.body["documents"]] == [
        "obsidian/Daily/2026-06-28.md",
        "obsidian/README.md",
    ]
    assert search_response.body["hits"][0]["path"] == "obsidian/README.md"


def test_github_repo_import_service_clones_repo_and_imports_supported_files(tmp_path: Path):
    from webapp.github_import import import_github_repo

    store = KnowledgeStore(tmp_path / "app.db")
    clone_root = tmp_path / "github-repos"
    commands: list[list[str]] = []

    def fake_clone(command: list[str]) -> None:
        commands.append(command)
        target = Path(command[-1])
        target.mkdir(parents=True)
        (target / "README.md").write_text("# Island\n\nGitHub repo import.", encoding="utf-8")
        src_dir = target / "src"
        src_dir.mkdir()
        (src_dir / "app.py").write_text("print('hello island')", encoding="utf-8")
        ignored_dir = target / "node_modules" / "pkg"
        ignored_dir.mkdir(parents=True)
        (ignored_dir / "index.js").write_text("ignored dependency", encoding="utf-8")
        git_dir = target / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("ignored git metadata", encoding="utf-8")

    imported = import_github_repo(
        store,
        repo_url="https://github.com/acme/island.git",
        branch="main",
        project_name="Island Code",
        clone_root=clone_root,
        clone_runner=fake_clone,
    )

    assert len(commands) == 1
    command = commands[0]
    assert command[:4] == ["git", "clone", "--depth", "1"]
    assert command[4:6] == ["--branch", "main"]
    assert command[-2] == "https://github.com/acme/island.git"
    assert Path(command[-1]).parent == clone_root
    assert imported.project.name == "Island Code"
    assert imported.project.root_path == Path(command[-1])
    assert imported.result.imported == 2
    assert imported.result.created == 2
    assert imported.result.skipped == 0
    assert imported.result.skipped_details == []
    assert [doc.relative_path for doc in store.list_documents(imported.project.id)] == ["README.md", "src/app.py"]


def test_github_repo_import_api_creates_project_and_records_batch(tmp_path: Path, monkeypatch):
    import webapp.github_import as github_import

    store = KnowledgeStore(tmp_path / "app.db")
    clone_root = tmp_path / "github-repos"
    commands: list[list[str]] = []

    def fake_clone(command: list[str]) -> None:
        commands.append(command)
        target = Path(command[-1])
        target.mkdir(parents=True)
        (target / "README.md").write_text("# Island\n\nGitHub repo import.", encoding="utf-8")
        src_dir = target / "src"
        src_dir.mkdir()
        (src_dir / "app.py").write_text("print('hello island')", encoding="utf-8")

    monkeypatch.setattr(github_import, "github_clone_root", lambda: clone_root)
    monkeypatch.setattr(github_import, "run_git_clone", fake_clone)

    response = dispatch(
        store,
        "POST",
        "/api/import/github-repo",
        {
            "repo_url": "https://github.com/acme/island.git",
            "branch": "main",
            "project_name": "Island Code",
        },
    )

    assert response.status == 200
    assert len(commands) == 1
    assert response.body["project"]["name"] == "Island Code"
    assert response.body["project"]["root_exists"] is True
    assert response.body["result"]["imported"] == 2
    assert response.body["result"]["created"] == 2
    assert response.body["batch"]["source_type"] == "github_repo"
    assert response.body["batch"]["status"] == "success"
    assert [doc["relative_path"] for doc in response.body["documents"]] == ["README.md", "src/app.py"]

    list_response = dispatch(
        store,
        "GET",
        f"/api/import/batches?project_id={response.body['project']['id']}",
    )
    assert [batch["source_type"] for batch in list_response.body["batches"]] == ["github_repo"]


def test_github_repo_import_api_rejects_invalid_payloads(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    missing_url = dispatch(store, "POST", "/api/import/github-repo", {})
    invalid_host = dispatch(
        store,
        "POST",
        "/api/import/github-repo",
        {"repo_url": "https://gitlab.com/acme/island.git"},
    )

    assert missing_url.status == 400
    assert missing_url.body["error"] == "repo_url is required"
    assert invalid_host.status == 400
    assert invalid_host.body["error"] == "github repository url is invalid"


def test_notion_and_obsidian_import_apis_reject_invalid_payloads(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", Path("browser-upload:知识岛"))

    missing_zip_content = dispatch(
        store,
        "POST",
        "/api/import/notion-zip",
        {"project_id": project.id, "filename": "export.zip"},
    )
    invalid_zip = dispatch(
        store,
        "POST",
        "/api/import/notion-zip",
        {
            "project_id": project.id,
            "filename": "export.zip",
            "content_base64": base64.b64encode(b"not a zip").decode("ascii"),
        },
    )
    missing_vault_path = dispatch(
        store,
        "POST",
        "/api/import/obsidian-vault",
        {"project_id": project.id},
    )
    unknown_project = dispatch(
        store,
        "POST",
        "/api/import/obsidian-vault",
        {"project_id": "missing", "vault_path": str(tmp_path)},
    )
    missing_vault_directory = dispatch(
        store,
        "POST",
        "/api/import/obsidian-vault",
        {"project_id": project.id, "vault_path": str(tmp_path / "missing")},
    )

    assert missing_zip_content.status == 400
    assert missing_zip_content.body["error"] == "content_base64 is required"
    assert invalid_zip.status == 400
    assert invalid_zip.body["error"] == "invalid notion zip"
    assert missing_vault_path.status == 400
    assert missing_vault_path.body["error"] == "vault_path is required"
    assert unknown_project.status == 404
    assert unknown_project.body["error"] == "project not found"
    assert missing_vault_directory.status == 400
    assert missing_vault_directory.body["error"] == "obsidian vault path does not exist"


def _build_zip_base64(entries: dict[str, str]) -> str:
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        for name, content in entries.items():
            archive.writestr(name, content)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


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


def test_web_fetch_preview_and_commit_api_create_searchable_virtual_source(tmp_path: Path, monkeypatch):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    content = "自动抓取正文可进入检索"
    preview = WebFetchPreview(
        url="https://example.com/article",
        final_url="https://example.com/article",
        title="网页标题",
        content=content,
        content_length=len(content.encode("utf-8")),
        content_type="text/html",
        fetched_at="2026-06-30T09:30:00+00:00",
        robots_allowed=True,
        status_code=200,
        content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )

    monkeypatch.setattr(imports_route_module, "fetch_web_preview", lambda url: preview)

    preview_response = dispatch(
        store,
        "POST",
        "/api/import/web-fetch/preview",
        {"project_id": project.id, "url": "https://example.com/article"},
    )
    commit_response = dispatch(
        store,
        "POST",
        "/api/import/web-fetch/commit",
        {"project_id": project.id, "preview": preview_response.body["preview"]},
    )
    search_response = dispatch(
        store,
        "POST",
        "/api/search",
        {"project_id": project.id, "query": "自动抓取"},
    )

    assert preview_response.status == 200
    assert preview_response.body["preview"]["content_hash"] == preview.content_hash
    assert commit_response.status == 200
    assert commit_response.body["batch"]["source_type"] == "web_fetch"
    assert commit_response.body["document"]["source_path"].startswith("web:")
    assert commit_response.body["document"]["relative_path"].startswith("web/")
    assert "最终 URL：https://example.com/article" in commit_response.body["document"]["content"]
    assert "内容哈希：" in commit_response.body["document"]["content"]
    assert search_response.body["hits"][0]["document_id"] == commit_response.body["document"]["id"]


def test_web_fetch_commit_api_rejects_tampered_preview_payload(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", tmp_path)

    response = dispatch(
        store,
        "POST",
        "/api/import/web-fetch/commit",
        {
            "project_id": project.id,
            "preview": {
                "url": "https://example.com/article",
                "final_url": "https://example.com/article",
                "title": "网页标题",
                "content": "被改过的正文",
                "content_length": len("被改过的正文".encode("utf-8")),
                "content_type": "text/html",
                "fetched_at": "2026-06-30T09:30:00+00:00",
                "robots_allowed": True,
                "status_code": 200,
                "content_hash": "not-the-real-hash",
                "extractor_version": "static-html-v1",
            },
        },
    )

    assert response.status == 400
    assert response.body["error"] == "content hash does not match"
    assert store.list_documents(project.id) == []


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


def test_document_collection_api_creates_updates_lists_and_deletes_without_deleting_documents(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    document = store.upsert_document(project.id, project_dir / "api.md", "api.md", "接口文档").document

    create_response = dispatch(
        store,
        "POST",
        "/api/document-collections",
        {
            "project_id": project.id,
            "name": "接口资料",
            "description": "接口相关文档",
            "color": "#0f766e",
        },
    )
    collection_id = create_response.body["collection"]["id"]
    add_response = dispatch(
        store,
        "POST",
        "/api/document-collections/items/add",
        {"collection_id": collection_id, "document_ids": [document.id]},
    )
    update_response = dispatch(
        store,
        "POST",
        "/api/document-collections/update",
        {
            "collection_id": collection_id,
            "name": "API 资料",
            "description": "更新后的说明",
            "color": "#4f46e5",
        },
    )
    list_response = dispatch(store, "GET", f"/api/document-collections?project_id={project.id}")
    delete_response = dispatch(
        store,
        "POST",
        "/api/document-collections/delete",
        {"collection_id": collection_id},
    )

    assert create_response.status == 200
    assert create_response.body["collection"]["name"] == "接口资料"
    assert add_response.status == 200
    assert add_response.body["collection"]["document_count"] == 1
    assert update_response.status == 200
    assert update_response.body["collection"]["name"] == "API 资料"
    assert update_response.body["collection"]["description"] == "更新后的说明"
    assert update_response.body["collection"]["color"] == "#4f46e5"
    assert list_response.status == 200
    assert list_response.body["collections"][0]["document_count"] == 1
    assert delete_response.status == 200
    assert delete_response.body["deleted"] is True
    assert delete_response.body["collections"] == []
    assert store.get_document(document.id) is not None


def test_document_collection_items_filter_documents_and_unassigned_documents(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    api_doc = store.upsert_document(project.id, project_dir / "api.md", "api.md", "接口文档").document
    ui_doc = store.upsert_document(project.id, project_dir / "ui.md", "ui.md", "界面文档").document
    collection = dispatch(
        store,
        "POST",
        "/api/document-collections",
        {"project_id": project.id, "name": "接口资料"},
    ).body["collection"]

    add_response = dispatch(
        store,
        "POST",
        "/api/document-collections/items/add",
        {"collection_id": collection["id"], "document_ids": [api_doc.id]},
    )
    filtered_response = dispatch(
        store,
        "GET",
        f"/api/documents?project_id={project.id}&collection_id={collection['id']}",
    )
    unassigned_response = dispatch(
        store,
        "GET",
        f"/api/documents?project_id={project.id}&collection_id=unassigned",
    )
    remove_response = dispatch(
        store,
        "POST",
        "/api/document-collections/items/remove",
        {"collection_id": collection["id"], "document_ids": [api_doc.id]},
    )
    unassigned_after_remove = dispatch(
        store,
        "GET",
        f"/api/documents?project_id={project.id}&collection_id=unassigned",
    )

    assert add_response.status == 200
    assert [doc["relative_path"] for doc in filtered_response.body["documents"]] == ["api.md"]
    assert [doc["relative_path"] for doc in unassigned_response.body["documents"]] == ["ui.md"]
    assert remove_response.status == 200
    assert remove_response.body["collection"]["document_count"] == 0
    assert [doc["relative_path"] for doc in unassigned_after_remove.body["documents"]] == ["api.md", "ui.md"]
    assert {api_doc.id, ui_doc.id} == {doc.id for doc in store.list_documents(project.id)}


def test_document_collection_api_rejects_cross_project_documents_and_invalid_payloads(tmp_path: Path):
    project_a_dir = tmp_path / "a"
    project_b_dir = tmp_path / "b"
    project_a_dir.mkdir()
    project_b_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project_a = store.create_project("A", project_a_dir)
    project_b = store.create_project("B", project_b_dir)
    document_b = store.upsert_document(project_b.id, project_b_dir / "b.md", "b.md", "B 项目").document
    collection = dispatch(
        store,
        "POST",
        "/api/document-collections",
        {"project_id": project_a.id, "name": "A 集合"},
    ).body["collection"]

    missing_project = dispatch(store, "GET", "/api/document-collections")
    unknown_project = dispatch(store, "GET", "/api/document-collections?project_id=missing")
    blank_name = dispatch(
        store,
        "POST",
        "/api/document-collections",
        {"project_id": project_a.id, "name": " "},
    )
    cross_project = dispatch(
        store,
        "POST",
        "/api/document-collections/items/add",
        {"collection_id": collection["id"], "document_ids": [document_b.id]},
    )
    unknown_filter = dispatch(
        store,
        "GET",
        f"/api/documents?project_id={project_a.id}&collection_id=missing",
    )

    assert missing_project.status == 400
    assert missing_project.body["error"] == "project_id is required"
    assert unknown_project.status == 404
    assert unknown_project.body["error"] == "project not found"
    assert blank_name.status == 400
    assert blank_name.body["error"] == "name is required"
    assert cross_project.status == 404
    assert cross_project.body["error"] == "document not found"
    assert unknown_filter.status == 404
    assert unknown_filter.body["error"] == "document collection not found"


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


def test_admin_rebuild_index_api_rebuilds_missing_project_chunks_and_vectors(tmp_path: Path):
    project_dir = tmp_path / "notes"
    other_dir = tmp_path / "other"
    project_dir.mkdir()
    other_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db", embedding_client=FakeEmbeddingClient())
    project = store.create_project("知识岛", project_dir)
    other_project = store.create_project("其他项目", other_dir)
    store.upsert_document(project.id, project_dir / "stack.md", "stack.md", "DeepSeek API Key setup")
    store.upsert_document(other_project.id, other_dir / "other.md", "other.md", "Other project content")
    other_chunk_ids = [chunk.id for chunk in store.list_chunks(other_project.id)]

    with sqlite3.connect(store.db_path) as conn:
        conn.execute("DELETE FROM chunk_vectors WHERE project_id = ?", (project.id,))
        conn.execute("DELETE FROM document_chunks WHERE project_id = ?", (project.id,))

    response = dispatch(store, "POST", "/api/admin/rebuild-index", {"project_id": project.id})
    missing_project = dispatch(store, "POST", "/api/admin/rebuild-index", {"project_id": "missing"})

    rebuilt_chunks = store.list_chunks(project.id)
    assert response.status == 200
    assert response.body == {
        "rebuilt": True,
        "project_ids": [project.id],
        "summary": {"projects": 1, "documents": 1, "chunks": 1, "vectors": 1},
    }
    assert [chunk.document.relative_path for chunk in rebuilt_chunks] == ["stack.md"]
    assert store.count_chunk_vectors(project.id) == 1
    assert [chunk.id for chunk in store.list_chunks(other_project.id)] == other_chunk_ids
    assert missing_project.status == 404
    assert missing_project.body["error"] == "project not found"


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


class FakeEmbeddingClient:
    provider = "api"
    model = "fake-embedding"

    def __init__(self):
        self.calls = []

    def embed_texts(self, texts):
        self.calls.append(list(texts))
        vectors = []
        for text in texts:
            lowered = text.lower()
            vectors.append({
                "deepseek": 1.0 if "deepseek" in lowered else 0.0,
                "api": 1.0 if "api" in lowered else 0.0,
                "key": 1.0 if "key" in lowered else 0.0,
            })
        return vectors
