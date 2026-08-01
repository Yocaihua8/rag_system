from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_vue_ollama_api_helper_uses_first_run_contracts():
    ollama_path = Path("frontend/src/api/ollama.js")
    assert ollama_path.exists(), "B-148 should add a Vue Ollama first-run API helper"
    ollama_js = _read(str(ollama_path))

    for marker in [
        'import { apiGet } from "./client.js";',
        "export async function getOllamaStatus()",
        'apiGet("/api/ollama/status")',
        "export async function pullOllamaModel({ model, handlers = {}, signal } = {})",
        'throw new Error("请选择要下载的模型")',
        'fetch("/api/ollama/pull"',
        'method: "POST"',
        '"Content-Type": "application/json"',
        "JSON.stringify({ model: cleanModel })",
        "response.body.getReader()",
        "new TextDecoder()",
        "handlers.onProgress?.(data)",
        "handlers.onDone?.(data)",
        "handlers.onError?.(data)",
        'throw new Error(data.error || "模型下载失败")',
    ]:
        assert marker in ollama_js
