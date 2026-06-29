"""Fallback configuration values for the Web/Tauri runtime."""
from __future__ import annotations

KB_ROOT = "~/KnowledgeIslandKB"

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIM = "768"

RETRIEVER_KIND = "vector"
CHUNK_SIZE = "512"
CHUNK_OVERLAP = "64"
RETRIEVAL_TOP_K = "8"

LLM_TEMPERATURE = "0.7"
LLM_MAX_TOKENS = "2048"

LLM_PROVIDER = "ollama"
LLM_API_BASE = "https://api.deepseek.com/v1"
LLM_API_KEY = ""
LLM_API_MODEL = "deepseek-chat"

EMBED_PROVIDER = "ollama"
EMBED_API_BASE = LLM_API_BASE
EMBED_API_KEY = ""
EMBED_API_MODEL = "text-embedding-3-small"
