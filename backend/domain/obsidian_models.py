from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ObsidianPairing:
    id: str
    project_id: str
    code_hash: str
    output_root: str
    expires_at: str
    consumed_at: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "output_root": self.output_root,
            "expires_at": self.expires_at,
            "consumed_at": self.consumed_at,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ObsidianConnection:
    id: str
    project_id: str
    vault_id: str
    vault_name: str
    output_root: str
    token_hash: str
    status: str
    sync_status: str
    last_synced_at: str
    created_at: str
    revoked_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "vault_id": self.vault_id,
            "vault_name": self.vault_name,
            "output_root": self.output_root,
            "status": self.status,
            "sync_status": self.sync_status,
            "last_synced_at": self.last_synced_at,
            "created_at": self.created_at,
            "revoked_at": self.revoked_at,
        }


@dataclass(frozen=True)
class ObsidianSyncEvent:
    id: str
    project_id: str
    connection_id: str
    event_id: str
    action: str
    path: str
    old_path: str
    content_hash: str
    payload: dict[str, Any]
    status: str
    result: dict[str, Any]
    received_at: str
    processed_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "connection_id": self.connection_id,
            "event_id": self.event_id,
            "action": self.action,
            "path": self.path,
            "old_path": self.old_path,
            "content_hash": self.content_hash,
            "payload": dict(self.payload),
            "status": self.status,
            "result": dict(self.result),
            "received_at": self.received_at,
            "processed_at": self.processed_at,
        }


@dataclass(frozen=True)
class ObsidianPublicationRevision:
    id: str
    project_id: str
    publication_id: str
    artifact_type: str
    stable_id: str
    target_path: str
    content: str
    content_hash: str
    expected_vault_hash: str
    status: str
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "revision_id": self.id,
            "project_id": self.project_id,
            "publication_id": self.publication_id,
            "artifact_type": self.artifact_type,
            "stable_id": self.stable_id,
            "target_path": self.target_path,
            "content": self.content,
            "content_hash": self.content_hash,
            "expected_vault_hash": self.expected_vault_hash,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class ObsidianPublication:
    id: str
    project_id: str
    connection_id: str
    revision: int
    status: str
    created_at: str
    updated_at: str
    confirmed_at: str
    completed_at: str
    artifacts: tuple[ObsidianPublicationRevision, ...] = field(
        default_factory=tuple
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "connection_id": self.connection_id,
            "revision": self.revision,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "confirmed_at": self.confirmed_at,
            "completed_at": self.completed_at,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
        }


@dataclass(frozen=True)
class ObsidianPublicationResult:
    id: str
    project_id: str
    publication_id: str
    revision_id: str
    connection_id: str
    status: str
    actual_hash: str
    error_code: str
    message: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "publication_id": self.publication_id,
            "revision_id": self.revision_id,
            "connection_id": self.connection_id,
            "status": self.status,
            "actual_hash": self.actual_hash,
            "error_code": self.error_code,
            "message": self.message,
            "created_at": self.created_at,
        }


__all__ = [
    "ObsidianConnection",
    "ObsidianPairing",
    "ObsidianPublication",
    "ObsidianPublicationResult",
    "ObsidianPublicationRevision",
    "ObsidianSyncEvent",
]
