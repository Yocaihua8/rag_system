# B-141 Vue Import Batch History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成 B-141G：把资料库页的导入批次历史和批次详情迁移到 Vue。

**Architecture:** 继续复用 `frontend/src/api/imports.js`，新增 `listImportBatches(projectId)` 和 `getImportBatchDetail(batchId)` 读取既有接口。新增 `ImportBatchHistoryPanel.vue` 展示最近批次、只读详情、跳过/错误明细，`LibraryView.vue` 组合该面板，`App.vue` 在项目切换和导入成功后刷新批次历史。

**Tech Stack:** Vue 3 + Vite；现有 `frontend/src/api/client.js`；FastAPI 既有导入批次历史接口。

---

> 状态：Active
> 创建时间：2026-05-26
> 负责人：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md, docs/guides/testing.md

## 1. 目标

完成 B-141G：在 Vue 资料库页中提供导入批次历史的最小只读迁移。用户选择项目空间后，可以查看最近导入批次，点击某个批次读取详情，并看到来源类型、状态、汇总计数以及跳过/读取失败明细。本阶段不迁移目录同步、浏览器文件夹上传、普通文件上传、导入预检、批次回滚、批次删除、批次重试、文档集合管理、后端行为或数据库 schema。

## 2. 背景

- B-141A 已完成：Vue + Vite 工程骨架和 FastAPI 静态托管策略已存在。
- B-141B 已完成：Vue API client、共享状态模型、AppShell 和四个基础 view 已存在。
- B-141C 已完成：Vue 资料库已有项目空间列表、选择和创建基础。
- B-141E 已完成：Vue 资料库已有文档列表和单文档预览。
- B-141F 已完成：Vue 资料库已有文本笔记和 URL 摘录导入；导入成功后刷新文档列表。
- `GET /api/import/batches` 和 `GET /api/import/batches/detail` 已存在，接口契约见 `docs/design/api-spec.md`。
- `webapp/static/` 仍作为完整业务 UI fallback 保留；B-141G 不删除 legacy 前端。

## 3. 任务清单

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141G plan，并将 BACKLOG 说明列追加本 plan 路径
- [x] 先写 Vue 导入批次历史红灯测试，覆盖 imports API helper、ImportBatchHistoryPanel、LibraryView/App 接入和状态字段
- [x] 扩展 `frontend/src/api/imports.js`，复用既有导入批次历史接口并处理未选择项目空间、未选择批次
- [x] 新增 `ImportBatchHistoryPanel`，展示批次列表、详情、空态、加载态、错误态和只读边界
- [x] 更新 `LibraryView.vue` 与 `App.vue`，在项目切换和导入成功后刷新批次历史，点击批次读取详情
- [x] 同步功能文档、架构/测试/devlog/CHANGELOG 中的 B-141G 说明
- [x] 完成验证、提交 B-141G，并更新本 plan 快照；B-141 保持 `doing`

## 4. 影响范围

| 类型 | 路径 | 说明 |
|------|------|------|
| 前端 | `frontend/src/api/imports.js` | 修改：增加导入批次列表和详情 API helper |
| 前端 | `frontend/src/components/ImportBatchHistoryPanel.vue` | 新增：资料库导入批次历史只读面板 |
| 前端 | `frontend/src/views/LibraryView.vue` | 修改：组合导入批次历史面板 |
| 前端 | `frontend/src/App.vue` | 修改：加载批次历史、处理批次详情选择 |
| 前端 | `frontend/src/state/app-state.js` | 修改：补充批次历史加载、错误和详情状态字段 |
| 前端 | `frontend/src/styles.css` | 修改：补充导入批次历史面板样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 B-141G Vue source/static contract tests |
| 文档 | `docs/features/frontend-engineering.md` | 修改：B-141G 行为边界 |
| 文档 | `docs/design/architecture-overview.md`, `docs/guides/testing.md` | 修改：Vue import batch helper/组件说明 |
| 文档 | `CHANGELOG.md`, `docs/devlog/2026-05-26.md` | 修改：实施记录 |
| 文档 | `docs/BACKLOG.md`, `docs/plans/B-141-vue-import-batch-history.md` | 修改/新增：计划联动 |

## 5. 冲突扫描

### 5.1 已扫描

| 路径 | 判断 |
|------|------|
| `docs/plans/B-141-vue-vite-foundation.md` | B-141A 已完成；B-141G 基于 Vue/Vite 骨架继续 |
| `docs/plans/B-141-vue-api-layout.md` | B-141B 已完成；B-141G 复用 API client、共享状态和 Library view |
| `docs/plans/B-141-vue-project-space.md` | B-141C 已完成；B-141G 复用 `selectedProjectId` 和项目空间面板 |
| `docs/plans/B-141-vue-workbench-answer-entry.md` | B-141D 已完成；B-141G 不修改问答入口 |
| `docs/plans/B-141-vue-document-list-preview.md` | B-141E 已完成；B-141G 复用资料库文档列表刷新点 |
| `docs/plans/B-141-vue-text-url-import.md` | B-141F 已完成；B-141G 在其导入成功后追加批次历史刷新 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 UI 计划，未标记 Active/Interrupted |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 计划，未标记 Active/Interrupted |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active/Interrupted |

### 5.2 处理结论

| 计划 | 重叠点 | 处理 |
|------|--------|------|
| `docs/plans/B-141-vue-vite-foundation.md` | 同属 B-141，但该 plan 已完成 B-141A | 分区：B-141G 不重复修改 Vite/静态托管策略 |
| `docs/plans/B-141-vue-api-layout.md` | 同属 B-141，但该 plan 已完成 B-141B | 分区：B-141G 复用 API/state/layout 基础，只迁移资料库导入批次历史 |
| `docs/plans/B-141-vue-project-space.md` | 同属 B-141，但该 plan 已完成 B-141C | 分区：B-141G 只读取项目选择状态，不重复迁移项目空间面板 |
| `docs/plans/B-141-vue-workbench-answer-entry.md` | 同属 B-141，但该 plan 已完成 B-141D | 分区：B-141G 不修改工作台问答入口 |
| `docs/plans/B-141-vue-document-list-preview.md` | 同属 B-141，但该 plan 已完成 B-141E | 分区：B-141G 不扩展文档预览语义，只在同一资料库页展示批次历史 |
| `docs/plans/B-141-vue-text-url-import.md` | 同属 B-141，但该 plan 已完成 B-141F | 分区：B-141G 复用导入成功刷新点，不改变文本/URL 导入契约 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 UI 计划，未标记 Active/Interrupted | 分区：B-141G 不修改 legacy desktop/UI 文档计划 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 计划，未标记 Active/Interrupted | 分区：B-141G 不修改 legacy `src/` |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active/Interrupted | 分区：B-141G 不修改数据库 schema |

## 6. 验收标准

- [ ] Vue 资料库页能在选择项目空间后读取并展示最近导入批次。
- [ ] 未选择项目空间、加载中、读取失败、无批次时都有明确状态提示。
- [ ] 点击批次后通过 `/api/import/batches/detail` 读取并展示批次详情。
- [ ] 批次详情只展示跳过和读取失败明细，不提供回滚、删除或重试操作。
- [ ] 文本笔记或 URL 摘录导入成功后刷新当前项目文档列表和导入批次历史。
- [ ] B-141G 不迁移目录同步、浏览器文件夹上传、普通文件上传、导入预检、文档集合或数据库 schema。
- [ ] `webapp/static/` 仍保留为迁移期 fallback。
- [ ] 相关测试与文档同步完成。

## 7. 回流清单

删除或中断本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141G 导入批次历史迁移边界 | `docs/features/frontend-engineering.md` | [x] |
| Vue import batch helper 和资料库批次组件边界 | `docs/design/architecture-overview.md` | [x] |
| B-141G Vue source/static contract 测试命令 | `docs/guides/testing.md` | [x] |
| 对外变更摘要 | `CHANGELOG.md` | [x] |
| 实施记录 | `docs/devlog/2026-05-26.md` | [x] |
| B-141 仍处于 doing，等待后续页面迁移 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-26：用户继续 B-141 技术栈迁移，并要求整体完成后再推送；本切片继续按 plan 规则提交，但不推送。
- 2026-05-26：B-141G 选择“资料库导入批次历史”薄片，不迁移目录同步、文件上传、预检、回滚、删除、重试、集合或数据库 schema。
- 2026-05-26：冲突扫描发现 B-141A/B/C/D/E/F plan 已完成但保留，其他 superpowers 历史计划未标记 Active/Interrupted；按分区处理。
- 2026-05-26：创建 `docs/plans/B-141-vue-import-batch-history.md`，并将 BACKLOG B-141 说明列追加本 plan 路径。
- 2026-05-26：确认 B-141G 红灯为 3 failed / 16 passed，失败点集中在缺少 import batch API helper、ImportBatchHistoryPanel 和 App 批次状态接入。
- 2026-05-26：新增 Vue 导入批次历史 helper、只读面板和 App/Library 接入，聚焦测试 19 passed。
- 2026-05-26：同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog 中的 B-141G 边界。
- 2026-05-26：完整验证通过：`npm run build`、`tests/test_webapp` 290 passed、legacy 回归 179 passed、B-141G touched-file `git diff --check` 退出码 0；浏览器资料库页烟测通过且控制台错误数为 0。

## 9. 状态快照

- **最后更新时间**：2026-05-26
- **进度**：已完成 7 / 7 项（见 § 3 勾选状态）
- **最新 commit**：`1f668bb` — `docs: 同步 B-141G 导入批次历史说明`
- **代码状态**：分支 `fix/url-virtual-source-preserve`；B-141G 导入批次历史薄片已完成；存在大量既有未提交改动，未纳入本轮提交
- **下一步**：继续 B-141H 页面级业务迁移，可在文件上传/目录同步、Workbench SSE 会话或设置页模型配置中选择下一个薄片
- **续任务须知**：B-141G 不删除 `webapp/static/`，不迁移目录同步/文件上传/预检/回滚/删除/重试/集合，不修改数据库 schema，不新增 Pinia/Vue Router；技术栈迁移整体完成前不推送
