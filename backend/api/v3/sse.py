from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import anyio
from fastapi import Request
from fastapi.responses import StreamingResponse
from pydantic import TypeAdapter

from backend.api.v3.models import AgentEvent
from backend.application.agent_service import ApplicationValidationError
from backend.storage.v3.errors import RecordNotFoundError


TERMINAL_RUN_STATUSES = {"completed", "failed", "cancelled"}
AGENT_EVENT_ADAPTER = TypeAdapter(AgentEvent)


def event_cursor(request: Request, after_sequence: int) -> int:
    raw_last_event_id = request.headers.get("last-event-id", "").strip()
    if not raw_last_event_id:
        return after_sequence
    try:
        last_event_id = int(raw_last_event_id)
    except ValueError as exc:
        raise ApplicationValidationError("Last-Event-ID must be an integer") from exc
    if last_event_id < 0:
        raise ApplicationValidationError("Last-Event-ID must not be negative")
    return max(after_sequence, last_event_id)


def stream_run_events(
    request: Request,
    *,
    store: Any,
    run_id: str,
    after_sequence: int,
    poll_interval_seconds: float = 0.1,
    heartbeat_seconds: float = 15.0,
) -> StreamingResponse:
    if store.get_run(run_id) is None:
        raise RecordNotFoundError("run not found")
    cursor = event_cursor(request, after_sequence)
    return StreamingResponse(
        _event_bytes(
            request,
            store=store,
            run_id=run_id,
            cursor=cursor,
            poll_interval_seconds=poll_interval_seconds,
            heartbeat_seconds=heartbeat_seconds,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _event_bytes(
    request: Request,
    *,
    store: Any,
    run_id: str,
    cursor: int,
    poll_interval_seconds: float,
    heartbeat_seconds: float,
) -> AsyncIterator[bytes]:
    current = cursor
    next_heartbeat = anyio.current_time() + heartbeat_seconds
    while True:
        if await request.is_disconnected():
            return
        events = await anyio.to_thread.run_sync(
            lambda: store.list_events(
                run_id,
                after_sequence=current,
                limit=500,
            )
        )
        for event in events:
            sequence = int(event["sequence"])
            if sequence <= current:
                continue
            current = sequence
            yield _format_event(event)

        run = await anyio.to_thread.run_sync(lambda: store.get_run(run_id))
        if run is None:
            return
        if str(run["status"]) in TERMINAL_RUN_STATUSES and not events:
            return

        now = anyio.current_time()
        if now >= next_heartbeat:
            yield f": keep-alive {current}\n\n".encode("utf-8")
            next_heartbeat = now + heartbeat_seconds
        await anyio.sleep(poll_interval_seconds)


def _format_event(event: dict[str, Any]) -> bytes:
    data = {
        "sequence": int(event["sequence"]),
        "event_type": str(event["event_type"]),
        "run_id": str(event["run_id"]),
        "step_id": event.get("step_id"),
        "event_schema_version": int(event.get("event_schema_version") or 1),
        "payload": dict(event.get("payload") or {}),
        "created_at": str(event["created_at"]),
    }
    validated = AGENT_EVENT_ADAPTER.validate_python(data)
    payload = json.dumps(
        validated.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return (
        f"id: {data['sequence']}\n"
        f"event: {data['event_type']}\n"
        f"data: {payload}\n\n"
    ).encode("utf-8")


__all__ = ["event_cursor", "stream_run_events"]
