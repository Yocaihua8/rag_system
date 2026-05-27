# B-141N Vue 文档集合重命名

> 状态：Active
> 创建时间：2026-05-27
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md；docs/design/api-spec.md；docs/design/document-collections-design.md

## 1. 目标

在 B-141M 已迁移文档集合新建/删除的基础上，继续迁移 Vue 资料库中的文档集合重命名。完成后，用户可在 Vue 资料库内选择已有集合名称进入编辑状态，提交新名称后复用既有 `POST /api/document-collections/update` 更新集合，并刷新集合列表与当前筛选显示。

本片不新增后端接口、不修改数据库结构、不迁移文档加入/移出集合。

## 2. 前置条件

- 已读取 `AGENTS.md`、`docs/BACKLOG.md`、`docs/features/frontend-engineering.md`、`docs/design/architecture-overview.md`、`docs/design/api-spec.md` 和 `docs/design/document-collections-design.md`。
- B-141L 已提供集合列表与筛选。
- B-141M 已提供集合新建与删除。
- 后端已存在 `POST /api/document-collections/update`。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。
未完成项不得删除。

- [x] 增加 Vue 源码契约测试，覆盖集合重命名 helper、面板编辑入口和 App 状态刷新。
- [x] 实现 `document-collections.js`、`DocumentCollectionPanel.vue`、`LibraryView.vue`、`App.vue` 和共享状态的最小重命名串联。
- [x] 同步 `docs/features/frontend-engineering.md`、`docs/design/architecture-overview.md`、`CHANGELOG.md`、`docs/guides/testing.md` 和 devlog。
- [ ] 运行前端源码测试、Web MVP 测试、legacy 回归、构建和浏览器冒烟。
- [ ] 完成 BACKLOG/plan 状态回写；如本片完全验收，通过提交保留验证快照。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/document-collections.js` | 新增 update helper |
| 代码 | `frontend/src/components/DocumentCollectionPanel.vue` | 新增重命名编辑态和提交/取消入口 |
| 代码 | `frontend/src/views/LibraryView.vue` | 传递集合重命名事件和状态 |
| 代码 | `frontend/src/App.vue` | 新增集合重命名处理与刷新 |
| 代码 | `frontend/src/state/app-state.js` | 新增集合重命名状态字段 |
| 代码 | `frontend/src/styles.css` | 视需要补充编辑态样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 新增 B-141N 源码契约测试 |
| 文档 | `docs/features/frontend-engineering.md` | 记录 B-141N 范围 |
| 文档 | `docs/design/architecture-overview.md` | 更新 Vue 迁移边界 |
| 文档 | `docs/guides/testing.md` | 更新 Vue 文档集合测试要求 |
| 文档 | `CHANGELOG.md` | 记录本片用户可见变化 |
| 文档 | `docs/devlog/2026-05-27.md` | 记录执行和验证 |
| 文档 | `docs/BACKLOG.md` | 回写 plan 路径 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-document-collections-manage.md` | B-141M 已完成集合新建/删除，本片在同一组件上追加重命名编辑态 |

### 5.2 与现有 plan 的重叠

创建本 plan 时扫描到 B-141A 至 B-141M 计划文件仍保留为 `Active`，但 § 9 均显示对应任务已完成；按项目规则视为无未完成冲突。本片只修改 B-141N 影响范围，不回滚或清理既有 plan 文件。

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
- [ ] 浏览器冒烟确认资料库页集合重命名入口可见且无控制台错误。
- [ ] 相关文档已同步（见下方"回流清单"）。

## 7. 回流清单

删除本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141N 迁移集合重命名，不迁移加入/移出文档 | `docs/features/frontend-engineering.md` | [ ] |
| Vue 文档集合 helper/panel/App 重命名边界 | `docs/design/architecture-overview.md` | [ ] |
| Vue 集合重命名测试和浏览器冒烟范围 | `docs/guides/testing.md` | [ ] |
| 用户可见变更 | `CHANGELOG.md` | [ ] |
| 执行与验证记录 | `docs/devlog/2026-05-27.md` | [ ] |

若产生了重大技术决策，**必须**在删除 plan 前新建对应 ADR。

## 8. 执行记录

- 2026-05-27：选择 B-141N 作为下一片，只迁移集合重命名；文档加入/移出需要改文档列表项操作区，留到后续单独切片。

## 9. 状态快照

> **每完成 § 3 中的一个任务后立即更新**，不等到中断时才填。
> 目的：无论因额度耗尽、开发者中断还是主动结束，下一个 session 都能从此处冷启动。
> 正常完成后随 plan 一起删除。

- **最后更新**：2026-05-27 15:55
- **进度**：已完成 3 / 5 项（见 § 3 勾选状态）
- **最新 commit**：`65bd564` — `feat: 接入 Vue 文档集合重命名`
- **代码状态**：`fix/url-virtual-source-preserve`；工作区存在大量非本片既有未提交改动，本片仅选择性暂存自身文件
- **下一步**：运行前端源码测试、Web MVP 测试、legacy 回归、构建和浏览器冒烟
- **续任务须知**：不要清理 unrelated dirty files；本片不得修改后端 schema 或 legacy `webapp/static/`
