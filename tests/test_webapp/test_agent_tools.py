from pathlib import Path

from backend.api.dispatch import dispatch
from backend.storage import KnowledgeStore


def test_agent_tools_api_lists_readonly_tools(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(store, "GET", "/api/agent/tools")

    assert response.status == 200
    tool_names = [tool["name"] for tool in response.body["tools"]]
    assert "project_overview" in tool_names
    assert "search_sources" in tool_names
    assert "shell" not in tool_names
    assert all(tool["read_only"] is True for tool in response.body["tools"])


def test_agent_tools_api_returns_tool_metadata_for_readonly_whitelist(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    response = dispatch(store, "GET", "/api/agent/tools")

    assert response.status == 200
    tools = {tool["name"]: tool for tool in response.body["tools"]}
    assert set(tools) == {"project_overview", "search_sources"}
    for tool in tools.values():
        assert tool["label"]
        assert tool["description"]
        assert isinstance(tool["parameters_schema"], dict)
        assert tool["parameters_schema"]["type"] == "object"
        assert tool["result_summary"]
        assert tool["use_cases"]
        assert "shell" not in tool["use_cases"]
        assert "文件写入" not in tool["use_cases"]
        assert "网络抓取" not in tool["use_cases"]

    assert tools["project_overview"]["parameters_schema"]["properties"] == {}
    assert tools["project_overview"]["parameters_schema"]["additionalProperties"] is False
    assert tools["search_sources"]["parameters_schema"]["required"] == ["query"]
    assert tools["search_sources"]["parameters_schema"]["properties"]["query"]["type"] == "string"


def test_agent_project_overview_tool_returns_counts_and_records_audit(tmp_path: Path):
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
        "/api/agent/tools/run",
        {"project_id": project.id, "tool": "project_overview", "arguments": {}},
    )

    assert response.status == 200
    assert response.body["result"]["project_name"] == "知识岛"
    assert response.body["result"]["document_count"] == 1
    assert response.body["result"]["chunk_count"] >= 1
    assert response.body["result"]["chat_message_count"] == 1
    runs = store.list_agent_tool_runs(project.id)
    assert len(runs) == 1
    assert runs[0].tool_name == "project_overview"
    assert runs[0].status == "success"


def test_agent_tool_run_rejects_unknown_tool_and_records_error(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(
        store,
        "POST",
        "/api/agent/tools/run",
        {"project_id": project.id, "tool": "shell", "arguments": {"command": "dir"}},
    )

    assert response.status == 400
    assert response.body["error"] == "unknown or disabled tool"
    runs = store.list_agent_tool_runs(project.id)
    assert len(runs) == 1
    assert runs[0].tool_name == "shell"
    assert runs[0].status == "error"


def test_agent_search_sources_tool_returns_hits_and_records_audit(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)
    store.upsert_document(
        project.id,
        project_dir / "api.md",
        "api.md",
        "search endpoint 使用 keyword + vector 混合召回来源片段。",
    )
    store.upsert_document(
        project.id,
        project_dir / "ui.md",
        "ui.md",
        "设置页面负责保存模型配置。",
    )

    response = dispatch(
        store,
        "POST",
        "/api/agent/tools/run",
        {"project_id": project.id, "tool": "search_sources", "arguments": {"query": "search endpoint"}},
    )

    assert response.status == 200
    assert response.body["result"]["query"] == "search endpoint"
    assert response.body["result"]["hit_count"] >= 1
    assert response.body["result"]["hits"][0]["path"] == "api.md"
    runs = store.list_agent_tool_runs(project.id)
    assert runs[0].tool_name == "search_sources"
    assert runs[0].arguments == {"query": "search endpoint"}
    assert runs[0].result["hit_count"] >= 1


def test_agent_search_sources_tool_requires_query_and_records_error(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    response = dispatch(
        store,
        "POST",
        "/api/agent/tools/run",
        {"project_id": project.id, "tool": "search_sources", "arguments": {"query": "  "}},
    )

    assert response.status == 400
    assert response.body["error"] == "query is required"
    runs = store.list_agent_tool_runs(project.id)
    assert runs[0].tool_name == "search_sources"
    assert runs[0].status == "error"


def test_agent_tool_runs_api_lists_current_project_audit_history(tmp_path: Path):
    project_dir = tmp_path / "notes"
    project_dir.mkdir()
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("知识岛", project_dir)

    dispatch(
        store,
        "POST",
        "/api/agent/tools/run",
        {"project_id": project.id, "tool": "project_overview", "arguments": {}},
    )
    dispatch(
        store,
        "POST",
        "/api/agent/tools/run",
        {"project_id": project.id, "tool": "search_sources", "arguments": {"query": "默认入口"}},
    )

    response = dispatch(store, "GET", f"/api/agent/tools/runs?project_id={project.id}")

    assert response.status == 200
    assert [run["tool_name"] for run in response.body["runs"]] == ["search_sources", "project_overview"]
    assert response.body["runs"][0]["arguments"] == {"query": "默认入口"}
    assert response.body["runs"][0]["status"] == "success"


def test_agent_tool_runs_api_rejects_missing_or_unknown_project(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")

    missing_id_response = dispatch(store, "GET", "/api/agent/tools/runs")
    unknown_project_response = dispatch(store, "GET", "/api/agent/tools/runs?project_id=missing")

    assert missing_id_response.status == 400
    assert missing_id_response.body["error"] == "project_id is required"
    assert unknown_project_response.status == 404
    assert unknown_project_response.body["error"] == "project not found"
