from pathlib import Path


def test_web_mvp_api_spec_documents_http_endpoints():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")

    assert "不对外提供 HTTP/API 服务" not in api_spec
    for endpoint in [
        "GET /api/health",
        "GET /api/projects",
        "POST /api/projects",
        "POST /api/import",
        "POST /api/search",
        "POST /api/answer",
        "GET /api/chat/messages",
        "GET /api/agent/tools",
        "POST /api/agent/tools/run",
    ]:
        assert endpoint in api_spec


def test_upload_api_spec_documents_binary_document_payload():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")

    assert "content_base64" in api_spec
    assert "pdf extraction requires optional parser" in api_spec


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
