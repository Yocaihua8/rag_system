from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from backend.domain.obsidian_models import (
    ObsidianConnection,
    ObsidianPairing,
    ObsidianPublication,
    ObsidianPublicationResult,
    ObsidianPublicationRevision,
    ObsidianSyncEvent,
)


CONNECTION_STATUSES = {"active", "revoked"}
CONNECTION_SYNC_STATUSES = {"idle", "syncing", "error"}
SYNC_ACTIONS = {"upsert", "rename", "delete"}
SYNC_EVENT_STATUSES = {"received", "applied", "ignored", "failed"}
PUBLICATION_STATUSES = {
    "draft",
    "confirmed",
    "queued",
    "applied",
    "conflict",
    "failed",
}
PUBLICATION_RESULT_STATUSES = {"applied", "conflict", "failed"}


class ObsidianStoreMixin:
    def _connect(self) -> sqlite3.Connection:
        raise NotImplementedError

    @staticmethod
    def _init_obsidian_schema(conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS obsidian_pairings (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                code_hash TEXT NOT NULL UNIQUE,
                output_root TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                consumed_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_obsidian_pairings_project
                ON obsidian_pairings(project_id, created_at);

            CREATE TABLE IF NOT EXISTS obsidian_connections (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                vault_id TEXT NOT NULL,
                vault_name TEXT NOT NULL,
                output_root TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL
                    CHECK(status IN ('active', 'revoked')),
                sync_status TEXT NOT NULL
                    CHECK(sync_status IN ('idle', 'syncing', 'error')),
                last_synced_at TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                revoked_at TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE UNIQUE INDEX IF NOT EXISTS uq_obsidian_active_project
                ON obsidian_connections(project_id)
                WHERE status = 'active';

            CREATE INDEX IF NOT EXISTS idx_obsidian_connections_project
                ON obsidian_connections(project_id, created_at);

            CREATE TABLE IF NOT EXISTS obsidian_sync_events (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                connection_id TEXT NOT NULL,
                event_id TEXT NOT NULL,
                action TEXT NOT NULL
                    CHECK(action IN ('upsert', 'rename', 'delete')),
                path TEXT NOT NULL,
                old_path TEXT NOT NULL DEFAULT '',
                content_hash TEXT NOT NULL DEFAULT '',
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK(status IN ('received', 'applied', 'ignored', 'failed')),
                result_json TEXT NOT NULL DEFAULT '{}',
                received_at TEXT NOT NULL,
                processed_at TEXT NOT NULL DEFAULT '',
                UNIQUE(connection_id, event_id),
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY(connection_id)
                    REFERENCES obsidian_connections(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_obsidian_sync_events_connection
                ON obsidian_sync_events(connection_id, received_at);

            CREATE TABLE IF NOT EXISTS obsidian_publications (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                connection_id TEXT NOT NULL,
                revision INTEGER NOT NULL CHECK(revision > 0),
                status TEXT NOT NULL
                    CHECK(status IN (
                        'draft', 'confirmed', 'queued',
                        'applied', 'conflict', 'failed'
                    )),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                confirmed_at TEXT NOT NULL DEFAULT '',
                completed_at TEXT NOT NULL DEFAULT '',
                UNIQUE(project_id, revision),
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY(connection_id)
                    REFERENCES obsidian_connections(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_obsidian_publications_connection
                ON obsidian_publications(connection_id, revision);

            CREATE TABLE IF NOT EXISTS obsidian_publication_revisions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                publication_id TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                stable_id TEXT NOT NULL,
                target_path TEXT NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                expected_vault_hash TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL
                    CHECK(status IN (
                        'draft', 'confirmed', 'queued',
                        'applied', 'conflict', 'failed'
                    )),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(publication_id, stable_id),
                UNIQUE(publication_id, target_path),
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY(publication_id)
                    REFERENCES obsidian_publications(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_obsidian_revisions_stable
                ON obsidian_publication_revisions(
                    project_id, stable_id, created_at
                );

            CREATE TABLE IF NOT EXISTS obsidian_publication_results (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                publication_id TEXT NOT NULL,
                revision_id TEXT NOT NULL UNIQUE,
                connection_id TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK(status IN ('applied', 'conflict', 'failed')),
                actual_hash TEXT NOT NULL DEFAULT '',
                error_code TEXT NOT NULL DEFAULT '',
                message TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY(publication_id)
                    REFERENCES obsidian_publications(id) ON DELETE CASCADE,
                FOREIGN KEY(revision_id)
                    REFERENCES obsidian_publication_revisions(id)
                    ON DELETE CASCADE,
                FOREIGN KEY(connection_id)
                    REFERENCES obsidian_connections(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_obsidian_publication_results
                ON obsidian_publication_results(
                    connection_id, publication_id, created_at
                );
            """
        )

    def create_obsidian_pairing(
        self,
        project_id: str,
        code_hash: str,
        output_root: str,
        expires_at: str,
    ) -> ObsidianPairing:
        pairing_id = str(uuid.uuid4())
        created_at = _utc_now()
        with self._connect() as conn:
            _require_project(conn, project_id)
            conn.execute(
                """
                INSERT INTO obsidian_pairings (
                    id, project_id, code_hash, output_root,
                    expires_at, consumed_at, created_at
                )
                VALUES (?, ?, ?, ?, ?, '', ?)
                """,
                (
                    pairing_id,
                    project_id,
                    code_hash,
                    output_root,
                    expires_at,
                    created_at,
                ),
            )
        pairing = self.get_obsidian_pairing(pairing_id)
        if pairing is None:
            raise RuntimeError("created Obsidian pairing was not found")
        return pairing

    def get_obsidian_pairing(
        self,
        pairing_id: str,
    ) -> ObsidianPairing | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM obsidian_pairings WHERE id = ?",
                (pairing_id,),
            ).fetchone()
        return _pairing_from_row(row) if row else None

    def get_obsidian_pairing_by_code_hash(
        self,
        code_hash: str,
    ) -> ObsidianPairing | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM obsidian_pairings WHERE code_hash = ?",
                (code_hash,),
            ).fetchone()
        return _pairing_from_row(row) if row else None

    def consume_obsidian_pairing_and_create_connection(
        self,
        pairing_id: str,
        *,
        token_hash: str,
        vault_id: str,
        vault_name: str,
        output_root: str,
    ) -> ObsidianConnection:
        connection_id = str(uuid.uuid4())
        created_at = _utc_now()
        with self._connect() as conn:
            pairing = conn.execute(
                "SELECT * FROM obsidian_pairings WHERE id = ?",
                (pairing_id,),
            ).fetchone()
            if pairing is None:
                raise ValueError("obsidian pairing not found")
            if pairing["consumed_at"]:
                raise ValueError("obsidian pairing already used")
            active = conn.execute(
                """
                SELECT id FROM obsidian_connections
                WHERE project_id = ? AND status = 'active'
                """,
                (pairing["project_id"],),
            ).fetchone()
            if active:
                raise ValueError("project already has an active Obsidian connection")
            consumed = conn.execute(
                """
                UPDATE obsidian_pairings
                SET consumed_at = ?
                WHERE id = ? AND consumed_at = ''
                """,
                (created_at, pairing_id),
            )
            if consumed.rowcount != 1:
                raise ValueError("obsidian pairing already used")
            try:
                conn.execute(
                    """
                    INSERT INTO obsidian_connections (
                        id, project_id, vault_id, vault_name, output_root,
                        token_hash, status, sync_status, last_synced_at,
                        created_at, revoked_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 'active', 'idle', '', ?, '')
                    """,
                    (
                        connection_id,
                        pairing["project_id"],
                        vault_id,
                        vault_name,
                        output_root,
                        token_hash,
                        created_at,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError(
                    "project already has an active Obsidian connection"
                ) from exc
        connection = self.get_obsidian_connection(connection_id)
        if connection is None:
            raise RuntimeError("created Obsidian connection was not found")
        return connection

    def get_obsidian_connection(
        self,
        connection_id: str,
    ) -> ObsidianConnection | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM obsidian_connections WHERE id = ?",
                (connection_id,),
            ).fetchone()
        return _connection_from_row(row) if row else None

    def get_active_obsidian_connection(
        self,
        project_id: str,
    ) -> ObsidianConnection | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM obsidian_connections
                WHERE project_id = ? AND status = 'active'
                LIMIT 1
                """,
                (project_id,),
            ).fetchone()
        return _connection_from_row(row) if row else None

    def get_obsidian_connection_by_token_hash(
        self,
        token_hash: str,
    ) -> ObsidianConnection | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM obsidian_connections
                WHERE token_hash = ? AND status = 'active'
                LIMIT 1
                """,
                (token_hash,),
            ).fetchone()
        return _connection_from_row(row) if row else None

    def list_obsidian_connections(
        self,
        project_id: str,
    ) -> list[ObsidianConnection]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM obsidian_connections
                WHERE project_id = ?
                ORDER BY created_at DESC
                """,
                (project_id,),
            ).fetchall()
        return [_connection_from_row(row) for row in rows]

    def revoke_obsidian_connection(
        self,
        project_id: str,
        connection_id: str,
    ) -> ObsidianConnection | None:
        revoked_at = _utc_now()
        with self._connect() as conn:
            result = conn.execute(
                """
                UPDATE obsidian_connections
                SET status = 'revoked', sync_status = 'idle', revoked_at = ?
                WHERE id = ? AND project_id = ? AND status = 'active'
                """,
                (revoked_at, connection_id, project_id),
            )
        if result.rowcount != 1:
            return None
        return self.get_obsidian_connection(connection_id)

    def update_obsidian_connection_sync(
        self,
        connection_id: str,
        sync_status: str,
        *,
        mark_synced: bool = False,
    ) -> ObsidianConnection | None:
        if sync_status not in CONNECTION_SYNC_STATUSES:
            raise ValueError("invalid Obsidian sync status")
        synced_at = _utc_now() if mark_synced else None
        with self._connect() as conn:
            if synced_at is None:
                result = conn.execute(
                    """
                    UPDATE obsidian_connections SET sync_status = ?
                    WHERE id = ? AND status = 'active'
                    """,
                    (sync_status, connection_id),
                )
            else:
                result = conn.execute(
                    """
                    UPDATE obsidian_connections
                    SET sync_status = ?, last_synced_at = ?
                    WHERE id = ? AND status = 'active'
                    """,
                    (sync_status, synced_at, connection_id),
                )
        if result.rowcount != 1:
            return None
        return self.get_obsidian_connection(connection_id)

    def create_obsidian_sync_event(
        self,
        project_id: str,
        connection_id: str,
        event_id: str,
        action: str,
        path: str,
        *,
        old_path: str = "",
        content_hash: str = "",
        payload: Mapping[str, Any] | None = None,
    ) -> tuple[ObsidianSyncEvent, bool]:
        if action not in SYNC_ACTIONS:
            raise ValueError("invalid Obsidian sync action")
        record_id = str(uuid.uuid4())
        received_at = _utc_now()
        created = True
        with self._connect() as conn:
            _require_active_connection(conn, project_id, connection_id)
            try:
                conn.execute(
                    """
                    INSERT INTO obsidian_sync_events (
                        id, project_id, connection_id, event_id, action,
                        path, old_path, content_hash, payload_json, status,
                        result_json, received_at, processed_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'received', '{}', ?, '')
                    """,
                    (
                        record_id,
                        project_id,
                        connection_id,
                        event_id,
                        action,
                        path,
                        old_path,
                        content_hash,
                        _json_dump(dict(payload or {})),
                        received_at,
                    ),
                )
            except sqlite3.IntegrityError:
                created = False
            row = conn.execute(
                """
                SELECT * FROM obsidian_sync_events
                WHERE connection_id = ? AND event_id = ?
                """,
                (connection_id, event_id),
            ).fetchone()
        if row is None:
            raise RuntimeError("Obsidian sync event was not persisted")
        return _sync_event_from_row(row), created

    def complete_obsidian_sync_event(
        self,
        connection_id: str,
        event_id: str,
        status: str,
        result: Mapping[str, Any],
    ) -> ObsidianSyncEvent:
        if status not in {"applied", "ignored", "failed"}:
            raise ValueError("invalid Obsidian sync event result")
        processed_at = _utc_now()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE obsidian_sync_events
                SET status = ?, result_json = ?, processed_at = ?
                WHERE connection_id = ? AND event_id = ? AND status = 'received'
                """,
                (
                    status,
                    _json_dump(dict(result)),
                    processed_at,
                    connection_id,
                    event_id,
                ),
            )
            row = conn.execute(
                """
                SELECT * FROM obsidian_sync_events
                WHERE connection_id = ? AND event_id = ?
                """,
                (connection_id, event_id),
            ).fetchone()
        if row is None:
            raise ValueError("Obsidian sync event not found")
        return _sync_event_from_row(row)

    def get_obsidian_sync_event(
        self,
        connection_id: str,
        event_id: str,
    ) -> ObsidianSyncEvent | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM obsidian_sync_events
                WHERE connection_id = ? AND event_id = ?
                """,
                (connection_id, event_id),
            ).fetchone()
        return _sync_event_from_row(row) if row else None

    def create_obsidian_publication(
        self,
        project_id: str,
        connection_id: str,
        artifacts: Iterable[Mapping[str, Any]],
    ) -> ObsidianPublication:
        artifact_list = [dict(item) for item in artifacts]
        if not artifact_list:
            raise ValueError("at least one publication artifact is required")
        publication_id = str(uuid.uuid4())
        created_at = _utc_now()
        with self._connect() as conn:
            _require_active_connection(conn, project_id, connection_id)
            row = conn.execute(
                """
                SELECT COALESCE(MAX(revision), 0) + 1 AS next_revision
                FROM obsidian_publications
                WHERE project_id = ?
                """,
                (project_id,),
            ).fetchone()
            revision = int(row["next_revision"])
            conn.execute(
                """
                INSERT INTO obsidian_publications (
                    id, project_id, connection_id, revision, status,
                    created_at, updated_at, confirmed_at, completed_at
                )
                VALUES (?, ?, ?, ?, 'draft', ?, ?, '', '')
                """,
                (
                    publication_id,
                    project_id,
                    connection_id,
                    revision,
                    created_at,
                    created_at,
                ),
            )
            seen_stable: set[str] = set()
            seen_paths: set[str] = set()
            for artifact in artifact_list:
                stable_id = _required_text(artifact.get("stable_id"), "stable_id")
                target_path = _required_text(
                    artifact.get("target_path"),
                    "target_path",
                )
                if stable_id in seen_stable or target_path in seen_paths:
                    raise ValueError(
                        "publication stable IDs and target paths must be unique"
                    )
                seen_stable.add(stable_id)
                seen_paths.add(target_path)
                conn.execute(
                    """
                    INSERT INTO obsidian_publication_revisions (
                        id, project_id, publication_id, artifact_type,
                        stable_id, target_path, content, content_hash,
                        expected_vault_hash, status, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        project_id,
                        publication_id,
                        _required_text(
                            artifact.get("artifact_type"),
                            "artifact_type",
                        ),
                        stable_id,
                        target_path,
                        str(artifact.get("content") or ""),
                        _required_text(
                            artifact.get("content_hash"),
                            "content_hash",
                        ),
                        str(artifact.get("expected_vault_hash") or ""),
                        created_at,
                        created_at,
                    ),
                )
        publication = self.get_obsidian_publication(
            project_id,
            publication_id,
        )
        if publication is None:
            raise RuntimeError("created Obsidian publication was not found")
        return publication

    def get_obsidian_publication(
        self,
        project_id: str,
        publication_id: str,
    ) -> ObsidianPublication | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM obsidian_publications
                WHERE id = ? AND project_id = ?
                """,
                (publication_id, project_id),
            ).fetchone()
            if row is None:
                return None
            artifacts = _publication_artifacts(conn, publication_id)
        return _publication_from_row(row, artifacts)

    def list_obsidian_publications(
        self,
        project_id: str,
        *,
        limit: int = 100,
    ) -> list[ObsidianPublication]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM obsidian_publications
                WHERE project_id = ?
                ORDER BY revision DESC
                LIMIT ?
                """,
                (project_id, max(1, min(int(limit), 500))),
            ).fetchall()
            return [
                _publication_from_row(
                    row,
                    _publication_artifacts(conn, row["id"]),
                )
                for row in rows
            ]

    def confirm_obsidian_publication(
        self,
        project_id: str,
        publication_id: str,
    ) -> ObsidianPublication | None:
        confirmed_at = _utc_now()
        with self._connect() as conn:
            result = conn.execute(
                """
                UPDATE obsidian_publications
                SET status = 'queued', confirmed_at = ?, updated_at = ?
                WHERE id = ? AND project_id = ? AND status = 'draft'
                """,
                (
                    confirmed_at,
                    confirmed_at,
                    publication_id,
                    project_id,
                ),
            )
            if result.rowcount == 1:
                conn.execute(
                    """
                    UPDATE obsidian_publication_revisions
                    SET status = 'queued', updated_at = ?
                    WHERE publication_id = ? AND status = 'draft'
                    """,
                    (confirmed_at, publication_id),
                )
        if result.rowcount != 1:
            return None
        return self.get_obsidian_publication(project_id, publication_id)

    def list_pending_obsidian_publications(
        self,
        connection_id: str,
    ) -> list[ObsidianPublication]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM obsidian_publications
                WHERE connection_id = ? AND status = 'queued'
                ORDER BY revision ASC
                """,
                (connection_id,),
            ).fetchall()
            return [
                _publication_from_row(
                    row,
                    _publication_artifacts(conn, row["id"]),
                )
                for row in rows
            ]

    def record_obsidian_publication_results(
        self,
        project_id: str,
        connection_id: str,
        publication_id: str,
        results: Iterable[Mapping[str, Any]],
    ) -> tuple[ObsidianPublication, list[ObsidianPublicationResult]]:
        result_list = [dict(item) for item in results]
        if not result_list:
            raise ValueError("publication results are required")
        now = _utc_now()
        stored_results: list[ObsidianPublicationResult] = []
        with self._connect() as conn:
            publication = conn.execute(
                """
                SELECT * FROM obsidian_publications
                WHERE id = ? AND project_id = ? AND connection_id = ?
                """,
                (publication_id, project_id, connection_id),
            ).fetchone()
            if publication is None:
                raise ValueError("Obsidian publication not found")
            if publication["status"] not in {
                "queued",
                "applied",
                "conflict",
                "failed",
            }:
                raise ValueError("Obsidian publication is not queued")
            for item in result_list:
                revision_id = _required_text(
                    item.get("revision_id"),
                    "revision_id",
                )
                status = _required_text(item.get("status"), "status")
                if status not in PUBLICATION_RESULT_STATUSES:
                    raise ValueError("invalid publication result status")
                artifact = conn.execute(
                    """
                    SELECT id FROM obsidian_publication_revisions
                    WHERE id = ? AND publication_id = ? AND project_id = ?
                    """,
                    (revision_id, publication_id, project_id),
                ).fetchone()
                if artifact is None:
                    raise ValueError(
                        "publication revision does not belong to publication"
                    )
                existing = conn.execute(
                    """
                    SELECT * FROM obsidian_publication_results
                    WHERE revision_id = ?
                    """,
                    (revision_id,),
                ).fetchone()
                actual_hash = str(item.get("actual_hash") or "")
                error_code = str(item.get("error_code") or "")
                message = str(item.get("message") or "")
                if existing:
                    if (
                        existing["status"] != status
                        or existing["actual_hash"] != actual_hash
                        or existing["error_code"] != error_code
                        or existing["message"] != message
                    ):
                        raise ValueError("publication result already recorded")
                    stored_results.append(_publication_result_from_row(existing))
                    continue
                result_id = str(uuid.uuid4())
                conn.execute(
                    """
                    INSERT INTO obsidian_publication_results (
                        id, project_id, publication_id, revision_id,
                        connection_id, status, actual_hash, error_code,
                        message, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        result_id,
                        project_id,
                        publication_id,
                        revision_id,
                        connection_id,
                        status,
                        actual_hash,
                        error_code,
                        message,
                        now,
                    ),
                )
                conn.execute(
                    """
                    UPDATE obsidian_publication_revisions
                    SET status = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (status, now, revision_id),
                )
                stored = conn.execute(
                    """
                    SELECT * FROM obsidian_publication_results WHERE id = ?
                    """,
                    (result_id,),
                ).fetchone()
                stored_results.append(_publication_result_from_row(stored))
            statuses = [
                row["status"]
                for row in conn.execute(
                    """
                    SELECT status FROM obsidian_publication_revisions
                    WHERE publication_id = ?
                    """,
                    (publication_id,),
                ).fetchall()
            ]
            final_status = _publication_status(statuses)
            completed_at = now if final_status in {
                "applied",
                "conflict",
                "failed",
            } else ""
            conn.execute(
                """
                UPDATE obsidian_publications
                SET status = ?, updated_at = ?, completed_at = ?
                WHERE id = ?
                """,
                (final_status, now, completed_at, publication_id),
            )
        updated = self.get_obsidian_publication(project_id, publication_id)
        if updated is None:
            raise RuntimeError("updated Obsidian publication was not found")
        return updated, stored_results

    def latest_obsidian_artifact_baseline(
        self,
        project_id: str,
        connection_id: str,
        stable_id: str,
    ) -> dict[str, str] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    r.actual_hash,
                    r.status,
                    r.error_code,
                    r.message,
                    pr.target_path,
                    p.revision
                FROM obsidian_publication_revisions pr
                JOIN obsidian_publications p
                  ON p.id = pr.publication_id
                JOIN obsidian_publication_results r
                  ON r.revision_id = pr.id
                WHERE pr.project_id = ?
                  AND p.connection_id = ?
                  AND pr.stable_id = ?
                ORDER BY p.revision DESC
                LIMIT 1
                """,
                (project_id, connection_id, stable_id),
            ).fetchone()
        if row is None:
            return None
        return {
            "actual_hash": str(row["actual_hash"]),
            "status": str(row["status"]),
            "error_code": str(row["error_code"]),
            "message": str(row["message"]),
            "target_path": str(row["target_path"]),
            "revision": str(row["revision"]),
        }


def _publication_status(statuses: list[str]) -> str:
    if not statuses or any(status in {"draft", "confirmed", "queued"} for status in statuses):
        return "queued"
    if all(status == "applied" for status in statuses):
        return "applied"
    if any(status == "conflict" for status in statuses):
        return "conflict"
    return "failed"


def _publication_artifacts(
    conn: sqlite3.Connection,
    publication_id: str,
) -> tuple[ObsidianPublicationRevision, ...]:
    rows = conn.execute(
        """
        SELECT * FROM obsidian_publication_revisions
        WHERE publication_id = ?
        ORDER BY target_path ASC
        """,
        (publication_id,),
    ).fetchall()
    return tuple(_publication_revision_from_row(row) for row in rows)


def _pairing_from_row(row: sqlite3.Row) -> ObsidianPairing:
    return ObsidianPairing(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        code_hash=str(row["code_hash"]),
        output_root=str(row["output_root"]),
        expires_at=str(row["expires_at"]),
        consumed_at=str(row["consumed_at"]),
        created_at=str(row["created_at"]),
    )


def _connection_from_row(row: sqlite3.Row) -> ObsidianConnection:
    return ObsidianConnection(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        vault_id=str(row["vault_id"]),
        vault_name=str(row["vault_name"]),
        output_root=str(row["output_root"]),
        token_hash=str(row["token_hash"]),
        status=str(row["status"]),
        sync_status=str(row["sync_status"]),
        last_synced_at=str(row["last_synced_at"]),
        created_at=str(row["created_at"]),
        revoked_at=str(row["revoked_at"]),
    )


def _sync_event_from_row(row: sqlite3.Row) -> ObsidianSyncEvent:
    return ObsidianSyncEvent(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        connection_id=str(row["connection_id"]),
        event_id=str(row["event_id"]),
        action=str(row["action"]),
        path=str(row["path"]),
        old_path=str(row["old_path"]),
        content_hash=str(row["content_hash"]),
        payload=_json_object(row["payload_json"]),
        status=str(row["status"]),
        result=_json_object(row["result_json"]),
        received_at=str(row["received_at"]),
        processed_at=str(row["processed_at"]),
    )


def _publication_from_row(
    row: sqlite3.Row,
    artifacts: tuple[ObsidianPublicationRevision, ...],
) -> ObsidianPublication:
    return ObsidianPublication(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        connection_id=str(row["connection_id"]),
        revision=int(row["revision"]),
        status=str(row["status"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        confirmed_at=str(row["confirmed_at"]),
        completed_at=str(row["completed_at"]),
        artifacts=artifacts,
    )


def _publication_revision_from_row(
    row: sqlite3.Row,
) -> ObsidianPublicationRevision:
    return ObsidianPublicationRevision(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        publication_id=str(row["publication_id"]),
        artifact_type=str(row["artifact_type"]),
        stable_id=str(row["stable_id"]),
        target_path=str(row["target_path"]),
        content=str(row["content"]),
        content_hash=str(row["content_hash"]),
        expected_vault_hash=str(row["expected_vault_hash"]),
        status=str(row["status"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _publication_result_from_row(
    row: sqlite3.Row,
) -> ObsidianPublicationResult:
    return ObsidianPublicationResult(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        publication_id=str(row["publication_id"]),
        revision_id=str(row["revision_id"]),
        connection_id=str(row["connection_id"]),
        status=str(row["status"]),
        actual_hash=str(row["actual_hash"]),
        error_code=str(row["error_code"]),
        message=str(row["message"]),
        created_at=str(row["created_at"]),
    )


def _require_project(conn: sqlite3.Connection, project_id: str) -> None:
    if not conn.execute(
        "SELECT 1 FROM projects WHERE id = ?",
        (project_id,),
    ).fetchone():
        raise ValueError("project not found")


def _require_active_connection(
    conn: sqlite3.Connection,
    project_id: str,
    connection_id: str,
) -> None:
    row = conn.execute(
        """
        SELECT 1 FROM obsidian_connections
        WHERE id = ? AND project_id = ? AND status = 'active'
        """,
        (connection_id, project_id),
    ).fetchone()
    if row is None:
        raise ValueError("active Obsidian connection not found")


def _required_text(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} is required")
    return text


def _json_dump(value: Mapping[str, Any]) -> str:
    return json.dumps(
        dict(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _json_object(value: object) -> dict[str, Any]:
    try:
        payload = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "ObsidianStoreMixin",
    "PUBLICATION_RESULT_STATUSES",
    "PUBLICATION_STATUSES",
    "SYNC_ACTIONS",
]
