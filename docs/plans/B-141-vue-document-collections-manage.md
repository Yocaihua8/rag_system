# B-141M Vue 文档集合新建删除

> 状态：Active
> 创建时间：2026-05-27
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md；docs/design/api-spec.md；docs/design/document-collections-design.md

## 1. 目标

在 B-141L 已迁移文档集合只读筛选的基础上，继续迁移 Vue 资料库里的文档集合最小写操作：新建集合和删除集合。完成后，Vue 资料库可在当前项目空间内创建集合、删除集合并刷新集合列表和文档列表，且删除集合不删除文档。

本片只复用已有后端接口，不新增接口、不修改数据库结构。

## 2. 前置条件

- 已读取 `AGENTS.md`、`docs/BACKLOG.md`、`docs/features/frontend-engineering.md`、`docs/design/architecture-overview.md`、`docs/design/api-spec.md` 和 `docs/design/document-collections-design.md`。
- B-141L 已提供 `DocumentCollectionPanel`、`listDocumentCollections()`、集合筛选状态和文档列表过滤。
- 后端已存在 `POST /api/document-collections` 与 `POST /api/document-collections/delete`。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。
未完成项不得删除。

- [ ] 增加 Vue 源码契约测试，覆盖集合新建/删除 helper、面板入口和 App 状态刷新。
- [ ] 实现 `frontend/src/api/document-collections.js`、`DocumentCollectionPanel.vue`、`LibraryView.vue`、`App.vue` 的最小功能串联。
- [ ] 同步 `docs/features/frontend-engineering.md`、`docs/design/architecture-overview.md`、`CHANGELOG.md`、`docs/guides/testing.md` 和 devlog。
- [ ] 运行前端源码测试、Web MVP 测试、legacy 回归、构建和浏览器冒烟。
- [ ] 完成 BACKLOG/plan 状态回写；如本片完全验收，通过提交保留验证快照。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/document-collections.js` | 新增 create/delete helper |
| 代码 | `frontend/src/components/DocumentCollectionPanel.vue` | 新增集合名称输入、创建按钮、删除集合按钮 |
| 代码 | `frontend/src/views/LibraryView.vue` | 传递集合创建/删除事件和状态 |
| 代码 | `frontend/src/App.vue` | 新增集合创建/删除处理与刷新 |
| 代码 | `frontend/src/state/app-state.js` | 新增集合表单/删除状态字段 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 新增 B-141M 源码契约测试 |
| 文档 | `docs/features/frontend-engineering.md` | 记录 B-141M 范围 |
| 文档 | `docs/design/architecture-overview.md` | 更新 Vue 迁移边界 |
| 文档 | `docs/guides/testing.md` | 更新 Vue 测试覆盖说明 |
| 文档 | `CHANGELOG.md` | 记录本片用户可见变化 |
| 文档 | `docs/devlog/2026-05-27.md` | 记录执行和验证 |
| 文档 | `docs/BACKLOG.md` | 回写 plan 路径和状态 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-document-collections-filter.md` | B-141L 已完成集合只读筛选，B-141M 在其组件和状态上追加最小写操作 |

### 5.2 与现有 plan 的重叠

创建本 plan 时扫描到 B-141A 至 B-141L 计划文件仍保留为 `Active`，但 § 9 均显示对应任务已完成；按项目规则视为无未完成冲突。本片只修改 B-141M 影响范围，不回滚或清理既有 plan 文件。

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

## 6. 完成标准

全部勾选后方可删除本 plan 文件：

- [ ] 功能行为符合 `docs/features/frontend-engineering.md` 和 `docs/design/document-collections-design.md` 的业务规则。
- [ ] Vue 源码契约测试通过。
- [ ] `npm run build` 通过。
- [ ] `.venv\Scripts\python.exe -m pytest tests/test_webapp -q` 通过。
- [ ] `.venv\Scripts\python.exe -m pytest tests/test_application tests/test_domain tests/test_adapters -q` 通过。
- [ ] 浏览器冒烟确认资料库页集合创建/删除入口可见且无控制台错误。
- [ ] 相关文档已同步（见下方"回流清单"）。

## 7. 回流清单

删除本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141M 迁移集合新建/删除，不迁移重命名、加入/移出文档 | `docs/features/frontend-engineering.md` | [ ] |
| Vue 文档集合 helper/panel/App 边界 | `docs/design/architecture-overview.md` | [ ] |
| Vue 源码测试和浏览器冒烟范围 | `docs/guides/testing.md` | [ ] |
| 用户可见变更 | `CHANGELOG.md` | [ ] |
| 执行与验证记录 | `docs/devlog/2026-05-27.md` | [ ] |

若产生了重大技术决策，**必须**在删除 plan 前新建对应 ADR。

## 8. 执行记录

- 2026-05-27：选择 B-141M 作为下一片，只迁移集合新建/删除，避免和文档加入/移出、重命名、检索过滤扩大为同一提交。

## 9. 状态快照

> **每完成 § 3 中的一个任务后立即更新**，不等到中断时才填。
> 目的：无论因额度耗尽、开发者中断还是主动结束，下一个 session 都能从此处冷启动。
> 正常完成后随 plan 一起删除。

- **最后更新**：2026-05-27 14:25
- **进度**：已完成 0 / 5 项（见 § 3 勾选状态）
- **最新 commit**：`N/A` — 尚未提交
- **代码状态**：`fix/url-virtual-source-preserve`；工作区存在大量非本片既有未提交改动，本片仅选择性暂存自身文件
- **下一步**：增加 Vue 源码契约测试，覆盖集合新建/删除 helper、面板入口和 App 状态刷新
- **续任务须知**：不要清理 unrelated dirty files；本片不得修改后端 schema 或 legacy `webapp/static/`
