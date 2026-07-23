# 架构设计说明

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-23
> Scope：Knowledge Island 1.x 当前实现与 2.0 已接受目标架构
> Related：docs/design/system-design-overview.md, docs/design/database-design.md, docs/design/api-spec.md, docs/adr/ADR-008-project-knowledge-coach-v2.md, docs/adr/ADR-009-obsidian-plugin-bridge.md

> 阅读边界：§ 1～§ 8 描述兼容保留的 1.x 能力；§ 9 描述 Knowledge Island 2.0 的目标架构与分片落地状态。只有 § 9.5 标记为“已实现”的切片才是当前可用能力。

## 1. 1.x 当前架构结论

Knowledge Island Web MVP 采用**本地单体分层架构**：FastAPI + Uvicorn 承担本地 HTTP 接口层，SQLite 承担全部持久化，展示层已完成 B-141 Vue 3 + Vite 前端工程化收口；B-142 已把 Vue 工作台补齐为覆盖 SSE、取消和会话历史的主体验；B-143 已删除 legacy 静态前端 fallback；B-155 后后端源码统一位于 `backend/`，Web 首页只服务 `backend/static_dist/` Vue/Vite 构建产物。所有处理在本机单进程内完成，无外部消息队列和微服务；B-08 起，写入型导入入口通过进程内项目级协调器实现跨项目并发、同项目串行。

| 字段 | 值 |
|------|----|
| 架构模式 | 本地单体（Local Monolith）|
| 核心边界 | 127.0.0.1:8765，不对外暴露 |
| 主要入口 | `app.py` → `backend/api/server.py:create_app()` / `run_server()` |
| 数据持久化 | SQLite（本地默认 `runtime/app.db`；Docker 默认位于 `ki-runtime` volume 的 `/app/runtime/app.db`）|
| 外部依赖 | 可选 LLM API / Embedding API（均有本地 fallback）|

B-147 后，旧 PySide6 / 六边形桌面端已归档到 `archive/src-desktop-legacy/`，仅作为历史参考，不再被 Web、Docker 或 Tauri sidecar 链路引用。

## 2. 架构图（文字版）

```text
┌──────────────────────────────────────────────────────────────┐
│                 浏览器（Vue/Vite 构建产物）                  │
│   frontend/src/* → backend/static_dist/*                     │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP REST（127.0.0.1:8765）
┌──────────────────────────▼───────────────────────────────────┐
│          backend/api/server.py（FastAPI + Uvicorn）            │
│        静态文件服务 + /api/* JSON + SSE                        │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│   backend/api/dispatch.py + backend/routes/*（API Handler）   │
│      兼容入口 / 领域路由 / 参数校验 / JSON 响应               │
├──────────┬───────────────┬──────────────┬────────────────────┤
│ingestion │    search     │   answers    │   agent_tools      │
│.py 等    │    .py        │   .py        │   .py              │
│文件处理  │  混合检索     │  LLM/fallback│  只读工具白名单    │
│分块向量化│  关键词+向量  │  上下文组装  │  工具审计记录      │
├──────────┴───────────────┴──────────────┴────────────────────┤
│   backend/storage/knowledge_store.py（SQLite）+ Qdrant provider│
│     KnowledgeStore — Schema 初始化 + CRUD + 向量索引同步       │
├──────────────────────────────────────────────────────────────┤
│  embeddings.py         llm.py          model_profiles.py     │
│  向量化（API/hash）    LLM Chat        Profile CRUD+Key引用  │
└──────────────────────────┬───────────────────────────────────┘
                           │ 可选网络调用
┌──────────────────────────▼───────────────────────────────────┐
│                      外部可选服务                             │
│   DeepSeek API / OpenAI-compatible API / Ollama（本地）      │
└──────────────────────────────────────────────────────────────┘
```

## 3. 技术栈

| 层级 | 技术 | 用途 | 选择原因 |
|------|------|------|----------|
| 展示层 | Vue 3 + Vite | 单页应用 UI | B-141A-Z 已完成 Vue 工程骨架和页面级迁移薄片；B-142 补齐 Vue 工作台 SSE/会话；B-143 已删除 legacy static fallback；B-155 后输出到 `backend/static_dist/` |
| 接口层 | FastAPI + Uvicorn | HTTP 路由、SSE、OpenAPI | ADR-001；标准化中间件与流式响应 |
| 业务层 | Python 3.11 | 核心逻辑 | 生态丰富，AI 库支持完善 |
| 数据层 | SQLite 3（标准库）| 全部持久化 | 零依赖单文件数据库，本地优先最合适 |
| 向量化 | OpenAI-compatible Embedding API / 本地 hash | chunk 向量化 | API 质量高；hash fallback 保证无网络可用 |
| 向量存储 | Qdrant local mode（可选）+ SQLite `chunk_vectors` 兼容副本 | HNSW 向量候选检索；SQLite 降级 | B-134；大项目避免查询时全量扫 SQLite 向量 |
| LLM | DeepSeek / OpenAI-compatible / Ollama | 回答生成 | 兼容最广泛的模型格式 |
| 关键词检索 | 内置 BM25 + regex / 中文 bigram 分词 | chunk 关键词评分 | 无新增运行时依赖 |
| PDF 解析 | pymupdf（可选）| PDF 文本提取 | 性能优秀；未安装时明确跳过 |
| 容器化 | Docker + Docker Compose | 非技术用户一键启动 | 消除 Python 环境依赖 |

## 4. 分层职责

### 4.1 展示层（frontend/ + backend/static_dist/）

- `frontend/` 是 B-141 起的 Vue 3 + Vite 源码目录，生产构建输出到 `backend/static_dist/`
- `frontend/src/api/client.js` 封装 Vue 前端 `apiGet` / `apiPost` 和错误归一化
- `frontend/src/api/projects.js` 封装 Vue 项目空间列表、创建、选择、最近项目恢复、改名、删除和项目级检索默认值读取/保存，调用既有 `/api/projects`、`/api/projects/rename`、`/api/projects/delete` 与 `/api/projects/retrieval-settings` 契约
- `frontend/src/api/answer.js` 封装 Vue 工作台非流式问答、SSE 流式问答、聊天会话/消息、工具来源上下文和回答反馈入口，调用既有 `POST /api/answer`、`GET /api/answer/stream`、`/api/chat/*` 与 `POST /api/answer/feedback` 契约
- `frontend/src/api/search.js` 封装 Vue 工作台检索调试和检索复盘入口，调用既有 `POST /api/search/debug` 与 `/api/retrieval/reviews*` 契约
- `frontend/src/api/agent.js` 封装 Vue 工作台 Agent 只读工具入口，调用既有 `/api/agent/tools*` 契约
- `frontend/src/api/documents.js` 封装 Vue 资料库文档列表、单文档预览和单文档删除入口，调用既有 `GET /api/documents`、`GET /api/document` 与 `POST /api/documents/delete` 契约
- `frontend/src/api/document-collections.js` 封装 Vue 资料库文档集合列表、新建、重命名、删除和文档关联入口，调用既有 `GET/POST /api/document-collections`、`POST /api/document-collections/update`、`POST /api/document-collections/delete` 与 `POST /api/document-collections/items/*` 契约
- `frontend/src/api/imports.js` 封装 Vue 资料库导入预检、目录同步、文本笔记、URL 摘录、普通文件上传、浏览器文件夹上传和导入批次历史入口，调用既有 `GET /api/import/preview`、`POST /api/import`、`POST /api/import/note`、`POST /api/import/url`、`POST /api/import/upload`、`GET /api/import/batches` 与 `GET /api/import/batches/detail` 契约
- `frontend/src/api/settings.js` 封装 Vue 设置页基础模型设置、模型 Profile 和 Prompt 预设入口，调用既有 `GET/POST /api/settings/llm`、`POST /api/settings/llm/test`、`/api/model-profiles*` 与 `/api/prompt-presets*` 契约
- `frontend/src/api/assessment.js` 封装 Vue 评估页开始评估和提交回答入口，调用既有 `POST /api/assessment/start` 与 `POST /api/assessment/answer` 契约
- `frontend/src/state/app-state.js` 保存迁移期共享 UI 状态，包括当前视图、项目、文档、会话、评估、工具和检索相关字段
- `frontend/src/components/AppShell.vue` 和 `frontend/src/views/*` 负责基础布局与四个主视图壳；B-142 已将工作台收敛为左侧会话、中间对话、右侧上下文结构，并迁移 Workbench SSE/取消和会话历史
- `frontend/src/components/ProjectSpacePanel.vue` 是 B-141C/Q 的项目空间薄片，负责资料库中的项目空间选择、创建、改名和删除 UI
- `frontend/src/components/QuestionPanel.vue`、`frontend/src/components/AnswerPanel.vue`、`frontend/src/components/SearchDebugPanel.vue` 和 `frontend/src/components/AgentToolsPanel.vue` 是 B-141D/U/V/W/X/Y/Z 的工作台薄片，负责问题输入、非流式提交结果、来源、来源质量、回答反馈、检索调试、项目级检索默认值、检索复盘、Agent 只读工具展示、工具建议和工具来源上下文提示
- `frontend/src/components/DocumentListPanel.vue` 和 `frontend/src/components/DocumentPreviewPanel.vue` 是 B-141E/O/P 的资料库文档薄片，负责文档列表、加载/空/错误状态、单文档正文预览、单文档加入/移出集合入口以及单文档删除入口
- `frontend/src/components/DocumentImportPanel.vue` 是 B-141F/H/I/J/K 的资料库导入薄片，负责导入预检、目录同步、文本笔记、URL 摘录、普通文件上传和浏览器文件夹上传入口
- `frontend/src/components/DocumentCollectionPanel.vue` 是 B-141L/M/N 的资料库文档集合薄片，负责全部/未分组/指定集合筛选、集合文档数展示、集合新建、删除和重命名入口
- `frontend/src/components/ImportBatchHistoryPanel.vue` 是 B-141G 的资料库导入批次历史薄片，负责最近批次、只读详情和跳过/读取失败明细展示
- `frontend/src/views/AssessmentView.vue` 是 B-141T 的评估页最小闭环薄片，负责开始评估、当前题目、作答提交、下一题/完成、结果概览、答题记录和待复测列表
- `frontend/src/views/SettingsView.vue` 是 B-141R/S 的设置页配置薄片，负责基础 LLM 设置读取/保存/测试、模型 Profile 列表/编辑/删除/默认/测试，以及项目级 Prompt 预设列表、模板复制、编辑、删除和默认切换入口
- legacy 原生前端已由 B-143 删除，不再作为 FastAPI 静态 fallback
- 接收用户操作，通过 `fetch` 调用后端 REST API
- 管理客户端 UI 状态（当前项目、会话、文档列表）
- 渲染回答、来源、检索结果、工具输出
- 必须：所有业务规则不在前端实现，前端只做展示和 API 调用

### 4.2 接口层（backend/api/server.py + backend/api/dispatch.py + backend/routes/*）

- `backend.api.server.create_app()` 创建 FastAPI app，`run_server()` 通过 Uvicorn 启动本地服务
- `backend.api.dispatch.dispatch()` 保持兼容入口，解析 `raw_path` 后交给 `backend.routes.dispatch_to_routes()`
- `/api/answer/stream` 由 FastAPI `StreamingResponse` 输出既有 SSE 事件
- 当前静态前端只服务 `backend/static_dist/`；构建产物不存在时启动阶段抛出明确错误，不再回退 legacy 静态目录。
- `backend/routes/*` 按领域承载 REST 路由分支，提取 URL 参数和请求体
- `backend/routes/admin.py` 只承载本地维护入口，目前提供 `POST /api/admin/rebuild-index`，调用 `KnowledgeStore.rebuild_index()` 重建 chunk 与向量索引
- 参数合法性校验（必填字段、类型、取值范围）
- 调用业务模块，封装统一 JSON 响应格式
- 错误分类与 HTTP 状态码映射
- 必须：不承载复杂业务规则，不直接操作 SQLite

### 4.3 业务层（ingestion / search / answers / agent_tools / result_export）

- 实现核心知识处理逻辑（分块、向量化、检索、回答生成、结果导出）
- 编排多个存储操作构成完整用例
- 管理可选依赖的降级逻辑（API 失败时 fallback）
- `backend/domain/result_export.py` 负责将已生成问答消息格式化为 Markdown / PDF 文件并写入本地输出目录
- 必须：不引入 HTTP 概念（无 request/response），不格式化最终 JSON

### 4.4 数据层（backend/storage/knowledge_store.py）

- 初始化 SQLite schema（建表、兼容迁移）
- 提供 CRUD 方法（`KnowledgeStore` 类统一封装）
- 提供维护性索引重建方法（`KnowledgeStore.rebuild_index()`），基于已存文档正文重建 `document_chunks` / `chunk_vectors` 并同步 Qdrant provider
- 管理连接复用与事务
- 必须：不承载业务规则，不被前端 JS 直接调用

## 5. 端口与适配器映射

| 能力 | 实现 | 调用方 |
|------|------|--------|
| HTTP 服务 | `backend.api.server.create_app` / `backend.api.server.run_server` | `app.py` / Uvicorn |
| API 分发 | `backend.api.dispatch.dispatch` + `backend.routes.dispatch_to_routes` | `backend.api.server` |
| SQLite 存储 | `KnowledgeStore` | `backend.routes/*`、导入/检索/工具模块 |
| 索引重建维护 | `KnowledgeStore.rebuild_index` / `ops/scripts/rebuild_index.sh` | `POST /api/admin/rebuild-index` |
| 进程内摄入协调 | `ProjectIndexingCoordinator` | `backend.routes.imports` |
| 后端配置 | `backend.config.settings` / `backend.config.paths` | `backend.domain.llm`、`backend.domain.embeddings`、设置 API、脚本 |
| Qdrant 向量索引 | `backend.providers.vector_store.QdrantVectorStore` | `KnowledgeStore` 写入同步、`search_documents` 向量候选 |
| 本地目录导入 | `import_project_documents` | `POST /api/import` |
| 浏览器上传导入 | `import_uploaded_files` | `POST /api/import/upload` |
| 文本笔记导入 | `build_note_document` | `POST /api/import/note` |
| 检索 | `search_documents` / `KnowledgeStore.list_graph_related_chunks` / `build_source_quality` | `/api/search*` / `/api/answer` / 只读工具 |
| 回答生成 | `build_local_answer` / OpenAI-compatible Chat | `POST /api/answer` |
| 结果导出 | `export_chat_message_result` | `POST /api/export/result` |
| Agent 只读工具 | `run_agent_tool` | `POST /api/agent/tools/run` |
| Coach 项目分析 | `backend.domain.project_analysis` | `/api/coach/analyze` 与三个只读理解接口 |
| Coach 评估与计划 | `backend.domain.coach_assessment` / `backend.domain.learning_plans` | 七个 B-162 Coach API |
| Coach 进度存储 | `backend.storage.coach_progress_store.CoachProgressStoreMixin` | `KnowledgeStore` / Coach 领域 |
| Obsidian 配对与同步 | `backend.domain.obsidian_bridge` / `backend.routes.obsidian` | Obsidian 配对、连接和事件 API |
| Obsidian 受控发布 | `backend.domain.obsidian_publications` / `backend.domain.obsidian_protocol` | 发布预览、确认、待执行和结果 API |
| Obsidian 持久化 | `backend.storage.obsidian_store.ObsidianStoreMixin` | `KnowledgeStore` / Obsidian 领域 |
| Obsidian Vault 适配器 | `integrations/obsidian-plugin/` | Obsidian 桌面 Vault 事件与受控文件写入 |
| Vue API helper | `frontend/src/api/client.js` | Vue 组件 / 后续页面模块 |
| Vue 项目空间 helper | `frontend/src/api/projects.js` | `App.vue` / `ProjectSpacePanel.vue` / `SearchDebugPanel.vue` |
| Vue 问答 helper | `frontend/src/api/answer.js` | `App.vue` / `QuestionPanel.vue` / `AnswerPanel.vue` |
| Vue 检索调试/复盘 helper | `frontend/src/api/search.js` | `App.vue` / `SearchDebugPanel.vue` |
| Vue Agent 工具 helper | `frontend/src/api/agent.js` | `App.vue` / `AgentToolsPanel.vue` |
| Vue 文档浏览 helper | `frontend/src/api/documents.js` | `App.vue` / `DocumentListPanel.vue` / `DocumentPreviewPanel.vue` |
| Vue 文档集合 helper | `frontend/src/api/document-collections.js` | `App.vue` / `DocumentCollectionPanel.vue` / `DocumentListPanel.vue` |
| Vue 导入 helper | `frontend/src/api/imports.js` | `App.vue` / `DocumentImportPanel.vue` / `ImportBatchHistoryPanel.vue` |
| Vue 设置 helper | `frontend/src/api/settings.js` | `App.vue` / `SettingsView.vue` |
| Vue 评估 helper | `frontend/src/api/assessment.js` | `App.vue` / `AssessmentView.vue` |
| Vue UI 状态 | `frontend/src/state/app-state.js` | `App.vue` / Vue 组件 |

## 6. 外部依赖

| 依赖项 | 类型 | 用途 | 降级策略 |
|--------|------|------|----------|
| DeepSeek / OpenAI API | 可选外部 | LLM 回答生成 | 降级为本地 chunk 聚合 fallback |
| OpenAI-compatible Embedding API | 可选外部 | chunk 向量化 | 降级为本地 hash 向量 |
| qdrant-client | 可选 Python 包 | 本地 Qdrant 向量索引 | 未安装或不可用时打印 `WARNING`，搜索回退 SQLite `chunk_vectors` |
| Ollama | 可选本地 | 本地 LLM 推理 | 需用户自行安装并启动服务 |
| FastAPI / Uvicorn | 必需 Python 包 | 本地 HTTP API、静态文件与 SSE | 无降级；B-139 后为 Web MVP 运行时 |
| Node.js / npm | 必需前端构建工具 | 安装 Vue/Vite 依赖并生成 `backend/static_dist/` | 未构建时不再回退 legacy 静态前端 |
| Vue 3 / Vite | 必需前端构建依赖 | B-141 起的前端工程化和生产构建 | B-141A-Z 已完成工程骨架、项目空间选择/创建/改名/删除、非流式问答、回答反馈、检索调试、项目级检索默认值、检索复盘、Agent 只读工具、工具来源上下文、文档浏览/删除、轻量导入、批次历史、普通文件上传、浏览器文件夹上传、当前目录同步、导入预检、文档集合筛选/新建/删除/重命名/加入/移出、设置页模型配置/Prompt 预设和评估页最小闭环薄片；B-142 已补齐 Workbench SSE/取消、会话历史和消息管理 |
| pymupdf | 可选 Python 包 | PDF 文本提取 | 未安装时 PDF 跳过，有明确说明 |
| Docker | 可选 | 容器化一键启动 | 非必需；`python app.py` 是主要入口 |

## 7. 关键设计约束

- **单进程**：所有处理在 `app.py` 进程内，无外部后台 worker 或消息队列；写入型导入使用进程内项目锁，跨项目可并发，同项目串行
- **本地优先**：所有核心功能在无网络时可用（LLM 降级本地片段，Embedding 降级 hash）
- **可选依赖隔离**：`pymupdf` 等可选能力通过隔离入口引入，失败不影响主流程
- **API Key 安全**：Profile 只保存引用 token，不持久化明文 Key
- **只读 Agent**：工具白名单硬编码，拒绝任意命令执行

## 8. 备选方案与取舍

| 方案 | 是否采用 | 原因 |
|------|----------|------|
| FastAPI 替代 `http.server` | 已采用（B-139）| ADR-001；B-155 后兼容入口为 `backend.api.dispatch.dispatch()`，HTTP 契约不变 |
| Vue 3 + Vite 替代 Vanilla JS | 已采用（B-141A-Z、B-142、B-143 已收口）| ADR-006；B-141 已完成工程骨架和主要页面级入口迁移，B-142 已补齐 Workbench SSE/取消与会话历史；B-143 已删除 legacy static fallback |
| Qdrant 替代 SQLite 向量全扫描 | 已采用（B-134）| Qdrant local mode 提供 HNSW 候选检索；SQLite `chunk_vectors` 保留为兼容副本和降级路径 |
| Graph-enhanced 检索 | 已采用（B-126）| 不新增必需依赖，不修改 Web MVP schema；仅在当前数据库已有 legacy `graph_nodes` / `graph_edges` 时读取一跳相邻来源并入候选池 |
| PostgreSQL 替代 SQLite | 否 | 本地单用户场景 SQLite 足够；多用户时再迁移 |
| LangChain / LlamaIndex 替代自研 | 否 | 引入大型框架与本地极简原则冲突，增加不透明性 |
| BM25 替代 regex 关键词检索 | 已采用（B-127）| `backend/domain/search.py` 使用内置 BM25 计算 `keyword_score`，不新增必需依赖 |
| `api.py` 按领域拆分 | 已完成（B-138 / B-155 路径迁移）| 61 个 REST 端点已迁入 `backend/routes/*`；兼容入口位于 `backend/api/dispatch.py`，保持 HTTP 契约不变 |

## 9. Knowledge Island 2.0 目标架构与落地状态

### 9.1 产品与代际边界

Knowledge Island 2.0 的目标定位是“面向个人开发学习的本地项目知识教练”。主闭环为：导入代码项目与笔记 → 生成有来源的项目理解 → 学习问答 → 项目知识评估 → 通用技能差距 → 学习计划 → 用户确认后发布到 Obsidian。

| 维度 | 1.x 当前实现 | 2.0 已接受目标 |
|------|--------------|----------------|
| 核心产品 | 本地 RAG 知识库与问答工作台 | 本地项目知识教练 |
| 评价主口径 | 文档问答与轻量评估 | 当前项目的知识覆盖 |
| 辅助口径 | 规则化掌握度结果 | 版本化通用技能树映射；不等同于职业能力 |
| 默认数据根 | 1.x 数据保留在 `runtime/` | B-161 起默认使用独立 `runtime/v2/` 数据代际 |
| Obsidian | `/api/import/obsidian-vault` 一次性只读导入 | 桌面插件桥接、事件同步和受控发布 |

2.0 不迁移、不删除、不覆盖 1.x 的 SQLite、向量目录、Qdrant 本地索引或输出文件。B-161 已将默认启动路径切换到独立 v2 数据根，并在写入前验证数据代际；旧数据保留用于 1.x 回退或人工归档，不自动纳入 2.0 项目。

### 9.2 目标逻辑架构

```text
┌───────────────────────────────┐       ┌──────────────────────────────┐
│ Vue：教练 / 学习地图 / 计划   │       │ Obsidian 桌面插件            │
│ 资料 / 设置 / 依据抽屉        │       │ Vault 事件 + 受控文件写入    │
└──────────────┬────────────────┘       └──────────────┬───────────────┘
               │ Coach / 现有 API                       │ Obsidian 专用 API
┌──────────────▼────────────────────────────────────────▼───────────────┐
│ FastAPI 路由层：鉴权、参数校验、响应映射；不直接读写 SQLite/Vault    │
├──────────────────────────────┬───────────────────────────────────────┤
│ Coach 领域                    │ Obsidian Bridge 领域                  │
│ 分析、知识点、技能映射        │ 配对、事件幂等、发布状态机、冲突判定  │
│ 评估、覆盖聚合、学习计划      │ 不直接访问 Vault 文件系统             │
├──────────────────────────────┴───────────────────────────────────────┤
│ 既有导入 / 检索 / 回答能力（按 2.0 数据代际复用）                    │
├──────────────────────────────────────────────────────────────────────┤
│ v2 Storage：SQLite + 向量索引，唯一持久化入口                         │
│ runtime/v2/*；来源快照、不可变发布修订、令牌哈希                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 9.3 Coach 领域边界

- **项目分析**：对 Python、JavaScript/TypeScript 和常见 Web 清单做结构化分析；其他文本项目使用目录、清单、文档和 RAG 通用回退。规则基线必须在无 LLM 时可运行，LLM 只增强摘要、题目和计划。
- **来源约束**：知识点、知识点—技能映射、评估结论和普通 `learning` 任务必须关联真实项目来源；`source_gap` 任务只能表达资料缺口且来源为空。来源 checksum、路径或内容变化后，相关分析运行标记为 `stale`，不得继续显示为最新结论。
- **稳定身份**：知识点使用稳定 ID 与分析运行解耦；重新分析产生新运行和新来源快照，不以标题或展示顺序作为身份。
- **双层评价**：项目知识覆盖是主口径；语言、框架、数据、测试、交付、AI 等通用技能是版本化辅助口径。状态统一为 `unassessed / needs_work / developing / mastered`，界面必须说明结果只针对当前项目。
- **评估与计划**：评估以持久会话记录题目、回答、评分方式、置信度和来源；学习计划草稿可编辑排序，确认后不可被重新生成覆盖。
- **分层约束**：Coach 领域不包含 HTTP 对象、SQLite 语句、Vault 文件写入或前端展示规则；路由层与存储层继续遵守现有职责边界。

B-162 当前落地路径：

- `backend/domain/coach_assessment.py`：定向会话、规则/模型评分、覆盖率和技能聚合。
- `backend/domain/learning_plans.py`：确定性计划生成、受限模型润色、草稿结构更新、确认和进度更新。
- `backend/storage/coach_progress_store.py`：评估与计划六张表的唯一持久化入口，`backend/storage/knowledge_store.py` 只负责组合存储 mixin。
- `backend/routes/coach.py`：在 B-161 四个基础接口上新增三个评估/覆盖接口和四个学习计划接口；旧 `/api/assessment/*` 继续由原路由处理。
- 评估或计划写入前防御性比较当前项目来源指纹；过期分析只读保留，阻止新评估、草稿结构更新和确认，不阻止确认版任务进度更新。
- 评估评分依据只保存在服务端；学习计划生成、结构更新和确认按项目内进程锁串行，并分别用结构哈希与进度哈希保护客户端更新。
- 学习计划确认只改变 Coach 持久化状态，不产生 Obsidian 发布副作用；受控写回由 B-163 的独立预览、确认和插件执行链路负责。

### 9.4 Obsidian 桥边界

- 仅支持 Obsidian 桌面插件；后端不直接扫描或写入 Vault，插件是 Vault 变更的唯一执行方。
- 每个项目最多一个活动连接。一次性限时配对码换取仅可访问 Obsidian 路由的可撤销令牌；服务端只保存令牌哈希。
- 插件批量发送 Markdown `upsert / rename / delete` 事件，事件携带幂等 ID、Frontmatter、标签以及已解析/未解析 Wikilink。系统生成目录必须从反向摄入中排除。
- 发布严格经过“预览 → 用户确认 → 插件执行 → 结果回报”。目标路径越界、文件缺少系统标记、稳定 ID 不匹配或内容 hash 已变化时，状态转为 `conflict`；v1 插件不自动合并。
- 默认输出目录为 `Knowledge Island/<项目名>/`。所有可更新文件必须包含 `knowledge_island_managed`、稳定 ID、项目 ID、产物类型和修订号；生成文件被用户删除后不自动重建。
- 现有 `/api/import/obsidian-vault` 保持一次性只读导入语义，不升级为后端直接双向文件同步。

B-163 已实现路径：

- `backend/domain/obsidian_bridge.py`：五分钟一次性配对、只存哈希的可撤销插件令牌、连接查询/撤销，以及最多 100 项的幂等同步批次。
- `backend/domain/obsidian_protocol.py`：Vault 路径规范化、输出根边界、管理 Frontmatter、稳定 artifact ID 与内容 SHA-256。
- `backend/domain/obsidian_publications.py`：四类 Markdown 预览、用户确认、插件待执行队列、结果汇总，以及从历史发布创建新修订的回滚。
- `backend/storage/obsidian_store.py`：配对、连接、事件、发布、不可变 artifact 修订和结果六张表的唯一持久化入口。
- `backend/routes/obsidian.py`：九个 Obsidian API；插件专用路由从请求上下文验证 Bearer 令牌，不把凭证传入普通业务响应。
- `integrations/obsidian-plugin/`：独立 `desktopOnly` 插件工程。插件监听 Vault Markdown 事件，持久化离线事件/结果队列，排除系统输出目录，领取 `queued` 发布并在 Vault 内原子写入。
- 插件覆盖前同时校验输出根、`knowledge_island_managed`、稳定 ID、项目 ID、产物类型、修订号和预期 Vault hash。任一校验失败回传 `conflict`，不自动合并、不越权覆盖用户笔记。
- 生成文件被删除后不自动重建；只有新的用户预览与确认产生后续执行。插件成功回传的实际 hash 成为下一修订覆盖基线。

### 9.5 实施门禁

| 切片 | 目标 | 本文状态 |
|------|------|----------|
| B-161 | 项目分析、知识点、来源与技能映射 | 已实现（存储、规则分析与 Coach 基础 API） |
| B-162 | 持久评估、覆盖聚合与学习计划 | 已实现（领域、存储与七个 Coach API） |
| B-163 | Obsidian 插件桥、同步与受控发布 | 已实现（领域、存储、九个 API 与独立桌面插件） |
| B-164 | Vue 教练闭环 | 待实现 |
| B-165 | OpenAPI、测试、插件构建、E2E 与发布验收 | 待实现 |
