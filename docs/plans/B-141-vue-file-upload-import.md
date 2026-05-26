# B-141 Vue File Upload Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成 B-141H：把资料库页的普通文件上传导入迁移到 Vue。

**Architecture:** 扩展 `frontend/src/api/imports.js`，新增 `importBrowserFiles({ projectId, files })`，把普通 `<input type="file" multiple>` 选择的文件读取为既有 `/api/import/upload` 请求体。`DocumentImportPanel.vue` 增加文件上传入口并 emit 文件列表；`App.vue` 处理上传响应，更新选中项目、文档列表和导入批次历史。

**Tech Stack:** Vue 3 + Vite；浏览器 File API；现有 `frontend/src/api/client.js`；FastAPI 既有 `/api/import/upload` 接口。

---

> 状态：Active
> 创建时间：2026-05-26
> 负责人：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md, docs/guides/testing.md

## 1. 目标

完成 B-141H：在 Vue 资料库页中提供普通文件上传导入入口。用户可以点击“选择文件上传导入”，一次选择一个或多个文件；有当前项目空间时导入当前项目，没有项目空间时复用后端行为创建 `browser-upload` 项目。导入成功后刷新项目列表、当前项目、文档列表和导入批次历史。本阶段不迁移浏览器文件夹导入、同步当前项目目录、导入预检、删除文档、文档集合、后端行为或数据库 schema。

## 2. 背景

- B-141A 已完成：Vue + Vite 工程骨架和 FastAPI 静态托管策略已存在。
- B-141B 已完成：Vue API client、共享状态模型、AppShell 和四个基础 view 已存在。
- B-141C 已完成：Vue 资料库已有项目空间列表、选择和创建基础。
- B-141E 已完成：Vue 资料库已有文档列表和单文档预览。
- B-141F 已完成：Vue 资料库已有文本笔记和 URL 摘录导入。
- B-141G 已完成：Vue 资料库已有导入批次历史。
- `POST /api/import/upload` 已存在，接口契约见 `docs/design/api-spec.md`。普通文件上传使用 `source_type=file_upload`，无当前项目时后端创建 `browser-upload` 项目。
- `webapp/static/` 仍作为完整业务 UI fallback 保留；B-141H 不删除 legacy 前端。

## 3. 任务清单

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141H plan，并将 BACKLOG 说明列追加本 plan 路径
- [x] 先写 Vue 普通文件上传导入红灯测试，覆盖 imports API helper、DocumentImportPanel 文件入口、App 接入和状态刷新
- [ ] 扩展 `frontend/src/api/imports.js`，复用既有 `/api/import/upload`，读取普通文件名为 `relative_path`，DOCX/PDF 走 `content_base64 + size`，其他文件走 `content`
- [ ] 更新 `DocumentImportPanel`，新增普通文件上传按钮和隐藏 `multiple` file input，不设置 `webkitdirectory`
- [ ] 更新 `App.vue`，处理文件上传导入响应，成功后刷新项目空间、文档列表和导入批次历史
- [ ] 同步功能文档、架构/测试/devlog/CHANGELOG 中的 B-141H 说明
- [ ] 完成验证、提交 B-141H，并更新本 plan 快照；B-141 保持 `doing`

## 4. 影响范围

| 类型 | 路径 | 说明 |
|------|------|------|
| 前端 | `frontend/src/api/imports.js` | 修改：增加普通文件上传导入 API helper 和文件读取 helper |
| 前端 | `frontend/src/components/DocumentImportPanel.vue` | 修改：增加普通文件上传入口 |
| 前端 | `frontend/src/App.vue` | 修改：处理文件上传导入响应与刷新 |
| 前端 | `frontend/src/styles.css` | 修改：如有必要补充上传入口样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 B-141H Vue source/static contract tests |
| 文档 | `docs/features/frontend-engineering.md` | 修改：B-141H 行为边界 |
| 文档 | `docs/design/architecture-overview.md`, `docs/guides/testing.md` | 修改：Vue 文件上传 helper/组件说明 |
| 文档 | `CHANGELOG.md`, `docs/devlog/2026-05-26.md` | 修改：实施记录 |
| 文档 | `docs/BACKLOG.md`, `docs/plans/B-141-vue-file-upload-import.md` | 修改/新增：计划联动 |

## 5. 冲突扫描

### 5.1 已扫描

| 路径 | 判断 |
|------|------|
| `docs/plans/B-141-vue-vite-foundation.md` | B-141A 已完成；B-141H 基于 Vue/Vite 骨架继续 |
| `docs/plans/B-141-vue-api-layout.md` | B-141B 已完成；B-141H 复用 API client、共享状态和 Library view |
| `docs/plans/B-141-vue-project-space.md` | B-141C 已完成；B-141H 复用项目空间选择状态 |
| `docs/plans/B-141-vue-workbench-answer-entry.md` | B-141D 已完成；B-141H 不修改问答入口 |
| `docs/plans/B-141-vue-document-list-preview.md` | B-141E 已完成；B-141H 成功导入后刷新文档列表 |
| `docs/plans/B-141-vue-text-url-import.md` | B-141F 已完成；B-141H 扩展同一导入面板，但不改变文本/URL 导入契约 |
| `docs/plans/B-141-vue-import-batch-history.md` | B-141G 已完成；B-141H 成功导入后刷新批次历史 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 UI 计划，未标记 Active/Interrupted |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 计划，未标记 Active/Interrupted |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active/Interrupted |

### 5.2 处理结论

| 计划 | 重叠点 | 处理 |
|------|--------|------|
| `docs/plans/B-141-vue-vite-foundation.md` | 同属 B-141，但该 plan 已完成 B-141A | 分区：B-141H 不重复修改 Vite/静态托管策略 |
| `docs/plans/B-141-vue-api-layout.md` | 同属 B-141，但该 plan 已完成 B-141B | 分区：B-141H 复用 API/state/layout 基础，只迁移普通文件上传导入 |
| `docs/plans/B-141-vue-project-space.md` | 同属 B-141，但该 plan 已完成 B-141C | 分区：B-141H 只读取和更新项目选择状态，不重复迁移项目空间面板 |
| `docs/plans/B-141-vue-workbench-answer-entry.md` | 同属 B-141，但该 plan 已完成 B-141D | 分区：B-141H 不修改工作台问答入口 |
| `docs/plans/B-141-vue-document-list-preview.md` | 同属 B-141，但该 plan 已完成 B-141E | 分区：B-141H 只在导入成功后刷新文档列表，不扩展预览语义 |
| `docs/plans/B-141-vue-text-url-import.md` | 同属 B-141，但该 plan 已完成 B-141F | 分区：B-141H 在同一导入面板追加普通文件上传入口，不改变文本/URL 导入 |
| `docs/plans/B-141-vue-import-batch-history.md` | 同属 B-141，但该 plan 已完成 B-141G | 分区：B-141H 只在导入成功后刷新批次历史，不改变批次详情 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 UI 计划，未标记 Active/Interrupted | 分区：B-141H 不修改 legacy desktop/UI 文档计划 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 计划，未标记 Active/Interrupted | 分区：B-141H 不修改 legacy `src/` |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active/Interrupted | 分区：B-141H 不修改数据库 schema |

## 6. 验收标准

- [ ] Vue 资料库页提供“选择文件上传导入”按钮和普通 `multiple` file input。
- [ ] 普通 file input 不设置 `webkitdirectory`。
- [ ] 有当前项目空间时，上传请求包含 `project_id` 和 `source_type=file_upload`。
- [ ] 没有当前项目空间时，上传请求包含 `project_name=browser-upload` 和 `source_type=file_upload`，允许后端创建上传项目。
- [ ] DOCX/PDF 文件以 `content_base64 + size` 上传，普通文本文件以 `content` 上传，`relative_path` 使用文件名。
- [ ] 导入成功后刷新项目空间、当前项目、文档列表和导入批次历史。
- [ ] B-141H 不迁移浏览器文件夹导入、同步当前项目目录、导入预检、文档集合、删除文档或数据库 schema。
- [ ] `webapp/static/` 仍保留为迁移期 fallback。
- [ ] 相关测试与文档同步完成。

## 7. 回流清单

删除或中断本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141H 普通文件上传导入迁移边界 | `docs/features/frontend-engineering.md` | [ ] |
| Vue file upload helper 和资料库导入组件边界 | `docs/design/architecture-overview.md` | [ ] |
| B-141H Vue source/static contract 测试命令 | `docs/guides/testing.md` | [ ] |
| 对外变更摘要 | `CHANGELOG.md` | [ ] |
| 实施记录 | `docs/devlog/2026-05-26.md` | [ ] |
| B-141 仍处于 doing，等待后续页面迁移 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-05-26：用户继续 B-141 技术栈迁移，并要求整体完成后再推送；本切片继续按 plan 规则提交，但不推送。
- 2026-05-26：B-141H 选择“资料库普通文件上传导入”薄片，不迁移浏览器文件夹导入、同步当前项目目录、预检、删除、集合或数据库 schema。
- 2026-05-26：冲突扫描发现 B-141A/B/C/D/E/F/G plan 已完成但保留，其他 superpowers 历史计划未标记 Active/Interrupted；按分区处理。
- 2026-05-26：创建 `docs/plans/B-141-vue-file-upload-import.md`，并将 BACKLOG B-141 说明列追加本 plan 路径。
- 2026-05-26：确认 B-141H 红灯为 3 failed / 19 passed，失败点集中在缺少 `importBrowserFiles`、文件上传面板入口和 App 上传响应接入。

## 9. 状态快照

- **最后更新时间**：2026-05-26
- **进度**：已完成 2 / 7 项（见 § 3 勾选状态）
- **最新 commit**：`0eaca26` — `docs: 创建 B-141H 文件上传计划`
- **代码状态**：分支 `fix/url-virtual-source-preserve`；存在大量既有未提交改动；本轮只追加 Vue 资料库普通文件上传导入相关变更
- **下一步**：实现 B-141H 普通文件上传导入最小 Vue 薄片
- **续任务须知**：B-141H 不删除 `webapp/static/`，不迁移浏览器文件夹导入/目录同步/预检/删除/集合，不修改数据库 schema，不新增 Pinia/Vue Router；技术栈迁移整体完成前不推送
