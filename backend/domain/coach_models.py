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
    "CoachLearningPlan",
    "CoachLearningPlanItem",
    "CoachSkillNode",
    "CoachSkillTaxonomy",
]
