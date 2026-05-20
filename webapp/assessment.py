from __future__ import annotations

import re
import uuid
from typing import Any

from webapp.models import Document
from webapp.storage import KnowledgeStore


def create_assessment_session(
    store: KnowledgeStore,
    project_id: str,
    question_count: int = 3,
) -> dict[str, Any]:
    documents = [doc for doc in store.list_documents(project_id) if doc.content.strip()]
    if not documents:
        raise ValueError("assessment requires imported documents")

    questions = [
        _question_from_document(document)
        for document in documents[: max(1, question_count)]
    ]
    return {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "questions": questions,
    }


def evaluate_assessment_answer(
    project_id: str,
    question: dict[str, Any],
    answer: str,
) -> dict[str, Any]:
    if question.get("project_id") != project_id:
        raise ValueError("question does not belong to project")
    normalized_answer = (answer or "").strip().lower()
    if not normalized_answer:
        raise ValueError("answer is required")

    expected_points = tuple(str(item) for item in question.get("expected_points", []) if str(item).strip())
    matched = tuple(point for point in expected_points if point.lower() in normalized_answer)
    missing = tuple(point for point in expected_points if point not in matched)
    score = round(len(matched) / max(1, len(expected_points)), 2)

    if score >= 0.75:
        status = "已掌握"
        feedback = "回答命中了主要依据，可以继续结合源码或文档做复述。"
    elif score >= 0.35:
        status = "基本理解"
        feedback = "回答覆盖了部分关键点，建议补充遗漏点后再确认。"
    else:
        status = "需要补充"
        feedback = "回答和来源片段的关键点匹配较少，建议先阅读对应文件。"

    return {
        "question_id": str(question.get("id", "")),
        "status": status,
        "score": score,
        "matched_points": list(matched),
        "missing_points": list(missing),
        "feedback": feedback,
        "source_path": str(question.get("source_path", "")),
    }


def _question_from_document(document: Document) -> dict[str, Any]:
    expected_points = _extract_expected_points(document.content, document.relative_path)
    return {
        "id": str(uuid.uuid4()),
        "project_id": document.project_id,
        "source_path": document.relative_path,
        "prompt": f"请说明 {document.relative_path} 里最核心的信息，并尽量引用文件中的关键词。",
        "expected_points": list(expected_points),
        "reference_snippet": document.content[:300].replace("\n", " ").strip(),
    }


def _extract_expected_points(content: str, relative_path: str) -> tuple[str, ...]:
    raw = f"{relative_path} {content[:1000]}".lower()
    candidates = re.findall(r"[a-z0-9_.#-]{2,}|[\u4e00-\u9fff]{2,}", raw)
    result: list[str] = []
    for token in candidates:
        if token in result:
            continue
        if token in {"md", "txt", "py", "js"}:
            continue
        result.append(token)
        if len(result) >= 5:
            break
    return tuple(result)
