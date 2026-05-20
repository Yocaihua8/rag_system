# 架构设计说明

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-16
> Scope：应用结构与端口适配边界
> Related：`requirements/functional-modules.md`、`design/system-design-overview.md`

## 1. 架构结论

系统采用六边形思路下的分层约束。`src/domain` 纯模型与业务规则，不依赖 I/O；`ports` 定义抽象；`adapters` 实现外部能力；`application` 负责用例编排；`desktop` 仅处理交互与线程模型。

| 层 | 作用 | 当前路径 |
|----|------|----------|
| 表现层 | 交互、参数组织、状态更新 | `src/desktop` |
| 应用层 | 流程编排、事务边界 | `src/application` |
| 端口层 | 能力契约（检索、嵌入、LLM、存储） | `src/ports` |
| 适配器层 | 技术实现（SQLite、Ollama、Chroma 等） | `src/adapters` |
| 领域层 | 不可变模型与核心约束 | `src/domain` |
| 配置层 | 配置优先级与默认值 | `src/config` |

## 2. 端口与适配器映射

| 端口 | 实现 | 调用方 |
|------|------|--------|
| `IWorkspaceStore` | `SqliteWorkspaceStore` | `workspace_usecases`, `query` 与 `ingest` 用例 |
| `IDocumentStore` | `SqliteDocumentStore` | `ingestion_usecases`, `project_...` 用例 |
| `IChunkStore` | `SqliteChunkStore` | `query_usecases`, `knowledge_mastery_usecases` |
| `IRetriever` | `VectorRetriever` / `KeywordRetriever` | `query_usecases` |
| `IEmbedder` | `OllamaEmbedder` / `DummyEmbedder` | `application` 及 `vector store` |
| `IVectorStore` | `ChromaVectorStore` / `NumpyVectorStore` | `VectorRetriever` |
| `ILLMClient` | `OllamaAdapter` / `OpenAICompatAdapter` | `generation_usecases`, `query_usecases` |

## 3. 依赖规则

- 依赖方向为：配置 -> 领域 -> 端口 -> 适配器 -> 应用 -> 表现。
- 应用层不直接 import adapter，统一在 `AppContainer` 组装。
- `desktop` 不包含数据库模型拼装逻辑。

## 4. 当前偏差说明

- 兼容层 `Workspace` 与新语义 `Project` 并存，数据库层保留双套关系，避免一次性破坏。
- 文档内容仍保留 legacy 字段（如 `content/domain/tags`）用于过渡。
