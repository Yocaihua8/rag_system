from __future__ import annotations

import re
import uuid
from typing import Any

from backend.webapp.models import Document
from backend.webapp.storage import KnowledgeStore


def create_assessment_session(
    store: KnowledgeStore,
    project_id: str,
    question_count: int = 3,
) -> dict[str, Any]:
    documents = [doc for doc in store.list_documents(project_id) if doc.content.strip()]
    if not documents:
        raise ValueError("assessment requires imported documents")

    target_count = max(1, question_count)
    questions = []
    for document in documents:
        for question in _questions_from_document(document):
            if len(questions) >= target_count:
                break
            question_type = str(question["question_type"])
            knowledge_point = str(question["knowledge_point"])
            persisted = store.create_assessment_question(
                project_id=project_id,
                source_path=str(question["source_path"]),
                prompt=str(question["prompt"]),
                expected_points=[str(item) for item in question["expected_points"]],
                reference_snippet=str(question["reference_snippet"]),
                question_type=question_type,
                knowledge_point=knowledge_point,
                question_id=str(question["id"]),
            )
            questions.append(persisted.to_dict())
        if len(questions) >= target_count:
            break

    if not questions:
        question = _concept_question_from_document(document=documents[0])
        persisted = store.create_assessment_question(
            project_id=project_id,
            source_path=str(question["source_path"]),
            prompt=str(question["prompt"]),
            expected_points=[str(item) for item in question["expected_points"]],
            reference_snippet=str(question["reference_snippet"]),
            question_type=str(question["question_type"]),
            knowledge_point=str(question["knowledge_point"]),
            question_id=str(question["id"]),
        )
        questions.append(persisted.to_dict())
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
    elif matched:
        status = "需要补充"
        feedback = "回答只命中了少量参考要点，建议围绕缺失要点补充来源依据。"
    else:
        status = "暂未掌握"
        feedback = "回答尚未命中参考要点，建议先阅读对应来源后再重新组织答案。"

    return {
        "question_id": str(question.get("id", "")),
        "question_type": str(question.get("question_type", "")),
        "knowledge_point": str(question.get("knowledge_point", "")),
        "status": status,
        "score": score,
        "matched_points": list(matched),
        "missing_points": list(missing),
        "feedback": feedback,
        "source_path": str(question.get("source_path", "")),
        "reference_snippet": str(question.get("reference_snippet", "")),
    }


def _questions_from_document(document: Document) -> list[dict[str, Any]]:
    knowledge_point = _knowledge_point_from_document(document)
    expected_points = _extract_expected_points(
        document.content,
        document.relative_path,
        (knowledge_point,),
    )
    reference_snippet = _reference_snippet(document.content)
    return [
        {
            "id": str(uuid.uuid4()),
            "project_id": document.project_id,
            "source_path": document.relative_path,
            "question_type": "concept",
            "knowledge_point": knowledge_point,
            "prompt": (
                f"概念理解：请说明“{knowledge_point}”主要解决什么问题，"
                f"并引用来源 {document.relative_path} 中的关键词。"
            ),
            "expected_points": list(expected_points),
            "reference_snippet": reference_snippet,
        },
        {
            "id": str(uuid.uuid4()),
            "project_id": document.project_id,
            "source_path": document.relative_path,
            "question_type": "flow",
            "knowledge_point": knowledge_point,
            "prompt": (
                f"流程说明：请按步骤说明“{knowledge_point}”相关流程和关键产物，"
                f"依据来源 {document.relative_path}。"
            ),
            "expected_points": list(expected_points),
            "reference_snippet": reference_snippet,
        },
        {
            "id": str(uuid.uuid4()),
            "project_id": document.project_id,
            "source_path": document.relative_path,
            "question_type": "code_location",
            "knowledge_point": knowledge_point,
            "prompt": (
                f"代码定位：请指出“{knowledge_point}”主要可以从哪些文件、函数或配置中找到依据，"
                f"优先检查 {document.relative_path}。"
            ),
            "expected_points": list(_extract_expected_points(
                document.content,
                document.relative_path,
                (knowledge_point, document.relative_path),
            )),
            "reference_snippet": reference_snippet,
        },
    ]


def _concept_question_from_document(document: Document) -> dict[str, Any]:
    knowledge_point = _knowledge_point_from_document(document)
    expected_points = _extract_expected_points(
        document.content,
        document.relative_path,
        (knowledge_point,),
    )
    return {
        "id": str(uuid.uuid4()),
        "project_id": document.project_id,
        "source_path": document.relative_path,
        "question_type": "concept",
        "knowledge_point": knowledge_point,
        "prompt": (
            f"概念理解：请说明“{knowledge_point}”主要解决什么问题，"
            f"并引用来源 {document.relative_path} 中的关键词。"
        ),
        "expected_points": list(expected_points),
        "reference_snippet": _reference_snippet(document.content),
    }


def _knowledge_point_from_document(document: Document) -> str:
    for line in document.content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                return heading[:80]
    path = document.relative_path.replace("\\", "/").split("/")[-1]
    stem = path.rsplit(".", 1)[0]
    return stem or document.relative_path


def _reference_snippet(content: str) -> str:
    return content[:300].replace("\n", " ").strip()


def _extract_expected_points(
    content: str,
    relative_path: str,
    extra_points: tuple[str, ...] = (),
) -> tuple[str, ...]:
    raw = f"{relative_path} {content[:1000]}".lower()
    candidates = re.findall(r"[a-z0-9_.#-]{2,}|[\u4e00-\u9fff]{2,}", raw)
    result: list[str] = []
    for point in extra_points:
        normalized = point.strip()
        if normalized and normalized not in result:
            result.append(normalized)
    for token in candidates:
        if token in result:
            continue
        if token in {"md", "txt", "py", "js"}:
            continue
        result.append(token)
        if len(result) >= 5:
            break
    return tuple(result)
