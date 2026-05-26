from fastapi.testclient import TestClient

from webapp.auth import load_auth_settings, validate_jwt
from webapp.server import create_app


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


def test_auth_disabled_keeps_existing_api_access(tmp_path):
    client = _client(tmp_path, load_auth_settings({}))

    response = client.get("/api/projects")

    assert response.status_code == 200
    assert "projects" in response.json()


def test_auth_enabled_allows_health_and_static_index_without_credentials(tmp_path):
    client = _client(tmp_path, _auth_settings())

    health_response = client.get("/api/health")
    index_response = client.get("/")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert index_response.status_code == 200
    assert index_response.headers["content-type"].startswith("text/html")


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

    assert docs_response.status_code == 401
    assert docs_response.json() == {"error": "authentication required"}
    assert openapi_response.status_code == 401
    assert authorized_docs_response.status_code == 200
