from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CoachAnalysisRun:
    id: str
    project_id: str
    analyzer_version: str
    source_fingerprint: str
    status: str
    summary: dict[str, Any]
    started_at: str
    finished_at: str

    def to_dict(self) -> dict[str, Any]:
        data = {
            "id": self.id,
            "project_id": self.project_id,
            "analyzer_version": self.analyzer_version,
            "source_fingerprint": self.source_fingerprint,
            "status": self.status,
            "summary": self.summary,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }
        for key, default in (
            ("source_count", 0),
            ("knowledge_point_count", 0),
            ("skill_mapping_count", 0),
            ("enhancement_mode", "rule"),
            ("warning", ""),
        ):
            data[key] = self.summary.get(key, default)
        return data


@dataclass(frozen=True)
class CoachKnowledgeSource:
    id: str
    run_id: str
    knowledge_point_id: str
    document_id: str
    source_path: str
    chunk_id: str
    source_hash: str
    excerpt: str
    locator: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "knowledge_point_id": self.knowledge_point_id,
            "document_id": self.document_id,
            "source_path": self.source_path,
            "chunk_id": self.chunk_id,
            "source_hash": self.source_hash,
            "excerpt": self.excerpt,
            "locator": self.locator,
        }


@dataclass(frozen=True)
class CoachKnowledgePoint:
    id: str
    project_id: str
    stable_key: str
    title: str
    category: str
    summary: str
    current_run_id: str
    created_at: str
    updated_at: str
    sources: tuple[CoachKnowledgeSource, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "stable_key": self.stable_key,
            "title": self.title,
            "category": self.category,
            "summary": self.summary,
            "current_run_id": self.current_run_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "sources": [source.to_dict() for source in self.sources],
        }


@dataclass(frozen=True)
class CoachSkillTaxonomy:
    id: str
    version: str
    name: str
    status: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class CoachSkillNode:
    id: str
    taxonomy_id: str
    stable_key: str
    parent_id: str
    name: str
    category: str
    sort_order: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "taxonomy_id": self.taxonomy_id,
            "stable_key": self.stable_key,
            "parent_id": self.parent_id,
            "name": self.name,
            "category": self.category,
            "sort_order": self.sort_order,
        }


@dataclass(frozen=True)
class CoachKnowledgeSkillMapping:
    id: str
    run_id: str
    knowledge_point_id: str
    knowledge_point_key: str
    skill_node_id: str
    skill_key: str
    confidence: float
    source_id: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "knowledge_point_id": self.knowledge_point_id,
            "knowledge_point_key": self.knowledge_point_key,
            "skill_node_id": self.skill_node_id,
            "skill_key": self.skill_key,
            "confidence": self.confidence,
            "source_id": self.source_id,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class CoachAssessmentQuestion:
    id: str
    session_id: str
    knowledge_point_id: str
    prompt: str
    question_type: str
    expected_points: tuple[str, ...]
    source_ids: tuple[str, ...]
    sort_order: int

    def to_dict(self, include_scoring_basis: bool = False) -> dict[str, Any]:
        data = {
            "id": self.id,
            "session_id": self.session_id,
            "knowledge_point_id": self.knowledge_point_id,
            "prompt": self.prompt,
            "question_type": self.question_type,
            "source_ids": list(self.source_ids),
            "sort_order": self.sort_order,
        }
        if include_scoring_basis:
            data["expected_points"] = list(self.expected_points)
        return data


@dataclass(frozen=True)
class CoachAssessmentSession:
    id: str
    project_id: str
    analysis_run_id: str
    target_type: str
    target_id: str
    status: str
    created_at: str
    completed_at: str
    questions: tuple[CoachAssessmentQuestion, ...] = field(default_factory=tuple)

    def to_dict(self, include_scoring_basis: bool = False) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "analysis_run_id": self.analysis_run_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "questions": [
                question.to_dict(include_scoring_basis=include_scoring_basis)
                for question in self.questions
            ],
        }


@dataclass(frozen=True)
class CoachAssessmentAnswer:
    id: str
    session_id: str
    question_id: str
    answer: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "question_id": self.question_id,
            "answer": self.answer,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class CoachAssessmentResult:
    id: str
    project_id: str
    session_id: str
    question_id: str
    knowledge_point_id: str
    answer_id: str
    evaluator: str
    score: float
    confidence: float
    status: str
    matched_evidence: tuple[dict[str, Any], ...]
    missing_points: tuple[str, ...]
    source_ids: tuple[str, ...]
    created_at: str
    evaluation_warning: str = ""
    feedback: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "question_id": self.question_id,
            "knowledge_point_id": self.knowledge_point_id,
            "answer_id": self.answer_id,
            "evaluator": self.evaluator,
            "score": self.score,
            "confidence": self.confidence,
            "status": self.status,
            "matched_evidence": [dict(item) for item in self.matched_evidence],
            "missing_points": list(self.missing_points),
            "source_ids": list(self.source_ids),
            "created_at": self.created_at,
            "evaluation_warning": self.evaluation_warning,
            "feedback": self.feedback,
        }


@dataclass(frozen=True)
class CoachSqlExerciseFixture:
    exercise_id: str
    schema: tuple[dict[str, Any], ...]
    seed_rows: dict[str, tuple[dict[str, Any], ...]]
    expected_columns: tuple[str, ...]
    expected_rows: tuple[tuple[Any, ...], ...]
    order_sensitive: bool
    required_semantics: dict[str, Any]
    limits: dict[str, Any]
    fixture_hash: str
    created_at: str

    def to_dict(self, include_scoring_basis: bool = False) -> dict[str, Any]:
        data = {
            "schema": [dict(table) for table in self.schema],
            "seed_rows": {
                table_name: [dict(row) for row in rows]
                for table_name, rows in self.seed_rows.items()
            },
        }
        if include_scoring_basis:
            data.update(
                {
                    "expected_columns": list(self.expected_columns),
                    "expected_rows": [list(row) for row in self.expected_rows],
                    "order_sensitive": self.order_sensitive,
                    "required_semantics": dict(self.required_semantics),
                    "limits": dict(self.limits),
                    "fixture_hash": self.fixture_hash,
                }
            )
        return data


@dataclass(frozen=True)
class CoachLearningExercise:
    id: str
    step_id: str
    variant: str
    question_type: str
    prompt: str
    expected_points: tuple[str, ...]
    reference_answer: str
    sort_order: int
    revealed_at: str
    created_at: str
    sql_fixture: CoachSqlExerciseFixture | None = None

    def to_dict(self, include_scoring_basis: bool = False) -> dict[str, Any]:
        data = {
            "id": self.id,
            "step_id": self.step_id,
            "variant": self.variant,
            "variant_no": 1 if self.variant == "primary" else 2,
            "question_type": self.question_type,
            "prompt": self.prompt,
            "sort_order": self.sort_order,
            "revealed_at": self.revealed_at,
        }
        if self.sql_fixture is not None:
            data["sql_fixture"] = self.sql_fixture.to_dict(
                include_scoring_basis=include_scoring_basis
            )
        if include_scoring_basis:
            data["expected_points"] = list(self.expected_points)
            data["reference_answer"] = self.reference_answer
        return data


@dataclass(frozen=True)
class CoachLearningAttempt:
    id: str
    session_id: str
    step_id: str
    exercise_id: str
    attempt_no: int
    idempotency_key: str
    request_hash: str
    answer: str
    status: str
    evaluator: str
    score: float | None
    confidence: float | None
    feedback: str
    error_code: str
    error_message: str
    result_preview: Any
    scoring_details: dict[str, Any]
    counts_for_mastery: bool
    created_at: str
    evaluated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "step_id": self.step_id,
            "exercise_id": self.exercise_id,
            "attempt_no": self.attempt_no,
            "answer": self.answer,
            "status": self.status,
            "evaluator": self.evaluator,
            "score": self.score,
            "confidence": self.confidence,
            "feedback": self.feedback,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "result_preview": self.result_preview,
            "scoring_details": dict(self.scoring_details),
            "counts_for_mastery": self.counts_for_mastery,
            "created_at": self.created_at,
            "evaluated_at": self.evaluated_at,
        }


@dataclass(frozen=True)
class CoachLearningStep:
    id: str
    session_id: str
    knowledge_point_id: str
    title: str
    explanation: str
    completion_threshold: float
    max_attempts: int
    status: str
    outcome: str
    sort_order: int
    created_at: str
    completed_at: str
    source_ids: tuple[str, ...] = field(default_factory=tuple)
    exercises: tuple[CoachLearningExercise, ...] = field(default_factory=tuple)
    attempts: tuple[CoachLearningAttempt, ...] = field(default_factory=tuple)

    @property
    def current_exercise(self) -> CoachLearningExercise | None:
        if not self.exercises:
            return None
        if len(self.attempts) >= 2:
            reinforcement = next(
                (
                    exercise
                    for exercise in self.exercises
                    if exercise.variant == "reinforcement"
                ),
                None,
            )
            if reinforcement is not None:
                return reinforcement
        return self.exercises[0]

    def to_dict(
        self,
        include_scoring_basis: bool = False,
        include_all_exercises: bool = False,
    ) -> dict[str, Any]:
        current_exercise = (
            self.current_exercise
            if self.status in {"awaiting_answer", "evaluated", "retrying"}
            else None
        )
        data = {
            "id": self.id,
            "session_id": self.session_id,
            "knowledge_point_id": self.knowledge_point_id,
            "title": self.title,
            "explanation": self.explanation,
            "completion_threshold": self.completion_threshold,
            "max_attempts": self.max_attempts,
            "status": self.status,
            "outcome": self.outcome,
            "sort_order": self.sort_order,
            "completed_at": self.completed_at,
            "source_ids": list(self.source_ids),
            "attempts": [attempt.to_dict() for attempt in self.attempts],
            "current_exercise": (
                current_exercise.to_dict(
                    include_scoring_basis=include_scoring_basis
                )
                if current_exercise is not None
                else None
            ),
        }
        if include_all_exercises:
            data["exercises"] = [
                exercise.to_dict(include_scoring_basis=include_scoring_basis)
                for exercise in self.exercises
            ]
        return data


@dataclass(frozen=True)
class CoachLearningSession:
    id: str
    project_id: str
    analysis_run_id: str
    target_type: str
    target_id: str
    origin_type: str
    plan_id: str
    plan_item_id: str
    status: str
    current_step_id: str
    version: int
    outcome: str
    created_at: str
    updated_at: str
    completed_at: str
    abandoned_at: str
    steps: tuple[CoachLearningStep, ...] = field(default_factory=tuple)

    @property
    def current_step(self) -> CoachLearningStep | None:
        if self.current_step_id:
            current = next(
                (step for step in self.steps if step.id == self.current_step_id),
                None,
            )
            if current is not None:
                return current
        return self.steps[0] if self.steps else None

    def to_dict(self, include_scoring_basis: bool = False) -> dict[str, Any]:
        current_step = self.current_step
        current_index = (
            next(
                (
                    index
                    for index, step in enumerate(self.steps)
                    if current_step is not None and step.id == current_step.id
                ),
                0,
            )
            if self.steps
            else 0
        )
        data = {
            "id": self.id,
            "project_id": self.project_id,
            "analysis_run_id": self.analysis_run_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "origin_type": self.origin_type,
            "plan_id": self.plan_id,
            "plan_item_id": self.plan_item_id,
            "status": self.status,
            "current_step_id": self.current_step_id,
            "version": self.version,
            "outcome": self.outcome,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "abandoned_at": self.abandoned_at,
            "progress": {
                "current": current_index + 1 if self.steps else 0,
                "total": len(self.steps),
            },
            "current_step": (
                current_step.to_dict(
                    include_scoring_basis=include_scoring_basis,
                    include_all_exercises=False,
                )
                if current_step is not None
                else None
            ),
            "current_exercise": (
                current_step.to_dict(
                    include_scoring_basis=include_scoring_basis,
                    include_all_exercises=False,
                )["current_exercise"]
                if current_step is not None
                else None
            ),
            "attempts": (
                [attempt.to_dict() for attempt in current_step.attempts]
                if current_step is not None
                else []
            ),
        }
        if include_scoring_basis:
            data["steps"] = [
                step.to_dict(
                    include_scoring_basis=True,
                    include_all_exercises=True,
                )
                for step in self.steps
            ]
        return data


@dataclass(frozen=True)
class CoachLearningPlanItem:
    id: str
    plan_id: str
    stable_key: str
    item_type: str
    objective: str
    knowledge_point_id: str
    skill_node_id: str
    source_ids: tuple[str, ...]
    practice_question: str
    completion_criteria: str
    estimated_minutes: int
    status: str
    sort_order: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "stable_key": self.stable_key,
            "item_type": self.item_type,
            "objective": self.objective,
            "knowledge_point_id": self.knowledge_point_id,
            "skill_node_id": self.skill_node_id,
            "source_ids": list(self.source_ids),
            "practice_question": self.practice_question,
            "completion_criteria": self.completion_criteria,
            "estimated_minutes": self.estimated_minutes,
            "status": self.status,
            "sort_order": self.sort_order,
        }


@dataclass(frozen=True)
class CoachLearningPlan:
    id: str
    project_id: str
    revision: int
    status: str
    based_on_run_id: str
    created_at: str
    confirmed_at: str
    items: tuple[CoachLearningPlanItem, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "revision": self.revision,
            "status": self.status,
            "based_on_run_id": self.based_on_run_id,
            "created_at": self.created_at,
            "confirmed_at": self.confirmed_at,
            "items": [item.to_dict() for item in self.items],
        }


__all__ = [
    "CoachAssessmentAnswer",
    "CoachAssessmentQuestion",
    "CoachAssessmentResult",
    "CoachAssessmentSession",
    "CoachAnalysisRun",
    "CoachKnowledgePoint",
    "CoachKnowledgeSkillMapping",
    "CoachKnowledgeSource",
    "CoachLearningAttempt",
    "CoachLearningExercise",
    "CoachLearningPlan",
    "CoachLearningPlanItem",
    "CoachLearningSession",
    "CoachLearningStep",
    "CoachSqlExerciseFixture",
    "CoachSkillNode",
    "CoachSkillTaxonomy",
]
