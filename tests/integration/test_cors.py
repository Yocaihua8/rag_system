from fastapi.testclient import TestClient

from backend.api.auth import load_auth_settings
from backend.api.server import create_app
from backend.config.desktop import DESKTOP_TOKEN_HEADER, DesktopRuntimeSettings
from backend.config.web import DEFAULT_CORS_ORIGINS, cors_origins


def _client(tmp_path, *, auth_enabled: bool = False) -> TestClient:
    auth = load_auth_settings(
        {
            "RAG_AUTH_ENABLED": "true" if auth_enabled else "false",
            "RAG_AUTH_API_KEY": "secret" if auth_enabled else "",
            "RAG_AUTH_JWT_SECRET": "jwt-secret" if auth_enabled else "",
        }
    )
    return TestClient(create_app(db_path=tmp_path / "app.db", auth_settings=auth))


def test_default_cors_origins_are_explicit_and_local_only():
    assert cors_origins({}) == DEFAULT_CORS_ORIGINS
    assert "*" not in DEFAULT_CORS_ORIGINS
    assert "http://127.0.0.1:5173" in DEFAULT_CORS_ORIGINS
    assert "http://127.0.0.1:5174" in DEFAULT_CORS_ORIGINS
    assert "http://127.0.0.1:4173" in DEFAULT_CORS_ORIGINS
    assert "http://127.0.0.1:4174" in DEFAULT_CORS_ORIGINS
    assert "tauri://localhost" in DEFAULT_CORS_ORIGINS


def test_cors_allows_configured_origin_and_required_request_headers(tmp_path):
    client = _client(tmp_path)
    response = client.options(
        "/api/projects",
        headers={
            "Origin": "http://127.0.0.1:5174",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type,x-api-key",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5174"
    assert response.headers.get("access-control-allow-credentials") is None
    assert "POST" in response.headers["access-control-allow-methods"]


def test_cors_rejects_unknown_origin(tmp_path):
    client = _client(tmp_path)
    response = client.options(
        "/api/projects",
        headers={
            "Origin": "https://example.invalid",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_authenticated_api_preflight_is_answered_before_authentication(tmp_path):
    client = _client(tmp_path, auth_enabled=True)
    response = client.options(
        "/api/projects",
        headers={
            "Origin": "http://127.0.0.1:4173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:4173"


def test_desktop_process_token_header_is_allowed_before_desktop_authentication(
    tmp_path,
):
    client = TestClient(
        create_app(
            db_path=tmp_path / "app.db",
            desktop_settings=DesktopRuntimeSettings(
                enabled=True,
                startup_token="ab" * 32,
            ),
        )
    )
    response = client.options(
        "/api/v3/health",
        headers={
            "Origin": "tauri://localhost",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": DESKTOP_TOKEN_HEADER,
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "tauri://localhost"
    assert DESKTOP_TOKEN_HEADER.lower() in response.headers[
        "access-control-allow-headers"
    ].lower()


def test_cors_configuration_rejects_wildcards():
    try:
        cors_origins({"KI_CORS_ORIGINS": "https://example.com,*"})
    except ValueError as error:
        assert "wildcard" in str(error)
    else:
        raise AssertionError("wildcard CORS origin must be rejected")
