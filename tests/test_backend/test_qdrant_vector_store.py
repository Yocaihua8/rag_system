from __future__ import annotations

from dataclasses import dataclass

from backend.providers.base import VectorUpsertRecord


def test_qdrant_settings_default_sqlite_and_env_override(tmp_path):
    from backend.config.vector_store import load_vector_store_settings

    defaults = load_vector_store_settings({})
    enabled = load_vector_store_settings(
        {
            "RAG_VECTOR_STORE_PROVIDER": "qdrant",
            "RAG_QDRANT_PATH": str(tmp_path / "vectors"),
            "RAG_QDRANT_COLLECTION": "test_chunks",
            "RAG_QDRANT_VECTOR_SIZE": "4",
        }
    )

    assert defaults.enabled is False
    assert defaults.provider == "sqlite"
    assert enabled.enabled is True
    assert enabled.provider == "qdrant"
    assert enabled.path == tmp_path / "vectors"
    assert enabled.collection == "test_chunks"
    assert enabled.vector_size == 4


def test_qdrant_settings_invalid_vector_size_uses_default(tmp_path):
    from backend.config.vector_store import DEFAULT_QDRANT_VECTOR_SIZE, load_vector_store_settings

    for raw_value in ("0", "-1", "not-an-int"):
        settings = load_vector_store_settings(
            {
                "RAG_VECTOR_STORE_PROVIDER": "qdrant",
                "RAG_QDRANT_PATH": str(tmp_path / raw_value),
                "RAG_QDRANT_VECTOR_SIZE": raw_value,
            }
        )

        assert settings.vector_size == DEFAULT_QDRANT_VECTOR_SIZE


def test_build_vector_store_returns_none_when_disabled():
    from backend.config.vector_store import VectorStoreSettings, build_vector_store

    store = build_vector_store(VectorStoreSettings(enabled=False), dependency_available=lambda: True)

    assert store is None


def test_build_vector_store_warns_for_unsupported_enabled_provider(capsys, tmp_path):
    from backend.config.vector_store import VectorStoreSettings, build_vector_store

    store = build_vector_store(
        VectorStoreSettings(
            enabled=True,
            provider="unknown",
            path=tmp_path / "vectors",
            collection="chunks",
            vector_size=4,
        ),
        dependency_available=lambda: True,
    )

    assert store is None
    assert "WARNING: unsupported vector store provider 'unknown'; using SQLite fallback" in capsys.readouterr().err


def test_build_vector_store_warns_when_qdrant_dependency_missing(capsys, tmp_path):
    from backend.config.vector_store import VectorStoreSettings, build_vector_store

    store = build_vector_store(
        VectorStoreSettings(
            enabled=True,
            provider="qdrant",
            path=tmp_path / "vectors",
            collection="chunks",
            vector_size=4,
        ),
        dependency_available=lambda: False,
    )

    assert store is None
    assert "WARNING: qdrant-client is not installed; Qdrant vector store disabled" in capsys.readouterr().err


def test_vector_dict_to_dense_keeps_numeric_dimensions_and_hashes_tokens():
    from backend.providers.vector_store.qdrant import vector_dict_to_dense

    dense = vector_dict_to_dense({"0": 1.0, "3": 0.5}, size=4)
    token_dense = vector_dict_to_dense({"deepseek": 1.0, "api": 0.25}, size=8)

    assert dense == [1.0, 0.0, 0.0, 0.5]
    assert len(token_dense) == 8
    assert sum(token_dense) == 1.25


def test_qdrant_vector_store_upserts_and_queries_with_local_client(tmp_path):
    from backend.providers.vector_store.qdrant import QdrantVectorStore

    clients = []

    def factory(path):
        client = _FakeQdrantClient(path)
        clients.append(client)
        return client

    store = QdrantVectorStore(
        path=tmp_path / "qdrant",
        collection="chunks",
        vector_size=4,
        client_factory=factory,
        models_module=_FakeModels,
    )
    record = VectorUpsertRecord(
        project_id="project-1",
        document_id="doc-1",
        chunk_id="chunk-1",
        chunk_index=2,
        path="docs/guide.md",
        content="DeepSeek API Key setup",
        vector={"0": 1.0, "3": 0.5},
        provider="api",
        model="fake-embedding",
    )

    store.upsert([record])
    clients[0].query_response = _FakeQueryResponse(
        [
            _FakeScoredPoint(
                id="chunk-1",
                score=0.91,
                payload={"provider": "api", "model": "fake-embedding"},
            )
        ]
    )
    hits = store.search("project-1", {"0": 1.0}, limit=3)

    assert clients[0].path == tmp_path / "qdrant"
    assert clients[0].created_collections == [
        {
            "collection_name": "chunks",
            "vectors_config": _FakeVectorParams(size=4, distance="Cosine"),
        }
    ]
    assert clients[0].upserts[0]["collection_name"] == "chunks"
    assert clients[0].upserts[0]["points"] == [
        _FakePointStruct(
            id="chunk-1",
            vector=[1.0, 0.0, 0.0, 0.5],
            payload={
                "project_id": "project-1",
                "document_id": "doc-1",
                "chunk_id": "chunk-1",
                "chunk_index": 2,
                "path": "docs/guide.md",
                "content": "DeepSeek API Key setup",
                "provider": "api",
                "model": "fake-embedding",
            },
        )
    ]
    assert clients[0].queries[0]["collection_name"] == "chunks"
    assert clients[0].queries[0]["query"] == [1.0, 0.0, 0.0, 0.0]
    assert clients[0].queries[0]["query_filter"] == _FakeFilter(
        must=[
            _FakeFieldCondition(
                key="project_id",
                match=_FakeMatchValue(value="project-1"),
            )
        ]
    )
    assert [(hit.chunk_id, hit.score, hit.provider, hit.model) for hit in hits] == [
        ("chunk-1", 0.91, "api", "fake-embedding")
    ]


def test_qdrant_vector_store_search_uses_payload_chunk_id_and_default_metadata(tmp_path):
    from backend.providers.vector_store.qdrant import QdrantVectorStore

    client = _FakeQdrantClient(tmp_path / "qdrant")
    store = QdrantVectorStore(
        path=tmp_path / "qdrant",
        collection="chunks",
        vector_size=4,
        client_factory=lambda path: client,
        models_module=_FakeModels,
    )
    client.query_response = _FakeQueryResponse(
        [
            _FakeScoredPoint(id="point-1", score=0.8, payload={"chunk_id": "payload-chunk"}),
            _FakeScoredPoint(id="", score=0.7, payload={}),
        ]
    )

    hits = store.search("project-1", {"0": 1.0}, limit=2)

    assert [(hit.chunk_id, hit.score, hit.provider, hit.model) for hit in hits] == [
        ("payload-chunk", 0.8, "local", "hashing-96"),
    ]


def test_qdrant_vector_store_delete_uses_chunk_ids_or_project_filter(tmp_path):
    from backend.providers.vector_store.qdrant import QdrantVectorStore

    client = _FakeQdrantClient(tmp_path / "qdrant")
    store = QdrantVectorStore(
        path=tmp_path / "qdrant",
        collection="chunks",
        vector_size=4,
        client_factory=lambda path: client,
        models_module=_FakeModels,
    )

    store.delete("project-1", chunk_ids=["chunk-1", "chunk-2"])
    store.delete("project-1")

    assert client.deletes == [
        {
            "collection_name": "chunks",
            "points_selector": _FakePointIdsList(points=["chunk-1", "chunk-2"]),
        },
        {
            "collection_name": "chunks",
            "points_selector": _FakeFilterSelector(
                filter=_FakeFilter(
                    must=[
                        _FakeFieldCondition(
                            key="project_id",
                            match=_FakeMatchValue(value="project-1"),
                        )
                    ]
                )
            ),
        },
    ]


def test_qdrant_vector_store_availability_warning_downgrades_without_raising(capsys, tmp_path):
    from backend.providers.vector_store.qdrant import QdrantVectorStore

    store = QdrantVectorStore(
        path=tmp_path / "qdrant",
        collection="chunks",
        vector_size=4,
        client_factory=lambda path: _BrokenQdrantClient(),
        models_module=_FakeModels,
    )

    assert store.is_available() is False
    assert "WARNING: Qdrant vector store unavailable: local mode failed" in capsys.readouterr().err


@dataclass(frozen=True)
class _FakeVectorParams:
    size: int
    distance: str


@dataclass(frozen=True)
class _FakePointStruct:
    id: str
    vector: list[float]
    payload: dict[str, object]


@dataclass(frozen=True)
class _FakeMatchValue:
    value: str


@dataclass(frozen=True)
class _FakeFieldCondition:
    key: str
    match: _FakeMatchValue


@dataclass(frozen=True)
class _FakeFilter:
    must: list[_FakeFieldCondition]


@dataclass(frozen=True)
class _FakePointIdsList:
    points: list[str]


@dataclass(frozen=True)
class _FakeFilterSelector:
    filter: _FakeFilter


@dataclass(frozen=True)
class _FakeScoredPoint:
    id: str
    score: float
    payload: dict[str, object]


@dataclass(frozen=True)
class _FakeQueryResponse:
    points: list[_FakeScoredPoint]


class _FakeDistance:
    COSINE = "Cosine"


class _FakeModels:
    Distance = _FakeDistance
    FieldCondition = _FakeFieldCondition
    FilterSelector = _FakeFilterSelector
    Filter = _FakeFilter
    MatchValue = _FakeMatchValue
    PointIdsList = _FakePointIdsList
    PointStruct = _FakePointStruct
    VectorParams = _FakeVectorParams


class _FakeQdrantClient:
    def __init__(self, path):
        self.path = path
        self.collections = set()
        self.created_collections = []
        self.upserts = []
        self.queries = []
        self.deletes = []
        self.query_response = _FakeQueryResponse([])

    def collection_exists(self, collection_name):
        return collection_name in self.collections

    def create_collection(self, collection_name, vectors_config):
        self.collections.add(collection_name)
        self.created_collections.append({
            "collection_name": collection_name,
            "vectors_config": vectors_config,
        })

    def upsert(self, collection_name, points):
        self.upserts.append({
            "collection_name": collection_name,
            "points": list(points),
        })

    def query_points(self, collection_name, query, query_filter, limit, with_payload):
        self.queries.append({
            "collection_name": collection_name,
            "query": list(query),
            "query_filter": query_filter,
            "limit": limit,
            "with_payload": with_payload,
        })
        return self.query_response

    def delete(self, collection_name, points_selector):
        self.deletes.append({
            "collection_name": collection_name,
            "points_selector": points_selector,
        })


class _BrokenQdrantClient:
    def collection_exists(self, collection_name):
        raise RuntimeError("local mode failed")
