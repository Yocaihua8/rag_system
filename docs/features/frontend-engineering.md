# 前端工程化

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-02
> Scope：B-141 Vue 3 + Vite 前端工程化（已完成 A-Z 页面级迁移收口）；B-142 Vue 工作台 SSE 与会话历史迁移（已完成）；B-143 legacy 静态前端 fallback 移除（已完成）；B-42 知识库辅助管理页（已完成）；B-128 对话分支与历史消息编辑重发；B-145 Tauri 桌面壳复用 Vue 构建产物；B-151 前端 Vitest 单元测试；B-156 第二阶段前端简洁化重设计
> Related：docs/adr/ADR-006-vue-vite-frontend.md, docs/design/architecture-overview.md, docs/features/desktop-packaging.md, docs/guides/setup.md, docs/guides/testing.md, docs/BACKLOG.md

## 1. 功能定位

B-141 是 Web 前端技术栈迁移，不新增后端业务能力。目标是把 legacy 原生 HTML/CSS/JS 前端逐步迁移到独立 `frontend/` 工程，使用 Vue 3 组件和 Vite 构建，降低大型单页脚本继续增长带来的维护成本。B-141 收口时已完成 A-Z 页面级迁移薄片；Workbench SSE/取消和聊天会话/历史已由 B-142 接入 Vue 工作台。

B-142 的目标是让 Vue 工作台覆盖 legacy 工作台主流程：采用左侧项目/会话、中间对话、右侧上下文的工作台结构，接入既有 `/api/answer/stream`、`/api/chat/sessions*` 和 `/api/chat/messages` 契约。B-142 不修改后端 API、不修改 SQLite schema、不扩大 Agent 工具权限；legacy static 删除已由 B-143 单独完成。

B-128 在 B-142 工作台基础上增加历史消息“编辑重发”入口。前端只把被编辑消息 ID 作为 `parentMessageId` 传给既有问答 helper，不在前端计算分支序号、不改写原消息；后端负责校验父消息归属和写入 `parent_message_id / branch_index`。

B-156 将 Vue 前端从迁移期四个并列一级页面收束为 `聊 / 库 / 设` 主线：默认进入聊天工作台，工作区和线程统一在左侧侧栏；`库` 改为资料管理弹窗；`设` 改为全屏覆盖页；独立 `评估/练习` 入口收进聊天输入框工具菜单。B-156 不修改后端 API、不修改 SQLite schema、不扩大 Agent 工具权限，也不伪造当前后端尚未提供的全局资料库或跨工作区连接接口。

B-143 已收口前端交付边界：删除 legacy 原生前端，`backend/api/server.py` 只服务 Vue/Vite 构建产物；B-155 后构建产物位于 `backend/static_dist/`。B-143 不修改后端 API、不修改 SQLite schema、不扩大 Agent 工具权限。

B-42 在 Vue 资料库页顶部提供知识库辅助管理概览。它复用当前资料库已有文档列表、导入批次和项目空间状态，同时新增只读项目摘要 helper 与评估题库 helper，用于展示项目状态、检索健康、摄入进度、文件列表、评估题库和最近结果。B-42 不新增数据库表、不改变导入/检索/评分算法，也不把后端业务规则写入前端。

## 2. 用户可见行为

- 默认访问地址仍为 `http://127.0.0.1:8765`。
- `/api/*` 请求路径、请求字段、响应字段和错误格式保持兼容。
- B-141A 只提供前端工程骨架和构建链，不替换完整业务 UI。
- B-141B 提供 Vue API client、共享状态模型和四个基础视图壳，不替换完整业务 UI。
- B-141C 在 Vue 资料库视图中提供项目空间列表、当前项目选择、最近项目恢复和新建项目空间。
- B-141D 在 Vue 工作台中提供非流式问答入口，复用既有 `POST /api/answer`，展示回答、来源和来源质量摘要。
- B-141E 在 Vue 资料库视图中提供当前项目文档列表和单文档正文预览，复用既有 `GET /api/documents` 与 `GET /api/document` 契约。
- B-141F 在 Vue 资料库视图中提供文本笔记导入和 URL 摘录导入，复用既有 `POST /api/import/note` 与 `POST /api/import/url` 契约。
- B-141G 在 Vue 资料库视图中提供导入批次历史和批次详情只读展示，复用既有 `GET /api/import/batches` 与 `GET /api/import/batches/detail` 契约。
- B-141H 在 Vue 资料库视图中提供普通文件上传导入，复用既有 `POST /api/import/upload` 契约；有当前项目空间时导入当前项目，没有项目空间时由后端创建 `browser-upload` 项目。
- B-141I 在 Vue 资料库视图中提供浏览器文件夹上传导入，复用既有 `POST /api/import/upload` 契约；前端用 `webkitRelativePath` 推导项目名和文档相对路径，并发送 `source_type=browser_folder_upload`。
- B-141J 在 Vue 资料库视图中提供当前项目目录同步入口，复用既有 `POST /api/import` 契约；后端继续负责项目根目录校验、导入规则和 `directory_sync` 批次记录。
- B-141K 在 Vue 资料库视图中提供当前项目目录导入预检入口，复用既有 `GET /api/import/preview` 只读契约；预检只展示可导入数、跳过数和跳过原因，不创建导入批次。
- B-141L 在 Vue 资料库视图中提供文档集合只读筛选入口，复用既有 `GET /api/document-collections` 与 `GET /api/documents?collection_id=...` 契约；当前只迁移全部/未分组/指定集合过滤，不迁移集合编辑或加入/移出文档。
- B-141M 在 Vue 资料库视图中提供文档集合新建和删除入口，复用既有 `POST /api/document-collections` 与 `POST /api/document-collections/delete` 契约；删除集合不删除文档，当前不迁移集合重命名或加入/移出文档。
- B-141N 在 Vue 资料库视图中提供文档集合重命名入口，复用既有 `POST /api/document-collections/update` 契约；当前不迁移加入/移出文档。
- B-141O 在 Vue 资料库文档列表中提供单文档加入集合和从当前集合移出入口，复用既有 `POST /api/document-collections/items/add` 与 `POST /api/document-collections/items/remove` 契约；当前不迁移批量选择、拖拽或删除文档。
- B-141P 在 Vue 资料库文档列表中提供单文档删除入口，复用既有 `POST /api/documents/delete` 契约；删除前提示源文件不会被删除，成功后刷新文档列表和文档集合列表。
- B-141Q 在 Vue 资料库项目空间面板中提供当前项目改名和删除入口，复用既有 `POST /api/projects/rename` 与 `POST /api/projects/delete` 契约；删除前提示项目内文档记录也会被删除，成功后清空当前项目相关状态。
- B-141R 在 Vue 设置视图中提供基础 LLM 设置读取/保存/测试，以及模型 Profile 列表、新建/编辑、删除、默认选择和连接测试入口；复用既有 `GET/POST /api/settings/llm`、`POST /api/settings/llm/test` 与 `/api/model-profiles*` 契约，Profile 只保存 Key 引用，不回显 API Key 明文。
- B-141S 在 Vue 设置视图中提供当前项目 Prompt 预设列表、内置模板复制、新建/编辑、删除、设置默认和清空默认入口；复用既有 `/api/prompt-presets*` 契约，预设只保存回答风格与格式，不保存 API Key。
- B-141T 在 Vue 评估视图中提供掌握评估最小闭环：开始评估、查看当前题目、提交回答、进入下一题/完成评估、查看结果概览、答题记录和待复测列表；复用既有 `/api/assessment/start` 与 `/api/assessment/answer` 契约。
- B-141U 在 Vue 工作台回答返回后提供回答反馈入口，支持“有用 / 无用 / 来源不准 / 需要更多上下文”四类反馈；复用既有 `POST /api/answer/feedback` 契约。
- B-141V 在 Vue 工作台提供检索调试入口，支持提交诊断查询、临时调整 `top_k` / `min_score` / 关键词 / 向量参数，并展示来源质量、文档/分块数量、向量可用状态、本次参数和命中片段；复用既有 `POST /api/search/debug` 契约。
- B-141W 在 Vue 工作台提供 Agent 只读工具面板，支持查看工具元数据、手动运行 `project_overview` / `search_sources`、展示工具结果、运行历史和单条详情；复用既有 `/api/agent/tools*` 契约。
- B-141X 在 Vue 工作台提供回答区工具建议与工具来源上下文闭环，支持展示后端 `tool_suggestion`、手动运行建议的 `search_sources`、把成功工具运行标记为下一问 `tool_run_id`，并在回答完成后展示 `tool_context`；复用既有 `/api/answer` 与 `/api/agent/tools/run` 契约。
- B-141Y 在 Vue 工作台提供项目级检索默认值读取和保存入口，支持把 `top_k`、`min_score`、关键词和向量开关保存为当前项目默认值；复用既有 `GET/POST /api/projects/retrieval-settings` 契约。
- B-141Z 在 Vue 工作台提供检索复盘入口，支持保存当前查询参数和人工备注，查看当前项目复盘历史、单条详情和删除复盘记录；复用既有 `/api/retrieval/reviews*` 契约。
- B-143 后，legacy static fallback 已删除；Web 首页唯一静态来源是 `backend/static_dist/`。
- B-142 在 Vue 工作台接入 `/api/answer/stream` EventSource 流式输出，支持取消当前请求，完成后刷新回答、来源、来源质量、可观察性、反馈入口、工具建议和当前会话消息。
- B-142 在 Vue 工作台接入 `/api/chat/sessions*` 和 `/api/chat/messages`，支持当前项目内会话列表、新建、重命名、删除、历史恢复、单条消息删除和当前消息清空。
- B-142 将 Vue 工作台信息架构调整为左侧会话、中间对话、右侧上下文；检索调试、检索复盘和 Agent 只读工具收敛到右侧上下文栏，不再与问答主流程同级抢占首屏。
- B-128 在 Vue 工作台历史消息上提供“编辑重发”，提交后通过 `/api/answer/stream` 携带 `parent_message_id` 生成新分支消息，并刷新当前会话消息。
- B-42 在 Vue 资料库页顶部展示知识库辅助管理概览；项目加载、项目切换、导入完成、同步目录、删除文档、开始评估和提交评估回答后，会刷新项目摘要与评估题库只读快照。
- B-156 后，默认首页为 `聊`，左侧 `WorkspaceSidebar` 同时管理工作区和线程；侧栏可收起，小屏默认只保留顶部菜单按钮，点击后以抽屉显示侧栏。
- B-156 后，`库` 不再作为一级普通页面挤压聊天区，而是打开 `LibraryModal`。弹窗包含 `加入库` 和 `选择资料` 两步；上传首屏只展示文件、文件夹、笔记、网页摘录和更多来源，GitHub / Notion / Obsidian 等高级来源收进“更多来源”；选择资料时展示资料夹筛选和资料列表。
- B-156 后，导入结果通过 `ImportResultList` 展示：默认折叠，有导入状态或错误时自动展开。当前导入接口仍以项目空间为边界，前端不显示“已连接到多个工作区”这类伪成功状态。
- B-156 后，回答来源、检索复盘、工具结果和对比回答进入默认收起的 `EvidenceDrawer`，`AnswerPanel` 只保留回答主体和少量反馈操作。
- B-156 后，`设` 是全屏覆盖页，顶部有返回按钮，左侧菜单在 `回答 / 资料 / 外观` 单页之间切换；模型连接字段收进“连接详情”，访问密钥仍不回显明文。
- B-156 后，主界面采用黑白灰中性配色；错误和警告状态保留必要提示色。

## 3. 工程目录

| 路径 | 用途 |
|------|------|
| `frontend/` | Vue 3 + Vite 前端源码 |
| `frontend/src/` | Vue 入口、组件、前端 API 客户端和样式 |
| `frontend/src/api/client.js` | Vue 前端 API helper，封装 `apiGet` / `apiPost` 与错误归一化 |
| `frontend/src/api/projects.js` | Vue 项目空间 API helper，封装项目列表、创建、选择、最近项目恢复、改名、删除、项目摘要和项目级检索默认值读取/保存 |
| `frontend/src/api/answer.js` | Vue 工作台非流式问答、SSE 流式问答、聊天会话/消息、工具上下文、对话分支和回答反馈 API helper，调用既有 `/api/answer`、`/api/answer/stream`、`/api/chat/*` 与 `/api/answer/feedback` |
| `frontend/src/api/search.js` | Vue 工作台检索调试和检索复盘 API helper，调用既有 `/api/search/debug` 与 `/api/retrieval/reviews*` 契约 |
| `frontend/src/api/agent.js` | Vue 工作台 Agent 工具 API helper，调用既有 `/api/agent/tools*` 契约 |
| `frontend/src/api/documents.js` | Vue 资料库文档 API helper，调用既有 `/api/documents`、`/api/document` 和 `/api/documents/delete` |
| `frontend/src/api/document-collections.js` | Vue 资料库文档集合 API helper，调用既有 `/api/document-collections` 列表/新建契约、`/api/document-collections/update` 重命名契约、`/api/document-collections/delete` 删除契约和 `/api/document-collections/items/*` 文档关联契约 |
| `frontend/src/api/imports.js` | Vue 资料库导入 API helper，调用既有 `/api/import/preview`、`/api/import`、`/api/import/note`、`/api/import/url`、`/api/import/upload`、`/api/import/batches` 和 `/api/import/batches/detail` |
| `frontend/src/api/settings.js` | Vue 设置页模型配置和 Prompt 预设 API helper，调用既有 `/api/settings/llm`、`/api/settings/llm/test`、`/api/model-profiles*` 和 `/api/prompt-presets*` 契约 |
| `frontend/src/api/assessment.js` | Vue 评估页 API helper，调用既有 `/api/assessment/start`、`/api/assessment/answer` 和只读 `/api/assessment/library` 契约 |
| `frontend/src/state/app-state.js` | Vue 迁移期共享状态模型和基础视图切换 |
| `frontend/src/components/` | 布局和业务组件，例如 `AppShell.vue`、`WorkspaceSidebar.vue`、`QuestionComposer.vue`、`ChatThread.vue`、`AnswerPanel.vue`、`EvidenceDrawer.vue`、`LibraryModal.vue`、`ImportResultList.vue`、`SearchDebugPanel.vue`、`AgentToolsPanel.vue`、`KnowledgeBaseManagementPanel.vue`、`DocumentListPanel.vue`、`DocumentPreviewPanel.vue`、`DocumentImportPanel.vue`、`DocumentCollectionPanel.vue`、`ImportBatchHistoryPanel.vue` |
| `frontend/src/views/` | 当前一级视图为 `聊` 和 `设`；资料库、评估等视图组件保留给弹窗、抽屉或后续复用 |
| `frontend/src/**/*.test.js` | B-151 起的 Vitest 单元测试，覆盖 API helper 和关键组件状态 |
| `backend/static_dist/` | Vite 生产构建输出，由 FastAPI 托管 |
| `src-tauri/` | Tauri 2 桌面壳；WebView 加载 `backend/static_dist/`，FastAPI 以 sidecar 方式运行 |
| legacy static | 已由 B-143 删除；不再作为 fallback 或生产入口 |

B-142 完成后，`frontend/src/api/answer.js` 继续保留非流式 `POST /api/answer` helper，同时补充 EventSource stream helper 和聊天会话 helper。工作台通过 `ChatSessionPanel`、`ChatThread` 和 `QuestionComposer` 承载会话列表、对话流、输入区和右侧上下文栏；这些组件只调用既有 API，不把检索、回答或权限业务规则写入前端。

B-128 完成后，`ChatThread` 在每条历史消息上提供“编辑重发”按钮；`App.vue` 使用原问题预填浏览器编辑框，确认后调用 `askQuestionStream({ parentMessageId })`。分支归属校验、分支序号和数据库写入均由后端完成。

Docker 镜像构建时会在 Node 构建阶段执行 `npm ci && npm run build`，并把生成的 `backend/static_dist/` 复制到最终 Python 运行镜像。Docker 模式不依赖宿主机预先执行 `npm run build`；本地直接运行 `python app.py` 时必须先生成 Vue 构建产物，缺失 `backend/static_dist/index.html` 会在启动阶段报错，不再回退 legacy UI。

B-145 起，Tauri Windows 桌面壳也复用 Vue/Vite 生产构建产物。B-155 后 `src-tauri/tauri.conf.json` 的 `frontendDist` 指向 `../backend/static_dist`，`scripts/build-backend-sidecar.ps1` 会在 PyInstaller 打包 FastAPI sidecar 前执行 `npm run build`。桌面模式不改变 `/api/*` 契约，也不把前端业务规则写入 Tauri 壳。

## 4. 非目标

- 不在 B-141A/B-141B/B-141C/B-141D/B-141E/B-141F/B-141G/B-141H/B-141I/B-141J/B-141K/B-141L/B-141M/B-141N/B-141O/B-141P/B-141Q/B-141R/B-141S/B-141T/B-141U/B-141V/B-141W/B-141X/B-141Y/B-141Z 迁移完整业务页面。
- B-141C 不迁移导入、重命名、删除、文档列表、问答、评估或设置完整流程。
- B-141D 不迁移 SSE 流式输出、取消、聊天会话/历史、回答反馈、Agent 工具或检索调试。
- B-141E 不迁移文件导入、目录同步、上传、笔记、URL 摘录、删除文档、文档集合增删改或导入批次历史。
- B-141F 不迁移目录同步、浏览器文件夹上传、普通文件上传、导入预检、删除文档、文档集合增删改或导入批次历史。
- B-141G 不迁移目录同步、浏览器文件夹上传、普通文件上传、导入预检、批次回滚、批次删除、批次重试、删除文档或文档集合增删改。
- B-141H 不迁移浏览器文件夹上传、同步当前项目目录、导入预检、删除文档、文档集合增删改或数据库 schema。
- B-141I 不迁移同步当前项目目录、导入预检、删除文档、文档集合增删改或数据库 schema。
- B-141J 不迁移导入预检、删除文档、文档集合增删改、项目改名/删除或数据库 schema。
- B-141K 不执行导入、不创建导入批次、不迁移删除文档、文档集合增删改、项目改名/删除或数据库 schema。
- B-141L 不迁移文档集合新建、编辑、删除、加入文档、移出文档、删除文档、项目改名/删除或数据库 schema。
- B-141M 不迁移文档集合重命名、加入文档、移出文档、删除文档、项目改名/删除或数据库 schema。
- B-141N 不迁移文档加入集合、移出集合、删除文档、项目改名/删除或数据库 schema。
- B-141O 不迁移批量选择、拖拽排序、删除文档、项目改名/删除、问答按集合过滤或数据库 schema。
- B-141P 不迁移批量删除、删除源文件、项目改名/删除、问答按集合过滤或数据库 schema。
- B-141Q 不迁移项目根目录修改、批量项目管理、备份恢复、Workbench SSE/会话、设置页模型配置或数据库 schema。
- B-141R 不迁移 Prompt 预设、Workbench SSE/会话、项目根目录修改、批量项目管理、模型配置导入导出、模型测速/价格统计或数据库 schema。
- B-141S 不迁移 Workbench SSE/会话、评估页、真实 LLM prompt 注入逻辑、项目根目录修改、批量项目管理、模型配置导入导出或数据库 schema。
- B-141T 不迁移评估题库管理、历史评估列表、回答反馈、知识点画像、Workbench SSE/会话或数据库 schema。
- B-141U 不迁移回答反馈备注输入、Workbench SSE/取消、聊天会话/历史、Agent 工具、检索调试或数据库 schema。
- B-141V 不迁移项目级检索默认值保存、检索复盘保存/列表/详情/删除、普通搜索结果、Workbench SSE/取消、聊天会话/历史、Agent 工具、检索算法或数据库 schema。
- B-141W 不迁移回答区工具建议按钮、工具来源回填到下一问、Workbench SSE/取消、聊天会话/历史、Agent 自动编排、工具白名单权限逻辑、后端 API 或数据库 schema。
- B-141X 不迁移 Workbench SSE/取消、聊天会话/历史、Agent 自动编排、工具白名单权限逻辑、检索复盘、后端 API 或数据库 schema。
- B-141Y 不迁移检索复盘保存/列表/详情/删除、普通搜索结果列表、Workbench SSE/取消、聊天会话/历史、检索算法、后端 API 或数据库 schema。
- B-141Z 不迁移普通搜索结果列表、检索健康项目卡、Workbench SSE/取消、聊天会话/历史、评估题库/历史、检索算法、后端 API 或数据库 schema。
- B-42 不迁移批量文档操作、文件夹树、评估题目编辑/删除/手工创建、跨刷新评估会话恢复、实时导入进度或数据库 schema。
- Workbench SSE/取消和聊天会话/历史已拆为 B-142，不作为 B-141 完成条件。
- B-141/B-142 不删除 legacy static；删除动作已由 B-143 单独执行。
- 不修改 SQLite schema。
- 不改变 Agent 工具权限边界。
- 不新增前端登录页；认证启用后的凭证 UI 后续另拆。

## 5. 架构落点

Vue 3 + Vite 只替代展示层工程组织。B-155 后后端由 `backend/api/server.py` 提供 FastAPI 服务，`backend/api/dispatch.py` 和 `backend/routes/*` 保持 API 契约，业务层和数据层位于 `backend/domain/` 与 `backend/storage/`。

B-141B 起，Vue 侧采用轻量 Composition API 结构：API helper 负责请求和错误归一化，共享状态模块保存当前项目、会话、文档、评估、工具、检索等迁移期字段。B-156 后，`AppShell` 负责 `聊 / 设` 顶层内容容器和侧栏收起状态，`WorkspaceSidebar` 负责 `聊 / 库 / 设` 入口、工作区、线程和资料目标选择。该状态模型只是前端 UI 状态，不新增后端数据规则。

B-141C 起，Vue 资料库视图先迁移项目空间薄片：`projects.js` 只调用既有 `GET /api/projects` 和 `POST /api/projects`，`ProjectSpacePanel` 只展示和提交项目空间状态，不承载导入、文档集合、问答或设置业务规则。

B-141D 起，Vue 工作台先迁移非流式问答薄片：`answer.js` 只调用既有 `POST /api/answer`，`QuestionPanel` 负责问题输入与提交状态，`AnswerPanel` 负责回答、来源和来源质量展示。后端 API、SQLite schema、SSE 流式问答、聊天会话、回答反馈、Agent 工具和检索调试不在本片调整。

B-141E 起，Vue 资料库继续迁移只读文档浏览薄片：`documents.js` 只调用既有 `GET /api/documents` 与 `GET /api/document`，`DocumentListPanel` 负责文档列表、空态和读取状态，`DocumentPreviewPanel` 负责单文档正文预览。文档列表仍不依赖列表响应中的 `content` 字段；正文只来自单文档预览接口。后端 API、SQLite schema、导入、删除、集合管理和批次历史不在本片调整。

B-141F 起，Vue 资料库继续迁移轻量导入薄片：`imports.js` 只调用既有 `POST /api/import/note` 与 `POST /api/import/url`，`DocumentImportPanel` 负责文本笔记和 URL 摘录两个表单、提交状态和错误/成功提示。成功导入后刷新 B-141E 文档列表。后端 API、SQLite schema、目录同步、文件上传、删除、集合管理和批次历史不在本片调整。

B-141G 起，Vue 资料库继续迁移导入批次历史薄片：`imports.js` 扩展只读 `GET /api/import/batches` 与 `GET /api/import/batches/detail` helper，`ImportBatchHistoryPanel` 负责最近批次列表、批次详情、汇总计数以及跳过/读取失败明细展示。文本笔记或 URL 摘录导入成功后会刷新文档列表和导入批次历史。后端 API、SQLite schema、目录同步、文件上传、导入预检、批次回滚/删除/重试和集合管理不在本片调整。

B-141H 起，Vue 资料库继续迁移普通文件上传导入薄片：`imports.js` 扩展 `POST /api/import/upload` helper，普通文件使用文件名作为 `relative_path`，文本文件上传 `content`，DOCX/PDF 上传 `content_base64 + size`。`DocumentImportPanel` 增加普通 `multiple` file input，明确不设置 `webkitdirectory`；`App.vue` 在成功后刷新项目空间、文档列表和导入批次历史。后端 API、SQLite schema、浏览器文件夹上传、同步当前项目目录、导入预检、删除和集合管理不在本片调整。

B-141I 起，Vue 资料库继续迁移浏览器文件夹上传导入薄片：`imports.js` 扩展 `POST /api/import/upload` helper，文件夹入口读取 `webkitRelativePath`，首段作为 `project_name`，其余路径作为文档 `relative_path`，并发送 `source_type=browser_folder_upload`。`DocumentImportPanel` 增加单独的 `webkitdirectory multiple` file input；普通文件上传 input 仍不设置 `webkitdirectory`。`App.vue` 在成功后选择后端返回项目，并刷新项目空间、文档列表和导入批次历史。后端 API、SQLite schema、同步当前项目目录、导入预检、删除和集合管理不在本片调整。

B-141J 起，Vue 资料库继续迁移当前项目目录同步薄片：`imports.js` 扩展 `POST /api/import` helper，`DocumentImportPanel` 增加“同步当前项目目录”按钮，未选择项目空间时禁用。`App.vue` 在成功后刷新文档列表和导入批次历史，并复用导入结果计数展示。后端 API、SQLite schema、导入预检、删除、集合管理和项目改名/删除不在本片调整。

B-141K 起，Vue 资料库继续迁移当前项目目录导入预检薄片：`imports.js` 扩展 `GET /api/import/preview` helper，`DocumentImportPanel` 在本地目录区域增加“预检当前项目目录”按钮和只读结果摘要，展示可导入数、跳过数和跳过原因。`App.vue` 单独保存 `importPreview`、`importPreviewLoading` 和 `importPreviewError`，预检完成后不刷新文档列表、不刷新导入批次历史，也不创建导入批次。后端 API、SQLite schema、删除、集合管理和项目改名/删除不在本片调整。

B-141L 起，Vue 资料库继续迁移文档集合只读筛选薄片：`document-collections.js` 只调用既有 `GET /api/document-collections`，`DocumentCollectionPanel` 展示“全部文档 / 未分组 / 指定集合”筛选、集合列表和集合文档数。`App.vue` 保存集合列表、集合加载状态和当前 `selectedDocumentCollectionId`，选择筛选项后复用 B-141E 的 `listDocuments(projectId, collectionId)` 刷新文档列表。后端 API、SQLite schema、集合新建/编辑/删除、加入/移出文档和删除文档不在本片调整。

B-141M 起，Vue 资料库继续迁移文档集合最小写操作：`document-collections.js` 扩展 `POST /api/document-collections` 和 `POST /api/document-collections/delete` helper，`DocumentCollectionPanel` 提供集合名称输入、新建按钮和删除集合按钮，`App.vue` 在创建或删除后刷新集合列表；删除当前筛选集合时清空筛选并刷新文档列表。后端 API、SQLite schema、集合重命名、加入/移出文档和删除文档不在本片调整。

B-141N 起，Vue 资料库继续迁移文档集合重命名薄片：`document-collections.js` 扩展 `POST /api/document-collections/update` helper，`DocumentCollectionPanel` 提供集合内联重命名入口、保存和取消按钮，`App.vue` 在重命名成功后刷新集合列表。后端 API、SQLite schema、加入/移出文档和删除文档不在本片调整。

B-141O 起，Vue 资料库继续迁移文档集合文档归组薄片：`document-collections.js` 扩展 `POST /api/document-collections/items/add` 与 `POST /api/document-collections/items/remove` helper，`DocumentListPanel` 在每个文档项下提供加入集合选择和当前集合移出按钮，`App.vue` 在成功后刷新集合列表和当前文档列表。后端 API、SQLite schema、批量选择、拖拽、删除文档和问答按集合过滤不在本片调整。

B-141P 起，Vue 资料库继续迁移单文档删除薄片：`documents.js` 扩展 `POST /api/documents/delete` helper，`DocumentListPanel` 在每个文档项下提供“删除文档”按钮，`App.vue` 在删除前弹出确认并提示源文件不会被删除，成功后清空当前预览、刷新文档列表和文档集合列表。后端 API、SQLite schema、批量删除、源文件删除、项目改名/删除和问答按集合过滤不在本片调整。

B-141Q 起，Vue 资料库继续迁移项目空间改名与删除薄片：`projects.js` 扩展 `POST /api/projects/rename` 与 `POST /api/projects/delete` helper，`ProjectSpacePanel` 在当前项目区域提供重命名表单和删除按钮，`App.vue` 在删除前弹出确认并提示项目内文档记录也会被删除，成功后清空当前项目选择、文档列表、预览、集合和导入批次状态。后端 API、SQLite schema、项目根目录修改、批量项目管理、Workbench SSE/会话和设置页模型配置不在本片调整。

B-141R 起，Vue 设置页继续迁移模型配置薄片：`settings.js` 封装既有 `/api/settings/llm`、`/api/settings/llm/test` 和 `/api/model-profiles*` helper，`SettingsView` 提供基础模型设置表单、连接测试、模型 Profile 列表、编辑表单、删除、默认选择和 Profile 测试入口。`App.vue` 保存模型设置/Profile 读取、提交、测试、删除和默认切换状态。Profile 只保存 Key 引用，基础模型设置的 API Key 输入留空时不覆盖既有 Key，页面只展示 Key 状态、不回显明文。后端 API、SQLite schema、Prompt 预设、Workbench SSE/会话和模型配置导入导出不在本片调整。

B-141S 起，Vue 设置页继续迁移项目级 Prompt 预设薄片：`settings.js` 扩展 `/api/prompt-presets*` helper，`SettingsView` 提供当前项目预设列表、默认预设状态、内置模板复制、编辑表单、删除、设置默认和清空默认入口。`App.vue` 在项目切换、创建、删除和刷新设置时同步读取 Prompt 预设，并保存读取、提交、删除和默认切换状态。后端 API、SQLite schema、真实 LLM prompt 注入逻辑、Workbench SSE/会话和评估页不在本片调整。

B-141T 起，Vue 评估页迁移掌握评估最小闭环：`assessment.js` 封装既有 `/api/assessment/start` 和 `/api/assessment/answer` helper，`AssessmentView` 提供开始/重置评估、当前题目、作答提交、下一题/完成、结果概览、答题记录和待复测列表。`App.vue` 保存评估会话、当前题目、题目序号、答题结果、待复测项、加载/提交状态和项目切换清理逻辑。后端 API、SQLite schema、评估题库管理、回答反馈和 Workbench SSE/会话不在本片调整。

B-141U 起，Vue 工作台迁移回答反馈薄片：`answer.js` 扩展 `POST /api/answer/feedback` helper，`AnswerPanel` 在回答返回且存在 `message.id` 时展示四类反馈按钮，`App.vue` 保存最后回答消息 ID、反馈提交状态、错误和保存提示。后端 API、SQLite schema、反馈备注输入、Workbench SSE/取消、聊天会话/历史、Agent 工具和检索调试不在本片调整。

B-141V 起，Vue 工作台迁移检索调试薄片：`search.js` 封装既有 `POST /api/search/debug` helper，`SearchDebugPanel` 提供诊断查询、`top_k`、`min_score`、关键词和向量开关，并展示来源质量、文档/分块数量、向量可用状态、本次参数和命中片段。`App.vue` 保存检索诊断结果、提交状态、错误和完成提示。后端 API、SQLite schema、项目级检索默认值保存、检索复盘、普通搜索结果、Workbench SSE/取消、聊天会话/历史和 Agent 工具不在本片调整。

B-141W 起，Vue 工作台迁移 Agent 只读工具薄片：`agent.js` 封装既有 `GET /api/agent/tools`、`POST /api/agent/tools/run`、`GET /api/agent/tools/runs` 和 `GET /api/agent/tools/runs/detail` helper，`AgentToolsPanel` 展示只读工具元数据、手动运行 `project_overview` / `search_sources`、工具结果、运行历史和单条详情。`App.vue` 保存工具元数据、运行结果、运行历史、详情、提交状态和错误。后端 API、SQLite schema、工具白名单权限、工具建议自动运行、工具来源回填、Workbench SSE/取消和聊天会话/历史不在本片调整。

B-141X 起，Vue 工作台迁移工具建议与来源上下文薄片：`answer.js` 在既有 `/api/answer` 请求中可选携带 `tool_run_id`，`AnswerPanel` 展示 `tool_suggestion`、可用 `search_sources` 工具结果、下一问上下文提示和本轮 `tool_context`。`App.vue` 只在用户点击后运行建议工具，不自动执行 Agent 工具；用户显式点击“使用工具结果作为下一问上下文”后，下一次非流式问答才发送 `tool_run_id`，回答完成后消耗该上下文。后端 API、SQLite schema、SSE/取消、聊天会话/历史、Agent 自动编排和工具白名单权限不在本片调整。

B-141Y 起，Vue 工作台迁移项目级检索默认值薄片：`projects.js` 扩展既有 `GET/POST /api/projects/retrieval-settings` helper，`SearchDebugPanel` 根据已加载默认值回填 `top_k`、`min_score`、关键词和向量控件，并提供“保存为默认”入口。`App.vue` 在项目加载、切换和创建后读取当前项目默认值，保存成功后更新当前面板状态。后端 API、SQLite schema、检索复盘、普通搜索结果、SSE/取消和聊天会话/历史不在本片调整。

B-141Z 起，Vue 工作台迁移检索复盘薄片：`search.js` 扩展既有 `POST/GET /api/retrieval/reviews`、`GET /api/retrieval/reviews/detail` 和 `POST /api/retrieval/reviews/delete` helper，`SearchDebugPanel` 在检索调试区提供复盘备注、保存复盘、复盘历史、详情和删除入口。`App.vue` 在项目加载、切换和创建后读取当前项目复盘列表，保存成功后刷新列表，详情读取失败只影响详情区域。后端 API、SQLite schema、普通搜索结果、SSE/取消和聊天会话/历史不在本片调整。

B-42 起，Vue 资料库页顶部挂载 `KnowledgeBaseManagementPanel`：`projects.js` 通过 `getProjectSummary(projectId)` 读取 `/api/projects/summary`，`assessment.js` 通过 `loadAssessmentLibrary(projectId)` 读取 `/api/assessment/library`。`App.vue` 保存 `projectSummary`、`assessmentLibrary` 及其 loading/error 状态，并在项目加载、切换、创建、导入、同步、删除文档和评估状态变化后刷新概览。组件只展示只读聚合信息，不执行导入、检索、评分或题目生成。

B-151 起，前端新增 Vitest + jsdom 单元测试层。`frontend/src/api/*.test.js` 覆盖 `apiGet/apiPost` 的 JSON 请求、HTTP/非 JSON/网络错误归一化，各业务 helper 的参数校验、URL/payload 构造、SSE EventSource 处理和浏览器文件上传 payload 转换；`frontend/src/components/*.test.js` 覆盖 `AnswerPanel`、`ProjectSpacePanel`、`QuestionComposer` 的 loading/error/disabled/emit 等组件状态。Vitest 只测纯前端逻辑和组件状态，不替代 Playwright E2E 的导入、检索、问答主流程。

## 6. 验收标准

- `frontend/` 存在最小 Vue 3 + Vite 工程。
- Vue 前端存在 `apiGet` / `apiPost`、共享状态模型、`聊 / 设` 当前一级视图、资料管理弹窗、资料库历史能力组件、评估历史能力组件、资料库项目空间选择/创建/改名/删除薄片、资料库文档列表/预览/删除薄片、资料库文本/URL 导入薄片、资料库导入批次历史薄片、资料库普通文件上传薄片、资料库浏览器文件夹上传薄片、资料库当前目录同步薄片、资料库导入预检薄片、资料库文档集合只读筛选/新建/删除/重命名/加入/移出薄片、设置页模型设置/Profile/Prompt 预设薄片、评估页最小闭环，以及工作台非流式问答、回答反馈、检索调试、项目级检索默认值、检索复盘、Agent 只读工具和工具来源上下文入口。
- Vue 工作台可在已选择项目空间时提交问题到既有 `/api/answer`，并展示回答、来源、模型模式和来源质量摘要。
- Vue 工作台可在回答返回后提交“有用 / 无用 / 来源不准 / 需要更多上下文”四类本地反馈。
- Vue 工作台可在已选择项目空间时提交检索诊断查询，临时调整 `top_k` / `min_score` / 关键词 / 向量参数，并展示来源质量、分块状态和命中片段。
- Vue 工作台可读取当前项目的检索默认值，调整 `top_k` / `min_score` / 关键词 / 向量参数后保存为当前项目默认值。
- Vue 工作台可保存当前查询的检索复盘，查看当前项目复盘历史、单条详情和删除复盘记录。
- Vue 工作台可在已选择项目空间时查看 Agent 只读工具元数据，手动运行 `project_overview` / `search_sources`，并展示工具结果、运行历史和单条详情。
- Vue 工作台可在回答来源不足时展示建议工具，用户手动运行 `search_sources` 后可把工具结果标记为下一问上下文，并在下一次 `/api/answer` 中发送 `tool_run_id`。
- Vue 默认首页可直接进入 `聊`，左侧侧栏同时管理工作区和线程；移动端默认隐藏侧栏，顶部菜单按钮可打开侧栏抽屉。
- `库` 入口打开资料管理弹窗，不作为一级普通页面；弹窗支持先加入库、再选择资料两个步骤，选择资料时可查看资料夹筛选和资料列表，并把高级来源和导入结果收起。
- 独立一级 `评估/练习` 入口已取消；练习与小测从聊天输入框左下角工具菜单进入。
- `设` 入口打开全屏设置页，左侧菜单一次只显示一个设置页面。
- Vue 资料库可在已选择项目空间时读取文档列表，并通过单文档预览接口展示正文。
- Vue 资料库可在已选择项目空间时提交文本笔记或 URL 摘录导入，并在成功后刷新文档列表。
- Vue 资料库可在已选择项目空间时读取导入批次历史，点击批次后查看只读详情、汇总计数和跳过/读取失败明细。
- Vue 资料库可选择一个或多个普通文件上传；有当前项目空间时导入当前项目，没有项目空间时由后端创建 `browser-upload` 项目。
- Vue 资料库可通过浏览器文件夹选择导入本机文件夹；前端不读取原始宿主机绝对路径，只上传授权文件内容和相对路径。
- Vue 资料库可在已选择项目空间时同步当前项目目录；未选择项目空间时同步入口禁用。
- Vue 资料库可在已选择项目空间时预检当前项目目录，展示可导入数、跳过数和跳过原因；预检不会写入文档或导入批次。
- Vue 资料库可在已选择项目空间时读取文档集合，并按全部、未分组或指定集合过滤文档列表。
- Vue 资料库可在已选择项目空间时新建或删除文档集合；删除集合会提示“集合内文档不会被删除”，并在删除当前筛选集合后回到全部文档。
- Vue 资料库可在已选择项目空间时重命名已有文档集合，并在成功后刷新集合列表。
- Vue 资料库可在文档列表中将单个文档加入指定集合，并在筛选到指定集合时把单个文档从当前集合移出；成功后刷新集合列表和当前文档列表。
- Vue 资料库可在文档列表中删除单个文档记录；删除前提示源文件不会被删除，成功后刷新文档列表和文档集合列表。
- Vue 资料库可在项目空间面板中改名当前项目空间，成功后刷新项目列表并保持当前项目选中。
- Vue 资料库可在项目空间面板中删除当前项目空间；删除前提示项目内文档记录也会被删除，成功后清空当前项目相关状态。
- Vue 资料库顶部可展示知识库辅助管理概览，包括项目状态、检索健康、摄入进度、文件列表、评估题库和最近结果；未选择项目、无文档、无导入批次和无评估题目时有明确空态。
- Vue 设置页可读取、保存和测试基础模型设置；API Key 输入留空不覆盖既有 Key，页面不回显明文 Key。
- Vue 设置页可读取模型 Profile 列表，新增或编辑 Profile，删除 Profile，设置或清空默认 Profile，并测试单个 Profile。
- Vue 设置页可在已选择项目空间时读取 Prompt 预设和内置模板，新增或编辑 Prompt 预设，删除 Prompt 预设，设置或清空默认 Prompt 预设。
- Vue 评估页可在已选择项目空间时开始评估、查看当前题目、提交回答、进入下一题或完成本轮，并查看结果概览、答题记录和待复测列表。
- `npm run build` 可生成 `backend/static_dist/`。
- `npm run test:unit` 可运行前端 Vitest 单元测试，并覆盖 API helper 请求/错误归一化和关键组件状态。
- FastAPI 只服务 `backend/static_dist/`；构建产物不存在时明确失败，不回退 legacy 静态目录。
- Tauri 桌面壳可复用 `backend/static_dist/` 作为 WebView 前端；完整 Windows 打包入口见 `docs/features/desktop-packaging.md`。
- Docker 镜像构建会内置生成 Vue/Vite 生产产物，容器启动后展示 `backend/static_dist/` 中的前端。
- Web MVP 后端测试保持通过。
- 文档说明清楚 legacy static 已由 B-143 删除，不再作为 fallback 保留。
- B-142 收口后，Vue 工作台已覆盖流式问答、取消、会话历史和消息管理；legacy fallback 移除已由 B-143 单独处理。
- B-128 收口后，Vue 工作台可从历史消息发起编辑重发，并在完成后刷新当前会话消息。

## 7. B-143 交付边界

B-143 完成后额外满足：

- legacy 原生前端文件已删除。
- `backend/api/server.py` 不再包含 `STATIC_LEGACY_DIR`、`STATIC_DIR` 或 fallback 到 legacy static 的逻辑。
- Vue/Vite 生产构建产物 `backend/static_dist/` 是 Web 首页唯一静态来源。
- 构建产物缺失时应给出明确启动错误，不再静默回退 legacy UI。
- `tests/test_webapp/test_frontend_static.py` 中仅针对 legacy 静态源码的断言已删除或迁移到 Vue 源码/构建测试。
- B-143 不修改 `/api/*` 契约、不修改 SQLite schema、不扩大 Agent 工具权限。

## 8. B-142 验收补充

B-142 完成时需要额外满足：

- Vue 工作台不再显示“SSE 和会话后续迁移”类占位文案。
- Vue 工作台能加载当前项目会话列表和当前会话消息。
- Vue 工作台能新建、重命名、删除会话，且会话按项目隔离。
- Vue 工作台能删除单条聊天消息和清空当前项目默认消息。
- Vue 提问通过 `EventSource` 访问 `/api/answer/stream`，能处理 `token`、`done` 和 `answer_error` 事件。
- 用户可取消当前流式请求；取消后输入区恢复可提交状态，不重复写入前端状态。
- `done` 事件后刷新回答、来源、来源质量、可观察性、当前会话消息、反馈入口和工具建议。
- `tool_run_id` 仍可作为下一问上下文发送，不回退 B-141X。
- 不改后端 API 契约、不改 SQLite schema、不扩大 Agent 工具权限。

## 9. B-128 验收补充

B-128 完成时需要额外满足：

- 历史消息区域显示“编辑重发”入口。
- 编辑重发提交后，前端通过 `/api/answer/stream` 发送 `parent_message_id`。
- 成功返回后刷新回答状态和当前会话消息。
- 前端不计算 `branch_index`，只展示后端返回的分支信息。
