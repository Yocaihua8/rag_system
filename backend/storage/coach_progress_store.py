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
    CoachLearningPlan,
    CoachLearningPlanItem,
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
            """
        )

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


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "ASSESSMENT_EVALUATORS",
    "ASSESSMENT_RESULT_STATUSES",
    "ASSESSMENT_SESSION_STATUSES",
    "ASSESSMENT_TARGET_TYPES",
    "CoachProgressStoreMixin",
    "LEARNING_PLAN_ITEM_STATUSES",
    "LEARNING_PLAN_ITEM_TYPES",
    "LEARNING_PLAN_STATUSES",
]
