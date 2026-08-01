from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from backend.domain.coach_assessment import (
    CoachAssessmentConflictError,
    _question_draft as coach_question_draft,
    _target_points as coach_target_points,
    score_coach_answer,
)
from backend.domain.coach_models import (
    CoachAssessmentQuestion,
    CoachKnowledgePoint,
    CoachLearningExercise,
    CoachLearningSession,
)
from backend.domain.learning_plans import learning_plan_progress_hash
from backend.domain.project_analysis import current_coach_analysis
from backend.storage import KnowledgeStore


MAX_LEARNING_ANSWER_CHARS = 20_000
LEARNING_COMPLETION_THRESHOLD = 0.75
LEARNING_MAX_ATTEMPTS = 3
LEARNING_TERMINAL_STATUSES = {"completed", "abandoned"}
LEARNING_TRANSITIONS = {
    "begin_learning": {"ready"},
    "begin_question": {"learning"},
    "retry": {"evaluated"},
    "next": {"evaluated"},
    "reveal": {"evaluated"},
    "abandon": {
        "ready",
        "learning",
        "awaiting_answer",
        "evaluated",
        "retrying",
    },
}
SQL_LIMITS = {
    "max_sql_chars": 10_000,
    "timeout_seconds": 1.0,
    "max_vm_steps": 1_000_000,
    "progress_ops": 1_000,
    "max_rows": 200,
    "max_columns": 32,
    "max_result_bytes": 256 * 1024,
    "max_tables": 8,
    "max_seed_rows": 1_000,
}


class CoachLearningNotFoundError(LookupError):
    pass


class CoachLearningConflictError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        session: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.session = session


def start_coach_learning_session(
    store: KnowledgeStore,
    project_id: str,
    target_type: str = "",
    target_id: str = "",
    *,
    plan_id: str = "",
    plan_item_id: str = "",
    origin_type: str = "coach",
) -> dict[str, Any]:
    run = _current_completed_analysis(store, project_id)
    resolved = _resolve_start_target(
        store,
        project_id,
        run.id,
        target_type=target_type,
        target_id=target_id,
        plan_id=plan_id,
        plan_item_id=plan_item_id,
        origin_type=origin_type,
    )
    active = store.get_active_coach_learning_session(project_id, run.id)
    if active is not None:
        if _same_start_target(active, resolved):
            return _session_view(store, active, resumed=True)
        raise CoachLearningConflictError(
            "learning_session_active_conflict",
            session=_session_view(store, active, resumed=True),
        )

    points = store.list_coach_knowledge_points(project_id, run_id=run.id)
    mappings = store.list_coach_skill_mappings(project_id, run_id=run.id)
    nodes = store.list_coach_skill_nodes()
    selected = coach_target_points(
        resolved["target_type"],
        resolved["target_id"],
        points,
        mappings,
        nodes,
    )[:3]
    if not selected:
        raise CoachLearningConflictError("learning_target_not_assessable")

    step_drafts = [
        _learning_step_draft(store, point, index)
        for index, point in enumerate(selected)
    ]
    current = current_coach_analysis(store, project_id)
    if current.status != "completed" or current.id != run.id:
        raise CoachLearningConflictError("analysis_stale")
    try:
        session = store.create_coach_learning_session(
            project_id,
            run.id,
            resolved["target_type"],
            resolved["target_id"],
            step_drafts,
            origin_type=resolved["origin_type"],
            plan_id=resolved["plan_id"],
            plan_item_id=resolved["plan_item_id"],
        )
    except ValueError as exc:
        if str(exc) != "learning_session_active_conflict":
            raise
        active = store.get_active_coach_learning_session(project_id, run.id)
        if active is not None and _same_start_target(active, resolved):
            return _session_view(store, active, resumed=True)
        raise CoachLearningConflictError(
            "learning_session_active_conflict",
            session=(
                _session_view(store, active, resumed=True)
                if active is not None
                else None
            ),
        ) from exc
    return _session_view(store, session, resumed=False)


def get_current_coach_learning_session(
    store: KnowledgeStore,
    project_id: str,
    *,
    session_id: str = "",
) -> dict[str, Any] | None:
    clean_session_id = str(session_id or "").strip()
    if clean_session_id:
        session = store.get_coach_learning_session(project_id, clean_session_id)
        if session is None:
            raise CoachLearningNotFoundError("coach learning session not found")
        return _session_view(store, session, resumed=True)
    try:
        run = current_coach_analysis(store, project_id)
    except ValueError as exc:
        raise CoachLearningNotFoundError(str(exc)) from exc
    session = store.get_active_coach_learning_session(project_id, run.id)
    return _session_view(store, session, resumed=True) if session else None


def transition_coach_learning_session(
    store: KnowledgeStore,
    project_id: str,
    session_id: str,
    action: str,
    expected_version: int,
) -> dict[str, Any]:
    session = _require_session(store, project_id, session_id)
    _require_writable(store, session)
    clean_action = str(action or "").strip()
    if clean_action not in LEARNING_TRANSITIONS:
        raise ValueError(
            "action must be begin_learning, begin_question, retry, next, "
            "reveal or abandon"
        )
    _check_expected_version(store, session, expected_version)
    if session.status not in LEARNING_TRANSITIONS[clean_action]:
        raise CoachLearningConflictError(
            "learning_session_invalid_transition",
            session=_session_view(store, session),
        )
    step = session.current_step
    if step is None:
        raise CoachLearningConflictError("learning_session_has_no_current_step")

    transition_kwargs: dict[str, Any] = {
        "step_id": step.id,
    }
    if clean_action == "begin_learning":
        next_status = "learning"
        transition_kwargs["step_status"] = "learning"
    elif clean_action == "begin_question":
        next_status = "awaiting_answer"
        transition_kwargs["step_status"] = "awaiting_answer"
    elif clean_action == "retry":
        if _step_has_valid_mastery(step):
            raise CoachLearningConflictError("learning_step_already_mastered")
        if len(step.attempts) >= step.max_attempts:
            raise CoachLearningConflictError("learning_attempt_limit_reached")
        next_status = "retrying"
        transition_kwargs["step_status"] = "retrying"
    elif clean_action == "reveal":
        if not step.attempts or _step_has_valid_mastery(step):
            raise CoachLearningConflictError("learning_answer_reveal_not_allowed")
        exercise = _last_attempt_exercise(step)
        if exercise is None:
            raise CoachLearningConflictError("learning_exercise_not_found")
        next_status = "evaluated"
        transition_kwargs["step_status"] = "evaluated"
        transition_kwargs["reveal_exercise_id"] = exercise.id
    elif clean_action == "abandon":
        next_status = "abandoned"
        transition_kwargs = {}
    else:
        return _advance_learning_session(
            store,
            session,
            expected_version,
        )

    try:
        stored = store.transition_coach_learning_session(
            project_id,
            session.id,
            expected_version,
            next_status,
            **transition_kwargs,
        )
    except ValueError as exc:
        _raise_store_conflict(store, project_id, session.id, exc)
        raise
    return _session_view(store, stored)


def submit_coach_learning_attempt(
    store: KnowledgeStore,
    project_id: str,
    session_id: str,
    exercise_id: str,
    answer: str,
    expected_version: int,
    idempotency_key: str,
) -> dict[str, Any]:
    raw_answer = str(answer)
    if not raw_answer.strip():
        raise ValueError("answer is required")
    if len(raw_answer) > MAX_LEARNING_ANSWER_CHARS:
        raise ValueError(
            f"answer must not exceed {MAX_LEARNING_ANSWER_CHARS} characters"
        )
    clean_key = str(idempotency_key or "").strip()
    if not clean_key:
        raise ValueError("idempotency_key is required")

    session = _require_session(store, project_id, session_id)
    request_hash = _attempt_request_hash(
        session.id,
        str(exercise_id).strip(),
        raw_answer,
        expected_version,
    )
    existing_attempt = next(
        (
            attempt
            for candidate_step in session.steps
            for attempt in candidate_step.attempts
            if attempt.idempotency_key == clean_key
        ),
        None,
    )
    if existing_attempt is not None:
        if existing_attempt.request_hash != request_hash:
            raise CoachLearningConflictError(
                "idempotency_payload_conflict",
                session=_session_view(store, session, resumed=True),
            )
        attempt = existing_attempt
        reserved_session = session
        replayed = True
        step = next(
            candidate
            for candidate in session.steps
            if candidate.id == attempt.step_id
        )
        current_exercise = next(
            candidate
            for candidate in step.exercises
            if candidate.id == attempt.exercise_id
        )
    else:
        _require_writable(store, session)
        _check_expected_version(store, session, expected_version)
        if session.status not in {"awaiting_answer", "retrying"}:
            raise CoachLearningConflictError(
                "learning_session_not_awaiting_answer",
                session=_session_view(store, session),
            )
        step = session.current_step
        if step is None:
            raise CoachLearningConflictError(
                "learning_session_has_no_current_step"
            )
        current_exercise = step.current_exercise
        if (
            current_exercise is None
            or current_exercise.id != str(exercise_id).strip()
        ):
            raise CoachLearningConflictError("learning_exercise_not_current")
        try:
            attempt, reserved_session, replayed = (
                store.reserve_coach_learning_attempt(
                    project_id,
                    session.id,
                    current_exercise.id,
                    raw_answer,
                    expected_version,
                    clean_key,
                    request_hash,
                )
            )
        except ValueError as exc:
            _raise_store_conflict(store, project_id, session.id, exc)
            raise

    if attempt.status != "grading":
        return {
            "attempt": attempt.to_dict(),
            "session": _session_view(store, reserved_session, resumed=True),
            "replayed": True,
            "pending": False,
            "plan_sync": _plan_sync_view(store, reserved_session),
        }
    if replayed and (
        not _session_sources_current(store, reserved_session)
        or not _grading_attempt_expired(attempt.created_at)
    ):
        return {
            "attempt": attempt.to_dict(),
            "session": _session_view(store, reserved_session, resumed=True),
            "replayed": True,
            "pending": True,
            "plan_sync": _plan_sync_view(store, reserved_session),
        }

    grading = _grade_attempt(current_exercise, step, raw_answer)
    passed = float(grading["score"]) >= step.completion_threshold
    counts_for_mastery = not current_exercise.revealed_at
    if passed and counts_for_mastery:
        step_outcome = "mastered"
    elif passed:
        step_outcome = "assisted"
    elif attempt.attempt_no >= step.max_attempts:
        step_outcome = "needs_work"
    else:
        step_outcome = ""
    plan_status = "in_progress"
    if passed and counts_for_mastery and _would_master_all_steps(
        reserved_session,
        step.id,
    ):
        plan_status = "done"
    try:
        finalized, stored_session, plan_sync = (
            store.finalize_coach_learning_attempt(
                project_id,
                session.id,
                attempt.id,
                reserved_session.version,
                evaluator=str(grading["evaluator"]),
                score=float(grading["score"]),
                confidence=float(grading.get("confidence", 1.0)),
                feedback=str(grading["feedback"]),
                error_code=str(grading.get("error_code") or ""),
                error_message=str(grading.get("error_message") or ""),
                result_preview=grading.get("result_preview"),
                scoring_details=dict(grading.get("scoring_details") or {}),
                counts_for_mastery=counts_for_mastery,
                session_status="evaluated",
                step_status="evaluated",
                step_outcome=step_outcome or None,
                plan_item_status=plan_status,
            )
        )
    except ValueError as exc:
        _raise_store_conflict(store, project_id, session.id, exc)
        raise
    return {
        "attempt": finalized.to_dict(),
        "session": _session_view(store, stored_session),
        "replayed": replayed,
        "pending": False,
        "plan_sync": _plan_sync_view(
            store,
            stored_session,
            sync_result=plan_sync,
        ),
    }


def _advance_learning_session(
    store: KnowledgeStore,
    session: CoachLearningSession,
    expected_version: int,
) -> dict[str, Any]:
    step = session.current_step
    if step is None:
        raise CoachLearningConflictError("learning_session_has_no_current_step")
    mastered = _step_has_valid_mastery(step)
    attempts_exhausted = len(step.attempts) >= step.max_attempts
    assisted = any(
        attempt.score is not None
        and attempt.score >= step.completion_threshold
        for attempt in step.attempts
    )
    if not mastered and not attempts_exhausted and not assisted:
        raise CoachLearningConflictError("learning_step_not_complete")
    step_outcome = (
        "mastered" if mastered else "assisted" if assisted else "needs_work"
    )
    ordered_steps = sorted(session.steps, key=lambda item: (item.sort_order, item.id))
    current_index = next(
        index for index, item in enumerate(ordered_steps) if item.id == step.id
    )
    has_next = current_index + 1 < len(ordered_steps)
    if has_next:
        next_step = ordered_steps[current_index + 1]
        next_status = "learning"
        current_step_id: str | None = next_step.id
        outcome: str | None = None
    else:
        next_status = "completed"
        current_step_id = step.id
        outcomes = [
            (
                step_outcome
                if item.id == step.id
                else (
                    "mastered"
                    if _step_has_valid_mastery(item)
                    else item.outcome or "needs_work"
                )
            )
            for item in ordered_steps
        ]
        outcome = (
            "mastered"
            if outcomes and all(item == "mastered" for item in outcomes)
            else "assisted"
            if any(item == "assisted" for item in outcomes)
            else "needs_work"
        )
    try:
        stored = store.transition_coach_learning_session(
            session.project_id,
            session.id,
            expected_version,
            next_status,
            current_step_id=current_step_id,
            outcome=outcome,
            step_id=step.id,
            step_status="completed",
            step_outcome=step_outcome,
        )
    except ValueError as exc:
        _raise_store_conflict(store, session.project_id, session.id, exc)
        raise
    return _session_view(store, stored)


def _resolve_start_target(
    store: KnowledgeStore,
    project_id: str,
    run_id: str,
    *,
    target_type: str,
    target_id: str,
    plan_id: str,
    plan_item_id: str,
    origin_type: str,
) -> dict[str, str]:
    clean_plan_id = str(plan_id or "").strip()
    clean_plan_item_id = str(plan_item_id or "").strip()
    if clean_plan_id or clean_plan_item_id:
        if not clean_plan_id or not clean_plan_item_id:
            raise ValueError("plan_id and plan_item_id must be provided together")
        plan = store.get_coach_learning_plan(project_id, clean_plan_id)
        if plan is None:
            raise CoachLearningNotFoundError("learning plan not found")
        if plan.status != "confirmed":
            raise CoachLearningConflictError("learning_plan_not_confirmed")
        if plan.based_on_run_id != run_id:
            raise CoachLearningConflictError("analysis_stale")
        item = next(
            (candidate for candidate in plan.items if candidate.id == clean_plan_item_id),
            None,
        )
        if item is None:
            raise ValueError("plan item does not belong to learning plan")
        if item.item_type != "learning":
            raise CoachLearningConflictError("learning_plan_item_not_learnable")
        if item.knowledge_point_id:
            resolved_type = "knowledge_point"
            resolved_id = item.knowledge_point_id
        elif item.skill_node_id:
            resolved_type = "skill"
            resolved_id = item.skill_node_id
        else:
            raise CoachLearningConflictError("learning_plan_item_not_learnable")
        return {
            "target_type": resolved_type,
            "target_id": resolved_id,
            "origin_type": "learning_plan",
            "plan_id": clean_plan_id,
            "plan_item_id": clean_plan_item_id,
        }

    clean_target_type = str(target_type or "").strip()
    clean_target_id = str(target_id or "").strip()
    if clean_target_type not in {"knowledge_point", "skill"}:
        raise ValueError("target_type must be knowledge_point or skill")
    if not clean_target_id:
        raise ValueError("target_id is required")
    clean_origin = str(origin_type or "coach").strip()
    if clean_origin not in {"coach", "learning_map"}:
        raise ValueError("origin_type must be coach or learning_map")
    return {
        "target_type": clean_target_type,
        "target_id": clean_target_id,
        "origin_type": clean_origin,
        "plan_id": "",
        "plan_item_id": "",
    }


def _same_start_target(
    session: CoachLearningSession,
    target: Mapping[str, str],
) -> bool:
    return (
        session.target_type == target["target_type"]
        and session.target_id == target["target_id"]
        and session.origin_type == target["origin_type"]
        and session.plan_id == target["plan_id"]
        and session.plan_item_id == target["plan_item_id"]
    )


def _learning_step_draft(
    store: KnowledgeStore,
    point: CoachKnowledgePoint,
    sort_order: int,
) -> dict[str, Any]:
    source_ids = [source.id for source in point.sources]
    if not source_ids:
        raise CoachLearningConflictError("learning_target_not_assessable")
    sql_exercises = _sql_exercise_drafts(store, point)
    if sql_exercises:
        exercises = sql_exercises
    else:
        try:
            primary = coach_question_draft(point, 0)
        except CoachAssessmentConflictError as exc:
            raise CoachLearningConflictError(str(exc)) from exc
        reinforcement_prompt = (
            f"巩固题：请换一种表述，结合当前项目中的真实位置和运行关系，"
            f"再次说明“{point.title}”的职责与关键实现。"
        )
        exercises = [
            {
                "variant": "primary",
                "question_type": primary["question_type"],
                "prompt": primary["prompt"],
                "expected_points": primary["expected_points"],
                "reference_answer": "；".join(primary["expected_points"]),
                "sort_order": 0,
            },
            {
                "variant": "reinforcement",
                "question_type": primary["question_type"],
                "prompt": reinforcement_prompt,
                "expected_points": primary["expected_points"],
                "reference_answer": "；".join(primary["expected_points"]),
                "sort_order": 1,
            },
        ]
    return {
        "knowledge_point_id": point.id,
        "title": point.title,
        "explanation": point.summary,
        "completion_threshold": LEARNING_COMPLETION_THRESHOLD,
        "max_attempts": LEARNING_MAX_ATTEMPTS,
        "source_ids": source_ids,
        "sort_order": sort_order,
        "exercises": exercises,
    }


def _sql_exercise_drafts(
    store: KnowledgeStore,
    point: CoachKnowledgePoint,
) -> list[dict[str, Any]]:
    try:
        import backend.domain.sql_learning  # noqa: F401
    except ImportError:
        return []
    documents = {
        document.id: document
        for document in store.list_documents(point.project_id)
    }
    parsed_tables: list[dict[str, Any]] = []
    for source in point.sources:
        texts = [source.excerpt]
        document = documents.get(source.document_id)
        if document is not None and document.checksum == source.source_hash:
            texts.append(document.content)
        for text in texts:
            parsed_tables = _parse_sqlite_tables(text)
            if parsed_tables:
                break
        if parsed_tables:
            break
    safe_tables = [
        table
        for table in parsed_tables
        if table["columns"]
        and not any(
            column["type"] == "BLOB"
            for column in table["columns"]
        )
    ][:2]
    if not safe_tables:
        return []
    exercises = (
        _relationship_sql_exercises(safe_tables)
        or _single_table_sql_exercises(safe_tables[0])
    )
    try:
        from backend.domain.sql_learning import grade_sql_query

        if any(
            not grade_sql_query(
                draft["sql_fixture"],
                str(draft["reference_answer"]),
            )["passed"]
            for draft in exercises
        ):
            return []
    except (TypeError, ValueError):
        return []
    return exercises


def _single_table_sql_exercises(
    table: Mapping[str, Any],
) -> list[dict[str, Any]]:
    table_name = str(table["name"])
    columns = list(table["columns"])
    selected = columns[: min(2, len(columns))]
    nullable = next(
        (
            column
            for column in columns
            if column["nullable"] and not column.get("primary_key")
        ),
        None,
    )
    numeric = next(
        (
            column
            for column in columns
            if column["type"] in {"INTEGER", "REAL", "NUMERIC"}
            and not column.get("primary_key")
        ),
        next(
            (
                column
                for column in columns
                if column["type"] in {"INTEGER", "REAL", "NUMERIC"}
            ),
            None,
        ),
    )
    filter_column = nullable or numeric or columns[0]
    rows = _synthetic_table_rows(table)
    if nullable is not None:
        predicate = f'"{filter_column["name"]}" IS NULL'
        matching = [
            row
            for row in rows
            if row[filter_column["name"]] is None
        ]
    elif numeric is not None:
        predicate = f'"{filter_column["name"]}" >= 2'
        matching = [
            row
            for row in rows
            if row[filter_column["name"]] is not None
            and float(row[filter_column["name"]]) >= 2
        ]
    else:
        expected = str(rows[1][filter_column["name"]])
        predicate = f'"{filter_column["name"]}" = \'{expected}\''
        matching = [
            row
            for row in rows
            if row[filter_column["name"]] == expected
        ]
    selected_names = [str(column["name"]) for column in selected]
    select_list = ", ".join(f'"{name}"' for name in selected_names)
    primary = _sql_exercise(
        variant="primary",
        sort_order=0,
        prompt=(
            f"使用下方明确标注的练习数据，查询 `{table_name}`，"
            f"按条件 `{predicate}` 筛选，并依次返回 "
            f"{', '.join(selected_names)} 列。"
        ),
        reference=(
            f'SELECT {select_list} FROM "{table_name}" '
            f"WHERE {predicate}"
        ),
        tables=[table],
        seed_rows={table_name: rows},
        expected_columns=selected_names,
        expected_rows=[
            [row[name] for name in selected_names]
            for row in matching
        ],
        order_sensitive=False,
        required_semantics={
            "tables": [table_name],
            "clauses": ["where"],
            "functions": [],
            "columns": [
                f"{table_name}.{name}"
                for name in selected_names
            ],
            "where_columns": [
                f"{table_name}.{filter_column['name']}"
            ],
        },
    )
    if numeric is not None:
        aggregate_predicate = f'"{numeric["name"]}" IS NOT NULL'
        aggregate_count = sum(
            row[numeric["name"]] is not None
            for row in rows
        )
        reinforcement = _sql_exercise(
            variant="reinforcement",
            sort_order=1,
            prompt=(
                f"巩固题：统计 `{table_name}` 练习表中 "
                f"`{numeric['name']}` 非 NULL 的行数，结果列命名为 "
                "`row_count`。"
            ),
            reference=(
                f'SELECT COUNT(*) AS row_count FROM "{table_name}" '
                f"WHERE {aggregate_predicate}"
            ),
            tables=[table],
            seed_rows={table_name: rows},
            expected_columns=["row_count"],
            expected_rows=[[aggregate_count]],
            order_sensitive=False,
            required_semantics={
                "tables": [table_name],
                "clauses": ["where"],
                "functions": ["count"],
                "where_columns": [
                    f"{table_name}.{numeric['name']}"
                ],
            },
        )
    else:
        order_column = selected_names[0]
        sorted_rows = sorted(
            rows,
            key=lambda row: (
                row[order_column] is not None,
                str(row[order_column] or ""),
            ),
        )
        reinforcement = _sql_exercise(
            variant="reinforcement",
            sort_order=1,
            prompt=(
                f"巩固题：查询 `{table_name}` 的 "
                f"{', '.join(selected_names)} 列，并按 `{order_column}` "
                "升序返回。"
            ),
            reference=(
                f'SELECT {select_list} FROM "{table_name}" '
                f'ORDER BY "{order_column}" ASC'
            ),
            tables=[table],
            seed_rows={table_name: rows},
            expected_columns=selected_names,
            expected_rows=[
                [row[name] for name in selected_names]
                for row in sorted_rows
            ],
            order_sensitive=True,
            required_semantics={
                "tables": [table_name],
                "clauses": ["order_by"],
                "functions": [],
                "columns": [
                    f"{table_name}.{name}"
                    for name in selected_names
                ],
            },
        )
    return [primary, reinforcement]


def _relationship_sql_exercises(
    tables: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    table_by_name = {
        str(table["name"]).casefold(): table
        for table in tables
    }
    relationship = next(
        (
            (child, foreign_key, table_by_name[foreign_key["table"].casefold()])
            for child in tables
            for foreign_key in child.get("foreign_keys", ())
            if foreign_key["table"].casefold() in table_by_name
        ),
        None,
    )
    if relationship is None:
        return []
    child, foreign_key, parent = relationship
    child_name = str(child["name"])
    parent_name = str(parent["name"])
    parent_key = next(
        (
            column
            for column in parent["columns"]
            if column["name"].casefold()
            == foreign_key["referenced_column"].casefold()
        ),
        None,
    )
    child_key = next(
        (
            column
            for column in child["columns"]
            if column["name"].casefold()
            == foreign_key["column"].casefold()
        ),
        None,
    )
    if parent_key is None or child_key is None:
        return []
    parent_label = next(
        (
            column
            for column in parent["columns"]
            if column["type"] == "TEXT"
        ),
        parent_key,
    )
    measure = next(
        (
            column
            for column in child["columns"]
            if column["type"] in {"INTEGER", "REAL", "NUMERIC"}
            and column["name"] != child_key["name"]
            and not column.get("primary_key")
        ),
        next(
            (
                column
                for column in child["columns"]
                if column["type"] in {"INTEGER", "REAL", "NUMERIC"}
                and column["name"] != child_key["name"]
            ),
            None,
        ),
    )
    if measure is None:
        return []
    parent_rows = _synthetic_table_rows(parent)
    parent_values = [
        row[parent_key["name"]]
        for row in parent_rows
        if row[parent_key["name"]] is not None
    ]
    if len(parent_values) < 2:
        return []
    child_rows = _synthetic_table_rows(
        child,
        overrides={
            child_key["name"]: (
                parent_values[0],
                parent_values[0],
                parent_values[1],
            ),
            measure["name"]: tuple(
                _synthetic_sql_value(
                    {
                        **measure,
                        "nullable": False,
                    },
                    index,
                )
                for index in range(1, 4)
            ),
        },
    )
    grouped: dict[Any, float] = {}
    labels: dict[Any, Any] = {
        row[parent_key["name"]]: row[parent_label["name"]]
        for row in parent_rows
    }
    for row in child_rows:
        key = row[child_key["name"]]
        value = row[measure["name"]]
        if key is None or value is None:
            continue
        grouped[key] = grouped.get(key, 0.0) + float(value)
    expected_aggregate = [
        [labels[key], int(total) if total.is_integer() else total]
        for key, total in grouped.items()
    ]
    schema_tables = [parent, child]
    seeds = {
        parent_name: parent_rows,
        child_name: child_rows,
    }
    join_columns = [
        f"{parent_name}.{parent_key['name']}",
        f"{child_name}.{child_key['name']}",
    ]
    primary = _sql_exercise(
        variant="primary",
        sort_order=0,
        prompt=(
            f"使用下方练习数据连接 `{parent_name}` 与 `{child_name}`，"
            f"按 `{parent_label['name']}` 分组汇总 `{measure['name']}`，"
            "结果列依次命名为 `group_name`、`total_value`。"
        ),
        reference=(
            f'SELECT p."{parent_label["name"]}" AS group_name, '
            f'SUM(c."{measure["name"]}") AS total_value '
            f'FROM "{parent_name}" AS p '
            f'JOIN "{child_name}" AS c '
            f'ON c."{child_key["name"]}" = p."{parent_key["name"]}" '
            f'GROUP BY p."{parent_label["name"]}"'
        ),
        tables=schema_tables,
        seed_rows=seeds,
        expected_columns=["group_name", "total_value"],
        expected_rows=expected_aggregate,
        order_sensitive=False,
        required_semantics={
            "tables": [parent_name, child_name],
            "clauses": ["join", "group_by"],
            "functions": ["sum"],
            "columns": [
                f"{parent_name}.{parent_label['name']}",
                f"{child_name}.{measure['name']}",
            ],
            "group_by_columns": [
                f"{parent_name}.{parent_label['name']}"
            ],
            "join_columns": join_columns,
        },
    )
    first_parent_value = parent_values[0]
    filtered_children = [
        row
        for row in child_rows
        if row[child_key["name"]] == first_parent_value
    ]
    filtered_children.sort(
        key=lambda row: str(row[measure["name"]] or "")
    )
    reinforcement = _sql_exercise(
        variant="reinforcement",
        sort_order=1,
        prompt=(
            f"巩固题：连接 `{parent_name}` 与 `{child_name}`，仅保留 "
            f"`{parent_key['name']}` 等于 {first_parent_value} 的数据，"
            f"返回 `group_name`、`{measure['name']}`，并按 "
            f"`{measure['name']}` 升序。"
        ),
        reference=(
            f'SELECT p."{parent_label["name"]}" AS group_name, '
            f'c."{measure["name"]}" '
            f'FROM "{parent_name}" AS p '
            f'JOIN "{child_name}" AS c '
            f'ON c."{child_key["name"]}" = p."{parent_key["name"]}" '
            f'WHERE p."{parent_key["name"]}" = '
            f"{_sql_literal(first_parent_value)} "
            f'ORDER BY c."{measure["name"]}" ASC'
        ),
        tables=schema_tables,
        seed_rows=seeds,
        expected_columns=["group_name", measure["name"]],
        expected_rows=[
            [labels[first_parent_value], row[measure["name"]]]
            for row in filtered_children
        ],
        order_sensitive=True,
        required_semantics={
            "tables": [parent_name, child_name],
            "clauses": ["join", "where", "order_by"],
            "functions": [],
            "columns": [
                f"{parent_name}.{parent_label['name']}",
                f"{child_name}.{measure['name']}",
            ],
            "where_columns": [
                f"{parent_name}.{parent_key['name']}"
            ],
            "join_columns": join_columns,
        },
    )
    return [primary, reinforcement]


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def _sql_exercise(
    *,
    variant: str,
    sort_order: int,
    prompt: str,
    reference: str,
    tables: list[Mapping[str, Any]],
    seed_rows: Mapping[str, list[dict[str, Any]]],
    expected_columns: list[str],
    expected_rows: list[list[Any]],
    order_sensitive: bool,
    required_semantics: Mapping[str, Any],
) -> dict[str, Any]:
    schema = [
        {
            "name": str(table["name"]),
            "columns": [
                {
                    "name": str(column["name"]),
                    "type": str(column["type"]),
                    "nullable": bool(column["nullable"]),
                }
                for column in table["columns"]
            ],
        }
        for table in tables
    ]
    fixture: dict[str, Any] = {
        "schema": schema,
        "seed_rows": {
            str(table_name): [dict(row) for row in rows]
            for table_name, rows in seed_rows.items()
        },
        "expected_columns": list(expected_columns),
        "expected_rows": [list(row) for row in expected_rows],
        "order_sensitive": order_sensitive,
        "required_semantics": dict(required_semantics),
        "limits": SQL_LIMITS,
    }
    fixture["fixture_hash"] = _fixture_hash(fixture)
    return {
        "variant": variant,
        "question_type": "sql_query",
        "prompt": prompt,
        "expected_points": [],
        "reference_answer": reference,
        "sort_order": sort_order,
        "sql_fixture": fixture,
    }


def _parse_sqlite_tables(text: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*;",
        flags=re.IGNORECASE | re.DOTALL,
    )
    tables: list[dict[str, Any]] = []
    for match in pattern.finditer(str(text or "")):
        columns: list[dict[str, Any]] = []
        foreign_keys: list[dict[str, str]] = []
        for definition in _split_sql_definitions(match.group(2)):
            clean = definition.strip()
            if not clean:
                continue
            foreign_match = re.search(
                r"\bFOREIGN\s+KEY\s*\(\s*"
                r"([A-Za-z_][A-Za-z0-9_]*)\s*\)\s*"
                r"REFERENCES\s+([A-Za-z_][A-Za-z0-9_]*)\s*"
                r"\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)",
                clean,
                flags=re.IGNORECASE,
            )
            if foreign_match:
                foreign_keys.append(
                    {
                        "column": foreign_match.group(1),
                        "table": foreign_match.group(2),
                        "referenced_column": foreign_match.group(3),
                    }
                )
                continue
            first = clean.split(None, 1)[0].casefold()
            if first in {
                "constraint",
                "foreign",
                "primary",
                "unique",
                "check",
            }:
                continue
            column_match = re.match(
                r"^([A-Za-z_][A-Za-z0-9_]*)"
                r"(?:\s+([A-Za-z]+))?(.*)$",
                clean,
                flags=re.DOTALL,
            )
            if not column_match:
                columns = []
                break
            raw_type = (column_match.group(2) or "TEXT").upper()
            data_type = _normalized_sqlite_type(raw_type)
            suffix = column_match.group(3)
            inline_reference = re.search(
                r"\bREFERENCES\s+([A-Za-z_][A-Za-z0-9_]*)\s*"
                r"\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)",
                suffix,
                flags=re.IGNORECASE,
            )
            if inline_reference:
                foreign_keys.append(
                    {
                        "column": column_match.group(1),
                        "table": inline_reference.group(1),
                        "referenced_column": inline_reference.group(2),
                    }
                )
            columns.append(
                {
                    "name": column_match.group(1),
                    "type": data_type,
                    "nullable": (
                        "NOT NULL" not in suffix.upper()
                        and "PRIMARY KEY" not in suffix.upper()
                    ),
                    "primary_key": "PRIMARY KEY" in suffix.upper(),
                }
            )
        if columns:
            tables.append(
                {
                    "name": match.group(1),
                    "columns": columns[:32],
                    "foreign_keys": foreign_keys,
                }
            )
    return tables


def _split_sql_definitions(value: str) -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote = ""
    for index, character in enumerate(value):
        if quote:
            if character == quote:
                quote = ""
            continue
        if character in {"'", '"', "`"}:
            quote = character
        elif character == "(":
            depth += 1
        elif character == ")":
            depth = max(0, depth - 1)
        elif character == "," and depth == 0:
            parts.append(value[start:index])
            start = index + 1
    parts.append(value[start:])
    return parts


def _normalized_sqlite_type(raw_type: str) -> str:
    folded = raw_type.upper()
    if "INT" in folded:
        return "INTEGER"
    if any(token in folded for token in ("REAL", "FLOA", "DOUB")):
        return "REAL"
    if any(token in folded for token in ("NUM", "DEC", "BOOL")):
        return "NUMERIC"
    if "BLOB" in folded:
        return "BLOB"
    return "TEXT"


def _synthetic_table_rows(
    table: Mapping[str, Any],
    *,
    overrides: Mapping[str, tuple[Any, ...]] | None = None,
) -> list[dict[str, Any]]:
    values = dict(overrides or {})
    return [
        {
            column["name"]: (
                values[column["name"]][index - 1]
                if column["name"] in values
                else _synthetic_sql_value(column, index)
            )
            for column in table["columns"]
        }
        for index in range(1, 4)
    ]


def _synthetic_sql_value(column: Mapping[str, Any], index: int) -> Any:
    data_type = str(column["type"])
    name = str(column["name"])
    if (
        index == 3
        and bool(column.get("nullable"))
        and not bool(column.get("primary_key"))
    ):
        return None
    if data_type == "INTEGER":
        return index
    if data_type in {"REAL", "NUMERIC"}:
        return float(index)
    if data_type == "BLOB":
        return f"{name}-{index}".encode("utf-8")
    return f"{name}_{index}"


def _fixture_hash(fixture: Mapping[str, Any]) -> str:
    raw = json.dumps(
        fixture,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=lambda value: (
            {"type": "blob", "hex": value.hex()}
            if isinstance(value, bytes)
            else str(value)
        ),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _grade_attempt(
    exercise: CoachLearningExercise,
    step: Any,
    answer: str,
) -> dict[str, Any]:
    if exercise.question_type == "sql_query":
        from backend.domain.sql_learning import grade_sql_query

        if exercise.sql_fixture is None:
            raise RuntimeError("sql exercise has no fixture")
        fixture = exercise.sql_fixture.to_dict(include_scoring_basis=True)
        result = grade_sql_query(fixture, answer)
        return {
            "evaluator": "sql",
            "score": float(result["score"]),
            "confidence": 1.0,
            "feedback": str(result["feedback"]),
            "error_code": str(result.get("error_code") or ""),
            "error_message": (
                str(result["feedback"]) if result.get("error_code") else ""
            ),
            "result_preview": {
                "columns": list(result.get("columns") or ()),
                "rows": list(result.get("rows") or ()),
                "row_count": int(result.get("row_count") or 0),
                "truncated": bool(result.get("truncated")),
            },
            "scoring_details": {
                "semantic_failures": list(
                    result.get("semantic_failures") or ()
                ),
                "differences": dict(result.get("differences") or {}),
                "used_tables": list(result.get("used_tables") or ()),
                "used_functions": list(result.get("used_functions") or ()),
            },
        }

    question = CoachAssessmentQuestion(
        id=exercise.id,
        session_id=step.session_id,
        knowledge_point_id=step.knowledge_point_id,
        prompt=exercise.prompt,
        question_type=exercise.question_type,
        expected_points=exercise.expected_points,
        source_ids=step.source_ids,
        sort_order=exercise.sort_order,
    )
    result = score_coach_answer(question, answer)
    missing = list(result["missing_points"])
    feedback = str(result["feedback"])
    if missing:
        feedback += " 尚未覆盖：" + "、".join(missing[:5]) + "。"
    return {
        "evaluator": "rule",
        "score": float(result["score"]),
        "confidence": float(result["confidence"]),
        "feedback": feedback,
        "error_code": "" if float(result["score"]) >= 1.0 else "missing_points",
        "error_message": "",
        "result_preview": None,
        "scoring_details": {
            "matched_evidence": list(result["matched_evidence"]),
            "missing_points": missing,
        },
    }


def _session_view(
    store: KnowledgeStore,
    session: CoachLearningSession,
    *,
    resumed: bool = False,
) -> dict[str, Any]:
    read_only = (
        session.status in LEARNING_TERMINAL_STATUSES
        or not _session_sources_current(store, session)
    )
    step = session.current_step
    visible_exercise = _visible_exercise(session)
    attempts = list(step.attempts) if step is not None else []
    sources = _sources_for_step(store, session, step)
    current_step = None
    if step is not None:
        current_step = {
            "id": step.id,
            "knowledge_point_id": step.knowledge_point_id,
            "title": step.title,
            "explanation": step.explanation,
            "completion_threshold": step.completion_threshold,
            "max_attempts": step.max_attempts,
            "status": step.status,
            "outcome": step.outcome,
            "sort_order": step.sort_order,
            "source_ids": list(step.source_ids),
            "attempt_count": len(step.attempts),
            "current_exercise": (
                _exercise_view(visible_exercise)
                if visible_exercise is not None
                else None
            ),
        }
    allowed_actions = (
        [] if read_only else _allowed_actions(session, step)
    )
    result = {
        "id": session.id,
        "project_id": session.project_id,
        "analysis_run_id": session.analysis_run_id,
        "target_type": session.target_type,
        "target_id": session.target_id,
        "origin_type": session.origin_type,
        "plan_id": session.plan_id,
        "plan_item_id": session.plan_item_id,
        "status": session.status,
        "version": session.version,
        "outcome": session.outcome,
        "read_only": read_only,
        "resumed": resumed,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "completed_at": session.completed_at,
        "abandoned_at": session.abandoned_at,
        "progress": _progress_view(session),
        "current_step": current_step,
        "current_exercise": (
            _exercise_view(visible_exercise)
            if visible_exercise is not None
            else None
        ),
        "attempts": [attempt.to_dict() for attempt in attempts],
        "allowed_actions": allowed_actions,
        "recommended_action": (
            allowed_actions[0] if allowed_actions else ""
        ),
        "sources": sources,
        "plan_sync": _plan_sync_view(store, session),
    }
    return result


def _exercise_view(exercise: CoachLearningExercise) -> dict[str, Any]:
    revealed = bool(exercise.revealed_at)
    payload = exercise.to_dict(include_scoring_basis=revealed)
    payload["variant_no"] = (
        2 if exercise.variant == "reinforcement" else 1
    )
    if exercise.sql_fixture is not None and not revealed:
        payload["sql_fixture"] = exercise.sql_fixture.to_dict(
            include_scoring_basis=False
        )
    return payload


def _visible_exercise(
    session: CoachLearningSession,
) -> CoachLearningExercise | None:
    step = session.current_step
    if step is None:
        return None
    if session.status in {"ready", "learning", "completed", "abandoned"}:
        return None
    if session.status == "evaluated" and step.attempts:
        exercise_id = step.attempts[-1].exercise_id
        return next(
            (
                exercise
                for exercise in step.exercises
                if exercise.id == exercise_id
            ),
            None,
        )
    return step.current_exercise


def _allowed_actions(
    session: CoachLearningSession,
    step: Any,
) -> list[str]:
    if session.status in LEARNING_TERMINAL_STATUSES or step is None:
        return []
    if session.status == "ready":
        return ["begin_learning", "abandon"]
    if session.status == "learning":
        return ["begin_question", "abandon"]
    if session.status in {"awaiting_answer", "retrying"}:
        return ["submit", "abandon"]
    if session.status != "evaluated":
        return []
    if _step_has_valid_mastery(step):
        return ["next", "abandon"]
    if any(
        attempt.score is not None
        and attempt.score >= step.completion_threshold
        for attempt in step.attempts
    ):
        return ["next", "abandon"]
    if len(step.attempts) >= step.max_attempts:
        return ["next", "abandon"]
    actions = ["retry"]
    exercise = _last_attempt_exercise(step)
    if exercise is not None and not exercise.revealed_at:
        actions.append("reveal")
    actions.append("abandon")
    return actions


def _progress_view(session: CoachLearningSession) -> dict[str, int]:
    ordered = sorted(session.steps, key=lambda item: (item.sort_order, item.id))
    step = session.current_step
    current = (
        next(
            (
                index + 1
                for index, item in enumerate(ordered)
                if step is not None and item.id == step.id
            ),
            0,
        )
        if ordered
        else 0
    )
    completed = sum(item.status == "completed" for item in ordered)
    if session.status == "completed":
        completed = len(ordered)
    return {
        "current": current,
        "completed": completed,
        "total": len(ordered),
    }


def _sources_for_step(
    store: KnowledgeStore,
    session: CoachLearningSession,
    step: Any,
) -> list[dict[str, Any]]:
    if step is None:
        return []
    points = store.list_coach_knowledge_points(
        session.project_id,
        run_id=session.analysis_run_id,
    )
    source_index = {
        source.id: source
        for point in points
        for source in point.sources
    }
    result = []
    for source_id in step.source_ids:
        source = source_index.get(source_id)
        if source is None:
            continue
        payload = source.to_dict()
        payload["path"] = payload["source_path"]
        result.append(payload)
    return result


def _plan_sync_view(
    store: KnowledgeStore,
    session: CoachLearningSession,
    *,
    sync_result: str = "",
) -> dict[str, Any]:
    if not session.plan_id or not session.plan_item_id:
        return {
            "linked": False,
            "status": "not_linked",
            "item_status": "",
            "progress_hash": "",
        }
    plan = store.get_coach_learning_plan(session.project_id, session.plan_id)
    item = (
        next(
            (
                candidate
                for candidate in plan.items
                if candidate.id == session.plan_item_id
            ),
            None,
        )
        if plan is not None
        else None
    )
    return {
        "linked": True,
        "status": sync_result or (
            "active"
            if plan is not None
            and plan.status == "confirmed"
            and plan.based_on_run_id == session.analysis_run_id
            and item is not None
            else "detached"
        ),
        "item_status": item.status if item is not None else "",
        "progress_hash": (
            learning_plan_progress_hash(plan) if plan is not None else ""
        ),
    }


def _current_completed_analysis(
    store: KnowledgeStore,
    project_id: str,
):
    try:
        run = current_coach_analysis(store, project_id)
    except ValueError as exc:
        raise CoachLearningNotFoundError(str(exc)) from exc
    if run.status != "completed":
        raise CoachLearningConflictError("analysis_stale")
    return run


def _require_session(
    store: KnowledgeStore,
    project_id: str,
    session_id: str,
) -> CoachLearningSession:
    clean_session_id = str(session_id or "").strip()
    if not clean_session_id:
        raise ValueError("session_id is required")
    session = store.get_coach_learning_session(project_id, clean_session_id)
    if session is None:
        raise CoachLearningNotFoundError("coach learning session not found")
    return session


def _require_writable(
    store: KnowledgeStore,
    session: CoachLearningSession,
) -> None:
    if not _session_sources_current(store, session):
        raise CoachLearningConflictError(
            "analysis_stale",
            session=_session_view(store, session),
        )
    if session.status in LEARNING_TERMINAL_STATUSES:
        raise CoachLearningConflictError(
            "learning_session_read_only",
            session=_session_view(store, session),
        )


def _session_sources_current(
    store: KnowledgeStore,
    session: CoachLearningSession,
) -> bool:
    try:
        current = current_coach_analysis(store, session.project_id)
    except ValueError:
        return False
    return (
        current.status == "completed"
        and current.id == session.analysis_run_id
    )


def _check_expected_version(
    store: KnowledgeStore,
    session: CoachLearningSession,
    expected_version: Any,
) -> None:
    if isinstance(expected_version, bool):
        raise ValueError("expected_version must be an integer")
    try:
        parsed = int(expected_version)
    except (TypeError, ValueError) as exc:
        raise ValueError("expected_version must be an integer") from exc
    if parsed != session.version:
        raise CoachLearningConflictError(
            "learning_session_version_conflict",
            session=_session_view(store, session, resumed=True),
        )


def _raise_store_conflict(
    store: KnowledgeStore,
    project_id: str,
    session_id: str,
    exc: ValueError,
) -> None:
    message = str(exc)
    aliases = {
        "learning_attempt_idempotency_conflict": (
            "idempotency_payload_conflict"
        ),
        "learning_session_active_conflict": (
            "learning_session_active_conflict"
        ),
        "learning_session_version_conflict": (
            "learning_session_version_conflict"
        ),
        "learning_attempt_limit_reached": "learning_attempt_limit_reached",
    }
    if message not in aliases:
        return
    latest = store.get_coach_learning_session(project_id, session_id)
    raise CoachLearningConflictError(
        aliases[message],
        session=(
            _session_view(store, latest, resumed=True)
            if latest is not None
            else None
        ),
    ) from exc


def _attempt_request_hash(
    session_id: str,
    exercise_id: str,
    answer: str,
    expected_version: int,
) -> str:
    payload = {
        "session_id": session_id,
        "exercise_id": exercise_id,
        "answer": answer,
        "expected_version": expected_version,
    }
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _grading_attempt_expired(created_at: str) -> bool:
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - created).total_seconds() > 30


def _last_attempt_exercise(step: Any) -> CoachLearningExercise | None:
    if not step.attempts:
        return None
    exercise_id = step.attempts[-1].exercise_id
    return next(
        (
            exercise
            for exercise in step.exercises
            if exercise.id == exercise_id
        ),
        None,
    )


def _step_has_valid_mastery(step: Any) -> bool:
    return any(
        attempt.status == "evaluated"
        and attempt.counts_for_mastery
        and attempt.score is not None
        and attempt.score >= step.completion_threshold
        for attempt in step.attempts
    )


def _would_master_all_steps(
    session: CoachLearningSession,
    current_step_id: str,
) -> bool:
    return all(
        step.id == current_step_id or _step_has_valid_mastery(step)
        for step in session.steps
    )


__all__ = [
    "CoachLearningConflictError",
    "CoachLearningNotFoundError",
    "get_current_coach_learning_session",
    "start_coach_learning_session",
    "submit_coach_learning_attempt",
    "transition_coach_learning_session",
]
