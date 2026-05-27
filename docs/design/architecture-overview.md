# 架构设计说明

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-27
> Scope：Knowledge Island Web MVP 架构层职责与技术栈
> Related：docs/design/system-design-overview.md, docs/design/database-design.md, docs/design/api-spec.md, docs/design/api-route-split-blueprint.md

## 1. 架构结论

Knowledge Island Web MVP 采用**本地单体分层架构**：FastAPI + Uvicorn 承担本地 HTTP 接口层，SQLite 承担全部持久化，展示层处于 B-141 迁移期：Vue 3 + Vite 工程骨架已引入，完整业务 UI 迁移前仍保留 legacy Vanilla JS SPA fallback。所有处理在本机单进程内完成，无消息队列和微服务。

| 字段 | 值 |
|------|----|
| 架构模式 | 本地单体（Local Monolith）|
| 核心边界 | 127.0.0.1:8765，不对外暴露 |
| 主要入口 | `app.py` → `webapp/server.py:create_app()` / `run_server()` |
| 数据持久化 | SQLite（`runtime/docker/knowledge.db`）|
| 外部依赖 | 可选 LLM API / Embedding API（均有本地 fallback）|

legacy PySide6 桌面端（`src/desktop/`）保留六边形分层约束，作为历史参考，不是当前默认入口。

B-20 后，legacy `QueryKnowledgeBaseUseCase` 会按 `QueryRequest.session_id` 读取同一 workspace、同一 legacy 会话最近 3 轮 `ConversationRecord`，并将其作为“最近对话”注入 prompt。未传 `session_id` 时继续使用默认会话，不影响 Web MVP 的 `chat_sessions` / `chat_messages`。

## 2. 架构图（文字版）

```text
┌──────────────────────────────────────────────────────────────┐
│          浏览器（Vue/Vite 构建产物或 legacy Vanilla SPA）      │
│   frontend/src/* 或 webapp/static/js/*                       │
└──────────────────────────┬───────────────────────────────────┘
                           │ HTTP REST（127.0.0.1:8765）
┌──────────────────────────▼───────────────────────────────────┐
│           webapp/server.py（FastAPI + Uvicorn）                │
│        静态文件服务 + /api/* JSON + SSE                        │
└──────────────────────────┬───────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────┐
│       webapp/api.py + webapp/routes/*（API Handler）          │
│      兼容入口 / 领域路由 / 参数校验 / JSON 响应               │
├──────────┬───────────────┬──────────────┬────────────────────┤
│ingestion │    search     │   answers    │   agent_tools      │
│.py 等    │    .py        │   .py        │   .py              │
│文件处理  │  混合检索     │  LLM/fallback│  只读工具白名单    │
│分块向量化│  关键词+向量  │  上下文组装  │  工具审计记录      │
├──────────┴───────────────┴──────────────┴────────────────────┤
│               webapp/storage.py（SQLite）                     │
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
| 展示层 | Vue 3 + Vite / legacy Vanilla HTML/CSS/JS | 单页应用 UI | B-141A 已建立 `frontend/` 工程骨架；完整迁移前 `webapp/static/` 仍作为 fallback |
| 接口层 | FastAPI + Uvicorn | HTTP 路由、SSE、OpenAPI | ADR-001；标准化中间件与流式响应 |
| 业务层 | Python 3.11 | 核心逻辑 | 生态丰富，AI 库支持完善 |
| 数据层 | SQLite 3（标准库）| 全部持久化 | 零依赖单文件数据库，本地优先最合适 |
| 向量化 | OpenAI-compatible Embedding API / 本地 hash | chunk 向量化 | API 质量高；hash fallback 保证无网络可用 |
| LLM | DeepSeek / OpenAI-compatible / Ollama | 回答生成 | 兼容最广泛的模型格式 |
| 关键词检索 | 内置 BM25 + regex / 中文 bigram 分词 | chunk 关键词评分 | 无新增运行时依赖 |
| PDF 解析 | pymupdf（可选）| PDF 文本提取 | 性能优秀；未安装时明确跳过 |
| 容器化 | Docker + Docker Compose | 非技术用户一键启动 | 消除 Python 环境依赖 |

## 4. 分层职责

### 4.1 展示层（frontend/ + webapp/static/）

- `frontend/` 是 B-141 起的 Vue 3 + Vite 源码目录，生产构建输出到 `webapp/static_dist/`
- `frontend/src/api/client.js` 封装 Vue 前端 `apiGet` / `apiPost` 和错误归一化
- `frontend/src/api/projects.js` 封装 Vue 项目空间列表、创建、选择和最近项目恢复，调用既有 `/api/projects` 契约
- `frontend/src/api/answer.js` 封装 Vue 工作台非流式问答入口，调用既有 `POST /api/answer` 契约
- `frontend/src/api/documents.js` 封装 Vue 资料库文档列表和单文档预览入口，调用既有 `GET /api/documents` 与 `GET /api/document` 契约
- `frontend/src/api/imports.js` 封装 Vue 资料库导入预检、目录同步、文本笔记、URL 摘录、普通文件上传、浏览器文件夹上传和导入批次历史入口，调用既有 `GET /api/import/preview`、`POST /api/import`、`POST /api/import/note`、`POST /api/import/url`、`POST /api/import/upload`、`GET /api/import/batches` 与 `GET /api/import/batches/detail` 契约
- `frontend/src/state/app-state.js` 保存迁移期共享 UI 状态，包括当前视图、项目、文档、会话、评估、工具和检索相关字段
- `frontend/src/components/AppShell.vue` 和 `frontend/src/views/*` 负责基础布局与四个主视图壳，完整业务页面后续逐步迁移
- `frontend/src/components/ProjectSpacePanel.vue` 是 B-141C 的第一个业务薄片，负责资料库中的项目空间选择与创建 UI
- `frontend/src/components/QuestionPanel.vue` 和 `frontend/src/components/AnswerPanel.vue` 是 B-141D 的工作台问答薄片，负责问题输入、非流式提交结果、来源和来源质量展示
- `frontend/src/components/DocumentListPanel.vue` 和 `frontend/src/components/DocumentPreviewPanel.vue` 是 B-141E 的资料库只读浏览薄片，负责文档列表、加载/空/错误状态和单文档正文预览
- `frontend/src/components/DocumentImportPanel.vue` 是 B-141F/H/I/J/K 的资料库导入薄片，负责导入预检、目录同步、文本笔记、URL 摘录、普通文件上传和浏览器文件夹上传入口
- `frontend/src/components/ImportBatchHistoryPanel.vue` 是 B-141G 的资料库导入批次历史薄片，负责最近批次、只读详情和跳过/读取失败明细展示
- `webapp/static/` 是迁移期 legacy 原生前端 fallback，B-141A 不删除
- 接收用户操作，通过 `fetch` 调用后端 REST API
- 管理客户端 UI 状态（当前项目、会话、文档列表）
- 渲染回答、来源、检索结果、工具输出
- 必须：所有业务规则不在前端实现，前端只做展示和 API 调用

### 4.2 接口层（webapp/server.py + webapp/api.py + webapp/routes/*）

- `webapp.server.create_app()` 创建 FastAPI app，`run_server()` 通过 Uvicorn 启动本地服务
- `webapp.api.dispatch()` 保持兼容入口，解析 `raw_path` 后交给 `webapp.routes.dispatch_to_routes()`
- `/api/answer/stream` 由 FastAPI `StreamingResponse` 输出既有 SSE 事件
- 静态前端优先服务 `webapp/static_dist/`；构建产物不存在时回退 `webapp/static/`
- `webapp/routes/*` 按领域承载 REST 路由分支，提取 URL 参数和请求体
- 参数合法性校验（必填字段、类型、取值范围）
- 调用业务模块，封装统一 JSON 响应格式
- 错误分类与 HTTP 状态码映射
- 必须：不承载复杂业务规则，不直接操作 SQLite

### 4.3 业务层（ingestion / search / answers / agent_tools）

- 实现核心知识处理逻辑（分块、向量化、检索、回答生成）
- 编排多个存储操作构成完整用例
- 管理可选依赖的降级逻辑（API 失败时 fallback）
- 必须：不引入 HTTP 概念（无 request/response），不格式化最终 JSON

### 4.4 数据层（webapp/storage.py）

- 初始化 SQLite schema（建表、兼容迁移）
- 提供 CRUD 方法（`KnowledgeStore` 类统一封装）
- 管理连接复用与事务
- 必须：不承载业务规则，不被前端 JS 直接调用

## 5. 端口与适配器映射

| 能力 | 实现 | 调用方 |
|------|------|--------|
| HTTP 服务 | `webapp.server.create_app` / `webapp.server.run_server` | `app.py` / Uvicorn |
| API 分发 | `webapp.api.dispatch` + `webapp.routes.dispatch_to_routes` | `webapp.server` |
| SQLite 存储 | `KnowledgeStore` | `webapp.routes/*`、导入/检索/工具模块 |
| 本地目录导入 | `import_project_documents` | `POST /api/import` |
| 浏览器上传导入 | `import_uploaded_files` | `POST /api/import/upload` |
| 文本笔记导入 | `build_note_document` | `POST /api/import/note` |
| 检索 | `search_documents` / `build_source_quality` | `/api/search*` / `/api/answer` / 只读工具 |
| 回答生成 | `build_local_answer` / OpenAI-compatible Chat | `POST /api/answer` |
| Agent 只读工具 | `run_agent_tool` | `POST /api/agent/tools/run` |
| Vue API helper | `frontend/src/api/client.js` | Vue 组件 / 后续页面模块 |
| Vue 项目空间 helper | `frontend/src/api/projects.js` | `App.vue` / `ProjectSpacePanel.vue` |
| Vue 问答 helper | `frontend/src/api/answer.js` | `App.vue` / `QuestionPanel.vue` / `AnswerPanel.vue` |
| Vue 文档浏览 helper | `frontend/src/api/documents.js` | `App.vue` / `DocumentListPanel.vue` / `DocumentPreviewPanel.vue` |
| Vue 导入 helper | `frontend/src/api/imports.js` | `App.vue` / `DocumentImportPanel.vue` / `ImportBatchHistoryPanel.vue` |
| Vue UI 状态 | `frontend/src/state/app-state.js` | `App.vue` / Vue 组件 |

## 6. 外部依赖

| 依赖项 | 类型 | 用途 | 降级策略 |
|--------|------|------|----------|
| DeepSeek / OpenAI API | 可选外部 | LLM 回答生成 | 降级为本地 chunk 聚合 fallback |
| OpenAI-compatible Embedding API | 可选外部 | chunk 向量化 | 降级为本地 hash 向量 |
| Ollama | 可选本地 | 本地 LLM 推理 | 需用户自行安装并启动服务 |
| FastAPI / Uvicorn | 必需 Python 包 | 本地 HTTP API、静态文件与 SSE | 无降级；B-139 后为 Web MVP 运行时 |
| Node.js / npm | 必需前端构建工具 | 安装 Vue/Vite 依赖并生成 `webapp/static_dist/` | 未构建时 FastAPI 回退 `webapp/static/` |
| Vue 3 / Vite | 必需前端构建依赖 | B-141 起的前端工程化和生产构建 | B-141A 提供骨架，B-141C/D/E/F/G/H/I/J/K 已迁移项目空间、非流式问答、文档浏览、轻量导入、批次历史、普通文件上传、浏览器文件夹上传、当前目录同步和导入预检薄片；完整业务 UI 仍在迁移中 |
| pymupdf | 可选 Python 包 | PDF 文本提取 | 未安装时 PDF 跳过，有明确说明 |
| Docker | 可选 | 容器化一键启动 | 非必需；`python app.py` 是主要入口 |

## 7. 关键设计约束

- **单进程**：所有处理在 `app.py` 进程内，无后台 worker 或消息队列
- **本地优先**：所有核心功能在无网络时可用（LLM 降级本地片段，Embedding 降级 hash）
- **可选依赖隔离**：`pymupdf` 等可选能力通过隔离入口引入，失败不影响主流程
- **API Key 安全**：Profile 只保存引用 token，不持久化明文 Key
- **只读 Agent**：工具白名单硬编码，拒绝任意命令执行

## 8. 备选方案与取舍

| 方案 | 是否采用 | 原因 |
|------|----------|------|
| FastAPI 替代 `http.server` | 已采用（B-139）| ADR-001；保留 `webapp.api.dispatch()` 兼容入口，先迁移 HTTP 外壳，B-140/B-141 串行推进 |
| Vue 3 + Vite 替代 Vanilla JS | 已采用（B-141A 起分阶段迁移）| ADR-006；先建立工程骨架和构建链，B-141C/D/E/F/G/H/I/J/K 已迁移项目空间、非流式问答、文档浏览、轻量导入、批次历史、普通文件上传、浏览器文件夹上传、当前目录同步和导入预检薄片，完整业务 UI 后续按页面迁移 |
| ChromaDB / Qdrant 替代 SQLite 向量 | 待实施（B-134）| SQLite 全扫描在 > 5000 chunks 时性能下降 |
| PostgreSQL 替代 SQLite | 否 | 本地单用户场景 SQLite 足够；多用户时再迁移 |
| LangChain / LlamaIndex 替代自研 | 否 | 引入大型框架与本地极简原则冲突，增加不透明性 |
| BM25 替代 regex 关键词检索 | 已采用（B-127）| `webapp/search.py` 使用内置 BM25 计算 `keyword_score`，不新增必需依赖 |
| `api.py` 按领域拆分 | 已完成（B-138）| 61 个 REST 端点已迁入 `webapp/routes/*`；`webapp/api.py` 仅保留 `dispatch()`、`answer_stream_events()` 和兼容导出入口，保持 `webapp.api.dispatch` 兼容入口 |
