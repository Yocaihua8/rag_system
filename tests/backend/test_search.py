from pathlib import Path

from backend.knowledge_island.chunking import split_into_chunks
from backend.knowledge_island.import_rules import MAX_TEXT_FILE_BYTES
from backend.knowledge_island.ingestion import import_directory
from backend.knowledge_island.search import search_documents
from backend.knowledge_island.storage import KnowledgeStore


def test_import_directory_indexes_supported_text_files(tmp_path: Path):
    project_dir = tmp_path / "demo"
    project_dir.mkdir()
    (project_dir / "README.md").write_text("# Demo\n\nPython SQLite local-first app", encoding="utf-8")
    (project_dir / "image.png").write_bytes(b"not text")

    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", project_dir)

    result = import_directory(store, project.id, project_dir)

    assert result.imported == 1
    assert result.skipped == 0
    documents = store.list_documents(project.id)
    assert [doc.relative_path for doc in documents] == ["README.md"]


def test_import_directory_reports_reimport_changes_and_removes_missing_files(tmp_path: Path):
    project_dir = tmp_path / "demo"
    project_dir.mkdir()
    (project_dir / "a.md").write_text("Alpha", encoding="utf-8")
    (project_dir / "b.md").write_text("Beta", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", project_dir)

    first = import_directory(store, project.id, project_dir)
    (project_dir / "a.md").write_text("Alpha changed", encoding="utf-8")
    (project_dir / "b.md").unlink()
    (project_dir / "c.md").write_text("Gamma", encoding="utf-8")

    second = import_directory(store, project.id, project_dir)

    assert first.created == 2
    assert second.imported == 2
    assert second.created == 1
    assert second.updated == 1
    assert second.deleted == 1
    assert second.unchanged == 0
    assert [doc.relative_path for doc in store.list_documents(project.id)] == ["a.md", "c.md"]
    assert [chunk.document.relative_path for chunk in store.list_chunks(project.id)] == ["a.md", "c.md"]


def test_import_directory_reports_unchanged_files_on_second_import(tmp_path: Path):
    project_dir = tmp_path / "demo"
    project_dir.mkdir()
    (project_dir / "README.md").write_text("Alpha", encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", project_dir)

    first = import_directory(store, project.id, project_dir)
    second = import_directory(store, project.id, project_dir)

    assert first.created == 1
    assert second.imported == 1
    assert second.created == 0
    assert second.updated == 0
    assert second.unchanged == 1
    assert second.deleted == 0
    assert [doc.relative_path for doc in store.list_documents(project.id)] == ["README.md"]


def test_import_directory_skips_dependency_cache_and_vcs_directories(tmp_path: Path):
    project_dir = tmp_path / "demo"
    project_dir.mkdir()
    (project_dir / "docs").mkdir()
    (project_dir / "docs" / "keep.md").write_text("Keep this", encoding="utf-8")

    for ignored_dir in [
        ".agents",
        ".claude",
        ".codex",
        ".git",
        ".idea",
        ".venv",
        ".vscode",
        "node_modules",
        "__pycache__",
    ]:
        nested = project_dir / ignored_dir
        nested.mkdir()
        (nested / "ignored.md").write_text("Do not import", encoding="utf-8")

    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", project_dir)

    result = import_directory(store, project.id, project_dir)

    assert result.imported == 1
    assert result.skipped == 0
    assert [doc.relative_path for doc in store.list_documents(project.id)] == ["docs/keep.md"]


def test_import_directory_skips_text_files_over_size_limit(tmp_path: Path):
    project_dir = tmp_path / "demo"
    project_dir.mkdir()
    (project_dir / "small.md").write_text("Small content", encoding="utf-8")
    (project_dir / "huge.md").write_text("x" * (MAX_TEXT_FILE_BYTES + 1), encoding="utf-8")
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", project_dir)

    result = import_directory(store, project.id, project_dir)

    assert result.imported == 1
    assert result.skipped == 1
    assert result.skipped_details == [{"path": "huge.md", "reason": "file too large"}]
    assert [doc.relative_path for doc in store.list_documents(project.id)] == ["small.md"]


def test_search_documents_ranks_matching_documents_first(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", tmp_path)
    store.upsert_document(project.id, tmp_path / "api.md", "api.md", "FastAPI route and request handler")
    store.upsert_document(project.id, tmp_path / "ui.md", "ui.md", "PySide desktop widget")

    hits = search_documents(store, project.id, "request api", limit=3)

    assert hits[0].document.relative_path == "api.md"
    assert hits[0].score > hits[-1].score
    assert "request handler" in hits[0].snippet


def test_search_documents_matches_chinese_terms_with_keyword_only(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", tmp_path)
    store.upsert_document(project.id, tmp_path / "entry.md", "entry.md", "默认入口是 app.py，用于启动本地 Web MVP。")
    store.upsert_document(project.id, tmp_path / "model.md", "model.md", "模型设置页面用于保存 API Key。")

    hits = search_documents(store, project.id, "默认入口", limit=2, use_keyword=True, use_vector=False)

    assert hits[0].document.relative_path == "entry.md"
    assert hits[0].keyword_score > 0
    assert hits[0].vector_score == 0
    assert "默认入口" in hits[0].snippet


def test_search_uses_bm25_so_repeated_common_terms_do_not_dominate(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", tmp_path)
    store.upsert_document(
        project.id,
        tmp_path / "common.md",
        "common.md",
        "API " * 30 + "route handler request",
    )
    store.upsert_document(
        project.id,
        tmp_path / "deepseek.md",
        "deepseek.md",
        "DeepSeek API key setup and model configuration",
    )

    hits = search_documents(
        store,
        project.id,
        "DeepSeek API",
        limit=2,
        use_keyword=True,
        use_vector=False,
    )

    assert hits[0].document.relative_path == "deepseek.md"
    assert hits[0].keyword_score > hits[1].keyword_score


def test_upsert_document_builds_retrievable_chunks(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", tmp_path)
    content = "\n\n".join(
        [
            "安装步骤：先启动 Docker Desktop，然后运行启动脚本。",
            "模型配置：打开设置页，填写 DeepSeek API Key。",
            "检索说明：导入后会生成分块，用于 RAG 召回。",
        ]
    )

    store.upsert_document(project.id, tmp_path / "guide.md", "guide.md", content)
    chunks = store.list_chunks(project.id)

    assert len(chunks) >= 2
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert all(chunk.document.relative_path == "guide.md" for chunk in chunks)
    assert "DeepSeek API Key" in " ".join(chunk.content for chunk in chunks)


def test_markdown_chunking_keeps_fenced_code_block_together():
    markdown = (
        "## 示例\n\n"
        "```python\n"
        "print('hello')\n"
        "print('world')\n"
        "```\n\n"
        "结论段落"
    )

    chunks = split_into_chunks(markdown, max_chars=120, overlap_chars=10)

    assert chunks == [
        "## 示例",
        "```python\nprint('hello')\nprint('world')\n```",
        "结论段落",
    ]


def test_search_returns_best_matching_chunk_not_entire_document(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", tmp_path)
    content = "\n\n".join(
        [
            "安装说明：启动 Docker 后打开浏览器。",
            "模型设置：在设置页填写 DeepSeek API Key，并点击测试连接。",
            "导入说明：选择文件夹导入后查看来源。",
        ]
    )
    store.upsert_document(project.id, tmp_path / "guide.md", "guide.md", content)

    hits = search_documents(store, project.id, "DeepSeek API Key", limit=1)
    body = hits[0].to_dict()

    assert body["path"] == "guide.md"
    assert body["chunk_index"] == 1
    assert "模型设置" in body["snippet"]
    assert "安装说明" not in body["snippet"]


def test_upsert_document_persists_vectors_for_chunks(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", tmp_path)

    store.upsert_document(
        project.id,
        tmp_path / "guide.md",
        "guide.md",
        "模型设置：填写 DeepSeek API Key。\n\n导入说明：选择文件夹导入。",
    )

    assert store.count_chunk_vectors(project.id) == len(store.list_chunks(project.id))


def test_search_returns_hybrid_scores_for_vector_retrieval(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "app.db")
    project = store.create_project("Demo", tmp_path)
    store.upsert_document(
        project.id,
        tmp_path / "model.md",
        "model.md",
        "模型设置：填写 DeepSeek API Key，并点击测试连接。",
    )
    store.upsert_document(
        project.id,
        tmp_path / "docker.md",
        "docker.md",
        "Docker 启动：运行一键脚本后打开浏览器。",
    )

    hits = search_documents(store, project.id, "模型 API Key", limit=2)
    body = hits[0].to_dict()

    assert body["path"] == "model.md"
    assert body["retrieval"] == "hybrid"
    assert body["keyword_score"] > 0
    assert body["vector_score"] > 0
    assert body["score"] == body["keyword_score"] + body["vector_score"]


def test_upsert_document_can_use_api_embedding_client(tmp_path: Path):
    embedding_client = FakeEmbeddingClient()
    store = KnowledgeStore(tmp_path / "app.db", embedding_client=embedding_client)
    project = store.create_project("Demo", tmp_path)

    store.upsert_document(
        project.id,
        tmp_path / "model.md",
        "model.md",
        "模型设置：填写 DeepSeek API Key。\n\n导入说明：选择文件夹导入。",
    )

    records = store.list_chunk_vector_records(project.id)
    assert embedding_client.calls == [["模型设置：填写 DeepSeek API Key。", "导入说明：选择文件夹导入。"]]
    assert {record["provider"] for record in records} == {"api"}
    assert {record["model"] for record in records} == {"fake-embedding"}


def test_search_can_use_api_embedding_client_for_query_vector(tmp_path: Path):
    embedding_client = FakeEmbeddingClient()
    store = KnowledgeStore(tmp_path / "app.db", embedding_client=embedding_client)
    project = store.create_project("Demo", tmp_path)
    store.upsert_document(
        project.id,
        tmp_path / "model.md",
        "model.md",
        "模型设置：填写 DeepSeek API Key，并点击测试连接。",
    )

    hits = search_documents(store, project.id, "DeepSeek API Key", limit=1, embedding_client=embedding_client)
    body = hits[0].to_dict()

    assert body["retrieval"] == "hybrid"
    assert body["vector_provider"] == "api"
    assert body["vector_model"] == "fake-embedding"
    assert body["vector_score"] > 0


class FakeEmbeddingClient:
    provider = "api"
    model = "fake-embedding"

    def __init__(self):
        self.calls = []

    def embed_texts(self, texts):
        self.calls.append(list(texts))
        vectors = []
        for text in texts:
            lowered = text.lower()
            vectors.append({
                "deepseek": 1.0 if "deepseek" in lowered else 0.0,
                "api": 1.0 if "api" in lowered else 0.0,
                "key": 1.0 if "key" in lowered else 0.0,
            })
        return vectors
