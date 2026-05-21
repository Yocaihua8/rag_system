from pathlib import Path

from webapp.api import dispatch
from webapp.ingestion import import_directory
from webapp.storage import KnowledgeStore


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
    assert response.body["tool_suggestion"] == {
        "tool": "search_sources",
        "arguments": {"query": "默认入口是什么？"},
        "reason": "当前回答没有可用来源，可先用只读来源检索工具扩大召回。",
    }
    assert store.list_agent_tool_runs(project.id) == []


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
