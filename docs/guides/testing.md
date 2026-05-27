# 测试指南

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-27

## 1. 目标

优先验证“文档行为 → 用例行为 → 集成行为”三层是否一致，避免只测单点函数。

## 2. 命令建议

```bash
.venv\Scripts\python.exe -m pytest tests/test_webapp -q
.venv\Scripts\python.exe -m pytest tests/test_webapp/test_auth.py tests/test_webapp/test_auth_middleware.py -q
.venv\Scripts\python.exe -m pytest tests/test_webapp/test_frontend_build.py -q
.venv\Scripts\python.exe -m pytest tests/test_webapp/test_frontend_vue_app.py -q
.venv\Scripts\python.exe -m pytest tests/test_webapp/test_fastapi_server.py tests/test_webapp/test_app_entrypoint.py tests/test_webapp/test_docker_startup.py -q
npm run build
.venv\Scripts\python.exe -m pytest tests/test_application/test_markdown_content.py -q
.venv\Scripts\python.exe -m pytest tests/test_application/test_ingestion_usecases.py -q
.venv\Scripts\python.exe -m pytest tests/test_adapters/test_storage.py tests/test_domain/test_models.py -q
docker compose config
```

## 3. 说明

- 受环境限制时，`pytest` 可能因依赖/网络导致不能完整运行，需在提交说明里写出失败原因与替代验证。
- 变更文档行为时，需复跑 markdown 安全与增量更新相关用例。
- 变更默认 Web MVP 的 API、导入、检索、回答或聊天记录行为时，必须复跑 `tests/test_webapp`。
- 变更认证配置、API Key、JWT、中间件保护路径或 FastAPI docs 访问规则时，必须覆盖 `tests/test_webapp/test_auth.py` 和 `tests/test_webapp/test_auth_middleware.py`，并确认认证关闭时现有 API 行为不变。
- 变更 `frontend/`、`package.json`、Vite 配置、`webapp/static_dist/` 服务策略或 legacy 静态 fallback 时，必须覆盖 `tests/test_webapp/test_frontend_build.py` 并运行 `npm run build`。
- 变更 Vue API helper、项目空间 helper、问答 helper、检索调试 helper、文档浏览 helper、文档集合 helper、导入 helper、共享状态、基础布局组件、项目空间选择/创建/改名/删除组件、工作台问答/回答反馈/检索调试组件、资料库文档列表/预览/删除组件、资料库文档集合筛选/新建/删除/重命名/加入/移出入口、资料库轻量导入组件、资料库导入批次历史组件、资料库普通文件上传入口、资料库浏览器文件夹上传入口、资料库当前目录同步入口、资料库导入预检入口或 Vue 主视图壳时，必须覆盖 `tests/test_webapp/test_frontend_vue_app.py` 并运行 `npm run build`。
- 变更 Web RAG 分块、embedding provider、向量索引、搜索排序、检索调试或来源字段时，必须覆盖 chunk 生成、向量持久化、API embedding 请求体、失败回退、文档更新后 chunk/vector 重建、搜索响应 `chunk_id/chunk_index/retrieval/keyword_score/vector_score/vector_provider/vector_model`、`/api/search/debug`、`source_quality` 和问答来源兼容。
- 变更检索复盘时，必须覆盖 `POST/GET /api/retrieval/reviews`、空命中保存、项目隔离、前端保存按钮和 `retrieval_reviews` 文档契约。
- 变更当前项目目录同步时，必须覆盖 `/api/import`、前端同步入口、未选项目禁用、同步成功后刷新文档列表和导入批次历史。
- 变更导入预检时，必须覆盖 `/api/import/preview`、前端预检入口、未选项目禁用、可导入/跳过摘要和跳过原因展示，并确认预检不会刷新文档列表或创建导入批次。
- 变更浏览器文件夹导入时，必须覆盖 `/api/import/upload`、前端 `webkitdirectory` 入口、`webkitRelativePath` 到 `project_name/relative_path` 的转换和导入规则跳过行为。
- 变更普通文件上传导入时，必须覆盖 `/api/import/upload`、前端普通 `multiple` file input、无 `webkitdirectory`、当前项目上传、无项目时创建 `browser-upload` 项目、DOCX/PDF `content_base64` 和文本文件 `content` 请求体。
- 变更文本笔记或 URL 摘录导入时，必须覆盖 `/api/import/note`、`/api/import/url`、同标题或同 URL 更新、空标题/空正文/超大正文/非字符串输入拒绝、前端资料库入口，以及目录同步和浏览器文件夹导入不会删除或覆盖 `note:` / `url:` 虚拟来源。
- 变更导入批次历史时，必须覆盖 `/api/import/batches`、`/api/import/batches/detail`、项目隔离、只展示跳过/读取失败明细、不提供回滚/删除/重试操作，以及前端资料库入口。
- 变更文档集合时，必须覆盖 `/api/document-collections`、`/api/document-collections/update`、`/api/document-collections/delete`、`/api/document-collections/items/add`、`/api/document-collections/items/remove`、按集合过滤文档列表、未分组过滤、跨项目文档拒绝、删除集合不删除文档和前端资料库入口。
- 变更 Vue 文档集合筛选入口时，必须覆盖 `GET /api/document-collections`、前端集合列表读取、全部/未分组/指定集合筛选、选择后刷新文档列表，并确认不提供集合新建/删除/加入/移出入口。
- 变更 Vue 文档集合管理入口时，必须覆盖 `POST /api/document-collections`、`POST /api/document-collections/update`、`POST /api/document-collections/delete`、前端集合名称校验、新建后刷新集合列表、重命名后刷新集合列表、删除前确认、删除集合不删除文档提示，以及删除当前筛选集合后清空筛选并刷新文档列表。
- 变更 Vue 文档集合加入/移出入口时，必须覆盖 `POST /api/document-collections/items/add`、`POST /api/document-collections/items/remove`、前端文档列表单文档加入集合、指定集合筛选下移出当前集合、成功后刷新集合列表和文档列表，以及未选集合/文档的错误提示。
- 变更 Vue 文档删除入口时，必须覆盖 `POST /api/documents/delete`、前端文档列表单文档删除按钮、删除前确认、源文件不会被删除提示、成功后刷新文档列表和集合列表，以及删除当前预览文档后的预览清理。
- 变更 Vue 项目空间改名/删除入口时，必须覆盖 `POST /api/projects/rename`、`POST /api/projects/delete`、前端项目空间面板改名表单、删除前确认、项目内文档记录会被删除提示、改名后刷新项目列表并保持当前项目选中，以及删除后清空当前项目相关资料库状态。
- 变更 Web 文档处理管线时，必须覆盖 DOCX 正文抽取、PDF 可选 `pymupdf` 正文抽取、缺少 PDF 解析器时明确跳过、浏览器上传 `content_base64` 和普通文本导入兼容行为。
- 变更模型设置页时，必须覆盖 `/api/settings/llm`、`/api/settings/llm/test`、Key 不回显和前端设置入口。
- 变更模型 Profile 时，必须覆盖 `/api/model-profiles`、`/api/model-profiles/update`、`/api/model-profiles/delete`、`/api/model-profiles/default`、`/api/model-profiles/test`、默认 Profile 注入 `/api/answer`、Key 引用白名单、Key 不写入响应和前端设置入口。
- 变更 Vue 设置页模型配置时，必须覆盖 `frontend/src/api/settings.js`、`SettingsView.vue`、`App.vue` 设置页状态流、Key 不回显、基础模型设置保存/测试、模型 Profile 新增/编辑/删除/默认/测试入口，并运行 `tests/test_webapp/test_frontend_vue_app.py` 与 `npm run build`。
- 变更 Vue 设置页 Prompt 预设时，必须覆盖 `frontend/src/api/settings.js`、`SettingsView.vue`、`App.vue` 设置页状态流、`/api/prompt-presets*` helper、内置模板复制、预设新增/编辑/删除/默认/清空默认入口，并运行 `tests/test_webapp/test_frontend_vue_app.py` 与 `npm run build`。
- 变更备份导出或恢复时，必须覆盖 `/api/export/project`、`/api/export/project/restore`、不导出或恢复 API Key、恢复为新项目空间、文档正文/chunk/vector 快照恢复、恢复时不重新调用 embedding，以及聊天来源 `document_id/chunk_id` 映射。
- 变更 Prompt 预设时，必须覆盖 `/api/prompt-presets`、`/api/prompt-presets/update`、`/api/prompt-presets/delete`、`/api/prompt-presets/default`、项目隔离、默认预设注入 `/api/answer`、固定来源约束优先级和前端设置入口。
- 变更掌握评估存储、自动出题、回答评估或前端闭环时，必须覆盖 `/api/assessment/start` 生成并持久化题目、题型 `concept / flow / code_location`、轻量知识点标签、`/api/assessment/answer` 使用服务端持久化题目要点评分、四档状态 `已掌握 / 基本理解 / 需要补充 / 暂未掌握`、持久化回答和结果、项目隔离、空项目拒绝、空回答拒绝、前端进度/下一题/答题记录/待复测列表。
- 变更 Vue 评估页时，必须覆盖 `frontend/src/api/assessment.js`、`AssessmentView.vue`、`App.vue` 评估状态流、开始评估、提交回答、下一题/完成、结果概览、答题记录和待复测列表，并运行 `tests/test_webapp/test_frontend_vue_app.py` 与 `npm run build`。
- 变更 Vue 工作台回答反馈时，必须覆盖 `frontend/src/api/answer.js`、`AnswerPanel.vue`、`WorkbenchView.vue`、`App.vue` 反馈状态流、`/api/answer/feedback` helper、四类反馈按钮、保存中/成功/失败状态，并运行 `tests/test_webapp/test_frontend_vue_app.py` 与 `npm run build`。
- 变更 Vue 工作台检索调试时，必须覆盖 `frontend/src/api/search.js`、`SearchDebugPanel.vue`、`WorkbenchView.vue`、`App.vue` 检索诊断状态流、`/api/search/debug` helper、`top_k/min_score/use_keyword/use_vector` 临时参数、来源质量/分块/向量状态/命中片段展示，并运行 `tests/test_webapp/test_frontend_vue_app.py` 与 `npm run build`。
- 变更 Agent 工具能力时，必须覆盖 `/api/agent/tools`、`/api/agent/tools/run`、`/api/agent/tools/runs`、只读工具白名单、未知工具拒绝和 `agent_tool_runs` 审计记录。
- 变更回答工具建议时，必须覆盖 `/api/answer` 的 `tool_suggestion`、前端建议工具展示、用户手动运行按钮，并确认不会自动写入 `agent_tool_runs`。
- 变更工具来源回填时，必须覆盖 `/api/answer` 的 `tool_run_id/tool_context`、同项目校验、跨项目拒绝和前端上下文提示。
- 变更问答流式输出或请求取消时，必须覆盖 `/api/answer/stream` 的 SSE `token/done/answer_error` 事件、OpenAI-compatible `stream=true` 解析、EventSource 前端入口、`source.close()` 取消后的状态提示和按钮恢复。
- 变更回答 Markdown 渲染时，必须覆盖 CDN 入口、`marked.parse`、`DOMPurify.sanitize`、`highlight.js` 代码高亮、纯文本回退和前端静态语法检查。
- 变更深色模式时，必须覆盖主题切换入口、`prefers-color-scheme`、`data-theme`、`localStorage` 持久化、浅色/深色 CSS 变量和前端静态语法检查。
- 变更 Web 端 LLM、掌握评估、首次引导或静态前端约束时，必须复跑 `tests/test_webapp`，并执行 `Get-ChildItem webapp\static\js\*.js | ForEach-Object { node --check $_.FullName }`。
- 变更 Docker 启停入口时，必须复跑 `tests/test_webapp/test_docker_startup.py`，并至少真实执行一次启动或停止脚本。
- 变更 FastAPI/Uvicorn 运行时、`app.py`、`webapp/server.py` 或 SSE 外壳时，必须复跑 `tests/test_webapp/test_fastapi_server.py`、`tests/test_webapp/test_app_entrypoint.py` 和 `tests/test_webapp/test_docker_startup.py`。

## 4. 回归清单

- Markdown 安全渲染链路
- 增量增删改（含源文件删除）
- 向量检索 + 来源返回一致性
- 用例级错误消息与状态码（若有）
- Web MVP 创建项目空间、导入目录、分块生成、向量索引生成、问答来源返回
- Web MVP 提问后可持久化聊天记录，并能按项目重新加载 `question/answer/mode/provider/sources`；真实 LLM prompt 会包含最近 3 轮历史
- Web MVP Agent 工具只开放只读项目概览和来源检索，未知工具会被拒绝并记录审计
- Web MVP Agent 工具运行历史按当前项目展示，切换项目后重新加载
- Web MVP 来源不足时只提示建议工具 `search_sources`；用户点击按钮后才运行 Agent 只读工具
- Web MVP `search_sources` 工具结果可显式回填到下一轮问答；跨项目工具运行 ID 必须被拒绝
- Web MVP 检索调试可返回命中 chunk、分数、来源质量、上下文预览和临时 RAG 参数
- Web MVP 检索复盘可保存一次诊断快照，保留查询参数、命中来源、来源质量和人工备注
- Web MVP 浏览器文件夹导入可创建上传项目，并按后缀、忽略目录和大小规则跳过文件；DOCX 可抽取正文，PDF 在安装可选解析器时可抽取正文，缺少解析器时有明确跳过原因
- Web MVP 文本笔记和 URL 摘录导入会写入 `note:` / `url:` 虚拟来源，同标题或同 URL 再次导入只更新原记录，目录同步和浏览器文件夹导入不会误删这些虚拟来源；真实文件或上传文件撞到笔记相对路径时会被跳过
- Web MVP 文档集合可新增、删除、加入或移出文档，并按全部、未分组或指定集合过滤资料库列表；集合只保存关联关系，删除集合不删除文档
- Web MVP DeepSeek 配置存在时优先真实 LLM，失败时本地回退
- Web MVP 模型设置页可保存 API Base / 模型名 / Key，且不回显 Key 明文
- Web MVP 模型 Profile 可新增、编辑、删除、设置默认和测试连接；Profile 只保存 Key 引用，默认 Profile 会优先参与真实 LLM 问答
- Web MVP Prompt 预设可新增、编辑、删除、设置默认；真实 LLM prompt 保留固定来源约束，预设不保存 API Key
- Web MVP 问答可通过 SSE / EventSource 流式渲染回答，完成后仍保存聊天记录、来源、质量提示和观察性元数据
- Web MVP 深色模式跟随系统偏好，并可通过侧栏按钮手动切换和持久化
- Web MVP 掌握评估入口、三类题型生成、逐题作答进度、服务端参考要点评分、四档状态输出、答题记录、待复测列表、题目/回答/结果持久化、回答反馈
- Web MVP 首次使用引导可见
- Docker 一键启动文件存在且端口、运行时目录、导入目录、DeepSeek 环境变量映射、双击启动/停止入口符合约定
- 可选认证默认关闭；启用后 `/api/health` 和静态首页放行，受保护 API、`/docs`、`/redoc`、`/openapi.json` 需要 API Key 或 Bearer JWT
- Vue/Vite 构建链可生成 `webapp/static_dist/`；构建产物存在时 FastAPI 首页来自 `static_dist`，缺失时回退 `webapp/static/`
- Vue 前端包含 API client、共享状态模型和工作台 / 资料库 / 评估 / 设置基础视图壳；资料库已迁移项目空间选择/创建/改名/删除薄片、文档列表/单文档预览/删除薄片、文本笔记/URL 摘录导入薄片、导入批次历史薄片、普通文件上传薄片、浏览器文件夹上传薄片、当前目录同步薄片、导入预检薄片和文档集合筛选/新建/删除/重命名/加入/移出薄片，设置页已迁移模型设置/Profile/Prompt 预设薄片，评估页已迁移最小闭环，工作台已迁移非流式问答、回答反馈和检索调试入口；完整业务流程未迁移前仍由 legacy 静态前端承担
