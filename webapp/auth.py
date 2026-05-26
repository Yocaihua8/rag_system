from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Mapping, Any


DEFAULT_JWT_TTL_SECONDS = 3600
MIN_JWT_TTL_SECONDS = 60


@dataclass(frozen=True)
class AuthSettings:
    enabled: bool
    api_key: str = ""
    jwt_secret: str = ""
    jwt_ttl_seconds: int = DEFAULT_JWT_TTL_SECONDS


def load_auth_settings(env: Mapping[str, str] | None = None) -> AuthSettings:
    values = os.environ if env is None else env
    enabled = _truthy(values.get("RAG_AUTH_ENABLED", ""))
    api_key = str(values.get("RAG_AUTH_API_KEY", "")).strip()
    jwt_secret = str(values.get("RAG_AUTH_JWT_SECRET", "")).strip()
    jwt_ttl_seconds = _ttl_seconds(values.get("RAG_AUTH_JWT_TTL_SECONDS", ""))
    if enabled and not api_key:
        raise ValueError("RAG_AUTH_API_KEY is required when RAG_AUTH_ENABLED=1")
    if enabled and not jwt_secret:
        raise ValueError("RAG_AUTH_JWT_SECRET is required when RAG_AUTH_ENABLED=1")
    return AuthSettings(
        enabled=enabled,
        api_key=api_key,
        jwt_secret=jwt_secret,
        jwt_ttl_seconds=jwt_ttl_seconds,
    )


def validate_api_key(settings: AuthSettings, candidate: str) -> bool:
    if not settings.enabled or not settings.api_key or not candidate:
        return False
    return hmac.compare_digest(settings.api_key, str(candidate))


def issue_jwt(
    settings: AuthSettings,
    subject: str = "local-user",
    now: int | None = None,
) -> str:
    if not settings.enabled or not settings.jwt_secret:
        raise ValueError("authentication is not enabled")
    issued_at = int(time.time() if now is None else now)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "iat": issued_at,
        "exp": issued_at + settings.jwt_ttl_seconds,
    }
    signing_input = f"{_base64url_json(header)}.{_base64url_json(payload)}"
    signature = _sign(settings.jwt_secret, signing_input)
    return f"{signing_input}.{signature}"


def validate_jwt(
    settings: AuthSettings,
    token: str,
    now: int | None = None,
) -> dict[str, Any] | None:
    if not settings.enabled or not settings.jwt_secret or not token:
        return None
    parts = str(token).split(".")
    if len(parts) != 3:
        return None
    signing_input = f"{parts[0]}.{parts[1]}"
    expected_signature = _sign(settings.jwt_secret, signing_input)
    if not hmac.compare_digest(expected_signature, parts[2]):
        return None
    header = _decode_base64url_json(parts[0])
    payload = _decode_base64url_json(parts[1])
    if not isinstance(header, dict) or header.get("alg") != "HS256":
        return None
    if not isinstance(payload, dict):
        return None
    expires_at = _int_value(payload.get("exp"))
    if expires_at is None:
        return None
    current_time = int(time.time() if now is None else now)
    if current_time > expires_at:
        return None
    return payload


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _ttl_seconds(value: str) -> int:
    try:
        parsed = int(str(value).strip())
    except ValueError:
        parsed = DEFAULT_JWT_TTL_SECONDS
    return max(MIN_JWT_TTL_SECONDS, parsed)


def _base64url_json(data: dict[str, Any]) -> str:
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _base64url_encode(raw)


def _decode_base64url_json(value: str) -> Any | None:
    try:
        raw = _base64url_decode(value)
        return json.loads(raw.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None


def _sign(secret: str, signing_input: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
    return _base64url_encode(digest)


def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))


def _int_value(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
