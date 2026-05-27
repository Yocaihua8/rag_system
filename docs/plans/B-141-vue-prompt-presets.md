# B-141S Vue 设置页 Prompt 预设迁移计划

> 状态：Active
> 创建时间：2026-05-28
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md（接口契约沿用 docs/design/api-spec.md，不新增或修改 API）

## 1. 目标

在 Vue 设置页迁移项目级 Prompt 预设管理入口，复用既有 `/api/prompt-presets*` 契约，让用户在选中项目空间后可以读取预设和内置模板、新建/编辑/删除预设、设置或清空默认预设。

本片不修改后端接口、SQLite schema、真实 LLM prompt 注入逻辑、Workbench SSE/会话或评估页。

## 2. 前置条件

- B-141R 已完成 Vue 设置页基础模型设置和模型 Profile 迁移。
- `docs/design/api-spec.md` 已定义 `/api/prompt-presets`、`/api/prompt-presets/update`、`/api/prompt-presets/delete`、`/api/prompt-presets/default` 契约。
- legacy 静态前端已有 Prompt 预设管理实现，可作为 Vue 行为对齐参考。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141S plan，并将 BACKLOG 说明列追加本 plan 路径。
- [x] 增加 Vue 源码契约红灯测试，覆盖 Prompt 预设 API helper、设置页 UI 和 App 状态流。
- [x] 实现 `frontend/src/api/settings.js`、`SettingsView.vue`、`App.vue` 和共享状态的 Prompt 预设串联。
- [x] 运行聚焦 Vue 测试和 Vite build，确认本片前端实现通过。
- [x] 同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog。
- [ ] 完成 Web MVP 全量、legacy 回归与浏览器烟测，并回写 plan 状态快照。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/settings.js` | 修改：增加 Prompt 预设 API helper |
| 代码 | `frontend/src/views/SettingsView.vue` | 修改：增加 Prompt 预设列表、模板、编辑表单和默认选择入口 |
| 代码 | `frontend/src/App.vue` | 修改：增加 Prompt 预设读取、保存、删除和默认切换状态流 |
| 代码 | `frontend/src/state/app-state.js` | 修改：补充 Prompt 预设操作状态 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 Vue Prompt 预设源码契约测试 |
| 文档 | `docs/features/frontend-engineering.md` | 修改：同步 B-141S 用户可见行为和非目标 |
| 文档 | `docs/design/architecture-overview.md` | 修改：同步 Vue 设置页迁移状态 |
| 文档 | `docs/guides/testing.md` | 修改：补充 Vue Prompt 预设验证要求 |
| 文档 | `CHANGELOG.md` | 修改：追加未发布变更 |
| 文档 | `docs/devlog/2026-05-28.md` | 新增或修改：记录本片执行与验证 |
| 文档 | `docs/BACKLOG.md` | 修改：追加本 plan 路径 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-settings-model-config.md` | 需要 Vue 设置页、`settings.js` helper 和 App 设置状态流作为基础 |

### 5.2 与现有 plan 的重叠

创建本 plan 时扫描到 B-141A 至 B-141R 计划文件仍保留为 `Active`，但 § 9 均显示对应任务已完成；按项目规则视为已完成但未删除的迁移记录。本片只扩展设置页 Prompt 预设影响范围，不清理既有 plan 文件。

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-api-layout.md` | `frontend/src/state/app-state.js`、`frontend/src/App.vue` 和基础设置页壳 | 分区：B-141S 只扩展 Prompt 预设状态和事件，不改基础布局 |
| `docs/plans/B-141-vue-settings-model-config.md` | `frontend/src/api/settings.js`、`SettingsView.vue`、`App.vue` | 分区：B-141S 只接入 Prompt 预设，不改模型设置/Profile 行为 |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/frontend-engineering.md` 的 B-141S 业务规则。
- [ ] Vue 设置页可在已选择项目空间时读取 Prompt 预设和内置模板。
- [ ] Vue 设置页可新建/编辑/删除 Prompt 预设，并可设置或清空默认预设。
- [ ] Prompt 预设 helper 只调用既有 `/api/prompt-presets*` 契约，不新增接口、不修改数据库 schema。
- [ ] 测试通过（参照 `docs/guides/testing.md` 最低要求）。
- [ ] 相关文档已同步（见下方"回流清单"）。
- [ ] B-141 保持 `doing`；本片完成后不删除 B-141 总任务。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141S 用户可见行为、非目标和验收标准 | `docs/features/frontend-engineering.md` | [x] |
| Vue 设置页 Prompt 预设 helper、状态和组件职责 | `docs/design/architecture-overview.md` | [x] |
| Vue Prompt 预设测试要求和回归检查 | `docs/guides/testing.md` | [x] |
| 未发布变更记录 | `CHANGELOG.md` | [x] |
| 当日执行记录和验证结果 | `docs/devlog/2026-05-28.md` | [x] |
| B-141 关联 plan 路径和状态 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-28：创建 B-141S plan；冲突扫描显示 B-141A 至 B-141R 为已完成但未删除的迁移记录，本片按设置页 Prompt 预设分区继续。
- 2026-05-28：新增 Vue 源码契约红灯测试；聚焦运行 `tests/test_webapp/test_frontend_vue_app.py` 得到 4 failed / 45 passed，失败点为缺少 Prompt 预设 helper、设置页 UI、App 状态流和 B-141S 文案。
- 2026-05-28：实现 Vue 设置页 Prompt 预设 helper、列表/模板/表单和 App 状态流；聚焦测试 `tests/test_webapp/test_frontend_vue_app.py` 为 49 passed。
- 2026-05-28：完成前端验证：Vue 源码测试 49 passed，`npm run build` 成功；构建产物未进入待提交范围。
- 2026-05-28：同步功能文档、架构说明、测试指南、CHANGELOG、BACKLOG 更新时间和 devlog；B-141S 明确不迁移 Workbench SSE/会话、评估页、真实 LLM prompt 注入逻辑或数据库 schema。

## 9. 状态快照

- **最后更新**：2026-05-28 00:32
- **进度**：已完成 5 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`待提交` — docs: 同步 B-141S Prompt 预设迁移说明
- **代码状态**：`fix/url-virtual-source-preserve`；工作区存在多项用户/历史未提交改动，本片仅允许暂存 B-141S 相关文件
- **下一步**：完成 Web MVP 全量、legacy 回归与浏览器烟测，并回写 plan 状态快照
- **续任务须知**：不修改后端 `/api/prompt-presets*` 契约、不修改数据库 schema；不要清理既有 B-141 历史 plan 文件
