# B-141Q Vue 项目空间改名与删除

> 状态：Active
> 创建时间：2026-05-27
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md；docs/design/api-spec.md

## 1. 目标

在 B-141C 已完成 Vue 项目空间列表、选择、最近项目恢复和新建项目空间的基础上，继续迁移“项目空间改名”和“项目空间删除”的最小前端薄片。

本片只复用既有 `POST /api/projects/rename` 与 `POST /api/projects/delete` 契约，不新增后端接口，不修改 SQLite schema，不删除 legacy `webapp/static/` fallback。删除项目空间沿用后端现有级联行为，前端只负责二次确认、状态清理和刷新。

## 2. 前置条件

- B-141C 已完成 Vue 项目空间选择/创建基础。
- B-141E 至 B-141P 已完成资料库文档列表、导入、集合和单文档删除等依赖当前项目空间的状态刷新。
- `docs/design/api-spec.md` 已记录 `POST /api/projects/rename` 与 `POST /api/projects/delete` 契约。
- legacy 前端已有项目改名/删除行为可作为交互边界参考：改名只更新项目名称；删除项目空间前需要二次确认，并清理当前项目相关 UI 状态。

## 3. 任务拆解

- [x] 创建 B-141Q plan，并将 BACKLOG 说明列追加本 plan 路径。
- [x] 增加 Vue 源码契约红灯测试，覆盖项目改名/删除 API helper、项目空间面板入口、LibraryView/App 事件与状态刷新。
- [x] 实现 `projects.js`、`ProjectSpacePanel.vue`、`LibraryView.vue`、`App.vue` 和共享状态的最小改名/删除串联。
- [x] 同步 `docs/features/frontend-engineering.md`、`docs/design/architecture-overview.md`、`CHANGELOG.md`、`docs/guides/testing.md` 和 devlog。
- [x] 运行前端源码测试、Web MVP 测试、legacy 回归、构建和浏览器冒烟。
- [ ] 完成 BACKLOG/plan 状态回写；如本片完全验收，通过提交保留验证快照。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/projects.js` | 新增 rename/delete helper |
| 代码 | `frontend/src/components/ProjectSpacePanel.vue` | 增加当前项目改名与删除入口 |
| 代码 | `frontend/src/views/LibraryView.vue` | 传递项目改名/删除状态与事件 |
| 代码 | `frontend/src/App.vue` | 新增改名/删除处理、确认、状态清理和刷新 |
| 代码 | `frontend/src/state/app-state.js` | 新增项目改名/删除操作状态字段 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 新增 B-141Q 源码契约测试 |
| 文档 | `docs/features/frontend-engineering.md` | 同步 B-141Q 行为与非目标 |
| 文档 | `docs/design/architecture-overview.md` | 同步 Vue 项目空间迁移状态 |
| 文档 | `docs/guides/testing.md` | 同步 Vue 前端测试覆盖说明 |
| 文档 | `docs/devlog/2026-05-27.md` | 记录 B-141Q 执行结果 |
| 文档 | `CHANGELOG.md` | 记录前端迁移薄片 |
| 文档 | `docs/BACKLOG.md` | 保持 B-141 为 doing 并关联本 plan |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-project-space.md` | 需要已存在项目空间列表、选择、新建和最近项目恢复状态 |
| `docs/plans/B-141-vue-document-delete.md` | 删除项目后需要清理当前文档、集合、导入批次和文档删除状态 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-project-space.md`、`docs/plans/B-141-vue-document-delete.md` | 均涉及 `projects.js`、`ProjectSpacePanel.vue`、`LibraryView.vue`、`App.vue` 和项目/资料库状态；这些 plan 的 § 3 已全部勾选，属于已完成但未删除的迁移记录 | 分区：B-141Q 只扩展项目改名/删除，不改项目创建、文档预览、导入、集合或单文档删除既有行为 |

## 6. 完成标准

- [x] 功能行为符合 `docs/features/frontend-engineering.md` 和 `docs/design/api-spec.md` 的业务规则。
- [x] Vue 资料库项目空间面板可对当前项目触发改名。
- [x] 改名成功后刷新项目列表，并保持当前项目选中。
- [x] Vue 资料库项目空间面板可对当前项目触发删除确认。
- [x] 删除确认文案明确会删除该项目空间内的文档记录。
- [x] 删除成功后清空当前项目选择、文档列表、预览、集合、导入批次和相关操作状态。
- [x] 未选择项目时项目改名/删除入口禁用或有明确提示。
- [x] B-141Q 不迁移项目根目录修改、批量项目管理、备份恢复、Workbench SSE/会话、设置页模型配置或数据库 schema。
- [x] Vue 源码契约测试通过。
- [x] `npm run build` 通过。
- [x] `.venv\Scripts\python.exe -m pytest tests/test_webapp -q` 通过。
- [x] `.venv\Scripts\python.exe -m pytest tests/test_application tests/test_domain tests/test_adapters -q` 通过。
- [x] 浏览器冒烟确认资料库页项目改名/删除入口可见且无控制台错误。
- [x] 相关文档已同步（见下方“回流清单”）。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141Q 用户可见行为、工程目录和非目标 | `docs/features/frontend-engineering.md` | [x] |
| Vue 表现层迁移状态 | `docs/design/architecture-overview.md` | [x] |
| Vue 源码契约测试覆盖范围 | `docs/guides/testing.md` | [x] |
| 本次执行记录 | `docs/devlog/2026-05-27.md` | [x] |
| 对外变更摘要 | `CHANGELOG.md` | [x] |
| B-141 关联 plan 路径和状态 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-27：创建 B-141Q plan；冲突扫描显示 B-141C/P 涉及相同项目与资料库状态文件但任务均已完成，本片按项目改名/删除分区继续。
- 2026-05-27：新增 Vue 源码契约红灯测试；聚焦运行 `tests/test_webapp/test_frontend_vue_app.py` 得到 3 failed / 40 passed，失败点为缺少项目 rename/delete helper、项目空间面板入口和 App 状态流。
- 2026-05-27：实现项目空间改名/删除 helper、面板入口和 App 处理流；聚焦测试为 43 passed。
- 2026-05-27：同步功能文档、架构文档、测试指南、devlog 和 CHANGELOG。
- 2026-05-27：完成 B-141Q 验证：Vue 源码 43 passed，`npm run build` 成功，Web MVP 314 passed，legacy 179 passed，浏览器烟测确认资料库页项目改名/删除入口可见且控制台 error 数 0。

## 9. 状态快照

- **最后更新**：2026-05-27
- **进度**：已完成 5 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`TBD` — 本片实现与验证待提交
- **代码状态**：`fix/url-virtual-source-preserve`；工作区存在多项用户/历史未提交改动，本片仅允许暂存 B-141Q 相关文件
- **下一步**：提交本片实现与验证快照，并回写最新 commit
- **续任务须知**：不要推送；不要清理 unrelated dirty files；不要修改后端接口或 SQLite schema。
