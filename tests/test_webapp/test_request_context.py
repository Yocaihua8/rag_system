from types import MappingProxyType

import pytest
from fastapi.testclient import TestClient

import backend.api.dispatch as dispatch_module
import backend.api.server as server
from backend.api.auth import AuthSettings
from backend.domain.models import ApiResponse
from backend.storage import KnowledgeStore


def test_dispatch_forwards_an_immutable_optional_request_context(tmp_path, monkeypatch):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    captured = {}

    def capture_routes(
        store,
        method,
        path,
        query,
        payload,
        llm_client=None,
        request_context=None,
    ):
        captured["request_context"] = request_context
        return ApiResponse(200, {"ok": True})

    monkeypatch.setattr(dispatch_module, "dispatch_to_routes", capture_routes)

    response = dispatch_module.dispatch(
        store,
        "GET",
        "/api/context",
        request_context={"authorization": "Bearer plugin-token"},
    )

    assert response.status == 200
    assert isinstance(captured["request_context"], MappingProxyType)
    assert captured["request_context"]["authorization"] == "Bearer plugin-token"
    with pytest.raises(TypeError):
        captured["request_context"]["authorization"] = "changed"


def test_fastapi_dispatch_passes_the_authorization_header_only(tmp_path, monkeypatch):
    store = KnowledgeStore(tmp_path / "app.db", vector_store=None)
    captured = {}

    def capture_dispatch(
        store,
        method,
        raw_path,
        payload=None,
        llm_client=None,
        request_context=None,
    ):
        captured["request_context"] = request_context
        return ApiResponse(200, {"ok": True})

    monkeypatch.setattr(server, "dispatch", capture_dispatch)
    client = TestClient(
        server.create_app(
            store=store,
            auth_settings=AuthSettings(enabled=False),
        )
    )

    response = client.get(
        "/api/context",
        headers={
            "Authorization": "Bearer plugin-token",
            "X-Unrelated": "must-not-be-forwarded",
        },
    )

    assert response.status_code == 200
    assert captured["request_context"] == {
        "authorization": "Bearer plugin-token",
    }
