from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from webapp.agent_tools import AgentToolError, list_agent_tools, run_agent_tool
from webapp.assessment import create_assessment_session, evaluate_assessment_answer
from webapp.answers import compose_answer
from webapp.ingestion import import_directory, preview_import_directory
from webapp.models import AgentToolRun, ApiResponse, SearchHit
from webapp.search import search_documents
from webapp.settings_api import get_llm_settings_body, save_llm_settings, test_llm_settings
from webapp.source_import import import_plain_text_note, import_url_excerpt
from webapp.storage import DEFAULT_RETRIEVAL_SETTINGS, KnowledgeStore
from webapp.upload_import import create_browser_upload_project, import_uploaded_files

ANSWER_FEEDBACK_RATINGS = {"useful", "not_useful", "source_wrong", "need_more_context"}
MAX_PROMPT_PRESET_TEXT_LENGTH = 4000
MAX_PROMPT_PRESET_FORMAT_LENGTH = 1000
PROMPT_PRESET_TEMPLATES = [
    {
        "name": "项目问答",
        "description": "回答项目是什么、怎么运行、接口在哪里等问题。",
        "system_prompt": "你是当前项目空间的问答助手。回答时优先说明依据文件；资料不足时直接指出缺口。",
        "answer_format": "先给结论，再列出依据来源和必要的下一步。",
    },
    {
        "name": "代码解释",
        "description": "解释文件、函数或模块职责。",
        "system_prompt": "你是代码解释助手。只解释已检索到的代码和文档片段，不臆测未提供的实现。",
        "answer_format": "按“结论 / 涉及文件 / 依据 / 注意点”组织回答。",
    },
    {
        "name": "学习复盘",
        "description": "把项目资料整理成学习提纲和检查点。",
        "system_prompt": "你是学习复盘助手。把来源资料转成可复习的知识点，不生成无来源结论。",
        "answer_format": "按“核心概念 / 自测问题 / 建议复习来源”组织回答。",
    },
]


def dispatch(
    store: KnowledgeStore,
    method: str,
    raw_path: str,
    payload: dict[str, Any] | None = None,
    llm_client: Any | None = None,
) -> ApiResponse:
    payload = payload or {}
    parsed = urlparse(raw_path)
    path = parsed.path
    query = parse_qs(parsed.query)

    if method == "GET" and path == "/api/health":
        return ApiResponse(200, {"status": "ok"})

    if method == "GET" and path == "/api/projects":
        return ApiResponse(200, {"projects": [project.to_dict() for project in store.list_projects()]})

    if method == "GET" and path == "/api/projects/summary":
        project_id = _value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        summary = store.get_project_summary(project_id)
        if not summary:
            return ApiResponse(404, {"error": "project not found"})
        return ApiResponse(200, {"summary": summary})

    if method == "GET" and path == "/api/projects/retrieval-settings":
        project_id = _value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        settings = store.get_project_retrieval_settings(project_id)
        if not settings:
            return ApiResponse(404, {"error": "project not found"})
        return ApiResponse(200, {"settings": settings})

    if method == "POST" and path == "/api/projects/retrieval-settings":
        project_id = str(payload.get("project_id", "")).strip()
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        current = store.get_project_retrieval_settings(project_id) or _default_retrieval_settings(project_id)
        settings = store.update_project_retrieval_settings(
            project_id,
            _int_value(payload.get("top_k"), int(current["top_k"]), minimum=1, maximum=20),
            _float_value(payload.get("min_score"), float(current["min_score"]), minimum=0.0),
            _bool_value(payload.get("use_keyword"), bool(current["use_keyword"])),
            _bool_value(payload.get("use_vector"), bool(current["use_vector"])),
        )
        return ApiResponse(200, {"settings": settings})

    if method == "GET" and path == "/api/prompt-presets":
        project_id = _value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        return ApiResponse(
            200,
            {
                "presets": [preset.to_dict() for preset in store.list_prompt_presets(project_id)],
                "default_preset_id": store.get_default_prompt_preset_id(project_id) or "",
                "templates": PROMPT_PRESET_TEMPLATES,
            },
        )

    if method == "POST" and path == "/api/prompt-presets":
        project_id = str(payload.get("project_id", "")).strip()
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        error = _prompt_preset_validation_error(payload)
        if error:
            return ApiResponse(400, {"error": error})
        preset = store.create_prompt_preset(
            project_id,
            str(payload.get("name", "")),
            str(payload.get("description", "")),
            str(payload.get("system_prompt", "")),
            str(payload.get("answer_format", "")),
        )
        return ApiResponse(200, {"preset": preset.to_dict()})

    if method == "POST" and path == "/api/prompt-presets/update":
        preset_id = str(payload.get("preset_id", "")).strip()
        if not preset_id:
            return ApiResponse(400, {"error": "preset_id is required"})
        if not store.get_prompt_preset(preset_id):
            return ApiResponse(404, {"error": "prompt preset not found"})
        error = _prompt_preset_validation_error(payload)
        if error:
            return ApiResponse(400, {"error": error})
        preset = store.update_prompt_preset(
            preset_id,
            str(payload.get("name", "")),
            str(payload.get("description", "")),
            str(payload.get("system_prompt", "")),
            str(payload.get("answer_format", "")),
        )
        if not preset:
            return ApiResponse(404, {"error": "prompt preset not found"})
        return ApiResponse(200, {"preset": preset.to_dict()})

    if method == "POST" and path == "/api/prompt-presets/delete":
        preset_id = str(payload.get("preset_id", "")).strip()
        if not preset_id:
            return ApiResponse(400, {"error": "preset_id is required"})
        preset = store.delete_prompt_preset(preset_id)
        if not preset:
            return ApiResponse(404, {"error": "prompt preset not found"})
        presets = [entry.to_dict() for entry in store.list_prompt_presets(preset.project_id)]
        return ApiResponse(200, {"deleted": True, "presets": presets})

    if method == "POST" and path == "/api/prompt-presets/default":
        project_id = str(payload.get("project_id", "")).strip()
        preset_id = str(payload.get("preset_id", "")).strip()
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        if preset_id:
            preset = store.get_prompt_preset(preset_id)
            if not preset or preset.project_id != project_id:
                return ApiResponse(404, {"error": "prompt preset not found"})
        default_id = store.set_default_prompt_preset(project_id, preset_id)
        return ApiResponse(200, {"default_preset_id": default_id or ""})

    if method == "GET" and path == "/api/export/project":
        project_id = _value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        project = store.get_project(project_id)
        if not project:
            return ApiResponse(404, {"error": "project not found"})
        return ApiResponse(200, {"export": _project_export_body(store, project_id)})

    if method == "GET" and path == "/api/agent/tools":
        return ApiResponse(200, {"tools": list_agent_tools()})

    if method == "GET" and path == "/api/agent/tools/runs":
        project_id = _value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        runs = [run.to_dict() for run in reversed(store.list_agent_tool_runs(project_id))]
        return ApiResponse(200, {"runs": runs})

    if method == "GET" and path == "/api/agent/tools/runs/detail":
        run_id = _value(query, "run_id")
        if not run_id:
            return ApiResponse(400, {"error": "run_id is required"})
        run = store.get_agent_tool_run(run_id)
        if not run:
            return ApiResponse(404, {"error": "tool run not found"})
        return ApiResponse(200, {"run": run.to_dict()})

    if method == "POST" and path == "/api/projects":
        root = Path(str(payload.get("path", ""))).expanduser()
        if not root.exists() or not root.is_dir():
            return ApiResponse(400, {"error": "path must be an existing directory"})
        project = store.create_project(str(payload.get("name", "")), root)
        return ApiResponse(201, {"project": project.to_dict()})

    if method == "POST" and path == "/api/projects/rename":
        project_id = str(payload.get("project_id", ""))
        name = str(payload.get("name", "")).strip()
        if not name:
            return ApiResponse(400, {"error": "name is required"})
        project = store.rename_project(project_id, name)
        if not project:
            return ApiResponse(404, {"error": "project not found"})
        return ApiResponse(200, {"project": project.to_dict()})

    if method == "POST" and path == "/api/projects/delete":
        project_id = str(payload.get("project_id", ""))
        if not store.delete_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        return ApiResponse(200, {"deleted": True})

    if method == "GET" and path == "/api/settings/llm":
        return ApiResponse(200, get_llm_settings_body())

    if method == "POST" and path == "/api/settings/llm":
        return ApiResponse(200, save_llm_settings(payload))

    if method == "POST" and path == "/api/settings/llm/test":
        try:
            return ApiResponse(200, test_llm_settings())
        except RuntimeError as exc:
            return ApiResponse(400, {"error": str(exc)})

    if method == "GET" and path == "/api/documents":
        project_id = _value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        documents = [doc.to_dict() for doc in store.list_documents(project_id)]
        return ApiResponse(200, {"documents": documents})

    if method == "GET" and path == "/api/chat/messages":
        project_id = _value(query, "project_id")
        session_id = _value(query, "session_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        if session_id and not _chat_session_belongs_to_project(store, session_id, project_id):
            return ApiResponse(404, {"error": "chat session not found"})
        messages = [message.to_dict() for message in store.list_chat_messages(project_id, session_id)]
        return ApiResponse(200, {"messages": messages})

    if method == "GET" and path == "/api/chat/sessions":
        project_id = _value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        sessions = [session.to_dict() for session in store.list_chat_sessions(project_id)]
        return ApiResponse(200, {"sessions": sessions})

    if method == "POST" and path == "/api/chat/sessions":
        project_id = str(payload.get("project_id", "")).strip()
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        session = store.create_chat_session(project_id, str(payload.get("title", "")))
        return ApiResponse(200, {"session": session.to_dict()})

    if method == "POST" and path == "/api/chat/sessions/rename":
        session_id = str(payload.get("session_id", "")).strip()
        title = str(payload.get("title", "")).strip()
        if not session_id:
            return ApiResponse(400, {"error": "session_id is required"})
        if not title:
            return ApiResponse(400, {"error": "title is required"})
        session = store.rename_chat_session(session_id, title)
        if not session:
            return ApiResponse(404, {"error": "chat session not found"})
        return ApiResponse(200, {"session": session.to_dict()})

    if method == "POST" and path == "/api/chat/sessions/delete":
        session_id = str(payload.get("session_id", "")).strip()
        if not session_id:
            return ApiResponse(400, {"error": "session_id is required"})
        session = store.delete_chat_session(session_id)
        if not session:
            return ApiResponse(404, {"error": "chat session not found"})
        sessions = [entry.to_dict() for entry in store.list_chat_sessions(session.project_id)]
        return ApiResponse(200, {"deleted": True, "sessions": sessions})

    if method == "POST" and path == "/api/chat/messages/delete":
        message_id = str(payload.get("message_id", "")).strip()
        if not message_id:
            return ApiResponse(400, {"error": "message_id is required"})
        message = store.delete_chat_message(message_id)
        if not message:
            return ApiResponse(404, {"error": "chat message not found"})
        messages = [entry.to_dict() for entry in store.list_chat_messages(message.project_id, message.session_id)]
        return ApiResponse(200, {"deleted": True, "messages": messages})

    if method == "POST" and path == "/api/chat/messages/clear":
        project_id = str(payload.get("project_id", "")).strip()
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        deleted = store.clear_chat_messages(project_id)
        return ApiResponse(200, {"deleted": deleted, "messages": []})

    if method == "POST" and path == "/api/answer/feedback":
        project_id = str(payload.get("project_id", "")).strip()
        message_id = str(payload.get("message_id", "")).strip()
        rating = str(payload.get("rating", "")).strip()
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not message_id:
            return ApiResponse(400, {"error": "message_id is required"})
        if rating not in ANSWER_FEEDBACK_RATINGS:
            return ApiResponse(400, {"error": "rating is invalid"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        message = store.get_chat_message(message_id)
        if not message or message.project_id != project_id:
            return ApiResponse(404, {"error": "chat message not found"})
        feedback = store.create_answer_feedback(
            project_id=project_id,
            message_id=message_id,
            rating=rating,
            note=str(payload.get("note", "")),
        )
        return ApiResponse(200, {"feedback": feedback.to_dict()})

    if method == "GET" and path == "/api/document":
        document_id = _value(query, "document_id")
        if not document_id:
            return ApiResponse(400, {"error": "document_id is required"})
        document = store.get_document(document_id)
        if not document:
            return ApiResponse(404, {"error": "document not found"})
        return ApiResponse(200, {"document": document.to_dict(include_content=True)})

    if method == "POST" and path == "/api/documents/delete":
        document_id = str(payload.get("document_id", ""))
        document = store.delete_document(document_id)
        if not document:
            return ApiResponse(404, {"error": "document not found"})
        documents = [doc.to_dict() for doc in store.list_documents(document.project_id)]
        return ApiResponse(200, {"deleted": True, "documents": documents})

    if method == "POST" and path == "/api/import":
        project_id = str(payload.get("project_id", ""))
        project = store.get_project(project_id)
        if not project:
            return ApiResponse(404, {"error": "project not found"})
        if not project.root_path.exists() or not project.root_path.is_dir():
            return ApiResponse(400, {"error": "project root path does not exist"})
        result = import_directory(store, project.id, project.root_path)
        documents = [doc.to_dict() for doc in store.list_documents(project.id)]
        return ApiResponse(200, {"result": result.to_dict(), "documents": documents})

    if method == "GET" and path == "/api/import/preview":
        project_id = _value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        project = store.get_project(project_id)
        if not project:
            return ApiResponse(404, {"error": "project not found"})
        if not project.root_path.exists() or not project.root_path.is_dir():
            return ApiResponse(400, {"error": "project root path does not exist"})
        preview = preview_import_directory(store, project.id, project.root_path)
        return ApiResponse(200, {"preview": preview})

    if method == "POST" and path == "/api/import/upload":
        files = payload.get("files")
        if not isinstance(files, list):
            return ApiResponse(400, {"error": "files is required"})
        project_id = str(payload.get("project_id", ""))
        project = store.get_project(project_id) if project_id else None
        if project_id and not project:
            return ApiResponse(404, {"error": "project not found"})
        if not project:
            project = create_browser_upload_project(store, str(payload.get("project_name", "")))
        result = import_uploaded_files(store, files, project)
        documents = [doc.to_dict() for doc in store.list_documents(project.id)]
        return ApiResponse(
            200,
            {
                "project": project.to_dict(),
                "result": result.to_dict(),
                "documents": documents,
            },
        )

    if method == "POST" and path == "/api/import/note":
        project_id = str(payload.get("project_id", ""))
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        try:
            write_result, result = import_plain_text_note(
                store,
                project_id,
                payload.get("title", ""),
                payload.get("content", ""),
            )
        except ValueError as exc:
            return ApiResponse(400, {"error": str(exc)})
        documents = [doc.to_dict() for doc in store.list_documents(project_id)]
        return ApiResponse(
            200,
            {
                "result": result.to_dict(),
                "document": write_result.document.to_dict(),
                "documents": documents,
            },
        )

    if method == "POST" and path == "/api/import/url":
        project_id = str(payload.get("project_id", ""))
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        try:
            write_result, result = import_url_excerpt(
                store,
                project_id,
                payload.get("url", ""),
                payload.get("title", ""),
                payload.get("content", ""),
            )
        except ValueError as exc:
            return ApiResponse(400, {"error": str(exc)})
        documents = [doc.to_dict() for doc in store.list_documents(project_id)]
        return ApiResponse(
            200,
            {
                "result": result.to_dict(),
                "document": write_result.document.to_dict(include_content=True),
                "documents": documents,
            },
        )

    if method == "POST" and path == "/api/search":
        project_id = str(payload.get("project_id", ""))
        query_text = str(payload.get("query", ""))
        hits = search_documents(store, project_id, query_text)
        return ApiResponse(200, {"hits": [hit.to_dict() for hit in hits if hit.score > 0]})

    if method == "POST" and path == "/api/search/debug":
        project_id = str(payload.get("project_id", ""))
        query_text = str(payload.get("query", ""))
        settings = _project_retrieval_settings(store, project_id)
        top_k = _int_value(payload.get("top_k"), int(settings["top_k"]), minimum=1, maximum=20)
        min_score = _float_value(payload.get("min_score"), float(settings["min_score"]), minimum=0.0)
        use_keyword = _bool_value(payload.get("use_keyword"), bool(settings["use_keyword"]))
        use_vector = _bool_value(payload.get("use_vector"), bool(settings["use_vector"]))
        hits = search_documents(
            store,
            project_id,
            query_text,
            limit=top_k,
            use_keyword=use_keyword,
            use_vector=use_vector,
        )
        useful_hits = [hit for hit in hits if hit.score >= min_score and hit.score > 0]
        vector_records = store.list_chunk_vector_records(project_id)
        return ApiResponse(
            200,
            {
                "hits": [hit.to_dict() for hit in useful_hits],
                "debug": {
                    "query": query_text,
                    "document_count": len(store.list_documents(project_id)),
                    "chunk_count": len(store.list_chunks(project_id)),
                    "vector_available": bool(vector_records),
                    "parameters": {
                        "top_k": top_k,
                        "min_score": min_score,
                        "use_keyword": use_keyword,
                        "use_vector": use_vector,
                    },
                    "quality": _source_quality(useful_hits),
                    "context_preview": [hit.to_dict() for hit in useful_hits[:top_k]],
                },
            },
        )

    if method == "GET" and path == "/api/retrieval/reviews":
        project_id = _value(query, "project_id")
        if not project_id:
            return ApiResponse(400, {"error": "project_id is required"})
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        reviews = [review.to_dict() for review in store.list_retrieval_reviews(project_id)]
        return ApiResponse(200, {"reviews": reviews})

    if method == "GET" and path == "/api/retrieval/reviews/detail":
        review_id = _value(query, "review_id")
        if not review_id:
            return ApiResponse(400, {"error": "review_id is required"})
        review = store.get_retrieval_review(review_id)
        if not review:
            return ApiResponse(404, {"error": "retrieval review not found"})
        return ApiResponse(200, {"review": review.to_dict()})

    if method == "POST" and path == "/api/retrieval/reviews":
        project_id = str(payload.get("project_id", ""))
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        query_text = str(payload.get("query", "")).strip()
        if not query_text:
            return ApiResponse(400, {"error": "query is required"})
        top_k = _int_value(payload.get("top_k"), 5, minimum=1, maximum=20)
        min_score = _float_value(payload.get("min_score"), 0.0, minimum=0.0)
        use_keyword = _bool_value(payload.get("use_keyword"), True)
        use_vector = _bool_value(payload.get("use_vector"), True)
        hits = search_documents(
            store,
            project_id,
            query_text,
            limit=top_k,
            use_keyword=use_keyword,
            use_vector=use_vector,
        )
        useful_hits = [hit for hit in hits if hit.score >= min_score and hit.score > 0]
        review = store.create_retrieval_review(
            project_id=project_id,
            query=query_text,
            parameters={
                "top_k": top_k,
                "min_score": min_score,
                "use_keyword": use_keyword,
                "use_vector": use_vector,
            },
            hits=[hit.to_dict() for hit in useful_hits],
            source_quality=_source_quality(useful_hits),
            note=str(payload.get("note", "")),
        )
        return ApiResponse(200, {"review": review.to_dict()})

    if method == "POST" and path == "/api/retrieval/reviews/delete":
        review_id = str(payload.get("review_id", "")).strip()
        if not review_id:
            return ApiResponse(400, {"error": "review_id is required"})
        review = store.delete_retrieval_review(review_id)
        if not review:
            return ApiResponse(404, {"error": "retrieval review not found"})
        reviews = [entry.to_dict() for entry in store.list_retrieval_reviews(review.project_id)]
        return ApiResponse(200, {"deleted": True, "reviews": reviews})

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

    if method == "POST" and path == "/api/answer":
        started_at = time.perf_counter()
        project_id = str(payload.get("project_id", ""))
        question = str(payload.get("question", ""))
        session_id = str(payload.get("session_id", "")).strip()
        if session_id and not _chat_session_belongs_to_project(store, session_id, project_id):
            return ApiResponse(404, {"error": "chat session not found"})
        retrieval_settings = _project_retrieval_settings(store, project_id)
        hits = search_documents(
            store,
            project_id,
            question,
            limit=int(retrieval_settings["top_k"]),
            use_keyword=bool(retrieval_settings["use_keyword"]),
            use_vector=bool(retrieval_settings["use_vector"]),
        )
        tool_context_run = None
        tool_context_hits = []
        tool_run_id = str(payload.get("tool_run_id", "")).strip()
        if tool_run_id:
            tool_context_run = store.get_agent_tool_run(tool_run_id)
            if not _is_usable_source_tool_context(tool_context_run, project_id):
                return ApiResponse(400, {"error": "tool context is not available"})
            tool_context_hits = _hits_from_tool_context(store, tool_context_run)
        min_score = float(retrieval_settings["min_score"])
        useful_hits = _dedupe_hits([hit for hit in hits if hit.score >= min_score and hit.score > 0] + tool_context_hits)
        project = store.get_project(project_id)
        history_messages = store.list_chat_messages(project_id, session_id)[-3:] if project else []
        prompt_preset = store.get_default_prompt_preset(project_id) if project else None
        answer_result = compose_answer(
            question,
            useful_hits,
            llm_client=llm_client,
            history_messages=history_messages,
            prompt_preset=prompt_preset,
        )
        sources = [hit.to_dict() for hit in useful_hits[:5]]
        message = None
        if project:
            message = store.create_chat_message(
                project_id=project_id,
                question=question,
                answer=answer_result.answer,
                mode=answer_result.mode,
                provider=answer_result.provider,
                warning=answer_result.warning,
                sources=sources,
                session_id=session_id,
            )
        body = {
            "answer": answer_result.answer,
            "sources": sources,
            "mode": answer_result.mode,
            "provider": answer_result.provider,
            "source_quality": _source_quality(useful_hits),
            "observability": _answer_observability(
                useful_hits,
                retrieval_settings,
                answer_result.mode,
                answer_result.provider,
                started_at,
            ),
        }
        if message:
            body["message"] = message.to_dict()
        if answer_result.warning:
            body["warning"] = answer_result.warning
        if answer_result.tool_suggestion:
            body["tool_suggestion"] = answer_result.tool_suggestion
        if tool_context_run:
            body["tool_context"] = {
                "tool_run_id": tool_context_run.id,
                "query": str(tool_context_run.result.get("query", "")),
                "hit_count": len(tool_context_hits),
            }
        return ApiResponse(200, body)

    if method == "POST" and path == "/api/assessment/start":
        project_id = str(payload.get("project_id", ""))
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        try:
            session = create_assessment_session(store, project_id)
        except ValueError as exc:
            return ApiResponse(400, {"error": str(exc)})
        return ApiResponse(200, {"session": session})

    if method == "POST" and path == "/api/assessment/answer":
        project_id = str(payload.get("project_id", ""))
        if not store.get_project(project_id):
            return ApiResponse(404, {"error": "project not found"})
        try:
            result = evaluate_assessment_answer(
                project_id=project_id,
                question=dict(payload.get("question") or {}),
                answer=str(payload.get("answer", "")),
            )
        except ValueError as exc:
            return ApiResponse(400, {"error": str(exc)})
        return ApiResponse(
            200,
            {"result": result},
        )

    return ApiResponse(404, {"error": "not found"})


def _value(query: dict[str, list[str]], key: str) -> str:
    values = query.get(key, [])
    return values[0] if values else ""


def _int_value(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _float_value(value: Any, default: float, minimum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, parsed)


def _bool_value(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return default


def _prompt_preset_validation_error(payload: dict[str, Any]) -> str:
    name = str(payload.get("name", "")).strip()
    system_prompt = str(payload.get("system_prompt", "")).strip()
    answer_format = str(payload.get("answer_format", "")).strip()
    if not name:
        return "name is required"
    if not system_prompt:
        return "system_prompt is required"
    if len(system_prompt) > MAX_PROMPT_PRESET_TEXT_LENGTH:
        return "system_prompt is too long"
    if len(answer_format) > MAX_PROMPT_PRESET_FORMAT_LENGTH:
        return "answer_format is too long"
    return ""


def _default_retrieval_settings(project_id: str) -> dict[str, object]:
    return {"project_id": project_id, **DEFAULT_RETRIEVAL_SETTINGS}


def _project_retrieval_settings(store: KnowledgeStore, project_id: str) -> dict[str, object]:
    return store.get_project_retrieval_settings(project_id) or _default_retrieval_settings(project_id)


def _chat_session_belongs_to_project(store: KnowledgeStore, session_id: str, project_id: str) -> bool:
    session = store.get_chat_session(session_id)
    return bool(session and session.project_id == project_id)


def _source_quality(hits: list[SearchHit]) -> dict[str, Any]:
    if not hits:
        return {
            "level": "none",
            "label": "没有找到可用来源",
            "reason": "当前问题没有命中已导入资料，回答不应视为确定结论。",
            "hit_count": 0,
            "max_score": 0.0,
        }
    max_score = max(hit.score for hit in hits)
    if len(hits) >= 2 or max_score >= 2.0:
        return {
            "level": "good",
            "label": "来源较充分",
            "reason": "当前回答有可追溯来源支撑。",
            "hit_count": len(hits),
            "max_score": max_score,
        }
    return {
        "level": "weak",
        "label": "来源偏少",
        "reason": "当前命中来源较少，建议补充资料或扩大检索词。",
        "hit_count": len(hits),
        "max_score": max_score,
    }


def _answer_observability(
    hits: list[SearchHit],
    retrieval_settings: dict[str, object],
    mode: str,
    provider: str,
    started_at: float,
) -> dict[str, Any]:
    return {
        "retrieval": {
            "top_k": int(retrieval_settings["top_k"]),
            "min_score": float(retrieval_settings["min_score"]),
            "use_keyword": bool(retrieval_settings["use_keyword"]),
            "use_vector": bool(retrieval_settings["use_vector"]),
            "hit_count": len(hits),
        },
        "model": {
            "mode": mode,
            "provider": provider,
        },
        "elapsed_ms": max(0, round((time.perf_counter() - started_at) * 1000)),
    }


def _project_export_body(store: KnowledgeStore, project_id: str) -> dict[str, Any]:
    project = store.get_project(project_id)
    documents = [
        {
            "id": document.id,
            "relative_path": document.relative_path,
            "source_path": str(document.source_path),
            "checksum": document.checksum,
            "updated_at": document.updated_at,
        }
        for document in store.list_documents(project_id)
    ]
    settings = get_llm_settings_body()["settings"]
    return {
        "version": 1,
        "project": project.to_dict() if project else {},
        "documents": documents,
        "chat_messages": [message.to_dict() for message in store.list_all_chat_messages(project_id)],
        "settings_summary": {
            "provider": settings.get("provider", ""),
            "api_base": settings.get("api_base", ""),
            "model": settings.get("model", ""),
            "key_configured": bool(settings.get("has_api_key")),
        },
    }


def _is_usable_source_tool_context(run: AgentToolRun | None, project_id: str) -> bool:
    return bool(
        run
        and run.project_id == project_id
        and run.tool_name == "search_sources"
        and run.status == "success"
        and isinstance(run.result.get("hits"), list)
    )


def _hits_from_tool_context(store: KnowledgeStore, run: AgentToolRun) -> list[SearchHit]:
    hits = []
    for item in run.result.get("hits", []):
        if not isinstance(item, dict):
            continue
        document = store.get_document(str(item.get("document_id", "")))
        snippet = str(item.get("snippet", "")).strip()
        if document and snippet:
            hits.append(
                SearchHit(
                    document=document,
                    score=float(item.get("score", 1.0) or 1.0),
                    snippet=snippet,
                    keyword_score=float(item.get("keyword_score", 0.0) or 0.0),
                    vector_score=float(item.get("vector_score", 0.0) or 0.0),
                    retrieval=str(item.get("retrieval", "tool_context")),
                    vector_provider=str(item.get("vector_provider", "local")),
                    vector_model=str(item.get("vector_model", "hashing-96")),
                )
            )
    return hits


def _dedupe_hits(hits: list[SearchHit]) -> list[SearchHit]:
    seen = set()
    unique_hits = []
    for hit in hits:
        key = (hit.document.id, hit.snippet)
        if key in seen:
            continue
        seen.add(key)
        unique_hits.append(hit)
    return unique_hits
