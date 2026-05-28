from __future__ import annotations

from typing import Any

from webapp.api_support import query_value, test_llm_settings_with_client
from webapp.llm import OpenAICompatibleChatClient
from webapp.model_profiles import (
    llm_config_from_profile,
    model_profile_payload,
    model_profile_validation_error,
    profile_fields_from_payload,
)
from webapp.models import ApiResponse
from webapp.settings_api import get_llm_settings_body, save_llm_settings, test_llm_settings
from webapp.storage import KnowledgeStore

MAX_PROMPT_PRESET_TEXT_LENGTH = 4000
MAX_PROMPT_PRESET_FORMAT_LENGTH = 1000
PROMPT_PRESET_TEMPLATES = [
    {
        "name": "项目问答",
        "description": "回答项目是什么、怎么运行、接口在哪里等问题。",
        "system_prompt": "你是当前项目空间的问答助手。回答时优先说明依据文件；资料不足时直接指出缺口。",
        "answer_format": "先给结论，再列出依据来源和必要的下一步。",
    },
    {
        "name": "代码解释",
        "description": "解释文件、函数或模块职责。",
        "system_prompt": "你是代码解释助手。只解释已检索到的代码和文档片段，不臆测未提供的实现。",
        "answer_format": "按“结论 / 涉及文件 / 依据 / 注意点”组织回答。",
    },
    {
        "name": "学习复盘",
        "description": "把项目资料整理成学习提纲和检查点。",
        "system_prompt": "你是学习复盘助手。把来源资料转成可复习的知识点，不生成无来源结论。",
        "answer_format": "按“核心概念 / 自测问题 / 建议复习来源”组织回答。",
    },
]


def handle_settings_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
    llm_client: Any | None = None,
) -> ApiResponse | None:
    if method == "GET" and path == "/api/settings/llm":
        return ApiResponse(200, get_llm_settings_body())

    if method == "POST" and path == "/api/settings/llm":
        return ApiResponse(200, save_llm_settings(payload))

    if method == "POST" and path == "/api/settings/llm/test":
        try:
            return ApiResponse(200, test_llm_settings())
        except RuntimeError as exc:
            return ApiResponse(400, {"error": str(exc)})

    prompt_response = _handle_prompt_presets_route(store, method, path, query, payload)
    if prompt_response is not None:
        return prompt_response

    return _handle_model_profiles_route(store, method, path, payload)


def _handle_prompt_presets_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "GET" and path == "/api/prompt-presets":
        project_id = query_value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        return ApiResponse(
            200,
            {
                "presets": [preset.to_dict() for preset in store.list_prompt_presets(project_id)],
                "default_preset_id": store.get_default_prompt_preset_id(project_id) or "",
                "templates": PROMPT_PRESET_TEMPLATES,
            },
        )

    if method == "POST" and path == "/api/prompt-presets":
        project_id = str(payload.get("project_id", "")).strip()
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        error = _prompt_preset_validation_error(payload)
        if error:
            return ApiResponse(400, {"error": error})
        preset = store.create_prompt_preset(
            project_id,
            str(payload.get("name", "")),
            str(payload.get("description", "")),
            str(payload.get("system_prompt", "")),
            str(payload.get("answer_format", "")),
        )
        return ApiResponse(200, {"preset": preset.to_dict()})

    if method == "POST" and path == "/api/prompt-presets/update":
        preset_id = str(payload.get("preset_id", "")).strip()
        if not preset_id:
            return ApiResponse(400, {"error": "preset_id is required"})
        if not store.get_prompt_preset(preset_id):
            return ApiResponse(404, {"error": "prompt preset not found"})
        error = _prompt_preset_validation_error(payload)
        if error:
            return ApiResponse(400, {"error": error})
        preset = store.update_prompt_preset(
            preset_id,
            str(payload.get("name", "")),
            str(payload.get("description", "")),
            str(payload.get("system_prompt", "")),
            str(payload.get("answer_format", "")),
        )
        if not preset:
            return ApiResponse(404, {"error": "prompt preset not found"})
        return ApiResponse(200, {"preset": preset.to_dict()})

    if method == "POST" and path == "/api/prompt-presets/delete":
        preset_id = str(payload.get("preset_id", "")).strip()
        if not preset_id:
            return ApiResponse(400, {"error": "preset_id is required"})
        preset = store.delete_prompt_preset(preset_id)
        if not preset:
            return ApiResponse(404, {"error": "prompt preset not found"})
        presets = [entry.to_dict() for entry in store.list_prompt_presets(preset.project_id)]
        return ApiResponse(200, {"deleted": True, "presets": presets})

    if method == "POST" and path == "/api/prompt-presets/default":
        project_id = str(payload.get("project_id", "")).strip()
        preset_id = str(payload.get("preset_id", "")).strip()
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        if preset_id:
            preset = store.get_prompt_preset(preset_id)
            if not preset or preset.project_id != project_id:
                return ApiResponse(404, {"error": "prompt preset not found"})
        default_id = store.set_default_prompt_preset(project_id, preset_id)
        return ApiResponse(200, {"default_preset_id": default_id or ""})

    return None


def _handle_model_profiles_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "GET" and path == "/api/model-profiles":
        return ApiResponse(200, _model_profiles_body(store))

    if method == "POST" and path == "/api/model-profiles":
        error = model_profile_validation_error(payload)
        if error:
            return ApiResponse(400, {"error": error})
        fields = profile_fields_from_payload(payload)
        profile = store.create_model_profile(**fields)
        return ApiResponse(200, {"profile": model_profile_payload(profile)})

    if method == "POST" and path == "/api/model-profiles/update":
        profile_id = str(payload.get("profile_id", "")).strip()
        if not profile_id:
            return ApiResponse(400, {"error": "profile_id is required"})
        if not store.get_model_profile(profile_id):
            return ApiResponse(404, {"error": "model profile not found"})
        error = model_profile_validation_error(payload)
        if error:
            return ApiResponse(400, {"error": error})
        fields = profile_fields_from_payload(payload)
        profile = store.update_model_profile(profile_id=profile_id, **fields)
        if not profile:
            return ApiResponse(404, {"error": "model profile not found"})
        return ApiResponse(200, {"profile": model_profile_payload(profile)})

    if method == "POST" and path == "/api/model-profiles/delete":
        profile_id = str(payload.get("profile_id", "")).strip()
        if not profile_id:
            return ApiResponse(400, {"error": "profile_id is required"})
        profile = store.delete_model_profile(profile_id)
        if not profile:
            return ApiResponse(404, {"error": "model profile not found"})
        return ApiResponse(200, {"deleted": True, "profiles": _model_profiles_body(store)["profiles"]})

    if method == "POST" and path == "/api/model-profiles/default":
        profile_id = str(payload.get("profile_id", "")).strip()
        if profile_id and not store.get_model_profile(profile_id):
            return ApiResponse(404, {"error": "model profile not found"})
        default_id = store.set_default_model_profile(profile_id)
        return ApiResponse(200, {"default_profile_id": default_id})

    if method == "POST" and path == "/api/model-profiles/test":
        profile_id = str(payload.get("profile_id", "")).strip()
        if not profile_id:
            return ApiResponse(400, {"error": "profile_id is required"})
        profile = store.get_model_profile(profile_id)
        if not profile:
            return ApiResponse(404, {"error": "model profile not found"})
        client = OpenAICompatibleChatClient(llm_config_from_profile(profile), timeout=20.0)
        if not client.is_configured():
            return ApiResponse(400, {"error": "LLM provider is not configured"})
        try:
            result = test_llm_settings_with_client(client)
        except RuntimeError as exc:
            return ApiResponse(400, {"error": str(exc)})
        return ApiResponse(200, result)

    return None


def _model_profiles_body(store: KnowledgeStore) -> dict[str, Any]:
    return {
        "profiles": [model_profile_payload(profile) for profile in store.list_model_profiles()],
        "default_profile_id": store.get_default_model_profile_id(),
    }


def _prompt_preset_validation_error(payload: dict[str, Any]) -> str:
    name = str(payload.get("name", "")).strip()
    system_prompt = str(payload.get("system_prompt", "")).strip()
    answer_format = str(payload.get("answer_format", "")).strip()
    if not name:
        return "name is required"
    if not system_prompt:
        return "system_prompt is required"
    if len(system_prompt) > MAX_PROMPT_PRESET_TEXT_LENGTH:
        return "system_prompt is too long"
    if len(answer_format) > MAX_PROMPT_PRESET_FORMAT_LENGTH:
        return "answer_format is too long"
    return ""
