"""
AppContainer — 依赖组装根（Composition Root）。

规则：
  - 这是整个代码库中唯一允许直接 import adapter 类的模块。
  - 所有其他模块（usecases / desktop）只持有 Port 接口，不感知具体实现。
  - build() 只在 bootstrap.py 中调用一次，得到的实例贯穿整个应用生命周期。
"""
from __future__ import annotations

from dataclasses import dataclass

from legacy.desktop.config.settings import AppSettings
from legacy.desktop.config.paths import ensure_runtime_dirs
from legacy.desktop.ports.chunk_store import IChunkStore
from legacy.desktop.ports.conversation_store import IConversationStore
from legacy.desktop.ports.document_store import IDocumentStore
from legacy.desktop.ports.knowledge_mastery_store import IKnowledgeMasteryStore
from legacy.desktop.ports.graph_store import IGraphStore
from legacy.desktop.ports.tag_store import IDocumentTagStore
from legacy.desktop.ports.source_store import ISourceStore
from legacy.desktop.ports.embedder import IEmbedder
from legacy.desktop.ports.llm_client import ILLMClient
from legacy.desktop.ports.tag_store import ITagStore
from legacy.desktop.ports.project_knowledge_store import IProjectKnowledgeStore
from legacy.desktop.ports.retriever import IRetriever
from legacy.desktop.ports.task_store import ITaskStore
from legacy.desktop.ports.vector_store import IVectorStore
from legacy.desktop.ports.workspace_store import IWorkspaceStore


@dataclass
class AppContainer:
    settings: AppSettings

    # 存储端口
    workspace_store: IWorkspaceStore
    document_store: IDocumentStore
    chunk_store: IChunkStore
    task_store: ITaskStore
    conversation_store: IConversationStore
    project_knowledge_store: IProjectKnowledgeStore
    mastery_store: IKnowledgeMasteryStore
    source_store: ISourceStore
    tag_store: ITagStore
    document_tag_store: IDocumentTagStore
    graph_store: IGraphStore

    # 推理端口
    embedder: IEmbedder
    vector_store: IVectorStore
    retriever: IRetriever
    llm_client: ILLMClient

    # ------------------------------------------------------------------ #
    # 工厂方法
    # ------------------------------------------------------------------ #

    @classmethod
    def build(cls, settings: AppSettings) -> "AppContainer":
        """
        唯一允许 import adapter 类的函数。
        根据 settings.retriever_kind 自动选择检索实现。
        """
        # ── 延迟导入，避免在 tests 中意外拉起所有依赖 ──
        from legacy.desktop.adapters.storage.db import create_connection, init_schema
        from legacy.desktop.adapters.storage.sqlite_workspace_store import SqliteWorkspaceStore
        from legacy.desktop.adapters.storage.sqlite_document_store import SqliteDocumentStore
        from legacy.desktop.adapters.storage.sqlite_chunk_store import SqliteChunkStore
        from legacy.desktop.adapters.storage.sqlite_task_store import SqliteTaskStore
        from legacy.desktop.adapters.storage.sqlite_conversation_store import SqliteConversationStore
        from legacy.desktop.adapters.storage.sqlite_project_knowledge_store import SqliteProjectKnowledgeStore
        from legacy.desktop.adapters.storage.sqlite_source_store import SqliteSourceStore
        from legacy.desktop.adapters.storage.sqlite_tag_store import SqliteTagStore, SqliteDocumentTagStore
        from legacy.desktop.adapters.storage.sqlite_knowledge_mastery_store import SqliteKnowledgeMasteryStore
        from legacy.desktop.adapters.storage.sqlite_graph_store import SqliteGraphStore
        from legacy.desktop.adapters.llm.ollama_adapter import OllamaAdapter
        from legacy.desktop.adapters.llm.openai_compat_adapter import OpenAICompatAdapter
        from legacy.desktop.adapters.embedding.ollama_embedder import OllamaEmbedder, DummyEmbedder
        from legacy.desktop.adapters.vector_store.chroma_store import ChromaVectorStore
        from legacy.desktop.adapters.vector_store.numpy_store import NumpyVectorStore
        from legacy.desktop.adapters.retrieval.vector_retriever import VectorRetriever
        from legacy.desktop.adapters.retrieval.keyword_retriever import KeywordRetriever

        # 运行时目录
        ensure_runtime_dirs(settings)

        # SQLite
        conn = create_connection(settings.db_path)
        init_schema(conn)

        ws_store = SqliteWorkspaceStore(conn)
        doc_store = SqliteDocumentStore(conn)
        chunk_store = SqliteChunkStore(conn)
        task_store = SqliteTaskStore(conn)
        conv_store = SqliteConversationStore(conn)
        project_knowledge_store = SqliteProjectKnowledgeStore(conn)
        mastery_store = SqliteKnowledgeMasteryStore(conn)
        source_store = SqliteSourceStore(conn)
        tag_store = SqliteTagStore(conn)
        document_tag_store = SqliteDocumentTagStore(conn)
        graph_store = SqliteGraphStore(conn)

        # ── LLM 路由 ──────────────────────────────────────────────────────
        # 优先级：api 模式（有 key）> ollama
        if settings.llm_provider == "api" and settings.llm_api_key:
            llm_client: ILLMClient = OpenAICompatAdapter(
                api_key=settings.llm_api_key,
                base_url=settings.llm_api_base,
                model=settings.llm_api_model,
            )
        else:
            llm_client = OllamaAdapter(host=settings.ollama_host)

        # ── Embedding + 向量库 + 检索器 路由 ─────────────────────────────
        # embed_provider="none" 或 retriever_kind="keyword" 均降级为关键词检索
        use_vector = (
            settings.embed_provider == "ollama"
            and settings.retriever_kind == "vector"
        )
        if use_vector:
            embedder: IEmbedder = OllamaEmbedder(
                host=settings.ollama_host,
                model=settings.embedding_model,
                dimension=settings.embedding_dim,
            )
            vector_store: IVectorStore = ChromaVectorStore(
                persist_dir=settings.vector_dir
            )
            retriever: IRetriever = VectorRetriever(
                embedder=embedder,
                vector_store=vector_store,
                chunk_store=chunk_store,
            )
        else:
            embedder = DummyEmbedder(dimension=settings.embedding_dim)
            vector_store = NumpyVectorStore()
            retriever = KeywordRetriever()

        # 启动时从数据库热载索引（keyword 模式需要）
        if not use_vector:
            _warm_up_retriever(retriever, chunk_store, ws_store)

        return cls(
            settings=settings,
            workspace_store=ws_store,
            document_store=doc_store,
            chunk_store=chunk_store,
            task_store=task_store,
            conversation_store=conv_store,
            project_knowledge_store=project_knowledge_store,
            mastery_store=mastery_store,
            source_store=source_store,
            tag_store=tag_store,
            document_tag_store=document_tag_store,
            graph_store=graph_store,
            embedder=embedder,
            vector_store=vector_store,
            retriever=retriever,
            llm_client=llm_client,
        )

    @classmethod
    def build_for_testing(cls, settings: AppSettings) -> "AppContainer":
        """
        测试专用工厂：使用内存 SQLite + DummyEmbedder + NumpyVectorStore。
        不依赖 Ollama 服务，无文件副作用。
        """
        from legacy.desktop.adapters.storage.db import create_connection, init_schema
        from legacy.desktop.adapters.storage.sqlite_workspace_store import SqliteWorkspaceStore
        from legacy.desktop.adapters.storage.sqlite_document_store import SqliteDocumentStore
        from legacy.desktop.adapters.storage.sqlite_chunk_store import SqliteChunkStore
        from legacy.desktop.adapters.storage.sqlite_task_store import SqliteTaskStore
        from legacy.desktop.adapters.storage.sqlite_conversation_store import SqliteConversationStore
        from legacy.desktop.adapters.storage.sqlite_project_knowledge_store import SqliteProjectKnowledgeStore
        from legacy.desktop.adapters.storage.sqlite_source_store import SqliteSourceStore
        from legacy.desktop.adapters.storage.sqlite_tag_store import SqliteTagStore, SqliteDocumentTagStore
        from legacy.desktop.adapters.storage.sqlite_knowledge_mastery_store import SqliteKnowledgeMasteryStore
        from legacy.desktop.adapters.storage.sqlite_graph_store import SqliteGraphStore
        from legacy.desktop.adapters.embedding.ollama_embedder import DummyEmbedder
        from legacy.desktop.adapters.vector_store.numpy_store import NumpyVectorStore
        from legacy.desktop.adapters.retrieval.keyword_retriever import KeywordRetriever

        class _FakeLLM:
            def generate(self, req):
                from legacy.desktop.ports.llm_client import LLMResponse
                return LLMResponse(content="[test answer]", model="fake")
            def stream(self, req):
                yield "[test answer]"
            def is_available(self): return True
            def list_models(self): return ["fake"]

        conn = create_connection(settings.db_path)
        init_schema(conn)

        embedder = DummyEmbedder(dimension=settings.embedding_dim)
        vector_store = NumpyVectorStore()
        chunk_store = SqliteChunkStore(conn)

        return cls(
            settings=settings,
            workspace_store=SqliteWorkspaceStore(conn),
            document_store=SqliteDocumentStore(conn),
            chunk_store=chunk_store,
            task_store=SqliteTaskStore(conn),
            conversation_store=SqliteConversationStore(conn),
            project_knowledge_store=SqliteProjectKnowledgeStore(conn),
            mastery_store=SqliteKnowledgeMasteryStore(conn),
            source_store=SqliteSourceStore(conn),
            tag_store=SqliteTagStore(conn),
            document_tag_store=SqliteDocumentTagStore(conn),
            graph_store=SqliteGraphStore(conn),
            embedder=embedder,
            vector_store=vector_store,
            retriever=KeywordRetriever(),
            llm_client=_FakeLLM(),
        )


def _warm_up_retriever(retriever: IRetriever, chunk_store: IChunkStore, ws_store: IWorkspaceStore) -> None:
    """启动时将数据库中的 chunks 载入内存检索索引（keyword 模式专用）。"""
    try:
        workspaces = ws_store.list_all()
        for ws in workspaces:
            chunks = chunk_store.list_by_workspace(ws.id)
            if chunks:
                retriever.index(chunks)
    except Exception:
        pass  # 启动失败不阻断 UI
