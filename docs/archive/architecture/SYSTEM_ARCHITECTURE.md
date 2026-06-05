# 系统架构设计（当前基准）

> **版本**：v3.0
> **日期**：2026-04
> **状态**：Active — 本文档取代 `ARCHITECTURE_ENTERPRISE_BASELINE.md` 与旧版 `STRUCTURE_BASELINE.md`

---

## 1. 产品定位

知识岛（Knowledge Island）是一款本地优先的个人 AI 第二大脑桌面端应用。当前实现仍沿用 PySide6 本地桌面架构，第一阶段围绕个人项目、文档、笔记和代码资料逐步补齐：

- 导入本地项目、Markdown、TXT、代码和配置资料并建立本地知识库
- 围绕项目或文档进行问答
- Markdown / plain text / HTML 双格式数据模型
- 项目知识点与掌握证据提炼（规划中）
- 个人知识掌握地图和轻量知识图谱（规划中）

简历项目子弹点、JD 关键词匹配和面试脚本生成保留为后续输出能力，不作为知识岛第一阶段主线。

---

## 2. 技术选型

| 层次 | 技术 | 备注 |
|------|------|------|
| 桌面 UI | PySide6 6.7+（Qt6） | 主运行时 |
| LLM 推理 | Ollama（`qwen2.5:7b`） | 本地，无需 API Key |
| 文本 Embedding | Ollama（`nomic-embed-text`） | 本地，768 维向量 |
| 向量存储 | ChromaDB（本地持久化） | 默认；可换 FAISS |
| 关系存储 | SQLite（WAL 模式） | 元数据 / 任务 / 对话历史 |
| 测试 | pytest | |
| Python | 3.11+ | |

---

## 3. 分层架构

### 3.1 层次图

```
┌─────────────────────────────────────────────┐
│              desktop/（Qt 表现层）            │  ← 仅依赖 application
│  views / controllers / workers               │
├─────────────────────────────────────────────┤
│           application/（用例编排层）          │  ← 仅依赖 ports + domain
│  *UseCases  /  AppContainer                  │
├─────────────────────────────────────────────┤
│              ports/（抽象接口层）             │  ← 仅依赖 domain
│  IRetriever / IEmbedder / ILLMClient / ...   │
├──────────────────────┬──────────────────────┤
│    adapters/         │     domain/           │
│  （具体实现层）       │  （纯业务逻辑层）     │
│  ollama / chroma /   │  models / services    │
│  sqlite / keyword    │  零 I/O，零 Qt        │
├──────────────────────┴──────────────────────┤
│              config/（配置层）                │  ← 仅依赖 stdlib
│  AppSettings  /  load_settings()             │
└─────────────────────────────────────────────┘
```

### 3.2 依赖规则（严格单向）

```
config  ←  domain  ←  ports  ←  adapters
                             ←  application  ←  desktop
```

**违禁项：**
- domain 不得 import ports / adapters / application / desktop
- ports 不得 import adapters / application / desktop
- application 不得直接 import adapter 类（仅 `container.py` 例外）
- desktop 不得 import adapters

---

## 4. 目录结构

```
rag_system/
├── app.py                        # 唯一可执行入口
├── pyproject.toml                # 统一依赖声明
├── .env.example                  # 环境变量模板
│
├── src/
│   ├── config/
│   │   ├── settings.py           # AppSettings dataclass + load_settings()
│   │   ├── defaults.py           # 兜底默认值（无硬编码路径）
│   │   └── paths.py              # 从 AppSettings 派生的路径辅助函数
│   │
│   ├── domain/
│   │   ├── models/
│   │   │   ├── document.py       # Document（frozen dataclass）
│   │   │   ├── chunk.py          # Chunk（frozen dataclass）
│   │   │   ├── workspace.py      # Workspace（frozen dataclass）
│   │   │   ├── task.py           # Task, TaskStatus, TaskKind
│   │   │   └── conversation.py   # ConversationRecord
│   │   ├── services/
│   │   │   ├── chunker.py        # split_document() — 纯函数
│   │   │   ├── tagger.py         # infer_domain(), build_tags() — 纯函数
│   │   │   ├── jd_analyzer.py    # 覆盖率分析、Gap 建议 — 纯函数
│   │   │   └── metric_extractor.py # extract_metrics() — 纯函数
│   │   └── errors.py             # DomainError 异常层级
│   │
│   ├── ports/
│   │   ├── embedder.py           # IEmbedder（★ 新增）
│   │   ├── vector_store.py       # IVectorStore（★ 新增）
│   │   ├── retriever.py          # IRetriever
│   │   ├── llm_client.py         # ILLMClient
│   │   ├── document_store.py     # IDocumentStore
│   │   ├── chunk_store.py        # IChunkStore
│   │   ├── task_store.py         # ITaskStore
│   │   ├── workspace_store.py    # IWorkspaceStore
│   │   └── conversation_store.py # IConversationStore
│   │
│   ├── adapters/
│   │   ├── llm/
│   │   │   └── ollama_adapter.py          # OllamaAdapter(ILLMClient)
│   │   ├── embedding/                     # ★ 新增
│   │   │   ├── ollama_embedder.py         # OllamaEmbedder(IEmbedder)
│   │   │   └── dummy_embedder.py          # DummyEmbedder — 测试用
│   │   ├── vector_store/                  # ★ 新增
│   │   │   ├── chroma_store.py            # ChromaVectorStore(IVectorStore)
│   │   │   └── numpy_store.py             # NumpyVectorStore — 零依赖备选
│   │   ├── retrieval/
│   │   │   ├── vector_retriever.py        # VectorRetriever(IRetriever) ★ 新增
│   │   │   └── keyword_retriever.py       # KeywordRetriever(IRetriever) — 备选/离线
│   │   └── storage/
│   │       ├── db.py                      # SQLite 连接工厂（路径从 AppSettings 注入）
│   │       ├── schema.py                  # DDL + 迁移辅助
│   │       ├── sqlite_workspace_store.py
│   │       ├── sqlite_document_store.py
│   │       ├── sqlite_chunk_store.py
│   │       ├── sqlite_task_store.py
│   │       └── sqlite_conversation_store.py
│   │
│   ├── application/
│   │   ├── container.py            # AppContainer — 唯一组装 adapter 的地方
│   │   ├── workspace_usecases.py   # 工作区 CRUD
│   │   ├── ingestion_usecases.py   # 摄入 + 分块 + Embedding + 索引
│   │   ├── query_usecases.py       # 语义检索 + LLM 问答
│   │   ├── generation_usecases.py  # 简历 / JD 匹配 / 面试生成
│   │   ├── task_usecases.py        # 任务查询
│   │   └── settings_usecases.py   # 配置读写
│   │
│   └── desktop/
│       ├── bootstrap.py            # 启动检查 + 构建容器 + 首次运行引导
│       ├── workers/
│       │   ├── base_worker.py      # BaseWorker(QThread)：progress_updated / result_ready
│       │   ├── ingest_worker.py    # IngestWorker
│       │   ├── query_worker.py     # QueryWorker（支持流式 token 输出）
│       │   └── generate_worker.py  # GenerateWorker
│       ├── controllers/
│       │   ├── workspace_controller.py
│       │   ├── ingestion_controller.py
│       │   ├── query_controller.py
│       │   └── generation_controller.py
│       └── views/
│           ├── main_window.py      # 侧边栏导航 + QStackedWidget
│           ├── workspace_view.py
│           ├── ingestion_view.py
│           ├── query_view.py
│           ├── generation_view.py  # 标签页：简历 / JD 匹配 / 面试
│           ├── task_status_bar.py
│           ├── settings_view.py
│           └── onboarding_wizard.py
│
├── runtime/          # 运行时产物（gitignore）
│   ├── app.db
│   ├── vectors/      # ChromaDB 持久化目录
│   └── logs/
│
├── scripts/
│   ├── init_storage.py
│   ├── seed_demo_files.py
│   └── migration_gate_check.py
│
└── docs/
    └── architecture/
        ├── SYSTEM_ARCHITECTURE.md   ← 本文档（主文档）
        └── RAG_PIPELINE.md          ← RAG 全流程详解
```

---

## 5. 核心 Port 接口定义

### IEmbedder（★ 关键新增）

```python
# src/ports/embedder.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class EmbeddingResult:
    vector: List[float]   # 维度固定（取决于模型，nomic-embed-text = 768）
    model: str

class IEmbedder(ABC):
    @abstractmethod
    def embed(self, text: str) -> EmbeddingResult: ...

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]: ...

    @property
    @abstractmethod
    def dimension(self) -> int: ...
```

### IVectorStore（★ 关键新增）

```python
# src/ports/vector_store.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class VectorSearchResult:
    chunk_id: str
    score: float          # 余弦相似度，范围 [0, 1]

class IVectorStore(ABC):
    @abstractmethod
    def upsert(self, chunk_id: str, vector: List[float], metadata: dict) -> None: ...

    @abstractmethod
    def upsert_batch(self, items: List[tuple[str, List[float], dict]]) -> None: ...

    @abstractmethod
    def search(self, query_vector: List[float], top_k: int, workspace_id: str) -> List[VectorSearchResult]: ...

    @abstractmethod
    def delete_by_workspace(self, workspace_id: str) -> None: ...
```

### IRetriever（更新）

```python
# src/ports/retriever.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List
from src.domain.models.chunk import Chunk

@dataclass(frozen=True)
class RetrievalQuery:
    question: str
    workspace_id: str
    domains: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    top_k: int = 8

@dataclass(frozen=True)
class RetrievalResult:
    chunks: List[Chunk]
    scores: List[float]

class IRetriever(ABC):
    @abstractmethod
    def search(self, query: RetrievalQuery) -> RetrievalResult: ...

    # 索引生命周期由 IngestWorkspaceUseCase 管理
    @abstractmethod
    def index(self, chunks: List[Chunk]) -> None: ...

    @abstractmethod
    def clear(self, workspace_id: str) -> None: ...
```

### ILLMClient

```python
# src/ports/llm_client.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, List, Optional

@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    model: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048

@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str

class ILLMClient(ABC):
    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse: ...

    @abstractmethod
    def stream(self, request: LLMRequest) -> Iterator[str]: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def list_models(self) -> List[str]: ...
```

---

## 6. 配置设计

### AppSettings 字段

```python
@dataclass(frozen=True)
class AppSettings:
    # 知识库根目录（用户可配）
    kb_root: Path             # 环境变量 RAG_KB_ROOT，默认 ~/KnowledgeIslandKB

    # 运行时目录（相对项目）
    runtime_dir: Path         # RAG_RUNTIME_DIR，默认 ./runtime
    db_path: Path             # 固定为 runtime_dir/app.db
    vector_dir: Path          # 固定为 runtime_dir/vectors（ChromaDB 持久化）
    logs_dir: Path

    # Ollama
    ollama_host: str          # RAG_OLLAMA_HOST，默认 http://localhost:11434
    ollama_model: str         # RAG_OLLAMA_MODEL，默认 qwen2.5:7b
    embedding_model: str      # RAG_EMBEDDING_MODEL，默认 nomic-embed-text
    embedding_dim: int        # RAG_EMBEDDING_DIM，默认 768

    # 检索
    retriever_kind: str       # RAG_RETRIEVER_KIND："vector"（默认）| "keyword"
    chunk_size: int           # RAG_CHUNK_SIZE，默认 512
    chunk_overlap: int        # RAG_CHUNK_OVERLAP，默认 64
    retrieval_top_k: int      # RAG_TOP_K，默认 8

    # LLM 生成
    llm_temperature: float    # 默认 0.7
    llm_max_tokens: int       # 默认 2048
```

### 优先级（高 → 低）

```
OS 环境变量
  → %APPDATA%/KnowledgeIsland/.env   （用户通过 Settings UI 写入）
    → 项目根 .env                     （开发者覆盖，gitignore）
      → src/config/defaults.py        （兜底，无硬编码路径）
```

---

## 7. AppContainer — 组装规则

```python
# src/application/container.py

@dataclass
class AppContainer:
    settings: AppSettings
    # ports（接口类型）
    workspace_store: IWorkspaceStore
    document_store: IDocumentStore
    chunk_store: IChunkStore
    task_store: ITaskStore
    conversation_store: IConversationStore
    embedder: IEmbedder           # ★
    vector_store: IVectorStore    # ★
    retriever: IRetriever
    llm_client: ILLMClient

    @classmethod
    def build(cls, settings: AppSettings) -> "AppContainer":
        """
        唯一允许 import adapter 类的函数。
        所有其他模块通过构造函数注入接口，不直接 import adapter。
        """
        from src.adapters.storage.db import create_connection
        from src.adapters.storage.sqlite_workspace_store import SqliteWorkspaceStore
        from src.adapters.storage.sqlite_document_store import SqliteDocumentStore
        from src.adapters.storage.sqlite_chunk_store import SqliteChunkStore
        from src.adapters.storage.sqlite_task_store import SqliteTaskStore
        from src.adapters.storage.sqlite_conversation_store import SqliteConversationStore
        from src.adapters.embedding.ollama_embedder import OllamaEmbedder
        from src.adapters.vector_store.chroma_store import ChromaVectorStore
        from src.adapters.retrieval.vector_retriever import VectorRetriever
        from src.adapters.llm.ollama_adapter import OllamaAdapter

        conn = create_connection(settings.db_path)
        embedder = OllamaEmbedder(host=settings.ollama_host,
                                   model=settings.embedding_model)
        vector_store = ChromaVectorStore(persist_dir=settings.vector_dir)
        retriever = VectorRetriever(embedder=embedder,
                                     vector_store=vector_store,
                                     chunk_store=...,     # 注入后填充
                                     top_k=settings.retrieval_top_k)
        ...
        return cls(settings=settings, ...)
```

---

## 8. Qt 桌面架构

### 窗口层级

```
QApplication
└── MainWindow (QMainWindow)
    ├── SideNav (QListWidget, 200px)
    │   ├── 工作区
    │   ├── 知识库
    │   ├── 问答
    │   ├── 生成
    │   └── 设置
    ├── ContentArea (QStackedWidget)
    │   ├── [0] WorkspaceView
    │   ├── [1] IngestionView
    │   ├── [2] QueryView
    │   ├── [3] GenerationView（标签页）
    │   └── [4] SettingsView
    └── TaskStatusBar（进度 + 消息）

对话框（按需弹出）：
    ├── OnboardingWizard（首次运行）
    └── WorkspaceCreateDialog
```

### QThread Worker 模式

```python
# src/desktop/workers/base_worker.py
class BaseWorker(QThread):
    progress_updated = Signal(int, str)   # (percent, message)
    result_ready     = Signal(object)     # WorkerResult
    error_occurred   = Signal(str)

    def run(self) -> None:
        try:
            data = self._execute()
            self.result_ready.emit(WorkerResult(success=True, data=data))
        except Exception as exc:
            self.error_occurred.emit(str(exc))
            self.result_ready.emit(WorkerResult(success=False, error=str(exc)))

    def _execute(self): raise NotImplementedError
```

### 信号流

```
用户点击  →  View.signal  →  Controller.handle()
  →  Worker.start()（QThread）
      →  UseCase.execute()（非主线程）
          →  Port 调用（I/O / Embedding / LLM）
          →  Worker.progress_updated.emit()
      →  Worker.result_ready.emit()
  →  Controller slot  →  View slot（主线程更新 UI）
```

**核心约束：** LLM 调用、Embedding、文件 I/O、数据库写入，一律在 Worker 线程内执行，严禁阻塞主线程。

---

## 9. 旧代码迁移映射

| 旧路径 | 新路径 | 操作 |
|--------|--------|------|
| `backend/app/config.py` | 废弃 | 删除（硬编码 F: 盘） |
| `backend/core/config.py` | `src/config/settings.py` | 重写 |
| `backend/app/schemas/` | `src/domain/models/` | 迁移，加 `frozen=True` |
| `backend/app/modules/preprocess/` | `src/domain/services/` | 迁移，去除路径依赖 |
| `backend/infra/model/llm/ollama_client.py` | `src/adapters/llm/ollama_adapter.py` | 重写，实现 ILLMClient |
| `backend/infra/storage/db/sqlite.py` | `src/adapters/storage/db.py` | 重写，路径改参数注入 |
| `backend/app/services/retrieval_service.py` | `src/adapters/retrieval/keyword_retriever.py` | 实现 IRetriever |
| `backend/app/modules/*/service.py` | `src/adapters/storage/sqlite_*_store.py` + `src/application/*_usecases.py` | 拆分持久化与编排 |
| `desktop/ui/main_window.py` | `src/desktop/views/main_window.py` | 重写完整布局 |
| `desktop/app/bootstrap.py` | `src/desktop/bootstrap.py` | 扩展，注入 AppContainer |
| `backend/app/main.py` | 废弃 | 删除（FastAPI 遗留） |
| `desktop/services/backend_client.py` | 废弃 | 删除（永远返回 True 的 stub） |
| `desktop/app/state.py` | 废弃 | 由 AppContainer 替代 |

**新增（无对应旧文件）：**
- `src/ports/embedder.py`
- `src/ports/vector_store.py`
- `src/adapters/embedding/ollama_embedder.py`
- `src/adapters/vector_store/chroma_store.py`
- `src/adapters/retrieval/vector_retriever.py`
- `src/application/container.py`

---

## 10. 实施顺序

```
第 1 步  src/config/settings.py          消灭硬编码路径
第 2 步  src/domain/models/ + errors.py  稳定数据模型
第 3 步  src/ports/                      定义所有接口契约
第 4 步  src/adapters/storage/           SQLite 各 store
第 5 步  src/adapters/llm/              OllamaAdapter
第 6 步  src/adapters/embedding/        OllamaEmbedder   ← 新
第 7 步  src/adapters/vector_store/     ChromaVectorStore ← 新
第 8 步  src/adapters/retrieval/        VectorRetriever   ← 新
第 9 步  src/application/container.py   组装容器
第 10 步 src/application/*_usecases.py  实现用例（含 Embedding 调用）
第 11 步 src/desktop/workers/           QThread 基础设施
第 12 步 src/desktop/views/ + controllers 完整 UI
```
