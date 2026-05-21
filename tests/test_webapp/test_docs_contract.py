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
    ]:
        assert endpoint in api_spec


def test_upload_api_spec_documents_binary_document_payload():
    api_spec = Path("docs/design/api-spec.md").read_text(encoding="utf-8")

    assert "content_base64" in api_spec
    assert "pdf extraction requires optional parser" in api_spec
