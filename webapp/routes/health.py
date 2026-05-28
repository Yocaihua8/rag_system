from __future__ import annotations

from webapp.models import ApiResponse


def handle_health_route(method: str, path: str) -> ApiResponse | None:
    if method == "GET" and path == "/api/health":
        return ApiResponse(200, {"status": "ok"})
    return None
