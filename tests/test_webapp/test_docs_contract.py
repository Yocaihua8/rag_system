from pathlib import Path


def test_web_mvp_api_spec_documents_http_endpoints():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")

    assert "不对外提供 HTTP/API 服务" not in api_spec
    for endpoint in [
        "GET /api/health",
        "GET /api/projects",
        "GET /api/projects/summary",
        "GET /api/projects/retrieval-settings",
        "GET /api/prompt-presets",
        "POST /api/projects",
        "POST /api/projects/retrieval-settings",
        "POST /api/prompt-presets",
        "POST /api/prompt-presets/update",
        "POST /api/prompt-presets/delete",
        "POST /api/prompt-presets/default",
        "GET /api/export/project",
        "GET /api/import/preview",
        "POST /api/import",
        "POST /api/search",
        "POST /api/import/note",
        "POST /api/search/debug",
        "POST /api/retrieval/reviews",
        "GET /api/retrieval/reviews",
        "GET /api/retrieval/reviews/detail",
        "POST /api/retrieval/reviews/delete",
        "POST /api/answer",
        "GET /api/chat/sessions",
        "POST /api/chat/sessions",
        "POST /api/chat/sessions/rename",
        "POST /api/chat/sessions/delete",
        "GET /api/chat/messages",
        "POST /api/chat/messages/delete",
        "POST /api/chat/messages/clear",
        "GET /api/agent/tools",
        "POST /api/agent/tools/run",
        "GET /api/agent/tools/runs",
        "GET /api/agent/tools/runs/detail",
    ]:
        assert endpoint in api_spec

    for summary_field in [
        "document_count",
        "chunk_count",
        "vector_count",
        "chat_message_count",
        "agent_tool_run_count",
        "retrieval_review_count",
        "last_activity_at",
    ]:
        assert summary_field in api_spec


def test_project_export_contract_is_documented():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "GET /api/export/project" in api_spec
    assert "settings_summary" in api_spec
    assert "key_configured" in api_spec
    assert "project_id is required" in api_spec
    assert "project not found" in api_spec
    assert "不导出 API Key" in api_spec
    assert "备份导出" in readme


def test_upload_api_spec_documents_binary_document_payload():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")

    assert "content_base64" in api_spec
    assert "pdf extraction requires optional parser" in api_spec
    assert "no extractable text" in api_spec


def test_note_import_contract_is_documented():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "/api/import/note" in api_spec
    assert "/api/import/url" in api_spec
    assert "title" in api_spec
    assert "content" in api_spec
    assert "note:" in api_spec
    assert "url:" in api_spec
    assert "文本笔记" in readme


def test_retrieval_review_contract_is_documented():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")
    database_design = Path("docs/design/database-design.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "/api/retrieval/reviews" in api_spec
    assert "retrieval_reviews" in database_design
    assert "parameters" in api_spec
    assert "source_quality" in api_spec
    assert "review_id is required" in api_spec
    assert "retrieval review not found" in api_spec
    assert '{"deleted":true}' in api_spec
    assert "只影响 retrieval_reviews" in api_spec
    assert "检索复盘" in readme


def test_search_api_spec_documents_chunk_source_fields():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")
    database_design = Path("docs/design/database-design.md").read_text(encoding="utf-8")

    assert "chunk_id" in api_spec
    assert "chunk_index" in api_spec
    assert "document_chunks" in database_design


def test_search_api_spec_documents_hybrid_vector_fields():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")
    database_design = Path("docs/design/database-design.md").read_text(encoding="utf-8")

    for field in ["retrieval", "keyword_score", "vector_score", "vector_provider", "vector_model"]:
        assert field in api_spec
    assert "source_quality" in api_spec
    for level in ["good", "weak", "none"]:
        assert level in api_spec
    assert "/api/search/debug" in api_spec
    assert "chunk_vectors" in database_design
    assert "provider/model" in database_design


def test_embedding_provider_config_is_documented():
    readme = Path("README.md").read_text(encoding="utf-8")
    env_example = Path(".env.example").read_text(encoding="utf-8")

    for key in ["RAG_EMBED_PROVIDER", "RAG_EMBED_API_BASE", "RAG_EMBED_API_MODEL", "RAG_EMBED_API_KEY"]:
        assert key in readme
        assert key in env_example


def test_chat_history_context_boundary_is_documented():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "最近 3 轮" in api_spec
    assert "最近 3 轮" in readme
    assert "不是完整 Agent 记忆" in api_spec


def test_agent_readonly_tools_are_documented():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")
    database_design = Path("docs/design/database-design.md").read_text(encoding="utf-8")

    assert "project_overview" in api_spec
    assert "search_sources" in api_spec
    assert "只读" in api_spec
    assert "不开放 shell" in api_spec
    assert "agent_tool_runs" in database_design
    assert "工具运行历史" in api_spec
    assert "run_id is required" in api_spec
    assert "tool run not found" in api_spec
    assert '{"run":...}' in api_spec


def test_agent_tool_metadata_contract_is_documented():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")

    for field in ["name", "description", "parameters_schema", "result_summary", "use_cases"]:
        assert field in api_spec
    assert "label" in api_spec
    assert "additionalProperties" in api_spec
    assert "required" in api_spec
    assert "项目概览" in api_spec
    assert "检索来源" in api_spec


def test_answer_tool_suggestion_contract_is_documented():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "tool_suggestion" in api_spec
    assert "search_sources" in api_spec
    assert "不自动执行" in api_spec
    assert "建议工具" in readme
    assert "手动运行" in readme
    assert "tool_run_id" in api_spec
    assert "tool_context" in api_spec


def test_chat_history_delete_contract_is_documented():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")

    assert "POST /api/chat/messages/delete" in api_spec
    assert "POST /api/chat/messages/clear" in api_spec
    assert "message_id is required" in api_spec
    assert "chat message not found" in api_spec


def test_chat_sessions_contract_is_documented():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")
    database_design = Path("docs/design/database-design.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "chat_sessions" in database_design
    assert "session_id" in api_spec
    assert "chat session not found" in api_spec
    assert "默认会话" in api_spec
    assert "多会话聊天" in readme


def test_answer_feedback_contract_is_documented():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")
    database_design = Path("docs/design/database-design.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "POST /api/answer/feedback" in api_spec
    assert "answer_feedback" in database_design
    assert '{"feedback":...}' in api_spec
    for rating in ["useful", "not_useful", "source_wrong", "need_more_context"]:
        assert rating in api_spec
    assert "rating is invalid" in api_spec
    assert "消息必须属于当前项目" in api_spec
    assert "回答反馈" in readme


def test_prompt_preset_contract_is_documented():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")
    database_design = Path("docs/design/database-design.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    for endpoint in [
        "GET /api/prompt-presets",
        "POST /api/prompt-presets",
        "POST /api/prompt-presets/update",
        "POST /api/prompt-presets/delete",
        "POST /api/prompt-presets/default",
    ]:
        assert endpoint in api_spec
    assert "prompt_presets" in database_design
    assert "default_prompt_preset_id" in database_design
    assert "项目问答" in api_spec
    assert "代码解释" in api_spec
    assert "学习复盘" in api_spec
    assert "prompt preset not found" in api_spec
    assert "不保存 API Key" in api_spec
    assert "Prompt 预设" in readme


def test_answer_observability_contract_is_documented():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "observability" in api_spec
    for field in ["top_k", "min_score", "use_keyword", "use_vector", "hit_count", "mode", "provider", "elapsed_ms"]:
        assert field in api_spec
    assert "最终可用来源数量" in api_spec
    assert "不持久化为新的数据库表" in api_spec
    assert "问答可观察性" in readme


def test_project_retrieval_settings_contract_is_documented():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")
    database_design = Path("docs/design/database-design.md").read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "GET /api/projects/retrieval-settings" in api_spec
    assert "POST /api/projects/retrieval-settings" in api_spec
    for field in ["retrieval_top_k", "retrieval_min_score", "retrieval_use_keyword", "retrieval_use_vector"]:
        assert field in database_design
    assert "问答和检索诊断共用" in api_spec
    assert "项目级检索默认值" in readme
