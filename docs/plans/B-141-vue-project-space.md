# B-141 Vue Project Space Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the first business slice into Vue by adding project-space listing, selection, persistence, and creation in the Library view.

**Architecture:** `frontend/src/api/projects.js` wraps existing project APIs on top of the shared Vue API client. `frontend/src/components/ProjectSpacePanel.vue` owns the project selection/create UI and emits refresh/create/select actions through helper functions that update `appState`. B-141C does not migrate import, rename, delete, documents, chat, assessment, model settings, or backend behavior.

**Tech Stack:** Vue 3 Composition API, Vite, existing FastAPI `/api/projects` contract, pytest source/static checks.

---

> 状态：Active
> 创建时间：2026-05-26
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md, docs/guides/testing.md

## 1. 目标

完成 B-141C：把“项目空间列表 / 当前项目选择 / 最近项目恢复 / 新建项目空间”迁移到 Vue 资料库视图，为后续导入、文档列表和问答页面迁移提供可复用的项目状态基础。本阶段只复用已有 `GET /api/projects` 与 `POST /api/projects`，不新增后端接口，不修改数据库 schema。

## 2. 前置条件

- B-141A 已完成：Vue + Vite 工程骨架和 FastAPI 静态托管策略已存在。
- B-141B 已完成：Vue API client、共享状态模型、AppShell 和四个基础 view 已存在。
- `webapp/static/` 仍作为完整业务 UI fallback 保留；B-141C 不删除 legacy 前端。
- `docs/design/api-spec.md` 已记录 `GET /api/projects` 与 `POST /api/projects` 契约。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141C plan，并将 BACKLOG 说明列追加本 plan 路径
- [x] 先写 Vue 项目空间红灯测试，覆盖项目 API helper、状态持久化、资料库项目空间组件和 App 启动加载
- [x] 新增 `frontend/src/api/projects.js`，封装 `listProjects/createProject/selectProject/restoreSelectedProjectId`
- [x] 新增 `ProjectSpacePanel` 并接入 `LibraryView`，展示项目列表、当前目录状态、错误/空状态和新建项目表单
- [x] 更新 `App.vue` 启动时加载项目空间，并把项目状态传给资料库视图
- [ ] 同步功能文档、架构/测试/devlog/CHANGELOG 中的 B-141C 说明
- [ ] 运行 npm 构建、Vue 前端工程测试、Web MVP 全量、legacy 回归和页面非空检查
- [ ] 更新 plan 快照，保留 B-141 为 `doing`，下一步指向 B-141D 页面迁移

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 前端 | `frontend/src/api/projects.js` | 新增：Vue 项目空间 API helper |
| 前端 | `frontend/src/components/ProjectSpacePanel.vue` | 新增：项目空间选择/创建面板 |
| 前端 | `frontend/src/views/LibraryView.vue` | 修改：接入项目空间面板 |
| 前端 | `frontend/src/App.vue` | 修改：启动加载项目空间并处理面板事件 |
| 前端 | `frontend/src/state/app-state.js` | 修改：补充项目加载/表单/错误状态 |
| 前端 | `frontend/src/styles.css` | 修改：项目空间面板基础样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 B-141C Vue source/static contract tests |
| 文档 | `docs/features/frontend-engineering.md` | 修改：B-141C 行为边界 |
| 文档 | `docs/design/architecture-overview.md`, `docs/guides/testing.md` | 修改：Vue 项目空间 helper/组件说明 |
| 文档 | `CHANGELOG.md`, `docs/devlog/2026-05-26.md` | 修改：实施记录 |
| 文档 | `docs/BACKLOG.md`, `docs/plans/B-141-vue-project-space.md` | 修改/新增：计划联动 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-vite-foundation.md` | B-141A 已完成；B-141C 基于 Vue/Vite 骨架继续 |
| `docs/plans/B-141-vue-api-layout.md` | B-141B 已完成；B-141C 复用 API client、共享状态和 Library view |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-vite-foundation.md` | 同属 B-141，但该 plan 已完成 B-141A | 分区：B-141C 不重复修改 Vite/静态托管策略 |
| `docs/plans/B-141-vue-api-layout.md` | 同属 B-141，但该 plan 已完成 B-141B | 分区：B-141C 复用其 API/state/layout 基础，只迁移项目空间薄片 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 UI 计划，未标记 Active/Interrupted | 分区：B-141C 不修改 legacy desktop/UI 文档计划 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 计划，未标记 Active/Interrupted | 分区：B-141C 不修改 legacy `src/` |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active/Interrupted | 分区：B-141C 不修改数据库 schema |

## 6. 完成标准

- [ ] Vue 资料库视图能显示项目空间列表、当前项目名称和本地目录状态。
- [ ] Vue 项目空间选择会写入共享状态并持久化最近项目 ID。
- [ ] Vue 新建项目表单调用现有 `POST /api/projects`，成功后刷新列表并选中新项目。
- [ ] B-141C 不迁移导入、重命名、删除、文档列表、问答、评估或设置业务流程。
- [ ] `npm run build` 通过。
- [ ] 相关测试与文档同步完成。

## 7. 回流清单

删除或中断本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141C 项目空间迁移边界 | `docs/features/frontend-engineering.md` | [ ] |
| Vue 项目空间 helper/组件架构说明 | `docs/design/architecture-overview.md` | [ ] |
| Vue 项目空间 source 测试要求 | `docs/guides/testing.md` | [ ] |
| 对外变更摘要 | `CHANGELOG.md` | [ ] |
| 实施记录 | `docs/devlog/2026-05-26.md` | [ ] |

## 8. 执行记录

- 2026-05-26：用户要求继续 B-141；B-141B 已完成，B-141C 选择最小业务切片“项目空间选择/创建”开始。
- 2026-05-26：冲突扫描发现 B-141A/B plan 已完成但保留，其他 superpowers 历史计划未标记 Active/Interrupted；按分区处理。
- 2026-05-26：创建 `docs/plans/B-141-vue-project-space.md`，并将 BACKLOG B-141 说明列追加本 plan 路径。
- 2026-05-26：新增 B-141C Vue source 红灯测试；失败于缺少 `frontend/src/api/projects.js`、`ProjectSpacePanel.vue` 和 App 项目空间加载逻辑。
- 2026-05-26：新增 `frontend/src/api/projects.js`，封装项目列表、创建、选择和最近项目恢复；Vue source 测试剩余失败收敛到组件和 App 接入。
- 2026-05-26：新增 `ProjectSpacePanel` 并接入 `LibraryView`；Vue source 测试剩余失败收敛到 App 启动加载和事件处理。
- 2026-05-26：更新 `App.vue` 和共享状态，启动时加载项目空间并处理刷新、选择、创建事件；Vue source 测试和 `npm run build` 通过。

## 9. 状态快照

- **最后更新**：2026-05-26 17:13
- **进度**：已完成 5 / 8 项（见 § 3 勾选状态）
- **最新 commit**：`52d25a7` — docs: 更新 B-141C 面板快照
- **代码状态**：分支 `fix/url-virtual-source-preserve`；存在大量既有未提交改动；B-141C 将只追加 Vue 项目空间相关变更
- **下一步**：同步功能文档、架构/测试/devlog/CHANGELOG 中的 B-141C 说明
- **续任务须知**：不删除 `webapp/static/`，不迁移导入/问答/评估/设置完整流程，不修改数据库 schema，不新增 Pinia/Vue Router
