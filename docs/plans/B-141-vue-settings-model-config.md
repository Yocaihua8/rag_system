# B-141R Vue 设置页模型配置迁移计划

> 状态：Active
> 创建时间：2026-05-27
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md；docs/design/api-spec.md；docs/design/model-profiles-design.md

## 1. 目标

在 B-141Q 已完成资料库项目空间改名/删除后，继续迁移 Vue 设置页的模型配置薄片。完成后，用户可在 Vue 设置页读取、保存和测试基础 LLM 设置，并管理模型 Profile 的创建、编辑、删除、默认和连接测试。所有操作复用既有 `/api/settings/llm` 与 `/api/model-profiles*` 契约，不新增后端接口，不修改 SQLite schema，不删除 legacy `webapp/static/` fallback。

Prompt 预设仍保留在后续切片；本片只迁移模型连接配置，避免设置页一次性改动过宽。

## 2. 前置条件

- B-141B 已完成 Vue API client、共享状态和设置页视图壳。
- B-141Q 已完成项目空间面板改名/删除，当前 B-141 下一步指向设置页模型配置或 Workbench SSE/会话。
- 后端已存在 `GET/POST /api/settings/llm`、`POST /api/settings/llm/test` 与 `GET/POST /api/model-profiles*` 契约，接口文档以 `docs/design/api-spec.md` 为准。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141R plan，并将 BACKLOG 说明列追加本 plan 路径。
- [x] 增加 Vue 源码契约红灯测试，覆盖设置 API helper、设置页模型表单/Profile 列表和 App 状态流。
- [x] 实现 `frontend/src/api/settings.js`、`SettingsView.vue`、`App.vue` 和共享状态的最小模型设置/Profile 串联。
- [x] 同步 `docs/features/frontend-engineering.md`、`docs/design/architecture-overview.md`、`CHANGELOG.md`、`docs/guides/testing.md` 和 devlog。
- [ ] 运行前端源码测试、Web MVP 测试、legacy 回归、构建和浏览器冒烟。
- [ ] 完成 BACKLOG/plan 状态回写；如本片完全验收，通过提交保留验证快照。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/settings.js` | 新增：Vue 设置页 API helper |
| 代码 | `frontend/src/views/SettingsView.vue` | 修改：模型设置/Profile 表单与列表 |
| 代码 | `frontend/src/App.vue` | 修改：读取、保存、测试和 Profile 状态流 |
| 代码 | `frontend/src/state/app-state.js` | 修改：补充模型设置/Profile 操作状态 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 Vue 设置页源码契约测试 |
| 文档 | `docs/features/frontend-engineering.md` | 修改：同步 B-141R 用户可见行为和非目标 |
| 文档 | `docs/design/architecture-overview.md` | 修改：同步 Vue 设置页迁移状态 |
| 文档 | `docs/guides/testing.md` | 修改：补充 Vue 设置页模型配置验证要求 |
| 文档 | `CHANGELOG.md` | 修改：记录 Unreleased Vue 设置页模型配置薄片 |
| 文档 | `docs/devlog/2026-05-27.md` | 修改：记录执行与验证 |
| 文档 | `docs/BACKLOG.md` | 修改：追加 plan 路径并保持 B-141 doing |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-api-layout.md` | 需要 Vue API client、共享状态和 Settings view 壳 |
| `docs/plans/B-141-vue-project-rename-delete.md` | B-141Q 最新快照指向 B-141R 候选；本片从该状态继续 |

### 5.2 与现有 plan 的重叠

创建本 plan 时扫描到 B-141A 至 B-141Q 计划文件仍保留为 `Active`，其中部分历史计划存在未勾选完成标准，但 § 9 均显示对应任务已完成；按项目规则视为已完成但未删除的迁移记录。本片只修改设置页模型配置影响范围，不清理既有 plan 文件。

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-api-layout.md` | `frontend/src/state/app-state.js`、`frontend/src/App.vue` 和基础设置页壳 | 分区：B-141R 只扩展设置页模型配置，不改基础布局 |
| `docs/plans/B-141-vue-project-rename-delete.md` | `frontend/src/App.vue` 共享状态编排文件 | 分区：B-141R 只接入设置页事件，不改资料库项目空间状态流 |

## 6. 完成标准

- [x] 功能行为符合 `docs/features/frontend-engineering.md` 和 `docs/design/api-spec.md` 的业务规则。
- [ ] Vue 设置页可读取、保存和测试基础模型设置，且不回显 API Key 明文。
- [ ] Vue 设置页可读取模型 Profile 列表，创建/编辑/删除 Profile，设置/清空默认 Profile，并测试单个 Profile。
- [ ] B-141R 不迁移 Prompt 预设、Workbench SSE/会话、项目根目录修改、批量项目管理或数据库 schema。
- [ ] Vue 源码契约测试通过。
- [ ] `npm run build` 通过。
- [ ] `.venv\Scripts\python.exe -m pytest tests/test_webapp -q` 通过。
- [ ] `.venv\Scripts\python.exe -m pytest tests/test_application tests/test_domain tests/test_adapters -q` 通过。
- [ ] 浏览器冒烟确认设置页模型配置入口可见且无控制台错误。
- [x] 相关文档已同步（见下方“回流清单”）。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141R 用户可见行为、非目标和验收标准 | `docs/features/frontend-engineering.md` | [x] |
| Vue 设置页 API helper、状态和组件职责 | `docs/design/architecture-overview.md` | [x] |
| Vue 设置页模型配置测试要求 | `docs/guides/testing.md` | [x] |
| Unreleased 变更记录 | `CHANGELOG.md` | [x] |
| 本次执行记录 | `docs/devlog/2026-05-27.md` | [x] |
| B-141 关联 plan 路径和状态 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-27：创建 B-141R plan；冲突扫描显示 B-141A 至 B-141Q 为已完成但未删除的迁移记录，本片按设置页模型配置分区继续。
- 2026-05-27：新增 Vue 源码契约红灯测试；聚焦运行 `tests/test_webapp/test_frontend_vue_app.py` 得到 3 failed / 43 passed，失败点为缺少设置页 helper、设置页模型配置 UI 和 App 状态流。
- 2026-05-27：实现 Vue 设置页模型设置/Profile helper、表单列表和 App 状态流；聚焦测试 `tests/test_webapp/test_frontend_vue_app.py` 为 46 passed，`npm run build` 成功。
- 2026-05-27：同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog；B-141R 明确不迁移 Prompt 预设和 Workbench SSE/会话。

## 9. 状态快照

- **最后更新**：2026-05-27 00:00
- **进度**：已完成 4 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`e0545e9` — feat: 接入 Vue 设置页模型配置
- **代码状态**：`fix/url-virtual-source-preserve`；工作区存在多项用户/历史未提交改动，本片仅允许暂存 B-141R 相关文件
- **下一步**：运行前端源码测试、Web MVP 测试、legacy 回归、构建和浏览器冒烟
- **续任务须知**：保持本片不迁移 Prompt 预设；不要清理既有 B-141 历史 plan 文件
