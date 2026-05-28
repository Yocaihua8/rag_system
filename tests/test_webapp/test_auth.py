import importlib

import pytest


def _auth_module():
    try:
        return importlib.import_module("backend.webapp.auth")
    except ModuleNotFoundError:
        pytest.fail("backend.webapp.auth must provide authentication helpers")


def test_auth_settings_are_disabled_by_default():
    auth = _auth_module()

    settings = auth.load_auth_settings({})

    assert settings.enabled is False
    assert settings.api_key == ""
    assert settings.jwt_secret == ""
    assert settings.jwt_ttl_seconds == 3600


def test_auth_settings_require_key_and_secret_when_enabled():
    auth = _auth_module()

    with pytest.raises(ValueError, match="RAG_AUTH_API_KEY"):
        auth.load_auth_settings({"RAG_AUTH_ENABLED": "1", "RAG_AUTH_JWT_SECRET": "secret"})

    with pytest.raises(ValueError, match="RAG_AUTH_JWT_SECRET"):
        auth.load_auth_settings({"RAG_AUTH_ENABLED": "1", "RAG_AUTH_API_KEY": "secret-key"})


def test_api_key_validation_uses_configured_key():
    auth = _auth_module()
    settings = auth.load_auth_settings(
        {
            "RAG_AUTH_ENABLED": "1",
            "RAG_AUTH_API_KEY": "secret-key",
            "RAG_AUTH_JWT_SECRET": "jwt-secret",
        }
    )

    assert auth.validate_api_key(settings, "secret-key") is True
    assert auth.validate_api_key(settings, "wrong-key") is False
    assert auth.validate_api_key(settings, "") is False


def test_jwt_round_trip_returns_claims_until_expiry():
    auth = _auth_module()
    settings = auth.load_auth_settings(
        {
            "RAG_AUTH_ENABLED": "1",
            "RAG_AUTH_API_KEY": "secret-key",
            "RAG_AUTH_JWT_SECRET": "jwt-secret",
            "RAG_AUTH_JWT_TTL_SECONDS": "120",
        }
    )

    token = auth.issue_jwt(settings, subject="local-user", now=1000)
    claims = auth.validate_jwt(settings, token, now=1050)

    assert claims["sub"] == "local-user"
    assert claims["iat"] == 1000
    assert claims["exp"] == 1120
    assert auth.validate_jwt(settings, token, now=1121) is None


def test_jwt_validation_rejects_tampered_token():
    auth = _auth_module()
    settings = auth.load_auth_settings(
        {
            "RAG_AUTH_ENABLED": "1",
            "RAG_AUTH_API_KEY": "secret-key",
            "RAG_AUTH_JWT_SECRET": "jwt-secret",
        }
    )
    token = auth.issue_jwt(settings, subject="local-user", now=1000)
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    assert auth.validate_jwt(settings, tampered, now=1001) is None
