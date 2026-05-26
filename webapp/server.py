from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from webapp.api import answer_stream_events, dispatch
from webapp.config import DEFAULT_HOST, DEFAULT_PORT, default_db_path
from webapp.storage import KnowledgeStore


STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app(db_path: Path | None = None, store: KnowledgeStore | None = None) -> FastAPI:
    knowledge_store = store or KnowledgeStore(db_path or default_db_path())
    app = FastAPI(title="Knowledge Island", docs_url="/docs", redoc_url="/redoc")
    app.state.knowledge_store = knowledge_store

    @app.get("/api/answer/stream")
    async def answer_stream(request: Request) -> StreamingResponse:
        return StreamingResponse(
            _answer_stream_bytes(knowledge_store, _raw_path(request)),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    @app.api_route("/api/{path:path}", methods=["GET", "POST"])
    async def api_dispatch(request: Request) -> JSONResponse:
        response = dispatch(
            knowledge_store,
            request.method,
            _raw_path(request),
            await _json_payload(request),
        )
        return JSONResponse(status_code=response.status, content=response.body)

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


app = create_app()


def run_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    db_path: Path | None = None,
) -> int:
    target_app = create_app(db_path=db_path)
    print(f"Knowledge Island Web is running at http://{host}:{port}")
    uvicorn.run(target_app, host=host, port=port)
    return 0


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


def _format_sse_event(event: Any) -> bytes:
    data = json.dumps(event.data, ensure_ascii=False)
    return f"event: {event.event}\ndata: {data}\n\n".encode("utf-8")
