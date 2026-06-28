from __future__ import annotations

import importlib.util
import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from backend.config.paths import app_data_dir
from backend.providers.base import BaseVectorStore
from backend.providers.vector_store.qdrant import QdrantVectorStore

DEFAULT_VECTOR_STORE_PROVIDER = "sqlite"
DEFAULT_QDRANT_COLLECTION = "knowledge_island_chunks"
DEFAULT_QDRANT_VECTOR_SIZE = 96


@dataclass(frozen=True)
class VectorStoreSettings:
    enabled: bool = False
    provider: str = DEFAULT_VECTOR_STORE_PROVIDER
    path: Path = app_data_dir() / "qdrant"
    collection: str = DEFAULT_QDRANT_COLLECTION
    vector_size: int = DEFAULT_QDRANT_VECTOR_SIZE


_CACHED_KEY: tuple[bool, str, Path, str, int] | None = None
_CACHED_VECTOR_STORE: BaseVectorStore | None = None


def load_vector_store_settings(environ: Mapping[str, str] | None = None) -> VectorStoreSettings:
    values = os.environ if environ is None else environ
    provider = str(values.get("RAG_VECTOR_STORE_PROVIDER") or DEFAULT_VECTOR_STORE_PROVIDER).strip().lower()
    return VectorStoreSettings(
        enabled=provider == "qdrant",
        provider=provider,
        path=Path(values.get("RAG_QDRANT_PATH") or app_data_dir() / "qdrant"),
        collection=str(values.get("RAG_QDRANT_COLLECTION") or DEFAULT_QDRANT_COLLECTION),
        vector_size=_positive_int(values.get("RAG_QDRANT_VECTOR_SIZE"), DEFAULT_QDRANT_VECTOR_SIZE),
    )


def build_vector_store(
    settings: VectorStoreSettings | None = None,
    *,
    dependency_available: Callable[[], bool] | None = None,
) -> BaseVectorStore | None:
    current = settings or load_vector_store_settings()
    if not current.enabled:
        return None
    if current.provider != "qdrant":
        print(
            f"WARNING: unsupported vector store provider {current.provider!r}; using SQLite fallback",
            file=sys.stderr,
        )
        return None
    dependency_check = dependency_available or _qdrant_available
    if not dependency_check():
        print(
            "WARNING: qdrant-client is not installed; Qdrant vector store disabled",
            file=sys.stderr,
        )
        return None
    return QdrantVectorStore(
        path=current.path,
        collection=current.collection,
        vector_size=current.vector_size,
    )


def get_default_vector_store() -> BaseVectorStore | None:
    global _CACHED_KEY, _CACHED_VECTOR_STORE

    settings = load_vector_store_settings()
    key = (
        settings.enabled,
        settings.provider,
        settings.path,
        settings.collection,
        settings.vector_size,
    )
    if _CACHED_KEY == key:
        return _CACHED_VECTOR_STORE

    _CACHED_KEY = key
    _CACHED_VECTOR_STORE = build_vector_store(settings)
    return _CACHED_VECTOR_STORE


def _qdrant_available() -> bool:
    return importlib.util.find_spec("qdrant_client") is not None


def _positive_int(value: str | None, default: int) -> int:
    try:
        parsed = int(value) if value is not None else default
    except ValueError:
        return default
    return parsed if parsed > 0 else default


__all__ = [
    "DEFAULT_QDRANT_COLLECTION",
    "DEFAULT_QDRANT_VECTOR_SIZE",
    "DEFAULT_VECTOR_STORE_PROVIDER",
    "VectorStoreSettings",
    "build_vector_store",
    "get_default_vector_store",
    "load_vector_store_settings",
]
