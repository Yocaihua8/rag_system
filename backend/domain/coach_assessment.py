from __future__ import annotations

import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable, Mapping

from backend.domain.coach_models import (
    CoachAssessmentQuestion,
    CoachAssessmentResult,
    CoachAssessmentSession,
    CoachKnowledgePoint,
    CoachKnowledgeSource,
    CoachSkillNode,
)
from backend.domain.models import Document, SearchHit
from backend.domain.project_analysis import current_coach_analysis
from backend.storage import KnowledgeStore


MAX_ASSESSMENT_ANSWER_CHARS = 20_000
LOW_CONFIDENCE_THRESHOLD = 0.65
SCOPE_NOTICE = "这是当前项目、当前来源版本下的评估结果，不代表整体职业能力。"


class CoachAssessmentNotFoundError(LookupError):
    pass


class CoachAssessmentConflictError(RuntimeError):
    pass


def start_coach_assessment(
    store: KnowledgeStore,
    project_id: str,
    target_type: str = "",
    target_id: str = "",
    *,
    session_id: str = "",
    restart: bool = False,
    llm_client: Any | None = None,
) -> dict[str, Any]:
    clean_session_id = session_id.strip()
    if clean_session_id:
        session = store.get_coach_assessment_session(project_id, clean_session_id)
        if session is None:
            raise CoachAssessmentNotFoundError("coach assessment session not found")
        if target_type and target_type != session.target_type:
            raise ValueError("target_type does not match the assessment session")
        if target_id and target_id != session.target_id:
            raise ValueError("target_id does not match the assessment session")
        return _session_view(store, session, resumed=True)

    clean_target_type = target_type.strip()
    clean_target_id = target_id.strip()
    if clean_target_type not in {"knowledge_point", "skill"}:
        raise ValueError("target_type must be knowledge_point or skill")
    if not clean_target_id:
        raise ValueError("target_id is required")

    try:
        run = current_coach_analysis(store, project_id)
    except ValueError as exc:
        raise CoachAssessmentNotFoundError(str(exc)) from exc
    if run.status != "completed":
        raise CoachAssessmentConflictError("analysis_stale")

    active = store.get_active_coach_assessment_session(
        project_id,
        run.id,
        clean_target_type,
        clean_target_id,
    )
    if active and not restart:
        return _session_view(store, active, resumed=True)
    if active:
        store.abandon_coach_assessment_session(project_id, active.id)

    points = store.list_coach_knowledge_points(project_id, run_id=run.id)
    mappings = store.list_coach_skill_mappings(project_id, run_id=run.id)
    nodes = store.list_coach_skill_nodes()
    target_points = _target_points(
        clean_target_type,
        clean_target_id,
        points,
        mappings,
        nodes,
    )
    if not target_points:
        raise CoachAssessmentConflictError("assessment_target_not_assessable")

    question_drafts = [
        _question_draft(point, index)
        for index, point in enumerate(target_points[:3])
    ]
    _enhance_question_prompts(question_drafts, target_points[:3], llm_client)
    current = current_coach_analysis(store, project_id)
    if current.status != "completed" or current.id != run.id:
        raise CoachAssessmentConflictError("analysis_stale")
    session = store.create_coach_assessment_session(
        project_id,
        run.id,
        clean_target_type,
        clean_target_id,
        question_drafts,
    )
    return _session_view(store, session, resumed=False)


def answer_coach_assessment(
    store: KnowledgeStore,
    project_id: str,
    session_id: str,
    question_id: str,
    answer: str,
    *,
    evaluation_mode: str = "auto",
    llm_client: Any | None = None,
) -> dict[str, Any]:
    clean_session_id = session_id.strip()
    clean_question_id = question_id.strip()
    clean_answer = answer.strip()
    if not clean_session_id:
        raise ValueError("session_id is required")
    if not clean_question_id:
        raise ValueError("question_id is required")
    if not clean_answer:
        raise ValueError("answer is required")
    if len(clean_answer) > MAX_ASSESSMENT_ANSWER_CHARS:
        raise ValueError(
            f"answer must not exceed {MAX_ASSESSMENT_ANSWER_CHARS} characters"
        )
    clean_mode = evaluation_mode.strip() or "auto"
    if clean_mode not in {"auto", "rule"}:
        raise ValueError("evaluation_mode must be auto or rule")

    session = store.get_coach_assessment_session(project_id, clean_session_id)
    if session is None:
        raise CoachAssessmentNotFoundError("coach assessment session not found")
    question = next(
        (item for item in session.questions if item.id == clean_question_id),
        None,
    )
    if question is None:
        raise CoachAssessmentNotFoundError("coach assessment question not found")

    existing_answers = {
        item.question_id: item
        for item in store.list_coach_assessment_answers(project_id, session.id)
    }
    existing_answer = existing_answers.get(question.id)
    if existing_answer:
        if existing_answer.answer != clean_answer:
            raise CoachAssessmentConflictError(
                "assessment_question_already_answered"
            )
        existing_result = next(
            (
                item
                for item in store.list_coach_assessment_results(
                    project_id,
                    session_id=session.id,
                )
                if item.question_id == question.id
            ),
            None,
        )
        if existing_result is None:
            raise RuntimeError("stored assessment answer has no result")
        return {
            "result": _result_view(existing_result),
            "session": _session_view(store, session, resumed=True),
            "replayed": True,
        }

    if session.status != "active":
        raise CoachAssessmentConflictError("assessment_session_not_active")
    current = current_coach_analysis(store, project_id)
    if (
        current is None
        or current.status != "completed"
        or current.id != session.analysis_run_id
    ):
        raise CoachAssessmentConflictError("analysis_stale")

    grading = score_coach_answer(question, clean_answer)
    if clean_mode == "auto" and llm_client is not None:
        try:
            grading = _score_with_model(
                store,
                project_id,
                session.analysis_run_id,
                question,
                clean_answer,
                llm_client,
            )
        except Exception as exc:
            grading["confidence"] = min(float(grading["confidence"]), 0.49)
            grading["evaluation_warning"] = (
                "模型评估无效，已回退规则评分："
                f"{type(exc).__name__}"
            )

    current = current_coach_analysis(store, project_id)
    if current.status != "completed" or current.id != session.analysis_run_id:
        raise CoachAssessmentConflictError("analysis_stale")
    _, result, stored_session = store.create_coach_assessment_answer_result(
        project_id,
        session.id,
        question.id,
        clean_answer,
        str(grading["evaluator"]),
        float(grading["score"]),
        float(grading["confidence"]),
        list(grading["matched_evidence"]),
        list(grading["missing_points"]),
        list(question.source_ids),
        evaluation_warning=str(grading.get("evaluation_warning", "")),
        feedback=str(grading["feedback"]),
    )
    return {
        "result": _result_view(result),
        "session": _session_view(store, stored_session, resumed=False),
        "replayed": False,
    }


def score_coach_answer(
    question: CoachAssessmentQuestion,
    answer: str,
) -> dict[str, Any]:
    matched: list[dict[str, str]] = []
    missing: list[str] = []
    for point in question.expected_points:
        evidence = _verbatim_match(answer, point)
        if evidence:
            matched.append({"point": point, "evidence": evidence})
        else:
            missing.append(point)
    score = round(len(matched) / max(1, len(question.expected_points)), 4)
    confidence = 0.60 if len(question.expected_points) >= 3 else 0.45
    status = assessment_status(score)
    return {
        "evaluator": "rule",
        "score": score,
        "confidence": confidence,
        "status": status,
        "matched_evidence": matched,
        "missing_points": missing,
        "feedback": _feedback(status),
        "evaluation_warning": "",
    }


def assessment_status(score: float) -> str:
    if score < 0.50:
        return "needs_work"
    if score < 0.75:
        return "developing"
    return "mastered"


def build_coach_coverage(
    store: KnowledgeStore,
    project_id: str,
) -> dict[str, Any]:
    try:
        run = current_coach_analysis(store, project_id)
    except ValueError as exc:
        raise CoachAssessmentNotFoundError(str(exc)) from exc
    stale = run.status == "stale"
    points = store.list_coach_knowledge_points(project_id, run_id=run.id)
    mappings = store.list_coach_skill_mappings(project_id, run_id=run.id)
    nodes = store.list_coach_skill_nodes()
    sessions = store.list_coach_assessment_sessions(project_id, limit=500)
    sessions_by_id = {session.id: session for session in sessions}
    results = store.list_coach_assessment_results(project_id, limit=1000)
    learning_sessions = store.list_coach_learning_sessions(
        project_id,
        limit=500,
    )

    evidence_by_point: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        session = sessions_by_id.get(result.session_id)
        if not session or session.analysis_run_id != run.id:
            continue
        evidence_by_point.setdefault(result.knowledge_point_id, []).append(
            {
                "id": result.id,
                "evidence_type": "assessment_result",
                "session_id": result.session_id,
                "score": result.score,
                "confidence": result.confidence,
                "status": result.status,
                "evaluator": result.evaluator,
                "created_at": result.created_at,
            }
        )
    recent_learning_attempts: list[dict[str, Any]] = []
    for session in learning_sessions:
        current_run = session.analysis_run_id == run.id
        for step in session.steps:
            for attempt in step.attempts:
                if (
                    attempt.status != "evaluated"
                    or not attempt.counts_for_mastery
                    or attempt.score is None
                ):
                    continue
                evidence = {
                    "id": attempt.id,
                    "evidence_type": "learning_attempt",
                    "session_id": session.id,
                    "score": float(attempt.score),
                    "confidence": float(attempt.confidence or 0.0),
                    "status": assessment_status(float(attempt.score)),
                    "evaluator": attempt.evaluator,
                    "created_at": attempt.created_at,
                    "knowledge_point_id": step.knowledge_point_id,
                    "analysis_run_id": session.analysis_run_id,
                    "target_type": session.target_type,
                    "target_id": session.target_id,
                    "valid_for_current_sources": bool(
                        current_run and not stale
                    ),
                }
                recent_learning_attempts.append(evidence)
                if current_run:
                    evidence_by_point.setdefault(
                        step.knowledge_point_id,
                        [],
                    ).append(evidence)
    latest_by_point = {
        point_id: max(
            evidence,
            key=lambda item: (
                str(item["created_at"]),
                str(item["id"]),
            ),
        )
        for point_id, evidence in evidence_by_point.items()
    }

    sources = _source_index(points)
    point_views: list[dict[str, Any]] = []
    point_state: dict[str, dict[str, Any]] = {}
    status_counts = {
        "unassessed": 0,
        "needs_work": 0,
        "developing": 0,
        "mastered": 0,
    }
    assessed_count = 0
    for point in points:
        result = latest_by_point.get(point.id)
        valid = bool(result and not stale)
        status = str(result["status"]) if valid and result else "unassessed"
        if valid:
            assessed_count += 1
        status_counts[status] += 1
        source_ids = [source.id for source in point.sources]
        view = {
            "id": point.id,
            "stable_key": point.stable_key,
            "title": point.title,
            "category": point.category,
            "summary": point.summary,
            "status": status,
            "assessment_state": "verified" if valid else "unverified",
            "valid_for_current_sources": valid,
            "score": result["score"] if result else None,
            "confidence": result["confidence"] if result else None,
            "low_confidence": (
                float(result["confidence"]) < LOW_CONFIDENCE_THRESHOLD
                if result
                else False
            ),
            "evaluator": str(result["evaluator"]) if result else "",
            "assessed_at": str(result["created_at"]) if result else "",
            "session_id": str(result["session_id"]) if result else "",
            "result_id": (
                str(result["id"])
                if result and result["evidence_type"] == "assessment_result"
                else ""
            ),
            "evidence_id": str(result["id"]) if result else "",
            "evidence_type": (
                str(result["evidence_type"]) if result else ""
            ),
            "historical_status": (
                str(result["status"]) if result and not valid else ""
            ),
            "source_ids": source_ids,
        }
        point_views.append(view)
        point_state[point.id] = view

    skill_views = _skill_coverage(nodes, mappings, point_state)
    recent = []
    for result in results[:20]:
        session = sessions_by_id.get(result.session_id)
        if session is None:
            continue
        valid = (
            not stale
            and session.analysis_run_id == run.id
        )
        recent.append(
            {
                **_result_view(result),
                "target_type": session.target_type,
                "target_id": session.target_id,
                "analysis_run_id": session.analysis_run_id,
                "valid_for_current_sources": valid,
            }
        )

    total = len(points)
    recent_learning_attempts.sort(
        key=lambda item: (
            str(item["created_at"]),
            str(item["id"]),
        ),
        reverse=True,
    )
    return {
        "project_id": project_id,
        "analysis": run.to_dict(),
        "stale": stale,
        "can_assess": not stale,
        "summary": {
            "knowledge_point_count": total,
            "assessed_count": assessed_count,
            "unassessed_count": total - assessed_count,
            "coverage_ratio": round(assessed_count / max(1, total), 4),
            "status_counts": status_counts,
        },
        "knowledge_points": point_views,
        "skills": skill_views,
        "recent_assessments": recent,
        "recent_learning_attempts": recent_learning_attempts[:20],
        "sources": sources,
        "scope_notice": SCOPE_NOTICE,
    }


def _target_points(
    target_type: str,
    target_id: str,
    points: list[CoachKnowledgePoint],
    mappings: list[Any],
    nodes: list[CoachSkillNode],
) -> list[CoachKnowledgePoint]:
    point_by_id = {point.id: point for point in points}
    if target_type == "knowledge_point":
        point = point_by_id.get(target_id)
        if point is None:
            raise ValueError("knowledge point does not belong to current analysis")
        return [point]

    node_by_id = {node.id: node for node in nodes}
    if target_id not in node_by_id:
        raise ValueError("skill node not found")
    descendant_ids = _descendant_skill_ids(target_id, nodes)
    best_confidence: dict[str, float] = {}
    for mapping in mappings:
        if mapping.skill_node_id not in descendant_ids:
            continue
        best_confidence[mapping.knowledge_point_id] = max(
            best_confidence.get(mapping.knowledge_point_id, 0.0),
            float(mapping.confidence),
        )
    ordered_ids = sorted(
        best_confidence,
        key=lambda point_id: (
            -best_confidence[point_id],
            point_by_id[point_id].stable_key if point_id in point_by_id else "",
        ),
    )
    return [point_by_id[point_id] for point_id in ordered_ids if point_id in point_by_id]


def _question_draft(
    point: CoachKnowledgePoint,
    sort_order: int,
) -> dict[str, Any]:
    source_ids = [source.id for source in point.sources]
    if not source_ids:
        raise CoachAssessmentConflictError("assessment_target_not_assessable")
    source_paths = "、".join(source.source_path for source in point.sources[:2])
    question_type = _question_type(point)
    if question_type == "flow":
        prompt = (
            f"请结合来源 {source_paths}，按步骤说明“{point.title}”在当前项目中的流程、"
            "关键职责与产物。"
        )
    elif question_type == "code_location":
        prompt = (
            f"请结合来源 {source_paths}，指出“{point.title}”在当前项目中的代码或配置位置，"
            "并说明它如何参与运行。"
        )
    else:
        prompt = (
            f"请结合来源 {source_paths}，说明“{point.title}”在当前项目中解决什么问题，"
            "并概括其关键实现。"
        )
    expected_points = _expected_points(point, prompt)
    if not expected_points:
        raise CoachAssessmentConflictError("assessment_target_not_assessable")
    return {
        "knowledge_point_id": point.id,
        "prompt": prompt,
        "question_type": question_type,
        "expected_points": expected_points,
        "source_ids": source_ids,
        "sort_order": sort_order,
    }


def _question_type(point: CoachKnowledgePoint) -> str:
    key = point.stable_key.lower()
    if point.category in {"architecture", "delivery"}:
        return "flow"
    if any(token in key for token in ("entrypoint", "config", "path", "file")):
        return "code_location"
    return "concept"


def _expected_points(
    point: CoachKnowledgePoint,
    prompt: str,
) -> list[str]:
    stop_words = {
        "and",
        "class",
        "const",
        "def",
        "else",
        "false",
        "from",
        "function",
        "if",
        "import",
        "none",
        "null",
        "return",
        "true",
        "var",
    }
    candidates: list[str] = []
    text = "\n".join(
        [point.summary]
        + [source.excerpt for source in point.sources]
    )
    candidates.extend(re.findall(r"[A-Za-z][A-Za-z0-9_.-]{1,39}", text))
    for segment in re.split(r"[\s，。；：、,.;:()\[\]{}]+", text):
        clean = segment.strip()
        if 2 <= len(clean) <= 32 and re.search(r"[\u4e00-\u9fff]", clean):
            candidates.append(clean)
    result: list[str] = []
    seen: set[str] = set()
    normalized_result: list[str] = []
    normalized_prompt = _normalized_text(prompt)
    for candidate in candidates:
        clean = candidate.strip()
        key = clean.casefold()
        normalized = _normalized_text(clean)
        if (
            not clean
            or key in seen
            or key in {"readme", "http", "https"}
            or key in stop_words
            or clean.isdigit()
            or not normalized
            or normalized in normalized_prompt
            or any(
                normalized in existing or existing in normalized
                for existing in normalized_result
            )
        ):
            continue
        seen.add(key)
        result.append(clean)
        normalized_result.append(normalized)
        if len(result) >= 5:
            break
    return result


def _enhance_question_prompts(
    drafts: list[dict[str, Any]],
    points: list[CoachKnowledgePoint],
    llm_client: Any | None,
) -> None:
    generate = getattr(llm_client, "generate_answer", None)
    if not callable(generate):
        return
    for draft, point in zip(drafts, points):
        hits = _hits_for_sources(point.sources, point.project_id)
        if not hits:
            continue
        try:
            raw = str(
                generate(
                    "请只改写下面这道项目理解题，使表达清晰但不改变目标或来源；"
                    "只返回改写后的题目正文：\n"
                    + str(draft["prompt"]),
                    hits,
                )
                or ""
            ).strip()
        except Exception:
            continue
        if raw and len(raw) <= 1_000 and "expected_points" not in raw:
            draft["prompt"] = raw


def _score_with_model(
    store: KnowledgeStore,
    project_id: str,
    run_id: str,
    question: CoachAssessmentQuestion,
    answer: str,
    llm_client: Any,
) -> dict[str, Any]:
    generate = getattr(llm_client, "generate_answer", None)
    if not callable(generate):
        raise ValueError("model client cannot evaluate answers")
    points = store.list_coach_knowledge_points(project_id, run_id=run_id)
    sources_by_id = {
        source.id: source
        for point in points
        for source in point.sources
    }
    sources = [
        sources_by_id[source_id]
        for source_id in question.source_ids
        if source_id in sources_by_id
    ]
    if len(sources) != len(question.source_ids):
        raise ValueError("assessment sources are unavailable")
    prompt = (
        "你是项目知识评估器。只返回 JSON，不要返回 Markdown。"
        "matched 中的 point 必须逐字来自 expected_points，evidence 必须逐字来自 user_answer；"
        "missing_points 必须与 matched 一起完整覆盖 expected_points；"
        "confidence 必须是 0 到 1。\n"
        + json.dumps(
            {
                "question": question.prompt,
                "expected_points": list(question.expected_points),
                "user_answer": answer,
                "schema": {
                    "matched": [{"point": "...", "evidence": "..."}],
                    "missing_points": ["..."],
                    "confidence": 0.0,
                },
            },
            ensure_ascii=False,
        )
    )
    raw = str(generate(prompt, _hits_for_sources(sources, project_id)) or "").strip()
    payload = _json_object(raw)
    matched_raw = payload.get("matched")
    missing_raw = payload.get("missing_points")
    confidence_raw = payload.get("confidence")
    if not isinstance(matched_raw, list) or not isinstance(missing_raw, list):
        raise ValueError("model assessment lists are invalid")
    try:
        confidence = float(confidence_raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("model confidence is invalid") from exc
    if not math.isfinite(confidence) or not 0 <= confidence <= 1:
        raise ValueError("model confidence is invalid")

    expected = list(question.expected_points)
    expected_set = set(expected)
    matched: list[dict[str, str]] = []
    matched_points: set[str] = set()
    for raw_item in matched_raw:
        if not isinstance(raw_item, Mapping):
            raise ValueError("model matched evidence is invalid")
        point = str(raw_item.get("point") or "").strip()
        evidence = str(raw_item.get("evidence") or "").strip()
        if point not in expected_set or point in matched_points:
            raise ValueError("model matched point is invalid")
        verbatim = _verbatim_match(answer, evidence)
        if not evidence or not verbatim:
            raise ValueError("model evidence is not present in the answer")
        matched_points.add(point)
        matched.append({"point": point, "evidence": verbatim})
    missing = [str(item).strip() for item in missing_raw]
    if (
        any(item not in expected_set for item in missing)
        or len(set(missing)) != len(missing)
        or matched_points & set(missing)
        or matched_points | set(missing) != expected_set
    ):
        raise ValueError("model assessment does not cover the scoring basis")

    score = round(len(matched) / max(1, len(expected)), 4)
    status = assessment_status(score)
    return {
        "evaluator": "model",
        "score": score,
        "confidence": min(confidence, 0.85),
        "status": status,
        "matched_evidence": matched,
        "missing_points": missing,
        "feedback": _feedback(status),
        "evaluation_warning": "",
    }


def _session_view(
    store: KnowledgeStore,
    session: CoachAssessmentSession,
    *,
    resumed: bool,
) -> dict[str, Any]:
    try:
        current = current_coach_analysis(store, session.project_id)
    except ValueError:
        current = None
    can_answer = bool(
        session.status == "active"
        and current
        and current.status == "completed"
        and current.id == session.analysis_run_id
    )
    answers = {
        answer.question_id: answer
        for answer in store.list_coach_assessment_answers(
            session.project_id,
            session.id,
        )
    }
    results = {
        result.question_id: result
        for result in store.list_coach_assessment_results(
            session.project_id,
            session_id=session.id,
        )
    }
    points = store.list_coach_knowledge_points(
        session.project_id,
        run_id=session.analysis_run_id,
    )
    sources = _source_index(points)
    question_views = []
    for question in session.questions:
        answer = answers.get(question.id)
        result = results.get(question.id)
        view = question.to_dict()
        view["answered"] = bool(answer)
        if answer and result:
            view["answer"] = answer.to_dict()
            view["result"] = _result_view(result)
        question_views.append(view)
    answered_count = len(answers)
    next_question = next(
        (question for question in question_views if not question["answered"]),
        None,
    )
    target = _target_payload(session, points, store.list_coach_skill_nodes())
    return {
        "id": session.id,
        "project_id": session.project_id,
        "analysis_run_id": session.analysis_run_id,
        "target_type": session.target_type,
        "target_id": session.target_id,
        "target": target,
        "status": session.status,
        "resumed": resumed,
        "read_only": not can_answer,
        "can_answer": can_answer,
        "question_count": len(question_views),
        "answered_count": answered_count,
        "current_question_id": next_question["id"] if next_question else None,
        "questions": question_views,
        "sources": sources,
        "created_at": session.created_at,
        "completed_at": session.completed_at,
        "scope_notice": SCOPE_NOTICE,
    }


def _target_payload(
    session: CoachAssessmentSession,
    points: list[CoachKnowledgePoint],
    nodes: list[CoachSkillNode],
) -> dict[str, str]:
    if session.target_type == "knowledge_point":
        point = next((item for item in points if item.id == session.target_id), None)
        return {
            "stable_key": point.stable_key if point else "",
            "label": point.title if point else "历史知识点",
        }
    node = next((item for item in nodes if item.id == session.target_id), None)
    return {
        "stable_key": node.stable_key if node else "",
        "label": node.name if node else "历史技能节点",
    }


def _result_view(result: CoachAssessmentResult) -> dict[str, Any]:
    return {
        **result.to_dict(),
        "low_confidence": result.confidence < LOW_CONFIDENCE_THRESHOLD,
    }


def _source_index(
    points: Iterable[CoachKnowledgePoint],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for point in points:
        for source in point.sources:
            payload = source.to_dict()
            payload["path"] = payload.pop("source_path")
            result[source.id] = payload
    return result


def _skill_coverage(
    nodes: list[CoachSkillNode],
    mappings: list[Any],
    point_state: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    result = []
    for node in nodes:
        descendants = _descendant_skill_ids(node.id, nodes)
        weights: dict[str, float] = {}
        source_ids: set[str] = set()
        for mapping in mappings:
            if mapping.skill_node_id not in descendants:
                continue
            weights[mapping.knowledge_point_id] = max(
                weights.get(mapping.knowledge_point_id, 0.0),
                float(mapping.confidence),
            )
            source_ids.add(mapping.source_id)
        mapped_ids = sorted(weights)
        assessed_ids = [
            point_id
            for point_id in mapped_ids
            if point_state.get(point_id, {}).get("assessment_state") == "verified"
        ]
        if not mapped_ids:
            assessment_state = "no_project_evidence"
            status = None
            score = None
            confidence = None
        elif not assessed_ids:
            assessment_state = "unverified"
            status = "unassessed"
            score = None
            confidence = None
        else:
            assessment_state = (
                "verified"
                if len(assessed_ids) == len(mapped_ids)
                else "partially_verified"
            )
            denominator = sum(weights[point_id] for point_id in assessed_ids)
            score = round(
                sum(
                    float(point_state[point_id]["score"]) * weights[point_id]
                    for point_id in assessed_ids
                )
                / max(denominator, 1e-9),
                4,
            )
            confidence = round(
                sum(
                    float(point_state[point_id]["confidence"]) * weights[point_id]
                    for point_id in assessed_ids
                )
                / max(denominator, 1e-9),
                4,
            )
            status = assessment_status(score)
        result.append(
            {
                **node.to_dict(),
                "project_evidence": (
                    "mapped" if mapped_ids else "no_project_evidence"
                ),
                "assessment_state": assessment_state,
                "status": status,
                "score": score,
                "confidence": confidence,
                "low_confidence": (
                    confidence < LOW_CONFIDENCE_THRESHOLD
                    if confidence is not None
                    else False
                ),
                "mapped_knowledge_point_count": len(mapped_ids),
                "assessed_knowledge_point_count": len(assessed_ids),
                "coverage_ratio": round(
                    len(assessed_ids) / max(1, len(mapped_ids)),
                    4,
                ),
                "knowledge_point_ids": mapped_ids,
                "source_ids": sorted(source_ids),
            }
        )
    return result


def _descendant_skill_ids(
    target_id: str,
    nodes: Iterable[CoachSkillNode],
) -> set[str]:
    children: dict[str, list[str]] = {}
    for node in nodes:
        children.setdefault(node.parent_id, []).append(node.id)
    result: set[str] = set()
    pending = [target_id]
    while pending:
        node_id = pending.pop()
        if node_id in result:
            continue
        result.add(node_id)
        pending.extend(children.get(node_id, ()))
    return result


def _hits_for_sources(
    sources: Iterable[CoachKnowledgeSource],
    project_id: str,
) -> list[SearchHit]:
    hits = []
    for source in sources:
        document = Document(
            id=source.document_id or f"snapshot:{source.id}",
            project_id=project_id,
            source_path=Path(source.source_path),
            relative_path=source.source_path,
            content=source.excerpt,
            checksum=source.source_hash,
            updated_at="",
        )
        hits.append(
            SearchHit(
                document=document,
                score=1.0,
                snippet=source.excerpt,
            )
        )
    return hits


def _json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("model assessment is not JSON")
    payload = json.loads(text[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("model assessment must be an object")
    return payload


def _verbatim_match(answer: str, value: str) -> str:
    clean_value = value.strip()
    if not clean_value:
        return ""
    answer_folded = answer.casefold()
    index = answer_folded.find(clean_value.casefold())
    if index >= 0:
        return answer[index : index + len(clean_value)]
    normalized_answer = _normalized_text(answer)
    normalized_value = _normalized_text(clean_value)
    if normalized_value and normalized_value in normalized_answer:
        return clean_value if clean_value in answer else ""
    return ""


def _normalized_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[\W_]+", "", normalized, flags=re.UNICODE)


def _feedback(status: str) -> str:
    return {
        "needs_work": "当前回答仍缺少主要项目依据，建议阅读来源后重新组织答案。",
        "developing": "当前回答已覆盖部分要点，建议补齐缺失点并结合来源复述。",
        "mastered": "当前回答已覆盖主要项目依据，可继续通过源码定位或实践巩固。",
    }[status]


__all__ = [
    "CoachAssessmentConflictError",
    "CoachAssessmentNotFoundError",
    "LOW_CONFIDENCE_THRESHOLD",
    "answer_coach_assessment",
    "assessment_status",
    "build_coach_coverage",
    "score_coach_answer",
    "start_coach_assessment",
]
