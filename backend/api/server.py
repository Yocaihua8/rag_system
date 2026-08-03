from __future__ import annotations

import hmac
import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Iterable

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool

from backend.api.dispatch import answer_stream_events, dispatch
from backend.api.auth import AuthSettings, issue_jwt, load_auth_settings, validate_api_key, validate_jwt
from backend.config.desktop import (
    DESKTOP_TOKEN_HEADER,
    DesktopRuntimeSettings,
    load_desktop_settings,
)
from backend.config.web import (
    CORS_ALLOWED_HEADERS,
    CORS_ALLOWED_METHODS,
    DEFAULT_HOST,
    DEFAULT_PORT,
    cors_origins,
    default_db_path,
)
from backend.config.settings import load_settings
from backend.api.openapi_schema import install_custom_openapi
from backend.api.v3.app import create_v3_app
from backend.config.v3 import V3RuntimeSettings, load_v3_settings
from backend.runtime.executor import AgentExecutor
from backend.routes.ollama import ollama_pull_events, validate_ollama_pull_payload
from backend.storage import KnowledgeStore
from backend.storage.v3 import AgentStore


AUTHENTICATION_REQUIRED = {"error": "authentication required"}
INVALID_CREDENTIALS = {"error": "invalid credentials"}
OBSIDIAN_SELF_AUTH_PATHS = {
    "/api/obsidian/pairing/complete",
    "/api/obsidian/connections/revoke",
    "/api/obsidian/sync/events",
    "/api/obsidian/publications/pending",
    "/api/obsidian/publications/result",
}


def create_app(
    db_path: Path | None = None,
    store: KnowledgeStore | None = None,
    auth_settings: AuthSettings | None = None,
    desktop_settings: DesktopRuntimeSettings | None = None,
    *,
    v3_db_path: Path | None = None,
    v3_store: AgentStore | None = None,
    v3_settings: V3RuntimeSettings | None = None,
    enable_v3: bool | None = None,
) -> FastAPI:
    runtime_settings = load_settings()
    knowledge_store = store or KnowledgeStore(
        db_path or default_db_path(),
        expected_generation="v2",
        chunk_size=runtime_settings.chunk_size,
        chunk_overlap=runtime_settings.chunk_overlap,
        retrieval_top_k=runtime_settings.retrieval_top_k,
        retriever_kind=runtime_settings.retriever_kind,
    )
    auth_config = auth_settings or load_auth_settings()
    desktop_config = desktop_settings or load_desktop_settings()
    v3_enabled = (
        enable_v3
        if enable_v3 is not None
        else (
            v3_store is not None
            or v3_db_path is not None
            or v3_settings is not None
            or (db_path is None and store is None)
        )
    )
    agent_store: AgentStore | None = None
    agent_executor: AgentExecutor | None = None
    v3_sub_app: FastAPI | None = None
    if v3_enabled:
        runtime_settings = v3_settings or load_v3_settings(
            {"KI_V3_DB_PATH": str(v3_db_path)} if v3_db_path else None
        )
        agent_store = v3_store or AgentStore(runtime_settings.db_path)
        agent_executor = AgentExecutor(agent_store, runtime_settings)
        v3_sub_app = create_v3_app(
            store=agent_store,
            executor=agent_executor,
            current_data_root=runtime_settings.data_root,
            legacy_data_root=knowledge_store.db_path.parent,
            backups_dir=runtime_settings.backups_dir,
            backup_retention=runtime_settings.backup_retention,
        )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if agent_store is None or agent_executor is None or v3_sub_app is None:
            yield
            return
        initialized = False
        try:
            info = await run_in_threadpool(agent_store.initialize)
            initialized = True
            v3_sub_app.state.database_info = info
            await agent_executor.start()
            yield
        finally:
            await agent_executor.stop()
            if initialized:
                await run_in_threadpool(agent_store.close)

    app = FastAPI(
        title="Knowledge Island",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    app.state.knowledge_store = knowledge_store
    app.state.auth_settings = auth_config
    app.state.desktop_settings = desktop_config
    app.state.v3_store = agent_store
    app.state.v3_executor = agent_executor

    @app.middleware("http")
    async def require_auth(request: Request, call_next):
        auth_error = _request_auth_error(auth_config, desktop_config, request)
        if auth_error == "missing":
            return _auth_error_response(
                AUTHENTICATION_REQUIRED,
                advertise_bearer=not desktop_config.enabled,
            )
        if auth_error == "invalid":
            return _auth_error_response(
                INVALID_CREDENTIALS,
                advertise_bearer=not desktop_config.enabled,
            )
        return await call_next(request)

    # CORS must wrap the authentication middleware so browser preflight requests
    # are answered before API authentication is evaluated.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(cors_origins()),
        allow_credentials=False,
        allow_methods=list(CORS_ALLOWED_METHODS),
        allow_headers=list(CORS_ALLOWED_HEADERS),
    )

    if v3_sub_app is not None:
        # Register the mount before the legacy catch-all dispatcher so /api/v3
        # is never interpreted as a v2 compatibility route.
        app.mount("/api/v3", v3_sub_app)

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
        if desktop_config.enabled or not auth_config.enabled:
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
            request_context={
                "authorization": request.headers.get("authorization", ""),
                "app_authenticated": (
                    "true"
                    if _app_authenticated(auth_config, request, desktop_config)
                    else "false"
                ),
            },
        )
        return JSONResponse(status_code=response.status, content=response.body)

    install_custom_openapi(app)
    return app


def run_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    db_path: Path | None = None,
) -> int:
    target_app = create_app(db_path=db_path)
    print(f"Knowledge Island API is running at http://{host}:{port}")
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


def _request_auth_error(
    auth_settings: AuthSettings,
    desktop_settings: DesktopRuntimeSettings,
    request: Request,
) -> str | None:
    if desktop_settings.enabled:
        return _desktop_auth_error(desktop_settings, request)
    return _auth_error(auth_settings, request)


def _desktop_auth_error(
    settings: DesktopRuntimeSettings,
    request: Request,
) -> str | None:
    if not _requires_desktop_auth(request.url.path):
        return None
    candidate = request.headers.get(DESKTOP_TOKEN_HEADER, "")
    if not candidate:
        return "missing"
    return None if hmac.compare_digest(settings.startup_token, candidate) else "invalid"


def _requires_desktop_auth(path: str) -> bool:
    if path in OBSIDIAN_SELF_AUTH_PATHS:
        return False
    if path == "/docs" or path.startswith("/docs/"):
        return True
    if path == "/redoc" or path.startswith("/redoc/"):
        return True
    if path == "/openapi.json":
        return True
    return path.startswith("/api/")


def _app_authenticated(
    settings: AuthSettings,
    request: Request,
    desktop_settings: DesktopRuntimeSettings | None = None,
) -> bool:
    if desktop_settings is not None and desktop_settings.enabled:
        return _desktop_auth_error(desktop_settings, request) is None
    if not settings.enabled:
        return True
    api_key = request.headers.get("x-api-key", "")
    if api_key:
        return validate_api_key(settings, api_key)
    authorization = request.headers.get("authorization", "")
    if not authorization:
        return False
    scheme, _, token = authorization.partition(" ")
    return (
        scheme.lower() == "bearer"
        and bool(token.strip())
        and validate_jwt(settings, token.strip()) is not None
    )


def _requires_auth(settings: AuthSettings, path: str) -> bool:
    if not settings.enabled:
        return False
    if path in {
        "/api/health",
        "/api/v3/health",
        "/api/auth/token",
        *OBSIDIAN_SELF_AUTH_PATHS,
    }:
        return False
    if path == "/docs" or path.startswith("/docs/"):
        return True
    if path == "/redoc" or path.startswith("/redoc/"):
        return True
    if path == "/openapi.json":
        return True
    return path.startswith("/api/")


def _auth_error_response(
    content: dict[str, str],
    *,
    advertise_bearer: bool = True,
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content=content,
        headers={"WWW-Authenticate": "Bearer"} if advertise_bearer else None,
    )


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
