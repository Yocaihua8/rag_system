# B-141V Vue 工作台检索调试迁移计划

> 状态：Active
> 创建时间：2026-05-28
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md（接口契约沿用既有 `/api/search/debug`，不新增或修改 API）

## 1. 目标

在 Vue 工作台迁移检索调试最小入口，复用既有 `POST /api/search/debug` 契约。用户在选择项目空间后，可以输入诊断查询，临时调整 `top_k`、`min_score`、关键词检索和向量检索开关，并查看命中片段、分数、来源质量、分块/向量状态和本次参数。

本片不迁移项目级检索默认值保存、检索复盘保存/列表/详情/删除、普通搜索结果列表、Workbench SSE/取消、聊天会话/历史、Agent 工具、检索算法或数据库 schema。

## 2. 前置条件

- B-141C 已提供 Vue 项目空间选择状态。
- `docs/design/api-spec.md` 已定义 `POST /api/search/debug` 契约和返回结构。
- legacy 静态前端已有检索调试面板，可作为 Vue 文案和只读展示参考。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141V plan，并将 BACKLOG 说明列追加本 plan 路径。
- [ ] 增加 Vue 源码契约红灯测试，覆盖检索调试 helper、SearchDebugPanel 控件和 Workbench/App 状态流。
- [ ] 实现 `frontend/src/api/search.js` 检索调试 helper、`SearchDebugPanel.vue` 诊断入口、`WorkbenchView.vue` 事件透传和 `App.vue` 状态处理。
- [ ] 运行聚焦 Vue 测试和 Vite build，确认本片前端实现通过。
- [ ] 同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog。
- [ ] 完成 Web MVP 全量、legacy 回归与浏览器烟测，并回写 plan 状态快照。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/search.js` | 新增：Vue 检索调试 API helper |
| 代码 | `frontend/src/components/SearchDebugPanel.vue` | 新增：检索调试表单、状态和结果展示 |
| 代码 | `frontend/src/views/WorkbenchView.vue` | 修改：挂载 SearchDebugPanel 并透传事件/状态 |
| 代码 | `frontend/src/App.vue` | 修改：处理检索调试提交状态和结果 |
| 代码 | `frontend/src/state/app-state.js` | 修改：补充检索调试提交/错误/状态字段 |
| 代码 | `frontend/src/styles.css` | 修改：补充检索调试控件和结果样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 Vue 检索调试源码契约测试 |
| 文档 | `docs/features/frontend-engineering.md` | 修改：同步 B-141V 用户可见行为和非目标 |
| 文档 | `docs/design/architecture-overview.md` | 修改：同步 Vue 工作台检索调试迁移状态 |
| 文档 | `docs/guides/testing.md` | 修改：补充 Vue 检索调试验证要求 |
| 文档 | `CHANGELOG.md` | 修改：追加未发布变更 |
| 文档 | `docs/devlog/2026-05-28.md` | 修改：记录本片执行与验证 |
| 文档 | `docs/BACKLOG.md` | 修改：追加本 plan 路径 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-api-layout.md` | 需要 Vue API client 和共享状态模型 |
| `docs/plans/B-141-vue-project-space.md` | 检索调试需要当前项目空间选择状态 |
| `docs/plans/B-141-vue-workbench-answer-entry.md` | 复用工作台布局和当前问题语义 |

### 5.2 与现有 plan 的重叠

创建本 plan 时扫描到 B-141A 至 B-141U 计划文件仍保留为 `Active`，但 § 9 均显示对应任务已完成；按项目规则视为已完成但未删除的迁移记录。本片只扩展 Vue 工作台检索调试，不清理既有 plan 文件。

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-workbench-answer-entry.md` | `WorkbenchView.vue`、`App.vue` 和工作台状态字段 | 分区：B-141V 只新增检索调试面板，不改非流式问答提交和回答渲染契约 |
| `docs/plans/B-141-vue-answer-feedback.md` | `WorkbenchView.vue`、`App.vue`、`frontend/src/api/answer.js` 周边工作台状态 | 分区：B-141V 不修改回答反馈 helper 和反馈提交状态 |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/frontend-engineering.md` 的 B-141V 业务规则。
- [ ] Vue 工作台在已选择项目空间时可提交检索诊断查询。
- [ ] Vue 工作台可临时设置 `top_k`、`min_score`、`use_keyword` 和 `use_vector`。
- [ ] Vue 工作台展示检索诊断来源质量、文档/分块数量、向量可用状态、本次参数和命中片段。
- [ ] 检索调试 helper 只调用既有 `POST /api/search/debug` 契约，不保存项目默认值、不创建检索复盘、不修改数据库 schema。
- [ ] 测试通过（参照 `docs/guides/testing.md` 最低要求）。
- [ ] 相关文档已同步（见下方"回流清单"）。
- [ ] B-141 保持 `doing`；本片完成后不删除 B-141 总任务。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141V 用户可见行为、非目标和验收标准 | `docs/features/frontend-engineering.md` | [ ] |
| Vue 工作台检索调试 helper、状态和组件职责 | `docs/design/architecture-overview.md` | [ ] |
| Vue 检索调试测试要求和回归检查 | `docs/guides/testing.md` | [ ] |
| 未发布变更记录 | `CHANGELOG.md` | [ ] |
| 当日执行记录和验证结果 | `docs/devlog/2026-05-28.md` | [ ] |
| B-141 关联 plan 路径和状态 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-28：创建 B-141V plan；选择 Vue 工作台检索调试作为下一薄片，原因是只复用既有 `/api/search/debug`，范围小于 Agent 工具、SSE/会话或检索复盘。
- 2026-05-28：将 `docs/plans/B-141-vue-search-debug.md` 追加到 BACKLOG B-141 说明列。

## 9. 状态快照

- **最后更新**：2026-05-28 02:02
- **进度**：已完成 1 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`待提交` — docs: 创建 B-141V 检索调试迁移计划
- **代码状态**：`fix/url-virtual-source-preserve`；工作区存在多项用户/历史未提交改动，本片仅允许暂存 B-141V 相关文件
- **下一步**：增加 Vue 检索调试 helper、组件和 App 状态流的红灯测试
- **续任务须知**：不修改后端 `/api/search/debug` 契约、不保存检索默认值、不创建检索复盘、不修改数据库 schema；不要清理既有 B-141 历史 plan 文件
