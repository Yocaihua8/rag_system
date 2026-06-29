from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from webapp.api import answer_stream_events, dispatch
from webapp.auth import AuthSettings, issue_jwt, load_auth_settings, validate_api_key, validate_jwt
from webapp.config import DEFAULT_HOST, DEFAULT_PORT, default_db_path
from webapp.openapi_schema import install_custom_openapi
from webapp.routes.ollama import ollama_pull_events, validate_ollama_pull_payload
from webapp.storage import KnowledgeStore


WEBAPP_DIR = Path(__file__).resolve().parent
STATIC_DIST_DIR = WEBAPP_DIR / "static_dist"
AUTHENTICATION_REQUIRED = {"error": "authentication required"}
INVALID_CREDENTIALS = {"error": "invalid credentials"}


def create_app(
    db_path: Path | None = None,
    store: KnowledgeStore | None = None,
    auth_settings: AuthSettings | None = None,
) -> FastAPI:
    knowledge_store = store or KnowledgeStore(db_path or default_db_path())
    auth_config = auth_settings or load_auth_settings()
    app = FastAPI(title="Knowledge Island", docs_url="/docs", redoc_url="/redoc")
    app.state.knowledge_store = knowledge_store
    app.state.auth_settings = auth_config

    @app.middleware("http")
    async def require_auth(request: Request, call_next):
        auth_error = _auth_error(auth_config, request)
        if auth_error == "missing":
            return _auth_error_response(AUTHENTICATION_REQUIRED)
        if auth_error == "invalid":
            return _auth_error_response(INVALID_CREDENTIALS)
        return await call_next(request)

    @app.get("/api/answer/stream")
    async def answer_stream(request: Request) -> StreamingResponse:
        return StreamingResponse(
            _answer_stream_bytes(knowledge_store, _raw_path(request)),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    @app.post("/api/ollama/pull", response_model=None)
    async def ollama_pull(request: Request) -> JSONResponse | StreamingResponse:
        payload = await _json_payload(request)
        error = validate_ollama_pull_payload(payload)
        if error:
            return JSONResponse(status_code=400, content={"error": error})
        return StreamingResponse(
            _ollama_pull_stream(str(payload.get("model", "")).strip()),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    @app.post("/api/auth/token")
    async def auth_token(request: Request) -> JSONResponse:
        if not auth_config.enabled:
            return JSONResponse(status_code=404, content={"error": "not found"})
        api_key = request.headers.get("x-api-key", "")
        if not api_key:
            return _auth_error_response(AUTHENTICATION_REQUIRED)
        if not validate_api_key(auth_config, api_key):
            return _auth_error_response(INVALID_CREDENTIALS)
        return JSONResponse(
            content={
                "access_token": issue_jwt(auth_config),
                "token_type": "bearer",
                "expires_in": auth_config.jwt_ttl_seconds,
            }
        )

    @app.api_route("/api/{path:path}", methods=["GET", "POST"])
    async def api_dispatch(request: Request) -> JSONResponse:
        response = await run_in_threadpool(
            dispatch,
            knowledge_store,
            request.method,
            _raw_path(request),
            await _json_payload(request),
        )
        return JSONResponse(status_code=response.status, content=response.body)

    install_custom_openapi(app)
    app.mount("/", StaticFiles(directory=_frontend_static_dir(), html=True), name="static")
    return app


def run_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    db_path: Path | None = None,
) -> int:
    target_app = create_app(db_path=db_path)
    print(f"Knowledge Island Web is running at http://{host}:{port}")
    uvicorn.run(target_app, host=host, port=port)
    return 0


def _auth_error(settings: AuthSettings, request: Request) -> str | None:
    if not _requires_auth(settings, request.url.path):
        return None
    api_key = request.headers.get("x-api-key", "")
    if api_key:
        return None if validate_api_key(settings, api_key) else "invalid"
    authorization = request.headers.get("authorization", "")
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            return "invalid"
        return None if validate_jwt(settings, token.strip()) is not None else "invalid"
    return "missing"


def _requires_auth(settings: AuthSettings, path: str) -> bool:
    if not settings.enabled:
        return False
    if path in {"/api/health", "/api/auth/token"}:
        return False
    if path == "/docs" or path.startswith("/docs/"):
        return True
    if path == "/redoc" or path.startswith("/redoc/"):
        return True
    if path == "/openapi.json":
        return True
    return path.startswith("/api/")


def _auth_error_response(content: dict[str, str]) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=content,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _frontend_static_dir() -> Path:
    if not (STATIC_DIST_DIR / "index.html").exists():
        raise RuntimeError("Vue build output missing. Run `npm run build` before starting Knowledge Island.")
    return STATIC_DIST_DIR


app = create_app()


async def _json_payload(request: Request) -> dict[str, Any]:
    if request.method != "POST":
        return {}
    raw_body = await request.body()
    if not raw_body:
        return {}
    try:
        data = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _raw_path(request: Request) -> str:
    query = request.url.query
    if query:
        return f"{request.url.path}?{query}"
    return request.url.path


def _answer_stream_bytes(store: KnowledgeStore, raw_path: str) -> Iterable[bytes]:
    try:
        for event in answer_stream_events(store, raw_path):
            yield _format_sse_event(event)
    except (BrokenPipeError, ConnectionResetError):
        return


def _ollama_pull_stream(model: str) -> Iterable[bytes]:
    try:
        for event in ollama_pull_events(model):
            yield _format_sse_event(event)
    except (BrokenPipeError, ConnectionResetError):
        return


def _format_sse_event(event: Any) -> bytes:
    data = json.dumps(event.data, ensure_ascii=False)
    return f"event: {event.event}\ndata: {data}\n\n".encode("utf-8")
