# B-141X Vue 工具建议与来源上下文迁移计划

> 状态：Active
> 创建时间：2026-05-28
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md（接口契约沿用既有 `/api/answer`、`/api/agent/tools/run` 和 `tool_run_id`，不新增或修改 API）

## 1. 目标

在 Vue 工作台迁移回答区工具建议与工具来源带入下一问的最小闭环。用户在回答无来源或来源不足时，可以看到后端返回的 `tool_suggestion`，手动运行建议的只读 `search_sources` 工具，并把成功的工具运行结果标记为下一次 `/api/answer` 的 `tool_run_id` 上下文。

本片不迁移 SSE 流式输出、取消按钮、聊天会话/历史、Agent 自动编排、工具白名单权限逻辑、检索复盘、后端 API 或数据库 schema。

## 2. 前置条件

- B-141D 已提供 Vue 非流式问答入口。
- B-141W 已提供 Vue Agent 只读工具 helper、运行结果、运行历史和详情面板。
- `docs/design/api-spec.md` 已定义 `/api/answer` 的 `tool_suggestion`、`tool_context` 和 `tool_run_id` 契约。
- legacy 静态前端已有手动运行建议工具、可用工具结果和下一问上下文提示，可作为 Vue 展示边界参考。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141X plan，并将 BACKLOG 说明列追加本 plan 路径。
- [x] 增加 Vue 源码契约红灯测试，覆盖 `tool_run_id` helper、回答区工具建议控件、可用工具结果和下一问上下文状态流。
- [x] 实现 `answer.js` 可选 `toolRunId`、`AnswerPanel.vue` 建议工具/上下文 UI、`App.vue` 状态处理和手动运行建议工具逻辑。
- [x] 运行聚焦 Vue 测试和 Vite build，确认本片前端实现通过。
- [ ] 同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog。
- [ ] 完成 Web MVP 全量、legacy 回归与浏览器烟测，并回写 plan 状态快照。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/answer.js` | 修改：`askQuestion` 支持可选 `toolRunId` 并发送 `tool_run_id` |
| 代码 | `frontend/src/components/AnswerPanel.vue` | 修改：展示工具建议、可用工具结果和下一问上下文提示 |
| 代码 | `frontend/src/views/WorkbenchView.vue` | 修改：透传工具建议与上下文事件/状态 |
| 代码 | `frontend/src/App.vue` | 修改：保存 `tool_suggestion`，手动运行 `search_sources`，设置/消耗下一问工具上下文 |
| 代码 | `frontend/src/state/app-state.js` | 修改：复用并补足 `currentToolSuggestion/currentToolContextRunId/lastUsableToolRun` 周边状态 |
| 代码 | `frontend/src/styles.css` | 修改：补充回答区建议工具与上下文提示样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 Vue 工具建议与来源上下文源码契约测试 |
| 文档 | `docs/features/frontend-engineering.md` | 修改：同步 B-141X 用户可见行为和非目标 |
| 文档 | `docs/design/architecture-overview.md` | 修改：同步 Vue 工作台工具建议/来源上下文迁移状态 |
| 文档 | `docs/guides/testing.md` | 修改：补充 Vue 工具建议和 `tool_run_id` 验证要求 |
| 文档 | `CHANGELOG.md` | 修改：追加未发布变更 |
| 文档 | `docs/devlog/2026-05-28.md` | 修改：记录本片执行与验证 |
| 文档 | `docs/BACKLOG.md` | 修改：追加本 plan 路径 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-workbench-answer-entry.md` | 需要 Vue 非流式问答入口和回答展示 |
| `docs/plans/B-141-vue-answer-feedback.md` | 需要回答区状态和反馈区布局边界 |
| `docs/plans/B-141-vue-agent-tools.md` | 需要 Vue Agent 工具 helper、运行结果和历史刷新能力 |

### 5.2 与现有 plan 的重叠

创建本 plan 时扫描到 B-141A 至 B-141W 计划文件仍保留为 `Active`，但 § 9 均显示对应任务已完成；按项目规则视为已完成但未删除的迁移记录。本片只扩展 Vue 工作台回答区的工具建议与下一问工具上下文，不清理既有 plan 文件。

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-workbench-answer-entry.md` | `frontend/src/api/answer.js`、`AnswerPanel.vue`、`App.vue` | 分区：B-141X 只增加 `tool_run_id` 和工具建议状态，不改非流式问答基础契约 |
| `docs/plans/B-141-vue-answer-feedback.md` | `AnswerPanel.vue`、`App.vue` 回答区状态 | 分区：B-141X 不修改反馈 rating、提交接口或反馈保存状态 |
| `docs/plans/B-141-vue-agent-tools.md` | `frontend/src/api/agent.js`、`App.vue` Agent 工具运行状态 | 分区：B-141X 复用 `runAgentTool`，不修改工具元数据、历史详情和白名单权限 |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/frontend-engineering.md` 的 B-141X 业务规则。
- [ ] Vue `askQuestion` 可选发送 `tool_run_id`，未设置上下文时不改变原请求体。
- [ ] Vue 回答区展示 `tool_suggestion`，并提供手动运行建议 `search_sources` 的按钮。
- [ ] 建议工具运行成功后展示可用工具结果，并允许用户标记为下一问上下文。
- [ ] 下一次提问会携带 `tool_run_id`，回答完成后显示 `tool_context` 并自动消耗当前工具上下文。
- [ ] 项目切换、项目删除和新建项目时清理工具建议、可用工具结果和上下文状态。
- [ ] 测试通过（参照 `docs/guides/testing.md` 最低要求）。
- [ ] 相关文档已同步（见下方"回流清单"）。
- [ ] B-141 保持 `doing`；本片完成后不删除 B-141 总任务。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141X 用户可见行为、非目标和验收标准 | `docs/features/frontend-engineering.md` | [ ] |
| Vue 工作台工具建议、`tool_run_id` 和上下文状态职责 | `docs/design/architecture-overview.md` | [ ] |
| Vue 工具建议和来源上下文测试要求 | `docs/guides/testing.md` | [ ] |
| 未发布变更记录 | `CHANGELOG.md` | [ ] |
| 当日执行记录和验证结果 | `docs/devlog/2026-05-28.md` | [ ] |
| B-141 关联 plan 路径和状态 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-28：创建 B-141X plan；选择 Vue 工具建议与来源上下文作为下一薄片，原因是 `/api/answer` 已返回 `tool_suggestion/tool_context` 且 B-141W 已迁移 Agent 只读工具运行能力，可限定为前端手动运行和 `tool_run_id` 状态流。
- 2026-05-28：将 `docs/plans/B-141-vue-tool-suggestion-context.md` 追加到 BACKLOG B-141 说明列。
- 2026-05-28：新增 Vue 工具建议与来源上下文源码契约红灯测试；聚焦运行 `tests/test_webapp/test_frontend_vue_app.py` 得到 3 failed / 60 passed，失败点为缺少 `toolRunId` 请求参数、回答区工具建议/上下文控件和 App 状态流。
- 2026-05-28：实现 Vue 工具建议与来源上下文状态流；聚焦测试 `tests/test_webapp/test_frontend_vue_app.py` 为 63 passed，`npm run build` 成功。

## 9. 状态快照

- **最后更新**：2026-05-28 02:58
- **进度**：已完成 4 / 6 项（见 § 3 勾选状态）
- **最新 commit**：待提交 — feat: 接入 Vue 工具建议来源上下文
- **代码状态**：`fix/url-virtual-source-preserve`；工作区存在多项用户/历史未提交改动，本片仅允许暂存 B-141X 相关文件
- **下一步**：同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog
- **续任务须知**：不修改后端 `/api/answer`、`/api/agent/tools*` 契约，不改变工具白名单权限，不做自动工具编排，不接入 SSE/取消，不迁移聊天会话/历史，不修改数据库 schema；不要清理既有 B-141 历史 plan 文件
