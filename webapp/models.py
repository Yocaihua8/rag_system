from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    root_path: Path
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        root_text = str(self.root_path)
        is_browser_upload = root_text.startswith("browser-upload:")
        return {
            "id": self.id,
            "name": self.name,
            "root_path": root_text,
            "root_exists": is_browser_upload or (self.root_path.exists() and self.root_path.is_dir()),
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class Document:
    id: str
    project_id: str
    source_path: Path
    relative_path: str
    content: str
    checksum: str
    updated_at: str

    def to_dict(self, include_content: bool = False) -> dict[str, Any]:
        data = {
            "id": self.id,
            "project_id": self.project_id,
            "source_path": self.source_path.as_posix(),
            "relative_path": self.relative_path,
            "checksum": self.checksum,
            "updated_at": self.updated_at,
        }
        if include_content:
            data["content"] = self.content
        return data


@dataclass(frozen=True)
class DocumentCollection:
    id: str
    project_id: str
    name: str
    description: str
    color: str
    created_at: str
    updated_at: str
    document_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "document_count": self.document_count,
        }


@dataclass(frozen=True)
class ImportBatch:
    id: str
    project_id: str
    source_type: str
    status: str
    started_at: str
    finished_at: str
    summary: dict[str, Any]
    message: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "source_type": self.source_type,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "summary": self.summary,
            "message": self.message,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ImportBatchItem:
    id: str
    batch_id: str
    project_id: str
    kind: str
    relative_path: str
    document_id: str
    reason: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "project_id": self.project_id,
            "kind": self.kind,
            "relative_path": self.relative_path,
            "document_id": self.document_id,
            "reason": self.reason,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    document: Document
    chunk_index: int
    content: str
    token_count: int
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "document_id": self.document.id,
            "project_id": self.document.project_id,
            "path": self.document.relative_path,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "token_count": self.token_count,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class SearchHit:
    document: Document
    score: float
    snippet: str
    chunk: DocumentChunk | None = None
    keyword_score: float = 0.0
    vector_score: float = 0.0
    retrieval: str = "keyword"
    vector_provider: str = "local"
    vector_model: str = "hashing-96"

    def to_dict(self) -> dict[str, Any]:
        data = {
            "path": self.document.relative_path,
            "score": self.score,
            "snippet": self.snippet,
            "document_id": self.document.id,
            "retrieval": self.retrieval,
            "keyword_score": self.keyword_score,
            "vector_score": self.vector_score,
            "vector_provider": self.vector_provider,
            "vector_model": self.vector_model,
        }
        if self.chunk is not None:
            data["chunk_id"] = self.chunk.id
            data["chunk_index"] = self.chunk.chunk_index
        return data


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    mode: str
    provider: str = "local"
    warning: str = ""
    tool_suggestion: dict[str, Any] | None = None


@dataclass(frozen=True)
class AssessmentQuestion:
    id: str
    project_id: str
    source_path: str
    question_type: str
    knowledge_point: str
    prompt: str
    expected_points: list[str]
    reference_snippet: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "source_path": self.source_path,
            "question_type": self.question_type,
            "knowledge_point": self.knowledge_point,
            "prompt": self.prompt,
            "expected_points": self.expected_points,
            "reference_snippet": self.reference_snippet,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class AssessmentAnswer:
    id: str
    project_id: str
    question_id: str
    answer: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "question_id": self.question_id,
            "answer": self.answer,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class AssessmentResult:
    id: str
    project_id: str
    question_id: str
    answer_id: str
    status: str
    score: float
    matched_points: list[str]
    missing_points: list[str]
    feedback: str
    source_path: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "question_id": self.question_id,
            "answer_id": self.answer_id,
            "status": self.status,
            "score": self.score,
            "matched_points": self.matched_points,
            "missing_points": self.missing_points,
            "feedback": self.feedback,
            "source_path": self.source_path,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ChatSession:
    id: str
    project_id: str
    title: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class PromptPreset:
    id: str
    project_id: str
    name: str
    description: str
    system_prompt: str
    answer_format: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "answer_format": self.answer_format,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class ModelProfile:
    id: str
    name: str
    provider: str
    api_base: str
    model: str
    temperature: float
    max_tokens: int
    api_key_ref: str
    is_default: bool
    created_at: str
    updated_at: str

    def to_dict(
        self,
        has_api_key: bool = False,
        api_key_source: str = "",
    ) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "api_base": self.api_base,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "api_key_ref": self.api_key_ref,
            "has_api_key": has_api_key,
            "api_key_source": api_key_source,
            "is_default": self.is_default,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class ChatMessage:
    id: str
    project_id: str
    question: str
    answer: str
    mode: str
    provider: str
    warning: str
    sources: list[dict[str, Any]]
    created_at: str
    session_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "question": self.question,
            "answer": self.answer,
            "mode": self.mode,
            "provider": self.provider,
            "warning": self.warning,
            "sources": self.sources,
            "created_at": self.created_at,
            "session_id": self.session_id,
        }


@dataclass(frozen=True)
class AnswerFeedback:
    id: str
    project_id: str
    message_id: str
    rating: str
    note: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "message_id": self.message_id,
            "rating": self.rating,
            "note": self.note,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class AgentToolRun:
    id: str
    project_id: str
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]
    status: str
    error: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result,
            "status": self.status,
            "error": self.error,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class RetrievalReview:
    id: str
    project_id: str
    query: str
    parameters: dict[str, Any]
    hits: list[dict[str, Any]]
    source_quality: dict[str, Any]
    note: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "query": self.query,
            "parameters": self.parameters,
            "hits": self.hits,
            "hit_count": len(self.hits),
            "source_quality": self.source_quality,
            "note": self.note,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ImportResult:
    imported: int
    skipped: int
    errors: list[str]
    skipped_details: list[dict[str, str]]
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    deleted: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "imported": self.imported,
            "skipped": self.skipped,
            "errors": self.errors,
            "skipped_details": self.skipped_details,
            "created": self.created,
            "updated": self.updated,
            "unchanged": self.unchanged,
            "deleted": self.deleted,
        }


@dataclass(frozen=True)
class ApiResponse:
    status: int
    body: dict[str, Any]


@dataclass(frozen=True)
class ApiStreamEvent:
    event: str
    data: dict[str, Any]
