# B-141U Vue 工作台回答反馈迁移计划

> 状态：Active
> 创建时间：2026-05-28
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md（接口契约沿用既有 `/api/answer/feedback`，不新增或修改 API）

## 1. 目标

在 Vue 工作台迁移回答反馈最小入口，复用既有 `POST /api/answer/feedback` 契约。用户在 Vue 工作台完成一次非流式问答后，可以对本次回答标记“有用 / 无用 / 来源不准 / 需要更多上下文”，页面展示保存状态。

本片不迁移 Workbench SSE/取消、聊天会话/历史管理、Agent 工具、检索调试、反馈备注输入、后端评分规则或数据库 schema。

## 2. 前置条件

- B-141D 已提供 Vue 工作台非流式问答入口，`POST /api/answer` 响应中包含可用于反馈的 `message.id`。
- `docs/design/api-spec.md` 已定义 `POST /api/answer/feedback` 契约和允许的 `rating` 枚举。
- legacy 静态前端已有回答反馈按钮，可作为 Vue 文案和状态行为参考。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141U plan，并将 BACKLOG 说明列追加本 plan 路径。
- [x] 增加 Vue 源码契约红灯测试，覆盖反馈 helper、AnswerPanel 反馈按钮、Workbench/App 事件和状态流。
- [x] 实现 `frontend/src/api/answer.js` 回答反馈 helper、`AnswerPanel.vue` 反馈入口、`WorkbenchView.vue` 事件透传和 `App.vue` 状态处理。
- [x] 运行聚焦 Vue 测试和 Vite build，确认本片前端实现通过。
- [x] 同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog。
- [x] 完成 Web MVP 全量、legacy 回归与浏览器烟测，并回写 plan 状态快照。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/answer.js` | 修改：新增回答反馈 API helper |
| 代码 | `frontend/src/components/AnswerPanel.vue` | 修改：新增回答反馈按钮与状态展示 |
| 代码 | `frontend/src/views/WorkbenchView.vue` | 修改：透传回答反馈事件和状态 |
| 代码 | `frontend/src/App.vue` | 修改：保存最后回答 message id，处理反馈提交状态 |
| 代码 | `frontend/src/state/app-state.js` | 修改：补充回答反馈提交/错误/状态字段 |
| 代码 | `frontend/src/styles.css` | 修改：补充反馈按钮组样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 Vue 回答反馈源码契约测试 |
| 文档 | `docs/features/frontend-engineering.md` | 修改：同步 B-141U 用户可见行为和非目标 |
| 文档 | `docs/design/architecture-overview.md` | 修改：同步 Vue 工作台回答反馈迁移状态 |
| 文档 | `docs/guides/testing.md` | 修改：补充 Vue 回答反馈验证要求 |
| 文档 | `CHANGELOG.md` | 修改：追加未发布变更 |
| 文档 | `docs/devlog/2026-05-28.md` | 修改：记录本片执行与验证 |
| 文档 | `docs/BACKLOG.md` | 修改：追加本 plan 路径 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-api-layout.md` | 需要 Vue API client 和共享状态模型 |
| `docs/plans/B-141-vue-project-space.md` | 回答反馈需要当前项目空间选择状态 |
| `docs/plans/B-141-vue-workbench-answer-entry.md` | 回答反馈依赖非流式问答响应中的 `message.id` |

### 5.2 与现有 plan 的重叠

创建本 plan 时扫描到 B-141A 至 B-141T 计划文件仍保留为 `Active`，但 § 9 均显示对应任务已完成；按项目规则视为已完成但未删除的迁移记录。本片只扩展 Vue 工作台回答反馈，不清理既有 plan 文件。

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-workbench-answer-entry.md` | `frontend/src/api/answer.js`、`AnswerPanel.vue`、`WorkbenchView.vue`、`App.vue` 和问答状态字段 | 分区：B-141U 只新增回答反馈入口，不改非流式问答提交和回答渲染契约 |
| `docs/plans/B-141-vue-api-layout.md` | `frontend/src/state/app-state.js`、`frontend/src/App.vue` 共享状态和基础视图壳 | 分区：B-141U 只追加回答反馈状态，不改基础布局 |

## 6. 完成标准

- [x] 功能行为符合 `docs/features/frontend-engineering.md` 的 B-141U 业务规则。
- [x] Vue 工作台在一次回答返回 `message.id` 后展示回答反馈入口。
- [x] Vue 工作台可提交 `useful / not_useful / source_wrong / need_more_context` 四类反馈。
- [x] Vue 工作台反馈保存后展示对应中文状态；提交失败时展示错误。
- [x] 反馈 helper 只调用既有 `POST /api/answer/feedback` 契约，不新增接口、不修改数据库 schema。
- [x] 测试通过（参照 `docs/guides/testing.md` 最低要求）。
- [x] 相关文档已同步（见下方"回流清单"）。
- [x] B-141 保持 `doing`；本片完成后不删除 B-141 总任务。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141U 用户可见行为、非目标和验收标准 | `docs/features/frontend-engineering.md` | [x] |
| Vue 工作台回答反馈 helper、状态和组件职责 | `docs/design/architecture-overview.md` | [x] |
| Vue 回答反馈测试要求和回归检查 | `docs/guides/testing.md` | [x] |
| 未发布变更记录 | `CHANGELOG.md` | [x] |
| 当日执行记录和验证结果 | `docs/devlog/2026-05-28.md` | [x] |
| B-141 关联 plan 路径和状态 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-28：创建 B-141U plan；选择 Vue 工作台回答反馈作为下一薄片，原因是只复用既有 `/api/answer/feedback`，范围小于 SSE/会话、Agent 工具或检索调试。
- 2026-05-28：将 `docs/plans/B-141-vue-answer-feedback.md` 追加到 BACKLOG B-141 说明列；顺手修正 B-141T plan 快照的最终提交号为 `4ef41eb`。
- 2026-05-28：新增 Vue 回答反馈源码契约红灯测试；聚焦运行 `tests/test_webapp/test_frontend_vue_app.py` 得到 3 failed / 52 passed，失败点为缺少反馈 helper、AnswerPanel 反馈控件和 App 状态流。
- 2026-05-28：实现 Vue 回答反馈 helper、显式四类反馈按钮和 App 状态流；聚焦测试 `tests/test_webapp/test_frontend_vue_app.py` 为 55 passed，`npm run build` 成功。
- 2026-05-28：同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog；B-141U 明确不迁移反馈备注输入、Workbench SSE/取消、聊天会话/历史、Agent 工具、检索调试或数据库 schema。
- 2026-05-28：完成 Web MVP 全量 326 passed、legacy 回归 179 passed、最终前端构建和浏览器烟测；临时项目 `B-141U-smoke-20260528013115` 已删除，本地服务已停止。

## 9. 状态快照

- **最后更新**：2026-05-28 01:38
- **进度**：已完成 6 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`待提交` — docs: 更新 B-141U 验证快照
- **代码状态**：`fix/url-virtual-source-preserve`；工作区存在多项用户/历史未提交改动，本片仅允许暂存 B-141U 相关文件
- **下一步**：B-141 可继续迁移 Workbench SSE/会话、Agent 工具、检索调试或评估题库/历史列表
- **续任务须知**：不修改后端 `/api/answer/feedback` 契约、不修改数据库 schema；不要清理既有 B-141 历史 plan 文件
