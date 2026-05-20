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
        return {
            "id": self.id,
            "name": self.name,
            "root_path": str(self.root_path),
            "root_exists": self.root_path.exists() and self.root_path.is_dir(),
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
class SearchHit:
    document: Document
    score: float
    snippet: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.document.relative_path,
            "score": self.score,
            "snippet": self.snippet,
            "document_id": self.document.id,
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
