from __future__ import annotations

from typing import Any

from webapp.search import search_documents
from webapp.storage import KnowledgeStore


READ_ONLY_TOOLS = [
    {
        "name": "project_overview",
        "title": "项目概览",
        "description": "读取当前项目的文档、分块、聊天记录和向量数量。",
        "read_only": True,
        "arguments": {},
    },
    {
        "name": "search_sources",
        "title": "检索来源",
        "description": "按查询词检索当前项目来源片段，返回可追溯命中。",
        "read_only": True,
        "arguments": {"query": "string"},
    },
]


def list_agent_tools() -> list[dict[str, Any]]:
    return [dict(tool) for tool in READ_ONLY_TOOLS]


def run_agent_tool(
    store: KnowledgeStore,
    project_id: str,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], Any]:
    arguments = arguments or {}
    project = store.get_project(project_id)
    if not project:
        raise ValueError("project not found")
    if tool_name == "project_overview":
        result = {
            "project_id": project.id,
            "project_name": project.name,
            "root_path": str(project.root_path),
            "root_exists": project.to_dict()["root_exists"],
            "document_count": len(store.list_documents(project.id)),
            "chunk_count": len(store.list_chunks(project.id)),
            "vector_count": store.count_chunk_vectors(project.id),
            "chat_message_count": len(store.list_chat_messages(project.id)),
        }
        run = store.create_agent_tool_run(
            project_id=project.id,
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            status="success",
        )
        return result, run

    if tool_name == "search_sources":
        query = str(arguments.get("query", "")).strip()
        if not query:
            run = store.create_agent_tool_run(
                project_id=project_id,
                tool_name=tool_name,
                arguments=arguments,
                result={},
                status="error",
                error="query is required",
            )
            raise AgentToolError("query is required", run)
        hits = [hit.to_dict() for hit in search_documents(store, project.id, query) if hit.score > 0][:5]
        result = {
            "project_id": project.id,
            "query": query,
            "hit_count": len(hits),
            "hits": hits,
        }
        run = store.create_agent_tool_run(
            project_id=project.id,
            tool_name=tool_name,
            arguments={"query": query},
            result=result,
            status="success",
        )
        return result, run

    if tool_name not in {tool["name"] for tool in READ_ONLY_TOOLS}:
        run = store.create_agent_tool_run(
            project_id=project_id,
            tool_name=tool_name,
            arguments=arguments,
            result={},
            status="error",
            error="unknown or disabled tool",
        )
        raise AgentToolError("unknown or disabled tool", run)


class AgentToolError(ValueError):
    def __init__(self, message: str, run: Any):
        super().__init__(message)
        self.run = run
