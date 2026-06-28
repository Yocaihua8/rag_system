from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.config.vector_store import get_default_vector_store
from backend.providers.base import BaseVectorStore, VectorUpsertRecord
from webapp.chunking import count_tokens, split_into_chunks
from webapp.embeddings import EmbeddingClient, embed_with_fallback, get_default_embedding_client
from webapp.models import (
    AgentToolRun,
    AnswerFeedback,
    AssessmentAnswer,
    AssessmentQuestion,
    AssessmentResult,
    ChatMessage,
    ChatSession,
    Document,
    DocumentChunk,
    DocumentCollection,
    ImportBatch,
    ImportBatchItem,
    ModelProfile,
    PromptPreset,
    Project,
    RetrievalReview,
)
from webapp.vector_index import deserialize_vector, serialize_vector

DEFAULT_RETRIEVAL_SETTINGS = {
    "top_k": 5,
    "min_score": 0.0,
    "use_keyword": True,
    "use_vector": True,
}


class DocumentWriteResult:
    def __init__(self, document: Document, action: str):
        self.document = document
        self.action = action


_DEFAULT_VECTOR_STORE = object()


class KnowledgeStore:
    def __init__(
        self,
        db_path: Path,
        embedding_client: EmbeddingClient | None = None,
        vector_store: BaseVectorStore | None | object = _DEFAULT_VECTOR_STORE,
    ):
        self.db_path = Path(db_path)
        self._embedding_client = embedding_client or get_default_embedding_client()
        self._vector_store = (
            get_default_vector_store() if vector_store is _DEFAULT_VECTOR_STORE else vector_store
        )
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def create_project(self, name: str, root_path: Path) -> Project:
        project = Project(
            id=str(uuid.uuid4()),
            name=name.strip() or Path(root_path).name,
            root_path=Path(root_path),
            created_at=_now(),
        )
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, root_path, created_at) VALUES (?, ?, ?, ?)",
                (project.id, project.name, str(project.root_path), project.created_at),
            )
        return project

    def restore_document_metadata(
        self,
        project_id: str,
        source_path: str,
        relative_path: str,
        checksum: str,
        updated_at: str,
    ) -> Document:
        document = Document(
            id=str(uuid.uuid4()),
            project_id=project_id,
            source_path=Path(source_path),
            relative_path=relative_path,
            content="",
            checksum=checksum,
            updated_at=updated_at or _now(),
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO documents
                    (id, project_id, source_path, relative_path, content, checksum, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.project_id,
                    str(document.source_path),
                    document.relative_path,
                    document.content,
                    document.checksum,
                    document.updated_at,
                ),
            )
        return document

    def restore_document_snapshot(
        self,
        project_id: str,
        source_path: str,
        relative_path: str,
        content: str,
        checksum: str,
        updated_at: str,
        chunks: list[dict[str, object]] | None = None,
    ) -> tuple[Document, dict[str, str], int, int]:
        document_content = str(content)
        document_checksum = str(checksum).strip()
        if not document_checksum and document_content:
            document_checksum = hashlib.sha256(document_content.encode("utf-8")).hexdigest()
        document = Document(
            id=str(uuid.uuid4()),
            project_id=project_id,
            source_path=Path(source_path),
            relative_path=relative_path,
            content=document_content,
            checksum=document_checksum,
            updated_at=updated_at or _now(),
        )
        chunk_id_map: dict[str, str] = {}
        now = _now()
        chunk_rows = []
        vector_rows = []
        vector_records: list[VectorUpsertRecord] = []
        for fallback_index, item in enumerate(chunks or []):
            if not isinstance(item, dict):
                continue
            chunk_content = str(item.get("content", ""))
            if not chunk_content:
                continue
            chunk_id = str(uuid.uuid4())
            original_chunk_id = str(item.get("id", "")).strip()
            if original_chunk_id:
                chunk_id_map[original_chunk_id] = chunk_id
            chunk_rows.append(
                (
                    chunk_id,
                    document.id,
                    document.project_id,
                    _int_snapshot_value(item.get("chunk_index"), fallback_index),
                    chunk_content,
                    _int_snapshot_value(item.get("token_count"), count_tokens(chunk_content)),
                    str(item.get("created_at", "")).strip() or now,
                )
            )
            vector_body = item.get("vector")
            if isinstance(vector_body, dict):
                vector = _snapshot_vector(vector_body.get("values"))
                if vector:
                    provider = str(vector_body.get("provider", "")).strip() or "local"
                    model = str(vector_body.get("model", "")).strip() or "hashing-96"
                    vector_rows.append(
                        (
                            chunk_id,
                            document.project_id,
                            serialize_vector(vector),
                            provider,
                            model,
                            str(vector_body.get("updated_at", "")).strip() or now,
                        )
                    )
                    vector_records.append(
                        VectorUpsertRecord(
                            project_id=document.project_id,
                            document_id=document.id,
                            chunk_id=chunk_id,
                            chunk_index=_int_snapshot_value(item.get("chunk_index"), fallback_index),
                            path=document.relative_path,
                            content=chunk_content,
                            vector=vector,
                            provider=provider,
                            model=model,
                        )
                    )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO documents
                    (id, project_id, source_path, relative_path, content, checksum, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.id,
                    document.project_id,
                    str(document.source_path),
                    document.relative_path,
                    document.content,
                    document.checksum,
                    document.updated_at,
                ),
            )
            if chunk_rows:
                conn.executemany(
                    """
                    INSERT INTO document_chunks
                        (id, document_id, project_id, chunk_index, content, token_count, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    chunk_rows,
                )
                conn.executemany(
                    """
                    INSERT INTO chunk_vectors
                        (chunk_id, project_id, vector_json, provider, model, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    vector_rows,
                )
                self._sync_vector_upsert(vector_records)
            elif document.content:
                self._replace_document_chunks(conn, document)
                rows = conn.execute(
                    """
                    SELECT id
                    FROM document_chunks
                    WHERE document_id = ?
                    ORDER BY chunk_index ASC
                    """,
                    (document.id,),
                ).fetchall()
                chunk_rows = [(row["id"],) for row in rows]
                vector_count = conn.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM chunk_vectors
                    WHERE project_id = ?
                      AND chunk_id IN (
                          SELECT id FROM document_chunks WHERE document_id = ?
                      )
                    """,
                    (document.project_id, document.id),
                ).fetchone()
                return document, chunk_id_map, len(chunk_rows), int(vector_count["total"])
        return document, chunk_id_map, len(chunk_rows), len(vector_rows)

    def list_projects(self) -> list[Project]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, root_path, created_at FROM projects ORDER BY created_at DESC"
            ).fetchall()
        return [_project_from_row(row) for row in rows]

    def get_project(self, project_id: str) -> Project | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, name, root_path, created_at FROM projects WHERE id = ?",
                (project_id,),
            ).fetchone()
        return _project_from_row(row) if row else None

    def get_project_summary(self, project_id: str) -> dict[str, object] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    p.id AS project_id,
                    p.name AS project_name,
                    (SELECT COUNT(*) FROM documents d WHERE d.project_id = p.id) AS document_count,
                    (SELECT COUNT(*) FROM document_chunks c WHERE c.project_id = p.id) AS chunk_count,
                    (SELECT COUNT(*) FROM chunk_vectors v WHERE v.project_id = p.id) AS vector_count,
                    (SELECT COUNT(*) FROM chat_messages m WHERE m.project_id = p.id) AS chat_message_count,
                    (SELECT COUNT(*) FROM agent_tool_runs r WHERE r.project_id = p.id) AS agent_tool_run_count,
                    (SELECT COUNT(*) FROM retrieval_reviews rr WHERE rr.project_id = p.id) AS retrieval_review_count,
                    MAX(
                        p.created_at,
                        COALESCE((SELECT MAX(d.updated_at) FROM documents d WHERE d.project_id = p.id), p.created_at),
                        COALESCE((SELECT MAX(v.updated_at) FROM chunk_vectors v WHERE v.project_id = p.id), p.created_at),
                        COALESCE((SELECT MAX(m.created_at) FROM chat_messages m WHERE m.project_id = p.id), p.created_at),
                        COALESCE((SELECT MAX(r.created_at) FROM agent_tool_runs r WHERE r.project_id = p.id), p.created_at),
                        COALESCE((SELECT MAX(rr.created_at) FROM retrieval_reviews rr WHERE rr.project_id = p.id), p.created_at)
                    ) AS last_activity_at
                FROM projects p
                WHERE p.id = ?
                """,
                (project_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "project_id": row["project_id"],
            "project_name": row["project_name"],
            "document_count": int(row["document_count"]),
            "chunk_count": int(row["chunk_count"]),
            "vector_count": int(row["vector_count"]),
            "chat_message_count": int(row["chat_message_count"]),
            "agent_tool_run_count": int(row["agent_tool_run_count"]),
            "retrieval_review_count": int(row["retrieval_review_count"]),
            "last_activity_at": row["last_activity_at"],
        }

    def get_project_retrieval_settings(self, project_id: str) -> dict[str, object] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    id AS project_id,
                    retrieval_top_k,
                    retrieval_min_score,
                    retrieval_use_keyword,
                    retrieval_use_vector
                FROM projects
                WHERE id = ?
                """,
                (project_id,),
            ).fetchone()
        return _retrieval_settings_from_row(row) if row else None

    def update_project_retrieval_settings(
        self,
        project_id: str,
        top_k: int,
        min_score: float,
        use_keyword: bool,
        use_vector: bool,
    ) -> dict[str, object] | None:
        with self._connect() as conn:
            result = conn.execute(
                """
                UPDATE projects
                SET retrieval_top_k = ?,
                    retrieval_min_score = ?,
                    retrieval_use_keyword = ?,
                    retrieval_use_vector = ?
                WHERE id = ?
                """,
                (
                    top_k,
                    min_score,
                    1 if use_keyword else 0,
                    1 if use_vector else 0,
                    project_id,
                ),
            )
        if result.rowcount == 0:
            return None
        return self.get_project_retrieval_settings(project_id)

    def get_default_prompt_preset_id(self, project_id: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT default_prompt_preset_id FROM projects WHERE id = ?",
                (project_id,),
            ).fetchone()
        if not row:
            return None
        return row["default_prompt_preset_id"] or ""

    def set_default_prompt_preset(self, project_id: str, preset_id: str = "") -> str | None:
        clean_preset_id = preset_id.strip()
        with self._connect() as conn:
            result = conn.execute(
                "UPDATE projects SET default_prompt_preset_id = ? WHERE id = ?",
                (clean_preset_id or None, project_id),
            )
        if result.rowcount == 0:
            return None
        return clean_preset_id

    def create_prompt_preset(
        self,
        project_id: str,
        name: str,
        description: str,
        system_prompt: str,
        answer_format: str,
    ) -> PromptPreset:
        now = _now()
        preset = PromptPreset(
            id=str(uuid.uuid4()),
            project_id=project_id,
            name=name.strip(),
            description=description.strip(),
            system_prompt=system_prompt.strip(),
            answer_format=answer_format.strip(),
            created_at=now,
            updated_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO prompt_presets
                    (id, project_id, name, description, system_prompt, answer_format, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    preset.id,
                    preset.project_id,
                    preset.name,
                    preset.description,
                    preset.system_prompt,
                    preset.answer_format,
                    preset.created_at,
                    preset.updated_at,
                ),
            )
        return preset

    def list_prompt_presets(self, project_id: str) -> list[PromptPreset]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, project_id, name, description, system_prompt, answer_format, created_at, updated_at
                FROM prompt_presets
                WHERE project_id = ?
                ORDER BY updated_at DESC
                """,
                (project_id,),
            ).fetchall()
        return [_prompt_preset_from_row(row) for row in rows]

    def get_prompt_preset(self, preset_id: str) -> PromptPreset | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, project_id, name, description, system_prompt, answer_format, created_at, updated_at
                FROM prompt_presets
                WHERE id = ?
                """,
                (preset_id,),
            ).fetchone()
        return _prompt_preset_from_row(row) if row else None

    def get_default_prompt_preset(self, project_id: str) -> PromptPreset | None:
        default_id = self.get_default_prompt_preset_id(project_id)
        if not default_id:
            return None
        preset = self.get_prompt_preset(default_id)
        if preset and preset.project_id == project_id:
            return preset
        return None

    def create_model_profile(
        self,
        name: str,
        provider: str,
        api_base: str,
        model: str,
        temperature: float,
        max_tokens: int,
        api_key_ref: str,
    ) -> ModelProfile:
        now = _now()
        profile = ModelProfile(
            id=str(uuid.uuid4()),
            name=name.strip(),
            provider=provider.strip(),
            api_base=api_base.strip(),
            model=model.strip(),
            temperature=temperature,
            max_tokens=max_tokens,
            api_key_ref=api_key_ref.strip(),
            is_default=False,
            created_at=now,
            updated_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO model_profiles
                    (id, name, provider, api_base, model, temperature, max_tokens, api_key_ref, is_default, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.id,
                    profile.name,
                    profile.provider,
                    profile.api_base,
                    profile.model,
                    profile.temperature,
                    profile.max_tokens,
                    profile.api_key_ref,
                    1 if profile.is_default else 0,
                    profile.created_at,
                    profile.updated_at,
                ),
            )
        return profile

    def list_model_profiles(self) -> list[ModelProfile]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, provider, api_base, model, temperature, max_tokens, api_key_ref, is_default, created_at, updated_at
                FROM model_profiles
                ORDER BY is_default DESC, updated_at DESC
                """
            ).fetchall()
        return [_model_profile_from_row(row) for row in rows]

    def get_model_profile(self, profile_id: str) -> ModelProfile | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, name, provider, api_base, model, temperature, max_tokens, api_key_ref, is_default, created_at, updated_at
                FROM model_profiles
                WHERE id = ?
                """,
                (profile_id,),
            ).fetchone()
        return _model_profile_from_row(row) if row else None

    def get_default_model_profile_id(self) -> str:
        with self._connect() as conn:
            row = conn.execute("SELECT id FROM model_profiles WHERE is_default = 1 LIMIT 1").fetchone()
        return row["id"] if row else ""

    def get_default_model_profile(self) -> ModelProfile | None:
        default_id = self.get_default_model_profile_id()
        return self.get_model_profile(default_id) if default_id else None

    def update_model_profile(
        self,
        profile_id: str,
        name: str,
        provider: str,
        api_base: str,
        model: str,
        temperature: float,
        max_tokens: int,
        api_key_ref: str,
    ) -> ModelProfile | None:
        with self._connect() as conn:
            result = conn.execute(
                """
                UPDATE model_profiles
                SET name = ?,
                    provider = ?,
                    api_base = ?,
                    model = ?,
                    temperature = ?,
                    max_tokens = ?,
                    api_key_ref = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    name.strip(),
                    provider.strip(),
                    api_base.strip(),
                    model.strip(),
                    temperature,
                    max_tokens,
                    api_key_ref.strip(),
                    _now(),
                    profile_id,
                ),
            )
        if result.rowcount == 0:
            return None
        return self.get_model_profile(profile_id)

    def delete_model_profile(self, profile_id: str) -> ModelProfile | None:
        profile = self.get_model_profile(profile_id)
        if not profile:
            return None
        with self._connect() as conn:
            conn.execute("DELETE FROM model_profiles WHERE id = ?", (profile_id,))
        return profile

    def set_default_model_profile(self, profile_id: str = "") -> str:
        clean_profile_id = profile_id.strip()
        with self._connect() as conn:
            conn.execute("UPDATE model_profiles SET is_default = 0")
            if clean_profile_id:
                result = conn.execute(
                    "UPDATE model_profiles SET is_default = 1, updated_at = ? WHERE id = ?",
                    (_now(), clean_profile_id),
                )
                if result.rowcount == 0:
                    return ""
        return clean_profile_id

    def update_prompt_preset(
        self,
        preset_id: str,
        name: str,
        description: str,
        system_prompt: str,
        answer_format: str,
    ) -> PromptPreset | None:
        now = _now()
        with self._connect() as conn:
            result = conn.execute(
                """
                UPDATE prompt_presets
                SET name = ?,
                    description = ?,
                    system_prompt = ?,
                    answer_format = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    name.strip(),
                    description.strip(),
                    system_prompt.strip(),
                    answer_format.strip(),
                    now,
                    preset_id,
                ),
            )
        if result.rowcount == 0:
            return None
        return self.get_prompt_preset(preset_id)

    def delete_prompt_preset(self, preset_id: str) -> PromptPreset | None:
        preset = self.get_prompt_preset(preset_id)
        if not preset:
            return None
        with self._connect() as conn:
            conn.execute(
                "UPDATE projects SET default_prompt_preset_id = NULL WHERE id = ? AND default_prompt_preset_id = ?",
                (preset.project_id, preset.id),
            )
            conn.execute("DELETE FROM prompt_presets WHERE id = ?", (preset_id,))
        return preset

    def rename_project(self, project_id: str, name: str) -> Project | None:
        clean_name = name.strip()
        with self._connect() as conn:
            result = conn.execute(
                "UPDATE projects SET name = ? WHERE id = ?",
                (clean_name, project_id),
            )
        if result.rowcount == 0:
            return None
        return self.get_project(project_id)

    def delete_project(self, project_id: str) -> bool:
        with self._connect() as conn:
            result = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        deleted = result.rowcount > 0
        if deleted:
            self._sync_vector_delete(project_id, None)
        return deleted

    def create_document_collection(
        self,
        project_id: str,
        name: str,
        description: str = "",
        color: str = "",
    ) -> DocumentCollection:
        now = _now()
        collection_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO document_collections
                    (id, project_id, name, description, color, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    collection_id,
                    project_id,
                    name.strip(),
                    description.strip(),
                    color.strip(),
                    now,
                    now,
                ),
            )
        collection = self.get_document_collection(collection_id)
        if not collection:
            raise RuntimeError("created document collection was not found")
        return collection

    def list_document_collections(self, project_id: str) -> list[DocumentCollection]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    c.id,
                    c.project_id,
                    c.name,
                    c.description,
                    c.color,
                    c.created_at,
                    c.updated_at,
                    COUNT(i.document_id) AS document_count
                FROM document_collections c
                LEFT JOIN document_collection_items i ON i.collection_id = c.id
                WHERE c.project_id = ?
                GROUP BY c.id
                ORDER BY c.updated_at DESC, c.name ASC
                """,
                (project_id,),
            ).fetchall()
        return [_document_collection_from_row(row) for row in rows]

    def get_document_collection(self, collection_id: str) -> DocumentCollection | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    c.id,
                    c.project_id,
                    c.name,
                    c.description,
                    c.color,
                    c.created_at,
                    c.updated_at,
                    COUNT(i.document_id) AS document_count
                FROM document_collections c
                LEFT JOIN document_collection_items i ON i.collection_id = c.id
                WHERE c.id = ?
                GROUP BY c.id
                """,
                (collection_id,),
            ).fetchone()
        return _document_collection_from_row(row) if row else None

    def update_document_collection(
        self,
        collection_id: str,
        name: str,
        description: str = "",
        color: str = "",
    ) -> DocumentCollection | None:
        with self._connect() as conn:
            result = conn.execute(
                """
                UPDATE document_collections
                SET name = ?, description = ?, color = ?, updated_at = ?
                WHERE id = ?
                """,
                (name.strip(), description.strip(), color.strip(), _now(), collection_id),
            )
        if result.rowcount == 0:
            return None
        return self.get_document_collection(collection_id)

    def delete_document_collection(self, collection_id: str) -> DocumentCollection | None:
        collection = self.get_document_collection(collection_id)
        if not collection:
            return None
        with self._connect() as conn:
            conn.execute("DELETE FROM document_collections WHERE id = ?", (collection_id,))
        return collection

    def add_documents_to_collection(
        self,
        collection_id: str,
        document_ids: list[str],
    ) -> DocumentCollection | None:
        collection = self.get_document_collection(collection_id)
        if not collection:
            return None
        clean_ids = _unique_non_empty(document_ids)
        if not self._documents_belong_to_project(clean_ids, collection.project_id):
            return None
        now = _now()
        with self._connect() as conn:
            for document_id in clean_ids:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO document_collection_items
                        (id, project_id, collection_id, document_id, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (str(uuid.uuid4()), collection.project_id, collection.id, document_id, now),
                )
            conn.execute(
                "UPDATE document_collections SET updated_at = ? WHERE id = ?",
                (now, collection.id),
            )
        return self.get_document_collection(collection_id)

    def remove_documents_from_collection(
        self,
        collection_id: str,
        document_ids: list[str],
    ) -> DocumentCollection | None:
        collection = self.get_document_collection(collection_id)
        if not collection:
            return None
        clean_ids = _unique_non_empty(document_ids)
        now = _now()
        with self._connect() as conn:
            for document_id in clean_ids:
                conn.execute(
                    """
                    DELETE FROM document_collection_items
                    WHERE collection_id = ? AND document_id = ?
                    """,
                    (collection.id, document_id),
                )
            conn.execute(
                "UPDATE document_collections SET updated_at = ? WHERE id = ?",
                (now, collection.id),
            )
        return self.get_document_collection(collection_id)

    def _documents_belong_to_project(self, document_ids: list[str], project_id: str) -> bool:
        if not document_ids:
            return True
        placeholders = ",".join("?" for _ in document_ids)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT id
                FROM documents
                WHERE project_id = ? AND id IN ({placeholders})
                """,
                (project_id, *document_ids),
            ).fetchall()
        return {row["id"] for row in rows} == set(document_ids)

    def upsert_document(
        self,
        project_id: str,
        source_path: Path,
        relative_path: str,
        content: str,
    ) -> DocumentWriteResult:
        checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
        now = _now()
        document_id = str(uuid.uuid4())
        action = "created"
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id, checksum FROM documents WHERE project_id = ? AND relative_path = ?",
                (project_id, relative_path),
            ).fetchone()
            if existing:
                document_id = existing["id"]
                action = "unchanged" if existing["checksum"] == checksum else "updated"
            document = Document(
                document_id,
                project_id,
                source_path,
                relative_path,
                content,
                checksum,
                now,
            )
            conn.execute(
                """
                INSERT INTO documents
                    (id, project_id, source_path, relative_path, content, checksum, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, relative_path) DO UPDATE SET
                    source_path = excluded.source_path,
                    content = excluded.content,
                    checksum = excluded.checksum,
                    updated_at = excluded.updated_at
                """,
                (
                    document_id,
                    project_id,
                    str(source_path),
                    relative_path,
                    content,
                    checksum,
                    now,
                ),
            )
            self._replace_document_chunks(conn, document)
        return DocumentWriteResult(document=document, action=action)

    def list_documents(self, project_id: str, collection_id: str = "") -> list[Document]:
        if collection_id == "unassigned":
            return self.list_unassigned_documents(project_id)
        if collection_id:
            return self.list_documents_for_collection(project_id, collection_id)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, project_id, source_path, relative_path, content, checksum, updated_at
                FROM documents
                WHERE project_id = ?
                ORDER BY relative_path ASC
                """,
                (project_id,),
            ).fetchall()
        return [_document_from_row(row) for row in rows]

    def create_import_batch(
        self,
        project_id: str,
        source_type: str,
        status: str,
        summary: dict[str, object],
        message: str = "",
        items: list[dict[str, object]] | None = None,
    ) -> ImportBatch:
        now = _now()
        batch_id = str(uuid.uuid4())
        clean_items = items or []
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO import_batches
                    (id, project_id, source_type, status, started_at, finished_at, summary_json, message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    project_id,
                    source_type,
                    status,
                    now,
                    now,
                    json.dumps(summary, ensure_ascii=False),
                    message.strip(),
                    now,
                ),
            )
            conn.executemany(
                """
                INSERT INTO import_batch_items
                    (id, batch_id, project_id, kind, relative_path, document_id, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        str(uuid.uuid4()),
                        batch_id,
                        project_id,
                        str(item.get("kind", "")).strip(),
                        str(item.get("relative_path", "")).strip(),
                        str(item.get("document_id", "")).strip(),
                        str(item.get("reason", "")).strip(),
                        now,
                    )
                    for item in clean_items
                ],
            )
        batch = self.get_import_batch(batch_id)
        if not batch:
            raise RuntimeError("created import batch was not found")
        return batch

    def list_import_batches(self, project_id: str, limit: int = 20) -> list[ImportBatch]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, project_id, source_type, status, started_at, finished_at, summary_json, message, created_at
                FROM import_batches
                WHERE project_id = ?
                ORDER BY rowid DESC
                LIMIT ?
                """,
                (project_id, limit),
            ).fetchall()
        return [_import_batch_from_row(row) for row in rows]

    def get_import_batch(self, batch_id: str) -> ImportBatch | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, project_id, source_type, status, started_at, finished_at, summary_json, message, created_at
                FROM import_batches
                WHERE id = ?
                """,
                (batch_id,),
            ).fetchone()
        return _import_batch_from_row(row) if row else None

    def list_import_batch_items(self, batch_id: str) -> list[ImportBatchItem]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, batch_id, project_id, kind, relative_path, document_id, reason, created_at
                FROM import_batch_items
                WHERE batch_id = ?
                ORDER BY rowid ASC
                """,
                (batch_id,),
            ).fetchall()
        return [_import_batch_item_from_row(row) for row in rows]

    def list_documents_for_collection(self, project_id: str, collection_id: str) -> list[Document]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT d.id, d.project_id, d.source_path, d.relative_path, d.content, d.checksum, d.updated_at
                FROM documents d
                JOIN document_collection_items i ON i.document_id = d.id
                WHERE d.project_id = ? AND i.collection_id = ?
                ORDER BY d.relative_path ASC
                """,
                (project_id, collection_id),
            ).fetchall()
        return [_document_from_row(row) for row in rows]

    def list_unassigned_documents(self, project_id: str) -> list[Document]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT d.id, d.project_id, d.source_path, d.relative_path, d.content, d.checksum, d.updated_at
                FROM documents d
                WHERE d.project_id = ?
                  AND NOT EXISTS (
                      SELECT 1
                      FROM document_collection_items i
                      WHERE i.document_id = d.id
                  )
                ORDER BY d.relative_path ASC
                """,
                (project_id,),
            ).fetchall()
        return [_document_from_row(row) for row in rows]

    def list_chunks(self, project_id: str) -> list[DocumentChunk]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    c.id AS chunk_id,
                    c.chunk_index,
                    c.content AS chunk_content,
                    c.token_count,
                    c.created_at AS chunk_created_at,
                    d.id,
                    d.project_id,
                    d.source_path,
                    d.relative_path,
                    d.content,
                    d.checksum,
                    d.updated_at
                FROM document_chunks c
                JOIN documents d ON d.id = c.document_id
                WHERE c.project_id = ?
                ORDER BY d.relative_path ASC, c.chunk_index ASC
                """,
                (project_id,),
            ).fetchall()
        return [_chunk_from_row(row) for row in rows]

    def list_chunk_vectors(self, project_id: str) -> dict[str, dict[str, float]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT chunk_id, vector_json FROM chunk_vectors WHERE project_id = ?",
                (project_id,),
            ).fetchall()
        return {row["chunk_id"]: deserialize_vector(row["vector_json"]) for row in rows}

    def list_chunk_vector_records(self, project_id: str) -> list[dict[str, object]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT chunk_id, vector_json, provider, model, updated_at
                FROM chunk_vectors
                WHERE project_id = ?
                ORDER BY chunk_id ASC
                """,
                (project_id,),
            ).fetchall()
        return [
            {
                "chunk_id": row["chunk_id"],
                "vector": deserialize_vector(row["vector_json"]),
                "provider": row["provider"],
                "model": row["model"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]

    def count_chunk_vectors(self, project_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS total FROM chunk_vectors WHERE project_id = ?",
                (project_id,),
            ).fetchone()
        return int(row["total"])

    def create_chat_message(
        self,
        project_id: str,
        question: str,
        answer: str,
        mode: str,
        provider: str,
        warning: str,
        sources: list[dict[str, object]],
        session_id: str = "",
        parent_message_id: str = "",
    ) -> ChatMessage:
        now = _now()
        parent_message_id = parent_message_id.strip()
        with self._connect() as conn:
            branch_index = _next_chat_branch_index(conn, parent_message_id) if parent_message_id else 0
            message = ChatMessage(
                id=str(uuid.uuid4()),
                project_id=project_id,
                question=question,
                answer=answer,
                mode=mode,
                provider=provider,
                warning=warning,
                sources=[dict(source) for source in sources],
                created_at=now,
                session_id=session_id,
                parent_message_id=parent_message_id,
                branch_index=branch_index,
            )
            conn.execute(
                """
                INSERT INTO chat_messages
                    (
                        id, project_id, session_id, parent_message_id, branch_index,
                        question, answer, mode, provider, warning, sources_json, created_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.project_id,
                    message.session_id or None,
                    message.parent_message_id or None,
                    message.branch_index,
                    message.question,
                    message.answer,
                    message.mode,
                    message.provider,
                    message.warning,
                    json.dumps(message.sources, ensure_ascii=False),
                    message.created_at,
                ),
            )
            if message.session_id:
                conn.execute(
                    "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
                    (now, message.session_id),
                )
        return message

    def list_chat_messages(self, project_id: str, session_id: str = "") -> list[ChatMessage]:
        with self._connect() as conn:
            if session_id:
                rows = conn.execute(
                    """
                    SELECT
                        id, project_id, session_id, parent_message_id, branch_index,
                        question, answer, mode, provider, warning, sources_json, created_at
                    FROM chat_messages
                    WHERE project_id = ? AND session_id = ?
                    ORDER BY created_at ASC
                    """,
                    (project_id, session_id),
                ).fetchall()
                return [_chat_message_from_row(row) for row in rows]
            rows = conn.execute(
                """
                SELECT
                    id, project_id, session_id, parent_message_id, branch_index,
                    question, answer, mode, provider, warning, sources_json, created_at
                FROM chat_messages
                WHERE project_id = ? AND session_id IS NULL
                ORDER BY created_at ASC
                """,
                (project_id,),
            ).fetchall()
        return [_chat_message_from_row(row) for row in rows]

    def list_all_chat_messages(self, project_id: str) -> list[ChatMessage]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    id, project_id, session_id, parent_message_id, branch_index,
                    question, answer, mode, provider, warning, sources_json, created_at
                FROM chat_messages
                WHERE project_id = ?
                ORDER BY created_at ASC
                """,
                (project_id,),
            ).fetchall()
        return [_chat_message_from_row(row) for row in rows]

    def create_chat_session(self, project_id: str, title: str = "") -> ChatSession:
        now = _now()
        session = ChatSession(
            id=str(uuid.uuid4()),
            project_id=project_id,
            title=title.strip() or "默认会话",
            created_at=now,
            updated_at=now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_sessions (id, project_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session.id, session.project_id, session.title, session.created_at, session.updated_at),
            )
        return session

    def restore_chat_session(
        self,
        project_id: str,
        title: str,
        created_at: str = "",
        updated_at: str = "",
    ) -> ChatSession:
        now = _now()
        session = ChatSession(
            id=str(uuid.uuid4()),
            project_id=project_id,
            title=title.strip() or "恢复会话",
            created_at=created_at or now,
            updated_at=updated_at or created_at or now,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_sessions (id, project_id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session.id, session.project_id, session.title, session.created_at, session.updated_at),
            )
        return session

    def list_chat_sessions(self, project_id: str) -> list[ChatSession]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, project_id, title, created_at, updated_at
                FROM chat_sessions
                WHERE project_id = ?
                ORDER BY updated_at DESC, created_at DESC
                """,
                (project_id,),
            ).fetchall()
        return [_chat_session_from_row(row) for row in rows]

    def get_chat_session(self, session_id: str) -> ChatSession | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, project_id, title, created_at, updated_at
                FROM chat_sessions
                WHERE id = ?
                """,
                (session_id,),
            ).fetchone()
        return _chat_session_from_row(row) if row else None

    def rename_chat_session(self, session_id: str, title: str) -> ChatSession | None:
        with self._connect() as conn:
            result = conn.execute(
                "UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?",
                (title.strip(), _now(), session_id),
            )
        if result.rowcount == 0:
            return None
        return self.get_chat_session(session_id)

    def delete_chat_session(self, session_id: str) -> ChatSession | None:
        session = self.get_chat_session(session_id)
        if not session:
            return None
        with self._connect() as conn:
            conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        return session

    def get_chat_message(self, message_id: str) -> ChatMessage | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    id, project_id, session_id, parent_message_id, branch_index,
                    question, answer, mode, provider, warning, sources_json, created_at
                FROM chat_messages
                WHERE id = ?
                """,
                (message_id,),
            ).fetchone()
        return _chat_message_from_row(row) if row else None

    def delete_chat_message(self, message_id: str) -> ChatMessage | None:
        message = self.get_chat_message(message_id)
        if not message:
            return None
        with self._connect() as conn:
            conn.execute("DELETE FROM chat_messages WHERE id = ?", (message_id,))
        return message

    def clear_chat_messages(self, project_id: str) -> int:
        with self._connect() as conn:
            result = conn.execute("DELETE FROM chat_messages WHERE project_id = ?", (project_id,))
        return result.rowcount

    def create_answer_feedback(
        self,
        project_id: str,
        message_id: str,
        rating: str,
        note: str = "",
    ) -> AnswerFeedback:
        feedback = AnswerFeedback(
            id=str(uuid.uuid4()),
            project_id=project_id,
            message_id=message_id,
            rating=rating,
            note=note.strip(),
            created_at=_now(),
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO answer_feedback
                    (id, project_id, message_id, rating, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback.id,
                    feedback.project_id,
                    feedback.message_id,
                    feedback.rating,
                    feedback.note,
                    feedback.created_at,
                ),
            )
        return feedback

    def restore_chat_message(
        self,
        project_id: str,
        question: str,
        answer: str,
        mode: str,
        provider: str,
        warning: str,
        sources: list[dict[str, object]],
        created_at: str,
        session_id: str = "",
        parent_message_id: str = "",
        branch_index: int = 0,
    ) -> ChatMessage:
        message = ChatMessage(
            id=str(uuid.uuid4()),
            project_id=project_id,
            question=question,
            answer=answer,
            mode=mode,
            provider=provider,
            warning=warning,
            sources=[dict(source) for source in sources],
            created_at=created_at or _now(),
            session_id=session_id,
            parent_message_id=parent_message_id.strip(),
            branch_index=max(0, int(branch_index or 0)),
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_messages
                    (
                        id, project_id, session_id, parent_message_id, branch_index,
                        question, answer, mode, provider, warning, sources_json, created_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.project_id,
                    message.session_id or None,
                    message.parent_message_id or None,
                    message.branch_index,
                    message.question,
                    message.answer,
                    message.mode,
                    message.provider,
                    message.warning,
                    json.dumps(message.sources, ensure_ascii=False),
                    message.created_at,
                ),
            )
        return message

    def list_answer_feedback(self, project_id: str) -> list[AnswerFeedback]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, project_id, message_id, rating, note, created_at
                FROM answer_feedback
                WHERE project_id = ?
                ORDER BY created_at DESC
                """,
                (project_id,),
            ).fetchall()
        return [_answer_feedback_from_row(row) for row in rows]

    def create_assessment_question(
        self,
        project_id: str,
        source_path: str,
        prompt: str,
        expected_points: list[str],
        reference_snippet: str,
        question_type: str = "concept",
        knowledge_point: str = "",
        question_id: str = "",
    ) -> AssessmentQuestion:
        question = AssessmentQuestion(
            id=question_id or str(uuid.uuid4()),
            project_id=project_id,
            source_path=source_path,
            question_type=question_type.strip() or "concept",
            knowledge_point=knowledge_point.strip(),
            prompt=prompt,
            expected_points=list(expected_points),
            reference_snippet=reference_snippet,
            created_at=_now(),
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO assessment_questions
                    (
                        id, project_id, source_path, question_type, knowledge_point,
                        prompt, expected_points_json, reference_snippet, created_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    question.id,
                    question.project_id,
                    question.source_path,
                    question.question_type,
                    question.knowledge_point,
                    question.prompt,
                    json.dumps(question.expected_points, ensure_ascii=False),
                    question.reference_snippet,
                    question.created_at,
                ),
            )
        return question

    def list_assessment_questions(self, project_id: str) -> list[AssessmentQuestion]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    id, project_id, source_path, question_type, knowledge_point,
                    prompt, expected_points_json, reference_snippet, created_at
                FROM assessment_questions
                WHERE project_id = ?
                ORDER BY created_at ASC
                """,
                (project_id,),
            ).fetchall()
        return [_assessment_question_from_row(row) for row in rows]

    def get_assessment_question(self, question_id: str) -> AssessmentQuestion | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    id, project_id, source_path, question_type, knowledge_point,
                    prompt, expected_points_json, reference_snippet, created_at
                FROM assessment_questions
                WHERE id = ?
                """,
                (question_id,),
            ).fetchone()
        return _assessment_question_from_row(row) if row else None

    def create_assessment_answer(
        self,
        project_id: str,
        question_id: str,
        answer: str,
    ) -> AssessmentAnswer:
        assessment_answer = AssessmentAnswer(
            id=str(uuid.uuid4()),
            project_id=project_id,
            question_id=question_id,
            answer=answer.strip(),
            created_at=_now(),
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO assessment_answers
                    (id, project_id, question_id, answer, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    assessment_answer.id,
                    assessment_answer.project_id,
                    assessment_answer.question_id,
                    assessment_answer.answer,
                    assessment_answer.created_at,
                ),
            )
        return assessment_answer

    def list_assessment_answers(self, project_id: str) -> list[AssessmentAnswer]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, project_id, question_id, answer, created_at
                FROM assessment_answers
                WHERE project_id = ?
                ORDER BY created_at ASC
                """,
                (project_id,),
            ).fetchall()
        return [_assessment_answer_from_row(row) for row in rows]

    def create_assessment_result(
        self,
        project_id: str,
        question_id: str,
        answer_id: str,
        status: str,
        score: float,
        matched_points: list[str],
        missing_points: list[str],
        feedback: str,
        source_path: str,
    ) -> AssessmentResult:
        result = AssessmentResult(
            id=str(uuid.uuid4()),
            project_id=project_id,
            question_id=question_id,
            answer_id=answer_id,
            status=status,
            score=score,
            matched_points=list(matched_points),
            missing_points=list(missing_points),
            feedback=feedback,
            source_path=source_path,
            created_at=_now(),
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO assessment_results
                    (
                        id, project_id, question_id, answer_id, status, score,
                        matched_points_json, missing_points_json, feedback,
                        source_path, created_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.id,
                    result.project_id,
                    result.question_id,
                    result.answer_id,
                    result.status,
                    result.score,
                    json.dumps(result.matched_points, ensure_ascii=False),
                    json.dumps(result.missing_points, ensure_ascii=False),
                    result.feedback,
                    result.source_path,
                    result.created_at,
                ),
            )
        return result

    def list_assessment_results(self, project_id: str) -> list[AssessmentResult]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    id, project_id, question_id, answer_id, status, score,
                    matched_points_json, missing_points_json, feedback,
                    source_path, created_at
                FROM assessment_results
                WHERE project_id = ?
                ORDER BY created_at ASC
                """,
                (project_id,),
            ).fetchall()
        return [_assessment_result_from_row(row) for row in rows]

    def create_agent_tool_run(
        self,
        project_id: str,
        tool_name: str,
        arguments: dict[str, object],
        result: dict[str, object],
        status: str,
        error: str = "",
    ) -> AgentToolRun:
        run = AgentToolRun(
            id=str(uuid.uuid4()),
            project_id=project_id,
            tool_name=tool_name,
            arguments=dict(arguments),
            result=dict(result),
            status=status,
            error=error,
            created_at=_now(),
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO agent_tool_runs
                    (id, project_id, tool_name, arguments_json, result_json, status, error, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.id,
                    run.project_id,
                    run.tool_name,
                    json.dumps(run.arguments, ensure_ascii=False),
                    json.dumps(run.result, ensure_ascii=False),
                    run.status,
                    run.error,
                    run.created_at,
                ),
            )
        return run

    def list_agent_tool_runs(self, project_id: str) -> list[AgentToolRun]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, project_id, tool_name, arguments_json, result_json, status, error, created_at
                FROM agent_tool_runs
                WHERE project_id = ?
                ORDER BY created_at ASC
                """,
                (project_id,),
            ).fetchall()
        return [_agent_tool_run_from_row(row) for row in rows]

    def get_agent_tool_run(self, run_id: str) -> AgentToolRun | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, project_id, tool_name, arguments_json, result_json, status, error, created_at
                FROM agent_tool_runs
                WHERE id = ?
                """,
                (run_id,),
            ).fetchone()
        return _agent_tool_run_from_row(row) if row else None

    def create_retrieval_review(
        self,
        project_id: str,
        query: str,
        parameters: dict[str, object],
        hits: list[dict[str, object]],
        source_quality: dict[str, object],
        note: str,
    ) -> RetrievalReview:
        review = RetrievalReview(
            id=str(uuid.uuid4()),
            project_id=project_id,
            query=query,
            parameters=parameters,
            hits=hits,
            source_quality=source_quality,
            note=note.strip(),
            created_at=_now(),
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO retrieval_reviews
                    (id, project_id, query, parameters_json, hits_json, quality_json, note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review.id,
                    review.project_id,
                    review.query,
                    json.dumps(review.parameters, ensure_ascii=False),
                    json.dumps(review.hits, ensure_ascii=False),
                    json.dumps(review.source_quality, ensure_ascii=False),
                    review.note,
                    review.created_at,
                ),
            )
        return review

    def list_retrieval_reviews(self, project_id: str, limit: int = 20) -> list[RetrievalReview]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, project_id, query, parameters_json, hits_json, quality_json, note, created_at
                FROM retrieval_reviews
                WHERE project_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (project_id, limit),
            ).fetchall()
        return [_retrieval_review_from_row(row) for row in rows]

    def get_retrieval_review(self, review_id: str) -> RetrievalReview | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, project_id, query, parameters_json, hits_json, quality_json, note, created_at
                FROM retrieval_reviews
                WHERE id = ?
                """,
                (review_id,),
            ).fetchone()
        return _retrieval_review_from_row(row) if row else None

    def delete_retrieval_review(self, review_id: str) -> RetrievalReview | None:
        review = self.get_retrieval_review(review_id)
        if not review:
            return None
        with self._connect() as conn:
            conn.execute("DELETE FROM retrieval_reviews WHERE id = ?", (review_id,))
        return review

    def get_document(self, document_id: str) -> Document | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, project_id, source_path, relative_path, content, checksum, updated_at
                FROM documents
                WHERE id = ?
                """,
                (document_id,),
            ).fetchone()
        return _document_from_row(row) if row else None

    def delete_document(self, document_id: str) -> Document | None:
        document = self.get_document(document_id)
        if not document:
            return None
        with self._connect() as conn:
            chunk_ids = _chunk_ids_for_documents(conn, [document.id])
            conn.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        self._sync_vector_delete(document.project_id, chunk_ids)
        return document

    def delete_documents_not_in(
        self,
        project_id: str,
        relative_paths: set[str],
        preserve_source_prefixes: tuple[str, ...] = (),
    ) -> int:
        documents = self.list_documents(project_id)
        preserved_paths = {
            doc.relative_path
            for doc in documents
            if str(doc.source_path).startswith(preserve_source_prefixes)
        }
        existing_paths = {doc.relative_path for doc in documents}
        relative_paths = set(relative_paths) | preserved_paths
        stale_paths = sorted(existing_paths - relative_paths)
        if not stale_paths:
            return 0
        stale_document_ids = [doc.id for doc in documents if doc.relative_path in stale_paths]
        with self._connect() as conn:
            chunk_ids = _chunk_ids_for_documents(conn, stale_document_ids)
            conn.executemany(
                "DELETE FROM documents WHERE project_id = ? AND relative_path = ?",
                [(project_id, relative_path) for relative_path in stale_paths],
            )
        self._sync_vector_delete(project_id, chunk_ids)
        return len(stale_paths)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    root_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    retrieval_top_k INTEGER NOT NULL DEFAULT 5,
                    retrieval_min_score REAL NOT NULL DEFAULT 0,
                    retrieval_use_keyword INTEGER NOT NULL DEFAULT 1,
                    retrieval_use_vector INTEGER NOT NULL DEFAULT 1,
                    default_prompt_preset_id TEXT
                );

                CREATE TABLE IF NOT EXISTS prompt_presets (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    system_prompt TEXT NOT NULL,
                    answer_format TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_prompt_presets_project
                    ON prompt_presets(project_id, updated_at);

                CREATE TABLE IF NOT EXISTS model_profiles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    api_base TEXT NOT NULL DEFAULT '',
                    model TEXT NOT NULL,
                    temperature REAL NOT NULL DEFAULT 0.7,
                    max_tokens INTEGER NOT NULL DEFAULT 2048,
                    api_key_ref TEXT NOT NULL DEFAULT '',
                    is_default INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_model_profiles_default
                    ON model_profiles(is_default, updated_at);

                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    content TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(project_id, relative_path),
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_documents_project
                    ON documents(project_id);

                CREATE TABLE IF NOT EXISTS document_collections (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    color TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(project_id, name),
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_document_collections_project
                    ON document_collections(project_id, updated_at);

                CREATE TABLE IF NOT EXISTS document_collection_items (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    collection_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(collection_id, document_id),
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY(collection_id) REFERENCES document_collections(id) ON DELETE CASCADE,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_document_collection_items_collection
                    ON document_collection_items(collection_id);

                CREATE INDEX IF NOT EXISTS idx_document_collection_items_document
                    ON document_collection_items(document_id);

                CREATE TABLE IF NOT EXISTS import_batches (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    summary_json TEXT NOT NULL,
                    message TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_import_batches_project
                    ON import_batches(project_id, created_at);

                CREATE TABLE IF NOT EXISTS import_batch_items (
                    id TEXT PRIMARY KEY,
                    batch_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    relative_path TEXT NOT NULL DEFAULT '',
                    document_id TEXT NOT NULL DEFAULT '',
                    reason TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(batch_id) REFERENCES import_batches(id) ON DELETE CASCADE,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_import_batch_items_batch
                    ON import_batch_items(batch_id, created_at);

                CREATE TABLE IF NOT EXISTS document_chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    project_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(document_id, chunk_index),
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_document_chunks_project
                    ON document_chunks(project_id);

                CREATE TABLE IF NOT EXISTS chunk_vectors (
                    chunk_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    vector_json TEXT NOT NULL,
                    provider TEXT NOT NULL DEFAULT 'local',
                    model TEXT NOT NULL DEFAULT 'hashing-96',
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(chunk_id) REFERENCES document_chunks(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_chunk_vectors_project
                    ON chunk_vectors(project_id);

                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_chat_sessions_project
                    ON chat_sessions(project_id, updated_at);

                CREATE TABLE IF NOT EXISTS chat_messages (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    session_id TEXT,
                    parent_message_id TEXT,
                    branch_index INTEGER NOT NULL DEFAULT 0,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    warning TEXT NOT NULL DEFAULT '',
                    sources_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_chat_messages_project
                    ON chat_messages(project_id, created_at);

                CREATE TABLE IF NOT EXISTS answer_feedback (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    message_id TEXT NOT NULL,
                    rating TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY(message_id) REFERENCES chat_messages(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_answer_feedback_project
                    ON answer_feedback(project_id, created_at);

                CREATE TABLE IF NOT EXISTS assessment_questions (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    question_type TEXT NOT NULL DEFAULT 'concept',
                    knowledge_point TEXT NOT NULL DEFAULT '',
                    prompt TEXT NOT NULL,
                    expected_points_json TEXT NOT NULL,
                    reference_snippet TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_assessment_questions_project
                    ON assessment_questions(project_id, created_at);

                CREATE TABLE IF NOT EXISTS assessment_answers (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY(question_id) REFERENCES assessment_questions(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_assessment_answers_project
                    ON assessment_answers(project_id, created_at);

                CREATE TABLE IF NOT EXISTS assessment_results (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    answer_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    score REAL NOT NULL,
                    matched_points_json TEXT NOT NULL,
                    missing_points_json TEXT NOT NULL,
                    feedback TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY(question_id) REFERENCES assessment_questions(id) ON DELETE CASCADE,
                    FOREIGN KEY(answer_id) REFERENCES assessment_answers(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_assessment_results_project
                    ON assessment_results(project_id, created_at);

                CREATE TABLE IF NOT EXISTS agent_tool_runs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    arguments_json TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_agent_tool_runs_project
                    ON agent_tool_runs(project_id, created_at);

                CREATE TABLE IF NOT EXISTS retrieval_reviews (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    hits_json TEXT NOT NULL,
                    quality_json TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_retrieval_reviews_project
                    ON retrieval_reviews(project_id, created_at);
                """
            )
            _ensure_column(conn, "projects", "retrieval_top_k", "INTEGER NOT NULL DEFAULT 5")
            _ensure_column(conn, "projects", "retrieval_min_score", "REAL NOT NULL DEFAULT 0")
            _ensure_column(conn, "projects", "retrieval_use_keyword", "INTEGER NOT NULL DEFAULT 1")
            _ensure_column(conn, "projects", "retrieval_use_vector", "INTEGER NOT NULL DEFAULT 1")
            _ensure_column(conn, "projects", "default_prompt_preset_id", "TEXT")
            _ensure_column(conn, "chat_messages", "session_id", "TEXT")
            _ensure_column(conn, "chat_messages", "parent_message_id", "TEXT")
            _ensure_column(conn, "chat_messages", "branch_index", "INTEGER NOT NULL DEFAULT 0")
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chat_messages_parent
                    ON chat_messages(parent_message_id, branch_index)
                """
            )
            _ensure_column(conn, "chunk_vectors", "provider", "TEXT NOT NULL DEFAULT 'local'")
            _ensure_column(conn, "chunk_vectors", "model", "TEXT NOT NULL DEFAULT 'hashing-96'")
            _ensure_column(conn, "assessment_questions", "question_type", "TEXT NOT NULL DEFAULT 'concept'")
            _ensure_column(conn, "assessment_questions", "knowledge_point", "TEXT NOT NULL DEFAULT ''")
            self._backfill_document_chunks(conn)
            self._backfill_chunk_vectors(conn)

    def _replace_document_chunks(self, conn: sqlite3.Connection, document: Document) -> None:
        old_chunk_ids = _chunk_ids_for_documents(conn, [document.id])
        conn.execute("DELETE FROM document_chunks WHERE document_id = ?", (document.id,))
        chunk_rows = []
        vector_rows = []
        vector_records: list[VectorUpsertRecord] = []
        now = _now()
        chunks = split_into_chunks(document.content)
        vectors, provider, model = embed_with_fallback(self._embedding_client, chunks)
        for index, chunk in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            chunk_rows.append(
                (
                    chunk_id,
                    document.id,
                    document.project_id,
                    index,
                    chunk,
                    count_tokens(chunk),
                    now,
                )
            )
            vector_rows.append(
                (
                    chunk_id,
                    document.project_id,
                    serialize_vector(vectors[index]),
                    provider,
                    model,
                    now,
                )
            )
            vector_records.append(
                VectorUpsertRecord(
                    project_id=document.project_id,
                    document_id=document.id,
                    chunk_id=chunk_id,
                    chunk_index=index,
                    path=document.relative_path,
                    content=chunk,
                    vector=vectors[index],
                    provider=provider,
                    model=model,
                )
            )
        conn.executemany(
            """
            INSERT INTO document_chunks
                (id, document_id, project_id, chunk_index, content, token_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            chunk_rows,
        )
        conn.executemany(
            """
            INSERT INTO chunk_vectors
                (chunk_id, project_id, vector_json, provider, model, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            vector_rows,
        )
        self._sync_vector_delete(document.project_id, old_chunk_ids)
        self._sync_vector_upsert(vector_records)

    def _backfill_document_chunks(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute(
            """
            SELECT
                d.id,
                d.project_id,
                d.source_path,
                d.relative_path,
                d.content,
                d.checksum,
                d.updated_at
            FROM documents d
            LEFT JOIN document_chunks c ON c.document_id = d.id
            WHERE c.id IS NULL
            """
        ).fetchall()
        for row in rows:
            self._replace_document_chunks(conn, _document_from_row(row))

    def _backfill_chunk_vectors(self, conn: sqlite3.Connection) -> None:
        now = _now()
        rows = conn.execute(
            """
            SELECT c.id, c.project_id, c.content
            FROM document_chunks c
            LEFT JOIN chunk_vectors v ON v.chunk_id = c.id
            WHERE v.chunk_id IS NULL
            """
        ).fetchall()
        chunks = [row["content"] for row in rows]
        vectors, provider, model = embed_with_fallback(self._embedding_client, chunks)
        conn.executemany(
            """
            INSERT INTO chunk_vectors
                (chunk_id, project_id, vector_json, provider, model, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["id"],
                    row["project_id"],
                    serialize_vector(vectors[index]),
                    provider,
                    model,
                    now,
                )
                for index, row in enumerate(rows)
            ],
        )

    def _sync_vector_upsert(self, records: list[VectorUpsertRecord]) -> None:
        if not self._vector_store or not records:
            return
        try:
            self._vector_store.upsert(records)
        except Exception as exc:
            print(f"WARNING: vector store upsert failed: {exc}", file=sys.stderr)

    def _sync_vector_delete(self, project_id: str, chunk_ids: list[str] | None) -> None:
        if not self._vector_store or chunk_ids == []:
            return
        try:
            self._vector_store.delete(project_id, chunk_ids)
        except Exception as exc:
            print(f"WARNING: vector store delete failed: {exc}", file=sys.stderr)


def _chunk_ids_for_documents(conn: sqlite3.Connection, document_ids: list[str]) -> list[str]:
    if not document_ids:
        return []
    placeholders = ",".join("?" for _ in document_ids)
    rows = conn.execute(
        f"""
        SELECT id
        FROM document_chunks
        WHERE document_id IN ({placeholders})
        ORDER BY document_id ASC, chunk_index ASC
        """,
        document_ids,
    ).fetchall()
    return [row["id"] for row in rows]


def _int_snapshot_value(value: object, default: int) -> int:
    if isinstance(value, int | float):
        return int(value)
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _snapshot_vector(value: object) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): float(raw_value)
        for key, raw_value in value.items()
        if isinstance(raw_value, int | float)
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_from_row(row: sqlite3.Row) -> Project:
    return Project(row["id"], row["name"], Path(row["root_path"]), row["created_at"])


def _chat_session_from_row(row: sqlite3.Row) -> ChatSession:
    return ChatSession(
        id=row["id"],
        project_id=row["project_id"],
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _prompt_preset_from_row(row: sqlite3.Row) -> PromptPreset:
    return PromptPreset(
        id=row["id"],
        project_id=row["project_id"],
        name=row["name"],
        description=row["description"],
        system_prompt=row["system_prompt"],
        answer_format=row["answer_format"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _model_profile_from_row(row: sqlite3.Row) -> ModelProfile:
    return ModelProfile(
        id=row["id"],
        name=row["name"],
        provider=row["provider"],
        api_base=row["api_base"],
        model=row["model"],
        temperature=float(row["temperature"]),
        max_tokens=int(row["max_tokens"]),
        api_key_ref=row["api_key_ref"],
        is_default=bool(row["is_default"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _retrieval_settings_from_row(row: sqlite3.Row) -> dict[str, object]:
    return {
        "project_id": row["project_id"],
        "top_k": int(row["retrieval_top_k"]),
        "min_score": float(row["retrieval_min_score"]),
        "use_keyword": bool(row["retrieval_use_keyword"]),
        "use_vector": bool(row["retrieval_use_vector"]),
    }


def _ensure_column(
    conn: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table_name})")}
    if column_name not in columns:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


def _document_from_row(row: sqlite3.Row) -> Document:
    return Document(
        row["id"],
        row["project_id"],
        Path(row["source_path"]),
        row["relative_path"],
        row["content"],
        row["checksum"],
        row["updated_at"],
    )


def _document_collection_from_row(row: sqlite3.Row) -> DocumentCollection:
    return DocumentCollection(
        id=row["id"],
        project_id=row["project_id"],
        name=row["name"],
        description=row["description"],
        color=row["color"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        document_count=int(row["document_count"]),
    )


def _import_batch_from_row(row: sqlite3.Row) -> ImportBatch:
    return ImportBatch(
        id=row["id"],
        project_id=row["project_id"],
        source_type=row["source_type"],
        status=row["status"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        summary=_json_object(row["summary_json"]),
        message=row["message"],
        created_at=row["created_at"],
    )


def _import_batch_item_from_row(row: sqlite3.Row) -> ImportBatchItem:
    return ImportBatchItem(
        id=row["id"],
        batch_id=row["batch_id"],
        project_id=row["project_id"],
        kind=row["kind"],
        relative_path=row["relative_path"],
        document_id=row["document_id"],
        reason=row["reason"],
        created_at=row["created_at"],
    )


def _chunk_from_row(row: sqlite3.Row) -> DocumentChunk:
    document = Document(
        row["id"],
        row["project_id"],
        Path(row["source_path"]),
        row["relative_path"],
        row["content"],
        row["checksum"],
        row["updated_at"],
    )
    return DocumentChunk(
        id=row["chunk_id"],
        document=document,
        chunk_index=row["chunk_index"],
        content=row["chunk_content"],
        token_count=row["token_count"],
        created_at=row["chunk_created_at"],
    )


def _next_chat_branch_index(conn: sqlite3.Connection, parent_message_id: str) -> int:
    row = conn.execute(
        """
        SELECT COALESCE(MAX(branch_index), 0) AS branch_index
        FROM chat_messages
        WHERE parent_message_id = ?
        """,
        (parent_message_id,),
    ).fetchone()
    return int(row["branch_index"] or 0) + 1


def _chat_message_from_row(row: sqlite3.Row) -> ChatMessage:
    try:
        sources = json.loads(row["sources_json"])
    except json.JSONDecodeError:
        sources = []
    if not isinstance(sources, list):
        sources = []
    return ChatMessage(
        id=row["id"],
        project_id=row["project_id"],
        question=row["question"],
        answer=row["answer"],
        mode=row["mode"],
        provider=row["provider"],
        warning=row["warning"],
        sources=[source for source in sources if isinstance(source, dict)],
        created_at=row["created_at"],
        session_id=row["session_id"] or "",
        parent_message_id=row["parent_message_id"] or "",
        branch_index=int(row["branch_index"] or 0),
    )


def _answer_feedback_from_row(row: sqlite3.Row) -> AnswerFeedback:
    return AnswerFeedback(
        id=row["id"],
        project_id=row["project_id"],
        message_id=row["message_id"],
        rating=row["rating"],
        note=row["note"],
        created_at=row["created_at"],
    )


def _assessment_question_from_row(row: sqlite3.Row) -> AssessmentQuestion:
    return AssessmentQuestion(
        id=row["id"],
        project_id=row["project_id"],
        source_path=row["source_path"],
        question_type=row["question_type"],
        knowledge_point=row["knowledge_point"],
        prompt=row["prompt"],
        expected_points=list(json.loads(row["expected_points_json"])),
        reference_snippet=row["reference_snippet"],
        created_at=row["created_at"],
    )


def _assessment_answer_from_row(row: sqlite3.Row) -> AssessmentAnswer:
    return AssessmentAnswer(
        id=row["id"],
        project_id=row["project_id"],
        question_id=row["question_id"],
        answer=row["answer"],
        created_at=row["created_at"],
    )


def _assessment_result_from_row(row: sqlite3.Row) -> AssessmentResult:
    return AssessmentResult(
        id=row["id"],
        project_id=row["project_id"],
        question_id=row["question_id"],
        answer_id=row["answer_id"],
        status=row["status"],
        score=float(row["score"]),
        matched_points=list(json.loads(row["matched_points_json"])),
        missing_points=list(json.loads(row["missing_points_json"])),
        feedback=row["feedback"],
        source_path=row["source_path"],
        created_at=row["created_at"],
    )


def _agent_tool_run_from_row(row: sqlite3.Row) -> AgentToolRun:
    return AgentToolRun(
        id=row["id"],
        project_id=row["project_id"],
        tool_name=row["tool_name"],
        arguments=_json_object(row["arguments_json"]),
        result=_json_object(row["result_json"]),
        status=row["status"],
        error=row["error"],
        created_at=row["created_at"],
    )


def _retrieval_review_from_row(row: sqlite3.Row) -> RetrievalReview:
    return RetrievalReview(
        id=row["id"],
        project_id=row["project_id"],
        query=row["query"],
        parameters=_json_object(row["parameters_json"]),
        hits=_json_list_of_objects(row["hits_json"]),
        source_quality=_json_object(row["quality_json"]),
        note=row["note"],
        created_at=row["created_at"],
    )


def _unique_non_empty(values: list[str]) -> list[str]:
    clean_values = []
    seen = set()
    for value in values:
        clean = str(value).strip()
        if clean and clean not in seen:
            clean_values.append(clean)
            seen.add(clean)
    return clean_values


def _json_object(raw: str) -> dict[str, object]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _json_list_of_objects(raw: str) -> list[dict[str, object]]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [entry for entry in data if isinstance(entry, dict)]
