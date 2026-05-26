# B-141 Vue Workbench Answer Entry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the first Workbench answer entry slice into Vue with non-streaming question submission, answer display, sources, and recoverable status messaging.

**Architecture:** `frontend/src/api/answer.js` wraps existing `POST /api/answer` on top of the shared Vue API client. `QuestionPanel.vue` owns question input and submit state, while `AnswerPanel.vue` owns answer/source rendering. `WorkbenchView.vue` composes both panels and emits a submit event to `App.vue`, which reads `appState.selectedProjectId` and stores the latest answer state. B-141D does not migrate SSE streaming, cancellation, chat sessions/history, answer feedback, Agent tools, retrieval debug, or backend behavior.

**Tech Stack:** Vue 3 Composition API, Vite, existing FastAPI `/api/answer` contract, pytest source/static checks.

---

> 状态：Active
> 创建时间：2026-05-26
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md, docs/guides/testing.md

## 1. 目标

完成 B-141D：在 Vue 工作台中提供最小可用的非流式问答入口。用户选择项目空间后，可以输入问题、提交到现有 `POST /api/answer`，并在 Vue 工作台看到回答、来源和状态提示。本阶段不新增后端接口，不修改数据库 schema，不迁移 legacy 流式 SSE、取消、聊天历史、回答反馈、Agent 工具和检索调试。

## 2. 前置条件

- B-141A 已完成：Vue + Vite 工程骨架和 FastAPI 静态托管策略已存在。
- B-141B 已完成：Vue API client、共享状态模型、AppShell 和四个基础 view 已存在。
- B-141C 已完成：Vue 已有项目空间列表、选择和创建基础，`appState.selectedProjectId` 可复用。
- `docs/design/api-spec.md` 已记录 `POST /api/answer` 契约。
- `webapp/static/` 仍作为完整业务 UI fallback 保留；B-141D 不删除 legacy 前端。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141D plan，并将 BACKLOG 说明列追加本 plan 路径
- [ ] 先写 Vue 工作台问答入口红灯测试，覆盖 answer API helper、QuestionPanel、AnswerPanel、Workbench/App 接入和状态字段
- [ ] 新增 `frontend/src/api/answer.js`，封装非流式 `askQuestion({ projectId, question })`
- [ ] 新增 `QuestionPanel` 和 `AnswerPanel`，展示输入、提交状态、回答、来源和来源质量
- [ ] 更新 `WorkbenchView.vue` 与 `App.vue`，处理非流式提问并写入共享状态
- [ ] 同步功能文档、架构/测试/devlog/CHANGELOG 中的 B-141D 说明
- [ ] 运行 npm 构建、Vue 前端工程测试、Web MVP 全量、legacy 回归和页面非空检查
- [ ] 更新 plan 快照，保留 B-141 为 `doing`，下一步指向 B-141E 页面迁移

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 前端 | `frontend/src/api/answer.js` | 新增：Vue 非流式问答 API helper |
| 前端 | `frontend/src/components/QuestionPanel.vue` | 新增：工作台问题输入与提交状态 |
| 前端 | `frontend/src/components/AnswerPanel.vue` | 新增：回答、来源和来源质量展示 |
| 前端 | `frontend/src/views/WorkbenchView.vue` | 修改：接入问答入口组件 |
| 前端 | `frontend/src/App.vue` | 修改：处理提问事件并更新 answer 状态 |
| 前端 | `frontend/src/state/app-state.js` | 修改：补充 question/answer/loading/error/source 状态 |
| 前端 | `frontend/src/styles.css` | 修改：问答入口与回答卡片基础样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 B-141D Vue source/static contract tests |
| 文档 | `docs/features/frontend-engineering.md` | 修改：B-141D 行为边界 |
| 文档 | `docs/design/architecture-overview.md`, `docs/guides/testing.md` | 修改：Vue answer helper/组件说明 |
| 文档 | `CHANGELOG.md`, `docs/devlog/2026-05-26.md` | 修改：实施记录 |
| 文档 | `docs/BACKLOG.md`, `docs/plans/B-141-vue-workbench-answer-entry.md` | 修改/新增：计划联动 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-vite-foundation.md` | B-141A 已完成；B-141D 基于 Vue/Vite 骨架继续 |
| `docs/plans/B-141-vue-api-layout.md` | B-141B 已完成；B-141D 复用 API client、共享状态和 Workbench view |
| `docs/plans/B-141-vue-project-space.md` | B-141C 已完成；B-141D 复用 `selectedProjectId` 和项目选择状态 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-141-vue-vite-foundation.md` | 同属 B-141，但该 plan 已完成 B-141A | 分区：B-141D 不重复修改 Vite/静态托管策略 |
| `docs/plans/B-141-vue-api-layout.md` | 同属 B-141，但该 plan 已完成 B-141B | 分区：B-141D 复用其 API/state/layout 基础，只迁移工作台问答入口 |
| `docs/plans/B-141-vue-project-space.md` | 同属 B-141，但该 plan 已完成 B-141C | 分区：B-141D 只读取项目选择状态，不重复迁移项目空间面板 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 UI 计划，未标记 Active/Interrupted | 分区：B-141D 不修改 legacy desktop/UI 文档计划 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 计划，未标记 Active/Interrupted | 分区：B-141D 不修改 legacy `src/` |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active/Interrupted | 分区：B-141D 不修改数据库 schema |

## 6. 完成标准

- [ ] Vue 工作台能显示问题输入框、提交按钮、项目选择提示和提交状态。
- [ ] Vue 工作台调用既有 `POST /api/answer`，请求体包含 `project_id` 和 `question`。
- [ ] Vue 工作台能展示回答文本、来源列表、模型模式和来源质量摘要。
- [ ] B-141D 不迁移 SSE 流式输出、取消、聊天会话/历史、回答反馈、Agent 工具或检索调试。
- [ ] `npm run build` 通过。
- [ ] 相关测试与文档同步完成。

## 7. 回流清单

删除或中断本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141D 工作台问答入口迁移边界 | `docs/features/frontend-engineering.md` | [ ] |
| Vue answer helper/组件架构说明 | `docs/design/architecture-overview.md` | [ ] |
| Vue 问答入口 source 测试要求 | `docs/guides/testing.md` | [ ] |
| 对外变更摘要 | `CHANGELOG.md` | [ ] |
| 实施记录 | `docs/devlog/2026-05-26.md` | [ ] |

## 8. 执行记录

- 2026-05-26：用户确认 B-141D 选择“工作台问答入口”；采用非流式 `/api/answer` 最小薄片，不迁移 SSE/取消/聊天历史/反馈/Agent/检索调试。
- 2026-05-26：冲突扫描发现 B-141A/B/C plan 已完成但保留，其他 superpowers 历史计划未标记 Active/Interrupted；按分区处理。
- 2026-05-26：创建 `docs/plans/B-141-vue-workbench-answer-entry.md`，并将 BACKLOG B-141 说明列追加本 plan 路径。

## 9. 状态快照

- **最后更新**：2026-05-26 17:30
- **进度**：已完成 1 / 8 项（见 § 3 勾选状态）
- **最新 commit**：`aee4f31` — docs: 完成 B-141C 计划快照
- **代码状态**：分支 `fix/url-virtual-source-preserve`；存在大量既有未提交改动；B-141D 将只追加 Vue 工作台问答入口相关变更
- **下一步**：提交 B-141D plan 与 BACKLOG 关联
- **续任务须知**：不删除 `webapp/static/`，不迁移 SSE/取消/聊天历史/反馈/Agent/检索调试，不修改数据库 schema，不新增 Pinia/Vue Router
