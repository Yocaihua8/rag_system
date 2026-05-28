# B-141Y Vue 项目级检索默认值迁移计划

> 状态：Active
> 创建时间：2026-05-28
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md（接口契约沿用既有 `GET/POST /api/projects/retrieval-settings`，不新增或修改 API）

## 1. 目标

在 Vue 工作台迁移项目级检索默认值的最小闭环。用户选择项目空间后，检索调试区会读取当前项目保存的 `top_k`、`min_score`、`use_keyword`、`use_vector` 默认值，允许用户调整并保存为默认；后续检索诊断和问答继续由后端共用这组项目默认值。

本片不迁移检索复盘保存/列表/详情/删除、普通搜索结果列表、Workbench SSE/取消、聊天会话/历史、检索算法、后端 API 或数据库 schema。

## 2. 前置条件

- B-141V 已提供 Vue 检索调试入口和 `SearchDebugPanel`。
- B-141X 已完成工作台回答区工具建议与来源上下文，不影响本片检索默认值。
- `docs/design/api-spec.md` 已定义 `GET/POST /api/projects/retrieval-settings` 契约。
- legacy 静态前端已有读取检索默认值、保存默认值并回填调试参数的行为，可作为 Vue 展示边界参考。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141Y plan，并将 BACKLOG 说明列追加本 plan 路径。
- [x] 增加 Vue 源码契约红灯测试，覆盖检索默认值 helper、`SearchDebugPanel` 默认值/保存控件、`WorkbenchView` 透传和 `App.vue` 状态流。
- [x] 实现 `projects.js` 检索默认值 helper、`SearchDebugPanel.vue` 默认值回填/保存入口、`WorkbenchView.vue` 透传和 `App.vue` 读取/保存状态。
- [ ] 运行聚焦 Vue 测试和 Vite build，确认本片前端实现通过。
- [ ] 同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog。
- [ ] 完成 Web MVP 全量、legacy 回归与浏览器烟测，并回写 plan 状态快照。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/projects.js` | 修改：增加读取/保存项目级检索默认值 helper |
| 代码 | `frontend/src/components/SearchDebugPanel.vue` | 修改：接收默认值、显示加载/保存状态、提供“保存为默认”入口 |
| 代码 | `frontend/src/views/WorkbenchView.vue` | 修改：透传检索默认值状态与保存事件 |
| 代码 | `frontend/src/App.vue` | 修改：项目切换/创建/加载时读取检索默认值，保存默认值后回填状态 |
| 代码 | `frontend/src/components/AppShell.vue` | 修改：迁移状态文案追加 B-141Y |
| 代码 | `frontend/src/state/app-state.js` | 修改：补足检索默认值读取/保存状态字段 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 Vue 检索默认值源码契约测试 |
| 文档 | `docs/features/frontend-engineering.md` | 修改：同步 B-141Y 用户可见行为和非目标 |
| 文档 | `docs/design/architecture-overview.md` | 修改：同步 Vue 工作台检索默认值迁移状态 |
| 文档 | `docs/guides/testing.md` | 修改：补充 Vue 检索默认值验证要求 |
| 文档 | `CHANGELOG.md` | 修改：追加未发布变更 |
| 文档 | `docs/devlog/2026-05-28.md` | 修改：记录本片执行与验证 |
| 文档 | `docs/BACKLOG.md` | 修改：追加本 plan 路径 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-project-space.md` | 检索默认值按当前项目空间读取和保存 |
| `docs/plans/B-141-vue-search-debug.md` | 本片复用 Vue 检索调试参数和结果展示 |
| `docs/plans/B-141-vue-tool-suggestion-context.md` | 同属工作台区域，需保持回答区工具来源状态不受影响 |

### 5.2 与现有 plan 的重叠

创建本 plan 时扫描到 B-141A 至 B-141X 计划文件仍保留为 `Active`，但 § 9 均显示对应任务已完成；按项目规则视为已完成但未删除的迁移记录。本片只扩展 Vue 工作台检索调试区的项目级默认值读取/保存，不清理既有 plan 文件。

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-search-debug.md` | `SearchDebugPanel.vue`、`WorkbenchView.vue`、`App.vue`、`frontend/src/api/search.js` 周边检索调试状态 | 分区：B-141Y 只增加默认值读取/保存，不修改 `/api/search/debug` 诊断契约或命中展示 |
| `docs/plans/B-141-vue-project-space.md` | `frontend/src/api/projects.js`、项目选择状态 | 分区：B-141Y 只扩展项目 helper，不修改项目空间 CRUD 与最近项目恢复 |
| `docs/plans/B-141-vue-tool-suggestion-context.md` | `WorkbenchView.vue`、`App.vue` 工作台状态 | 分区：B-141Y 不修改回答区工具建议、工具结果或 `tool_run_id` 状态流 |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/frontend-engineering.md` 的 B-141Y 业务规则。
- [ ] Vue `projects.js` 可读取和保存当前项目 `retrieval-settings`，未选择项目时给出明确前端错误或空状态。
- [ ] Vue 检索调试区会把已加载默认值回填到 `top_k`、`min_score`、关键词和向量控件。
- [ ] 用户点击“保存为默认”后调用既有 `POST /api/projects/retrieval-settings`，成功后显示保存状态并继续保留当前参数。
- [ ] 项目切换、项目创建和项目删除时检索默认值状态不会串到其他项目。
- [ ] 测试通过（参照 `docs/guides/testing.md` 最低要求）。
- [ ] 相关文档已同步（见下方"回流清单"）。
- [ ] B-141 保持 `doing`；本片完成后不删除 B-141 总任务。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141Y 用户可见行为、非目标和验收标准 | `docs/features/frontend-engineering.md` | [ ] |
| Vue 工作台检索默认值 helper、状态和组件职责 | `docs/design/architecture-overview.md` | [ ] |
| Vue 检索默认值测试要求 | `docs/guides/testing.md` | [ ] |
| 未发布变更记录 | `CHANGELOG.md` | [ ] |
| 当日执行记录和验证结果 | `docs/devlog/2026-05-28.md` | [ ] |
| B-141 关联 plan 路径和状态 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-28：创建 B-141Y plan；选择项目级检索默认值作为下一薄片，原因是后端 `GET/POST /api/projects/retrieval-settings` 契约已存在，B-141V 已迁移检索调试参数控件，可限定为 Vue 侧读取、回填和保存默认值。
- 2026-05-28：将 `docs/plans/B-141-vue-retrieval-settings.md` 追加到 BACKLOG B-141 说明列。
- 2026-05-28：新增 Vue 检索默认值源码契约红灯测试；聚焦运行 `tests/test_webapp/test_frontend_vue_app.py` 得到 3 failed / 63 passed，失败点为缺少 `retrieval-settings` helper、检索调试默认值/保存控件和 App 状态流。
- 2026-05-28：实现 Vue 检索默认值读取/保存状态流；`projects.js` 复用既有 `GET/POST /api/projects/retrieval-settings`，`SearchDebugPanel` 根据已加载默认值回填诊断参数并提供“保存为默认”入口，`App.vue` 在项目加载、切换和创建时读取当前项目默认值。

## 9. 状态快照

- **最后更新**：2026-05-28 12:39
- **进度**：已完成 3 / 6 项（见 § 3 勾选状态）
- **最新 commit**：待提交 — feat: 接入 Vue 检索默认值设置
- **代码状态**：`fix/url-virtual-source-preserve`；工作区存在多项用户/历史未提交改动，本片仅允许暂存 B-141Y 相关文件
- **下一步**：运行聚焦 Vue 测试和 Vite build，确认本片前端实现通过
- **续任务须知**：不修改后端 `/api/projects/retrieval-settings`、`/api/search/debug`、`/api/answer` 契约，不迁移检索复盘，不接入 SSE/会话，不修改数据库 schema；不要清理既有 B-141 历史 plan 文件
