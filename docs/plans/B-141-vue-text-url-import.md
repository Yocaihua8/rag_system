# B-141 Vue Text And URL Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成 B-141F：把资料库页的文本笔记导入和 URL 摘录导入迁移到 Vue。

**Architecture:** `frontend/src/api/imports.js` 包装既有 `POST /api/import/note` 与 `POST /api/import/url`。`DocumentImportPanel.vue` 负责两个轻量表单、提交状态和结果提示，`LibraryView.vue` 组合导入面板与 B-141E 文档列表/预览。`App.vue` 读取 `appState.selectedProjectId`，提交成功后刷新文档列表，但不实现文件夹上传、文件上传、目录同步、删除、集合管理或批次历史。

**Tech Stack:** Vue 3 + Vite；现有 `frontend/src/api/client.js`；FastAPI 既有文本笔记和 URL 摘录导入接口。

---

> 状态：Active
> 创建时间：2026-05-26
> 负责人：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md, docs/guides/testing.md

## 1. 目标

完成 B-141F：在 Vue 资料库页中提供最小可用的文本笔记导入和 URL 摘录导入。用户选择项目空间后，可以提交手写文本笔记或人工粘贴 URL 摘录，成功后刷新当前项目文档列表。本阶段不迁移目录同步、浏览器文件夹上传、普通文件上传、导入预检、删除文档、文档集合增删改、导入批次历史、后端行为或数据库 schema。

## 2. 背景

- B-141A 已完成：Vue + Vite 工程骨架和 FastAPI 静态托管策略已存在。
- B-141B 已完成：Vue API client、共享状态模型、AppShell 和四个基础 view 已存在。
- B-141C 已完成：Vue 资料库已有项目空间列表、选择和创建基础。
- B-141E 已完成：Vue 资料库已有文档列表和单文档预览。
- `POST /api/import/note` 和 `POST /api/import/url` 已存在，接口契约见 `docs/design/api-spec.md`。
- `webapp/static/` 仍作为完整业务 UI fallback 保留；B-141F 不删除 legacy 前端。

## 3. 任务清单

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141F plan，并将 BACKLOG 说明列追加本 plan 路径
- [x] 先写 Vue 文本笔记/URL 摘录导入红灯测试，覆盖 imports API helper、DocumentImportPanel、LibraryView/App 接入和状态字段
- [x] 新增 `frontend/src/api/imports.js`，复用既有导入接口并处理未选择项目空间、标题/正文/URL 必填
- [x] 新增 `DocumentImportPanel`，展示文本笔记和 URL 摘录两个导入表单、未选项目提示、提交状态、错误和成功提示
- [x] 更新 `LibraryView.vue` 与 `App.vue`，处理导入事件，成功后刷新文档列表
- [x] 同步功能文档、架构/测试/devlog/CHANGELOG 中的 B-141F 说明
- [x] 完成验证、提交 B-141F，并更新本 plan 快照；B-141 保持 `doing`

## 4. 影响范围

| 类型 | 路径 | 说明 |
|------|------|------|
| 前端 | `frontend/src/api/imports.js` | 新增：文本笔记和 URL 摘录导入 API helper |
| 前端 | `frontend/src/components/DocumentImportPanel.vue` | 新增：资料库轻量导入表单 |
| 前端 | `frontend/src/views/LibraryView.vue` | 修改：组合导入面板与既有文档列表/预览 |
| 前端 | `frontend/src/App.vue` | 修改：处理文本笔记/URL 导入并刷新文档 |
| 前端 | `frontend/src/state/app-state.js` | 修改：补充导入提交、错误和状态字段 |
| 前端 | `frontend/src/styles.css` | 修改：补充资料库导入面板样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 B-141F Vue source/static contract tests |
| 文档 | `docs/features/frontend-engineering.md` | 修改：B-141F 行为边界 |
| 文档 | `docs/design/architecture-overview.md`, `docs/guides/testing.md` | 修改：Vue imports helper/组件说明 |
| 文档 | `CHANGELOG.md`, `docs/devlog/2026-05-26.md` | 修改：实施记录 |
| 文档 | `docs/BACKLOG.md`, `docs/plans/B-141-vue-text-url-import.md` | 修改/新增：计划联动 |

## 5. 冲突扫描

### 5.1 已扫描

| 路径 | 判断 |
|------|------|
| `docs/plans/B-141-vue-vite-foundation.md` | B-141A 已完成；B-141F 基于 Vue/Vite 骨架继续 |
| `docs/plans/B-141-vue-api-layout.md` | B-141B 已完成；B-141F 复用 API client、共享状态和 Library view |
| `docs/plans/B-141-vue-project-space.md` | B-141C 已完成；B-141F 复用 `selectedProjectId` 和项目空间面板 |
| `docs/plans/B-141-vue-workbench-answer-entry.md` | B-141D 已完成；B-141F 不修改问答入口 |
| `docs/plans/B-141-vue-document-list-preview.md` | B-141E 已完成；B-141F 成功导入后刷新该文档列表 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 UI 计划，未标记 Active/Interrupted |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 计划，未标记 Active/Interrupted |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active/Interrupted |

### 5.2 处理结论

| 计划 | 重叠点 | 处理 |
|------|--------|------|
| `docs/plans/B-141-vue-vite-foundation.md` | 同属 B-141，但该 plan 已完成 B-141A | 分区：B-141F 不重复修改 Vite/静态托管策略 |
| `docs/plans/B-141-vue-api-layout.md` | 同属 B-141，但该 plan 已完成 B-141B | 分区：B-141F 复用 API/state/layout 基础，只迁移资料库文本/URL 导入 |
| `docs/plans/B-141-vue-project-space.md` | 同属 B-141，但该 plan 已完成 B-141C | 分区：B-141F 只读取项目选择状态，不重复迁移项目空间面板 |
| `docs/plans/B-141-vue-workbench-answer-entry.md` | 同属 B-141，但该 plan 已完成 B-141D | 分区：B-141F 不修改工作台问答入口 |
| `docs/plans/B-141-vue-document-list-preview.md` | 同属 B-141，但该 plan 已完成 B-141E | 分区：B-141F 只在导入成功后刷新文档列表，不扩展预览语义 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 UI 计划，未标记 Active/Interrupted | 分区：B-141F 不修改 legacy desktop/UI 文档计划 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 计划，未标记 Active/Interrupted | 分区：B-141F 不修改 legacy `src/` |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active/Interrupted | 分区：B-141F 不修改数据库 schema |

## 6. 验收标准

- [ ] Vue 资料库页能在选择项目空间后提交文本笔记导入。
- [ ] Vue 资料库页能在选择项目空间后提交 URL 摘录导入。
- [ ] 未选择项目空间、提交中、提交失败和提交成功都有明确状态提示。
- [ ] 成功导入后刷新当前项目文档列表。
- [ ] B-141F 不迁移目录同步、浏览器文件夹上传、普通文件上传、导入预检、删除文档、文档集合增删改、批次历史或数据库 schema。
- [ ] `webapp/static/` 仍保留为迁移期 fallback。
- [ ] 相关测试与文档同步完成。

## 7. 回流清单

删除或中断本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141F 文本笔记/URL 摘录导入迁移边界 | `docs/features/frontend-engineering.md` | [x] |
| Vue imports helper 和资料库导入组件边界 | `docs/design/architecture-overview.md` | [x] |
| B-141F Vue source/static contract 测试命令 | `docs/guides/testing.md` | [x] |
| 对外变更摘要 | `CHANGELOG.md` | [x] |
| 实施记录 | `docs/devlog/2026-05-26.md` | [x] |
| B-141 仍处于 doing，等待后续页面迁移 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-26：用户继续 B-141 技术栈迁移，并要求整体完成后再推送；本切片继续按 plan 规则提交，但不推送。
- 2026-05-26：B-141F 选择“资料库文本笔记 + URL 摘录导入”薄片，不迁移目录同步、文件上传、删除、集合或批次历史。
- 2026-05-26：冲突扫描发现 B-141A/B/C/D/E plan 已完成但保留，其他 superpowers 历史计划未标记 Active/Interrupted；按分区处理。
- 2026-05-26：创建 `docs/plans/B-141-vue-text-url-import.md`，并将 BACKLOG B-141 说明列追加本 plan 路径。
- 2026-05-26：确认 B-141F 红灯为 3 failed / 13 passed，失败点集中在缺少 imports helper、DocumentImportPanel 和 App 导入状态接入。
- 2026-05-26：新增 Vue 资料库文本笔记/URL 摘录导入薄片、组件和状态接入，聚焦测试 16 passed，`npm run build` 成功。
- 2026-05-26：同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog 中的 B-141F 边界。
- 2026-05-26：完整验证通过：`npm run build`、`tests/test_webapp` 287 passed、legacy 回归 179 passed、B-141F touched-file `git diff --check` 退出码 0；浏览器资料库页烟测通过且控制台错误数为 0。
- 2026-05-26：提交 `47daf4f`，B-141F 资料库轻量导入薄片完成；BACKLOG B-141 保持 `doing`，后续继续 B-141G。

## 9. 状态快照

- **最后更新时间**：2026-05-26
- **进度**：已完成 7 / 7 项（见 § 3 勾选状态）
- **最新 commit**：`47daf4f` — `feat: 接入 Vue 资料库轻量导入入口`
- **代码状态**：分支 `fix/url-virtual-source-preserve`；B-141F 资料库文本/URL 导入薄片已完成；存在大量既有未提交改动，未纳入本轮提交
- **下一步**：继续 B-141G 页面级业务迁移，可在文件上传/目录同步、Workbench SSE 会话或设置页模型配置中选择下一个薄片
- **续任务须知**：B-141F 不删除 `webapp/static/`，不迁移目录同步/文件上传/删除/集合/批次，不修改数据库 schema，不新增 Pinia/Vue Router；技术栈迁移整体完成前不推送
