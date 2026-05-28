from __future__ import annotations

import os
from typing import Any

from src.config.settings import _persistent_env, load_settings
from backend.webapp.llm import LlmConfig
from backend.webapp.models import ModelProfile

ALLOWED_API_KEY_REFS = {
    "",
    "env:RAG_LLM_API_KEY",
    "env:DEEPSEEK_API_KEY",
    "saved:RAG_LLM_API_KEY",
}


def model_profile_payload(profile: ModelProfile) -> dict[str, Any]:
    key_value, key_source = resolve_api_key_ref(profile.api_key_ref)
    return profile.to_dict(has_api_key=bool(key_value), api_key_source=key_source)


def model_profile_validation_error(payload: dict[str, Any]) -> str:
    name = str(payload.get("name", "")).strip()
    provider = str(payload.get("provider", "")).strip().lower()
    model = str(payload.get("model", "")).strip()
    api_key_ref = str(payload.get("api_key_ref", "")).strip()
    if not name:
        return "name is required"
    if provider not in {"api", "ollama"}:
        return "provider is required"
    if not model:
        return "model is required"
    if api_key_ref not in ALLOWED_API_KEY_REFS:
        return "api_key_ref is invalid"
    return ""


def profile_fields_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(payload.get("name", "")).strip(),
        "provider": str(payload.get("provider", "")).strip().lower(),
        "api_base": str(payload.get("api_base", "")).strip(),
        "model": str(payload.get("model", "")).strip(),
        "temperature": _float_value(payload.get("temperature"), 0.7, 0.0, 2.0),
        "max_tokens": _int_value(payload.get("max_tokens"), 2048, 1, 128000),
        "api_key_ref": str(payload.get("api_key_ref", "")).strip(),
    }


def llm_config_from_profile(profile: ModelProfile) -> LlmConfig:
    api_key, _ = resolve_api_key_ref(profile.api_key_ref)
    return LlmConfig(
        provider=profile.provider,
        api_base=profile.api_base,
        api_key=api_key,
        model=profile.model,
        temperature=profile.temperature,
        max_tokens=profile.max_tokens,
    )


def resolve_api_key_ref(api_key_ref: str) -> tuple[str, str]:
    clean_ref = api_key_ref.strip()
    if clean_ref == "env:RAG_LLM_API_KEY":
        return _env_value("RAG_LLM_API_KEY"), "environment" if _env_value("RAG_LLM_API_KEY") else ""
    if clean_ref == "env:DEEPSEEK_API_KEY":
        value = _env_value("DEEPSEEK_API_KEY") or _env_value("DEEPSEEK_APIKEY") or _env_value("deepseekapikey")
        return value, "environment" if value else ""
    if clean_ref == "saved:RAG_LLM_API_KEY":
        value = load_settings().llm_api_key
        return value, "saved" if value else ""
    return "", ""


def _env_value(key: str) -> str:
    return os.environ.get(key, "") or _persistent_env().get(key, "")


def _int_value(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _float_value(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))
