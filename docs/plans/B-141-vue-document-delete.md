# B-141P Vue 资料库删除文档

> 状态：Active
> 创建时间：2026-05-27
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md；docs/design/api-spec.md

## 1. 目标

在 B-141E 已完成 Vue 文档列表/预览、B-141O 已完成文档集合加入/移出的基础上，继续迁移“从当前项目空间移除文档记录”的最小前端薄片。

本片只复用既有 `POST /api/documents/delete` 契约，不新增后端接口，不修改 SQLite schema，不删除源文件，不删除 legacy `webapp/static/` fallback。

## 2. 前置条件

- B-141E 已完成 Vue 文档列表和单文档预览。
- B-141L 至 B-141O 已完成 Vue 文档集合筛选、新建、删除、重命名、加入和移出。
- `docs/design/api-spec.md` 已记录 `POST /api/documents/delete` 接口契约。
- legacy 前端已有文档删除行为可作为交互边界参考：删除文档记录不删除源文件，成功后刷新文档列表和集合信息。

## 3. 任务拆解

- [x] 创建 B-141P plan，并将 BACKLOG 说明列追加本 plan 路径。
- [x] 增加 Vue 源码契约红灯测试，覆盖文档删除 API helper、文档列表删除入口、LibraryView/App 事件与状态刷新。
- [ ] 实现 `documents.js`、`DocumentListPanel.vue`、`LibraryView.vue`、`App.vue` 和共享状态的最小删除文档串联。
- [ ] 同步 `docs/features/frontend-engineering.md`、`docs/design/architecture-overview.md`、`CHANGELOG.md`、`docs/guides/testing.md` 和 devlog。
- [ ] 运行前端源码测试、Web MVP 测试、legacy 回归、构建和浏览器冒烟。
- [ ] 完成 BACKLOG/plan 状态回写；如本片完全验收，通过提交保留验证快照。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/documents.js` | 新增 delete helper |
| 代码 | `frontend/src/components/DocumentListPanel.vue` | 增加单文档删除入口和删除状态提示 |
| 代码 | `frontend/src/views/LibraryView.vue` | 传递删除状态与事件 |
| 代码 | `frontend/src/App.vue` | 新增删除确认、API 调用、列表/集合刷新和预览清理 |
| 代码 | `frontend/src/state/app-state.js` | 新增删除文档操作状态字段 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 新增 B-141P 源码契约测试 |
| 文档 | `docs/features/frontend-engineering.md` | 同步 B-141P 行为与非目标 |
| 文档 | `docs/design/architecture-overview.md` | 同步 Vue 资料库迁移状态 |
| 文档 | `docs/guides/testing.md` | 同步 Vue 前端测试覆盖说明 |
| 文档 | `docs/devlog/2026-05-27.md` | 记录 B-141P 执行结果 |
| 文档 | `CHANGELOG.md` | 记录前端迁移薄片 |
| 文档 | `docs/BACKLOG.md` | 保持 B-141 为 doing 并关联本 plan |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-document-list-preview.md` | 需要已存在文档列表、选中文档和预览状态 |
| `docs/plans/B-141-vue-document-collection-items.md` | 需要删除后刷新集合计数和当前筛选文档列表 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-document-list-preview.md`、`docs/plans/B-141-vue-document-collection-items.md` | 均涉及 `documents.js`、`DocumentListPanel.vue`、`LibraryView.vue`、`App.vue` 和文档列表状态；这些 plan 的 § 3 已全部勾选，属于已完成但未删除的迁移记录 | 分区：B-141P 只扩展单文档删除，不改文档预览、集合筛选、加入或移出既有行为 |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/frontend-engineering.md` 和 `docs/design/api-spec.md` 的业务规则。
- [ ] Vue 资料库文档列表可对单个文档触发删除确认。
- [ ] 删除确认文案明确“源文件不会被删除”。
- [ ] 删除成功后刷新当前文档列表和文档集合列表。
- [ ] 删除当前预览文档后清空预览状态。
- [ ] 未选择文档时有明确错误提示或禁用态。
- [ ] B-141P 不迁移批量删除、源文件删除、项目改名/删除、问答按集合过滤或数据库 schema。
- [ ] Vue 源码契约测试通过。
- [ ] `npm run build` 通过。
- [ ] `.venv\Scripts\python.exe -m pytest tests/test_webapp -q` 通过。
- [ ] `.venv\Scripts\python.exe -m pytest tests/test_application tests/test_domain tests/test_adapters -q` 通过。
- [ ] 浏览器冒烟确认资料库页删除文档入口可见且无控制台错误。
- [ ] 相关文档已同步（见下方“回流清单”）。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141P 用户可见行为、工程目录和非目标 | `docs/features/frontend-engineering.md` | [ ] |
| Vue 表现层迁移状态 | `docs/design/architecture-overview.md` | [ ] |
| Vue 源码契约测试覆盖范围 | `docs/guides/testing.md` | [ ] |
| 本次执行记录 | `docs/devlog/2026-05-27.md` | [ ] |
| 对外变更摘要 | `CHANGELOG.md` | [ ] |
| B-141 关联 plan 路径和状态 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-27：创建 B-141P plan；冲突扫描显示 B-141E/O 涉及相同文件但任务均已完成，本片按单文档删除分区继续。
- 2026-05-27：新增 Vue 源码契约红灯测试；聚焦运行 `tests/test_webapp/test_frontend_vue_app.py` 得到 4 failed / 36 passed，失败点为迁移文案仍停留 B-141O、缺少 delete helper、文档列表删除入口和 App 删除处理函数。

## 9. 状态快照

- **最后更新**：2026-05-27 15:39
- **进度**：已完成 2 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`7b21ce4` — docs: 更新 B-141P 计划快照
- **代码状态**：`fix/url-virtual-source-preserve`；工作区存在多项用户/历史未提交改动，本片仅允许暂存 B-141P 相关文件
- **下一步**：实现 `documents.js`、`DocumentListPanel.vue`、`LibraryView.vue`、`App.vue` 和共享状态的最小删除文档串联
- **续任务须知**：不要推送；不要清理 unrelated dirty files；不要修改后端接口或 SQLite schema。
