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
            "source_path": str(self.source_path),
            "relative_path": self.relative_path,
            "checksum": self.checksum,
            "updated_at": self.updated_at,
        }
        if include_content:
            data["content"] = self.content
        return data


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
