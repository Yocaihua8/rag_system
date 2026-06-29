from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

OPENAPI_TITLE = "Knowledge Island"
OPENAPI_VERSION = "0.1.0"

WEB_MVP_API_OPERATIONS: list[tuple[str, str, str]] = [
    ("GET", "/api/health", "Health check"),
    ("POST", "/api/auth/token", "Exchange API key for bearer token"),
    ("POST", "/api/admin/rebuild-index", "Rebuild document chunks and vector index"),
    ("GET", "/api/ollama/status", "Check local Ollama status"),
    ("POST", "/api/ollama/pull", "Pull a recommended Ollama model"),
    ("GET", "/api/projects", "List project spaces"),
    ("GET", "/api/projects/summary", "Get project summary"),
    ("POST", "/api/projects", "Create project space"),
    ("POST", "/api/projects/rename", "Rename project space"),
    ("POST", "/api/projects/delete", "Delete project space"),
    ("GET", "/api/export/project", "Export project backup"),
    ("POST", "/api/export/project/restore", "Restore project backup"),
    ("GET", "/api/documents", "List project documents"),
    ("GET", "/api/document", "Get document detail"),
    ("POST", "/api/documents/delete", "Delete document record"),
    ("GET", "/api/document-collections", "List document collections"),
    ("POST", "/api/document-collections", "Create document collection"),
    ("POST", "/api/document-collections/update", "Update document collection"),
    ("POST", "/api/document-collections/delete", "Delete document collection"),
    ("POST", "/api/document-collections/items/add", "Add documents to collection"),
    ("POST", "/api/document-collections/items/remove", "Remove documents from collection"),
    ("GET", "/api/projects/retrieval-settings", "Get project retrieval settings"),
    ("POST", "/api/projects/retrieval-settings", "Save project retrieval settings"),
    ("GET", "/api/prompt-presets", "List prompt presets"),
    ("POST", "/api/prompt-presets", "Create prompt preset"),
    ("POST", "/api/prompt-presets/update", "Update prompt preset"),
    ("POST", "/api/prompt-presets/delete", "Delete prompt preset"),
    ("POST", "/api/prompt-presets/default", "Set default prompt preset"),
    ("GET", "/api/model-profiles", "List model profiles"),
    ("POST", "/api/model-profiles", "Create model profile"),
    ("POST", "/api/model-profiles/update", "Update model profile"),
    ("POST", "/api/model-profiles/delete", "Delete model profile"),
    ("POST", "/api/model-profiles/default", "Set default model profile"),
    ("POST", "/api/model-profiles/test", "Test model profile"),
    ("GET", "/api/import/preview", "Preview project import"),
    ("POST", "/api/import", "Import project directory"),
    ("POST", "/api/import/upload", "Import uploaded files"),
    ("POST", "/api/import/note", "Import plain text note"),
    ("POST", "/api/import/url", "Import URL excerpt"),
    ("POST", "/api/import/notion-zip", "Import Notion markdown zip"),
    ("POST", "/api/import/obsidian-vault", "Import Obsidian vault"),
    ("POST", "/api/import/github-repo", "Import GitHub repository"),
    ("GET", "/api/import/batches", "List import batches"),
    ("GET", "/api/import/batches/detail", "Get import batch detail"),
    ("POST", "/api/search", "Search project documents"),
    ("POST", "/api/search/debug", "Debug retrieval pipeline"),
    ("GET", "/api/retrieval/reviews", "List retrieval reviews"),
    ("POST", "/api/retrieval/reviews", "Create retrieval review"),
    ("GET", "/api/retrieval/reviews/detail", "Get retrieval review detail"),
    ("POST", "/api/retrieval/reviews/delete", "Delete retrieval review"),
    ("POST", "/api/answer", "Generate answer"),
    ("POST", "/api/answer/compare", "Compare answers from two model profiles"),
    ("GET", "/api/answer/stream", "Stream answer generation"),
    ("POST", "/api/answer/feedback", "Submit answer feedback"),
    ("GET", "/api/chat/sessions", "List chat sessions"),
    ("POST", "/api/chat/sessions", "Create chat session"),
    ("POST", "/api/chat/sessions/rename", "Rename chat session"),
    ("POST", "/api/chat/sessions/delete", "Delete chat session"),
    ("GET", "/api/chat/messages", "List chat messages"),
    ("POST", "/api/chat/messages/delete", "Delete chat message"),
    ("POST", "/api/chat/messages/clear", "Clear chat messages"),
    ("GET", "/api/agent/tools", "List read-only agent tools"),
    ("POST", "/api/agent/tools/run", "Run read-only agent tool"),
    ("GET", "/api/agent/tools/runs", "List agent tool runs"),
    ("GET", "/api/agent/tools/runs/detail", "Get agent tool run detail"),
    ("GET", "/api/settings/llm", "Get LLM settings"),
    ("POST", "/api/settings/llm", "Save LLM settings"),
    ("POST", "/api/settings/llm/test", "Test LLM settings"),
    ("GET", "/api/assessment/library", "Get assessment library summary"),
    ("POST", "/api/assessment/start", "Start assessment session"),
    ("POST", "/api/assessment/answer", "Submit assessment answer"),
]


def install_custom_openapi(app: FastAPI) -> None:
    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=OPENAPI_TITLE,
            version=OPENAPI_VERSION,
            summary="Local Web MVP API for Knowledge Island.",
            description="OpenAPI 3 schema for the local Knowledge Island Web MVP. Official contracts remain in docs/design/api-spec.md.",
            routes=[route for route in app.routes if getattr(route, "name", "") != "api_dispatch"],
        )
        schema["paths"] = _api_paths()
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi


def _api_paths() -> dict[str, dict[str, Any]]:
    paths: dict[str, dict[str, Any]] = {}
    for method, path, summary in WEB_MVP_API_OPERATIONS:
        method_key = method.lower()
        paths.setdefault(path, {})[method_key] = _operation(method_key, path, summary)
    return paths


def _operation(method: str, path: str, summary: str) -> dict[str, Any]:
    operation: dict[str, Any] = {
        "tags": [_tag_for_path(path)],
        "summary": summary,
        "operationId": _operation_id(method, path),
        "responses": {
            "200": _json_response("Successful response"),
            "400": _json_response("Invalid request"),
            "404": _json_response("Resource not found"),
        },
    }
    if method == "post":
        operation["requestBody"] = {
            "required": False,
            "content": {
                "application/json": {
                    "schema": {"type": "object", "additionalProperties": True},
                }
            },
        }
    if path == "/api/answer/stream":
        operation["responses"]["200"] = {
            "description": "Server-sent event stream",
            "content": {"text/event-stream": {"schema": {"type": "string"}}},
        }
    return operation


def _json_response(description: str) -> dict[str, Any]:
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": {"type": "object", "additionalProperties": True},
            }
        },
    }


def _tag_for_path(path: str) -> str:
    parts = path.strip("/").split("/")
    if len(parts) < 2:
        return "system"
    return parts[1].replace("-", " ").title()


def _operation_id(method: str, path: str) -> str:
    clean = path.strip("/").replace("/", "_").replace("-", "_")
    return f"{method}_{clean}"
