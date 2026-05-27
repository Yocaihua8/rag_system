# B-141O Vue 文档集合加入移出

> 状态：Active
> 创建时间：2026-05-27
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md；docs/design/api-spec.md；docs/design/document-collections-design.md

## 1. 目标

在 B-141L/B-141M/B-141N 已完成 Vue 文档集合读取、筛选、新建、删除和重命名的基础上，继续迁移“把文档加入集合 / 从当前集合移出文档”的最小前端薄片。

本片只复用既有 `POST /api/document-collections/items/add` 和 `POST /api/document-collections/items/remove` 契约，不新增后端接口，不修改 SQLite schema，不删除 legacy `webapp/static/` fallback。

## 2. 前置条件

- B-141L 已完成 Vue 文档集合只读筛选。
- B-141M 已完成 Vue 文档集合新建/删除。
- B-141N 已完成 Vue 文档集合重命名。
- `docs/design/api-spec.md` 已记录集合 items add/remove 接口契约。
- `docs/design/document-collections-design.md` 已记录集合关系不复制正文、不移动源文件、不重建 chunk/vector 的边界。

## 3. 任务拆解

- [x] 创建 B-141O plan，并将 BACKLOG 说明列追加本 plan 路径。
- [x] 增加 Vue 源码契约红灯测试，覆盖集合 items API helper、文档列表加入/移出入口、LibraryView/App 事件与状态刷新。
- [ ] 实现 `document-collections.js`、`DocumentListPanel.vue`、`LibraryView.vue`、`App.vue` 和共享状态的最小加入/移出串联。
- [ ] 同步 `docs/features/frontend-engineering.md`、`docs/design/architecture-overview.md`、`CHANGELOG.md`、`docs/guides/testing.md` 和 devlog。
- [ ] 运行前端源码测试、Web MVP 测试、legacy 回归、构建和浏览器冒烟。
- [ ] 完成 BACKLOG/plan 状态回写；如本片完全验收，通过提交保留验证快照。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/document-collections.js` | 新增 add/remove item helper |
| 代码 | `frontend/src/components/DocumentListPanel.vue` | 增加单文档加入集合 / 当前集合移出入口 |
| 代码 | `frontend/src/views/LibraryView.vue` | 传递集合列表、当前筛选、items 操作状态与事件 |
| 代码 | `frontend/src/App.vue` | 新增集合 items 加入/移出处理与刷新 |
| 代码 | `frontend/src/state/app-state.js` | 新增集合 items 操作状态字段 |
| 代码 | `frontend/src/styles.css` | 补充文档列表内集合操作样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 新增 B-141O 源码契约测试 |
| 文档 | `docs/features/frontend-engineering.md` | 同步 B-141O 行为与非目标 |
| 文档 | `docs/design/architecture-overview.md` | 同步 Vue 资料库迁移状态 |
| 文档 | `docs/guides/testing.md` | 同步 Vue 前端测试覆盖说明 |
| 文档 | `docs/devlog/2026-05-27.md` | 记录 B-141O 执行结果 |
| 文档 | `CHANGELOG.md` | 记录前端迁移薄片 |
| 文档 | `docs/BACKLOG.md` | 保持 B-141 为 doing 并关联本 plan |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-document-collections-filter.md` | 需要已存在集合筛选状态和列表过滤 |
| `docs/plans/B-141-vue-document-collections-manage.md` | 需要已存在集合新建/删除入口和状态刷新 |
| `docs/plans/B-141-vue-document-collections-rename.md` | 需要已存在集合编辑状态，避免 items 操作混入集合元数据表单 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-document-collections-filter.md`、`docs/plans/B-141-vue-document-collections-manage.md`、`docs/plans/B-141-vue-document-collections-rename.md` | 均涉及 `document-collections.js`、`LibraryView.vue`、`App.vue` 和集合状态；这些 plan 的 § 3 已全部勾选，属于已完成但未删除的迁移记录 | 分区：B-141O 只扩展文档与集合的关联 items 操作，不改集合筛选、新建、删除、重命名既有行为 |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/frontend-engineering.md` 和 `docs/design/document-collections-design.md` 的业务规则。
- [ ] Vue 资料库文档列表在存在集合时可把单个文档加入指定集合。
- [ ] Vue 资料库筛选到指定集合时可把单个文档从当前集合移出。
- [ ] 加入/移出成功后刷新文档集合列表和当前文档列表，并清理当前预览。
- [ ] 未选择项目、未选择集合、未选择文档时有明确错误提示或禁用态。
- [ ] B-141O 不迁移批量选择、拖拽、删除文档、项目改名/删除、问答按集合过滤或数据库 schema。
- [ ] Vue 源码契约测试通过。
- [ ] `npm run build` 通过。
- [ ] `.venv\Scripts\python.exe -m pytest tests/test_webapp -q` 通过。
- [ ] `.venv\Scripts\python.exe -m pytest tests/test_application tests/test_domain tests/test_adapters -q` 通过。
- [ ] 浏览器冒烟确认资料库页集合加入/移出入口可见且无控制台错误。
- [ ] 相关文档已同步（见下方“回流清单”）。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141O 用户可见行为、工程目录和非目标 | `docs/features/frontend-engineering.md` | [ ] |
| Vue 表现层迁移状态 | `docs/design/architecture-overview.md` | [ ] |
| Vue 源码契约测试覆盖范围 | `docs/guides/testing.md` | [ ] |
| 本次执行记录 | `docs/devlog/2026-05-27.md` | [ ] |
| 对外变更摘要 | `CHANGELOG.md` | [ ] |
| B-141 关联 plan 路径和状态 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-05-27：创建 B-141O plan；冲突扫描显示 B-141L/M/N 涉及相同文件但任务均已完成，本片按 items 操作分区继续。
- 2026-05-27：新增 Vue 源码契约红灯测试；聚焦运行 `tests/test_webapp/test_frontend_vue_app.py` 得到 4 failed / 33 passed，失败点为缺少 add/remove helper、文档列表操作入口和 App 处理函数。

## 9. 状态快照

- **最后更新**：2026-05-27 00:00
- **进度**：已完成 2 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`e6755da` — test: 覆盖 Vue 文档集合文档归组入口
- **代码状态**：`fix/url-virtual-source-preserve`；工作区存在多项用户/历史未提交改动，本片仅允许暂存 B-141O 相关文件
- **下一步**：实现 `document-collections.js`、`DocumentListPanel.vue`、`LibraryView.vue`、`App.vue` 和共享状态的最小加入/移出串联
- **续任务须知**：不要推送；不要清理 unrelated dirty files；不要修改后端接口或 SQLite schema。
