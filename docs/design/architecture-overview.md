# 架构设计说明

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-22
> Scope：应用结构与端口适配边界
> Related：`requirements/functional-modules.md`、`design/system-design-overview.md`

## 1. 架构结论

当前默认交付形态是本地 Web MVP，运行链路为 `app.py` -> `webapp.server.run_server()` -> `webapp.api.dispatch()` -> `webapp/*` 业务模块。旧 PySide6 桌面端仍保留六边形思路下的分层约束，作为 legacy 参考和后续迁移来源。

新任务默认优先维护 Web MVP；除非任务明确要求迁移 legacy，否则不要在同一轮里同时改 `webapp/` 和 `src/desktop/`。

### Web MVP 当前结构

| 层 | 作用 | 当前路径 |
|----|------|----------|
| 服务入口 | 启动本机 HTTP 服务与静态文件服务 | `app.py`、`webapp/server.py` |
| API 层 | 路由分发、请求校验、响应组装 | `webapp/api.py` |
| 存储层 | SQLite schema 与读写 | `webapp/storage.py` |
| 入库处理 | 本地目录、浏览器上传、文本笔记、文档处理 | `webapp/ingestion.py`、`webapp/upload_import.py`、`webapp/source_import.py`、`webapp/document_processing.py` |
| 检索与回答 | keyword + vector 混合召回、来源质量、本地回答 | `webapp/search.py`、`webapp/answers.py` |
| 工具与设置 | Agent 只读工具、LLM/Embedding 设置 | `webapp/agent_tools.py`、`webapp/config.py` |
| Web UI | 原生 HTML/CSS/JavaScript 交互 | `webapp/static/` |

### legacy 分层结构

| 层 | 作用 | 当前路径 |
|----|------|----------|
| 表现层 | 交互、参数组织、状态更新 | `src/desktop` |
| 应用层 | 流程编排、事务边界 | `src/application` |
| 端口层 | 能力契约（检索、嵌入、LLM、存储） | `src/ports` |
| 适配器层 | 技术实现（SQLite、Ollama、Chroma 等） | `src/adapters` |
| 领域层 | 不可变模型与核心约束 | `src/domain` |
| 配置层 | 配置优先级与默认值 | `src/config` |

## 2. 端口与适配器映射

### Web MVP 模块映射

| 能力 | 实现 | 调用方 |
|------|------|--------|
| HTTP 服务 | `webapp.server.run_server` | `app.py` |
| API 分发 | `webapp.api.dispatch` | `webapp.server` |
| SQLite 存储 | `KnowledgeStore` | `webapp.api`、导入/检索/工具模块 |
| 本地目录导入 | `import_project_documents` | `POST /api/import` |
| 浏览器上传导入 | `import_uploaded_files` | `POST /api/import/upload` |
| 文本笔记导入 | `build_note_document` | `POST /api/import/note` |
| 检索 | `search_documents`、`build_source_quality` | `/api/search`、`/api/search/debug`、`/api/answer`、只读工具 |
| 回答生成 | `build_local_answer`、OpenAI-compatible Chat Completions 调用 | `POST /api/answer` |
| Agent 只读工具 | `run_agent_tool` | `POST /api/agent/tools/run` |

### legacy 端口映射

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

- Web MVP：`api.py` 负责路由分发，不直接写 SQLite；SQLite 读写集中在 `storage.py`；导入、检索、回答和工具逻辑分别放在独立模块。
- Web MVP 不通过 `src/ports` 组装运行，避免把 legacy 六边形约束误套到当前轻量 Web 入口；需要迁移时另开任务。
- legacy：依赖方向为配置 -> 领域 -> 端口 -> 适配器 -> 应用 -> 表现；应用层不直接 import adapter，统一在 `AppContainer` 组装；`desktop` 不包含数据库模型拼装逻辑。

## 4. 当前偏差说明

- 兼容层 `Workspace` 与新语义 `Project` 并存，legacy 数据库层保留双套关系，避免一次性破坏。
- 文档内容仍保留 legacy 字段（如 `content/domain/tags`）用于过渡。
- Web MVP 使用独立轻量表承载当前交付能力，包括 `projects`、`documents`、`document_chunks`、`chunk_vectors`、`chat_messages`、`agent_tool_runs` 和 `retrieval_reviews`。
