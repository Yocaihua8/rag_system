# B-141W Vue 工作台 Agent 只读工具迁移计划

> 状态：Active
> 创建时间：2026-05-28
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md（接口契约沿用既有 `/api/agent/tools*`，不新增或修改 API）

## 1. 目标

在 Vue 工作台迁移 Agent 只读工具最小面板，复用既有 `GET /api/agent/tools`、`POST /api/agent/tools/run`、`GET /api/agent/tools/runs` 和 `GET /api/agent/tools/runs/detail` 契约。用户在选择项目空间后，可以查看只读工具元数据，运行 `project_overview` 和 `search_sources`，查看工具运行结果、运行历史和单条详情。

本片不迁移回答区工具建议按钮、工具来源回填到下一问、Workbench SSE/取消、聊天会话/历史、Agent 自动编排、工具白名单权限逻辑、后端 API 或数据库 schema。

## 2. 前置条件

- B-141C 已提供 Vue 项目空间选择状态。
- B-141D/B-141U/B-141V 已提供工作台问答、反馈和检索调试布局。
- `docs/design/api-spec.md` 已定义 Agent 只读工具 API 契约和只读白名单边界。
- legacy 静态前端已有 Agent 工具面板，可作为 Vue 文案和展示参考。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141W plan，并将 BACKLOG 说明列追加本 plan 路径。
- [x] 增加 Vue 源码契约红灯测试，覆盖 Agent 工具 helper、AgentToolsPanel 控件和 Workbench/App 状态流。
- [x] 实现 `frontend/src/api/agent.js` helper、`AgentToolsPanel.vue` 工具面板、`WorkbenchView.vue` 事件透传和 `App.vue` 状态处理。
- [x] 运行聚焦 Vue 测试和 Vite build，确认本片前端实现通过。
- [x] 同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog。
- [ ] 完成 Web MVP 全量、legacy 回归与浏览器烟测，并回写 plan 状态快照。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/agent.js` | 新增：Vue Agent 工具 API helper |
| 代码 | `frontend/src/components/AgentToolsPanel.vue` | 新增：只读工具列表、运行入口、结果、历史和详情展示 |
| 代码 | `frontend/src/views/WorkbenchView.vue` | 修改：挂载 AgentToolsPanel 并透传事件/状态 |
| 代码 | `frontend/src/App.vue` | 修改：读取工具元数据、运行工具、刷新历史、读取详情 |
| 代码 | `frontend/src/state/app-state.js` | 修改：补充 Agent 工具提交/错误/状态字段 |
| 代码 | `frontend/src/styles.css` | 修改：补充 Agent 工具面板样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 Vue Agent 工具源码契约测试 |
| 文档 | `docs/features/frontend-engineering.md` | 修改：同步 B-141W 用户可见行为和非目标 |
| 文档 | `docs/design/architecture-overview.md` | 修改：同步 Vue 工作台 Agent 工具迁移状态 |
| 文档 | `docs/guides/testing.md` | 修改：补充 Vue Agent 工具验证要求 |
| 文档 | `CHANGELOG.md` | 修改：追加未发布变更 |
| 文档 | `docs/devlog/2026-05-28.md` | 修改：记录本片执行与验证 |
| 文档 | `docs/BACKLOG.md` | 修改：追加本 plan 路径 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-api-layout.md` | 需要 Vue API client 和共享状态模型 |
| `docs/plans/B-141-vue-project-space.md` | Agent 工具运行需要当前项目空间选择状态 |
| `docs/plans/B-141-vue-workbench-answer-entry.md` | 复用工作台布局和问答区域 |
| `docs/plans/B-141-vue-search-debug.md` | 复用工作台诊断/结果展示风格 |

### 5.2 与现有 plan 的重叠

创建本 plan 时扫描到 B-141A 至 B-141V 计划文件仍保留为 `Active`，但 § 9 均显示对应任务已完成；按项目规则视为已完成但未删除的迁移记录。本片只扩展 Vue 工作台 Agent 只读工具，不清理既有 plan 文件。

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-workbench-answer-entry.md` | `WorkbenchView.vue`、`App.vue` 和工作台状态字段 | 分区：B-141W 只新增 Agent 工具面板，不改非流式问答提交和回答渲染契约 |
| `docs/plans/B-141-vue-answer-feedback.md` | `WorkbenchView.vue`、`App.vue`、`frontend/src/api/answer.js` 周边工作台状态 | 分区：B-141W 不修改回答反馈 helper 和反馈提交状态 |
| `docs/plans/B-141-vue-search-debug.md` | `WorkbenchView.vue`、`App.vue` 和工作台诊断区域 | 分区：B-141W 不修改检索调试 helper、参数或结果结构 |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/frontend-engineering.md` 的 B-141W 业务规则。
- [ ] Vue 工作台展示 `project_overview` 和 `search_sources` 只读工具元数据。
- [ ] Vue 工作台可运行 `project_overview` 并展示项目、文档、分块、向量和对话统计。
- [ ] Vue 工作台可输入 query 运行 `search_sources` 并展示命中数量和来源片段。
- [ ] Vue 工作台展示当前项目工具运行历史，并可读取单条运行详情。
- [ ] Agent helper 只调用既有 `/api/agent/tools*` 契约，不修改工具白名单、不自动执行工具、不修改数据库 schema。
- [ ] 测试通过（参照 `docs/guides/testing.md` 最低要求）。
- [ ] 相关文档已同步（见下方"回流清单"）。
- [ ] B-141 保持 `doing`；本片完成后不删除 B-141 总任务。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141W 用户可见行为、非目标和验收标准 | `docs/features/frontend-engineering.md` | [x] |
| Vue 工作台 Agent helper、状态和组件职责 | `docs/design/architecture-overview.md` | [x] |
| Vue Agent 工具测试要求和回归检查 | `docs/guides/testing.md` | [x] |
| 未发布变更记录 | `CHANGELOG.md` | [x] |
| 当日执行记录和验证结果 | `docs/devlog/2026-05-28.md` | [x] |
| B-141 关联 plan 路径和状态 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-28：创建 B-141W plan；选择 Vue 工作台 Agent 只读工具作为下一薄片，原因是后端 `/api/agent/tools*` 契约和 legacy 面板已存在，Vue 侧可限定为工具元数据、手动运行、历史和详情展示。
- 2026-05-28：将 `docs/plans/B-141-vue-agent-tools.md` 追加到 BACKLOG B-141 说明列。
- 2026-05-28：新增 Vue Agent 工具源码契约红灯测试；聚焦运行 `tests/test_webapp/test_frontend_vue_app.py` 得到 3 failed / 58 passed，失败点为缺少 Agent 工具 helper、AgentToolsPanel 和 App/Workbench 状态流。
- 2026-05-28：实现 Vue Agent 工具 helper、工作台只读工具面板和 App 状态流；聚焦测试 `tests/test_webapp/test_frontend_vue_app.py` 为 61 passed，`npm run build` 成功。
- 2026-05-28：同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog；B-141W 明确不迁移回答区工具建议按钮、工具来源回填到下一问、Workbench SSE/取消、聊天会话/历史、Agent 自动编排、工具白名单权限逻辑、后端 API 或数据库 schema。

## 9. 状态快照

- **最后更新**：2026-05-28 02:20
- **进度**：已完成 5 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`e1f7d61` — feat: 接入 Vue 工作台 Agent 只读工具
- **代码状态**：`fix/url-virtual-source-preserve`；工作区存在多项用户/历史未提交改动，本片仅允许暂存 B-141W 相关文件
- **下一步**：完成 Web MVP 全量、legacy 回归与浏览器烟测，并回写 plan 状态快照
- **续任务须知**：不修改后端 `/api/agent/tools*` 契约、不改变只读白名单权限、不做工具建议自动运行、不做工具来源回填、不修改数据库 schema；不要清理既有 B-141 历史 plan 文件
