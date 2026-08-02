from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse


def request_id(request: Request) -> str:
    existing = getattr(request.state, "request_id", "")
    if existing:
        return str(existing)
    generated = str(uuid4())
    request.state.request_id = generated
    return generated


def success(
    request: Request,
    data: Any,
    *,
    status_code: int = 200,
) -> JSONResponse:
    identifier = request_id(request)
    return JSONResponse(
        status_code=status_code,
        content={"data": data, "meta": {"request_id": identifier}},
        headers={"X-Request-ID": identifier},
    )


def failure(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    identifier = request_id(request)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
            "request_id": identifier,
        },
        headers={"X-Request-ID": identifier},
    )
