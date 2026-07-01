from __future__ import annotations

from typing import Any, Iterable

from backend.providers.llm.ollama import OllamaLLM
from backend.domain.models import ApiResponse, ApiStreamEvent

RECOMMENDED_FIRST_RUN_MODELS = [
    {"model": "qwen2.5:3b", "label": "轻量 CPU 可用", "size_hint": "~2GB"},
    {"model": "qwen2.5:7b", "label": "均衡推荐", "size_hint": "~5GB"},
    {"model": "deepseek-r1:8b", "label": "推理增强", "size_hint": "~5GB"},
]


def handle_ollama_route(
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "GET" and path == "/api/ollama/status":
        return ApiResponse(200, ollama_status_body())
    return None


def ollama_status_body(client: OllamaLLM | None = None) -> dict[str, Any]:
    ollama = client or OllamaLLM(timeout=5.0)
    try:
        tags = ollama.get_tags()
    except Exception as exc:
        return {
            "available": False,
            "host": ollama.host,
            "models": [],
            "recommended_models": recommended_models(),
            "error": str(exc),
        }
    return {
        "available": True,
        "host": ollama.host,
        "models": _model_names(tags),
        "recommended_models": recommended_models(),
        "error": "",
    }


def validate_ollama_pull_payload(payload: dict[str, Any]) -> str:
    model = str(payload.get("model", "")).strip()
    if not model:
        return "model is required"
    if model not in _recommended_model_names():
        return "model is not in the recommended first-run list"
    return ""


def ollama_pull_events(model: str, client: OllamaLLM | None = None) -> Iterable[ApiStreamEvent]:
    ollama = client or OllamaLLM(timeout=600.0)
    try:
        for item in ollama.pull_model(model):
            status = str(item.get("status", "")).strip()
            if status == "success":
                yield ApiStreamEvent("done", {"status": "done", "model": model})
                return
            yield ApiStreamEvent("progress", _progress_body(model, item, status))
    except Exception as exc:
        yield ApiStreamEvent("error", {"error": str(exc), "model": model})


def recommended_models() -> list[dict[str, str]]:
    return [dict(item) for item in RECOMMENDED_FIRST_RUN_MODELS]


def _model_names(tags: dict[str, Any]) -> list[str]:
    models = tags.get("models", [])
    if not isinstance(models, list):
        return []
    return [str(item.get("name", "")) for item in models if isinstance(item, dict) and item.get("name")]


def _recommended_model_names() -> set[str]:
    return {item["model"] for item in RECOMMENDED_FIRST_RUN_MODELS}


def _progress_body(model: str, item: dict[str, Any], status: str) -> dict[str, Any]:
    body: dict[str, Any] = {"status": status, "model": model}
    completed = item.get("completed")
    total = item.get("total")
    if isinstance(completed, int) and isinstance(total, int) and total > 0:
        body["completed"] = completed
        body["total"] = total
        body["progress"] = completed / total
    return body
