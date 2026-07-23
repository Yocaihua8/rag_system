from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from backend.domain.coach_models import (
    CoachAnalysisRun,
    CoachKnowledgePoint,
    CoachKnowledgeSkillMapping,
    CoachKnowledgeSource,
    CoachSkillNode,
)


class CoachStoreMixin:
    """SQLite persistence for the v2 project-knowledge coach domain."""

    def _connect(self) -> sqlite3.Connection:
        raise NotImplementedError

    @staticmethod
    def _init_coach_schema(conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS coach_analysis_runs (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                analyzer_version TEXT NOT NULL,
                source_fingerprint TEXT NOT NULL,
                status TEXT NOT NULL,
                summary_json TEXT NOT NULL DEFAULT '{}',
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_coach_analysis_runs_project
                ON coach_analysis_runs(project_id, started_at);

            CREATE TABLE IF NOT EXISTS coach_knowledge_points (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                stable_key TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                summary TEXT NOT NULL,
                current_run_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(project_id, stable_key),
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY(current_run_id) REFERENCES coach_analysis_runs(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_coach_knowledge_points_project
                ON coach_knowledge_points(project_id, updated_at);

            CREATE TABLE IF NOT EXISTS coach_knowledge_sources (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                knowledge_point_id TEXT NOT NULL,
                document_id TEXT,
                source_path TEXT NOT NULL,
                chunk_id TEXT,
                source_hash TEXT NOT NULL,
                excerpt TEXT NOT NULL,
                locator_json TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY(run_id) REFERENCES coach_analysis_runs(id) ON DELETE CASCADE,
                FOREIGN KEY(knowledge_point_id) REFERENCES coach_knowledge_points(id) ON DELETE CASCADE,
                FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE SET NULL,
                FOREIGN KEY(chunk_id) REFERENCES document_chunks(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_coach_knowledge_sources_run
                ON coach_knowledge_sources(run_id, knowledge_point_id);

            CREATE INDEX IF NOT EXISTS idx_coach_knowledge_sources_document
                ON coach_knowledge_sources(document_id, source_path);

            CREATE TABLE IF NOT EXISTS coach_skill_taxonomies (
                id TEXT PRIMARY KEY,
                version TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS coach_skill_nodes (
                id TEXT PRIMARY KEY,
                taxonomy_id TEXT NOT NULL,
                stable_key TEXT NOT NULL,
                parent_id TEXT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                sort_order INTEGER NOT NULL DEFAULT 0,
                UNIQUE(taxonomy_id, stable_key),
                FOREIGN KEY(taxonomy_id) REFERENCES coach_skill_taxonomies(id) ON DELETE CASCADE,
                FOREIGN KEY(parent_id) REFERENCES coach_skill_nodes(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_coach_skill_nodes_taxonomy
                ON coach_skill_nodes(taxonomy_id, sort_order, stable_key);

            CREATE TABLE IF NOT EXISTS coach_knowledge_skill_mappings (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                knowledge_point_id TEXT NOT NULL,
                skill_node_id TEXT NOT NULL,
                confidence REAL NOT NULL,
                source_id TEXT NOT NULL,
                rationale TEXT NOT NULL,
                UNIQUE(run_id, knowledge_point_id, skill_node_id),
                FOREIGN KEY(run_id) REFERENCES coach_analysis_runs(id) ON DELETE CASCADE,
                FOREIGN KEY(knowledge_point_id) REFERENCES coach_knowledge_points(id) ON DELETE CASCADE,
                FOREIGN KEY(skill_node_id) REFERENCES coach_skill_nodes(id) ON DELETE CASCADE,
                FOREIGN KEY(source_id) REFERENCES coach_knowledge_sources(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_coach_skill_mappings_run
                ON coach_knowledge_skill_mappings(run_id, knowledge_point_id);
            """
        )

    def create_coach_analysis_run(
        self,
        project_id: str,
        analyzer_version: str,
        source_fingerprint: str,
    ) -> CoachAnalysisRun:
        clean_project_id = project_id.strip()
        clean_version = analyzer_version.strip()
        clean_fingerprint = source_fingerprint.strip()
        if not clean_project_id or not clean_version or not clean_fingerprint:
            raise ValueError("project_id, analyzer_version and source_fingerprint are required")

        run = CoachAnalysisRun(
            id=str(uuid.uuid4()),
            project_id=clean_project_id,
            analyzer_version=clean_version,
            source_fingerprint=clean_fingerprint,
            status="running",
            summary={},
            started_at=_utc_now(),
            finished_at="",
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO coach_analysis_runs
                    (id, project_id, analyzer_version, source_fingerprint, status,
                     summary_json, started_at, finished_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.id,
                    run.project_id,
                    run.analyzer_version,
                    run.source_fingerprint,
                    run.status,
                    "{}",
                    run.started_at,
                    run.finished_at,
                ),
            )
        return run

    def save_coach_analysis_result(
        self,
        run_id: str,
        summary: Mapping[str, Any],
        knowledge_points: Iterable[Mapping[str, Any]],
        skill_taxonomy: Mapping[str, Any] | None = None,
        skill_nodes: Iterable[Mapping[str, Any]] = (),
        mappings: Iterable[Mapping[str, Any]] = (),
    ) -> CoachAnalysisRun:
        try:
            return self._save_coach_analysis_result(
                run_id,
                summary,
                knowledge_points,
                skill_taxonomy,
                skill_nodes,
                mappings,
            )
        except Exception as exc:
            self.mark_coach_analysis_failed(run_id, type(exc).__name__)
            raise

    def _save_coach_analysis_result(
        self,
        run_id: str,
        summary: Mapping[str, Any],
        knowledge_points: Iterable[Mapping[str, Any]],
        skill_taxonomy: Mapping[str, Any] | None = None,
        skill_nodes: Iterable[Mapping[str, Any]] = (),
        mappings: Iterable[Mapping[str, Any]] = (),
    ) -> CoachAnalysisRun:
        point_drafts = list(knowledge_points)
        node_drafts = list(skill_nodes)
        mapping_drafts = list(mappings)
        taxonomy_draft = dict(
            skill_taxonomy
            or {"version": "v1", "name": "通用开发技能树", "status": "active"}
        )
        now = _utc_now()

        with self._connect() as conn:
            run_row = conn.execute(
                """
                SELECT id, project_id, analyzer_version, source_fingerprint, status,
                       summary_json, started_at, finished_at
                FROM coach_analysis_runs
                WHERE id = ?
                """,
                (run_id,),
            ).fetchone()
            if not run_row:
                raise ValueError("coach analysis run not found")
            if run_row["status"] not in {"pending", "running", "failed"}:
                raise ValueError("coach analysis run is already finalized")

            project_id = str(run_row["project_id"])
            taxonomy_id, taxonomy_version = _upsert_taxonomy(conn, taxonomy_draft, now)
            skill_ids = _upsert_skill_nodes(conn, taxonomy_id, node_drafts)
            point_ids: dict[str, str] = {}
            source_ids: dict[str, list[tuple[str, str, str, str]]] = {}

            for point in point_drafts:
                stable_key = _required_text(point, "stable_key")
                if stable_key in point_ids:
                    raise ValueError(f"duplicate knowledge point stable_key: {stable_key}")
                point_id = _upsert_knowledge_point(
                    conn,
                    project_id=project_id,
                    run_id=run_id,
                    stable_key=stable_key,
                    title=_required_text(point, "title"),
                    category=_required_text(point, "category"),
                    summary=_required_text(point, "summary"),
                    now=now,
                )
                point_ids[stable_key] = point_id
                point_sources = list(_mapping_sequence(point.get("sources")))
                if not point_sources:
                    raise ValueError(f"knowledge point {stable_key!r} requires at least one source")
                source_ids[stable_key] = []
                for source in point_sources:
                    source_id, source_path, source_hash, locator_json = _insert_knowledge_source(
                        conn,
                        project_id=project_id,
                        run_id=run_id,
                        knowledge_point_id=point_id,
                        source=source,
                    )
                    source_ids[stable_key].append(
                        (source_id, source_path, source_hash, locator_json)
                    )
                mapping_drafts.extend(_mapping_sequence(point.get("skill_mappings")))

            for mapping in mapping_drafts:
                point_key = _text_alias(
                    mapping,
                    "knowledge_point_key",
                    "knowledge_point_stable_key",
                )
                skill_key = _text_alias(mapping, "skill_key", "skill_stable_key")
                if point_key not in point_ids:
                    raise ValueError(f"unknown knowledge point key: {point_key}")
                if skill_key not in skill_ids:
                    raise ValueError(
                        f"unknown skill key {skill_key!r} in taxonomy {taxonomy_version!r}"
                    )
                source_id = _resolve_mapping_source(mapping, source_ids[point_key])
                confidence = _confidence(mapping.get("confidence", 0.0))
                conn.execute(
                    """
                    INSERT INTO coach_knowledge_skill_mappings
                        (id, run_id, knowledge_point_id, skill_node_id, confidence,
                         source_id, rationale)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        run_id,
                        point_ids[point_key],
                        skill_ids[skill_key],
                        confidence,
                        source_id,
                        _required_text(mapping, "rationale"),
                    ),
                )

            conn.execute(
                """
                UPDATE coach_analysis_runs
                SET status = 'completed', summary_json = ?, finished_at = ?
                WHERE id = ?
                """,
                (json.dumps(dict(summary), ensure_ascii=False), now, run_id),
            )
            completed_row = conn.execute(
                """
                SELECT id, project_id, analyzer_version, source_fingerprint, status,
                       summary_json, started_at, finished_at
                FROM coach_analysis_runs
                WHERE id = ?
                """,
                (run_id,),
            ).fetchone()

        return _analysis_run_from_row(completed_row)

    def mark_coach_analysis_failed(
        self,
        run_id: str,
        error_type: str = "",
    ) -> CoachAnalysisRun | None:
        now = _utc_now()
        summary = {"error_type": error_type.strip()} if error_type.strip() else {}
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE coach_analysis_runs
                SET status = 'failed', summary_json = ?, finished_at = ?
                WHERE id = ? AND status IN ('pending', 'running')
                """,
                (json.dumps(summary, ensure_ascii=False), now, run_id),
            )
            row = conn.execute(
                """
                SELECT id, project_id, analyzer_version, source_fingerprint, status,
                       summary_json, started_at, finished_at
                FROM coach_analysis_runs
                WHERE id = ?
                """,
                (run_id,),
            ).fetchone()
        return _analysis_run_from_row(row) if row else None

    def get_latest_coach_analysis_run(self, project_id: str) -> CoachAnalysisRun | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, project_id, analyzer_version, source_fingerprint, status,
                       summary_json, started_at, finished_at
                FROM coach_analysis_runs
                WHERE project_id = ?
                ORDER BY started_at DESC, rowid DESC
                LIMIT 1
                """,
                (project_id,),
            ).fetchone()
        return _analysis_run_from_row(row) if row else None

    def get_current_coach_analysis_run(self, project_id: str) -> CoachAnalysisRun | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, project_id, analyzer_version, source_fingerprint, status,
                       summary_json, started_at, finished_at
                FROM coach_analysis_runs
                WHERE project_id = ? AND status IN ('completed', 'stale')
                ORDER BY started_at DESC, rowid DESC
                LIMIT 1
                """,
                (project_id,),
            ).fetchone()
        return _analysis_run_from_row(row) if row else None

    def list_coach_knowledge_points(
        self,
        project_id: str,
        include_sources: bool = True,
        run_id: str = "",
    ) -> list[CoachKnowledgePoint]:
        target_run_id = run_id.strip()
        if not target_run_id:
            latest = self.get_current_coach_analysis_run(project_id)
            if not latest:
                return []
            target_run_id = latest.id

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT
                       p.id, p.project_id, p.stable_key, p.title, p.category,
                       p.summary, p.current_run_id, p.created_at, p.updated_at
                FROM coach_knowledge_points p
                JOIN coach_knowledge_sources s ON s.knowledge_point_id = p.id
                WHERE p.project_id = ? AND s.run_id = ?
                ORDER BY p.category ASC, p.title ASC, p.stable_key ASC
                """,
                (project_id, target_run_id),
            ).fetchall()
            sources_by_point: dict[str, tuple[CoachKnowledgeSource, ...]] = {}
            if include_sources and rows:
                source_rows = conn.execute(
                    """
                    SELECT id, run_id, knowledge_point_id, document_id, source_path,
                           chunk_id, source_hash, excerpt, locator_json
                    FROM coach_knowledge_sources
                    WHERE run_id = ?
                    ORDER BY rowid ASC
                    """,
                    (target_run_id,),
                ).fetchall()
                grouped: dict[str, list[CoachKnowledgeSource]] = {}
                for source_row in source_rows:
                    source = _knowledge_source_from_row(source_row)
                    grouped.setdefault(source.knowledge_point_id, []).append(source)
                sources_by_point = {
                    point_id: tuple(point_sources)
                    for point_id, point_sources in grouped.items()
                }

        return [
            _knowledge_point_from_row(row, sources_by_point.get(str(row["id"]), ()))
            for row in rows
        ]

    def list_coach_skill_nodes(self, version: str = "v1") -> list[CoachSkillNode]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT n.id, n.taxonomy_id, n.stable_key, n.parent_id, n.name,
                       n.category, n.sort_order
                FROM coach_skill_nodes n
                JOIN coach_skill_taxonomies t ON t.id = n.taxonomy_id
                WHERE t.version = ?
                ORDER BY n.sort_order ASC, n.stable_key ASC
                """,
                (version,),
            ).fetchall()
        return [_skill_node_from_row(row) for row in rows]

    def list_coach_skill_mappings(
        self,
        project_id: str,
        run_id: str = "",
    ) -> list[CoachKnowledgeSkillMapping]:
        target_run_id = run_id.strip()
        if not target_run_id:
            latest = self.get_current_coach_analysis_run(project_id)
            if not latest:
                return []
            target_run_id = latest.id

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT m.id, m.run_id, m.knowledge_point_id,
                       p.stable_key AS knowledge_point_key,
                       m.skill_node_id, n.stable_key AS skill_key,
                       m.confidence, m.source_id, m.rationale
                FROM coach_knowledge_skill_mappings m
                JOIN coach_analysis_runs r ON r.id = m.run_id
                JOIN coach_knowledge_points p ON p.id = m.knowledge_point_id
                JOIN coach_skill_nodes n ON n.id = m.skill_node_id
                WHERE r.project_id = ? AND m.run_id = ?
                ORDER BY p.stable_key ASC, n.stable_key ASC
                """,
                (project_id, target_run_id),
            ).fetchall()
        return [_skill_mapping_from_row(row) for row in rows]

    def mark_coach_analysis_stale(
        self,
        project_id: str,
        document_id: str = "",
        source_path: str = "",
    ) -> int:
        filters = ["r.project_id = ?", "r.status = 'completed'"]
        values: list[object] = [project_id]
        clean_document_id = document_id.strip()
        clean_source_path = source_path.strip()
        if clean_document_id:
            filters.append("s.document_id = ?")
            values.append(clean_document_id)
        if clean_source_path:
            filters.append("s.source_path = ?")
            values.append(clean_source_path)

        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT DISTINCT r.id
                FROM coach_analysis_runs r
                JOIN coach_knowledge_sources s ON s.run_id = r.id
                WHERE {' AND '.join(filters)}
                """,
                values,
            ).fetchall()
            run_ids = [str(row["id"]) for row in rows]
            if run_ids:
                placeholders = ",".join("?" for _ in run_ids)
                conn.execute(
                    f"""
                    UPDATE coach_analysis_runs
                    SET status = 'stale'
                    WHERE id IN ({placeholders})
                    """,
                    run_ids,
                )
        return len(run_ids)


def _upsert_taxonomy(
    conn: sqlite3.Connection,
    draft: Mapping[str, Any],
    now: str,
) -> tuple[str, str]:
    version = _required_text(draft, "version")
    name = _required_text(draft, "name")
    status = str(draft.get("status") or "active").strip()
    row = conn.execute(
        "SELECT id FROM coach_skill_taxonomies WHERE version = ?",
        (version,),
    ).fetchone()
    taxonomy_id = str(row["id"]) if row else str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO coach_skill_taxonomies (id, version, name, status, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(version) DO UPDATE SET
            name = excluded.name,
            status = excluded.status
        """,
        (taxonomy_id, version, name, status, now),
    )
    return taxonomy_id, version


def _upsert_skill_nodes(
    conn: sqlite3.Connection,
    taxonomy_id: str,
    drafts: list[Mapping[str, Any]],
) -> dict[str, str]:
    node_ids: dict[str, str] = {}
    for draft in drafts:
        stable_key = _required_text(draft, "stable_key")
        if stable_key in node_ids:
            raise ValueError(f"duplicate skill stable_key: {stable_key}")
        row = conn.execute(
            """
            SELECT id
            FROM coach_skill_nodes
            WHERE taxonomy_id = ? AND stable_key = ?
            """,
            (taxonomy_id, stable_key),
        ).fetchone()
        node_id = str(row["id"]) if row else str(uuid.uuid4())
        node_ids[stable_key] = node_id
        conn.execute(
            """
            INSERT INTO coach_skill_nodes
                (id, taxonomy_id, stable_key, parent_id, name, category, sort_order)
            VALUES (?, ?, ?, NULL, ?, ?, ?)
            ON CONFLICT(taxonomy_id, stable_key) DO UPDATE SET
                parent_id = NULL,
                name = excluded.name,
                category = excluded.category,
                sort_order = excluded.sort_order
            """,
            (
                node_id,
                taxonomy_id,
                stable_key,
                _required_text(draft, "name"),
                _required_text(draft, "category"),
                _integer(draft.get("sort_order"), 0),
            ),
        )

    for draft in drafts:
        stable_key = _required_text(draft, "stable_key")
        parent_key = _text_alias(draft, "parent_key", "parent_stable_key", required=False)
        if parent_key and parent_key not in node_ids:
            row = conn.execute(
                """
                SELECT id
                FROM coach_skill_nodes
                WHERE taxonomy_id = ? AND stable_key = ?
                """,
                (taxonomy_id, parent_key),
            ).fetchone()
            if not row:
                raise ValueError(f"unknown parent skill key: {parent_key}")
            node_ids[parent_key] = str(row["id"])
        conn.execute(
            "UPDATE coach_skill_nodes SET parent_id = ? WHERE id = ?",
            (node_ids.get(parent_key) if parent_key else None, node_ids[stable_key]),
        )
    return node_ids


def _upsert_knowledge_point(
    conn: sqlite3.Connection,
    *,
    project_id: str,
    run_id: str,
    stable_key: str,
    title: str,
    category: str,
    summary: str,
    now: str,
) -> str:
    row = conn.execute(
        """
        SELECT id, created_at
        FROM coach_knowledge_points
        WHERE project_id = ? AND stable_key = ?
        """,
        (project_id, stable_key),
    ).fetchone()
    point_id = str(row["id"]) if row else str(uuid.uuid4())
    created_at = str(row["created_at"]) if row else now
    conn.execute(
        """
        INSERT INTO coach_knowledge_points
            (id, project_id, stable_key, title, category, summary, current_run_id,
             created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(project_id, stable_key) DO UPDATE SET
            title = excluded.title,
            category = excluded.category,
            summary = excluded.summary,
            current_run_id = excluded.current_run_id,
            updated_at = excluded.updated_at
        """,
        (
            point_id,
            project_id,
            stable_key,
            title,
            category,
            summary,
            run_id,
            created_at,
            now,
        ),
    )
    return point_id


def _insert_knowledge_source(
    conn: sqlite3.Connection,
    *,
    project_id: str,
    run_id: str,
    knowledge_point_id: str,
    source: Mapping[str, Any],
) -> tuple[str, str, str, str]:
    document_id = str(source.get("document_id") or "").strip()
    chunk_id = str(source.get("chunk_id") or "").strip()
    if not document_id and not chunk_id:
        raise ValueError("source must reference an imported document or chunk")
    document_row = None
    if document_id:
        document_row = conn.execute(
            """
            SELECT id, project_id, relative_path, checksum
            FROM documents
            WHERE id = ?
            """,
            (document_id,),
        ).fetchone()
        if not document_row or str(document_row["project_id"]) != project_id:
            raise ValueError("source document does not belong to the analysis project")
    if chunk_id:
        chunk_row = conn.execute(
            """
            SELECT c.id, c.document_id, c.project_id
            FROM document_chunks c
            WHERE c.id = ?
            """,
            (chunk_id,),
        ).fetchone()
        if not chunk_row or str(chunk_row["project_id"]) != project_id:
            raise ValueError("source chunk does not belong to the analysis project")
        if document_id and str(chunk_row["document_id"]) != document_id:
            raise ValueError("source chunk does not belong to source document")
        if not document_id:
            document_id = str(chunk_row["document_id"])
            document_row = conn.execute(
                """
                SELECT id, project_id, relative_path, checksum
                FROM documents
                WHERE id = ?
                """,
                (document_id,),
            ).fetchone()

    requested_path = str(source.get("source_path") or "").strip()
    requested_hash = str(source.get("source_hash") or source.get("checksum") or "").strip()
    if not document_row:
        raise ValueError("source document not found")
    source_path = str(document_row["relative_path"])
    source_hash = str(document_row["checksum"])
    if requested_path and requested_path != source_path:
        raise ValueError("source_path does not match the imported document")
    if requested_hash and requested_hash != source_hash:
        raise ValueError("source_hash does not match the imported document")
    if not source_path or not source_hash:
        raise ValueError("source_path and source_hash are required")
    excerpt = str(source.get("excerpt") or source.get("snippet") or "").strip()
    if not excerpt:
        raise ValueError("source excerpt is required")

    locator = source.get("locator")
    if not isinstance(locator, Mapping):
        locator = {}
    locator_json = json.dumps(dict(locator), ensure_ascii=False, sort_keys=True)
    source_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO coach_knowledge_sources
            (id, run_id, knowledge_point_id, document_id, source_path, chunk_id,
             source_hash, excerpt, locator_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_id,
            run_id,
            knowledge_point_id,
            document_id or None,
            source_path,
            chunk_id or None,
            source_hash,
            excerpt,
            locator_json,
        ),
    )
    return source_id, source_path, source_hash, locator_json


def _resolve_mapping_source(
    mapping: Mapping[str, Any],
    sources: list[tuple[str, str, str, str]],
) -> str:
    requested_id = str(mapping.get("source_id") or "").strip()
    if requested_id:
        if requested_id not in {source_id for source_id, _, _, _ in sources}:
            raise ValueError("mapping source_id does not belong to its knowledge point")
        return requested_id

    requested_path = str(mapping.get("source_path") or "").strip()
    requested_hash = str(
        mapping.get("source_hash") or mapping.get("source_checksum") or ""
    ).strip()
    requested_locator = mapping.get("source_locator")
    requested_locator_json = (
        json.dumps(dict(requested_locator), ensure_ascii=False, sort_keys=True)
        if isinstance(requested_locator, Mapping)
        else ""
    )
    matches = [
        source_id
        for source_id, source_path, source_hash, locator_json in sources
        if (not requested_path or source_path == requested_path)
        and (not requested_hash or source_hash == requested_hash)
        and (not requested_locator_json or locator_json == requested_locator_json)
    ]
    if len(matches) == 1:
        return matches[0]
    if not requested_path and not requested_hash and len(sources) == 1:
        return sources[0][0]
    raise ValueError("mapping must identify exactly one knowledge source")


def _analysis_run_from_row(row: sqlite3.Row) -> CoachAnalysisRun:
    return CoachAnalysisRun(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        analyzer_version=str(row["analyzer_version"]),
        source_fingerprint=str(row["source_fingerprint"]),
        status=str(row["status"]),
        summary=_json_object(row["summary_json"]),
        started_at=str(row["started_at"]),
        finished_at=str(row["finished_at"]),
    )


def _knowledge_source_from_row(row: sqlite3.Row) -> CoachKnowledgeSource:
    return CoachKnowledgeSource(
        id=str(row["id"]),
        run_id=str(row["run_id"]),
        knowledge_point_id=str(row["knowledge_point_id"]),
        document_id=str(row["document_id"] or ""),
        source_path=str(row["source_path"]),
        chunk_id=str(row["chunk_id"] or ""),
        source_hash=str(row["source_hash"]),
        excerpt=str(row["excerpt"]),
        locator=_json_object(row["locator_json"]),
    )


def _knowledge_point_from_row(
    row: sqlite3.Row,
    sources: tuple[CoachKnowledgeSource, ...],
) -> CoachKnowledgePoint:
    return CoachKnowledgePoint(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        stable_key=str(row["stable_key"]),
        title=str(row["title"]),
        category=str(row["category"]),
        summary=str(row["summary"]),
        current_run_id=str(row["current_run_id"] or ""),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        sources=sources,
    )


def _skill_node_from_row(row: sqlite3.Row) -> CoachSkillNode:
    return CoachSkillNode(
        id=str(row["id"]),
        taxonomy_id=str(row["taxonomy_id"]),
        stable_key=str(row["stable_key"]),
        parent_id=str(row["parent_id"] or ""),
        name=str(row["name"]),
        category=str(row["category"]),
        sort_order=int(row["sort_order"]),
    )


def _skill_mapping_from_row(row: sqlite3.Row) -> CoachKnowledgeSkillMapping:
    return CoachKnowledgeSkillMapping(
        id=str(row["id"]),
        run_id=str(row["run_id"]),
        knowledge_point_id=str(row["knowledge_point_id"]),
        knowledge_point_key=str(row["knowledge_point_key"]),
        skill_node_id=str(row["skill_node_id"]),
        skill_key=str(row["skill_key"]),
        confidence=float(row["confidence"]),
        source_id=str(row["source_id"]),
        rationale=str(row["rationale"]),
    )


def _mapping_sequence(value: object) -> list[Mapping[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        raise ValueError("expected a list of objects")
    result = list(value)
    if not all(isinstance(item, Mapping) for item in result):
        raise ValueError("expected a list of objects")
    return result


def _required_text(mapping: Mapping[str, Any], key: str) -> str:
    value = str(mapping.get(key) or "").strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _text_alias(
    mapping: Mapping[str, Any],
    *keys: str,
    required: bool = True,
) -> str:
    for key in keys:
        value = str(mapping.get(key) or "").strip()
        if value:
            return value
    if required:
        raise ValueError(f"{keys[0]} is required")
    return ""


def _confidence(value: object) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("confidence must be a number") from exc
    if parsed < 0.0 or parsed > 1.0:
        raise ValueError("confidence must be between 0 and 1")
    return parsed


def _integer(value: object, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _json_object(value: object) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = ["CoachStoreMixin"]
