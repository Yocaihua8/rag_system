# Changelog

所有版本变更记录遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 结构，版本号遵循语义化版本（[Semantic Versioning](https://semver.org/lang/zh-CN/)）。

开发过程细节（每个 B-xxx 变更文件、临时决策、卡点）见 `docs/devlog/`。

---

## [Unreleased]

---

## [v1.0.0] - 2026-07-01

### Added
- **Vue/Vite 前端工程骨架**：新增 `frontend/`、根 `package.json` 和 Vite 构建链，生产构建输出到 `backend/static_dist/`
- **Vue 基础应用壳**：新增 Vue API client、共享状态模型、`AppShell` 和工作台 / 资料库 / 评估 / 设置四个基础视图壳
- **Vue 项目空间薄片**：资料库视图新增项目空间列表、选择、最近项目恢复和新建项目空间表单，复用既有 `/api/projects` 契约
- **Vue 项目空间改名/删除薄片**：资料库视图新增当前项目改名和删除入口，复用既有 `/api/projects/rename` 与 `/api/projects/delete` 契约；删除前提示项目内文档记录也会被删除
- **Vue 工作台问答薄片**：工作台视图新增非流式问题输入、回答展示、来源列表和来源质量摘要，复用既有 `/api/answer` 契约
- **Vue 资料库文档浏览薄片**：资料库视图新增当前项目文档列表和单文档正文预览，复用既有 `/api/documents` 与 `/api/document` 契约
- **Vue 资料库轻量导入薄片**：资料库视图新增文本笔记导入和 URL 摘录导入，复用既有 `/api/import/note` 与 `/api/import/url` 契约
- **Vue 资料库导入批次历史薄片**：资料库视图新增导入批次列表和只读详情，复用既有 `/api/import/batches` 与 `/api/import/batches/detail` 契约
- **Vue 资料库普通文件上传薄片**：资料库视图新增普通多文件上传入口，复用既有 `/api/import/upload` 契约
- **Vue 资料库浏览器文件夹导入薄片**：资料库视图新增 `webkitdirectory` 文件夹选择入口，复用既有 `/api/import/upload` 与 `browser_folder_upload` 契约
- **Vue 资料库目录同步薄片**：资料库视图新增“同步当前项目目录”入口，复用既有 `/api/import` 契约
- **Vue 资料库导入预检薄片**：资料库视图新增“预检当前项目目录”入口，复用既有 `/api/import/preview` 只读契约
- **网页抓取导入**：资料库视图新增单 URL 网页抓取预览与确认入库，后端新增 `/api/import/web-fetch/preview` 和 `/api/import/web-fetch/commit`，写入 `web:` 虚拟来源与 `web_fetch` 导入批次；手动 `/api/import/url` 仍不联网
- **GitHub Actions CI 流水线**：新增 `.github/workflows/ci.yml`，在 `main` push / PR 上并行运行 `python-tests`（backend + webapp pytest、文档一致性）和 `frontend-e2e`（Vue/Vite build、Playwright E2E），并为 pip/npm 依赖配置版本化缓存
- **Vue 资料库文档集合筛选薄片**：资料库视图新增文档集合只读筛选入口，复用既有 `/api/document-collections` 与 `/api/documents?collection_id=...` 契约
- **Vue 资料库文档集合管理薄片**：资料库视图新增文档集合新建和删除入口，复用既有 `/api/document-collections` 与 `/api/document-collections/delete` 契约；删除集合不删除文档
- **Vue 资料库文档集合重命名薄片**：资料库视图新增文档集合重命名入口，复用既有 `/api/document-collections/update` 契约
- **Vue 资料库文档集合归组薄片**：资料库文档列表新增单文档加入集合和从当前集合移出入口，复用既有 `/api/document-collections/items/add` 与 `/api/document-collections/items/remove` 契约
- **Vue 资料库文档删除薄片**：资料库文档列表新增单文档删除入口，复用既有 `/api/documents/delete` 契约；删除前提示源文件不会被删除
- **Vue 设置页模型配置薄片**：设置视图新增基础模型设置读取/保存/测试和模型 Profile 新增/编辑/删除/默认/测试入口，复用既有 `/api/settings/llm` 与 `/api/model-profiles*` 契约，API Key 不回显明文
- **Vue 设置页 Prompt 预设薄片**：设置视图新增当前项目 Prompt 预设列表、内置模板复制、新增/编辑/删除/默认/清空默认入口，复用既有 `/api/prompt-presets*` 契约
- **Vue 评估页最小闭环薄片**：评估视图新增开始评估、当前题作答、下一题/完成、结果概览、答题记录和待复测列表，复用既有 `/api/assessment/start` 与 `/api/assessment/answer` 契约
- **Vue 工作台回答反馈薄片**：工作台视图在回答返回后新增“有用 / 无用 / 来源不准 / 需要更多上下文”反馈入口，复用既有 `/api/answer/feedback` 契约
- **Vue 工作台检索调试薄片**：工作台视图新增检索诊断查询、`top_k` / `min_score` / 关键词 / 向量临时参数和命中片段展示，复用既有 `/api/search/debug` 契约
- **Vue 工作台检索默认值薄片**：工作台视图新增项目级检索默认值读取/保存入口，可把 `top_k` / `min_score` / 关键词 / 向量开关保存为当前项目默认值，复用既有 `/api/projects/retrieval-settings` 契约
- **Vue 工作台检索复盘薄片**：工作台视图新增复盘备注、保存复盘、复盘历史、详情和删除入口，复用既有 `/api/retrieval/reviews*` 契约
- **Vue 工作台 Agent 只读工具薄片**：工作台视图新增只读工具元数据、`project_overview` / `search_sources` 手动运行、工具结果、运行历史和详情展示，复用既有 `/api/agent/tools*` 契约
- **Vue 工作台工具来源上下文薄片**：工作台回答区新增工具建议展示、建议 `search_sources` 手动运行、工具结果标记为下一问上下文和 `tool_context` 展示，复用既有 `/api/answer` 与 `/api/agent/tools/run` 契约
- **B-141 Vue 前端工程化收口**：B-141A-Z 页面级迁移薄片已完成并通过收口验证；Workbench SSE/会话迁移拆为后续 B-142，legacy 静态前端继续作为 fallback
- **可选认证中间件**：Web MVP 支持通过 `RAG_AUTH_ENABLED=1` 启用 API Key + Bearer JWT 认证，保护 `/api/*`、`/docs`、`/redoc` 和 `/openapi.json`
- **FastAPI 运行时**：Web MVP HTTP 服务层迁移到 FastAPI + Uvicorn，保留 `python app.py` 启动方式，并新增本地 `/docs` 自动接口文档入口
- **深色模式**：Web 页面跟随系统深色偏好，并提供侧栏按钮手动切换浅色 / 深色主题；手动选择保存到浏览器 `localStorage`
- **评估题模型与存储**：Web MVP 新增 `assessment_questions`、`assessment_answers`、`assessment_results`，开始评估会保存题目，提交回答会保存回答和评估结果
- **自动出题用例**：Web MVP `/api/assessment/start` 可规则化生成概念理解、流程说明、代码定位三类题，并为每题保存轻量知识点标签和来源
- **回答评估用例**：Web MVP `/api/assessment/answer` 按服务端已保存题目的参考要点评分，输出已掌握 / 基本理解 / 需要补充 / 暂未掌握四档状态
- **评估前端闭环**：评估页支持一轮多题进度、逐题提交、下一题、答题记录和待复测列表
- **完整备份恢复**：项目备份导出包含文档正文、chunk 和 vector；恢复到新项目后无需重新导入即可检索问答
- **Qdrant 本地向量存储**：可通过 `RAG_VECTOR_STORE_PROVIDER=qdrant` 启用 Qdrant local mode，文档入库/更新/删除同步本地向量索引，搜索时由 Qdrant 返回向量候选
- **流式问答输出**：新增 `/api/answer/stream` SSE 通道，前端通过 EventSource 边收边渲染回答，完成后刷新来源、观察性和聊天记录

### Changed
- **后端源码目录重组**：B-155 将原 `webapp/` 生产代码按职责迁移到 `backend/api`、`backend/routes`、`backend/domain`、`backend/storage`，删除受控 `webapp/` 源码目录；HTTP API 契约和 SQLite schema 保持不变，Vue/Vite 构建产物改为输出到 `backend/static_dist/`。
- **BACKLOG 完成项归档**：B-149 CI 持续集成流水线已完成并从 `docs/BACKLOG.md §5` 移除；对应能力见 Added 中 GitHub Actions CI 流水线条目。
- **BACKLOG 完成项归档**：按 BACKLOG 流转规则从 `docs/BACKLOG.md §5` 移除 27 个已完成项，并保留在本变更记录中追溯：B-06、B-07、B-08、B-24、B-25、B-42、B-117、B-118、B-119、B-125、B-126、B-128、B-133、B-134、B-135、B-136、B-137、B-139、B-140、B-141、B-142、B-143、B-144、B-145、B-146、B-147、B-148；未完成项、`doing` 项和 `wontfix` legacy 项继续留在 BACKLOG。
- **静态前端托管策略**：FastAPI 只服务 Vite 构建产物；构建产物缺失时明确失败，不再回退 legacy static
- **SSE 服务端外壳**：`/api/answer/stream` 改由 FastAPI `StreamingResponse` 输出，继续保持 `token/done/answer_error` 事件协议
- **测试覆盖补充**：新增增量导入无变更统计、中文关键词召回、`list_by_ids` 批量加载和 Markdown 代码块分块专项测试
- **问答取消机制**：前端问答从 `fetch AbortController` 调整为关闭当前 EventSource 流，保留取消按钮和取消状态提示
- **关键词检索评分**：Web MVP 关键词召回从 regex 词频累加改为内置 BM25 评分，降低重复常见词压过稀有命中的风险
- **向量检索路径**：启用 Qdrant 时不再查询时全量遍历 SQLite `chunk_vectors`；默认和降级路径继续使用 SQLite 兼容副本
- **API 路由拆分蓝图**：补充 `api.py` 按领域拆分方案，明确后续迁移到领域路由时保持 HTTP 契约和 `dispatch()` 入口不变
- **API 路由拆分实施**：新增领域 route registry，完成 health、projects、settings、documents、imports、search、chat、answers、agent、assessment、export 全组迁移；B-155 后兼容入口位于 `backend/api/dispatch.py`

### Fixed
- **Docker 前端构建产物**：Docker 镜像构建阶段会生成并内置 `backend/static_dist/`，避免宿主机未预构建或旧产物导致容器缺少前端。
- **大项目向量检索线性变慢**：B-134 提供 Qdrant HNSW 候选检索路径，解决大型项目查询时 SQLite 向量全扫描的性能瓶颈。

### Security
- B-132 网页抓取预览只接受公开 `http/https`，拒绝凭据、非标准端口、localhost、私网、链路本地、保留地址和重定向后的非公网目标，并遵守 robots.txt、响应大小上限、超时和 content-type allowlist
- 认证启用时，`/api/health` 和静态首页保持放行；其他受保护接口缺少凭证返回 401，凭证错误或过期返回 401，不回显认证密钥

---

## [v0.9.0] - 2026-05-25

### Added
- **导入批次历史**：导入目录、文件上传、文本笔记、URL 摘录后写入 `import_batches` / `import_batch_items`；资料库页可查看最近批次、跳过明细和读取失败明细
- **文档集合分组**：资料库页可创建文档集合，把文档加入或移出集合，并按全部 / 未分组 / 指定集合过滤；删除集合不删除文档
- **模型 Profile 多配置**：设置页可保存多个 provider / API 地址 / 模型名组合并选择默认 Profile；Profile 只保存 Key 引用（`env:*` / `saved:*`），不保存 API Key 明文
- **项目级 Prompt 预设**：设置页可为当前项目空间新增、编辑、删除 Prompt 预设并设置默认；真实 LLM prompt 会在固定来源约束后注入预设的 `system_prompt` / `answer_format`
- **Markdown 渲染 + 代码语法高亮**：回答区通过 CDN 接入 `marked.js` + `DOMPurify` + `highlight.js`，支持标题、列表、代码块和语法高亮；库不可用时回退纯文本
- **问答请求取消**：提问等待期间前端通过 `AbortController` 显示"取消"按钮，中止当前浏览器请求并恢复按钮状态；不改变 `/api/answer` 契约
- **前端全局错误边界**：监听 `window.onerror` + `unhandledrejection`，未捕获异常显示可恢复提示，避免 SPA 静默空白

### Changed
- legacy 多轮对话：`ConversationRecord` 和 `conversations` 增加 `session_id`；`QueryKnowledgeBaseUseCase` 按同一会话读取最近 3 轮上下文注入 prompt；Web MVP 多会话保持不变
- legacy `SettingsController`：设置保存逻辑从 `MainWindow` 抽离到独立 controller，保留原有字段保存行为

---

## [v0.8.0] - 2026-05-23

### Added
- **多会话聊天**：工作台可新建、切换、改名和删除聊天会话；`/api/answer` 支持按 `session_id` 保存消息并按当前会话读取最近上下文
- **检索复盘**：可把一次检索诊断保存为快照，记录查询参数、命中来源、来源质量和人工备注；支持查看详情和删除
- **Agent 只读工具**：开放 `project_overview` 和 `search_sources` 两个只读工具，每次运行写入 `agent_tool_runs` 审计记录；不开放 shell 或任意文件写入
- **工具建议与手动运行**：来源不足时回答区显示建议工具按钮，用户明确点击后才运行 `search_sources`，不自动执行
- **工具来源回填**：用户运行 `search_sources` 后，下一轮 `/api/answer` 可通过 `tool_run_id` 合并工具命中来源
- **备份导出与恢复（第一版）**：可导出当前项目元数据、文档列表和聊天记录；可把同版本备份恢复为新项目空间；第一版不含文档正文、chunk/vector 或 API Key
- **回答质量反馈**：回答下方可标记"有用 / 无用 / 来源不准 / 需要更多上下文"，保存到本地 `answer_feedback` 表，不调用外部服务
- **检索调试**：工作台可临时调整 `top_k`、最低分、关键词/向量开关，查看命中 chunk、分数、来源质量和上下文预览；参数不持久化
- **来源质量提示**：回答返回 `source_quality`，用于提示来源较充分、来源偏少或没有可用来源
- **项目健康概览**：资料库页展示文档、chunk、向量、聊天、工具运行、检索复盘数量和最近活动时间
- **项目级检索默认值**：当前项目可保存 `top_k`、最低分、关键词/向量开关，问答和检索诊断共用这组设置
- **文本笔记导入**：资料库页可把标题和正文作为 `note:` 虚拟来源写入当前项目空间；同标题再次导入只更新原记录
- **URL 摘录导入**：可保存 URL、标题和人工粘贴正文为 `url:` 虚拟来源；第一版不自动抓取网页
- **文件上传导入**：资料库新增浏览器文件选择入口，可一次上传一个或多个文件
- **聊天记录管理**：支持删除单条或清空当前项目聊天记录，前端删除前二次确认
- **导入预检**：`GET /api/import/preview` 预估可导入文件数、跳过数和跳过原因，不写入文档

### Changed
- 模型设置页：连接测试失败时针对 API Key 未配置、鉴权失败、服务连接失败分类显示更具体的恢复提示
- 资料库导入状态说明：跳过文件改为"未导入"，导入错误改为"读取失败"，降低跳过与失败混淆

---

## [v0.7.0] - 2026-05-21

### Added
- **Web MVP 首版**：基于 Python 标准库 HTTP 服务 + SQLite + 原生 HTML/CSS/JS，默认监听 `http://127.0.0.1:8765`；不新增必需运行时依赖
- **项目空间管理**：创建、切换、改名、删除项目空间；前端记住最近选中项目并在刷新后恢复
- **本地目录导入**：支持文本文件、DOCX 正文抽取（标准库解包）、PDF 可选解析（`pymupdf`，未安装时明确跳过）
- **浏览器文件夹导入**：通过 `webkitdirectory` 选择本地项目文件夹，无需后端访问本机路径，适合 Docker 模式
- **RAG 分块检索**：导入时生成 `document_chunks` 和 `chunk_vectors`；搜索使用关键词 + 向量混合召回
- **真实 Embedding 接入**：配置 `RAG_EMBED_PROVIDER=api` 后请求 OpenAI-compatible `/embeddings`；失败时回退本地 hashing 向量
- **真实 LLM 问答**：配置 DeepSeek / OpenAI-compatible 后 `/api/answer` 优先使用真实模型；失败时回退本地片段回答
- **多轮上下文**：真实 LLM 请求最多带入同项目最近 3 轮问答历史
- **聊天记录持久化**：`/api/answer` 成功后保存 question/answer/mode/provider/sources；刷新后可按项目恢复对话
- **Agent 只读工具（第一批）**：开放 `project_overview` 工具，返回文档/chunk/向量/聊天统计，写入 `agent_tool_runs` 审计
- **掌握评估入口**：从已导入文档生成最小评估题，提交回答后返回状态、得分、命中要点和建议阅读来源
- **模型设置页**：可通过 UI 配置 API Base、模型名和 API Key；支持连接测试，不回显 Key 明文
- **首次使用引导**：首屏覆盖创建项目空间、导入目录、提问/评估、配置模型四个步骤
- **Docker 一键启动**：`Dockerfile` + `compose.yaml` + `scripts/docker_up.ps1`；透传 `DEEPSEEK_API_KEY` 和 `RAG_EMBED_*`
- **Docker 双击入口**：`Start-KnowledgeIsland-Docker.bat` / `Stop-KnowledgeIsland-Docker.bat`，面向非技术用户

### Changed
- 默认入口从 PySide6 桌面端切换为本地 Web MVP（`app.py` → `webapp.server.run_server()`）；旧桌面端保留为 legacy

---

## 编写规则

1. 一次发布写一个版本块；未发布内容统一写到 `[Unreleased]`
2. 只记录对使用者 / 维护者有意义的变更，开发过程细节写 `docs/devlog/`
3. 每条尽量写"结果"，不写"做了什么"（✅ 新增文档集合分组 / ❌ 增加了 document_collections 表）
4. 破坏性变更在条目开头标 **BREAKING**；弃用项注明替代方案

## 预发布检查清单

**发布前整体检查**以 `docs/guides/release-process.md § 1` 为权威源；本节只列与 CHANGELOG 相关的补充项：

- [ ] `[Unreleased]` 段至少有一个条目（否则不应发版）
- [ ] 每条属于正确分类：Added / Changed / Fixed / Removed / Security
- [ ] 每条是"结果"描述，不是"做了什么"
- [ ] 破坏性变更已标 **BREAKING**
- [ ] 弃用项已注明替代方案和下线时间
- [ ] 发版后将 `[Unreleased]` 整段迁移为新版本块，`[Unreleased]` 重置为空模板
