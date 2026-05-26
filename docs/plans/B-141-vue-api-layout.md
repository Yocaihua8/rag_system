# B-141 Vue API Client And Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Vue API client, shared state model, and base layout shell for the new frontend without migrating full business workflows yet.

**Architecture:** `frontend/src/api/` owns normalized fetch helpers, `frontend/src/state/` owns a small reactive app state, and `frontend/src/components` plus `frontend/src/views` own the navigation shell and placeholder views. B-141B keeps legacy `webapp/static/` as the complete business UI until later page-by-page migration.

**Tech Stack:** Vue 3 Composition API (`reactive`, `computed`), Vite, npm, pytest static/source checks.

---

> 状态：Active
> 创建时间：2026-05-26
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/adr/ADR-006-vue-vite-frontend.md, docs/design/architecture-overview.md, docs/guides/testing.md

## 1. 目标

完成 B-141B：在 Vue 前端中建立可复用 API 客户端、共享状态模型和基础布局/视图切换，为后续按页面迁移工作台、资料库、评估、设置打基础。本阶段不实现完整项目导入、问答、评估或设置业务流程。

## 2. 前置条件

- B-141A 已完成：`frontend/`、Vite 构建、`webapp/static_dist/` 静态托管策略已存在。
- `webapp/static/` 仍作为完整业务 UI fallback 保留。
- 已用 ctx7 查询 Vue 3 Composition API 当前文档，确认可用 `reactive` 管理模块状态、组件通过 props/emits 和组合式函数拆分。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141B plan，并将 BACKLOG 说明列追加本 plan 路径
- [x] 先写 Vue API/state/layout 红灯测试，覆盖 API helper、状态字段、四个基础视图和 App 组装
- [x] 新增 `frontend/src/api/client.js`，迁移 legacy API 错误归一化和 `apiGet/apiPost`
- [x] 新增 `frontend/src/state/app-state.js`，定义当前 Vue 迁移期共享状态和视图切换 helper
- [ ] 拆分 `AppShell`、基础 views，并让 `App.vue` 使用 Vue 状态完成四视图切换和健康检查
- [ ] 同步功能文档、架构/测试/devlog/CHANGELOG 中的 B-141B 说明
- [ ] 运行 npm 构建、前端工程测试、Web MVP 全量、legacy 回归和空白检查
- [ ] 更新 plan 快照，保留 B-141 为 `doing`，下一步指向 B-141C 页面迁移

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 前端 | `frontend/src/api/client.js` | 新增：Vue 前端 API helper |
| 前端 | `frontend/src/state/app-state.js` | 新增：Vue 前端共享状态 |
| 前端 | `frontend/src/components/AppShell.vue` | 新增：基础布局与导航 |
| 前端 | `frontend/src/views/*.vue` | 新增：工作台、资料库、评估、设置占位视图 |
| 前端 | `frontend/src/App.vue`, `frontend/src/styles.css` | 修改：组装基础布局和状态 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 新增：Vue source/static contract tests |
| 文档 | `docs/features/frontend-engineering.md` | 修改：B-141B 边界 |
| 文档 | `docs/design/architecture-overview.md`, `docs/guides/testing.md` | 修改：Vue state/API/layout 说明 |
| 文档 | `CHANGELOG.md`, `docs/devlog/2026-05-26.md` | 修改：实施记录 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-vite-foundation.md` | B-141A 已完成；B-141B 基于该 Vue/Vite 骨架继续 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-vite-foundation.md` | 同属 B-141，但该 plan 已完成 B-141A | 分区：B-141B 只扩展 Vue 源码结构，不重复修改静态托管策略 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 UI 计划，未标记 Active/Interrupted | 分区：B-141B 不修改 legacy desktop/UI 文档计划 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 计划，未标记 Active/Interrupted | 分区：B-141B 不修改 legacy `src/` |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active/Interrupted | 分区：B-141B 不修改数据库 schema |

## 6. 完成标准

- [ ] Vue 前端存在 API helper，错误提示与 legacy 前端保持同类恢复提示。
- [ ] Vue 前端存在共享状态模型，包含当前项目、会话、文档、评估、工具、检索等后续迁移所需字段。
- [ ] Vue 前端基础布局包含工作台、资料库、评估、设置四个视图和导航切换。
- [ ] B-141B 不实现完整业务流程，不删除 legacy `webapp/static/`。
- [ ] `npm run build` 通过。
- [ ] 相关测试与文档同步完成。

## 7. 回流清单

删除或中断本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141B API/state/layout 边界 | `docs/features/frontend-engineering.md` | [ ] |
| Vue API/state/layout 架构说明 | `docs/design/architecture-overview.md` | [ ] |
| Vue source 测试命令 | `docs/guides/testing.md` | [ ] |
| 对外变更摘要 | `CHANGELOG.md` | [ ] |
| 实施记录 | `docs/devlog/2026-05-26.md` | [ ] |

## 8. 执行记录

- 2026-05-26：用户要求继续 B-141；B-141A 已完成，B-141B 从 Vue API 客户端、状态模型和基础布局开始。
- 2026-05-26：冲突扫描发现 B-141A plan 已完成但保留，其他 superpowers 历史计划未标记 Active/Interrupted；按分区处理。
- 2026-05-26：创建 `docs/plans/B-141-vue-api-layout.md`，并将 BACKLOG B-141 说明列追加本 plan 路径。
- 2026-05-26：新增 `tests/test_webapp/test_frontend_vue_app.py` 后红灯失败于缺少 Vue API client、state、AppShell 和基础 views。
- 2026-05-26：新增 `frontend/src/api/client.js`，复用 legacy API 错误归一化语义；聚焦 API client 测试与 `npm run build` 通过。
- 2026-05-26：新增 `frontend/src/state/app-state.js`，对齐 legacy 关键状态字段并提供 `showView()` 视图切换 helper；聚焦状态测试与 `npm run build` 通过。

## 9. 状态快照

- **最后更新**：2026-05-26 16:17
- **进度**：已完成 4 / 8 项（见 § 3 勾选状态）
- **最新 commit**：`681619b` — feat: 新增 Vue API 客户端
- **代码状态**：分支 `fix/url-virtual-source-preserve`；存在大量既有未提交改动；B-141B 将只追加 Vue API/state/layout 相关变更
- **下一步**：拆分 `AppShell`、基础 views，并让 `App.vue` 使用 Vue 状态完成四视图切换和健康检查
- **续任务须知**：不删除 `webapp/static/`，不迁移完整业务流程，不修改数据库 schema，不新增 Pinia/Vue Router
