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


__all__ = [
    "CoachAnalysisRun",
    "CoachKnowledgePoint",
    "CoachKnowledgeSkillMapping",
    "CoachKnowledgeSource",
    "CoachSkillNode",
    "CoachSkillTaxonomy",
]
