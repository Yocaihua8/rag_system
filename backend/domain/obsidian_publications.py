from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from backend.domain.coach_assessment import build_coach_coverage
from backend.domain.learning_plans import build_current_learning_plan
from backend.domain.obsidian_models import (
    ObsidianConnection,
    ObsidianPublication,
)
from backend.domain.obsidian_protocol import (
    OBSIDIAN_ARTIFACT_TYPES,
    artifact_target_path,
    markdown_body,
    path_is_within_root,
    render_managed_markdown,
    stable_artifact_id,
    text_sha256,
)
from backend.domain.project_analysis import (
    build_coach_overview,
    build_knowledge_points_view,
    current_coach_analysis,
)
from backend.storage import KnowledgeStore


PUBLICATION_SCOPE_NOTICE = (
    "这些文件只描述当前项目和对应来源版本，不代表整体职业能力。"
)
DEFAULT_ARTIFACT_TYPES = (
    "project_understanding",
    "knowledge_coverage",
    "learning_plan",
    "assessment_record",
)
_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ObsidianPublicationNotFoundError(LookupError):
    pass


class ObsidianPublicationConflictError(RuntimeError):
    pass


class _PublicationCoordinator:
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


_publication_coordinator = _PublicationCoordinator()


def preview_obsidian_publication(
    store: KnowledgeStore,
    project_id: str,
    *,
    artifact_types: object = None,
    assessment_session_ids: object = None,
    source_publication_id: str = "",
) -> dict[str, Any]:
    connection = _active_connection(store, project_id)
    with _publication_coordinator.project_scope(project_id):
        next_revision = _next_revision(store, project_id)
        if source_publication_id.strip():
            artifacts = _rollback_artifacts(
                store,
                project_id,
                connection,
                source_publication_id.strip(),
                next_revision,
            )
            source_mode = "rollback"
        else:
            types = _artifact_types(artifact_types)
            session_ids = _session_ids(assessment_session_ids)
            artifacts = _current_artifacts(
                store,
                project_id,
                connection,
                next_revision,
                types,
                session_ids,
                assessment_explicit=artifact_types is not None,
            )
            source_mode = "current"
        publication = store.create_obsidian_publication(
            project_id,
            connection.id,
            artifacts,
        )
        if publication.revision != next_revision:
            raise RuntimeError("Obsidian publication revision changed concurrently")
        return {
            "publication": publication.to_dict(),
            "source_mode": source_mode,
            "scope_notice": PUBLICATION_SCOPE_NOTICE,
        }


def confirm_obsidian_publication(
    store: KnowledgeStore,
    project_id: str,
    publication_id: str,
) -> dict[str, Any]:
    with _publication_coordinator.project_scope(project_id):
        publication = _publication(store, project_id, publication_id)
        if publication.status == "queued":
            return {
                "publication": publication.to_dict(),
                "replayed": True,
            }
        if publication.status != "draft":
            raise ObsidianPublicationConflictError(
                "publication_not_confirmable"
            )
        connection = _active_connection(store, project_id)
        if connection.id != publication.connection_id:
            raise ObsidianPublicationConflictError(
                "publication_connection_inactive"
            )
        _validate_publication_artifacts(publication, connection)
        queued = store.confirm_obsidian_publication(
            project_id,
            publication.id,
        )
        if queued is None:
            raise ObsidianPublicationConflictError(
                "publication_not_confirmable"
            )
        return {
            "publication": queued.to_dict(),
            "replayed": False,
        }


def pending_obsidian_publications(
    store: KnowledgeStore,
    connection: ObsidianConnection,
) -> dict[str, Any]:
    return {
        "publications": [
            publication.to_dict()
            for publication in store.list_pending_obsidian_publications(
                connection.id
            )
        ]
    }


def record_obsidian_publication_result(
    store: KnowledgeStore,
    connection: ObsidianConnection,
    publication_id: object,
    results: object,
) -> dict[str, Any]:
    clean_publication_id = _required_text(
        publication_id,
        "publication_id",
    )
    if not isinstance(results, list) or not results:
        raise ValueError("results must be a non-empty array")
    normalized = [_publication_result(item) for item in results]
    try:
        publication, stored_results = (
            store.record_obsidian_publication_results(
                connection.project_id,
                connection.id,
                clean_publication_id,
                normalized,
            )
        )
    except ValueError as exc:
        message = str(exc)
        if "not found" in message:
            raise ObsidianPublicationNotFoundError(message) from exc
        raise ObsidianPublicationConflictError(message) from exc
    return {
        "publication": publication.to_dict(),
        "results": [item.to_dict() for item in stored_results],
    }


def _current_artifacts(
    store: KnowledgeStore,
    project_id: str,
    connection: ObsidianConnection,
    revision: int,
    artifact_types: list[str],
    assessment_session_ids: list[str],
    *,
    assessment_explicit: bool,
) -> list[dict[str, Any]]:
    run = current_coach_analysis(store, project_id)
    if run.status != "completed":
        raise ObsidianPublicationConflictError("analysis_stale")
    artifacts: list[dict[str, Any]] = []
    if "project_understanding" in artifact_types:
        stable_id = stable_artifact_id(
            project_id,
            "project_understanding",
        )
        body = _render_project_understanding(store, project_id)
        artifacts.append(
            _artifact(
                store,
                connection,
                revision,
                "project_understanding",
                stable_id,
                artifact_target_path(
                    connection.output_root,
                    "project_understanding",
                ),
                body,
            )
        )
    if "knowledge_coverage" in artifact_types:
        stable_id = stable_artifact_id(
            project_id,
            "knowledge_coverage",
        )
        body = _render_coverage(store, project_id)
        artifacts.append(
            _artifact(
                store,
                connection,
                revision,
                "knowledge_coverage",
                stable_id,
                artifact_target_path(
                    connection.output_root,
                    "knowledge_coverage",
                ),
                body,
            )
        )
    if "learning_plan" in artifact_types:
        stable_id = stable_artifact_id(project_id, "learning_plan")
        body = _render_learning_plan(store, project_id)
        artifacts.append(
            _artifact(
                store,
                connection,
                revision,
                "learning_plan",
                stable_id,
                artifact_target_path(
                    connection.output_root,
                    "learning_plan",
                ),
                body,
            )
        )
    if "assessment_record" in artifact_types:
        assessment_artifacts = _assessment_artifacts(
            store,
            project_id,
            connection,
            revision,
            assessment_session_ids,
        )
        if assessment_explicit and not assessment_artifacts:
            raise ObsidianPublicationConflictError(
                "assessment_records_not_found"
            )
        artifacts.extend(assessment_artifacts)
    if not artifacts:
        raise ObsidianPublicationConflictError(
            "publication_has_no_artifacts"
        )
    return artifacts


def _rollback_artifacts(
    store: KnowledgeStore,
    project_id: str,
    connection: ObsidianConnection,
    source_publication_id: str,
    revision: int,
) -> list[dict[str, Any]]:
    source = store.get_obsidian_publication(
        project_id,
        source_publication_id,
    )
    if source is None:
        raise ObsidianPublicationNotFoundError(
            "source Obsidian publication not found"
        )
    artifacts = []
    for previous in source.artifacts:
        if previous.artifact_type == "assessment_record":
            target_path = _assessment_rollback_path(
                connection.output_root,
                previous.target_path,
            )
        else:
            target_path = artifact_target_path(
                connection.output_root,
                previous.artifact_type,
            )
        artifacts.append(
            _artifact(
                store,
                connection,
                revision,
                previous.artifact_type,
                previous.stable_id,
                target_path,
                markdown_body(previous.content),
            )
        )
    if not artifacts:
        raise ObsidianPublicationConflictError(
            "source_publication_has_no_artifacts"
        )
    return artifacts


def _artifact(
    store: KnowledgeStore,
    connection: ObsidianConnection,
    revision: int,
    artifact_type: str,
    stable_id: str,
    target_path: str,
    body: str,
) -> dict[str, Any]:
    if not path_is_within_root(target_path, connection.output_root):
        raise ObsidianPublicationConflictError(
            "publication_path_outside_output_root"
        )
    content = render_managed_markdown(
        stable_id=stable_id,
        project_id=connection.project_id,
        artifact_type=artifact_type,
        revision=revision,
        body=body,
    )
    baseline = store.latest_obsidian_artifact_baseline(
        connection.project_id,
        connection.id,
        stable_id,
    )
    return {
        "artifact_type": artifact_type,
        "stable_id": stable_id,
        "target_path": target_path,
        "content": content,
        "content_hash": text_sha256(content),
        "expected_vault_hash": (
            str(baseline.get("actual_hash") or "") if baseline else ""
        ),
    }


def _render_project_understanding(
    store: KnowledgeStore,
    project_id: str,
) -> str:
    overview = build_coach_overview(store, project_id)
    points = build_knowledge_points_view(store, project_id)
    lines = [
        "# 项目理解",
        "",
        f"> {overview['scope_notice']}",
        "",
        str(overview["summary"]).strip() or "当前分析未生成摘要。",
        "",
        "## 项目信号",
        "",
    ]
    signals = overview.get("signals") or {}
    if isinstance(signals, Mapping) and signals:
        for key, value in sorted(signals.items()):
            lines.append(f"- **{key}**：{_display_value(value)}")
    else:
        lines.append("- 当前来源未提取到额外信号。")
    lines.extend(["", "## 项目知识点", ""])
    for point in points["items"]:
        lines.extend(
            [
                f"### {point['title']}",
                "",
                str(point["summary"]),
                "",
                f"- 分类：`{point['category']}`",
                f"- 稳定标识：`{point['stable_key']}`",
                f"- 来源：{_source_refs(point['source_ids'], points['sources'])}",
                "",
            ]
        )
    lines.extend(_sources_section(points["sources"]))
    return "\n".join(lines)


def _render_coverage(
    store: KnowledgeStore,
    project_id: str,
) -> str:
    coverage = build_coach_coverage(store, project_id)
    summary = coverage["summary"]
    lines = [
        "# 知识覆盖与技能差距",
        "",
        f"> {coverage['scope_notice']}",
        "",
        f"- 知识点总数：{summary['knowledge_point_count']}",
        f"- 已评估：{summary['assessed_count']}",
        f"- 未评估：{summary['unassessed_count']}",
        f"- 覆盖率：{summary['coverage_ratio']:.0%}",
        "",
        "## 项目知识覆盖",
        "",
    ]
    for point in coverage["knowledge_points"]:
        score = (
            f"{float(point['score']):.0%}"
            if point.get("score") is not None
            else "未验证"
        )
        confidence = (
            f"{float(point['confidence']):.0%}"
            if point.get("confidence") is not None
            else "N/A"
        )
        lines.extend(
            [
                f"### {point['title']}",
                "",
                f"- 状态：`{point['status']}`",
                f"- 分数：{score}",
                f"- 置信度：{confidence}",
                f"- 来源：{_source_refs(point['source_ids'], coverage['sources'])}",
                "",
            ]
        )
    lines.extend(["## 通用技能辅助视图", ""])
    for skill in coverage["skills"]:
        if skill["assessment_state"] == "no_project_evidence":
            continue
        lines.append(
            f"- **{skill['name']}**："
            f"`{skill['assessment_state']}` / "
            f"`{skill.get('status') or 'unassessed'}`，"
            f"验证 {skill['assessed_knowledge_point_count']}/"
            f"{skill['mapped_knowledge_point_count']}"
        )
    lines.extend(_sources_section(coverage["sources"]))
    return "\n".join(lines)


def _render_learning_plan(
    store: KnowledgeStore,
    project_id: str,
) -> str:
    current = build_current_learning_plan(store, project_id)
    plan = current.get("confirmed")
    if not plan:
        raise ObsidianPublicationConflictError(
            "confirmed_learning_plan_required"
        )
    lines = [
        "# 学习计划",
        "",
        f"> {current['scope_notice']}",
        "",
        f"- 计划版本：{plan['revision']}",
        f"- 状态：`{plan['status']}`",
        "",
    ]
    for index, item in enumerate(plan["items"], start=1):
        lines.extend(
            [
                f"## {index}. {item['objective']}",
                "",
                f"- 任务状态：`{item['status']}`",
                f"- 预计时长：{item['estimated_minutes']} 分钟",
                f"- 练习问题：{item['practice_question']}",
                f"- 完成标准：{item['completion_criteria']}",
                f"- 阅读来源：{_source_refs(item['source_ids'], current['sources'])}",
                "",
            ]
        )
    lines.extend(_sources_section(current["sources"]))
    return "\n".join(lines)


def _assessment_artifacts(
    store: KnowledgeStore,
    project_id: str,
    connection: ObsidianConnection,
    revision: int,
    requested_session_ids: list[str],
) -> list[dict[str, Any]]:
    sessions = store.list_coach_assessment_sessions(project_id, limit=500)
    if requested_session_ids:
        requested = set(requested_session_ids)
        sessions = [session for session in sessions if session.id in requested]
        if {session.id for session in sessions} != requested:
            raise ObsidianPublicationNotFoundError(
                "assessment session not found"
            )
    else:
        sessions = [session for session in sessions if session.status == "completed"][:20]
    results = store.list_coach_assessment_results(project_id, limit=1000)
    results_by_session: dict[str, list[Any]] = {}
    for result in results:
        results_by_session.setdefault(result.session_id, []).append(result)
    artifacts = []
    for session in sessions:
        session_results = results_by_session.get(session.id, [])
        if not session_results:
            continue
        timestamp = session.completed_at or session.created_at
        stable_id = stable_artifact_id(
            project_id,
            "assessment_record",
            session.id,
        )
        body, sources = _render_assessment_record(
            store,
            session,
            session_results,
        )
        artifacts.append(
            _artifact(
                store,
                connection,
                revision,
                "assessment_record",
                stable_id,
                artifact_target_path(
                    connection.output_root,
                    "assessment_record",
                    timestamp=timestamp,
                ),
                f"{body}\n{_sources_section_text(sources)}",
            )
        )
    return artifacts


def _render_assessment_record(
    store: KnowledgeStore,
    session: Any,
    results: list[Any],
) -> tuple[str, dict[str, Any]]:
    questions = {question.id: question for question in session.questions}
    answers = {
        answer.question_id: answer
        for answer in store.list_coach_assessment_answers(
            session.project_id,
            session.id,
        )
    }
    points = store.list_coach_knowledge_points(
        session.project_id,
        run_id=session.analysis_run_id,
    )
    sources = {
        source.id: {
            **source.to_dict(),
            "path": source.source_path,
        }
        for point in points
        for source in point.sources
    }
    lines = [
        "# 评估记录",
        "",
        "> 这是当前项目、当前来源版本下的评估结果，不代表整体职业能力。",
        "",
        f"- 会话：`{session.id}`",
        f"- 目标类型：`{session.target_type}`",
        f"- 目标 ID：`{session.target_id}`",
        f"- 完成时间：{session.completed_at or session.created_at}",
        "",
    ]
    for index, result in enumerate(results, start=1):
        question = questions.get(result.question_id)
        answer = answers.get(result.question_id)
        lines.extend(
            [
                f"## {index}. {question.prompt if question else '历史题目'}",
                "",
                f"- 回答：{answer.answer if answer else 'N/A'}",
                f"- 状态：`{result.status}`",
                f"- 评分方式：`{result.evaluator}`",
                f"- 分数：{result.score:.0%}",
                f"- 置信度：{result.confidence:.0%}",
                f"- 命中证据：{_matched_evidence(result.matched_evidence)}",
                f"- 缺失点：{', '.join(result.missing_points) or '无'}",
                f"- 来源：{_source_refs(result.source_ids, sources)}",
                "",
            ]
        )
    return "\n".join(lines), sources


def _validate_publication_artifacts(
    publication: ObsidianPublication,
    connection: ObsidianConnection,
) -> None:
    for artifact in publication.artifacts:
        if not path_is_within_root(
            artifact.target_path,
            connection.output_root,
        ):
            raise ObsidianPublicationConflictError(
                "publication_path_outside_output_root"
            )
        if text_sha256(artifact.content) != artifact.content_hash:
            raise ObsidianPublicationConflictError(
                "publication_content_hash_changed"
            )
        required = {
            "knowledge_island_managed: true",
            f'knowledge_island_id: "{artifact.stable_id}"',
            f'knowledge_island_project_id: "{publication.project_id}"',
            f'knowledge_island_artifact_type: "{artifact.artifact_type}"',
            f"knowledge_island_revision: {publication.revision}",
        }
        if not all(marker in artifact.content for marker in required):
            raise ObsidianPublicationConflictError(
                "publication_managed_metadata_invalid"
            )


def _publication_result(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ValueError("publication results must be objects")
    revision_id = _required_text(value.get("revision_id"), "revision_id")
    status = _required_text(value.get("status"), "status")
    if status not in {"applied", "conflict", "failed"}:
        raise ValueError("status must be applied, conflict or failed")
    actual_hash = str(value.get("actual_hash") or "").strip().casefold()
    if status == "applied" and not _HASH_PATTERN.fullmatch(actual_hash):
        raise ValueError("applied result requires a valid actual_hash")
    if actual_hash and not _HASH_PATTERN.fullmatch(actual_hash):
        raise ValueError("actual_hash must be a SHA-256 hash")
    error_code = str(value.get("error_code") or "").strip()[:120]
    message = str(value.get("message") or "").strip()[:1000]
    return {
        "revision_id": revision_id,
        "status": status,
        "actual_hash": actual_hash,
        "error_code": error_code,
        "message": message,
    }


def _publication(
    store: KnowledgeStore,
    project_id: str,
    publication_id: str,
) -> ObsidianPublication:
    clean_id = _required_text(publication_id, "publication_id")
    publication = store.get_obsidian_publication(project_id, clean_id)
    if publication is None:
        raise ObsidianPublicationNotFoundError(
            "Obsidian publication not found"
        )
    return publication


def _active_connection(
    store: KnowledgeStore,
    project_id: str,
) -> ObsidianConnection:
    if store.get_project(project_id) is None:
        raise ObsidianPublicationNotFoundError("project not found")
    connection = store.get_active_obsidian_connection(project_id)
    if connection is None:
        raise ObsidianPublicationConflictError(
            "active_obsidian_connection_required"
        )
    return connection


def _next_revision(store: KnowledgeStore, project_id: str) -> int:
    publications = store.list_obsidian_publications(project_id, limit=1)
    return publications[0].revision + 1 if publications else 1


def _artifact_types(value: object) -> list[str]:
    if value is None:
        return list(DEFAULT_ARTIFACT_TYPES)
    if not isinstance(value, list) or not value:
        raise ValueError("artifact_types must be a non-empty array")
    result = []
    for item in value:
        artifact_type = str(item or "").strip()
        if artifact_type not in OBSIDIAN_ARTIFACT_TYPES:
            raise ValueError("unsupported artifact_type")
        if artifact_type not in result:
            result.append(artifact_type)
    return result


def _session_ids(value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("assessment_session_ids must be an array")
    result = []
    for item in value:
        session_id = str(item or "").strip()
        if not session_id:
            raise ValueError(
                "assessment_session_ids must contain non-empty strings"
            )
        if session_id not in result:
            result.append(session_id)
    return result


def _assessment_rollback_path(output_root: str, previous_path: str) -> str:
    filename = previous_path.rsplit("/", 1)[-1]
    timestamp = filename.removesuffix(".md")
    return artifact_target_path(
        output_root,
        "assessment_record",
        timestamp=timestamp,
    )


def _source_refs(
    source_ids: Iterable[str],
    sources: Mapping[str, Mapping[str, Any]],
) -> str:
    refs = []
    for source_id in source_ids:
        source = sources.get(source_id)
        if source:
            refs.append(f"`{source.get('path') or source_id}`")
    return "、".join(refs) or "无"


def _sources_section(
    sources: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    return ["", *_sources_section_text(sources).splitlines()]


def _sources_section_text(
    sources: Mapping[str, Mapping[str, Any]],
) -> str:
    lines = ["## 来源", ""]
    if not sources:
        return "\n".join([*lines, "- 无"])
    for source_id, source in sorted(
        sources.items(),
        key=lambda item: str(item[1].get("path") or item[0]),
    ):
        lines.append(
            f"- `{source.get('path') or source_id}`"
            f"（source: `{source_id}`）"
        )
        excerpt = str(source.get("excerpt") or "").strip()
        if excerpt:
            lines.append(f"  > {excerpt.replace(chr(10), ' ')}")
    return "\n".join(lines)


def _matched_evidence(value: Iterable[Mapping[str, Any]]) -> str:
    matches = [
        str(item.get("evidence") or "").strip()
        for item in value
        if str(item.get("evidence") or "").strip()
    ]
    return "、".join(matches) or "无"


def _display_value(value: object) -> str:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value.strip()


__all__ = [
    "ObsidianPublicationConflictError",
    "ObsidianPublicationNotFoundError",
    "confirm_obsidian_publication",
    "pending_obsidian_publications",
    "preview_obsidian_publication",
    "record_obsidian_publication_result",
]
