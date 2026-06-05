from __future__ import annotations

from typing import Iterable, List, Optional

from legacy.desktop.domain.errors import ValidationError
from legacy.desktop.domain.models.source import Source
from legacy.desktop.domain.models.tag import Tag, DocumentTag
from legacy.desktop.ports.source_store import ISourceStore
from legacy.desktop.ports.tag_store import IDocumentTagStore, ITagStore


class DocumentTaggingUseCase:
    """文档标签的最小应用用例。"""

    def __init__(
        self,
        tag_store: ITagStore,
        document_tag_store: IDocumentTagStore,
    ) -> None:
        self._tag_store = tag_store
        self._document_tag_store = document_tag_store

    def set_document_tags(self, document_id: str, names: Iterable[str]) -> List[Tag]:
        tags = self._normalize_names(names)
        if not tags:
            self._document_tag_store.delete_by_document(document_id)
            return []

        tag_models = [self._get_or_create_tag(name) for name in tags]
        self._document_tag_store.delete_by_document(document_id)
        for tag in tag_models:
            self._document_tag_store.save(DocumentTag.create(document_id=document_id, tag_id=tag.id))
        return tag_models

    def list_document_tags(self, document_id: str) -> List[Tag]:
        tag_ids = self._document_tag_store.list_tag_ids_by_document(document_id)
        tags = [tag for tag in (self._tag_store.get(tag_id) for tag_id in tag_ids) if tag is not None]
        return sorted(tags, key=lambda tag: tag.name)

    def clear_document_tags(self, document_id: str) -> None:
        self._document_tag_store.delete_by_document(document_id)

    def _normalize_names(self, names: Iterable[str]) -> List[str]:
        normalized = []
        seen = set()
        for name in names:
            value = (name or "").strip()
            if not value or value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        return normalized

    def _get_or_create_tag(self, name: str) -> Tag:
        normalized = name.strip()
        if not normalized:
            raise ValidationError("标签名称不能为空")
        tag = self._tag_store.get_by_name(normalized)
        if tag is not None:
            return tag
        tag = Tag.create(name=normalized, color="")
        self._tag_store.save(tag)
        return tag


class SourceUseCase:
    """导入来源记录与 checksum 判重。"""

    def __init__(self, store: ISourceStore) -> None:
        self._store = store

    def upsert_source(
        self,
        document_id: str,
        source_type: str,
        source_path: str,
        checksum: str = "",
    ) -> Source:
        source = Source.create(
            document_id=document_id,
            source_type=source_type,
            source_path=source_path,
            checksum=checksum,
        )
        self._store.save(source)
        return source

    def get_by_document(self, document_id: str) -> Optional[Source]:
        return self._store.get_by_document(document_id)

    def is_unchanged(self, source_path: str, checksum: str) -> bool:
        if not source_path or not checksum:
            return False
        return self._store.exists_same_checksum(source_path, checksum)

    def last_source_for_path(self, source_path: str) -> Optional[Source]:
        return self._store.find_by_path(source_path)
