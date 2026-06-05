from __future__ import annotations

from typing import Any

from backend.knowledge_island.agent_tools import AgentToolError, list_agent_tools, run_agent_tool
from backend.knowledge_island.api_support import query_value
from backend.knowledge_island.models import ApiResponse
from backend.knowledge_island.storage import KnowledgeStore


def handle_agent_route(
    store: KnowledgeStore,
    method: str,
    path: str,
    query: dict[str, list[str]],
    payload: dict[str, Any],
) -> ApiResponse | None:
    if method == "GET" and path == "/api/agent/tools":
        return ApiResponse(200, {"tools": list_agent_tools()})

    if method == "GET" and path == "/api/agent/tools/runs":
        project_id = query_value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        runs = [run.to_dict() for run in reversed(store.list_agent_tool_runs(project_id))]
        return ApiResponse(200, {"runs": runs})

    if method == "GET" and path == "/api/agent/tools/runs/detail":
        run_id = query_value(query, "run_id")
        if not run_id:
            return ApiResponse(400, {"error": "run_id is required"})
        run = store.get_agent_tool_run(run_id)
        if not run:
            return ApiResponse(404, {"error": "tool run not found"})
        return ApiResponse(200, {"run": run.to_dict()})

    if method == "POST" and path == "/api/agent/tools/run":
        project_id = str(payload.get("project_id", ""))
        tool_name = str(payload.get("tool", ""))
        arguments = payload.get("arguments") if isinstance(payload.get("arguments"), dict) else {}
        try:
            result, run = run_agent_tool(store, project_id, tool_name, arguments)
        except AgentToolError as exc:
            return ApiResponse(400, {"error": str(exc), "run": exc.run.to_dict()})
        except ValueError as exc:
            return ApiResponse(404, {"error": str(exc)})
        return ApiResponse(200, {"result": result, "run": run.to_dict()})

    return None
