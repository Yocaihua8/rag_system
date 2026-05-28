from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

from backend.webapp.answer_api import answer_body_from_result, prepare_answer_context
from backend.webapp.api_support import query_value, test_llm_settings_with_client
from backend.webapp.answers import compose_answer_stream
from backend.webapp.llm import OpenAICompatibleChatClient
from backend.webapp.models import ApiResponse, ApiStreamEvent
from backend.webapp.routes import dispatch_to_routes
from backend.webapp.storage import KnowledgeStore


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

    routed_response = dispatch_to_routes(store, method, path, query, payload, llm_client=llm_client)
    if routed_response is not None:
        return routed_response

    return ApiResponse(404, {"error": "not found"})


def answer_stream_events(
    store: KnowledgeStore,
    raw_path: str,
    llm_client: Any | None = None,
):
    parsed = urlparse(raw_path)
    query = parse_qs(parsed.query)
    payload: dict[str, Any] = {
        "project_id": query_value(query, "project_id"),
        "question": query_value(query, "question"),
        "session_id": query_value(query, "session_id"),
        "tool_run_id": query_value(query, "tool_run_id"),
    }
    context, error = prepare_answer_context(store, payload, llm_client)
    if error:
        yield ApiStreamEvent("answer_error", error.body)
        return

    stream = compose_answer_stream(
        str(context["question"]),
        context["useful_hits"],
        llm_client=context["answer_llm_client"],
        history_messages=context["history_messages"],
        prompt_preset=context["prompt_preset"],
    )
    while True:
        try:
            token = next(stream)
        except StopIteration as stopped:
            answer_result = stopped.value
            break
        if token:
            yield ApiStreamEvent("token", {"text": token})
    yield ApiStreamEvent("done", answer_body_from_result(store, context, answer_result))
