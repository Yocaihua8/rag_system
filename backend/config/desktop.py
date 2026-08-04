"""Desktop-only process binding and session authentication settings."""
from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass

from backend.config.settings import load_backend_env
from backend.config.web import DEFAULT_HOST, DEFAULT_PORT


DESKTOP_TOKEN_HEADER = "X-KI-Desktop-Token"
DESKTOP_TOKEN_ENV = "KI_DESKTOP_STARTUP_TOKEN"
DESKTOP_MODE_ENV = "KI_DESKTOP_MODE"
_TOKEN_PATTERN = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class DesktopRuntimeSettings:
    enabled: bool
    startup_token: str = ""


@dataclass(frozen=True)
class ServerBinding:
    host: str
    port: int


def load_desktop_settings(
    environ: Mapping[str, str] | None = None,
) -> DesktopRuntimeSettings:
    values = _values(environ)
    enabled = _truthy(values.get(DESKTOP_MODE_ENV, ""))
    if not enabled:
        return DesktopRuntimeSettings(enabled=False)

    token = str(values.get(DESKTOP_TOKEN_ENV, "")).strip()
    if not _TOKEN_PATTERN.fullmatch(token):
        raise ValueError(
            f"{DESKTOP_TOKEN_ENV} must be 64 lowercase hexadecimal characters"
        )
    return DesktopRuntimeSettings(enabled=True, startup_token=token)


def load_server_binding(
    environ: Mapping[str, str] | None = None,
    *,
    desktop_settings: DesktopRuntimeSettings | None = None,
) -> ServerBinding:
    values = _values(environ)
    desktop = desktop_settings or load_desktop_settings(values)
    host = str(values.get("KI_API_HOST", DEFAULT_HOST)).strip() or DEFAULT_HOST
    raw_port = str(values.get("KI_API_PORT", "")).strip()

    if desktop.enabled and not raw_port:
        raise ValueError("KI_API_PORT is required when KI_DESKTOP_MODE=1")
    try:
        port = int(raw_port or DEFAULT_PORT)
    except ValueError as exc:
        raise ValueError("KI_API_PORT must be an integer") from exc
    if port < 1 or port > 65_535:
        raise ValueError("KI_API_PORT must be between 1 and 65535")
    if desktop.enabled and host != DEFAULT_HOST:
        raise ValueError("desktop mode must bind exactly to 127.0.0.1")
    return ServerBinding(host=host, port=port)


def _values(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    if environ is not None:
        return environ
    return {**load_backend_env(), **os.environ}


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


__all__ = [
    "DESKTOP_MODE_ENV",
    "DESKTOP_TOKEN_ENV",
    "DESKTOP_TOKEN_HEADER",
    "DesktopRuntimeSettings",
    "ServerBinding",
    "load_desktop_settings",
    "load_server_binding",
]
