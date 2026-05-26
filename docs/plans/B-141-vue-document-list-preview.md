# B-141 Vue Document List Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成 B-141E：把资料库页的文档列表和单文档预览只读流程迁移到 Vue。

**Architecture:** `frontend/src/api/documents.js` 包装现有 `GET /api/documents` 与 `GET /api/document`。`DocumentListPanel.vue` 负责按当前项目展示文档列表和选择事件，`DocumentPreviewPanel.vue` 负责展示单文档正文预览、加载态和错误态。`LibraryView.vue` 组合项目空间面板、文档列表和预览，`App.vue` 读取 `appState.selectedProjectId` 并维护文档列表与预览状态。

**Tech Stack:** Vue 3 + Vite；现有 `frontend/src/api/client.js`；FastAPI 既有文档查询接口。

---

> 状态：Active
> 创建时间：2026-05-26
> 负责人：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md, docs/guides/testing.md

## 1. 目标

完成 B-141E：在 Vue 资料库页中提供最小可用的只读文档列表和单文档预览。用户选择项目空间后，可以加载该项目文档列表，点击文档后通过既有单文档预览接口查看正文。本阶段不迁移文件导入、目录同步、上传、笔记、URL 摘录、删除文档、文档集合增删改、批次历史、后端行为或数据库 schema。

## 2. 背景

- B-141A 已完成：Vue + Vite 工程骨架和 FastAPI 静态托管策略已存在。
- B-141B 已完成：Vue API client、共享状态模型、AppShell 和四个基础 view 已存在。
- B-141C 已完成：Vue 已有项目空间列表、选择和创建基础，`appState.selectedProjectId` 可复用。
- B-141D 已完成：Vue 工作台已有非流式问答入口。
- `GET /api/documents` 默认不返回正文；正文预览必须使用 `GET /api/document`。
- `webapp/static/` 仍作为完整业务 UI fallback 保留；B-141E 不删除 legacy 前端。

## 3. 任务清单

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141E plan，并将 BACKLOG 说明列追加本 plan 路径
- [x] 先写 Vue 资料库文档列表/预览红灯测试，覆盖 documents API helper、DocumentListPanel、DocumentPreviewPanel、LibraryView/App 接入和状态字段
- [x] 新增 `frontend/src/api/documents.js`，复用既有只读文档接口并处理未选择项目空间
- [x] 新增 `DocumentListPanel` 和 `DocumentPreviewPanel`，展示文档列表、空态、加载态、错误态和正文预览
- [x] 更新 `LibraryView.vue` 与 `App.vue`，在项目切换后加载文档并处理文档选择/预览状态
- [x] 同步功能文档、架构/测试/devlog/CHANGELOG 中的 B-141E 说明
- [x] 完成验证、提交 B-141E，并更新本 plan 快照；B-141 保持 `doing`

## 4. 影响范围

| 类型 | 路径 | 说明 |
|------|------|------|
| 前端 | `frontend/src/api/documents.js` | 新增：文档列表与单文档预览 API helper |
| 前端 | `frontend/src/components/DocumentListPanel.vue` | 新增：资料库文档列表、空态、加载态、错误态 |
| 前端 | `frontend/src/components/DocumentPreviewPanel.vue` | 新增：单文档正文预览 |
| 前端 | `frontend/src/views/LibraryView.vue` | 修改：组合项目空间、文档列表和预览面板 |
| 前端 | `frontend/src/App.vue` | 修改：加载文档列表、选择文档并读取预览 |
| 前端 | `frontend/src/state/app-state.js` | 修改：补充文档列表/预览状态字段 |
| 前端 | `frontend/src/styles.css` | 修改：补充资料库列表/预览布局样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 B-141E Vue source/static contract tests |
| 文档 | `docs/features/frontend-engineering.md` | 修改：B-141E 行为边界 |
| 文档 | `docs/design/architecture-overview.md`, `docs/guides/testing.md` | 修改：Vue documents helper/组件说明 |
| 文档 | `CHANGELOG.md`, `docs/devlog/2026-05-26.md` | 修改：实施记录 |
| 文档 | `docs/BACKLOG.md`, `docs/plans/B-141-vue-document-list-preview.md` | 修改/新增：计划联动 |

## 5. 冲突扫描

### 5.1 已扫描

| 路径 | 判断 |
|------|------|
| `docs/plans/B-141-vue-vite-foundation.md` | B-141A 已完成；B-141E 基于 Vue/Vite 骨架继续 |
| `docs/plans/B-141-vue-api-layout.md` | B-141B 已完成；B-141E 复用 API client、共享状态和 Library view |
| `docs/plans/B-141-vue-project-space.md` | B-141C 已完成；B-141E 复用 `selectedProjectId` 和项目空间面板 |
| `docs/plans/B-141-vue-workbench-answer-entry.md` | B-141D 已完成；B-141E 不修改问答入口 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 UI 计划，未标记 Active/Interrupted |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 计划，未标记 Active/Interrupted |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active/Interrupted |

### 5.2 处理结论

| 计划 | 重叠点 | 处理 |
|------|--------|------|
| `docs/plans/B-141-vue-vite-foundation.md` | 同属 B-141，但该 plan 已完成 B-141A | 分区：B-141E 不重复修改 Vite/静态托管策略 |
| `docs/plans/B-141-vue-api-layout.md` | 同属 B-141，但该 plan 已完成 B-141B | 分区：B-141E 复用 API/state/layout 基础，只迁移资料库文档列表/预览 |
| `docs/plans/B-141-vue-project-space.md` | 同属 B-141，但该 plan 已完成 B-141C | 分区：B-141E 只读取项目选择状态，不重复迁移项目空间面板 |
| `docs/plans/B-141-vue-workbench-answer-entry.md` | 同属 B-141，但该 plan 已完成 B-141D | 分区：B-141E 不修改工作台问答入口 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 UI 计划，未标记 Active/Interrupted | 分区：B-141E 不修改 legacy desktop/UI 文档计划 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 计划，未标记 Active/Interrupted | 分区：B-141E 不修改 legacy `src/` |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active/Interrupted | 分区：B-141E 不修改数据库 schema |

## 6. 验收标准

- [ ] Vue 资料库页能在选择项目空间后展示文档列表。
- [ ] 未选择项目空间、加载中、读取失败、无文档时都有明确状态提示。
- [ ] 点击文档后通过 `/api/document` 读取并展示正文预览。
- [ ] 文档列表不依赖列表响应中的 `content` 字段。
- [ ] B-141E 不迁移导入、删除、文档集合增删改、批次历史或数据库 schema。
- [ ] `webapp/static/` 仍保留为迁移期 fallback。
- [ ] 相关测试与文档同步完成。

## 7. 回流清单

删除或中断本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141E 文档列表/预览迁移边界 | `docs/features/frontend-engineering.md` | [x] |
| Vue documents helper 和资料库组件边界 | `docs/design/architecture-overview.md` | [x] |
| B-141E Vue source/static contract 测试命令 | `docs/guides/testing.md` | [x] |
| 对外变更摘要 | `CHANGELOG.md` | [x] |
| 实施记录 | `docs/devlog/2026-05-26.md` | [x] |
| B-141 仍处于 doing，等待后续页面迁移 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-26：用户要求继续 B-141，并说明技术栈迁移整体完成后再提交推送；本切片继续按 plan 规则提交，但不推送。
- 2026-05-26：B-141E 选择“资料库文档列表 + 单文档预览”只读薄片，不迁移导入/删除/集合/批次等写流程。
- 2026-05-26：冲突扫描发现 B-141A/B/C/D plan 已完成但保留，其他 superpowers 历史计划未标记 Active/Interrupted；按分区处理。
- 2026-05-26：创建 `docs/plans/B-141-vue-document-list-preview.md`，并将 BACKLOG B-141 说明列追加本 plan 路径。
- 2026-05-26：确认 B-141E 红灯为 3 failed / 10 passed，失败点集中在缺少 documents helper、文档列表/预览组件和 App 文档状态接入。
- 2026-05-26：新增 Vue 资料库文档列表/预览薄片、组件和状态接入，聚焦测试 13 passed，`npm run build` 成功。
- 2026-05-26：同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog 中的 B-141E 边界。
- 2026-05-26：完整验证通过：`npm run build`、`tests/test_webapp` 284 passed、legacy 回归 179 passed、B-141E touched-file `git diff --check` 退出码 0；浏览器资料库页烟测通过且控制台错误数为 0。
- 2026-05-26：提交 `bcf2551`，B-141E 只读文档浏览薄片完成；BACKLOG B-141 保持 `doing`，后续继续 B-141F。

## 9. 状态快照

- **最后更新时间**：2026-05-26
- **进度**：已完成 7 / 7 项（见 § 3 勾选状态）
- **最新 commit**：`bcf2551` — feat: 接入 Vue 资料库文档浏览薄片
- **代码状态**：分支 `fix/url-virtual-source-preserve`；存在大量既有未提交改动；B-141E 相关变更已完成
- **下一步**：B-141F 继续选择下一个 Vue 页面级业务切片，建议在资料库导入、工作台 SSE/会话或设置页模型配置之间择一
- **续任务须知**：B-141E 不删除 `webapp/static/`，不迁移导入/删除/集合/批次，不修改数据库 schema，不新增 Pinia/Vue Router；技术栈迁移整体完成前不推送
