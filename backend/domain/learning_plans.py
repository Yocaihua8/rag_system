from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Any

from backend.domain.coach_assessment import (
    CoachAssessmentNotFoundError,
    build_coach_coverage,
)
from backend.domain.coach_models import (
    CoachKnowledgePoint,
    CoachKnowledgeSource,
    CoachLearningPlan,
    CoachSkillNode,
)
from backend.domain.models import Document, SearchHit
from backend.domain.project_analysis import current_coach_analysis
from backend.storage import KnowledgeStore


DEFAULT_MAX_PLAN_ITEMS = 8
MAX_PLAN_ITEMS = 20
MAX_EDIT_ITEMS = 50
PLAN_SCOPE_NOTICE = "学习计划仅针对当前项目和当前来源版本，不代表整体职业能力。"


class CoachLearningPlanNotFoundError(LookupError):
    pass


class CoachLearningPlanConflictError(RuntimeError):
    pass


class _ProjectPlanCoordinator:
    def __init__(self) -> None:
        self._guard = Lock()
        self._locks: dict[str, Lock] = {}

    @contextmanager
    def project_scope(self, project_id: str):
        with self._guard:
            project_lock = self._locks.setdefault(project_id, Lock())
        project_lock.acquire()
        try:
            yield
        finally:
            project_lock.release()


_plan_coordinator = _ProjectPlanCoordinator()


def generate_learning_plan(
    store: KnowledgeStore,
    project_id: str,
    *,
    llm_client: Any | None = None,
    max_items: int = DEFAULT_MAX_PLAN_ITEMS,
) -> dict[str, Any]:
    clean_limit = _plan_limit(max_items)
    with _plan_coordinator.project_scope(project_id):
        run = _current_analysis(store, project_id)
        if run.status != "completed":
            raise CoachLearningPlanConflictError("analysis_stale")
        try:
            coverage = build_coach_coverage(store, project_id)
        except CoachAssessmentNotFoundError as exc:
            raise CoachLearningPlanNotFoundError(str(exc)) from exc

        points = store.list_coach_knowledge_points(project_id, run_id=run.id)
        point_by_id = {point.id: point for point in points}
        mappings = store.list_coach_skill_mappings(project_id, run_id=run.id)
        best_skill_by_point: dict[str, tuple[float, str]] = {}
        for mapping in mappings:
            candidate = (float(mapping.confidence), mapping.skill_node_id)
            current = best_skill_by_point.get(mapping.knowledge_point_id)
            if current is None or candidate > current:
                best_skill_by_point[mapping.knowledge_point_id] = candidate

        candidates = [
            item
            for item in coverage["knowledge_points"]
            if item["status"] != "mastered"
        ]
        candidates.sort(key=_gap_sort_key)
        if not candidates:
            raise CoachLearningPlanConflictError("no_actionable_learning_gaps")

        drafts = []
        for sort_order, coverage_item in enumerate(candidates[:clean_limit]):
            point = point_by_id.get(str(coverage_item["id"]))
            if point is None:
                continue
            skill_match = best_skill_by_point.get(point.id)
            drafts.append(
                _learning_item_draft(
                    point,
                    str(coverage_item["status"]),
                    skill_match[1] if skill_match else "",
                    sort_order,
                )
            )
        if not drafts:
            raise CoachLearningPlanConflictError("no_actionable_learning_gaps")

        generation_mode = "rule"
        warning = ""
        try:
            if _enhance_plan_text(drafts, points, llm_client):
                generation_mode = "model"
        except Exception as exc:
            warning = f"模型计划增强无效，已回退规则草稿：{type(exc).__name__}"

        _require_current_completed_run(store, project_id, run.id)
        plan = store.create_coach_learning_plan(project_id, run.id, drafts)
        response = _single_plan_response(store, plan)
        response["generation_mode"] = generation_mode
        response["warning"] = warning
        return response


def build_current_learning_plan(
    store: KnowledgeStore,
    project_id: str,
) -> dict[str, Any]:
    run = _current_analysis(store, project_id)
    plans = store.list_coach_learning_plans(project_id, limit=500)
    draft = next((plan for plan in plans if plan.status == "draft"), None)
    confirmed = next(
        (plan for plan in plans if plan.status == "confirmed"),
        None,
    )
    current_ids = {plan.id for plan in (draft, confirmed) if plan is not None}
    history = [plan for plan in plans if plan.id not in current_ids]
    source_index = _sources_for_plans(store, plans)
    return {
        "project_id": project_id,
        "analysis": run.to_dict(),
        "stale": run.status == "stale",
        "draft": (
            _plan_view(
                draft,
                run.id,
                run.status,
                source_index,
                is_current_draft=True,
            )
            if draft
            else None
        ),
        "confirmed": (
            _plan_view(confirmed, run.id, run.status, source_index)
            if confirmed
            else None
        ),
        "history": [
            _plan_view(plan, run.id, run.status, source_index)
            for plan in history
        ],
        "sources": source_index,
        "scope_notice": PLAN_SCOPE_NOTICE,
    }


def update_learning_plan(
    store: KnowledgeStore,
    project_id: str,
    plan_id: str,
    *,
    items: Any = None,
    item_statuses: Any = None,
    expected_revision: Any = None,
    expected_items_hash: str = "",
    expected_progress_hash: str = "",
) -> dict[str, Any]:
    has_items = items is not None
    has_statuses = item_statuses is not None
    if has_items == has_statuses:
        raise ValueError("provide exactly one of items or item_statuses")

    with _plan_coordinator.project_scope(project_id):
        plan = _require_plan(store, project_id, plan_id)
        _check_expected_plan_version(
            plan,
            expected_revision,
            expected_items_hash,
        )
        if has_items:
            if plan.status != "draft":
                raise CoachLearningPlanConflictError(
                    "learning_plan_not_editable"
                )
            latest_draft = _latest_plan(store, project_id, "draft")
            if latest_draft is None or latest_draft.id != plan.id:
                raise CoachLearningPlanConflictError(
                    "learning_plan_not_current_draft"
                )
            _require_current_completed_run(
                store,
                project_id,
                plan.based_on_run_id,
            )
            normalized = _validated_update_items(store, plan, items)
            _require_current_completed_run(
                store,
                project_id,
                plan.based_on_run_id,
            )
            updated = store.update_coach_learning_plan(
                project_id,
                plan.id,
                normalized,
            )
        else:
            if plan.status != "confirmed":
                raise CoachLearningPlanConflictError(
                    "learning_plan_progress_not_editable"
                )
            _check_expected_progress(plan, expected_progress_hash)
            if not isinstance(item_statuses, Mapping):
                raise ValueError("item_statuses must be an object")
            normalized_statuses = {
                str(key).strip(): str(value).strip()
                for key, value in item_statuses.items()
            }
            if not normalized_statuses or any(
                not key for key in normalized_statuses
            ):
                raise ValueError("item_statuses is required")
            updated = store.update_coach_learning_plan_progress(
                project_id,
                plan.id,
                normalized_statuses,
            )
        return _single_plan_response(store, updated)


def confirm_learning_plan(
    store: KnowledgeStore,
    project_id: str,
    plan_id: str,
    *,
    expected_revision: Any = None,
    expected_items_hash: str = "",
) -> dict[str, Any]:
    with _plan_coordinator.project_scope(project_id):
        plan = _require_plan(store, project_id, plan_id)
        if plan.status == "confirmed":
            response = _single_plan_response(store, plan)
            response["replayed"] = True
            return response
        _check_expected_plan_version(
            plan,
            expected_revision,
            expected_items_hash,
        )
        if plan.status != "draft":
            raise CoachLearningPlanConflictError(
                "learning_plan_not_confirmable"
            )
        latest_draft = _latest_plan(store, project_id, "draft")
        if latest_draft is None or latest_draft.id != plan.id:
            raise CoachLearningPlanConflictError(
                "learning_plan_not_current_draft"
            )
        _require_current_completed_run(
            store,
            project_id,
            plan.based_on_run_id,
        )
        confirmed = store.confirm_coach_learning_plan(project_id, plan.id)
        response = _single_plan_response(store, confirmed)
        response["replayed"] = False
        return response


def learning_plan_items_hash(plan: CoachLearningPlan) -> str:
    payload = [
        {
            "stable_key": item.stable_key,
            "item_type": item.item_type,
            "objective": item.objective,
            "knowledge_point_id": item.knowledge_point_id,
            "skill_node_id": item.skill_node_id,
            "source_ids": list(item.source_ids),
            "practice_question": item.practice_question,
            "completion_criteria": item.completion_criteria,
            "estimated_minutes": item.estimated_minutes,
            "sort_order": item.sort_order,
        }
        for item in plan.items
    ]
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def learning_plan_progress_hash(plan: CoachLearningPlan) -> str:
    payload = [
        {
            "id": item.id,
            "stable_key": item.stable_key,
            "status": item.status,
        }
        for item in plan.items
    ]
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _learning_item_draft(
    point: CoachKnowledgePoint,
    status: str,
    skill_node_id: str,
    sort_order: int,
) -> dict[str, Any]:
    sources = list(point.sources)
    source_ids = [source.id for source in sources]
    item_type = "learning" if source_ids else "source_gap"
    labels = {
        "needs_work": (
            f"补强“{point.title}”的当前项目理解",
            f"不查看答案，结合项目来源说明“{point.title}”的职责、位置与实现依据。",
            "完成定向评估，结果至少达到 developing，并能指出一条真实来源。",
            45,
        ),
        "developing": (
            f"完善“{point.title}”的关键实现理解",
            f"结合源码或文档复述“{point.title}”的关键步骤，并解释一处实现细节。",
            "完成定向评估并达到 mastered，答案覆盖主要项目依据。",
            35,
        ),
        "unassessed": (
            f"验证“{point.title}”的项目知识覆盖",
            f"阅读来源后，用自己的话说明“{point.title}”如何参与当前项目。",
            "完成一次有效定向评估，并记录仍需补强的要点。",
            25,
        ),
    }
    objective, practice, completion, minutes = labels[status]
    if item_type == "source_gap":
        objective = f"为“{point.title}”补充可验证的项目资料"
        practice = f"定位能说明“{point.title}”的源码、清单、测试或项目文档。"
        completion = "导入至少一条真实来源并重新运行项目分析。"
        minutes = 20
    return {
        "stable_key": f"learn:{point.stable_key}",
        "item_type": item_type,
        "objective": objective,
        "knowledge_point_id": point.id,
        "skill_node_id": skill_node_id,
        "source_ids": source_ids,
        "practice_question": practice,
        "completion_criteria": completion,
        "estimated_minutes": minutes,
        "status": "todo",
        "sort_order": sort_order,
    }


def _gap_sort_key(item: Mapping[str, Any]) -> tuple[Any, ...]:
    rank = {
        "needs_work": 0,
        "developing": 1,
        "unassessed": 2,
    }.get(str(item.get("status")), 9)
    raw_score = item.get("score")
    score = float(raw_score) if isinstance(raw_score, (int, float)) else 1.0
    return rank, score, str(item.get("stable_key") or "")


def _enhance_plan_text(
    drafts: list[dict[str, Any]],
    points: list[CoachKnowledgePoint],
    llm_client: Any | None,
) -> bool:
    generate = getattr(llm_client, "generate_answer", None)
    if not callable(generate):
        return False
    source_ids = {
        source_id
        for draft in drafts
        for source_id in draft["source_ids"]
    }
    source_by_id = {
        source.id: source
        for point in points
        for source in point.sources
    }
    sources = [
        source_by_id[source_id]
        for source_id in sorted(source_ids)
        if source_id in source_by_id
    ]
    prompt = (
        "你是本地项目学习计划编辑器。只返回 JSON 数组，不要返回 Markdown。"
        "只能润色 objective、practice_question、completion_criteria；"
        "stable_key 必须原样返回且每项恰好一次，不得增加任务或来源。\n"
        + json.dumps(
            [
                {
                    "stable_key": draft["stable_key"],
                    "objective": draft["objective"],
                    "practice_question": draft["practice_question"],
                    "completion_criteria": draft["completion_criteria"],
                }
                for draft in drafts
            ],
            ensure_ascii=False,
        )
    )
    raw = str(
        generate(
            prompt,
            _hits_for_sources(sources, points[0].project_id if points else ""),
        )
        or ""
    ).strip()
    payload = _json_array(raw)
    expected_keys = [str(draft["stable_key"]) for draft in drafts]
    if len(payload) != len(drafts):
        raise ValueError("model learning plan item count is invalid")
    enhanced_by_key: dict[str, dict[str, str]] = {}
    for item in payload:
        if not isinstance(item, Mapping):
            raise ValueError("model learning plan items must be objects")
        stable_key = str(item.get("stable_key") or "").strip()
        if stable_key in enhanced_by_key or stable_key not in expected_keys:
            raise ValueError("model learning plan stable_key is invalid")
        enhanced_by_key[stable_key] = {
            field: _enhanced_text(item.get(field), field)
            for field in (
                "objective",
                "practice_question",
                "completion_criteria",
            )
        }
    if set(enhanced_by_key) != set(expected_keys):
        raise ValueError("model learning plan is incomplete")
    for draft in drafts:
        draft.update(enhanced_by_key[str(draft["stable_key"])])
    return True


def _validated_update_items(
    store: KnowledgeStore,
    plan: CoachLearningPlan,
    items: Any,
) -> list[dict[str, Any]]:
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty array")
    if len(items) > MAX_EDIT_ITEMS:
        raise ValueError(f"items must not exceed {MAX_EDIT_ITEMS}")
    points = store.list_coach_knowledge_points(
        plan.project_id,
        run_id=plan.based_on_run_id,
    )
    point_by_id = {point.id: point for point in points}
    source_to_point = {
        source.id: point.id
        for point in points
        for source in point.sources
    }
    mappings = store.list_coach_skill_mappings(
        plan.project_id,
        run_id=plan.based_on_run_id,
    )
    nodes = store.list_coach_skill_nodes()
    mapped_points_by_skill: dict[str, set[str]] = {}
    for node in nodes:
        descendants = _descendant_skill_ids(node.id, nodes)
        mapped_points_by_skill[node.id] = {
            mapping.knowledge_point_id
            for mapping in mappings
            if mapping.skill_node_id in descendants
        }

    normalized = []
    for sort_order, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise ValueError("learning plan items must be objects")
        item_type = str(item.get("item_type") or "learning").strip()
        knowledge_point_id = str(item.get("knowledge_point_id") or "").strip()
        skill_node_id = str(item.get("skill_node_id") or "").strip()
        source_ids = _text_list(item.get("source_ids"), "source_ids")
        if knowledge_point_id and knowledge_point_id not in point_by_id:
            raise ValueError(
                "knowledge point does not belong to the plan analysis"
            )
        if skill_node_id and not mapped_points_by_skill.get(skill_node_id):
            raise ValueError("skill node has no evidence in the plan analysis")
        if knowledge_point_id and skill_node_id and (
            knowledge_point_id not in mapped_points_by_skill[skill_node_id]
        ):
            raise ValueError(
                "knowledge point is not mapped to the selected skill"
            )
        if any(source_id not in source_to_point for source_id in source_ids):
            raise ValueError("source does not belong to the plan analysis")
        if knowledge_point_id and any(
            source_to_point[source_id] != knowledge_point_id
            for source_id in source_ids
        ):
            raise ValueError(
                "source does not belong to the selected knowledge point"
            )
        if skill_node_id and not knowledge_point_id:
            allowed_points = mapped_points_by_skill[skill_node_id]
            if any(
                source_to_point[source_id] not in allowed_points
                for source_id in source_ids
            ):
                raise ValueError(
                    "source does not belong to the selected skill"
                )
        if item_type == "learning" and not source_ids:
            raise ValueError("learning item requires at least one source")
        if item_type == "source_gap" and source_ids:
            raise ValueError("source_gap item must not invent reading sources")
        estimated_minutes = item.get("estimated_minutes")
        if (
            isinstance(estimated_minutes, bool)
            or not isinstance(estimated_minutes, int)
            or estimated_minutes <= 0
        ):
            raise ValueError("estimated_minutes must be a positive integer")
        normalized.append(
            {
                "stable_key": _required_text(item.get("stable_key"), "stable_key"),
                "item_type": item_type,
                "objective": _required_text(item.get("objective"), "objective"),
                "knowledge_point_id": knowledge_point_id,
                "skill_node_id": skill_node_id,
                "source_ids": source_ids,
                "practice_question": _required_text(
                    item.get("practice_question"),
                    "practice_question",
                ),
                "completion_criteria": _required_text(
                    item.get("completion_criteria"),
                    "completion_criteria",
                ),
                "estimated_minutes": estimated_minutes,
                "status": "todo",
                "sort_order": sort_order,
            }
        )
    return normalized


def _single_plan_response(
    store: KnowledgeStore,
    plan: CoachLearningPlan,
) -> dict[str, Any]:
    try:
        current = current_coach_analysis(store, plan.project_id)
    except ValueError:
        current = None
    current_run_id = current.id if current else ""
    current_status = current.status if current else "missing"
    sources = _sources_for_plans(store, [plan])
    latest_draft = _latest_plan(store, plan.project_id, "draft")
    return {
        "plan": _plan_view(
            plan,
            current_run_id,
            current_status,
            sources,
            is_current_draft=bool(
                plan.status == "draft"
                and latest_draft
                and latest_draft.id == plan.id
            ),
        ),
        "sources": sources,
        "scope_notice": PLAN_SCOPE_NOTICE,
    }


def _plan_view(
    plan: CoachLearningPlan,
    current_run_id: str,
    current_status: str,
    sources: Mapping[str, Mapping[str, Any]],
    *,
    is_current_draft: bool = False,
) -> dict[str, Any]:
    payload = plan.to_dict()
    for item in payload["items"]:
        item["reading_sources"] = [
            dict(sources[source_id])
            for source_id in item["source_ids"]
            if source_id in sources
        ]
    is_current_run = (
        plan.based_on_run_id == current_run_id
        and current_status == "completed"
    )
    payload.update(
        {
            "items_hash": learning_plan_items_hash(plan),
            "progress_hash": learning_plan_progress_hash(plan),
            "analysis_status": (
                "completed" if is_current_run else "stale"
            ),
            "based_on_current_analysis": is_current_run,
            "can_edit_structure": (
                plan.status == "draft"
                and is_current_draft
                and is_current_run
            ),
            "can_update_progress": plan.status == "confirmed",
            "can_confirm": (
                plan.status == "draft"
                and is_current_draft
                and is_current_run
            ),
        }
    )
    return payload


def _sources_for_plans(
    store: KnowledgeStore,
    plans: Iterable[CoachLearningPlan],
) -> dict[str, dict[str, Any]]:
    plan_list = list(plans)
    result: dict[str, dict[str, Any]] = {}
    project_by_run = {
        plan.based_on_run_id: plan.project_id
        for plan in plan_list
    }
    for run_id, project_id in project_by_run.items():
        for point in store.list_coach_knowledge_points(
            project_id,
            run_id=run_id,
        ):
            for source in point.sources:
                payload = source.to_dict()
                payload["path"] = payload.pop("source_path")
                result[source.id] = payload
    return result


def _latest_plan(
    store: KnowledgeStore,
    project_id: str,
    status: str,
) -> CoachLearningPlan | None:
    plans = store.list_coach_learning_plans(
        project_id,
        status=status,
        limit=1,
    )
    return plans[0] if plans else None


def _require_plan(
    store: KnowledgeStore,
    project_id: str,
    plan_id: str,
) -> CoachLearningPlan:
    clean_plan_id = plan_id.strip()
    if not clean_plan_id:
        raise ValueError("plan_id is required")
    plan = store.get_coach_learning_plan(project_id, clean_plan_id)
    if plan is None:
        raise CoachLearningPlanNotFoundError("learning plan not found")
    return plan


def _current_analysis(
    store: KnowledgeStore,
    project_id: str,
):
    try:
        return current_coach_analysis(store, project_id)
    except ValueError as exc:
        raise CoachLearningPlanNotFoundError(str(exc)) from exc


def _require_current_completed_run(
    store: KnowledgeStore,
    project_id: str,
    run_id: str,
) -> None:
    current = _current_analysis(store, project_id)
    if current.status != "completed" or current.id != run_id:
        raise CoachLearningPlanConflictError("analysis_stale")


def _check_expected_plan_version(
    plan: CoachLearningPlan,
    expected_revision: Any,
    expected_items_hash: str,
) -> None:
    if expected_revision is not None:
        if isinstance(expected_revision, bool):
            raise ValueError("expected_revision must be an integer")
        try:
            revision = int(expected_revision)
        except (TypeError, ValueError) as exc:
            raise ValueError("expected_revision must be an integer") from exc
        if revision != plan.revision:
            raise CoachLearningPlanConflictError(
                "learning_plan_revision_conflict"
            )
    clean_hash = str(expected_items_hash or "").strip()
    if clean_hash and clean_hash != learning_plan_items_hash(plan):
        raise CoachLearningPlanConflictError("learning_plan_items_conflict")


def _check_expected_progress(
    plan: CoachLearningPlan,
    expected_progress_hash: str,
) -> None:
    clean_hash = str(expected_progress_hash or "").strip()
    if clean_hash and clean_hash != learning_plan_progress_hash(plan):
        raise CoachLearningPlanConflictError("learning_plan_progress_conflict")


def _plan_limit(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("max_items must be an integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("max_items must be an integer") from exc
    if parsed < 1 or parsed > MAX_PLAN_ITEMS:
        raise ValueError(f"max_items must be between 1 and {MAX_PLAN_ITEMS}")
    return parsed


def _text_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field} must be an array")
    result = [str(item).strip() for item in value]
    if any(not item for item in result) or len(set(result)) != len(result):
        raise ValueError(f"{field} must contain unique non-empty values")
    return result


def _required_text(value: Any, field: str) -> str:
    clean = str(value or "").strip()
    if not clean:
        raise ValueError(f"{field} is required")
    if len(clean) > 4_000:
        raise ValueError(f"{field} must not exceed 4000 characters")
    return clean


def _enhanced_text(value: Any, field: str) -> str:
    clean = _required_text(value, field)
    if len(clean) > 1_000:
        raise ValueError(f"model {field} is too long")
    return clean


def _json_array(raw: str) -> list[Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end < start:
        raise ValueError("model learning plan is not JSON")
    payload = json.loads(text[start : end + 1])
    if not isinstance(payload, list):
        raise ValueError("model learning plan must be an array")
    return payload


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


__all__ = [
    "CoachLearningPlanConflictError",
    "CoachLearningPlanNotFoundError",
    "PLAN_SCOPE_NOTICE",
    "build_current_learning_plan",
    "confirm_learning_plan",
    "generate_learning_plan",
    "learning_plan_items_hash",
    "learning_plan_progress_hash",
    "update_learning_plan",
]
