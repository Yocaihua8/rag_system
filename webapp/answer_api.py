from __future__ import annotations

import time
import sys
from typing import Any

from webapp.answers import compose_answer
from webapp.api_support import project_retrieval_settings, source_quality
from webapp.llm import OpenAICompatibleChatClient
from webapp.model_profiles import llm_config_from_profile
from webapp.models import AgentToolRun, ApiResponse, SearchHit
from webapp.search import search_documents
from webapp.storage import KnowledgeStore


def answer_response(
    store: KnowledgeStore,
    payload: dict[str, Any],
    llm_client: Any | None = None,
) -> ApiResponse:
    context, error = prepare_answer_context(store, payload, llm_client)
    if error:
        return error
    answer_result = compose_answer(
        str(context["question"]),
        context["useful_hits"],
        llm_client=context["answer_llm_client"],
        history_messages=context["history_messages"],
        prompt_preset=context["prompt_preset"],
    )
    return ApiResponse(200, answer_body_from_result(store, context, answer_result))


def prepare_answer_context(
    store: KnowledgeStore,
    payload: dict[str, Any],
    llm_client: Any | None,
) -> tuple[dict[str, Any], ApiResponse | None]:
    started_at = time.perf_counter()
    project_id = str(payload.get("project_id", ""))
    question = str(payload.get("question", ""))
    session_id = str(payload.get("session_id", "")).strip()
    if session_id and not _chat_session_belongs_to_project(store, session_id, project_id):
        return {}, ApiResponse(404, {"error": "chat session not found"})
    retrieval_settings = project_retrieval_settings(store, project_id)
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
            return {}, ApiResponse(400, {"error": "tool context is not available"})
        tool_context_hits = _hits_from_tool_context(store, tool_context_run)
    min_score = float(retrieval_settings["min_score"])
    useful_hits = _dedupe_hits([hit for hit in hits if hit.score >= min_score and hit.score > 0] + tool_context_hits)
    project = store.get_project(project_id)
    return {
        "started_at": started_at,
        "project_id": project_id,
        "question": question,
        "session_id": session_id,
        "retrieval_settings": retrieval_settings,
        "useful_hits": useful_hits,
        "project": project,
        "history_messages": store.list_chat_messages(project_id, session_id)[-3:] if project else [],
        "prompt_preset": store.get_default_prompt_preset(project_id) if project else None,
        "answer_llm_client": llm_client if llm_client is not None else _default_model_profile_client(store),
        "tool_context_run": tool_context_run,
        "tool_context_hits": tool_context_hits,
    }, None


def answer_body_from_result(store: KnowledgeStore, context: dict[str, Any], answer_result: Any) -> dict[str, Any]:
    useful_hits = context["useful_hits"]
    sources = [hit.to_dict() for hit in useful_hits[:5]]
    message = None
    project = context["project"]
    if project:
        message = store.create_chat_message(
            project_id=str(context["project_id"]),
            question=str(context["question"]),
            answer=answer_result.answer,
            mode=answer_result.mode,
            provider=answer_result.provider,
            warning=answer_result.warning,
            sources=sources,
            session_id=str(context["session_id"]),
        )
    body = {
        "answer": answer_result.answer,
        "sources": sources,
        "mode": answer_result.mode,
        "provider": answer_result.provider,
        "source_quality": source_quality(useful_hits),
        "observability": _answer_observability(
            useful_hits,
            context["retrieval_settings"],
            answer_result.mode,
            answer_result.provider,
            float(context["started_at"]),
        ),
    }
    if message:
        body["message"] = message.to_dict()
    if answer_result.warning:
        body["warning"] = answer_result.warning
    if answer_result.tool_suggestion:
        body["tool_suggestion"] = answer_result.tool_suggestion
    tool_context_run = context["tool_context_run"]
    if tool_context_run:
        body["tool_context"] = {
            "tool_run_id": tool_context_run.id,
            "query": str(tool_context_run.result.get("query", "")),
            "hit_count": len(context["tool_context_hits"]),
        }
    return body


def _default_model_profile_client(store: KnowledgeStore) -> OpenAICompatibleChatClient | None:
    profile = store.get_default_model_profile()
    if not profile:
        return None
    client_class = _openai_compatible_chat_client_class()
    client = client_class(llm_config_from_profile(profile))
    return client if client.is_configured() else None


def _openai_compatible_chat_client_class():
    api_module = sys.modules.get("webapp.api")
    return getattr(api_module, "OpenAICompatibleChatClient", OpenAICompatibleChatClient)


def _chat_session_belongs_to_project(store: KnowledgeStore, session_id: str, project_id: str) -> bool:
    session = store.get_chat_session(session_id)
    return bool(session and session.project_id == project_id)


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
