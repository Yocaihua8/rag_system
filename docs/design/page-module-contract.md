# 页面模块契约

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：Knowledge Island v2.0.0 Vue 主壳、教练、学习地图、学习计划、资料弹窗与设置
> Related：`ui-wireframes.md`、`component-api-contract.md`、`frontend-backend-contract-check.md`

本文档冻结当前 Vue 主入口的页面编排、状态切换和文件边界。页面事实以 `frontend/src/App.vue` 及其当前装配的视图为准；接口字段以 `api-spec.md` 为准。

## 1. 基本信息

| 项 | 当前契约 |
|----|----------|
| 应用入口 | `frontend/src/App.vue` |
| 页面壳 | `frontend/src/components/AppShell.vue` |
| 侧边栏 | `frontend/src/components/WorkspaceSidebar.vue` |
| 页面切换 | 不使用 `vue-router`；由 `appState.currentView` 和 `handleChangeView(view)` 切换 |
| 可用主视图 | `coach`、`learning-map`、`learning-plan`、`settings` |
| 资料入口 | `LibraryModal` 覆盖层；不占用 `currentView`，关闭后保留原主视图 |
| 页面集成 Owner | `frontend/src/App.vue`，Owner 为 RAG 团队 |
| 接口调用边界 | `App.vue` 调用 `frontend/src/api/*.js`；页面和展示组件通过 props 接收状态、通过 emits 上报动作 |

## 2. 页面与模块顺序

### 2.1 全局页面壳

| 顺序 | 模块 | 文件 | 必需 | 当前职责 |
|------|------|------|------|----------|
| 1 | 工作区侧边栏 | `components/WorkspaceSidebar.vue` | 是 | 主视图入口、项目选择、资料入口和线程选择 |
| 2 | 顶栏 | `components/AppShell.vue` | 是 | 当前视图标题、当前项目和线程数量 |
| 3 | 主内容插槽 | `components/AppShell.vue` | 是 | 承载当前主视图与覆盖层 |

窄屏下 `AppShell` 初始折叠侧边栏；判定条件为 `max-width: 760px`。展开、折叠只改变壳层状态，不改变当前项目或当前视图。

### 2.2 教练（`currentView = coach`）

页面编排文件为 `frontend/src/views/WorkbenchView.vue`，模块顺序固定为：

1. 页面标题。
2. 首次运行向导 `FirstRunWizard`（仅 `firstRunVisible` 为真时显示）。
3. 主列：`QuestionComposer` → `ChatThread` → `AnswerPanel`。
4. 右侧依据区 `EvidenceDrawer`。
5. 依据区高级页签：查来源 / 复盘、工具、模型对比。

`WorkbenchView` 只展示父级状态并转发交互；提问、SSE 取消、聊天记录、检索复盘、Agent 工具与反馈动作均由 `App.vue` 处理。

### 2.3 学习地图（`currentView = learning-map`）

页面编排文件为 `frontend/src/views/LearningMapView.vue`，模块顺序固定为：

1. 标题与“分析项目 / 刷新”动作。
2. 错误、加载、未选项目和分析过期提示。
3. 项目理解摘要与知识点、已验证数、项目覆盖指标。
4. 双栏内容：项目知识点 → 通用技能辅助映射。
5. 当前项目最近评估记录。

进入该视图时 `App.vue` 调用 `loadCoachWorkspace()`。分析过期时仍可回看历史结果，但视图禁止发起新的定向评估。

### 2.4 学习计划（`currentView = learning-plan`）

页面编排文件为 `frontend/src/views/LearningPlanView.vue`，模块顺序固定为：

1. 标题与“刷新 / 生成草稿”动作。
2. 错误、状态、加载、未选项目和分析过期提示。
3. 同时存在草稿与已确认计划时显示版本页签。
4. 无计划空状态，或当前计划摘要。
5. 草稿模式：任务结构编辑、排序、来源查看和确认。
6. 已确认模式：任务进度更新和来源查看。
7. 已确认计划的 Obsidian 发布预览入口；无活动连接时转入设置页。

进入该视图时 `App.vue` 并行加载当前学习计划和 Obsidian 连接。视图只依据服务端返回的 `can_edit_structure`、`can_update_progress`、`can_confirm` 等能力字段开放操作。

### 2.5 资料弹窗

“资料”入口由 `WorkspaceSidebar` 发出 `open-library`，`App.vue` 打开 `LibraryModal`。当前步骤为：

| 步骤 | `libraryStep` | 当前内容 |
|------|---------------|----------|
| 加入资料 | `upload` | 笔记、URL、文件、文件夹、GitHub 仓库、Obsidian Vault 等现有导入入口 |
| 选择资料 | `select` | 当前项目的资料集合、文档列表与文档选择 |

弹窗打开、关闭和步骤切换不得修改 `currentView`。选择资料时侧边栏进入 `workspace-select`；关闭弹窗或返回线程后恢复 `threads`。

当前 URL 表单只发出 `{ url }`，而 `importUrlExcerpt()` 还要求非空 `title` 与 `content`，因此该可见入口会在前端校验阶段失败；它是 BACKLOG ISSUE-008 的已知缺陷，不得按已交付闭环验收。

### 2.6 设置（`currentView = settings`）

页面编排文件为 `frontend/src/views/SettingsView.vue`，设置页签顺序固定为：

1. 回答：LLM 连接、模型 Profile、项目回答模板。
2. 资料：当前仅展示本地资料说明；位置选择、备份、恢复按钮禁用。
3. Obsidian：连接列表、撤销连接和一次性配对码。
4. 外观：当前保留入口，主题切换未接入。

进入设置时 `App.vue` 加载 Obsidian 连接；切换到 Obsidian 页签时再次按需加载。返回动作切换回 `coach`。

### 2.7 覆盖层

覆盖层均由 `App.vue` 统一装配，不能自行创建第二套页面状态：

| 覆盖层 | 触发来源 | 关闭后行为 |
|--------|----------|------------|
| `CoachSourceDrawer` | 学习地图、学习计划或评估的“查看来源” | 保留当前主视图和项目 |
| `CoachAssessmentOverlay` | 学习地图定向评估或教练评估入口 | 保留当前主视图和评估状态 |
| `ObsidianPublicationDialog` | 学习计划发布预览 | 保留当前学习计划 |

## 3. 稳定定位标识

以下标识已存在于当前源码。重命名或删除时必须同步组件测试和本文档。

| 范围 | 标识 |
|------|------|
| 壳层 | `data-shell-action="open-sidebar"`、`data-shell-action="collapse-sidebar"`、`data-workspace-sidebar` |
| 主导航 | `data-view-key="coach"`、`learning-map`、`learning-plan`、`settings`；`data-nav-action="library"` |
| 侧边栏 | `data-sidebar-action="open-library"`、`data-sidebar-action="create-chat-session"`、`data-sidebar-workspace` |
| 学习地图 | `data-learning-map-action="analyze"`、`refresh`、`open-overview-sources`、`assess-knowledge-point`、`open-knowledge-sources`、`assess-skill`、`open-skill-sources`、`open-assessment-sources` |
| 学习计划 | `data-learning-plan-action="refresh"`、`generate`、`confirm`、`preview-publication`、`open-obsidian-settings`、`move-up`、`move-down`、`open-sources`、`save`、`save-progress`；`data-learning-plan-tab="draft"`、`data-learning-plan-tab="confirmed"` |
| 学习计划字段 | `data-learning-plan-field="objective"`、`practice-question`、`completion-criteria`、`estimated-minutes`、`status` |
| 设置 | `data-settings-action="back"`、`connection-details`；`data-settings-page="answer"`、`data-settings-page="data"`、`data-settings-page="obsidian"`、`data-settings-page="appearance"`；`data-obsidian-settings`、`data-obsidian-pairing-form`、`data-obsidian-pairing-result` |

不得为了方便自动化测试平行新增另一套同义 `data-*`。确需新增时，先确定稳定业务语义，再同步本文档。

## 4. 文件修改边界

| 文件 / 目录 | Owner | 允许内容 | 禁止事项 |
|-------------|-------|----------|----------|
| `frontend/src/App.vue` | 集成 Owner | 视图装配、共享状态下发、事件处理、HTTP/SSE 用例编排 | 在展示组件中复制第二套集成状态；新增未经后端契约支持的请求 |
| `frontend/src/components/AppShell.vue` | 壳层 Owner | 布局、顶栏、默认插槽、侧边栏转发 | 直接调用业务 API；拥有教练或学习计划业务状态 |
| `frontend/src/components/WorkspaceSidebar.vue` | 导航 Owner | 导航、项目与线程选择事件 | 直接修改父级状态；把资料弹窗改成伪路由 |
| `frontend/src/views/WorkbenchView.vue` | 教练视图 Owner | 教练页面模块顺序和展示 | 直接发 HTTP/SSE；自行保存项目或聊天状态 |
| `frontend/src/views/LearningMapView.vue` | 学习地图 Owner | 地图、来源入口、评估入口展示 | 在前端重算服务端覆盖率或评估结论 |
| `frontend/src/views/LearningPlanView.vue` | 学习计划 Owner | 草稿编辑、确认和进度交互展示 | 绕过服务端能力标志或并发校验字段 |
| `frontend/src/views/SettingsView.vue` | 设置视图 Owner | 当前四个设置页签与表单展示 | 将禁用入口伪装为可用；回显明文 Key 或插件令牌 |
| `frontend/src/api/*.js` | API 边界 Owner | 调用 `api-spec.md` 中已存在的 HTTP/SSE 接口、前端参数规范化 | 新增未在 `api-spec.md` 定义的接口；在组件内散落 `fetch` |

任何需要同时改变页面装配和组件 API 的任务，都由 `App.vue` 集成 Owner 统一收口。

## 5. 命名与样式边界

| 类别 | 当前规则 |
|------|----------|
| 视图键 | 仅使用 `coach`、`learning-map`、`learning-plan`、`settings` |
| 资料 | 使用弹窗状态 `libraryModalOpen / libraryStep`，不创建 `library` 主视图键 |
| 根样式 | 壳层 `.workspace-shell`；教练 `.view-panel.chat-view`；学习地图 `.view-panel.learning-map-view`；学习计划 `.view-panel.learning-plan-view`；设置 `.settings-fullscreen` |
| 组件样式 | 保持组件或视图的既有语义前缀，单个模块不得通过无前缀选择器覆盖其他视图 |
| API 字段 | 前端 camelCase 仅用于组件 API；HTTP 请求和响应继续使用 `api-spec.md` 定义的 snake_case |

## 6. 页面验收口径

| 验收项 | 最低通过标准 |
|--------|--------------|
| 主导航 | 四个 `data-view-key` 能切换对应内容，资料入口只打开弹窗 |
| 状态保留 | 打开并关闭资料、来源、评估或发布覆盖层后，当前主视图和当前项目不被重置 |
| 教练 | 问题提交、SSE 输出、取消、聊天历史和依据区由同一 `App.vue` 状态链驱动 |
| 学习地图 | 未选项目、加载、错误、stale、空数据和正常数据均有明确展示 |
| 学习计划 | 草稿与已确认计划权限来自服务端；结构更新与进度更新保持分离 |
| 设置 | 回答和 Obsidian 使用真实接口；资料备份/恢复与外观未接入项保持禁用 |
| 响应式 | 760px 以下侧边栏可折叠和重新打开，主内容不依赖路由刷新 |

## 7. AI 编程边界

- 不得引入 `vue-router` 或新增主视图键，除非先更新架构与页面契约。
- 不得把 `App.vue` 的 API 编排复制到视图或展示组件。
- 不得用 mock 数据替代 `App.vue` 下发的真实状态。
- 不得在前端推导覆盖率、评估状态、学习计划权限或发布状态。
- 不得新增后端接口、请求字段或响应字段；需求存在缺口时先更新 `api-spec.md` 并完成后端实现。
- 不得让资料弹窗、来源抽屉、评估覆盖层或发布对话框隐式改变当前项目。

## 8. 提交前检查清单

- [ ] `App.vue` 仍是唯一页面集成 Owner
- [ ] 四个主视图键和资料弹窗边界未变化，或已同步本契约
- [ ] props / emits 变化已同步 `component-api-contract.md`
- [ ] 新增或修改的 HTTP/SSE 调用已在 `api-spec.md` 存在
- [ ] 稳定 `data-*` 标识未被无说明重命名
- [ ] 设置中的未接入能力没有被伪装为可用
- [ ] 页面主路径、覆盖层关闭和窄屏侧边栏均已验证
