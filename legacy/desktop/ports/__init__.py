from legacy.desktop.ports.embedder import IEmbedder, EmbeddingResult
from legacy.desktop.ports.vector_store import IVectorStore, VectorSearchResult
from legacy.desktop.ports.retriever import IRetriever, RetrievalQuery, RetrievalResult
from legacy.desktop.ports.llm_client import ILLMClient, LLMRequest, LLMResponse
from legacy.desktop.ports.document_store import IDocumentStore
from legacy.desktop.ports.chunk_store import IChunkStore
from legacy.desktop.ports.source_store import ISourceStore
from legacy.desktop.ports.tag_store import ITagStore, IDocumentTagStore
from legacy.desktop.ports.task_store import ITaskStore
from legacy.desktop.ports.workspace_store import IWorkspaceStore
from legacy.desktop.ports.conversation_store import IConversationStore
from legacy.desktop.ports.knowledge_mastery_store import IKnowledgeMasteryStore
from legacy.desktop.ports.graph_store import IGraphStore

__all__ = [
    "IEmbedder", "EmbeddingResult",
    "IVectorStore", "VectorSearchResult",
    "IRetriever", "RetrievalQuery", "RetrievalResult",
    "ILLMClient", "LLMRequest", "LLMResponse",
    "IDocumentStore",
    "IChunkStore",
    "ITaskStore",
    "ISourceStore",
    "ITagStore",
    "IDocumentTagStore",
    "IWorkspaceStore",
    "IConversationStore",
    "IKnowledgeMasteryStore",
    "IGraphStore",
]
