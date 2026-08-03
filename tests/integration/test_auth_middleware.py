from fastapi.testclient import TestClient

from backend.api.auth import load_auth_settings, validate_jwt
from backend.api.server import create_app
from backend.config.desktop import DESKTOP_TOKEN_HEADER, DesktopRuntimeSettings


DESKTOP_TOKEN = "ab" * 32


def _auth_settings():
    return load_auth_settings(
        {
            "RAG_AUTH_ENABLED": "1",
            "RAG_AUTH_API_KEY": "secret-key",
            "RAG_AUTH_JWT_SECRET": "jwt-secret",
            "RAG_AUTH_JWT_TTL_SECONDS": "120",
        }
    )


def _client(tmp_path, settings):
    return TestClient(create_app(db_path=tmp_path / "app.db", auth_settings=settings))


def _desktop_client(tmp_path, settings=None):
    return TestClient(
        create_app(
            db_path=tmp_path / "app.db",
            auth_settings=settings or load_auth_settings({}),
            desktop_settings=DesktopRuntimeSettings(
                enabled=True,
                startup_token=DESKTOP_TOKEN,
            ),
        )
    )


def test_auth_disabled_keeps_existing_api_access(tmp_path):
    client = _client(tmp_path, load_auth_settings({}))

    response = client.get("/api/projects")

    assert response.status_code == 200
    assert "projects" in response.json()


def test_auth_enabled_allows_health_but_root_remains_api_only(tmp_path):
    client = _client(tmp_path, _auth_settings())

    health_response = client.get("/api/health")
    index_response = client.get("/")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert index_response.status_code == 404


def test_auth_enabled_rejects_protected_api_without_credentials(tmp_path):
    client = _client(tmp_path, _auth_settings())

    response = client.get("/api/projects")

    assert response.status_code == 401
    assert response.json() == {"error": "authentication required"}


def test_auth_enabled_rejects_invalid_api_key(tmp_path):
    client = _client(tmp_path, _auth_settings())

    response = client.get("/api/projects", headers={"X-API-Key": "wrong-key"})

    assert response.status_code == 401
    assert response.json() == {"error": "invalid credentials"}


def test_auth_enabled_accepts_configured_api_key(tmp_path):
    client = _client(tmp_path, _auth_settings())

    response = client.get("/api/projects", headers={"X-API-Key": "secret-key"})

    assert response.status_code == 200
    assert "projects" in response.json()


def test_token_endpoint_exchanges_api_key_for_bearer_token(tmp_path):
    settings = _auth_settings()
    client = _client(tmp_path, settings)

    response = client.post("/api/auth/token", headers={"X-API-Key": "secret-key"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 120
    assert validate_jwt(settings, body["access_token"]) is not None


def test_auth_enabled_accepts_bearer_token(tmp_path):
    client = _client(tmp_path, _auth_settings())
    token_response = client.post("/api/auth/token", headers={"X-API-Key": "secret-key"})
    token = token_response.json()["access_token"]

    response = client.get("/api/projects", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert "projects" in response.json()


def test_auth_enabled_protects_fastapi_docs(tmp_path):
    client = _client(tmp_path, _auth_settings())

    docs_response = client.get("/docs")
    openapi_response = client.get("/openapi.json")
    authorized_docs_response = client.get("/docs", headers={"X-API-Key": "secret-key"})
    authorized_openapi_response = client.get("/openapi.json", headers={"X-API-Key": "secret-key"})

    assert docs_response.status_code == 401
    assert docs_response.json() == {"error": "authentication required"}
    assert openapi_response.status_code == 401
    assert authorized_docs_response.status_code == 200
    assert authorized_openapi_response.status_code == 200
    assert "/api/answer/compare" in authorized_openapi_response.json()["paths"]


def test_desktop_mode_protects_health_api_and_docs_with_process_token(tmp_path):
    client = _desktop_client(tmp_path)

    for path in ("/api/health", "/api/projects", "/docs", "/openapi.json"):
        missing_response = client.get(path)
        invalid_response = client.get(
            path,
            headers={DESKTOP_TOKEN_HEADER: "cd" * 32},
        )
        accepted_response = client.get(
            path,
            headers={DESKTOP_TOKEN_HEADER: DESKTOP_TOKEN},
        )

        assert missing_response.status_code == 401
        assert missing_response.json() == {"error": "authentication required"}
        assert "www-authenticate" not in missing_response.headers
        assert invalid_response.status_code == 401
        assert invalid_response.json() == {"error": "invalid credentials"}
        assert accepted_response.status_code == 200


def test_desktop_mode_does_not_accept_web_api_key_or_issue_web_token(tmp_path):
    client = _desktop_client(tmp_path, _auth_settings())

    api_key_response = client.get(
        "/api/projects",
        headers={"X-API-Key": "secret-key"},
    )
    desktop_response = client.get(
        "/api/projects",
        headers={DESKTOP_TOKEN_HEADER: DESKTOP_TOKEN},
    )
    token_response = client.post(
        "/api/auth/token",
        headers={
            DESKTOP_TOKEN_HEADER: DESKTOP_TOKEN,
            "X-API-Key": "secret-key",
        },
    )

    assert api_key_response.status_code == 401
    assert desktop_response.status_code == 200
    assert token_response.status_code == 404
    assert token_response.json() == {"error": "not found"}


def test_desktop_mode_keeps_obsidian_pairing_self_authenticated(tmp_path):
    client = _desktop_client(tmp_path)

    response = client.post("/api/obsidian/pairing/complete", json={})

    assert response.status_code != 401
