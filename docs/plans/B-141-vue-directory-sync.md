# B-141 Vue Directory Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成 B-141J：把资料库页的“同步当前项目目录”入口迁移到 Vue。

**Architecture:** 扩展 `frontend/src/api/imports.js`，新增 `syncProjectDirectory({ projectId })`，复用既有 `POST /api/import`。`DocumentImportPanel.vue` 增加当前项目目录同步按钮并 emit `sync-directory`；`App.vue` 处理同步响应，刷新当前项目文档列表和导入批次历史。

**Tech Stack:** Vue 3 + Vite；现有 `frontend/src/api/client.js`；FastAPI 既有 `/api/import` 接口。

---

> 状态：Active
> 创建时间：2026-05-26
> 负责人：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md, docs/guides/testing.md

## 1. 目标

完成 B-141J：在 Vue 资料库页中提供“同步当前项目目录”入口。用户选择已有项目空间后，可点击按钮调用既有 `POST /api/import`，由后端读取该项目的 `root_path` 并完成目录同步；同步成功后刷新当前项目文档列表和导入批次历史。本阶段不迁移导入预检、删除文档、文档集合、项目改名/删除、后端行为或数据库 schema。

## 2. 背景

- B-141A 已完成：Vue + Vite 工程骨架和 FastAPI 静态托管策略已存在。
- B-141B 已完成：Vue API client、共享状态模型、AppShell 和四个基础 view 已存在。
- B-141C 已完成：Vue 资料库已有项目空间列表、选择和创建基础。
- B-141E 已完成：Vue 资料库已有文档列表和单文档预览。
- B-141F/G/H/I 已完成：Vue 资料库已有轻量导入、导入批次历史、普通文件上传和浏览器文件夹上传。
- `POST /api/import` 已存在，接口契约见 `docs/design/api-spec.md`。后端负责校验项目是否存在、项目根目录是否存在，并记录 `directory_sync` 导入批次。
- `webapp/static/` 仍作为完整业务 UI fallback 保留；B-141J 不删除 legacy 前端。

## 3. 任务清单

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141J plan，并将 BACKLOG 说明列追加本 plan 路径
- [x] 先写 Vue 目录同步红灯测试，覆盖 imports API helper、DocumentImportPanel 同步入口、App 接入和状态刷新
- [x] 扩展 `frontend/src/api/imports.js`，新增 `syncProjectDirectory({ projectId })`，校验项目后调用既有 `POST /api/import`
- [x] 更新 `DocumentImportPanel`，新增“同步当前项目目录”按钮，未选项目时禁用
- [x] 更新 `App.vue`，处理目录同步响应，成功后刷新文档列表和导入批次历史
- [x] 同步功能文档、架构/测试/devlog/CHANGELOG 中的 B-141J 说明
- [ ] 完成验证、提交 B-141J，并更新本 plan 快照；B-141 保持 `doing`

## 4. 影响范围

| 类型 | 路径 | 说明 |
|------|------|------|
| 前端 | `frontend/src/api/imports.js` | 修改：增加目录同步 API helper |
| 前端 | `frontend/src/components/DocumentImportPanel.vue` | 修改：增加同步当前项目目录入口 |
| 前端 | `frontend/src/App.vue` | 修改：处理目录同步响应与刷新 |
| 前端 | `frontend/src/views/LibraryView.vue` | 修改：转发 `sync-directory` 事件 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 B-141J Vue source/static contract tests |
| 文档 | `docs/features/frontend-engineering.md` | 修改：B-141J 行为边界 |
| 文档 | `docs/design/architecture-overview.md`, `docs/guides/testing.md` | 修改：Vue 目录同步 helper/组件说明 |
| 文档 | `CHANGELOG.md`, `docs/devlog/2026-05-26.md` | 修改：实施记录 |
| 文档 | `docs/BACKLOG.md`, `docs/plans/B-141-vue-directory-sync.md` | 修改/新增：计划联动 |

## 5. 冲突扫描

### 5.1 已扫描

| 路径 | 判断 |
|------|------|
| `docs/plans/B-141-vue-vite-foundation.md` | B-141A 已完成；B-141J 基于 Vue/Vite 骨架继续 |
| `docs/plans/B-141-vue-api-layout.md` | B-141B 已完成；B-141J 复用 API client、共享状态和 Library view |
| `docs/plans/B-141-vue-project-space.md` | B-141C 已完成；B-141J 复用当前项目选择状态 |
| `docs/plans/B-141-vue-workbench-answer-entry.md` | B-141D 已完成；B-141J 不修改问答入口 |
| `docs/plans/B-141-vue-document-list-preview.md` | B-141E 已完成；B-141J 成功同步后刷新文档列表 |
| `docs/plans/B-141-vue-text-url-import.md` | B-141F 已完成；B-141J 扩展同一导入面板，但不改变文本/URL 导入契约 |
| `docs/plans/B-141-vue-import-batch-history.md` | B-141G 已完成；B-141J 成功同步后刷新批次历史 |
| `docs/plans/B-141-vue-file-upload-import.md` | B-141H 已完成；B-141J 不改变普通文件上传入口 |
| `docs/plans/B-141-vue-browser-folder-import.md` | B-141I 已完成；B-141J 不改变浏览器文件夹上传入口 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 UI 计划，未标记 Active/Interrupted |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 计划，未标记 Active/Interrupted |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active/Interrupted |

### 5.2 处理结论

| 计划 | 重叠点 | 处理 |
|------|--------|------|
| B-141A/I 相关已完成 plan | 同属 B-141，但均已完成各自薄片 | 分区：B-141J 只迁移目录同步入口，不重复调整既有 Vue/Vite、项目、文档、导入或批次薄片 |
| 历史 superpowers 计划 | 未标记 Active/Interrupted | 分区：B-141J 不修改 legacy `src/`、数据库 schema 或历史 desktop UI |

## 6. 验收标准

- [ ] Vue 资料库页提供“同步当前项目目录”按钮。
- [ ] 未选择项目空间时，同步按钮禁用。
- [ ] 目录同步请求调用 `POST /api/import`，请求体包含当前 `project_id`。
- [ ] 未选择项目空间时，API helper 抛出“请先创建或选择项目空间”。
- [ ] 同步成功后刷新当前项目文档列表和导入批次历史，并显示导入结果计数。
- [ ] B-141J 不迁移导入预检、删除文档、文档集合、项目改名/删除、后端行为或数据库 schema。
- [ ] `webapp/static/` 仍保留为迁移期 fallback。
- [ ] 相关测试与文档同步完成。

## 7. 回流清单

删除或中断本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141J 目录同步迁移边界 | `docs/features/frontend-engineering.md` | [x] |
| Vue directory sync helper 和资料库导入组件边界 | `docs/design/architecture-overview.md` | [x] |
| B-141J Vue source/static contract 测试命令 | `docs/guides/testing.md` | [x] |
| 对外变更摘要 | `CHANGELOG.md` | [x] |
| 实施记录 | `docs/devlog/2026-05-26.md` | [x] |
| B-141 仍处于 doing，等待后续页面迁移 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-26：用户继续 B-141 技术栈迁移，并要求整体完成后再推送；本切片继续按 plan 规则提交，但不推送。
- 2026-05-26：B-141J 选择“资料库同步当前项目目录”薄片，不迁移导入预检、删除、集合、项目改名/删除或数据库 schema。
- 2026-05-26：冲突扫描发现 B-141A/B/C/D/E/F/G/H/I plan 已完成但保留，其他 superpowers 历史计划未标记 Active/Interrupted；按分区处理。
- 2026-05-26：创建 `docs/plans/B-141-vue-directory-sync.md`，并将 BACKLOG B-141 说明列追加本 plan 路径。
- 2026-05-26：确认 B-141J 红灯为 5 failed / 23 passed，失败点集中在缺少 `syncProjectDirectory`、导入面板同步入口和 App 目录同步响应接入。
- 2026-05-26：新增 Vue 目录同步 helper、面板按钮和 App 响应接入，聚焦测试 28 passed。
- 2026-05-26：同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog 中的 B-141J 边界。

## 9. 状态快照

- **最后更新时间**：2026-05-26
- **进度**：已完成 6 / 7 项（见 § 3 勾选状态）
- **最新 commit**：`75a104e` — `feat: 接入 Vue 当前目录同步`
- **代码状态**：分支 `fix/url-virtual-source-preserve`；存在大量既有未提交改动；本轮只追加 Vue 资料库当前目录同步相关变更
- **下一步**：完成 B-141J 完整验证并提交收尾快照
- **续任务须知**：B-141J 不删除 `webapp/static/`，不迁移预检/删除/集合/项目改名删除，不修改数据库 schema，不新增 Pinia/Vue Router；技术栈迁移整体完成前不推送
