# 架构设计说明

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-28
> Scope：Knowledge Island Web MVP 架构层职责与技术栈
> Related：docs/design/system-design-overview.md, docs/design/database-design.md, docs/design/api-spec.md, docs/design/api-route-split-blueprint.md

## 1. 架构结论

Knowledge Island Web MVP 采用**本地单体分层架构**：FastAPI + Uvicorn 承担本地 HTTP 接口层，SQLite 承担全部持久化，展示层已完成 Vue 3 + Vite 前端工程化收口；B-146 后，后端运行时代码聚合在 `backend/knowledge_island/`，前端 npm 配置归入 `frontend/`，Docker 运维入口归入 `ops/docker/`，不再保留 legacy 静态前端 fallback。所有处理在本机单进程内完成，无消息队列和微服务。

| 字段 | 值 |
|------|----|
| 架构模式 | 本地单体（Local Monolith）|
| 核心边界 | 127.0.0.1:8765，不对外暴露 |
| 主要入口 | `backend/app.py` → `backend/knowledge_island/server.py:create_app()` / `run_server()` |
| 数据持久化 | SQLite（默认 `runtime/knowledge_island/knowledge_island.db`；Docker 挂载 `runtime/docker/`）|
| 外部依赖 | 可选 LLM API / Embedding API（均有本地 fallback）|

legacy PySide6 桌面端（`legacy/desktop/`）保留六边形分层约束，作为历史参考，不是当前默认入口。

B-20 后，legacy `QueryKnowledgeBaseUseCase` 会按 `QueryRequest.session_id` 读取同一 workspace、同一 legacy 会话最近 3 轮 `ConversationRecord`，并将其作为“最近对话”注入 prompt。未传 `session_id` 时继续使用默认会话，不影响 Web MVP 的 `chat_sessions` / `chat_messages`。

## 2. 架构图（文字版）

```text
┌──────────────────────────────────────────────────────────────┐
│                 浏览器（Vue/Vite 构建产物）                  │
│                 frontend/src/* → backend/knowledge_island/static_dist/         │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP REST（127.0.0.1:8765）
┌──────────────────────────▼───────────────────────────────────┐
│           backend/knowledge_island/server.py（FastAPI + Uvicorn）                │
│        静态文件服务 + /api/* JSON + SSE                        │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│       backend/knowledge_island/api.py + backend/knowledge_island/routes/*（API Handler）          │
│      兼容入口 / 领域路由 / 参数校验 / JSON 响应               │
├──────────┬───────────────┬──────────────┬────────────────────┤
│ingestion │    search     │   answers    │   agent_tools      │
│.py 等    │    .py        │   .py        │   .py              │
│文件处理  │  混合检索     │  LLM/fallback│  只读工具白名单    │
│分块向量化│  关键词+向量  │  上下文组装  │  工具审计记录      │
├──────────┴───────────────┴──────────────┴────────────────────┤
│               backend/knowledge_island/storage.py（SQLite）                     │
│         KnowledgeStore — Schema 初始化 + 所有 CRUD            │
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
| 展示层 | Vue 3 + Vite | 单页应用 UI | B-141A-Z 已完成 Vue 工程骨架和页面级迁移薄片；B-142 已补齐工作台 SSE 与会话历史；B-143 已移除 legacy fallback；B-146 后 npm 配置位于 `frontend/`，构建输出为 `backend/knowledge_island/static_dist/` |
| 接口层 | FastAPI + Uvicorn | HTTP 路由、SSE、OpenAPI | ADR-001；标准化中间件与流式响应 |
| 业务层 | Python 3.11 | 核心逻辑 | 生态丰富，AI 库支持完善 |
| 数据层 | SQLite 3（标准库）| 全部持久化 | 零依赖单文件数据库，本地优先最合适 |
| 向量化 | OpenAI-compatible Embedding API / 本地 hash | chunk 向量化 | API 质量高；hash fallback 保证无网络可用 |
| 向量存储 | Qdrant local mode / SQLite fallback | chunk 向量 ANN 检索与降级 | `VectorBackend` 抽象隔离检索后端；`KI_VECTOR_BACKEND=sqlite` 可回退到旧全扫描 |
| LLM | DeepSeek / OpenAI-compatible / Ollama | 回答生成 | 兼容最广泛的模型格式 |
| 关键词检索 | 内置 BM25 + regex / 中文 bigram 分词 | chunk 关键词评分 | 无新增运行时依赖 |
| PDF 解析 | pymupdf（可选）| PDF 文本提取 | 性能优秀；未安装时明确跳过 |
| 容器化 | Docker + Docker Compose | 非技术用户一键启动 | 消除 Python 环境依赖；B-146 后 Dockerfile、Compose 和启停脚本位于 `ops/docker/` |

## 4. 分层职责

### 4.1 展示层（frontend/）

- `frontend/` 是 B-141 起的 Vue 3 + Vite 源码目录，生产构建输出到 `backend/knowledge_island/static_dist/`
- `frontend/src/api/client.js` 封装 Vue 前端 `apiGet` / `apiPost` 和错误归一化
- `frontend/src/api/projects.js` 封装 Vue 项目空间列表、创建、选择、最近项目恢复、改名、删除和项目级检索默认值读取/保存，调用既有 `/api/projects`、`/api/projects/rename`、`/api/projects/delete` 与 `/api/projects/retrieval-settings` 契约
- `frontend/src/api/answer.js` 封装 Vue 工作台非流式问答、工具来源上下文和回答反馈入口，调用既有 `POST /api/answer` 与 `POST /api/answer/feedback` 契约
- `frontend/src/api/search.js` 封装 Vue 工作台检索调试和检索复盘入口，调用既有 `POST /api/search/debug` 与 `/api/retrieval/reviews*` 契约
- `frontend/src/api/agent.js` 封装 Vue 工作台 Agent 只读工具入口，调用既有 `/api/agent/tools*` 契约
- `frontend/src/api/documents.js` 封装 Vue 资料库文档列表、单文档预览和单文档删除入口，调用既有 `GET /api/documents`、`GET /api/document` 与 `POST /api/documents/delete` 契约
- `frontend/src/api/document-collections.js` 封装 Vue 资料库文档集合列表、新建、重命名、删除和文档关联入口，调用既有 `GET/POST /api/document-collections`、`POST /api/document-collections/update`、`POST /api/document-collections/delete` 与 `POST /api/document-collections/items/*` 契约
- `frontend/src/api/imports.js` 封装 Vue 资料库导入预检、目录同步、文本笔记、URL 摘录、普通文件上传、浏览器文件夹上传和导入批次历史入口，调用既有 `GET /api/import/preview`、`POST /api/import`、`POST /api/import/note`、`POST /api/import/url`、`POST /api/import/upload`、`GET /api/import/batches` 与 `GET /api/import/batches/detail` 契约
- `frontend/src/api/settings.js` 封装 Vue 设置页基础模型设置、模型 Profile 和 Prompt 预设入口，调用既有 `GET/POST /api/settings/llm`、`POST /api/settings/llm/test`、`/api/model-profiles*` 与 `/api/prompt-presets*` 契约
- `frontend/src/api/assessment.js` 封装 Vue 评估页开始评估和提交回答入口，调用既有 `POST /api/assessment/start` 与 `POST /api/assessment/answer` 契约
- `frontend/src/state/app-state.js` 保存迁移期共享 UI 状态，包括当前视图、项目、文档、会话、评估、工具和检索相关字段
- `frontend/src/components/AppShell.vue` 和 `frontend/src/views/*` 负责基础布局与四个主视图壳，B-142 继续迁移 Workbench SSE/取消和会话历史
- `frontend/src/components/ProjectSpacePanel.vue` 是 B-141C/Q 的项目空间薄片，负责资料库中的项目空间选择、创建、改名和删除 UI
- `frontend/src/components/QuestionPanel.vue`、`frontend/src/components/AnswerPanel.vue`、`frontend/src/components/SearchDebugPanel.vue` 和 `frontend/src/components/AgentToolsPanel.vue` 是 B-141D/U/V/W/X/Y/Z 的工作台薄片，负责问题输入、非流式提交结果、来源、来源质量、回答反馈、检索调试、项目级检索默认值、检索复盘、Agent 只读工具展示、工具建议和工具来源上下文提示
- `frontend/src/components/DocumentListPanel.vue` 和 `frontend/src/components/DocumentPreviewPanel.vue` 是 B-141E/O/P 的资料库文档薄片，负责文档列表、加载/空/错误状态、单文档正文预览、单文档加入/移出集合入口以及单文档删除入口
- `frontend/src/components/DocumentImportPanel.vue` 是 B-141F/H/I/J/K 的资料库导入薄片，负责导入预检、目录同步、文本笔记、URL 摘录、普通文件上传和浏览器文件夹上传入口
- `frontend/src/components/DocumentCollectionPanel.vue` 是 B-141L/M/N 的资料库文档集合薄片，负责全部/未分组/指定集合筛选、集合文档数展示、集合新建、删除和重命名入口
- `frontend/src/components/ImportBatchHistoryPanel.vue` 是 B-141G 的资料库导入批次历史薄片，负责最近批次、只读详情和跳过/读取失败明细展示
- `frontend/src/views/AssessmentView.vue` 是 B-141T 的评估页最小闭环薄片，负责开始评估、当前题目、作答提交、下一题/完成、结果概览、答题记录和待复测列表
- `frontend/src/views/SettingsView.vue` 是 B-141R/S 的设置页配置薄片，负责基础 LLM 设置读取/保存/测试、模型 Profile 列表/编辑/删除/默认/测试，以及项目级 Prompt 预设列表、模板复制、编辑、删除和默认切换入口
- `backend/knowledge_island/static_dist/` 是唯一静态前端服务目录，由 `npm --prefix frontend run build` 本地生成且不入库
- 接收用户操作，通过 `fetch` 调用后端 REST API
- 管理客户端 UI 状态（当前项目、会话、文档列表）
- 渲染回答、来源、检索结果、工具输出
- 必须：所有业务规则不在前端实现，前端只做展示和 API 调用

### 4.2 接口层（backend/knowledge_island/server.py + backend/knowledge_island/api.py + backend/knowledge_island/routes/*）

- `backend.knowledge_island.server.create_app()` 创建 FastAPI app，`run_server()` 通过 Uvicorn 启动本地服务
- `backend.knowledge_island.api.dispatch()` 保持兼容入口，解析 `raw_path` 后交给 `backend.knowledge_island.routes.dispatch_to_routes()`
- `/api/answer/stream` 由 FastAPI `StreamingResponse` 输出既有 SSE 事件
- 静态前端服务 `backend/knowledge_island/static_dist/`；构建产物不存在时返回 503 构建提示，不再回退 legacy 前端
- `backend/knowledge_island/routes/*` 按领域承载 REST 路由分支，提取 URL 参数和请求体
- 参数合法性校验（必填字段、类型、取值范围）
- 调用业务模块，封装统一 JSON 响应格式
- 错误分类与 HTTP 状态码映射
- 必须：不承载复杂业务规则，不直接操作 SQLite

### 4.3 业务层（ingestion / search / answers / agent_tools）

- 实现核心知识处理逻辑（分块、向量化、检索、回答生成）
- 编排多个存储操作构成完整用例
- 管理可选依赖的降级逻辑（API 失败时 fallback）
- 必须：不引入 HTTP 概念（无 request/response），不格式化最终 JSON

### 4.4 数据层（backend/knowledge_island/storage.py）

- 初始化 SQLite schema（建表、兼容迁移）
- 提供 CRUD 方法（`KnowledgeStore` 类统一封装）
- 管理连接复用与事务
- 必须：不承载业务规则，不被前端 JS 直接调用

## 5. 端口与适配器映射

| 能力 | 实现 | 调用方 |
|------|------|--------|
| HTTP 服务 | `backend.knowledge_island.server.create_app` / `backend.knowledge_island.server.run_server` | `backend/app.py` / Uvicorn |
| API 分发 | `backend.knowledge_island.api.dispatch` + `backend.knowledge_island.routes.dispatch_to_routes` | `backend.knowledge_island.server` |
| SQLite 存储 | `KnowledgeStore` | `backend.knowledge_island.routes/*`、导入/检索/工具模块 |
| 向量后端 | `backend.knowledge_island.vector_backend.VectorBackend` | `search_documents` / `KnowledgeStore` chunk 向量写入 |
| 本地目录导入 | `import_project_documents` | `POST /api/import` |
| 浏览器上传导入 | `import_uploaded_files` | `POST /api/import/upload` |
| 文本笔记导入 | `build_note_document` | `POST /api/import/note` |
| 检索 | `search_documents` / `build_source_quality` | `/api/search*` / `/api/answer` / 只读工具 |
| 回答生成 | `build_local_answer` / OpenAI-compatible Chat | `POST /api/answer` |
| Agent 只读工具 | `run_agent_tool` | `POST /api/agent/tools/run` |
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
| Qdrant Client | 可选 Python 包 | 本地 Qdrant 向量后端 | 未安装或显式 `KI_VECTOR_BACKEND=sqlite` 时使用 SQLite `chunk_vectors` 全扫描 |
| Ollama | 可选本地 | 本地 LLM 推理 | 需用户自行安装并启动服务 |
| FastAPI / Uvicorn | 必需 Python 包 | 本地 HTTP API、静态文件与 SSE | 无降级；B-139 后为 Web MVP 运行时 |
| Node.js / npm | 必需前端构建工具 | 安装 Vue/Vite 依赖并生成 `backend/knowledge_island/static_dist/` | 未构建时 FastAPI 返回 503 构建提示 |
| Vue 3 / Vite | 必需前端构建依赖 | B-141 起的前端工程化和生产构建 | B-141A-Z 已完成工程骨架、项目空间选择/创建/改名/删除、非流式问答、回答反馈、检索调试、项目级检索默认值、检索复盘、Agent 只读工具、工具来源上下文、文档浏览/删除、轻量导入、批次历史、普通文件上传、浏览器文件夹上传、当前目录同步、导入预检、文档集合筛选/新建/删除/重命名/加入/移出、设置页模型配置/Prompt 预设和评估页最小闭环薄片；B-142 已补齐 Vue 工作台 SSE 流式问答、取消当前回答、聊天会话和历史恢复 |
| pymupdf | 可选 Python 包 | PDF 文本提取 | 未安装时 PDF 跳过，有明确说明 |
| Docker | 可选 | 容器化一键启动 | 非必需；`python backend/app.py` 是主要入口；配置与脚本位于 `ops/docker/` |

## 7. 关键设计约束

- **单进程**：所有处理在 `backend/app.py` 进程内，无后台 worker 或消息队列
- **本地优先**：所有核心功能在无网络时可用（LLM 降级本地片段，Embedding 降级 hash）
- **可选依赖隔离**：`pymupdf` 等可选能力通过隔离入口引入，失败不影响主流程
- **API Key 安全**：Profile 只保存引用 token，不持久化明文 Key
- **只读 Agent**：工具白名单硬编码，拒绝任意命令执行

## 8. 备选方案与取舍

| 方案 | 是否采用 | 原因 |
|------|----------|------|
| FastAPI 替代 `http.server` | 已采用（B-139）| ADR-001；保留 `backend.knowledge_island.api.dispatch()` 兼容入口，先迁移 HTTP 外壳，B-140/B-141 串行推进 |
| Vue 3 + Vite 替代 Vanilla JS | 已采用（B-144 已解耦前后端目录）| ADR-006；B-141 已完成工程骨架和主要页面级入口迁移，B-142 已补齐 Workbench SSE/会话，B-143 已删除 `webapp/static/`，B-144 已将后端聚合到 `backend/knowledge_island/` |
| Qdrant 替代 SQLite 向量全扫描 | 已接入（B-134）| v0.13.0 通过 `backend/knowledge_island/vector_backend.py` 支持 Qdrant local mode；SQLite `chunk_vectors` 保留为备份和降级路径 |
| PostgreSQL 替代 SQLite | 否 | 本地单用户场景 SQLite 足够；多用户时再迁移 |
| LangChain / LlamaIndex 替代自研 | 否 | 引入大型框架与本地极简原则冲突，增加不透明性 |
| BM25 替代 regex 关键词检索 | 已采用（B-127）| `backend/knowledge_island/search.py` 使用内置 BM25 计算 `keyword_score`，不新增必需依赖 |
| `api.py` 按领域拆分 | 已完成（B-138）| 61 个 REST 端点已迁入 `backend/knowledge_island/routes/*`；`backend/knowledge_island/api.py` 仅保留 `dispatch()`、`answer_stream_events()` 和兼容导出入口，保持 `backend.knowledge_island.api.dispatch` 兼容入口 |
