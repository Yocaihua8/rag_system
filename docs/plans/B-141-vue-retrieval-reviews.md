# B-141Z Vue 检索复盘迁移计划

> 状态：Active
> 创建时间：2026-05-28
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md（接口契约沿用既有 `GET/POST /api/retrieval/reviews`、`GET /api/retrieval/reviews/detail`、`POST /api/retrieval/reviews/delete`，不新增或修改 API）

## 1. 目标

在 Vue 工作台迁移检索复盘的最小闭环。用户运行检索诊断后，可以填写人工备注并保存一次复盘快照；工作台显示当前项目的复盘列表，支持查看单条详情和删除复盘记录。复盘快照仍由后端按 `query/top_k/min_score/use_keyword/use_vector` 重新检索后保存，不信任前端传回的命中结果。

本片不迁移普通搜索结果页、检索健康项目卡、Workbench SSE/取消、聊天会话/历史、评估题库/历史、检索算法、后端 API 或数据库 schema。

## 2. 前置条件

- B-141V 已提供 Vue 检索调试入口和 `SearchDebugPanel`。
- B-141Y 已迁移项目级检索默认值，检索调试参数已可稳定回填。
- `docs/design/api-spec.md` 已定义检索复盘保存、列表、详情和删除契约。
- legacy 静态前端已有检索复盘保存、列表、详情和删除行为，可作为 Vue 展示边界参考。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141Z plan，并将 BACKLOG 说明列追加本 plan 路径。
- [x] 增加 Vue 源码契约红灯测试，覆盖检索复盘 API helper、`SearchDebugPanel` 保存/列表/详情/删除控件、`WorkbenchView` 透传和 `App.vue` 状态流。
- [ ] 实现 `search.js` 检索复盘 helper、`SearchDebugPanel.vue` 复盘 UI、`WorkbenchView.vue` 透传和 `App.vue` 读取/保存/详情/删除状态。
- [ ] 运行聚焦 Vue 测试和 Vite build，确认本片前端实现通过。
- [ ] 同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog。
- [ ] 完成 Web MVP 全量、legacy 回归与浏览器烟测，并回写 plan 状态快照。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/search.js` | 修改：增加检索复盘保存、列表、详情和删除 helper |
| 代码 | `frontend/src/components/SearchDebugPanel.vue` | 修改：在检索调试区增加复盘备注、保存按钮、列表、详情和删除入口 |
| 代码 | `frontend/src/views/WorkbenchView.vue` | 修改：透传检索复盘状态与事件 |
| 代码 | `frontend/src/App.vue` | 修改：项目加载/切换时读取复盘列表，处理保存、详情、删除状态 |
| 代码 | `frontend/src/components/AppShell.vue` | 修改：迁移状态文案追加 B-141Z |
| 代码 | `frontend/src/state/app-state.js` | 修改：补足检索复盘列表、详情、加载、保存、删除状态字段 |
| 样式 | `frontend/src/styles.css` | 修改：补充检索复盘列表与详情的局部样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 Vue 检索复盘源码契约测试 |
| 文档 | `docs/features/frontend-engineering.md` | 修改：同步 B-141Z 用户可见行为和非目标 |
| 文档 | `docs/design/architecture-overview.md` | 修改：同步 Vue 工作台检索复盘迁移状态 |
| 文档 | `docs/guides/testing.md` | 修改：补充 Vue 检索复盘验证要求 |
| 文档 | `CHANGELOG.md` | 修改：追加未发布变更 |
| 文档 | `docs/devlog/2026-05-28.md` | 修改：记录本片执行与验证 |
| 文档 | `docs/BACKLOG.md` | 修改：追加本 plan 路径 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-search-debug.md` | 复盘保存复用检索诊断查询与参数 |
| `docs/plans/B-141-vue-retrieval-settings.md` | 复盘表单需与当前项目默认参数保持一致 |
| `docs/plans/B-141-vue-project-space.md` | 复盘列表按当前项目隔离读取和清理 |

### 5.2 与现有 plan 的重叠

创建本 plan 时扫描到 B-141A 至 B-141Y 计划文件仍保留为 `Active`，但 § 9 均显示对应任务已完成；按项目规则视为已完成但未删除的迁移记录。本片只扩展 Vue 工作台检索调试区的检索复盘读取/保存/详情/删除，不清理既有 plan 文件。

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-search-debug.md` | `SearchDebugPanel.vue`、`WorkbenchView.vue`、`App.vue`、`frontend/src/api/search.js` 周边检索调试状态 | 分区：B-141Z 只增加复盘持久化和历史展示，不修改 `/api/search/debug` 诊断契约或命中展示 |
| `docs/plans/B-141-vue-retrieval-settings.md` | `SearchDebugPanel.vue` 检索参数和默认值状态 | 分区：B-141Z 复用当前诊断参数，不修改项目级默认值读取/保存逻辑 |
| `docs/plans/B-141-vue-tool-suggestion-context.md` | `WorkbenchView.vue`、`App.vue` 工作台状态 | 分区：B-141Z 不修改回答区工具建议、工具结果或 `tool_run_id` 状态流 |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/frontend-engineering.md` 的 B-141Z 业务规则。
- [ ] Vue `search.js` 可保存、列出、读取详情并删除当前项目检索复盘。
- [ ] Vue 检索调试区仅在有项目空间时启用复盘保存；无查询时给出明确错误。
- [ ] 保存复盘成功后刷新当前项目复盘列表并显示保存状态。
- [ ] 用户可查看单条复盘详情，详情包含查询、时间、参数、来源质量、备注和命中片段。
- [ ] 删除复盘需要二次确认，删除后刷新列表并清空对应详情。
- [ ] 项目切换、项目创建和项目删除时检索复盘状态不会串到其他项目。
- [ ] 测试通过（参照 `docs/guides/testing.md` 最低要求）。
- [ ] 相关文档已同步（见下方“回流清单”）。
- [ ] B-141 保持 `doing`；本片完成后不删除 B-141 总任务。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141Z 用户可见行为、非目标和验收标准 | `docs/features/frontend-engineering.md` | [ ] |
| Vue 工作台检索复盘 helper、状态和组件职责 | `docs/design/architecture-overview.md` | [ ] |
| Vue 检索复盘测试要求 | `docs/guides/testing.md` | [ ] |
| 未发布变更记录 | `CHANGELOG.md` | [ ] |
| 当日执行记录和验证结果 | `docs/devlog/2026-05-28.md` | [ ] |
| B-141 关联 plan 路径和状态 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-28：创建 B-141Z plan；选择检索复盘作为下一薄片，原因是后端 `POST/GET/detail/delete /api/retrieval/reviews` 契约已存在，B-141V/B-141Y 已提供检索调试查询与参数，可限定为 Vue 侧复盘保存、列表、详情和删除。
- 2026-05-28：将 `docs/plans/B-141-vue-retrieval-reviews.md` 追加到 BACKLOG B-141 说明列。
- 2026-05-28：新增 Vue 检索复盘源码契约红灯测试；聚焦运行 `tests/test_webapp/test_frontend_vue_app.py` 得到 5 failed / 64 passed，失败点为缺少检索复盘 helper、`SearchDebugPanel` 保存/列表/详情/删除控件和 `App.vue` 状态流。

## 9. 状态快照

- **最后更新**：2026-05-28 13:15
- **进度**：已完成 2 / 6 项（见 § 3 勾选状态）
- **最新 commit**：16dba3c docs: 创建 B-141Z 检索复盘迁移计划
- **代码状态**：`fix/url-virtual-source-preserve`；工作区存在多项用户/历史未提交改动，本片仅允许暂存 B-141Z 相关文件
- **下一步**：实现 Vue 检索复盘 helper、组件和 App 状态流
- **续任务须知**：不修改后端 `/api/retrieval/reviews*`、`/api/search/debug` 或 `/api/answer` 契约，不迁移普通搜索结果页，不接入 SSE/会话，不修改数据库 schema；不要清理既有 B-141 历史 plan 文件
