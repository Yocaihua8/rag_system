from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from backend.domain.coach_models import (
    CoachAssessmentAnswer,
    CoachAssessmentQuestion,
    CoachAssessmentResult,
    CoachAssessmentSession,
    CoachLearningAttempt,
    CoachLearningExercise,
    CoachLearningPlan,
    CoachLearningPlanItem,
    CoachLearningSession,
    CoachLearningStep,
    CoachSqlExerciseFixture,
)


ASSESSMENT_TARGET_TYPES = {"knowledge_point", "skill"}
ASSESSMENT_SESSION_STATUSES = {"active", "completed", "abandoned"}
ASSESSMENT_EVALUATORS = {"rule", "model"}
ASSESSMENT_RESULT_STATUSES = {
    "unassessed",
    "needs_work",
    "developing",
    "mastered",
}
LEARNING_PLAN_STATUSES = {"draft", "confirmed", "archived"}
LEARNING_PLAN_ITEM_TYPES = {"learning", "source_gap"}
LEARNING_PLAN_ITEM_STATUSES = {"todo", "in_progress", "done", "skipped"}
LEARNING_SESSION_TARGET_TYPES = {"knowledge_point", "skill"}
LEARNING_SESSION_ORIGIN_TYPES = {"coach", "learning_map", "learning_plan"}
LEARNING_SESSION_STATUSES = {
    "ready",
    "learning",
    "awaiting_answer",
    "evaluated",
    "retrying",
    "completed",
    "abandoned",
}
LEARNING_SESSION_NON_TERMINAL_STATUSES = LEARNING_SESSION_STATUSES - {
    "completed",
    "abandoned",
}
LEARNING_OUTCOMES = {"", "mastered", "needs_work", "assisted"}
LEARNING_STEP_STATUSES = {
    "ready",
    "learning",
    "awaiting_answer",
    "evaluated",
    "retrying",
    "completed",
}
LEARNING_EXERCISE_VARIANTS = {"primary", "reinforcement"}
LEARNING_EXERCISE_TYPES = {"concept", "flow", "code_location", "sql_query"}
LEARNING_ATTEMPT_STATUSES = {"grading", "evaluated", "failed"}
LEARNING_ATTEMPT_EVALUATORS = {"", "rule", "model", "sql"}
_UNCHANGED = object()


class CoachProgressStoreMixin:
    """Persistence for coach assessments, coverage evidence and learning plans."""

    def _connect(self) -> sqlite3.Connection:
        raise NotImplementedError

    @staticmethod
    def _init_coach_progress_schema(conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS coach_assessment_sessions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                analysis_run_id TEXT NOT NULL,
                target_type TEXT NOT NULL
                    CHECK(target_type IN ('knowledge_point', 'skill')),
                target_id TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK(status IN ('active', 'completed', 'abandoned')),
                created_at TEXT NOT NULL,
                completed_at TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY(analysis_run_id)
                    REFERENCES coach_analysis_runs(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_coach_assessment_sessions_project
                ON coach_assessment_sessions(project_id, created_at);

            CREATE UNIQUE INDEX IF NOT EXISTS uq_coach_assessment_active_target
                ON coach_assessment_sessions(
                    project_id, analysis_run_id, target_type, target_id
                )
                WHERE status = 'active';

            CREATE TABLE IF NOT EXISTS coach_assessment_questions (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                knowledge_point_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                question_type TEXT NOT NULL,
                expected_points_json TEXT NOT NULL,
                source_ids_json TEXT NOT NULL,
                sort_order INTEGER NOT NULL,
                UNIQUE(session_id, sort_order),
                FOREIGN KEY(session_id)
                    REFERENCES coach_assessment_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY(knowledge_point_id)
                    REFERENCES coach_knowledge_points(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_coach_assessment_questions_session
                ON coach_assessment_questions(session_id, sort_order);

            CREATE TABLE IF NOT EXISTS coach_assessment_answers (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(session_id, question_id),
                FOREIGN KEY(session_id)
                    REFERENCES coach_assessment_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY(question_id)
                    REFERENCES coach_assessment_questions(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_coach_assessment_answers_session
                ON coach_assessment_answers(session_id, created_at);

            CREATE TABLE IF NOT EXISTS coach_assessment_results (
                id TEXT PRIMARY KEY,
                answer_id TEXT NOT NULL UNIQUE,
                evaluator TEXT NOT NULL CHECK(evaluator IN ('rule', 'model')),
                score REAL NOT NULL CHECK(score >= 0 AND score <= 1),
                confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
                status TEXT NOT NULL
                    CHECK(status IN (
                        'unassessed', 'needs_work', 'developing', 'mastered'
                    )),
                evaluation_warning TEXT NOT NULL DEFAULT '',
                feedback TEXT NOT NULL DEFAULT '',
                matched_evidence_json TEXT NOT NULL,
                missing_points_json TEXT NOT NULL,
                source_ids_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(answer_id)
                    REFERENCES coach_assessment_answers(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_coach_assessment_results_created
                ON coach_assessment_results(created_at);

            CREATE TABLE IF NOT EXISTS coach_learning_plans (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                revision INTEGER NOT NULL CHECK(revision > 0),
                status TEXT NOT NULL
                    CHECK(status IN ('draft', 'confirmed', 'archived')),
                based_on_run_id TEXT,
                created_at TEXT NOT NULL,
                confirmed_at TEXT NOT NULL DEFAULT '',
                UNIQUE(project_id, revision),
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY(based_on_run_id)
                    REFERENCES coach_analysis_runs(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_coach_learning_plans_project
                ON coach_learning_plans(project_id, revision);

            CREATE UNIQUE INDEX IF NOT EXISTS uq_coach_learning_plan_confirmed
                ON coach_learning_plans(project_id)
                WHERE status = 'confirmed';

            CREATE TABLE IF NOT EXISTS coach_learning_plan_items (
                id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                stable_key TEXT NOT NULL,
                item_type TEXT NOT NULL
                    CHECK(item_type IN ('learning', 'source_gap')),
                objective TEXT NOT NULL,
                knowledge_point_id TEXT,
                skill_node_id TEXT,
                source_ids_json TEXT NOT NULL,
                practice_question TEXT NOT NULL,
                completion_criteria TEXT NOT NULL,
                estimated_minutes INTEGER NOT NULL CHECK(estimated_minutes > 0),
                status TEXT NOT NULL
                    CHECK(status IN ('todo', 'in_progress', 'done', 'skipped')),
                sort_order INTEGER NOT NULL,
                UNIQUE(plan_id, stable_key),
                UNIQUE(plan_id, sort_order),
                FOREIGN KEY(plan_id)
                    REFERENCES coach_learning_plans(id) ON DELETE CASCADE,
                FOREIGN KEY(knowledge_point_id)
                    REFERENCES coach_knowledge_points(id) ON DELETE SET NULL,
                FOREIGN KEY(skill_node_id)
                    REFERENCES coach_skill_nodes(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_coach_learning_plan_items_plan
                ON coach_learning_plan_items(plan_id, sort_order);

            CREATE TABLE IF NOT EXISTS coach_learning_sessions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                analysis_run_id TEXT NOT NULL,
                target_type TEXT NOT NULL
                    CHECK(target_type IN ('knowledge_point', 'skill')),
                target_id TEXT NOT NULL,
                origin_type TEXT NOT NULL
                    CHECK(origin_type IN ('coach', 'learning_map', 'learning_plan')),
                plan_id TEXT,
                plan_item_id TEXT,
                status TEXT NOT NULL
                    CHECK(status IN (
                        'ready', 'learning', 'awaiting_answer', 'evaluated',
                        'retrying', 'completed', 'abandoned'
                    )),
                current_step_id TEXT,
                version INTEGER NOT NULL DEFAULT 1 CHECK(version > 0),
                outcome TEXT NOT NULL DEFAULT ''
                    CHECK(outcome IN ('', 'mastered', 'needs_work', 'assisted')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT NOT NULL DEFAULT '',
                abandoned_at TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY(analysis_run_id)
                    REFERENCES coach_analysis_runs(id) ON DELETE CASCADE,
                FOREIGN KEY(plan_id)
                    REFERENCES coach_learning_plans(id) ON DELETE SET NULL,
                FOREIGN KEY(plan_item_id)
                    REFERENCES coach_learning_plan_items(id) ON DELETE SET NULL,
                FOREIGN KEY(current_step_id)
                    REFERENCES coach_learning_steps(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_coach_learning_sessions_project
                ON coach_learning_sessions(project_id, updated_at);

            CREATE UNIQUE INDEX IF NOT EXISTS uq_coach_learning_active_run
                ON coach_learning_sessions(project_id, analysis_run_id)
                WHERE status IN (
                    'ready', 'learning', 'awaiting_answer',
                    'evaluated', 'retrying'
                );

            CREATE TABLE IF NOT EXISTS coach_learning_steps (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                knowledge_point_id TEXT NOT NULL,
                title TEXT NOT NULL,
                explanation TEXT NOT NULL,
                completion_threshold REAL NOT NULL DEFAULT 0.75
                    CHECK(completion_threshold >= 0 AND completion_threshold <= 1),
                max_attempts INTEGER NOT NULL DEFAULT 3
                    CHECK(max_attempts > 0 AND max_attempts <= 3),
                status TEXT NOT NULL DEFAULT 'ready'
                    CHECK(status IN (
                        'ready', 'learning', 'awaiting_answer',
                        'evaluated', 'retrying', 'completed'
                    )),
                outcome TEXT NOT NULL DEFAULT ''
                    CHECK(outcome IN ('', 'mastered', 'needs_work', 'assisted')),
                sort_order INTEGER NOT NULL CHECK(sort_order >= 0),
                created_at TEXT NOT NULL,
                completed_at TEXT NOT NULL DEFAULT '',
                UNIQUE(session_id, sort_order),
                UNIQUE(id, session_id),
                FOREIGN KEY(session_id)
                    REFERENCES coach_learning_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY(knowledge_point_id)
                    REFERENCES coach_knowledge_points(id) ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_coach_learning_steps_session
                ON coach_learning_steps(session_id, sort_order);

            CREATE TABLE IF NOT EXISTS coach_learning_step_sources (
                step_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                sort_order INTEGER NOT NULL CHECK(sort_order >= 0),
                PRIMARY KEY(step_id, source_id),
                UNIQUE(step_id, sort_order),
                FOREIGN KEY(step_id)
                    REFERENCES coach_learning_steps(id) ON DELETE CASCADE,
                FOREIGN KEY(source_id)
                    REFERENCES coach_knowledge_sources(id) ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_coach_learning_step_sources_source
                ON coach_learning_step_sources(source_id);

            CREATE TABLE IF NOT EXISTS coach_learning_exercises (
                id TEXT PRIMARY KEY,
                step_id TEXT NOT NULL,
                variant TEXT NOT NULL
                    CHECK(variant IN ('primary', 'reinforcement')),
                question_type TEXT NOT NULL
                    CHECK(question_type IN (
                        'concept', 'flow', 'code_location', 'sql_query'
                    )),
                prompt TEXT NOT NULL,
                expected_points_json TEXT NOT NULL DEFAULT '[]',
                reference_answer TEXT NOT NULL,
                sort_order INTEGER NOT NULL CHECK(sort_order >= 0),
                revealed_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                UNIQUE(step_id, variant),
                UNIQUE(step_id, sort_order),
                UNIQUE(id, step_id),
                FOREIGN KEY(step_id)
                    REFERENCES coach_learning_steps(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_coach_learning_exercises_step
                ON coach_learning_exercises(step_id, sort_order);

            CREATE TABLE IF NOT EXISTS coach_sql_exercise_fixtures (
                exercise_id TEXT PRIMARY KEY,
                schema_json TEXT NOT NULL,
                seed_rows_json TEXT NOT NULL,
                expected_columns_json TEXT NOT NULL,
                expected_rows_json TEXT NOT NULL,
                order_sensitive INTEGER NOT NULL DEFAULT 0
                    CHECK(order_sensitive IN (0, 1)),
                required_semantics_json TEXT NOT NULL DEFAULT '{}',
                limits_json TEXT NOT NULL DEFAULT '{}',
                fixture_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(exercise_id)
                    REFERENCES coach_learning_exercises(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS coach_learning_attempts (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                exercise_id TEXT NOT NULL,
                attempt_no INTEGER NOT NULL
                    CHECK(attempt_no > 0 AND attempt_no <= 3),
                idempotency_key TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                answer TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK(status IN ('grading', 'evaluated', 'failed')),
                evaluator TEXT NOT NULL DEFAULT ''
                    CHECK(evaluator IN ('', 'rule', 'model', 'sql')),
                score REAL CHECK(score IS NULL OR (score >= 0 AND score <= 1)),
                confidence REAL
                    CHECK(confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
                feedback TEXT NOT NULL DEFAULT '',
                error_code TEXT NOT NULL DEFAULT '',
                error_message TEXT NOT NULL DEFAULT '',
                result_preview_json TEXT NOT NULL DEFAULT 'null',
                scoring_details_json TEXT NOT NULL DEFAULT '{}',
                counts_for_mastery INTEGER NOT NULL DEFAULT 0
                    CHECK(counts_for_mastery IN (0, 1)),
                created_at TEXT NOT NULL,
                evaluated_at TEXT NOT NULL DEFAULT '',
                UNIQUE(step_id, attempt_no),
                UNIQUE(session_id, idempotency_key),
                FOREIGN KEY(session_id)
                    REFERENCES coach_learning_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY(step_id, session_id)
                    REFERENCES coach_learning_steps(id, session_id) ON DELETE CASCADE,
                FOREIGN KEY(exercise_id, step_id)
                    REFERENCES coach_learning_exercises(id, step_id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_coach_learning_attempts_session
                ON coach_learning_attempts(session_id, created_at);

            CREATE INDEX IF NOT EXISTS idx_coach_learning_attempts_evidence
                ON coach_learning_attempts(
                    session_id, counts_for_mastery, evaluated_at
                );
            """
        )

    def create_coach_learning_session(
        self,
        project_id: str,
        analysis_run_id: str,
        target_type: str,
        target_id: str,
        steps: Iterable[Mapping[str, Any]],
        *,
        origin_type: str = "coach",
        plan_id: str = "",
        plan_item_id: str = "",
    ) -> CoachLearningSession:
        clean_project_id = _required_text_value(project_id, "project_id")
        clean_run_id = _required_text_value(analysis_run_id, "analysis_run_id")
        clean_target_type = _enum_value(
            target_type, "target_type", LEARNING_SESSION_TARGET_TYPES
        )
        clean_target_id = _required_text_value(target_id, "target_id")
        clean_origin_type = _enum_value(
            origin_type, "origin_type", LEARNING_SESSION_ORIGIN_TYPES
        )
        clean_plan_id = str(plan_id or "").strip()
        clean_plan_item_id = str(plan_item_id or "").strip()
        if bool(clean_plan_id) != bool(clean_plan_item_id):
            raise ValueError("plan_id and plan_item_id must be provided together")
        if clean_origin_type == "learning_plan" and not clean_plan_id:
            raise ValueError("learning_plan origin requires plan linkage")
        step_drafts = list(steps)
        if not step_drafts:
            raise ValueError("at least one learning step is required")

        session_id = str(uuid.uuid4())
        now = _utc_now()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            _require_project(conn, clean_project_id)
            _require_analysis_run(conn, clean_project_id, clean_run_id)
            _require_assessment_target(
                conn,
                clean_project_id,
                clean_run_id,
                clean_target_type,
                clean_target_id,
            )
            if _active_learning_session_row(conn, clean_project_id, clean_run_id):
                raise ValueError("learning_session_active_conflict")
            _require_learning_plan_link(
                conn,
                clean_project_id,
                clean_run_id,
                clean_plan_id,
                clean_plan_item_id,
            )
            try:
                conn.execute(
                    """
                    INSERT INTO coach_learning_sessions
                        (id, project_id, analysis_run_id, target_type, target_id,
                         origin_type, plan_id, plan_item_id, status,
                         current_step_id, version, outcome, created_at, updated_at,
                         completed_at, abandoned_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ready', NULL, 1, '', ?, ?, '', '')
                    """,
                    (
                        session_id,
                        clean_project_id,
                        clean_run_id,
                        clean_target_type,
                        clean_target_id,
                        clean_origin_type,
                        clean_plan_id or None,
                        clean_plan_item_id or None,
                        now,
                        now,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                if _active_learning_session_row(
                    conn, clean_project_id, clean_run_id
                ):
                    raise ValueError("learning_session_active_conflict") from exc
                raise

            step_ids: list[tuple[int, str]] = []
            seen_step_orders: set[int] = set()
            for fallback_order, draft in enumerate(step_drafts):
                if not isinstance(draft, Mapping):
                    raise ValueError("learning step must be an object")
                knowledge_point_id = _required_mapping_text(
                    draft, "knowledge_point_id"
                )
                _require_question_knowledge_point(
                    conn,
                    clean_project_id,
                    clean_run_id,
                    clean_target_type,
                    clean_target_id,
                    knowledge_point_id,
                )
                source_ids = _non_empty_text_list(
                    draft.get("source_ids"), "source_ids"
                )
                _require_sources_for_analysis_run(
                    conn,
                    clean_project_id,
                    clean_run_id,
                    source_ids,
                    knowledge_point_id,
                )
                sort_order = _non_negative_integer(
                    draft.get("sort_order"),
                    fallback_order,
                    "sort_order",
                )
                if sort_order in seen_step_orders:
                    raise ValueError("learning step sort_order must be unique")
                seen_step_orders.add(sort_order)
                completion_threshold = _unit_interval(
                    draft.get("completion_threshold", 0.75),
                    "completion_threshold",
                )
                max_attempts = _bounded_integer(
                    draft.get("max_attempts"),
                    3,
                    "max_attempts",
                    1,
                    3,
                )
                exercise_drafts = list(draft.get("exercises") or ())
                if not exercise_drafts:
                    raise ValueError("learning step requires exercises")

                step_id = str(uuid.uuid4())
                step_ids.append((sort_order, step_id))
                conn.execute(
                    """
                    INSERT INTO coach_learning_steps
                        (id, session_id, knowledge_point_id, title, explanation,
                         completion_threshold, max_attempts, status, outcome,
                         sort_order, created_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'ready', '', ?, ?, '')
                    """,
                    (
                        step_id,
                        session_id,
                        knowledge_point_id,
                        _required_mapping_text(draft, "title"),
                        _required_mapping_text(draft, "explanation"),
                        completion_threshold,
                        max_attempts,
                        sort_order,
                        now,
                    ),
                )
                conn.executemany(
                    """
                    INSERT INTO coach_learning_step_sources
                        (step_id, source_id, sort_order)
                    VALUES (?, ?, ?)
                    """,
                    [
                        (step_id, source_id, source_order)
                        for source_order, source_id in enumerate(source_ids)
                    ],
                )
                _insert_learning_exercises(conn, step_id, exercise_drafts, now)

            current_step_id = min(step_ids)[1]
            conn.execute(
                """
                UPDATE coach_learning_sessions
                SET current_step_id = ?
                WHERE id = ?
                """,
                (current_step_id, session_id),
            )
            session = _learning_session_from_db(conn, clean_project_id, session_id)
        if session is None:
            raise RuntimeError("learning session was not persisted")
        return session

    def get_active_coach_learning_session(
        self,
        project_id: str,
        analysis_run_id: str,
    ) -> CoachLearningSession | None:
        clean_project_id = _required_text_value(project_id, "project_id")
        clean_run_id = _required_text_value(analysis_run_id, "analysis_run_id")
        with self._connect() as conn:
            row = _active_learning_session_row(
                conn, clean_project_id, clean_run_id
            )
            if not row:
                return None
            return _learning_session_from_db(
                conn, clean_project_id, str(row["id"])
            )

    def get_coach_learning_session(
        self,
        project_id: str,
        session_id: str,
    ) -> CoachLearningSession | None:
        clean_project_id = _required_text_value(project_id, "project_id")
        clean_session_id = _required_text_value(session_id, "session_id")
        with self._connect() as conn:
            return _learning_session_from_db(
                conn, clean_project_id, clean_session_id
            )

    def list_coach_learning_sessions(
        self,
        project_id: str,
        limit: int = 500,
    ) -> list[CoachLearningSession]:
        clean_project_id = _required_text_value(project_id, "project_id")
        clean_limit = _bounded_integer(limit, 500, "limit", 1, 500)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id
                FROM coach_learning_sessions
                WHERE project_id = ?
                ORDER BY created_at DESC, rowid DESC
                LIMIT ?
                """,
                (clean_project_id, clean_limit),
            ).fetchall()
            sessions = [
                _learning_session_from_db(
                    conn,
                    clean_project_id,
                    str(row["id"]),
                )
                for row in rows
            ]
            return [session for session in sessions if session is not None]

    def list_coach_learning_attempts(
        self,
        project_id: str,
        session_id: str,
        step_id: str = "",
    ) -> list[CoachLearningAttempt]:
        clean_project_id = _required_text_value(project_id, "project_id")
        clean_session_id = _required_text_value(session_id, "session_id")
        clean_step_id = str(step_id or "").strip()
        with self._connect() as conn:
            if not _learning_session_row(conn, clean_project_id, clean_session_id):
                return []
            sql = """
                SELECT a.*
                FROM coach_learning_attempts a
                WHERE a.session_id = ?
            """
            params: list[object] = [clean_session_id]
            if clean_step_id:
                sql += " AND a.step_id = ?"
                params.append(clean_step_id)
            sql += " ORDER BY a.created_at ASC, a.attempt_no ASC, a.id ASC"
            rows = conn.execute(sql, params).fetchall()
            return [_learning_attempt_from_row(row) for row in rows]

    def transition_coach_learning_session(
        self,
        project_id: str,
        session_id: str,
        expected_version: int,
        status: str,
        *,
        current_step_id: str | None = None,
        outcome: str | None = None,
        step_id: str = "",
        step_status: str = "",
        step_outcome: str | None = None,
        reveal_exercise_id: str = "",
    ) -> CoachLearningSession:
        clean_project_id = _required_text_value(project_id, "project_id")
        clean_session_id = _required_text_value(session_id, "session_id")
        clean_status = _enum_value(
            status, "status", LEARNING_SESSION_STATUSES
        )
        clean_expected_version = _positive_integer(
            expected_version, "expected_version"
        )
        clean_outcome = (
            None
            if outcome is None
            else _enum_value(outcome, "outcome", LEARNING_OUTCOMES)
        )
        clean_step_id = str(step_id or "").strip()
        clean_step_status = str(step_status or "").strip()
        if clean_step_status:
            clean_step_status = _enum_value(
                clean_step_status, "step_status", LEARNING_STEP_STATUSES
            )
            if not clean_step_id:
                raise ValueError("step_id is required when step_status is provided")
        clean_step_outcome = (
            None
            if step_outcome is None
            else _enum_value(
                step_outcome, "step_outcome", LEARNING_OUTCOMES
            )
        )
        clean_reveal_id = str(reveal_exercise_id or "").strip()
        now = _utc_now()

        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = _learning_session_row(conn, clean_project_id, clean_session_id)
            if not row:
                raise ValueError("learning session not found")
            if int(row["version"]) != clean_expected_version:
                raise ValueError("learning_session_version_conflict")

            next_step_id: str | None | object = _UNCHANGED
            if current_step_id is not None:
                candidate_step_id = str(current_step_id).strip()
                if candidate_step_id:
                    _require_learning_step(
                        conn, clean_session_id, candidate_step_id
                    )
                    next_step_id = candidate_step_id
                else:
                    next_step_id = None

            if clean_step_id:
                _require_learning_step(conn, clean_session_id, clean_step_id)
                step_assignments: list[str] = []
                step_values: list[object] = []
                if clean_step_status:
                    step_assignments.append("status = ?")
                    step_values.append(clean_step_status)
                    if clean_step_status == "completed":
                        step_assignments.append("completed_at = ?")
                        step_values.append(now)
                if clean_step_outcome is not None:
                    step_assignments.append("outcome = ?")
                    step_values.append(clean_step_outcome)
                if step_assignments:
                    step_values.extend((clean_step_id, clean_session_id))
                    conn.execute(
                        f"""
                        UPDATE coach_learning_steps
                        SET {", ".join(step_assignments)}
                        WHERE id = ? AND session_id = ?
                        """,
                        step_values,
                    )

            if clean_reveal_id:
                exercise_row = conn.execute(
                    """
                    SELECT e.id
                    FROM coach_learning_exercises e
                    JOIN coach_learning_steps s ON s.id = e.step_id
                    WHERE e.id = ? AND s.session_id = ?
                    """,
                    (clean_reveal_id, clean_session_id),
                ).fetchone()
                if not exercise_row:
                    raise ValueError("learning exercise does not belong to session")
                conn.execute(
                    """
                    UPDATE coach_learning_exercises
                    SET revealed_at = CASE
                        WHEN revealed_at = '' THEN ?
                        ELSE revealed_at
                    END
                    WHERE id = ?
                    """,
                    (now, clean_reveal_id),
                )

            assignments = [
                "status = ?",
                "version = version + 1",
                "updated_at = ?",
            ]
            values: list[object] = [clean_status, now]
            if next_step_id is not _UNCHANGED:
                assignments.append("current_step_id = ?")
                values.append(next_step_id)
            if clean_outcome is not None:
                assignments.append("outcome = ?")
                values.append(clean_outcome)
            if clean_status == "completed":
                assignments.append("completed_at = ?")
                values.append(now)
            if clean_status == "abandoned":
                assignments.append("abandoned_at = ?")
                values.append(now)
            values.extend(
                (clean_session_id, clean_project_id, clean_expected_version)
            )
            cursor = conn.execute(
                f"""
                UPDATE coach_learning_sessions
                SET {", ".join(assignments)}
                WHERE id = ? AND project_id = ? AND version = ?
                """,
                values,
            )
            if cursor.rowcount != 1:
                raise ValueError("learning_session_version_conflict")
            session = _learning_session_from_db(
                conn, clean_project_id, clean_session_id
            )
        if session is None:
            raise RuntimeError("learning session disappeared")
        return session

    def reserve_coach_learning_attempt(
        self,
        project_id: str,
        session_id: str,
        exercise_id: str,
        answer: str,
        expected_version: int,
        idempotency_key: str,
        request_hash: str,
    ) -> tuple[CoachLearningAttempt, CoachLearningSession, bool]:
        clean_project_id = _required_text_value(project_id, "project_id")
        clean_session_id = _required_text_value(session_id, "session_id")
        clean_exercise_id = _required_text_value(exercise_id, "exercise_id")
        raw_answer = str(answer)
        if not raw_answer.strip():
            raise ValueError("answer is required")
        clean_expected_version = _positive_integer(
            expected_version, "expected_version"
        )
        clean_idempotency_key = _required_text_value(
            idempotency_key, "idempotency_key"
        )
        clean_request_hash = _required_text_value(request_hash, "request_hash")
        now = _utc_now()

        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = _learning_attempt_by_idempotency(
                conn,
                clean_project_id,
                clean_session_id,
                clean_idempotency_key,
            )
            if existing:
                if (
                    str(existing["request_hash"]) != clean_request_hash
                    or str(existing["exercise_id"]) != clean_exercise_id
                    or str(existing["answer"]) != raw_answer
                ):
                    raise ValueError("learning_attempt_idempotency_conflict")
                session = _learning_session_from_db(
                    conn, clean_project_id, clean_session_id
                )
                if session is None:
                    raise RuntimeError("learning session disappeared")
                return _learning_attempt_from_row(existing), session, True

            session_row = _learning_session_row(
                conn, clean_project_id, clean_session_id
            )
            if not session_row:
                raise ValueError("learning session not found")
            if int(session_row["version"]) != clean_expected_version:
                raise ValueError("learning_session_version_conflict")
            exercise_row = conn.execute(
                """
                SELECT e.id, e.step_id, s.max_attempts
                FROM coach_learning_exercises e
                JOIN coach_learning_steps s ON s.id = e.step_id
                WHERE e.id = ? AND s.session_id = ?
                """,
                (clean_exercise_id, clean_session_id),
            ).fetchone()
            if not exercise_row:
                raise ValueError("learning exercise does not belong to session")
            step_id_value = str(exercise_row["step_id"])
            count_row = conn.execute(
                """
                SELECT COUNT(*) AS attempt_count
                FROM coach_learning_attempts
                WHERE step_id = ?
                """,
                (step_id_value,),
            ).fetchone()
            attempt_no = int(count_row["attempt_count"]) + 1
            if attempt_no > int(exercise_row["max_attempts"]):
                raise ValueError("learning_attempt_limit_reached")

            attempt_id = str(uuid.uuid4())
            conn.execute(
                """
                INSERT INTO coach_learning_attempts
                    (id, session_id, step_id, exercise_id, attempt_no,
                     idempotency_key, request_hash, answer, status, evaluator,
                     score, confidence, feedback, error_code, error_message,
                     result_preview_json, scoring_details_json,
                     counts_for_mastery, created_at, evaluated_at)
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, 'grading', '',
                    NULL, NULL, '', '', '', 'null', '{}', 0, ?, ''
                )
                """,
                (
                    attempt_id,
                    clean_session_id,
                    step_id_value,
                    clean_exercise_id,
                    attempt_no,
                    clean_idempotency_key,
                    clean_request_hash,
                    raw_answer,
                    now,
                ),
            )
            cursor = conn.execute(
                """
                UPDATE coach_learning_sessions
                SET version = version + 1, updated_at = ?
                WHERE id = ? AND project_id = ? AND version = ?
                """,
                (
                    now,
                    clean_session_id,
                    clean_project_id,
                    clean_expected_version,
                ),
            )
            if cursor.rowcount != 1:
                raise ValueError("learning_session_version_conflict")
            attempt_row = _learning_attempt_row(
                conn, clean_project_id, attempt_id
            )
            session = _learning_session_from_db(
                conn, clean_project_id, clean_session_id
            )
        if attempt_row is None or session is None:
            raise RuntimeError("learning attempt reservation was not persisted")
        return _learning_attempt_from_row(attempt_row), session, False

    def finalize_coach_learning_attempt(
        self,
        project_id: str,
        session_id: str,
        attempt_id: str,
        expected_version: int,
        *,
        evaluator: str,
        score: float,
        confidence: float = 1.0,
        feedback: str = "",
        error_code: str = "",
        error_message: str = "",
        result_preview: object = None,
        scoring_details: Mapping[str, Any] | None = None,
        counts_for_mastery: bool = False,
        session_status: str = "evaluated",
        session_outcome: str | None = None,
        step_status: str = "evaluated",
        step_outcome: str | None = None,
        plan_item_status: str = "",
    ) -> tuple[CoachLearningAttempt, CoachLearningSession, str]:
        clean_project_id = _required_text_value(project_id, "project_id")
        clean_session_id = _required_text_value(session_id, "session_id")
        clean_attempt_id = _required_text_value(attempt_id, "attempt_id")
        clean_expected_version = _positive_integer(
            expected_version, "expected_version"
        )
        clean_evaluator = _enum_value(
            evaluator,
            "evaluator",
            LEARNING_ATTEMPT_EVALUATORS - {""},
        )
        clean_score = _unit_interval(score, "score")
        clean_confidence = _unit_interval(confidence, "confidence")
        clean_session_status = _enum_value(
            session_status, "session_status", LEARNING_SESSION_STATUSES
        )
        clean_step_status = _enum_value(
            step_status, "step_status", LEARNING_STEP_STATUSES
        )
        clean_session_outcome = (
            None
            if session_outcome is None
            else _enum_value(
                session_outcome, "session_outcome", LEARNING_OUTCOMES
            )
        )
        clean_step_outcome = (
            None
            if step_outcome is None
            else _enum_value(
                step_outcome, "step_outcome", LEARNING_OUTCOMES
            )
        )
        clean_plan_status = str(plan_item_status or "").strip()
        if clean_plan_status not in {"", "in_progress", "done"}:
            raise ValueError("plan_item_status must be in_progress or done")
        clean_details = dict(scoring_details or {})
        now = _utc_now()

        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            attempt_row = _learning_attempt_row(
                conn, clean_project_id, clean_attempt_id
            )
            if (
                not attempt_row
                or str(attempt_row["session_id"]) != clean_session_id
            ):
                raise ValueError("learning attempt not found")
            if str(attempt_row["status"]) != "grading":
                session = _learning_session_from_db(
                    conn, clean_project_id, clean_session_id
                )
                if session is None:
                    raise RuntimeError("learning session disappeared")
                return _learning_attempt_from_row(attempt_row), session, "unchanged"
            session_row = _learning_session_row(
                conn, clean_project_id, clean_session_id
            )
            if not session_row:
                raise ValueError("learning session not found")
            if int(session_row["version"]) != clean_expected_version:
                raise ValueError("learning_session_version_conflict")

            conn.execute(
                """
                UPDATE coach_learning_attempts
                SET status = 'evaluated', evaluator = ?, score = ?,
                    confidence = ?, feedback = ?, error_code = ?,
                    error_message = ?, result_preview_json = ?,
                    scoring_details_json = ?, counts_for_mastery = ?,
                    evaluated_at = ?
                WHERE id = ? AND status = 'grading'
                """,
                (
                    clean_evaluator,
                    clean_score,
                    clean_confidence,
                    str(feedback or ""),
                    str(error_code or ""),
                    str(error_message or ""),
                    _json_dump(result_preview),
                    _json_dump(clean_details),
                    int(bool(counts_for_mastery)),
                    now,
                    clean_attempt_id,
                ),
            )
            step_id_value = str(attempt_row["step_id"])
            step_assignments = ["status = ?"]
            step_values: list[object] = [clean_step_status]
            if clean_step_outcome is not None:
                step_assignments.append("outcome = ?")
                step_values.append(clean_step_outcome)
            if clean_step_status == "completed":
                step_assignments.append("completed_at = ?")
                step_values.append(now)
            step_values.extend((step_id_value, clean_session_id))
            conn.execute(
                f"""
                UPDATE coach_learning_steps
                SET {", ".join(step_assignments)}
                WHERE id = ? AND session_id = ?
                """,
                step_values,
            )

            plan_sync = _sync_linked_learning_plan_item(
                conn, session_row, clean_plan_status
            )
            session_assignments = [
                "status = ?",
                "version = version + 1",
                "updated_at = ?",
            ]
            session_values: list[object] = [clean_session_status, now]
            if clean_session_outcome is not None:
                session_assignments.append("outcome = ?")
                session_values.append(clean_session_outcome)
            if clean_session_status == "completed":
                session_assignments.append("completed_at = ?")
                session_values.append(now)
            if clean_session_status == "abandoned":
                session_assignments.append("abandoned_at = ?")
                session_values.append(now)
            session_values.extend(
                (clean_session_id, clean_project_id, clean_expected_version)
            )
            cursor = conn.execute(
                f"""
                UPDATE coach_learning_sessions
                SET {", ".join(session_assignments)}
                WHERE id = ? AND project_id = ? AND version = ?
                """,
                session_values,
            )
            if cursor.rowcount != 1:
                raise ValueError("learning_session_version_conflict")
            finalized_row = _learning_attempt_row(
                conn, clean_project_id, clean_attempt_id
            )
            session = _learning_session_from_db(
                conn, clean_project_id, clean_session_id
            )
        if finalized_row is None or session is None:
            raise RuntimeError("learning attempt finalization was not persisted")
        return _learning_attempt_from_row(finalized_row), session, plan_sync

    def create_coach_assessment_session(
        self,
        project_id: str,
        analysis_run_id: str,
        target_type: str,
        target_id: str,
        questions: Iterable[Mapping[str, Any]],
    ) -> CoachAssessmentSession:
        clean_project_id = _required_text_value(project_id, "project_id")
        clean_run_id = _required_text_value(analysis_run_id, "analysis_run_id")
        clean_target_type = _enum_value(
            target_type,
            "target_type",
            ASSESSMENT_TARGET_TYPES,
        )
        clean_target_id = _required_text_value(target_id, "target_id")
        question_drafts = list(questions)
        if not question_drafts:
            raise ValueError("at least one assessment question is required")
        now = _utc_now()
        session_id = str(uuid.uuid4())

        with self._connect() as conn:
            _require_project(conn, clean_project_id)
            _require_analysis_run(conn, clean_project_id, clean_run_id)
            _require_assessment_target(
                conn,
                clean_project_id,
                clean_run_id,
                clean_target_type,
                clean_target_id,
            )
            existing = _active_assessment_session_row(
                conn,
                clean_project_id,
                clean_run_id,
                clean_target_type,
                clean_target_id,
            )
            if existing:
                questions = _assessment_questions_for_session(
                    conn,
                    str(existing["id"]),
                )
                return _assessment_session_from_row(existing, questions)
            try:
                conn.execute(
                    """
                    INSERT INTO coach_assessment_sessions
                        (id, project_id, analysis_run_id, target_type, target_id,
                         status, created_at, completed_at)
                    VALUES (?, ?, ?, ?, ?, 'active', ?, '')
                    """,
                    (
                        session_id,
                        clean_project_id,
                        clean_run_id,
                        clean_target_type,
                        clean_target_id,
                        now,
                    ),
                )
            except sqlite3.IntegrityError:
                existing = _active_assessment_session_row(
                    conn,
                    clean_project_id,
                    clean_run_id,
                    clean_target_type,
                    clean_target_id,
                )
                if not existing:
                    raise
                questions = _assessment_questions_for_session(
                    conn,
                    str(existing["id"]),
                )
                return _assessment_session_from_row(existing, questions)
            seen_orders: set[int] = set()
            for index, draft in enumerate(question_drafts):
                if not isinstance(draft, Mapping):
                    raise ValueError("assessment questions must be objects")
                sort_order = _integer(draft.get("sort_order"), index)
                if sort_order in seen_orders:
                    raise ValueError("assessment question sort_order must be unique")
                seen_orders.add(sort_order)
                expected_points = _non_empty_text_list(
                    draft.get("expected_points"),
                    "expected_points",
                )
                source_ids = _non_empty_text_list(
                    draft.get("source_ids"),
                    "source_ids",
                )
                knowledge_point_id = _required_mapping_text(
                    draft,
                    "knowledge_point_id",
                )
                _require_question_knowledge_point(
                    conn,
                    clean_project_id,
                    clean_run_id,
                    clean_target_type,
                    clean_target_id,
                    knowledge_point_id,
                )
                _require_sources_for_analysis_run(
                    conn,
                    clean_project_id,
                    clean_run_id,
                    source_ids,
                    knowledge_point_id,
                )
                conn.execute(
                    """
                    INSERT INTO coach_assessment_questions
                        (id, session_id, knowledge_point_id, prompt, question_type,
                         expected_points_json, source_ids_json, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        session_id,
                        knowledge_point_id,
                        _required_mapping_text(draft, "prompt"),
                        _required_mapping_text(draft, "question_type"),
                        _json_dump(expected_points),
                        _json_dump(source_ids),
                        sort_order,
                    ),
                )

        session = self.get_coach_assessment_session(clean_project_id, session_id)
        if not session:
            raise RuntimeError("created assessment session was not found")
        return session

    def get_active_coach_assessment_session(
        self,
        project_id: str,
        analysis_run_id: str,
        target_type: str,
        target_id: str,
    ) -> CoachAssessmentSession | None:
        with self._connect() as conn:
            row = _active_assessment_session_row(
                conn,
                project_id,
                analysis_run_id,
                target_type,
                target_id,
            )
            if not row:
                return None
            questions = _assessment_questions_for_session(conn, str(row["id"]))
        return _assessment_session_from_row(row, questions)

    def get_coach_assessment_session(
        self,
        project_id: str,
        session_id: str,
    ) -> CoachAssessmentSession | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, project_id, analysis_run_id, target_type, target_id,
                       status, created_at, completed_at
                FROM coach_assessment_sessions
                WHERE id = ? AND project_id = ?
                """,
                (session_id, project_id),
            ).fetchone()
            if not row:
                return None
            questions = _assessment_questions_for_session(conn, session_id)
        return _assessment_session_from_row(row, questions)

    def list_coach_assessment_sessions(
        self,
        project_id: str,
        status: str = "",
        limit: int = 50,
    ) -> list[CoachAssessmentSession]:
        clean_limit = max(1, min(int(limit), 500))
        clean_status = status.strip()
        if clean_status:
            _enum_value(
                clean_status,
                "status",
                ASSESSMENT_SESSION_STATUSES,
            )
        query = """
            SELECT id, project_id, analysis_run_id, target_type, target_id,
                   status, created_at, completed_at
            FROM coach_assessment_sessions
            WHERE project_id = ?
        """
        values: list[object] = [project_id]
        if clean_status:
            query += " AND status = ?"
            values.append(clean_status)
        query += " ORDER BY created_at DESC, rowid DESC LIMIT ?"
        values.append(clean_limit)

        with self._connect() as conn:
            rows = conn.execute(query, values).fetchall()
            return [
                _assessment_session_from_row(
                    row,
                    _assessment_questions_for_session(conn, str(row["id"])),
                )
                for row in rows
            ]

    def abandon_coach_assessment_session(
        self,
        project_id: str,
        session_id: str,
    ) -> CoachAssessmentSession:
        with self._connect() as conn:
            row = _assessment_session_row(conn, project_id, session_id)
            if not row:
                raise ValueError("assessment session not found")
            if row["status"] == "completed":
                raise ValueError("completed assessment session cannot be abandoned")
            if row["status"] == "active":
                conn.execute(
                    """
                    UPDATE coach_assessment_sessions
                    SET status = 'abandoned'
                    WHERE id = ? AND project_id = ?
                    """,
                    (session_id, project_id),
                )
        session = self.get_coach_assessment_session(project_id, session_id)
        if not session:
            raise RuntimeError("assessment session was not found after update")
        return session

    def create_coach_assessment_answer_result(
        self,
        project_id: str,
        session_id: str,
        question_id: str,
        answer: str,
        evaluator: str,
        score: float,
        confidence: float,
        matched_evidence: Iterable[Mapping[str, Any] | str],
        missing_points: Iterable[str],
        source_ids: Iterable[str],
        evaluation_warning: str = "",
        feedback: str = "",
    ) -> tuple[
        CoachAssessmentAnswer,
        CoachAssessmentResult,
        CoachAssessmentSession,
    ]:
        clean_answer = _required_text_value(answer, "answer")
        clean_evaluator = _enum_value(
            evaluator,
            "evaluator",
            ASSESSMENT_EVALUATORS,
        )
        clean_score = _unit_interval(score, "score")
        clean_confidence = _unit_interval(confidence, "confidence")
        clean_source_ids = _text_list(source_ids, "source_ids")
        clean_missing_points = _text_list(missing_points, "missing_points")
        now = _utc_now()
        answer_id = str(uuid.uuid4())
        result_id = str(uuid.uuid4())

        with self._connect() as conn:
            session_row = _assessment_session_row(conn, project_id, session_id)
            if not session_row:
                raise ValueError("assessment session not found")
            question_row = conn.execute(
                """
                SELECT id, knowledge_point_id, expected_points_json, source_ids_json
                FROM coach_assessment_questions
                WHERE id = ? AND session_id = ?
                """,
                (question_id, session_id),
            ).fetchone()
            if not question_row:
                raise ValueError("assessment question not found in session")
            existing_answer_row = conn.execute(
                """
                SELECT id, session_id, question_id, answer, created_at
                FROM coach_assessment_answers
                WHERE session_id = ? AND question_id = ?
                """,
                (session_id, question_id),
            ).fetchone()
            if existing_answer_row:
                if str(existing_answer_row["answer"]) != clean_answer:
                    raise ValueError(
                        "assessment question has already been answered "
                        "with a different answer"
                    )
                existing_result_row = _assessment_result_row_for_answer(
                    conn,
                    project_id,
                    str(existing_answer_row["id"]),
                )
                if not existing_result_row:
                    raise RuntimeError("assessment answer has no stored result")
                existing_session = self.get_coach_assessment_session(
                    project_id,
                    session_id,
                )
                if not existing_session:
                    raise RuntimeError("assessment session was not found")
                return (
                    _assessment_answer_from_row(existing_answer_row),
                    _assessment_result_from_row(existing_result_row),
                    existing_session,
                )
            if session_row["status"] != "active":
                raise ValueError("assessment session is not active")
            allowed_source_ids = set(_json_text_list(question_row["source_ids_json"]))
            if not clean_source_ids or not set(clean_source_ids) <= allowed_source_ids:
                raise ValueError(
                    "assessment result sources must belong to the assessment question"
                )
            _require_sources_for_project(conn, project_id, clean_source_ids)
            expected_points = _json_text_list(question_row["expected_points_json"])
            if not set(clean_missing_points) <= set(expected_points):
                raise ValueError(
                    "missing_points must belong to the question scoring basis"
                )
            clean_evidence = _validated_evidence_list(
                matched_evidence,
                expected_points,
                clean_answer,
            )

            conn.execute(
                """
                INSERT INTO coach_assessment_answers
                    (id, session_id, question_id, answer, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (answer_id, session_id, question_id, clean_answer, now),
            )

            result_status = _assessment_status(clean_score)
            conn.execute(
                """
                    INSERT INTO coach_assessment_results
                        (id, answer_id, evaluator, score, confidence, status,
                         evaluation_warning, matched_evidence_json,
                         feedback, missing_points_json, source_ids_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result_id,
                    answer_id,
                    clean_evaluator,
                    clean_score,
                    clean_confidence,
                    result_status,
                    str(evaluation_warning or "").strip(),
                    _json_dump(clean_evidence),
                    str(feedback or "").strip(),
                    _json_dump(clean_missing_points),
                    _json_dump(clean_source_ids),
                    now,
                ),
            )
            question_count = int(
                conn.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM coach_assessment_questions
                    WHERE session_id = ?
                    """,
                    (session_id,),
                ).fetchone()["total"]
            )
            answer_count = int(
                conn.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM coach_assessment_answers
                    WHERE session_id = ?
                    """,
                    (session_id,),
                ).fetchone()["total"]
            )
            if answer_count >= question_count:
                conn.execute(
                    """
                    UPDATE coach_assessment_sessions
                    SET status = 'completed', completed_at = ?
                    WHERE id = ? AND project_id = ?
                    """,
                    (now, session_id, project_id),
                )

        stored_answer = CoachAssessmentAnswer(
            id=answer_id,
            session_id=session_id,
            question_id=question_id,
            answer=clean_answer,
            created_at=now,
        )
        stored_result = CoachAssessmentResult(
            id=result_id,
            project_id=project_id,
            session_id=session_id,
            question_id=question_id,
            knowledge_point_id=str(question_row["knowledge_point_id"]),
            answer_id=answer_id,
            evaluator=clean_evaluator,
            score=clean_score,
            confidence=clean_confidence,
            status=_assessment_status(clean_score),
            matched_evidence=tuple(clean_evidence),
            missing_points=tuple(clean_missing_points),
            source_ids=tuple(clean_source_ids),
            created_at=now,
            evaluation_warning=str(evaluation_warning or "").strip(),
            feedback=str(feedback or "").strip(),
        )
        stored_session = self.get_coach_assessment_session(project_id, session_id)
        if not stored_session:
            raise RuntimeError("assessment session was not found after answer")
        return stored_answer, stored_result, stored_session

    def list_coach_assessment_answers(
        self,
        project_id: str,
        session_id: str,
    ) -> list[CoachAssessmentAnswer]:
        with self._connect() as conn:
            if not _assessment_session_row(conn, project_id, session_id):
                return []
            rows = conn.execute(
                """
                SELECT id, session_id, question_id, answer, created_at
                FROM coach_assessment_answers
                WHERE session_id = ?
                ORDER BY created_at ASC, rowid ASC
                """,
                (session_id,),
            ).fetchall()
        return [_assessment_answer_from_row(row) for row in rows]

    def list_coach_assessment_results(
        self,
        project_id: str,
        session_id: str = "",
        limit: int = 200,
    ) -> list[CoachAssessmentResult]:
        query = """
            SELECT r.id, s.project_id, s.id AS session_id, q.id AS question_id,
                   q.knowledge_point_id, r.answer_id, r.evaluator, r.score,
                   r.confidence, r.status,
                   r.evaluation_warning, r.feedback, r.matched_evidence_json,
                   r.missing_points_json, r.source_ids_json, r.created_at
            FROM coach_assessment_results r
            JOIN coach_assessment_answers a ON a.id = r.answer_id
            JOIN coach_assessment_questions q ON q.id = a.question_id
            JOIN coach_assessment_sessions s ON s.id = a.session_id
            WHERE s.project_id = ?
        """
        values: list[object] = [project_id]
        if session_id.strip():
            query += " AND s.id = ?"
            values.append(session_id.strip())
        query += " ORDER BY r.created_at DESC, r.rowid DESC LIMIT ?"
        values.append(max(1, min(int(limit), 1000)))
        with self._connect() as conn:
            rows = conn.execute(query, values).fetchall()
        return [_assessment_result_from_row(row) for row in rows]

    def create_coach_learning_plan(
        self,
        project_id: str,
        based_on_run_id: str,
        items: Iterable[Mapping[str, Any]],
    ) -> CoachLearningPlan:
        clean_project_id = _required_text_value(project_id, "project_id")
        clean_run_id = _required_text_value(based_on_run_id, "based_on_run_id")
        item_drafts = list(items)
        if not item_drafts:
            raise ValueError("learning plan requires at least one item")
        plan_id = str(uuid.uuid4())
        now = _utc_now()

        with self._connect() as conn:
            _require_project(conn, clean_project_id)
            _require_analysis_run(conn, clean_project_id, clean_run_id)
            revision = int(
                conn.execute(
                    """
                    SELECT COALESCE(MAX(revision), 0) + 1 AS next_revision
                    FROM coach_learning_plans
                    WHERE project_id = ?
                    """,
                    (clean_project_id,),
                ).fetchone()["next_revision"]
            )
            conn.execute(
                """
                INSERT INTO coach_learning_plans
                    (id, project_id, revision, status, based_on_run_id,
                     created_at, confirmed_at)
                VALUES (?, ?, ?, 'draft', ?, ?, '')
                """,
                (plan_id, clean_project_id, revision, clean_run_id, now),
            )
            _replace_learning_plan_items(
                conn,
                clean_project_id,
                plan_id,
                item_drafts,
            )

        plan = self.get_coach_learning_plan(clean_project_id, plan_id)
        if not plan:
            raise RuntimeError("created learning plan was not found")
        return plan

    def get_coach_learning_plan(
        self,
        project_id: str,
        plan_id: str,
    ) -> CoachLearningPlan | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, project_id, revision, status, based_on_run_id,
                       created_at, confirmed_at
                FROM coach_learning_plans
                WHERE id = ? AND project_id = ?
                """,
                (plan_id, project_id),
            ).fetchone()
            if not row:
                return None
            items = _learning_plan_items(conn, plan_id)
        return _learning_plan_from_row(row, items)

    def list_coach_learning_plans(
        self,
        project_id: str,
        status: str = "",
        limit: int = 100,
    ) -> list[CoachLearningPlan]:
        clean_status = status.strip()
        if clean_status:
            _enum_value(clean_status, "status", LEARNING_PLAN_STATUSES)
        query = """
            SELECT id, project_id, revision, status, based_on_run_id,
                   created_at, confirmed_at
            FROM coach_learning_plans
            WHERE project_id = ?
        """
        values: list[object] = [project_id]
        if clean_status:
            query += " AND status = ?"
            values.append(clean_status)
        query += " ORDER BY revision DESC LIMIT ?"
        values.append(max(1, min(int(limit), 500)))
        with self._connect() as conn:
            rows = conn.execute(query, values).fetchall()
            return [
                _learning_plan_from_row(
                    row,
                    _learning_plan_items(conn, str(row["id"])),
                )
                for row in rows
            ]

    def update_coach_learning_plan(
        self,
        project_id: str,
        plan_id: str,
        items: Iterable[Mapping[str, Any]],
    ) -> CoachLearningPlan:
        item_drafts = list(items)
        if not item_drafts:
            raise ValueError("learning plan requires at least one item")
        with self._connect() as conn:
            row = _learning_plan_row(conn, project_id, plan_id)
            if not row:
                raise ValueError("learning plan not found")
            if row["status"] != "draft":
                raise ValueError("only draft learning plans can be updated")
            _replace_learning_plan_items(conn, project_id, plan_id, item_drafts)
        plan = self.get_coach_learning_plan(project_id, plan_id)
        if not plan:
            raise RuntimeError("learning plan was not found after update")
        return plan

    def confirm_coach_learning_plan(
        self,
        project_id: str,
        plan_id: str,
    ) -> CoachLearningPlan:
        now = _utc_now()
        with self._connect() as conn:
            row = _learning_plan_row(conn, project_id, plan_id)
            if not row:
                raise ValueError("learning plan not found")
            if row["status"] == "confirmed":
                pass
            elif row["status"] != "draft":
                raise ValueError("only draft learning plans can be confirmed")
            else:
                run_row = conn.execute(
                    """
                    SELECT status
                    FROM coach_analysis_runs
                    WHERE id = ? AND project_id = ?
                    """,
                    (row["based_on_run_id"], project_id),
                ).fetchone()
                if not run_row or run_row["status"] != "completed":
                    raise ValueError(
                        "learning plan cannot be confirmed from a stale analysis"
                    )
                item_count = int(
                    conn.execute(
                        """
                        SELECT COUNT(*) AS total
                        FROM coach_learning_plan_items
                        WHERE plan_id = ?
                        """,
                        (plan_id,),
                    ).fetchone()["total"]
                )
                if item_count == 0:
                    raise ValueError("learning plan requires at least one item")
                conn.execute(
                    """
                    UPDATE coach_learning_plans
                    SET status = 'archived'
                    WHERE project_id = ?
                      AND status = 'confirmed'
                      AND id != ?
                    """,
                    (project_id, plan_id),
                )
                conn.execute(
                    """
                    UPDATE coach_learning_plans
                    SET status = 'confirmed', confirmed_at = ?
                    WHERE id = ? AND project_id = ?
                    """,
                    (now, plan_id, project_id),
                )
        plan = self.get_coach_learning_plan(project_id, plan_id)
        if not plan:
            raise RuntimeError("learning plan was not found after confirmation")
        return plan

    def update_coach_learning_plan_progress(
        self,
        project_id: str,
        plan_id: str,
        item_statuses: Mapping[str, str],
    ) -> CoachLearningPlan:
        if not item_statuses:
            raise ValueError("item_statuses is required")
        with self._connect() as conn:
            plan_row = _learning_plan_row(conn, project_id, plan_id)
            if not plan_row:
                raise ValueError("learning plan not found")
            if plan_row["status"] != "confirmed":
                raise ValueError(
                    "progress can only be updated on a confirmed learning plan"
                )
            item_rows = conn.execute(
                """
                SELECT id, stable_key
                FROM coach_learning_plan_items
                WHERE plan_id = ?
                """,
                (plan_id,),
            ).fetchall()
            item_ids = {
                str(row["id"]): str(row["id"])
                for row in item_rows
            }
            item_ids.update(
                {
                    str(row["stable_key"]): str(row["id"])
                    for row in item_rows
                }
            )
            updates: list[tuple[str, str]] = []
            for item_ref, raw_status in item_statuses.items():
                item_id = item_ids.get(str(item_ref).strip())
                if not item_id:
                    raise ValueError("learning plan item not found")
                status = _enum_value(
                    raw_status,
                    "status",
                    LEARNING_PLAN_ITEM_STATUSES,
                )
                updates.append((status, item_id))
            conn.executemany(
                """
                UPDATE coach_learning_plan_items
                SET status = ?
                WHERE id = ? AND plan_id = ?
                """,
                [(status, item_id, plan_id) for status, item_id in updates],
            )
        plan = self.get_coach_learning_plan(project_id, plan_id)
        if not plan:
            raise RuntimeError("learning plan was not found after progress update")
        return plan

    def archive_coach_learning_plan(
        self,
        project_id: str,
        plan_id: str,
    ) -> CoachLearningPlan:
        with self._connect() as conn:
            row = _learning_plan_row(conn, project_id, plan_id)
            if not row:
                raise ValueError("learning plan not found")
            if row["status"] != "archived":
                conn.execute(
                    """
                    UPDATE coach_learning_plans
                    SET status = 'archived'
                    WHERE id = ? AND project_id = ?
                    """,
                    (plan_id, project_id),
                )
        plan = self.get_coach_learning_plan(project_id, plan_id)
        if not plan:
            raise RuntimeError("learning plan was not found after archive")
        return plan


def _insert_learning_exercises(
    conn: sqlite3.Connection,
    step_id: str,
    exercise_drafts: Iterable[Mapping[str, Any]],
    created_at: str,
) -> None:
    seen_variants: set[str] = set()
    seen_orders: set[int] = set()
    for fallback_order, draft in enumerate(exercise_drafts):
        if not isinstance(draft, Mapping):
            raise ValueError("learning exercise must be an object")
        variant = _enum_value(
            draft.get("variant"),
            "variant",
            LEARNING_EXERCISE_VARIANTS,
        )
        if variant in seen_variants:
            raise ValueError("learning exercise variant must be unique")
        seen_variants.add(variant)
        question_type = _enum_value(
            draft.get("question_type"),
            "question_type",
            LEARNING_EXERCISE_TYPES,
        )
        sort_order = _non_negative_integer(
            draft.get("sort_order"),
            fallback_order,
            "sort_order",
        )
        if sort_order in seen_orders:
            raise ValueError("learning exercise sort_order must be unique")
        seen_orders.add(sort_order)
        expected_points = _text_list(
            draft.get("expected_points") or (),
            "expected_points",
        )
        exercise_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO coach_learning_exercises
                (id, step_id, variant, question_type, prompt,
                 expected_points_json, reference_answer, sort_order,
                 revealed_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, '', ?)
            """,
            (
                exercise_id,
                step_id,
                variant,
                question_type,
                _required_mapping_text(draft, "prompt"),
                _json_dump(expected_points),
                _required_mapping_text(draft, "reference_answer"),
                sort_order,
                created_at,
            ),
        )
        fixture = draft.get("sql_fixture")
        if question_type == "sql_query":
            if not isinstance(fixture, Mapping):
                raise ValueError("sql_query exercise requires sql_fixture")
            _insert_sql_exercise_fixture(
                conn,
                exercise_id,
                fixture,
                created_at,
            )
        elif fixture is not None:
            raise ValueError("sql_fixture is only valid for sql_query exercises")
    if "primary" not in seen_variants:
        raise ValueError("learning step requires a primary exercise")


def _insert_sql_exercise_fixture(
    conn: sqlite3.Connection,
    exercise_id: str,
    fixture: Mapping[str, Any],
    created_at: str,
) -> None:
    schema = _mapping_list(fixture.get("schema"), "schema")
    if not schema:
        raise ValueError("sql fixture schema requires at least one table")
    if len(schema) > 8:
        raise ValueError("sql fixture schema supports at most 8 tables")
    seed_rows = _seed_rows_mapping(fixture.get("seed_rows"))
    if sum(len(rows) for rows in seed_rows.values()) > 1000:
        raise ValueError("sql fixture supports at most 1000 seed rows")
    expected_columns = _non_empty_text_list(
        fixture.get("expected_columns"),
        "expected_columns",
    )
    expected_rows = _row_list(fixture.get("expected_rows"), "expected_rows")
    required_semantics = _mapping_value(
        fixture.get("required_semantics"),
        "required_semantics",
    )
    limits = _mapping_value(fixture.get("limits"), "limits")
    fixture_hash = _required_mapping_text(fixture, "fixture_hash")
    conn.execute(
        """
        INSERT INTO coach_sql_exercise_fixtures
            (exercise_id, schema_json, seed_rows_json, expected_columns_json,
             expected_rows_json, order_sensitive, required_semantics_json,
             limits_json, fixture_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            exercise_id,
            _json_dump(schema),
            _json_dump(seed_rows),
            _json_dump(expected_columns),
            _json_dump(expected_rows),
            int(bool(fixture.get("order_sensitive", False))),
            _json_dump(required_semantics),
            _json_dump(limits),
            fixture_hash,
            created_at,
        ),
    )


def _require_learning_plan_link(
    conn: sqlite3.Connection,
    project_id: str,
    analysis_run_id: str,
    plan_id: str,
    plan_item_id: str,
) -> None:
    if not plan_id and not plan_item_id:
        return
    row = conn.execute(
        """
        SELECT p.id
        FROM coach_learning_plans p
        JOIN coach_learning_plan_items i ON i.plan_id = p.id
        WHERE p.id = ?
          AND i.id = ?
          AND p.project_id = ?
          AND p.based_on_run_id = ?
          AND p.status = 'confirmed'
          AND i.item_type = 'learning'
        """,
        (plan_id, plan_item_id, project_id, analysis_run_id),
    ).fetchone()
    if not row:
        raise ValueError(
            "learning plan item must belong to the current confirmed plan"
        )


def _learning_session_row(
    conn: sqlite3.Connection,
    project_id: str,
    session_id: str,
) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT id, project_id, analysis_run_id, target_type, target_id,
               origin_type, plan_id, plan_item_id, status, current_step_id,
               version, outcome, created_at, updated_at, completed_at,
               abandoned_at
        FROM coach_learning_sessions
        WHERE id = ? AND project_id = ?
        """,
        (session_id, project_id),
    ).fetchone()


def _active_learning_session_row(
    conn: sqlite3.Connection,
    project_id: str,
    analysis_run_id: str,
) -> sqlite3.Row | None:
    placeholders = ",".join(
        "?" for _ in LEARNING_SESSION_NON_TERMINAL_STATUSES
    )
    return conn.execute(
        f"""
        SELECT id, project_id, analysis_run_id, target_type, target_id,
               origin_type, plan_id, plan_item_id, status, current_step_id,
               version, outcome, created_at, updated_at, completed_at,
               abandoned_at
        FROM coach_learning_sessions
        WHERE project_id = ?
          AND analysis_run_id = ?
          AND status IN ({placeholders})
        ORDER BY updated_at DESC, rowid DESC
        LIMIT 1
        """,
        (
            project_id,
            analysis_run_id,
            *sorted(LEARNING_SESSION_NON_TERMINAL_STATUSES),
        ),
    ).fetchone()


def _learning_session_from_db(
    conn: sqlite3.Connection,
    project_id: str,
    session_id: str,
) -> CoachLearningSession | None:
    row = _learning_session_row(conn, project_id, session_id)
    if not row:
        return None
    step_rows = conn.execute(
        """
        SELECT id, session_id, knowledge_point_id, title, explanation,
               completion_threshold, max_attempts, status, outcome,
               sort_order, created_at, completed_at
        FROM coach_learning_steps
        WHERE session_id = ?
        ORDER BY sort_order ASC, rowid ASC
        """,
        (session_id,),
    ).fetchall()
    steps = tuple(
        _learning_step_from_row(
            conn,
            step_row,
            _learning_exercises_for_step(conn, str(step_row["id"])),
            _learning_attempts_for_step(conn, str(step_row["id"])),
        )
        for step_row in step_rows
    )
    return CoachLearningSession(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        analysis_run_id=str(row["analysis_run_id"]),
        target_type=str(row["target_type"]),
        target_id=str(row["target_id"]),
        origin_type=str(row["origin_type"]),
        plan_id=str(row["plan_id"] or ""),
        plan_item_id=str(row["plan_item_id"] or ""),
        status=str(row["status"]),
        current_step_id=str(row["current_step_id"] or ""),
        version=int(row["version"]),
        outcome=str(row["outcome"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        completed_at=str(row["completed_at"]),
        abandoned_at=str(row["abandoned_at"]),
        steps=steps,
    )


def _learning_step_from_row(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    exercises: tuple[CoachLearningExercise, ...],
    attempts: tuple[CoachLearningAttempt, ...],
) -> CoachLearningStep:
    source_rows = conn.execute(
        """
        SELECT source_id
        FROM coach_learning_step_sources
        WHERE step_id = ?
        ORDER BY sort_order ASC, rowid ASC
        """,
        (str(row["id"]),),
    ).fetchall()
    return CoachLearningStep(
        id=str(row["id"]),
        session_id=str(row["session_id"]),
        knowledge_point_id=str(row["knowledge_point_id"]),
        title=str(row["title"]),
        explanation=str(row["explanation"]),
        completion_threshold=float(row["completion_threshold"]),
        max_attempts=int(row["max_attempts"]),
        status=str(row["status"]),
        outcome=str(row["outcome"]),
        sort_order=int(row["sort_order"]),
        created_at=str(row["created_at"]),
        completed_at=str(row["completed_at"]),
        source_ids=tuple(str(source["source_id"]) for source in source_rows),
        exercises=exercises,
        attempts=attempts,
    )


def _learning_exercises_for_step(
    conn: sqlite3.Connection,
    step_id: str,
) -> tuple[CoachLearningExercise, ...]:
    rows = conn.execute(
        """
        SELECT id, step_id, variant, question_type, prompt,
               expected_points_json, reference_answer, sort_order,
               revealed_at, created_at
        FROM coach_learning_exercises
        WHERE step_id = ?
        ORDER BY sort_order ASC, rowid ASC
        """,
        (step_id,),
    ).fetchall()
    return tuple(_learning_exercise_from_row(conn, row) for row in rows)


def _learning_exercise_from_row(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
) -> CoachLearningExercise:
    fixture_row = conn.execute(
        """
        SELECT exercise_id, schema_json, seed_rows_json,
               expected_columns_json, expected_rows_json, order_sensitive,
               required_semantics_json, limits_json, fixture_hash, created_at
        FROM coach_sql_exercise_fixtures
        WHERE exercise_id = ?
        """,
        (str(row["id"]),),
    ).fetchone()
    return CoachLearningExercise(
        id=str(row["id"]),
        step_id=str(row["step_id"]),
        variant=str(row["variant"]),
        question_type=str(row["question_type"]),
        prompt=str(row["prompt"]),
        expected_points=tuple(_json_text_list(row["expected_points_json"])),
        reference_answer=str(row["reference_answer"]),
        sort_order=int(row["sort_order"]),
        revealed_at=str(row["revealed_at"]),
        created_at=str(row["created_at"]),
        sql_fixture=(
            _sql_exercise_fixture_from_row(fixture_row)
            if fixture_row is not None
            else None
        ),
    )


def _sql_exercise_fixture_from_row(row: sqlite3.Row) -> CoachSqlExerciseFixture:
    schema = _json_list(row["schema_json"])
    raw_seed_rows = _json_mapping(row["seed_rows_json"])
    expected_rows = _json_list(row["expected_rows_json"])
    return CoachSqlExerciseFixture(
        exercise_id=str(row["exercise_id"]),
        schema=tuple(
            dict(item) for item in schema if isinstance(item, Mapping)
        ),
        seed_rows={
            str(table_name): tuple(
                dict(item)
                for item in rows
                if isinstance(item, Mapping)
            )
            for table_name, rows in raw_seed_rows.items()
            if isinstance(rows, list)
        },
        expected_columns=tuple(
            _json_text_list(row["expected_columns_json"])
        ),
        expected_rows=tuple(
            tuple(item) if isinstance(item, list) else (item,)
            for item in expected_rows
        ),
        order_sensitive=bool(row["order_sensitive"]),
        required_semantics=_json_mapping(row["required_semantics_json"]),
        limits=_json_mapping(row["limits_json"]),
        fixture_hash=str(row["fixture_hash"]),
        created_at=str(row["created_at"]),
    )


def _learning_attempts_for_step(
    conn: sqlite3.Connection,
    step_id: str,
) -> tuple[CoachLearningAttempt, ...]:
    rows = conn.execute(
        """
        SELECT *
        FROM coach_learning_attempts
        WHERE step_id = ?
        ORDER BY attempt_no ASC, created_at ASC, id ASC
        """,
        (step_id,),
    ).fetchall()
    return tuple(_learning_attempt_from_row(row) for row in rows)


def _learning_attempt_from_row(row: sqlite3.Row) -> CoachLearningAttempt:
    return CoachLearningAttempt(
        id=str(row["id"]),
        session_id=str(row["session_id"]),
        step_id=str(row["step_id"]),
        exercise_id=str(row["exercise_id"]),
        attempt_no=int(row["attempt_no"]),
        idempotency_key=str(row["idempotency_key"]),
        request_hash=str(row["request_hash"]),
        answer=str(row["answer"]),
        status=str(row["status"]),
        evaluator=str(row["evaluator"]),
        score=(float(row["score"]) if row["score"] is not None else None),
        confidence=(
            float(row["confidence"])
            if row["confidence"] is not None
            else None
        ),
        feedback=str(row["feedback"]),
        error_code=str(row["error_code"]),
        error_message=str(row["error_message"]),
        result_preview=_json_load(row["result_preview_json"]),
        scoring_details=_json_mapping(row["scoring_details_json"]),
        counts_for_mastery=bool(row["counts_for_mastery"]),
        created_at=str(row["created_at"]),
        evaluated_at=str(row["evaluated_at"]),
    )


def _learning_attempt_row(
    conn: sqlite3.Connection,
    project_id: str,
    attempt_id: str,
) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT a.*
        FROM coach_learning_attempts a
        JOIN coach_learning_sessions s ON s.id = a.session_id
        WHERE a.id = ? AND s.project_id = ?
        """,
        (attempt_id, project_id),
    ).fetchone()


def _learning_attempt_by_idempotency(
    conn: sqlite3.Connection,
    project_id: str,
    session_id: str,
    idempotency_key: str,
) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT a.*
        FROM coach_learning_attempts a
        JOIN coach_learning_sessions s ON s.id = a.session_id
        WHERE a.session_id = ?
          AND a.idempotency_key = ?
          AND s.project_id = ?
        """,
        (session_id, idempotency_key, project_id),
    ).fetchone()


def _require_learning_step(
    conn: sqlite3.Connection,
    session_id: str,
    step_id: str,
) -> None:
    row = conn.execute(
        """
        SELECT id
        FROM coach_learning_steps
        WHERE id = ? AND session_id = ?
        """,
        (step_id, session_id),
    ).fetchone()
    if not row:
        raise ValueError("learning step does not belong to session")


def _sync_linked_learning_plan_item(
    conn: sqlite3.Connection,
    session_row: sqlite3.Row,
    desired_status: str,
) -> str:
    plan_id = str(session_row["plan_id"] or "")
    plan_item_id = str(session_row["plan_item_id"] or "")
    if not plan_id or not plan_item_id:
        return "not_linked"
    if not desired_status:
        return "unchanged"
    row = conn.execute(
        """
        SELECT i.status
        FROM coach_learning_plans p
        JOIN coach_learning_plan_items i ON i.plan_id = p.id
        WHERE p.id = ?
          AND i.id = ?
          AND p.project_id = ?
          AND p.based_on_run_id = ?
          AND p.status = 'confirmed'
          AND i.item_type = 'learning'
        """,
        (
            plan_id,
            plan_item_id,
            str(session_row["project_id"]),
            str(session_row["analysis_run_id"]),
        ),
    ).fetchone()
    if not row:
        return "detached"
    current_status = str(row["status"])
    if current_status in {"done", "skipped"}:
        return "unchanged"
    if desired_status == "in_progress" and current_status != "todo":
        return "unchanged"
    conn.execute(
        """
        UPDATE coach_learning_plan_items
        SET status = ?
        WHERE id = ? AND plan_id = ?
          AND status IN ('todo', 'in_progress')
        """,
        (desired_status, plan_item_id, plan_id),
    )
    return "updated"


def _replace_learning_plan_items(
    conn: sqlite3.Connection,
    project_id: str,
    plan_id: str,
    drafts: list[Mapping[str, Any]],
) -> None:
    existing_rows = conn.execute(
        """
        SELECT id, stable_key
        FROM coach_learning_plan_items
        WHERE plan_id = ?
        """,
        (plan_id,),
    ).fetchall()
    existing_ids = {str(row["stable_key"]): str(row["id"]) for row in existing_rows}
    seen_keys: set[str] = set()
    seen_orders: set[int] = set()
    normalized: list[tuple[Mapping[str, Any], str, int]] = []

    for index, draft in enumerate(drafts):
        if not isinstance(draft, Mapping):
            raise ValueError("learning plan items must be objects")
        stable_key = _required_mapping_text(draft, "stable_key")
        if stable_key in seen_keys:
            raise ValueError("learning plan item stable_key must be unique")
        seen_keys.add(stable_key)
        sort_order = _integer(draft.get("sort_order"), index)
        if sort_order in seen_orders:
            raise ValueError("learning plan item sort_order must be unique")
        seen_orders.add(sort_order)
        normalized.append((draft, stable_key, sort_order))

    if existing_ids:
        conn.execute(
            "DELETE FROM coach_learning_plan_items WHERE plan_id = ?",
            (plan_id,),
        )

    for draft, stable_key, sort_order in normalized:
        item_type = _enum_value(
            draft.get("item_type") or "learning",
            "item_type",
            LEARNING_PLAN_ITEM_TYPES,
        )
        item_status = _enum_value(
            draft.get("status") or "todo",
            "status",
            LEARNING_PLAN_ITEM_STATUSES,
        )
        knowledge_point_id = str(draft.get("knowledge_point_id") or "").strip()
        skill_node_id = str(draft.get("skill_node_id") or "").strip()
        if item_type == "learning" and not (knowledge_point_id or skill_node_id):
            raise ValueError(
                "learning plan item requires a knowledge point or skill node"
            )
        if knowledge_point_id:
            _require_knowledge_point(conn, project_id, knowledge_point_id)
        if skill_node_id:
            _require_project_skill(conn, project_id, skill_node_id)
        source_ids = _text_list(draft.get("source_ids") or (), "source_ids")
        if item_type == "learning" and not source_ids:
            raise ValueError("learning item requires at least one source")
        if source_ids:
            _require_sources_for_project(conn, project_id, source_ids)
        estimated_minutes = _integer(draft.get("estimated_minutes"), 0)
        if estimated_minutes <= 0:
            raise ValueError("estimated_minutes must be greater than zero")

        conn.execute(
            """
            INSERT INTO coach_learning_plan_items
                (id, plan_id, stable_key, item_type, objective,
                 knowledge_point_id, skill_node_id, source_ids_json,
                 practice_question, completion_criteria, estimated_minutes,
                 status, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                existing_ids.get(stable_key, str(uuid.uuid4())),
                plan_id,
                stable_key,
                item_type,
                _required_mapping_text(draft, "objective"),
                knowledge_point_id or None,
                skill_node_id or None,
                _json_dump(source_ids),
                _required_mapping_text(draft, "practice_question"),
                _required_mapping_text(draft, "completion_criteria"),
                estimated_minutes,
                item_status,
                sort_order,
            ),
        )


def _require_project(conn: sqlite3.Connection, project_id: str) -> None:
    row = conn.execute("SELECT id FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise ValueError("project not found")


def _require_assessment_target(
    conn: sqlite3.Connection,
    project_id: str,
    run_id: str,
    target_type: str,
    target_id: str,
) -> None:
    if target_type == "knowledge_point":
        _require_knowledge_point(conn, project_id, target_id)
        row = conn.execute(
            """
            SELECT id
            FROM coach_knowledge_sources
            WHERE run_id = ? AND knowledge_point_id = ?
            LIMIT 1
            """,
            (run_id, target_id),
        ).fetchone()
        if not row:
            raise ValueError("knowledge point is not part of analysis run")
    else:
        row = conn.execute(
            """
            WITH RECURSIVE skill_descendants(id) AS (
                SELECT id
                FROM coach_skill_nodes
                WHERE id = ?
                UNION ALL
                SELECT n.id
                FROM coach_skill_nodes n
                JOIN skill_descendants d ON n.parent_id = d.id
            )
            SELECT m.id
            FROM coach_knowledge_skill_mappings m
            JOIN coach_analysis_runs r ON r.id = m.run_id
            WHERE m.run_id = ?
              AND m.skill_node_id IN (SELECT id FROM skill_descendants)
              AND r.project_id = ?
            LIMIT 1
            """,
            (target_id, run_id, project_id),
        ).fetchone()
        if not row:
            raise ValueError("skill node has no evidence in analysis run")


def _require_question_knowledge_point(
    conn: sqlite3.Connection,
    project_id: str,
    run_id: str,
    target_type: str,
    target_id: str,
    knowledge_point_id: str,
) -> None:
    _require_knowledge_point(conn, project_id, knowledge_point_id)
    if target_type == "knowledge_point" and knowledge_point_id != target_id:
        raise ValueError("question knowledge point must match assessment target")
    if target_type == "skill":
        row = conn.execute(
            """
            WITH RECURSIVE skill_descendants(id) AS (
                SELECT id
                FROM coach_skill_nodes
                WHERE id = ?
                UNION ALL
                SELECT n.id
                FROM coach_skill_nodes n
                JOIN skill_descendants d ON n.parent_id = d.id
            )
            SELECT id
            FROM coach_knowledge_skill_mappings
            WHERE run_id = ?
              AND knowledge_point_id = ?
              AND skill_node_id IN (SELECT id FROM skill_descendants)
            LIMIT 1
            """,
            (target_id, run_id, knowledge_point_id),
        ).fetchone()
        if not row:
            raise ValueError(
                "question knowledge point is not mapped to target skill"
            )


def _require_knowledge_point(
    conn: sqlite3.Connection,
    project_id: str,
    knowledge_point_id: str,
) -> None:
    row = conn.execute(
        """
        SELECT id
        FROM coach_knowledge_points
        WHERE id = ? AND project_id = ?
        """,
        (knowledge_point_id, project_id),
    ).fetchone()
    if not row:
        raise ValueError("knowledge point does not belong to project")


def _require_project_skill(
    conn: sqlite3.Connection,
    project_id: str,
    skill_node_id: str,
) -> None:
    row = conn.execute(
        """
        WITH RECURSIVE skill_descendants(id) AS (
            SELECT id
            FROM coach_skill_nodes
            WHERE id = ?
            UNION ALL
            SELECT n.id
            FROM coach_skill_nodes n
            JOIN skill_descendants d ON n.parent_id = d.id
        )
        SELECT m.id
        FROM coach_knowledge_skill_mappings m
        JOIN coach_analysis_runs r ON r.id = m.run_id
        WHERE m.skill_node_id IN (SELECT id FROM skill_descendants)
          AND r.project_id = ?
        LIMIT 1
        """,
        (skill_node_id, project_id),
    ).fetchone()
    if not row:
        raise ValueError("skill node has no evidence in project")


def _require_sources_for_project(
    conn: sqlite3.Connection,
    project_id: str,
    source_ids: Iterable[str],
) -> None:
    unique_ids = set(source_ids)
    if not unique_ids:
        return
    placeholders = ",".join("?" for _ in unique_ids)
    rows = conn.execute(
        f"""
        SELECT s.id
        FROM coach_knowledge_sources s
        JOIN coach_analysis_runs r ON r.id = s.run_id
        WHERE r.project_id = ? AND s.id IN ({placeholders})
        """,
        (project_id, *sorted(unique_ids)),
    ).fetchall()
    if {str(row["id"]) for row in rows} != unique_ids:
        raise ValueError("source does not belong to project")


def _require_sources_for_analysis_run(
    conn: sqlite3.Connection,
    project_id: str,
    run_id: str,
    source_ids: Iterable[str],
    knowledge_point_id: str,
) -> None:
    unique_ids = set(source_ids)
    placeholders = ",".join("?" for _ in unique_ids)
    rows = conn.execute(
        f"""
        SELECT s.id
        FROM coach_knowledge_sources s
        JOIN coach_analysis_runs r ON r.id = s.run_id
        WHERE r.project_id = ?
          AND s.run_id = ?
          AND s.knowledge_point_id = ?
          AND s.id IN ({placeholders})
        """,
        (project_id, run_id, knowledge_point_id, *sorted(unique_ids)),
    ).fetchall()
    if {str(row["id"]) for row in rows} != unique_ids:
        raise ValueError(
            "question source must belong to its knowledge point and analysis run"
        )


def _require_analysis_run(
    conn: sqlite3.Connection,
    project_id: str,
    run_id: str,
) -> None:
    row = conn.execute(
        """
        SELECT id
        FROM coach_analysis_runs
        WHERE id = ? AND project_id = ?
        """,
        (run_id, project_id),
    ).fetchone()
    if not row:
        raise ValueError("analysis run does not belong to project")


def _assessment_session_row(
    conn: sqlite3.Connection,
    project_id: str,
    session_id: str,
) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT id, project_id, analysis_run_id, target_type, target_id, status,
               created_at, completed_at
        FROM coach_assessment_sessions
        WHERE id = ? AND project_id = ?
        """,
        (session_id, project_id),
    ).fetchone()


def _active_assessment_session_row(
    conn: sqlite3.Connection,
    project_id: str,
    analysis_run_id: str,
    target_type: str,
    target_id: str,
) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT id, project_id, analysis_run_id, target_type, target_id, status,
               created_at, completed_at
        FROM coach_assessment_sessions
        WHERE project_id = ?
          AND analysis_run_id = ?
          AND target_type = ?
          AND target_id = ?
          AND status = 'active'
        LIMIT 1
        """,
        (project_id, analysis_run_id, target_type, target_id),
    ).fetchone()


def _assessment_questions_for_session(
    conn: sqlite3.Connection,
    session_id: str,
) -> tuple[CoachAssessmentQuestion, ...]:
    rows = conn.execute(
        """
        SELECT id, session_id, knowledge_point_id, prompt, question_type,
               expected_points_json, source_ids_json, sort_order
        FROM coach_assessment_questions
        WHERE session_id = ?
        ORDER BY sort_order ASC, rowid ASC
        """,
        (session_id,),
    ).fetchall()
    return tuple(_assessment_question_from_row(row) for row in rows)


def _assessment_session_from_row(
    row: sqlite3.Row,
    questions: tuple[CoachAssessmentQuestion, ...],
) -> CoachAssessmentSession:
    return CoachAssessmentSession(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        analysis_run_id=str(row["analysis_run_id"]),
        target_type=str(row["target_type"]),
        target_id=str(row["target_id"]),
        status=str(row["status"]),
        created_at=str(row["created_at"]),
        completed_at=str(row["completed_at"]),
        questions=questions,
    )


def _assessment_question_from_row(row: sqlite3.Row) -> CoachAssessmentQuestion:
    return CoachAssessmentQuestion(
        id=str(row["id"]),
        session_id=str(row["session_id"]),
        knowledge_point_id=str(row["knowledge_point_id"]),
        prompt=str(row["prompt"]),
        question_type=str(row["question_type"]),
        expected_points=tuple(_json_text_list(row["expected_points_json"])),
        source_ids=tuple(_json_text_list(row["source_ids_json"])),
        sort_order=int(row["sort_order"]),
    )


def _assessment_answer_from_row(row: sqlite3.Row) -> CoachAssessmentAnswer:
    return CoachAssessmentAnswer(
        id=str(row["id"]),
        session_id=str(row["session_id"]),
        question_id=str(row["question_id"]),
        answer=str(row["answer"]),
        created_at=str(row["created_at"]),
    )


def _assessment_result_row_for_answer(
    conn: sqlite3.Connection,
    project_id: str,
    answer_id: str,
) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT r.id, s.project_id, s.id AS session_id, q.id AS question_id,
               q.knowledge_point_id, r.answer_id, r.evaluator, r.score,
               r.confidence, r.status, r.evaluation_warning, r.feedback,
               r.matched_evidence_json, r.missing_points_json,
               r.source_ids_json, r.created_at
        FROM coach_assessment_results r
        JOIN coach_assessment_answers a ON a.id = r.answer_id
        JOIN coach_assessment_questions q ON q.id = a.question_id
        JOIN coach_assessment_sessions s ON s.id = a.session_id
        WHERE r.answer_id = ? AND s.project_id = ?
        """,
        (answer_id, project_id),
    ).fetchone()


def _assessment_result_from_row(row: sqlite3.Row) -> CoachAssessmentResult:
    evidence = _json_list(row["matched_evidence_json"])
    return CoachAssessmentResult(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        session_id=str(row["session_id"]),
        question_id=str(row["question_id"]),
        knowledge_point_id=str(row["knowledge_point_id"]),
        answer_id=str(row["answer_id"]),
        evaluator=str(row["evaluator"]),
        score=float(row["score"]),
        confidence=float(row["confidence"]),
        status=str(row["status"]),
        matched_evidence=tuple(
            dict(item) if isinstance(item, Mapping) else {"text": str(item)}
            for item in evidence
        ),
        missing_points=tuple(_json_text_list(row["missing_points_json"])),
        source_ids=tuple(_json_text_list(row["source_ids_json"])),
        created_at=str(row["created_at"]),
        evaluation_warning=str(row["evaluation_warning"]),
        feedback=str(row["feedback"]),
    )


def _learning_plan_row(
    conn: sqlite3.Connection,
    project_id: str,
    plan_id: str,
) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT id, project_id, revision, status, based_on_run_id,
               created_at, confirmed_at
        FROM coach_learning_plans
        WHERE id = ? AND project_id = ?
        """,
        (plan_id, project_id),
    ).fetchone()


def _learning_plan_items(
    conn: sqlite3.Connection,
    plan_id: str,
) -> tuple[CoachLearningPlanItem, ...]:
    rows = conn.execute(
        """
        SELECT id, plan_id, stable_key, item_type, objective,
               knowledge_point_id, skill_node_id, source_ids_json,
               practice_question, completion_criteria, estimated_minutes,
               status, sort_order
        FROM coach_learning_plan_items
        WHERE plan_id = ?
        ORDER BY sort_order ASC, rowid ASC
        """,
        (plan_id,),
    ).fetchall()
    return tuple(_learning_plan_item_from_row(row) for row in rows)


def _learning_plan_from_row(
    row: sqlite3.Row,
    items: tuple[CoachLearningPlanItem, ...],
) -> CoachLearningPlan:
    return CoachLearningPlan(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        revision=int(row["revision"]),
        status=str(row["status"]),
        based_on_run_id=str(row["based_on_run_id"] or ""),
        created_at=str(row["created_at"]),
        confirmed_at=str(row["confirmed_at"]),
        items=items,
    )


def _learning_plan_item_from_row(row: sqlite3.Row) -> CoachLearningPlanItem:
    return CoachLearningPlanItem(
        id=str(row["id"]),
        plan_id=str(row["plan_id"]),
        stable_key=str(row["stable_key"]),
        item_type=str(row["item_type"]),
        objective=str(row["objective"]),
        knowledge_point_id=str(row["knowledge_point_id"] or ""),
        skill_node_id=str(row["skill_node_id"] or ""),
        source_ids=tuple(_json_text_list(row["source_ids_json"])),
        practice_question=str(row["practice_question"]),
        completion_criteria=str(row["completion_criteria"]),
        estimated_minutes=int(row["estimated_minutes"]),
        status=str(row["status"]),
        sort_order=int(row["sort_order"]),
    )


def _assessment_status(score: float) -> str:
    if score < 0.50:
        return "needs_work"
    if score < 0.75:
        return "developing"
    return "mastered"


def _validated_evidence_list(
    values: Iterable[Mapping[str, Any] | str],
    expected_points: Iterable[str],
    answer: str,
) -> list[dict[str, Any]]:
    allowed_points = set(expected_points)
    normalized_answer = answer.casefold()
    result: list[dict[str, Any]] = []
    for value in values:
        if isinstance(value, Mapping):
            item = dict(value)
            point = str(item.get("point") or "").strip()
            evidence = str(item.get("evidence") or "").strip()
        else:
            text = str(value).strip()
            point = text
            evidence = text
            item = {}
        if not point or point not in allowed_points:
            raise ValueError(
                "matched evidence point must belong to the question scoring basis"
            )
        if not evidence or evidence.casefold() not in normalized_answer:
            raise ValueError(
                "matched evidence must be a verbatim excerpt from the answer"
            )
        item["point"] = point
        item["evidence"] = evidence
        result.append(item)
    return result


def _non_empty_text_list(value: object, name: str) -> list[str]:
    result = _text_list(value, name)
    if not result:
        raise ValueError(f"{name} requires at least one value")
    return result


def _text_list(value: object, name: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Iterable):
        raise ValueError(f"{name} must be a list")
    result: list[str] = []
    seen: set[str] = set()
    for raw_value in value:
        clean_value = str(raw_value).strip()
        if clean_value and clean_value not in seen:
            result.append(clean_value)
            seen.add(clean_value)
    return result


def _required_mapping_text(mapping: Mapping[str, Any], key: str) -> str:
    return _required_text_value(mapping.get(key), key)


def _required_text_value(value: object, name: str) -> str:
    clean_value = str(value or "").strip()
    if not clean_value:
        raise ValueError(f"{name} is required")
    return clean_value


def _enum_value(value: object, name: str, allowed: set[str]) -> str:
    clean_value = _required_text_value(value, name)
    if clean_value not in allowed:
        raise ValueError(f"{name} must be one of: {', '.join(sorted(allowed))}")
    return clean_value


def _unit_interval(value: object, name: str) -> float:
    try:
        clean_value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc
    if clean_value < 0.0 or clean_value > 1.0:
        raise ValueError(f"{name} must be between 0 and 1")
    return clean_value


def _integer(value: object, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _positive_integer(value: object, name: str) -> int:
    try:
        clean_value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive integer") from exc
    if clean_value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return clean_value


def _non_negative_integer(value: object, default: int, name: str) -> int:
    try:
        clean_value = int(value) if value is not None else default
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a non-negative integer") from exc
    if clean_value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return clean_value


def _bounded_integer(
    value: object,
    default: int,
    name: str,
    minimum: int,
    maximum: int,
) -> int:
    try:
        clean_value = int(value) if value is not None else default
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"{name} must be between {minimum} and {maximum}"
        ) from exc
    if clean_value < minimum or clean_value > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return clean_value


def _mapping_list(value: object, name: str) -> list[dict[str, Any]]:
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Iterable):
        raise ValueError(f"{name} must be a list")
    result: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError(f"{name} entries must be objects")
        result.append(dict(item))
    return result


def _mapping_value(value: object, name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return dict(value)


def _seed_rows_mapping(value: object) -> dict[str, list[dict[str, Any]]]:
    if not isinstance(value, Mapping):
        raise ValueError("seed_rows must be an object")
    result: dict[str, list[dict[str, Any]]] = {}
    for raw_table_name, raw_rows in value.items():
        table_name = str(raw_table_name).strip()
        if not table_name:
            raise ValueError("seed_rows table name is required")
        if (
            isinstance(raw_rows, (str, bytes, Mapping))
            or not isinstance(raw_rows, Iterable)
        ):
            raise ValueError("seed_rows table value must be a list")
        rows: list[dict[str, Any]] = []
        for raw_row in raw_rows:
            if not isinstance(raw_row, Mapping):
                raise ValueError("seed_rows entries must be objects")
            rows.append(dict(raw_row))
        result[table_name] = rows
    return result


def _row_list(value: object, name: str) -> list[list[Any]]:
    if isinstance(value, (str, bytes, Mapping)) or not isinstance(value, Iterable):
        raise ValueError(f"{name} must be a list")
    result: list[list[Any]] = []
    for row in value:
        if (
            isinstance(row, (str, bytes, Mapping))
            or not isinstance(row, Iterable)
        ):
            raise ValueError(f"{name} entries must be lists")
        result.append(list(row))
    return result


def _json_dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False)


def _json_list(value: object) -> list[Any]:
    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _json_text_list(value: object) -> list[str]:
    return [str(item) for item in _json_list(value) if str(item).strip()]


def _json_mapping(value: object) -> dict[str, Any]:
    parsed = _json_load(value)
    return dict(parsed) if isinstance(parsed, Mapping) else {}


def _json_load(value: object) -> Any:
    try:
        return json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "ASSESSMENT_EVALUATORS",
    "ASSESSMENT_RESULT_STATUSES",
    "ASSESSMENT_SESSION_STATUSES",
    "ASSESSMENT_TARGET_TYPES",
    "CoachProgressStoreMixin",
    "LEARNING_ATTEMPT_EVALUATORS",
    "LEARNING_ATTEMPT_STATUSES",
    "LEARNING_EXERCISE_TYPES",
    "LEARNING_EXERCISE_VARIANTS",
    "LEARNING_OUTCOMES",
    "LEARNING_PLAN_ITEM_STATUSES",
    "LEARNING_PLAN_ITEM_TYPES",
    "LEARNING_PLAN_STATUSES",
    "LEARNING_SESSION_ORIGIN_TYPES",
    "LEARNING_SESSION_STATUSES",
    "LEARNING_SESSION_TARGET_TYPES",
    "LEARNING_STEP_STATUSES",
]
