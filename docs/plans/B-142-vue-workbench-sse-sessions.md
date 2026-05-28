# B-142 Vue 工作台 SSE 与会话历史迁移

> 状态：Active
> 创建时间：2026-05-28
> 创建方：Codex
> 关联 BACKLOG：B-142
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md

## 1. 目标

把 Vue 工作台补齐为旧静态前端保留的主问答能力：使用既有 `/api/answer/stream` 进行 EventSource 流式输出，支持关闭当前流式请求，并接入既有 `/api/chat/sessions*` 与 `/api/chat/messages` 会话列表和历史恢复。任务不修改后端 API 契约、不修改 SQLite schema、不删除 `webapp/static/`。

## 2. 前置条件

- 已读取 `AGENTS.md`、`docs/BACKLOG.md`、`docs/features/frontend-engineering.md`、`docs/design/api-spec.md`、`docs/guides/testing.md`。
- B-141 已完成，Vue 工作台已有非流式问答、回答反馈、检索调试、Agent 工具和工具来源上下文入口。
- 后端已有 `/api/answer/stream`、`/api/chat/sessions*` 与 `/api/chat/messages` 契约，B-142 只做 Vue 侧接入。

## 3. 任务拆解

- [x] Vue 工作台接入流式问答和取消按钮：先补 `tests/test_webapp/test_frontend_vue_app.py` 红灯断言，再实现 `frontend/src/api/answer.js`、`QuestionPanel.vue`、`AnswerPanel.vue`、`WorkbenchView.vue`、`App.vue` 和 `app-state.js` 中的 EventSource 状态流。
- [x] Vue 工作台接入会话列表和历史恢复：先补 Vue 源码测试红灯断言，再新增/实现 `frontend/src/api/chat.js`、会话面板组件、`WorkbenchView.vue`、`App.vue` 和 `app-state.js` 中的会话状态流。
- [ ] 文档回流和收口验证：更新 `docs/features/frontend-engineering.md`、`docs/guides/testing.md`、`docs/BACKLOG.md`，运行指定验证，完成后删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/answer.js` | 修改：新增 EventSource 流式问答 helper，保留非流式兼容 |
| 代码 | `frontend/src/api/chat.js` | 新增：封装会话和消息 API helper |
| 代码 | `frontend/src/state/app-state.js` | 修改：补齐流式回答、取消、会话和历史状态字段 |
| 代码 | `frontend/src/components/QuestionPanel.vue` | 修改：增加取消当前回答入口 |
| 代码 | `frontend/src/components/AnswerPanel.vue` | 修改：展示流式回答增量、会话历史相关状态 |
| 代码 | `frontend/src/components/ChatSessionPanel.vue` | 新增：会话列表、新建、重命名、删除和消息历史入口 |
| 代码 | `frontend/src/views/WorkbenchView.vue` | 修改：接入会话面板与流式事件 |
| 代码 | `frontend/src/App.vue` | 修改：接入流式问答、取消、会话加载和历史恢复状态流 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：新增 B-142 Vue 源码契约断言 |
| 文档 | `docs/features/frontend-engineering.md` | 修改：记录 B-142 已完成行为和边界 |
| 文档 | `docs/guides/testing.md` | 修改：补充 Vue 工作台 SSE/会话验证要求 |
| 文档 | `docs/BACKLOG.md` | 修改：B-142 生命周期状态更新 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-141 已完成，当前无未完成依赖 plan |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | 创建本 plan 前扫描 `docs/plans/` 与 `docs/superpowers/plans/`，未发现 Active/Interrupted plan 覆盖 `frontend/src`、`/api/answer/stream` 或 `/api/chat/*` | N/A |

## 6. 完成标准

- [ ] Vue 工作台使用 `/api/answer/stream` EventSource 渲染增量回答，并在 `done` 后保留完整响应、来源、质量提示、观察性信息和回答反馈消息 ID。
- [ ] 用户可取消当前流式请求；取消后关闭 EventSource、恢复按钮状态，并保留明确取消提示。
- [ ] Vue 工作台可读取、创建、重命名、删除当前项目聊天会话，并按当前会话读取历史消息。
- [ ] 会话切换后历史消息和下一轮问答 `session_id` 与当前会话一致；工具来源上下文仍只在用户显式选择后发送。
- [ ] `tests/test_webapp/test_frontend_vue_app.py`、`npm run build`、`tests/test_webapp -q` 验证结果已记录。
- [ ] 相关文档已同步，BACKLOG B-142 状态已更新为 `done`。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-142 Vue 工作台 SSE、取消、会话和历史恢复行为 | `docs/features/frontend-engineering.md` | [ ] |
| Vue 工作台 SSE/会话测试要求 | `docs/guides/testing.md` | [ ] |
| B-142 完成状态与 B-143 前置条件解除 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-05-28 15:22：确认用户已同意执行；创建 `fix/b-142-vue-workbench-sse-sessions` 分支；冲突扫描未发现覆盖本任务影响范围的 Active/Interrupted plan。
- 2026-05-28 15:31：完成 Vue 工作台流式问答和取消按钮薄片；红灯先失败于缺少 `streamQuestion`、取消入口和 App 状态流；实现后 `tests/test_webapp/test_frontend_vue_app.py -q` 与 `npm run build` 通过。
- 2026-05-28 15:41：完成 Vue 工作台会话列表和历史恢复薄片；红灯先失败于缺少 `chat.js`、`ChatSessionPanel.vue` 和 App 会话状态流；实现后 `tests/test_webapp/test_frontend_vue_app.py -q` 与 `npm run build` 通过。

## 9. 状态快照

- **最后更新**：2026-05-28 15:41
- **进度**：已完成 2 / 3 项（见 § 3 勾选状态）
- **最新 commit**：待提交 — Vue 工作台会话列表和历史恢复
- **代码状态**：`fix/b-142-vue-workbench-sse-sessions`；会话/历史恢复薄片待提交
- **下一步**：文档回流和收口验证
- **续任务须知**：`chat.js` 已封装既有 `/api/chat/*`；`ChatSessionPanel` 只做前端状态和已有 API 调用，不新增后端契约。
