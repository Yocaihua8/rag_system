from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.knowledge_island.llm import OpenAICompatibleChatClient
from backend.knowledge_island.models import Document, SearchHit
from backend.knowledge_island.storage import DEFAULT_RETRIEVAL_SETTINGS


def query_value(query: dict[str, list[str]], key: str) -> str:
    values = query.get(key, [])
    return values[0] if values else ""


def int_value(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def float_value(value: Any, default: float, minimum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, parsed)


def bool_value(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return default


def default_retrieval_settings(project_id: str) -> dict[str, object]:
    return {"project_id": project_id, **DEFAULT_RETRIEVAL_SETTINGS}


def project_retrieval_settings(store: Any, project_id: str) -> dict[str, object]:
    return store.get_project_retrieval_settings(project_id) or default_retrieval_settings(project_id)


def source_quality(hits: list[SearchHit]) -> dict[str, Any]:
    if not hits:
        return {
            "level": "none",
            "label": "没有找到可用来源",
            "reason": "当前问题没有命中已导入资料，回答不应视为确定结论。",
            "hit_count": 0,
            "max_score": 0.0,
        }
    max_score = max(hit.score for hit in hits)
    if len(hits) >= 2 or max_score > 1.0:
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


def test_llm_settings_with_client(client: OpenAICompatibleChatClient) -> dict[str, Any]:
    document = SearchHit(
        document=storeless_settings_test_document(),
        score=1.0,
        snippet="知识岛模型连接测试。",
    )
    answer = client.generate_answer("请回复：连接正常。", [document])
    return {"ok": True, "provider": client.provider, "message": answer[:200]}


def storeless_settings_test_document() -> Document:
    return Document(
        id="settings-test",
        project_id="settings",
        source_path=Path("settings-test.md"),
        relative_path="settings-test.md",
        content="知识岛模型连接测试。",
        checksum="settings-test",
        updated_at="",
    )
