# 前后端契约对照分析

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：Knowledge Island v2.0.0 Vue 主路径、React v3 平行入口与本地 FastAPI HTTP/SSE 契约
> Related：`api-spec.md`、`page-module-contract.md`、`component-api-contract.md`

本文档对照当前 Vue 主路径、独立 `frontend-v3/` 第一阶段和现有后端接口。它不定义新接口；方法、路径、字段、响应和错误仍以 `api-spec.md` 为权威源。Vue 仍是正式入口，两个前端的状态和 API 代际不能混用。

## 1. 对照目标

| 项 | 当前结论 |
|----|----------|
| 前端集成入口 | `frontend/src/App.vue` |
| 前端请求边界 | `frontend/src/api/*.js`；`App.vue` 只直接使用其中的 `apiGet` 检查健康状态 |
| 传输方式 | JSON HTTP；问答与 Ollama 拉取使用 SSE |
| 页面范围 | 教练、学习地图、学习计划、资料弹窗、设置及评估/逐点学习等覆盖层 |
| 验收标准 | 前端只调用 `api-spec.md` 已定义的接口；请求参数和响应解包与现有契约一致；未接入能力不伪装成功 |

## 2. 通用调用契约

### 2.1 JSON 请求

`frontend/src/api/client.js` 当前行为：

- `apiGet(path)` 使用浏览器 GET。
- `apiPost(path, payload)` 使用 POST、`Content-Type: application/json` 和 JSON body，可传 `AbortSignal`。
- 非 2xx 响应优先显示响应体中的 `error`；无法解析错误响应时显示 HTTP 状态提示。
- 网络 `TypeError` 统一转换为“本地服务暂时不可用”提示。
- 成功响应必须是 JSON；前端不会把 HTML 或纯文本当作成功结果。

前端组件不得绕过该边界自行创造另一套错误解析规则。

### 2.2 SSE

| 场景 | 前端封装 | 接口 | 事件 |
|------|----------|------|------|
| 流式问答 | `askQuestionStream` | `GET /api/answer/stream` | `token`、`done`、`answer_error` |
| 拉取 Ollama 模型 | `pullOllamaModel` | `POST /api/ollama/pull` | `progress`、`done`、`error` |

问答流使用 `EventSource`，取消时前端关闭连接并抛出 `AbortError`。`done` 负载与同步 `/api/answer` 成功响应一致。

### 2.3 字段命名

- 组件 props / emits 使用 camelCase。
- HTTP query 和 JSON body 使用 `api-spec.md` 定义的 snake_case。
- 转换只允许发生在 `frontend/src/api/*.js` 或 `App.vue` 的用例编排处。
- 前端不得重命名后端稳定 ID、来源 ID、revision、hash 或状态枚举后再持久化。

## 3. 页面行为与现有接口

### 3.1 应用启动、项目和线程

| 前端行为 | API 封装 | 现有接口 | 当前契约 |
|----------|----------|----------|----------|
| 读取 Ollama 状态 | `getOllamaStatus` | `GET /api/ollama/status` | 不可达时仍返回 200 和 `available=false` |
| 拉取推荐模型 | `pullOllamaModel` | `POST /api/ollama/pull` | 仅允许服务端推荐白名单，SSE 返回进度 |
| 读取项目 | `loadProjects` | `GET /api/projects` | 前端取 `projects`；选择结果保存在本地选择状态 |
| 创建项目 | `createProject` | `POST /api/projects` | 首次运行向导使用服务端返回的 `project` |
| 读取项目摘要 / 检索设置 | `getProjectSummary`、`getRetrievalSettings` | `GET /api/projects/summary`、`GET /api/projects/retrieval-settings` | 未选项目时前端不发请求 |
| 保存检索设置 | `saveRetrievalSettings` | `POST /api/projects/retrieval-settings` | 数值和布尔值在 API 封装处规范化 |
| 线程列表与消息 | `listChatSessions`、`listChatMessages` | `GET /api/chat/sessions`、`GET /api/chat/messages` | `project_id` 必填；消息可按 `session_id` 过滤 |
| 新建线程 | `createChatSession` | `POST /api/chat/sessions` | 当前侧边栏提供新建入口 |
| 删除 / 清空消息 | `deleteChatMessage`、`clearChatMessages` | `POST /api/chat/messages/delete`、`POST /api/chat/messages/clear` | 不在组件内直接修改后端记录 |
| 服务检查 | `apiGet` | `GET /api/health` | 成功响应 `status=ok` |

### 3.2 教练

| 前端行为 | API 封装 | 现有接口 | 当前契约 |
|----------|----------|----------|----------|
| 流式提问 | `askQuestionStream` | `GET /api/answer/stream` | `project_id`、`question` 必填；可带 `session_id`、`tool_run_id`、`parent_message_id` |
| 同步提问 | `askQuestion` | `POST /api/answer` | 保留为现有封装；当前主体验优先使用 SSE |
| 双模型对比 | `compareAnswers` | `POST /api/answer/compare` | 必须传两个不同的 Profile ID |
| 回答反馈 | `submitAnswerFeedback` | `POST /api/answer/feedback` | `project_id`、`message_id`、`rating` 必填 |
| 检索调试 | `runSearchDebug` | `POST /api/search/debug` | 使用当前项目和检索参数 |
| 检索设置 | `getRetrievalSettings`、`saveRetrievalSettings` | `GET/POST /api/projects/retrieval-settings` | 服务端设置是权威值 |
| 检索复盘 | `save/list/get/deleteRetrievalReview` | `GET/POST /api/retrieval/reviews`、`GET /api/retrieval/reviews/detail`、`POST /api/retrieval/reviews/delete` | 列表、详情和删除使用既有 ID |
| Agent 工具 | `listAgentTools`、`runAgentTool`、运行记录相关封装 | `GET /api/agent/tools`、`POST /api/agent/tools/run`、`GET /api/agent/tools/runs`、`GET /api/agent/tools/runs/detail` | 只调用后端白名单工具；前端不扩展工具权限 |

教练回答中的 `sources`、`source_quality`、`pipeline_trace`、`observability`、`tool_suggestion` 和 `tool_context` 直接来自后端响应。前端只展示和传递，不得伪造来源或工具运行结果。

### 3.3 学习地图与定向评估

| 前端行为 | API 封装 | 现有接口 | 当前契约 |
|----------|----------|----------|----------|
| 分析当前项目 | `analyzeCoachProject` | `POST /api/coach/analyze` | 只分析已入库资料；`project_id` 必填 |
| 项目理解 | `getCoachOverview` | `GET /api/coach/overview` | 前端取 `overview` |
| 知识点 | `getCoachKnowledgePoints` | `GET /api/coach/knowledge-points` | 前端取 `knowledge_points` |
| 技能映射 | `getCoachSkills` | `GET /api/coach/skills` | 前端取 `skills` |
| 覆盖与历史评估 | `getCoachCoverage` | `GET /api/coach/coverage` | stale 时仍可返回历史只读数据 |
| 发起 / 恢复评估 | `startCoachAssessment` | `POST /api/coach/assessments/start` | 新会话使用目标类型和 ID；恢复使用 `session_id`；可选 `restart` |
| 提交评估回答 | `answerCoachAssessment` | `POST /api/coach/assessments/answer` | `project_id`、`session_id`、`question_id`、`answer` 必填 |

前端必须保留服务端 stale 语义：来源变化后历史分析可读，但不能把它当作当前结果，也不能绕过 `409 analysis_stale` 发起新评估或逐点学习。

### 3.4 逐点学习

| 前端行为 | API 封装 | 接口 | 当前契约 |
|----------|----------|------|----------|
| 启动或恢复目标 | `startCoachLearningSession` | `POST /api/coach/learning-sessions/start` | 直接目标与计划任务参数二选一；前端取 `session` |
| 恢复活动或历史会话 | `getCurrentCoachLearningSession` | `GET /api/coach/learning-sessions/current` | `project_id` 必填，`session_id` 可选；前端取 `session` 或 `null` |
| 推进会话状态 | `transitionCoachLearningSession` | `POST /api/coach/learning-sessions/transition` | 发送服务端会话 `version` 和 `allowed_actions` 中的动作；前端取 `session` |
| 提交 attempt | `submitCoachLearningAttempt` | `POST /api/coach/learning-sessions/attempts` | 保留原始 `answer`，发送 `expected_version / idempotency_key`；前端使用返回的 `attempt / session / replayed / plan_sync` |

- `startCoachLearningSession` 只接受 `{targetType,targetId}` 或 `{planId,planItemId}` 其中一组；组件参数在 helper 中转换为 snake_case。
- `expectedVersion` 必须是大于等于 1 的整数。答案只以 `trim()` 判断非空，真正提交时保留原始换行和缩进。
- `CoachLearningSessionOverlay` 只发送服务端 `allowed_actions` 中的动作。一次提交生命周期复用同一幂等键；加载或提交中禁止重复操作。
- 请求冲突或失败后，`App.vue` 重新读取指定会话并展示服务端最新快照，不在客户端合并 attempt、重算版本或伪造成功。
- attempt 更新当前覆盖后重新加载 coverage；仅 `plan_sync.linked=true` 时重新加载当前学习计划。组件不得从分数自行决定掌握或任务完成。

### 3.5 学习计划

| 前端行为 | API 封装 | 现有接口 | 当前契约 |
|----------|----------|----------|----------|
| 生成草稿 | `generateLearningPlan` | `POST /api/coach/learning-plans/generate` | `project_id` 必填；`max_items` 可选 |
| 读取当前计划 | `getCurrentLearningPlan` | `GET /api/coach/learning-plans/current` | 前端取 `current` |
| 更新计划 | `updateLearningPlan` | `POST /api/coach/learning-plans/update` | `items` 和 `item_statuses` 必须二选一 |
| 确认计划 | `confirmLearningPlan` | `POST /api/coach/learning-plans/confirm` | 使用当前 `plan_id`，可带 revision 和 items hash |
| 预览发布 | `previewObsidianPublication` | `POST /api/obsidian/publications/preview` | 当前项目须有活动连接、当前分析和已确认计划 |
| 确认发布 | `confirmObsidianPublication` | `POST /api/obsidian/publications/confirm` | 将既有 draft 推进到 queued，不代表插件已写入 |

结构更新可携带 `expected_revision / expected_items_hash`；进度更新还可携带 `expected_progress_hash`。前端必须展示冲突，不得吞掉 `learning_plan_*_conflict` 后覆盖服务端新版本。

确认版 `learning` 任务通过 `start-learning` 事件把 `planId / planItemId` 交给 `App.vue`，再由逐点学习 API 启动绑定会话。打开会话不会在前端修改任务；服务端 `plan_sync` 更新后重新请求当前计划。

### 3.6 资料弹窗

| 前端行为 | API 封装 | 现有接口 |
|----------|----------|----------|
| 文档列表 / 详情 | `listDocuments`、`getDocument` | `GET /api/documents`、`GET /api/document` |
| 文档集合列表 | `listDocumentCollections` | `GET /api/document-collections` |
| 笔记导入 | `importPlainTextNote` | `POST /api/import/note` |
| URL 内容导入 | `importUrlExcerpt` | `POST /api/import/url`；当前弹窗仅提交 `url`，缺少 helper 必需的 `title/content`，属于 ISSUE-008 |
| 浏览器文件 / 文件夹导入 | `importBrowserFiles`、`importBrowserFolder` | `POST /api/import/upload` |
| GitHub 仓库导入 | `importGithubRepo` | `POST /api/import/github-repo` |
| Obsidian Vault 一次性导入 | `importObsidianVault` | `POST /api/import/obsidian-vault` |
| Obsidian 连接状态 | `listObsidianConnections` | `GET /api/obsidian/connections` |

当前资料弹窗的 GitHub 和 Vault 导入是后端现有导入能力；Obsidian Vault 一次性导入不等同于插件连接、持续同步或成果发布。

### 3.7 设置

| 设置区域 | API 封装 | 现有接口 | 当前状态 |
|----------|----------|----------|----------|
| LLM 设置 | `load/save/testLlmSettings` | `GET /api/settings/llm`、`POST /api/settings/llm`、`POST /api/settings/llm/test` | 已接入 |
| 模型 Profile | Profile 相关封装 | `GET /api/model-profiles`；`POST /api/model-profiles`、`POST /api/model-profiles/update`、`POST /api/model-profiles/delete`、`POST /api/model-profiles/default`、`POST /api/model-profiles/test` | 列表、新增、更新、删除、默认和测试已接入 |
| 项目回答模板 | Prompt Preset 相关封装 | `GET /api/prompt-presets`；`POST /api/prompt-presets`、`POST /api/prompt-presets/update`、`POST /api/prompt-presets/delete`、`POST /api/prompt-presets/default` | 列表、新增、更新、删除和默认已接入 |
| Obsidian 连接 | `listObsidianConnections`、`startObsidianPairing`、`revokeObsidianConnection` | `GET /api/obsidian/connections`、`POST /api/obsidian/pairing/start`、`POST /api/obsidian/connections/revoke` | 已接入；配对码一次性显示 |
| 资料位置、备份、恢复 | 无当前页面调用 | N/A | `SettingsView` 按钮禁用，不得显示成功 |
| 外观主题 | 无当前页面调用 | N/A | 仅保留入口，未接入主题切换 |

普通设置和连接响应不得包含明文 API Key 或插件令牌。前端只显示 `has_api_key`、来源说明、一次性配对码等契约允许的字段。

## 4. 当前边界与未接入项

| 边界 | 当前事实 | 处理要求 |
|------|----------|----------|
| 前端路由 | 当前无 `vue-router`，也无按 URL 直达子页契约 | 使用 `currentView`；不得把 URL 路径写成已支持 |
| 资料与外观设置 | 页面按钮明确禁用 | 不新增假数据或前端本地“成功”状态 |
| URL 摘录入口 | `LibraryModal` 只发送 `{ url }`，`importUrlExcerpt` 要求 `url/title/content` | 当前操作会在前端校验失败；修复前不得写成可用导入闭环 |
| 项目导出 / 恢复 | `api-spec.md` 已有后端接口，但当前主设置页和 API 封装未接入 | 这是前端未接入，不是后端缺失；后续接入需单独设计交互和验证 |
| 可选认证 | `api-spec.md` 支持 `RAG_AUTH_ENABLED=1`；当前 `api/client.js` 不附加 `X-API-Key` 或 Bearer Header，`EventSource` 也无凭证装配 | 当前 Vue 主路径只承诺默认本地认证关闭模式；启用认证前必须先补完整前端凭证链 |
| 插件端接口 | `/pairing/complete`、`/sync/events`、`/publications/pending`、`/publications/result` 面向 Obsidian 插件 | 主 Vue 前端不得冒充插件调用这些接口 |
| SQL 练习执行 | 前端只显示服务端公开 fixture 并提交原始 SQL | 不在浏览器执行 SQL，不传数据库路径，不显示 reveal 前的评分依据 |

## 5. 缺口结论

| 检查项 | 结论 |
|--------|------|
| 当前五个主入口与逐点覆盖层的新增 API | 当前 Unreleased 源码新增四个 `/api/coach/learning-sessions/*` 操作，均已在 `api-spec.md` 和 `frontend/src/api/coach.js` 映射 |
| 当前前端请求路径与 API 规格冲突 | 未发现明显路径冲突；URL 摘录属于请求参数装配缺口 |
| 需要明确的运行边界 | URL 摘录参数不完整；可选认证尚未接入 Vue 凭证链；资料备份/恢复和外观仍是禁用 UI |
| 逐点学习接线边界 | 新增逐点覆盖层和三个现有入口，不新增主视图键；业务状态、评分、证据资格和计划联动仍归后端 |

## 6. 联调验证清单

- [ ] 默认本地模式下，`GET /api/health` 与首次启动请求可正常返回
- [ ] 未选择项目时，API 封装不会发送要求 `project_id` 的业务请求
- [ ] 问答 SSE 能处理 `token / done / answer_error`，取消后关闭连接
- [ ] 学习地图在 stale 时只读展示并禁止新评估
- [ ] 教练、学习地图和确认计划任务都经同一 API helper 打开逐点学习；工作区可恢复活动会话且不自动打开覆盖层
- [ ] 学习提交保留原始答案、幂等键和服务端 version；冲突后恢复最新快照，不出现重复 attempt
- [ ] SQL fixture 只展示合成数据，浏览器不执行 SQL或接收正式数据库路径；stale、completed、abandoned 文案可区分
- [ ] 学习计划更新保持 `items` 与 `item_statuses` 二选一，并传递服务端并发校验字段
- [ ] 资料弹窗只调用现有导入、文档和连接接口；URL 摘录修复前保持已知失败边界
- [ ] 设置页不回显明文 Key / Token，未接入按钮保持禁用
- [ ] 发布确认显示 queued 语义，不把它解释成插件已完成写入
- [ ] 开启可选认证前，先验证普通 JSON、问答 EventSource 和 Ollama SSE 的凭证传递链

## 7. 相关文件索引

### 前端

- `frontend/src/App.vue`：主视图、共享状态、覆盖层和 API 用例集成。
- `frontend/src/components/AppShell.vue`：页面壳和默认插槽。
- `frontend/src/components/WorkspaceSidebar.vue`：主导航、项目和线程选择。
- `frontend/src/views/WorkbenchView.vue`：教练页面。
- `frontend/src/views/LearningMapView.vue`：学习地图。
- `frontend/src/views/LearningPlanView.vue`：学习计划。
- `frontend/src/components/CoachLearningSessionOverlay.vue`：当前逐点学习步骤、练习、fixture、attempt 和动作展示。
- `frontend/src/views/SettingsView.vue`：当前设置能力与禁用边界。
- `frontend/src/api/*.js`：现有 HTTP/SSE 调用封装。

### 文档

- `api-spec.md`：接口方法、路径、字段、响应、错误码和认证边界的权威源。
- `page-module-contract.md`：主视图和覆盖层编排。
- `component-api-contract.md`：props、emits、slot 和组件职责。

## 8. 结论

- 当前 Vue 主路径已接入教练、学习地图、学习计划、资料和设置所需的 HTTP/SSE API，并通过四个 Coach 学习会话操作接入逐点学习覆盖层；URL 摘录、可选认证等已列缺口不在该闭环范围内。
- 新页面动作仍必须先在 `api-spec.md` 找到契约；逐点学习组件不得绕过 `frontend/src/api/coach.js` 或复制服务端状态机。
- 可选认证、资料备份/恢复和外观主题是明确边界，不能在未实现完整链路前写成“可用”。

## 9. React v3 平行接线

`frontend-v3/src/api/` 只从 `/api/v3/openapi.json` 生成类型，`VITE_API_BASE_URL` 必须直接包含 `/api/v3`。`openapi-fetch` 处理 JSON envelope；运行事件由独立 fetch-stream parser 处理，不能回退到 v2 `EventSource` 合同。

| 页面 / 行为 | v3 接口 | 当前处理 |
|-------------|---------|----------|
| 服务状态 | `GET /api/v3/health` | 同时显示连接与 executor 事实；失败不伪装在线 |
| 项目选择 / 创建 | `GET/POST /api/v3/projects` | 只接受后端实际存在的目录；浏览器阶段明确要求完整路径 |
| 项目资料扫描 / 浏览 | `POST /projects/{id}/sources/scan`、`GET /projects/{id}/sources`、`GET /projects/{id}/documents` | 只显示后端返回的 Sources 与相对文档元数据；扫描写请求使用稳定 `Idempotency-Key`，不回退到 v2 导入或演示资料 |
| 项目资料概览 | `GET /projects/{id}/insights/overview` | 只展示受控 v3 Documents 元数据汇总；资料为空时明确提示扫描，不合成评分或技术栈结论 |
| 任务列表 / 首次发送 | `GET/POST /api/v3/tasks` | 创建响应直接使用 `initial_message`，不重复追加首消息 |
| 继续任务 | `POST /api/v3/tasks/{id}/messages` | 成功消息 ID 作为新 Run 的不可变输入引用 |
| 刷新恢复 | `GET /api/v3/tasks/{id}/runs?limit=20&offset=0` | 按服务端倒序结果取最近 Run，并保留历史运行标识；不把浏览器存储当作运行事实源 |
| 运行 / 控制 | `POST /tasks/{id}/runs`、`GET/POST /runs/*` | 全部写请求强制稳定 `Idempotency-Key`；版本化控制和审批另外发送服务端 `expected_version` / request hash |
| 分段回答 | `GET /runs/{id}/events`、`GET /tasks/{id}/messages` | Run 内按 sequence 去重；最多五次有界重连并从最后序号续传；完整消息负责刷新历史 |
| 详细过程 | steps、approvals、artifacts | 产物按 Task 查询并标注所属 Run；只展示真实返回，当前固定工作流不会伪造审批 |
| 工作流 | definitions / versions | 定义、详情与版本步骤只读接线；绑定、编辑、校验和执行 UI 在稳定 API 可用前保持禁用 |
| 模型 Profile 设置 | `GET/POST /model-profiles`、`POST /model-profiles/{id}/update|default|delete` | 使用独立 v3 数据和幂等写请求；只提交 Key 引用，不提供 Key 录入或连接测试 |
| Artifact 受控导出 | `GET /artifacts/{id}/export-preview`、`POST /artifacts/{id}/export-confirm` | 详细过程先读取版本/hash/受管文件名，再由用户确认；确认请求使用稳定 `Idempotency-Key`，不接受或展示绝对路径 |
| 洞察与其余设置 | N/A | 资料快照概览已在项目页接入；其余能力只保留明确不可用说明，不调用 v2 填空 |

TanStack Query 持有服务端项目、任务、运行、步骤、审批、产物和工作流；Zustand 只保存界面主题、抽屉、最后项目选择和按任务隔离的未发送草稿。离线恢复后不会自动提交写请求。

任务创建、追加消息与启动 Run 使用 `sessionStorage` intent ledger 处理“消息已保存但 Run 响应丢失”的部分成功场景。ledger 只保存 SHA-256 摘要、幂等键、阶段和消息 ID，24 小时过期且最多 64 条，不保存原始 prompt 或项目路径，也不是运行事实源。Run 明确成功后立即释放对应 intent；用户再次提交相同正文会生成新的操作键。项目创建、运行控制和审批决议同样先对输入做 SHA-256 摘要，再持久化未决幂等键。
