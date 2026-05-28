"""
兜底默认值。
所有值均为字符串，由 settings.py 负责类型转换。
不包含任何硬编码的绝对路径。
"""
from __future__ import annotations

# 知识库根目录（相对用户主目录，运行时展开为绝对路径）
KB_ROOT = "~/KnowledgeIslandKB"

# Ollama
OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIM = "768"

# 检索
RETRIEVER_KIND = "vector"   # "vector" | "keyword"
CHUNK_SIZE = "512"
CHUNK_OVERLAP = "64"
RETRIEVAL_TOP_K = "8"

# LLM 生成
LLM_TEMPERATURE = "0.7"
LLM_MAX_TOKENS = "2048"

# LLM 提供商（"ollama" | "api"）
LLM_PROVIDER = "ollama"
LLM_API_BASE = "https://api.deepseek.com/v1"
LLM_API_KEY = ""            # 优先由 OS 环境变量 RAG_LLM_API_KEY 提供
LLM_API_MODEL = "deepseek-chat"

# Embedding 提供商（"ollama" | "none" | "api"）
EMBED_PROVIDER = "ollama"
EMBED_API_BASE = LLM_API_BASE
EMBED_API_KEY = ""
EMBED_API_MODEL = "text-embedding-3-small"
