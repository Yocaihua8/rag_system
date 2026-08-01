# 组件 API 契约

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：Knowledge Island v2.0.0 当前 Vue 主壳、主视图与覆盖层装配接口
> Related：`page-module-contract.md`、`frontend-backend-contract-check.md`、`ui-wireframes.md`

本文档冻结当前主路径组件的职责、props、emits 和插槽。`defineProps / defineEmits` 是组件定义的事实源，`frontend/src/App.vue` 是当前装配关系的事实源。

## 1. 总体职责边界

| 组件 | 文件 | 类型 | 主要职责 | 不负责 |
|------|------|------|----------|--------|
| `App` | `frontend/src/App.vue` | 集成 Owner | 保存共享页面状态、装配视图与覆盖层、调用 API 模块、处理事件 | 复用型展示组件内部布局 |
| `AppShell` | `frontend/src/components/AppShell.vue` | 页面壳 | 侧边栏、顶栏、主内容插槽 | 业务 API 和页面业务状态机 |
| `WorkspaceSidebar` | `frontend/src/components/WorkspaceSidebar.vue` | 导航组件 | 主导航、项目选择、资料入口、线程选择 | 直接修改父状态或调用 API |
| `WorkbenchView` | `frontend/src/views/WorkbenchView.vue` | 教练页面 | 组合提问、聊天、回答依据、检索复盘和工具模块 | HTTP/SSE 请求编排 |
| `LearningMapView` | `frontend/src/views/LearningMapView.vue` | 学习地图页面 | 展示项目理解、知识点、技能映射和评估记录 | 重新计算服务端分析或评估结果 |
| `LearningPlanView` | `frontend/src/views/LearningPlanView.vue` | 学习计划页面 | 草稿编辑、确认入口、进度更新和发布入口 | 决定服务端可编辑性或并发版本 |
| `SettingsView` | `frontend/src/views/SettingsView.vue` | 设置页面 | 回答、资料、Obsidian 和外观设置界面 | 保存明文密钥；伪造禁用能力 |
| `LibraryModal` | `frontend/src/components/LibraryModal.vue` | 覆盖层 | 资料导入与选择 | 成为独立主视图或直接切换 `currentView` |

## 2. 页面壳组件

### 2.1 `AppShell`

#### props

| prop | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `currentView` | `String` | 是 | N/A | 当前主视图键 |
| `sidebarMode` | `String` | 否 | `"threads"` | 侧边栏线程模式或资料工作区选择模式 |
| `projects` | `Array` | 否 | `[]` | 项目列表 |
| `selectedProjectId` | `String` | 否 | `""` | 当前项目 |
| `libraryTargetProjectId` | `String` | 否 | `""` | 资料弹窗目标项目 |
| `chatSessions` | `Array` | 否 | `[]` | 线程列表 |
| `selectedChatSessionId` | `String` | 否 | `""` | 当前线程 |

#### emits

`back-to-threads`、`change-view`、`create-chat-session`、`open-library`、`select-chat-session`、`select-library-target-project`、`select-project`。

#### slots

| slot | 作用 | 当前使用方 |
|------|------|------------|
| 默认插槽 | 承载当前主视图和由 `App.vue` 装配的覆盖层 | `frontend/src/App.vue` |

### 2.2 `WorkspaceSidebar`

#### props

| prop | 类型 | 默认值 |
|------|------|--------|
| `currentView` | `String` | `"coach"` |
| `sidebarMode` | `String` | `"threads"` |
| `projects` | `Array` | `[]` |
| `selectedProjectId` | `String` | `""` |
| `libraryTargetProjectId` | `String` | `""` |
| `chatSessions` | `Array` | `[]` |
| `selectedChatSessionId` | `String` | `""` |

#### emits

`back-to-threads`、`change-view`、`collapse-sidebar`、`create-chat-session`、`open-library`、`select-chat-session`、`select-library-target-project`、`select-project`。

事件 payload 契约：

| 事件 | payload |
|------|---------|
| `change-view` | `coach`、`learning-map`、`learning-plan`、`settings` 之一 |
| `select-project`、`select-library-target-project` | 项目 ID 字符串 |
| `select-chat-session` | 线程 ID 字符串 |
| `create-chat-session` | 当前实现传空字符串 |
| 其余事件 | 无 payload |

## 3. 主视图组件

### 3.1 `WorkbenchView`

两个 props 为必填：`statusMessage:String`、`selectedProjectId:String`。

其余 props 按职责分组如下；除特别说明外，字符串默认 `""`、布尔值默认 `false`、数组默认 `[]`、对象默认 `null`。

| 分组 | props |
|------|-------|
| 首次运行 | `projectFormSubmitting`、`projectFormError`、`projectFormStatus`、`firstRunVisible`、`ollamaStatus`、`ollamaStatusLoading`、`ollamaStatusError`、`ollamaPullingModel`、`ollamaPullProgress`、`ollamaPullStatus`、`ollamaPullError` |
| 回答 | `answerResult`、`answerLoading`、`answerError`、`answerStatus`、`answerStreamingText`、`answerCancelStatus`、`lastAnswerMessageId` |
| 回答反馈 | `answerFeedbackSubmitting`、`answerFeedbackStatus`、`answerFeedbackError` |
| 聊天 | `chatMessages`、`chatMessagesLoading`、`chatMessagesError` |
| 依据与工具上下文 | `evidenceCollapsed`（默认 `true`）、`currentToolSuggestion`、`lastUsableToolRun`、`currentToolContextRunId` |
| 模型对比 | `modelProfiles`、`modelComparisonResult`、`modelComparisonLoading`、`modelComparisonError`、`modelComparisonStatus` |
| 检索调试 | `searchDebugResult`、`searchDebugLoading`、`searchDebugError`、`searchDebugStatus` |
| 检索设置 | `retrievalSettings`、`retrievalSettingsLoading`、`retrievalSettingsSaving`、`retrievalSettingsStatus`、`retrievalSettingsError` |
| 检索复盘 | `retrievalReviews`、`retrievalReviewsLoading`、`retrievalReviewsError`、`retrievalReviewSaving`、`retrievalReviewError`、`retrievalReviewStatus`、`selectedRetrievalReview`、`retrievalReviewDetailLoading`、`retrievalReviewDetailError`、`deletingRetrievalReviewId` |
| Agent 工具 | `agentTools`、`agentToolsLoading`、`agentToolsError`、`agentToolRuns`、`agentToolRunsLoading`、`agentToolRunsError`、`selectedAgentToolRun`、`agentToolResult`、`agentToolStatus`、`agentToolError`、`agentToolSubmittingName`、`agentToolDetailLoading`、`agentToolDetailError` |

emits：

`cancel-answer`、`check-health`、`clear-chat-messages`、`clear-tool-context`、`compare-answers`、`create-project`、`delete-chat-message`、`delete-retrieval-review`、`dismiss-first-run`、`edit-chat-message`、`load-agent-tool-runs`、`load-agent-tools`、`open-library`、`pull-ollama-model`、`refresh-ollama-status`、`run-agent-tool`、`run-search-debug`、`run-tool-suggestion`、`save-retrieval-review`、`save-retrieval-settings`、`select-agent-tool-run`、`select-retrieval-review`、`submit-answer-feedback`、`submit-question`、`start-assessment-tool`、`toggle-evidence`、`use-tool-result-context`。

### 3.2 `LearningMapView`

#### props

| prop | 类型 | 默认值 |
|------|------|--------|
| `projectId`、`selectedProjectId` | `String` | `""` |
| `overview`、`knowledgePoints`、`skills`、`coverage` | `Object` | `{}` |
| `loading`、`analyzing` | `Boolean` | `false` |
| `error` | `String` | `""` |

`projectId` 优先于 `selectedProjectId`。当前 `App.vue` 使用 `selectedProjectId`。

#### emits

| 事件 | payload |
|------|---------|
| `analyze`、`refresh` | 无 |
| `start-assessment` | `{ target_type, target_id }` |
| `open-sources` | `{ title, source_ids, sources }` |

### 3.3 `LearningPlanView`

#### props

| prop | 类型 | 默认值 |
|------|------|--------|
| `projectId`、`selectedProjectId` | `String` | `""` |
| `currentPlan` | `Object` | `{}` |
| `loading`、`generating`、`saving`、`confirming`、`publicationLoading` | `Boolean` | `false` |
| `error`、`status`、`publicationError`、`publicationStatus` | `String` | `""` |
| `obsidianConnection` | `Object` | `null` |

#### emits

| 事件 | payload |
|------|---------|
| `generate`、`refresh`、`preview-publication`、`open-obsidian-settings` | 无 |
| `update-plan` | 草稿结构：`{ planId, items, expectedRevision, expectedItemsHash }`；任务进度：`{ planId, itemStatuses, expectedProgressHash }` |
| `confirm` | `{ planId, expectedRevision, expectedItemsHash }` |
| `open-sources` | `{ title, source_ids, sources }` |

### 3.4 `SettingsView`

props 按职责分组如下：

| 分组 | props 与默认值 |
|------|----------------|
| 页签 | `settingsPage:String = "answer"` |
| 当前项目 | `selectedProjectId:String = ""` |
| LLM | `llmSettings:Object = {}`；`llmSettingsLoading / llmSettingsSubmitting / llmSettingsTesting:Boolean = false`；`llmSettingsError / llmSettingsStatus:String = ""` |
| 模型 Profile | `modelProfiles:Array = []`；`defaultModelProfileId:String = ""`；`modelProfilesLoading / modelProfileSubmitting / modelProfileDefaultSubmitting:Boolean = false`；`modelProfileLoadError / modelProfileTestingId / modelProfileDeletingId / modelProfileMutationError / modelProfileStatus:String = ""` |
| 回答模板 | `promptPresets / promptPresetTemplates:Array = []`；`selectedPromptPresetId:String = ""`；`promptPresetsLoading / promptPresetSubmitting / promptPresetDefaultSubmitting:Boolean = false`；`promptPresetLoadError / promptPresetDeletingId / promptPresetMutationError / promptPresetStatus:String = ""` |
| Obsidian | `obsidianConnections:Array = []`；`obsidianConnectionsLoading / obsidianPairingLoading:Boolean = false`；`obsidianConnectionError / obsidianPairingError / obsidianRevokingId:String = ""`；`obsidianPairing:Object = null` |

emits：

`back`、`change-settings-page`、`load-settings`、`save-llm-settings`、`test-llm-settings`、`load-model-profiles`、`save-model-profile`、`delete-model-profile`、`set-default-model-profile`、`test-model-profile`、`load-prompt-presets`、`save-prompt-preset`、`delete-prompt-preset`、`set-default-prompt-preset`、`load-obsidian-connections`、`start-obsidian-pairing`、`revoke-obsidian-connection`。

`change-settings-page` 当前 payload 仅为 `answer`、`data`、`obsidian`、`appearance`。

## 4. 覆盖层的当前调用方契约

本节记录 `App.vue` 当前实际传入和监听的接口，不替代各组件自身的 `defineProps / defineEmits`。

### 4.1 `LibraryModal`

| 类型 | 当前调用方接口 |
|------|----------------|
| props | `open`、`step`、`documents`、`documentsLoading`、`documentsLoadError`、`documentCollections`、`selectedDocumentCollectionId`、`documentCollectionsLoading`、`documentCollectionsLoadError`、`importStatus`、`importError`、`importSubmitting`、`obsidianConnections`、`obsidianConnectionsLoading`、`obsidianConnectionsError` |
| emits | `close`、`back-to-upload`、`choose-material`、`refresh-collections`、`select-collection`、`refresh-documents`、`select-document`、`import-note`、`import-url`、`import-files`、`import-folder`、`import-github-repo`、`import-obsidian-vault`、`refresh-obsidian-connections`、`open-obsidian-settings` |

### 4.2 教练覆盖层

| 组件 | props | emits |
|------|-------|-------|
| `CoachSourceDrawer` | `open`、`title`、`sourceIds`、`sources` | `close` |
| `CoachAssessmentOverlay` | `open`、`knowledgePoints`、`skills`、`initialTarget`、`session`、`assessmentResult`、`loading`、`submitting`、`error` | `close`、`open-sources`、`start`、`restart`、`submit-answer` |
| `ObsidianPublicationDialog` | `open`、`preview`、`loading`、`error`、`status` | `close`、`confirm` |

## 5. slots 与内容边界

| 组件 | slot | 契约 |
|------|------|------|
| `AppShell` | 默认插槽 | 仅由 `App.vue` 放入当前视图和覆盖层 |
| `EvidenceDrawer`（由 `WorkbenchView` 使用） | `advanced` | 放入检索调试/复盘、Agent 工具和模型对比，不接管主回答内容 |
| 其他本契约组件 | N/A | 当前主路径不依赖具名 slot 作为跨组件 API |

## 6. CSS 与稳定定位

| 组件 | 根 class / 稳定标识 |
|------|---------------------|
| `AppShell` | `.workspace-shell`、`data-shell-action` |
| `WorkspaceSidebar` | `.workspace-left`、`data-workspace-sidebar`、`data-view-key`、`data-nav-action`、`data-sidebar-action` |
| `WorkbenchView` | `.view-panel.chat-view` |
| `LearningMapView` | `.view-panel.learning-map-view`、`data-learning-map-action` |
| `LearningPlanView` | `.view-panel.learning-plan-view`、`data-learning-plan-action`、`data-learning-plan-field`、`data-learning-plan-tab` |
| `SettingsView` | `.settings-fullscreen`、`data-settings-page`、`data-settings-action`、`data-obsidian-settings` |

组件私有样式继续使用当前语义前缀。禁止为单个组件新增无前缀全局选择器，或删除测试和交互依赖的 `data-*`。

## 7. 数据与 API 依赖

- 主视图不使用 mock 作为运行时默认数据；空数组、空对象、空字符串和 `null` 只表示未加载或无数据状态。
- `App.vue` 是业务状态和副作用 Owner；视图组件通过 props 消费状态，通过 emits 请求动作。
- 真实 HTTP/SSE 请求只能经 `frontend/src/api/*.js` 中的现有封装进入。
- 组件不得把 API snake_case 字段改造成另一套未经记录的持久化契约。
- 来源、覆盖、评估、学习计划能力和发布状态必须直接使用服务端响应，不得由组件伪造。

## 8. 变更规则

以下变更必须先更新本契约并同步调用方：

- 重命名主路径组件文件。
- 新增、删除、重命名 props 或修改其必填性、默认值。
- 修改 emits 名称或 payload 结构。
- 把资料弹窗或覆盖层改成主视图。
- 让视图组件直接调用 HTTP/SSE、保存全局状态或写入公共样式。
- 修改根 class 或稳定 `data-*` 标识。

## 9. 验收清单

- [ ] `AppShell` 与 `WorkspaceSidebar` 的 props / emits 与源码一致
- [ ] 四个主视图只消费 props、发出本契约列出的事件
- [ ] `App.vue` 已处理新增或变更的事件
- [ ] 覆盖层调用方接口与 `App.vue` 当前装配一致
- [ ] 空、加载、错误、stale 和禁用状态没有被 mock 数据掩盖
- [ ] 组件未新增绕过 `frontend/src/api/*.js` 的请求
- [ ] 稳定 class 和 `data-*` 未被无说明重命名
