# B-141 Vue Browser Folder Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成 B-141I：把资料库页的浏览器文件夹上传导入迁移到 Vue。

**Architecture:** 扩展 `frontend/src/api/imports.js`，新增 `importBrowserFolder({ files })`，读取 `webkitRelativePath` 生成项目名和相对路径，复用既有 `POST /api/import/upload`，并显式发送 `source_type=browser_folder_upload`。`DocumentImportPanel.vue` 增加单独的文件夹选择入口和隐藏 `webkitdirectory multiple` input；`App.vue` 在导入成功后选择后端返回项目，刷新项目空间、文档列表和导入批次历史。

**Tech Stack:** Vue 3 + Vite；浏览器 File API / `webkitdirectory`；现有 `frontend/src/api/client.js`；FastAPI 既有 `/api/import/upload` 接口。

---

> 状态：Active
> 创建时间：2026-05-26
> 负责人：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md, docs/guides/testing.md

## 1. 目标

完成 B-141I：在 Vue 资料库页中提供浏览器文件夹上传导入入口。用户点击“选择本机文件夹导入”后，通过浏览器授权选择一个文件夹；前端使用 `webkitRelativePath` 去掉根目录作为文档 `relative_path`，根目录名作为 `project_name`，后端创建或返回 `browser-upload:<project_name>` 项目空间。导入成功后 Vue 选择该项目空间，并刷新项目列表、文档列表和导入批次历史。本阶段不迁移同步当前项目目录、导入预检、删除文档、文档集合、后端行为或数据库 schema。

## 2. 背景

- B-141A 已完成：Vue + Vite 工程骨架和 FastAPI 静态托管策略已存在。
- B-141B 已完成：Vue API client、共享状态模型、AppShell 和四个基础 view 已存在。
- B-141C 已完成：Vue 资料库已有项目空间列表、选择和创建基础。
- B-141E 已完成：Vue 资料库已有文档列表和单文档预览。
- B-141F 已完成：Vue 资料库已有文本笔记和 URL 摘录导入。
- B-141G 已完成：Vue 资料库已有导入批次历史。
- B-141H 已完成：Vue 资料库已有普通文件上传导入，普通 file input 明确不设置 `webkitdirectory`。
- `POST /api/import/upload` 已存在，接口契约见 `docs/design/api-spec.md`。浏览器文件夹上传使用 `source_type=browser_folder_upload`，不读取本机原始路径。
- `webapp/static/` 仍作为完整业务 UI fallback 保留；B-141I 不删除 legacy 前端。

## 3. 任务清单

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-141I plan，并将 BACKLOG 说明列追加本 plan 路径
- [x] 先写 Vue 浏览器文件夹导入红灯测试，覆盖 imports API helper、DocumentImportPanel 文件夹入口、App 接入和状态刷新
- [x] 扩展 `frontend/src/api/imports.js`，复用既有 `/api/import/upload`，读取 `webkitRelativePath`，根目录作为 `project_name`，相对路径去掉根目录
- [x] 更新 `DocumentImportPanel`，新增浏览器文件夹导入按钮和隐藏 `webkitdirectory multiple` input，并保持普通文件上传 input 不设置 `webkitdirectory`
- [x] 更新 `App.vue`，处理浏览器文件夹导入响应，成功后选择后端返回项目并刷新项目空间、文档列表和导入批次历史
- [x] 同步功能文档、架构/测试/devlog/CHANGELOG 中的 B-141I 说明
- [ ] 完成验证、提交 B-141I，并更新本 plan 快照；B-141 保持 `doing`

## 4. 影响范围

| 类型 | 路径 | 说明 |
|------|------|------|
| 前端 | `frontend/src/api/imports.js` | 修改：增加浏览器文件夹导入 API helper 和 `webkitRelativePath` 处理 |
| 前端 | `frontend/src/components/DocumentImportPanel.vue` | 修改：增加浏览器文件夹导入入口 |
| 前端 | `frontend/src/App.vue` | 修改：处理浏览器文件夹导入响应与刷新 |
| 前端 | `frontend/src/views/LibraryView.vue` | 修改：转发 `import-folder` 事件 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 B-141I Vue source/static contract tests |
| 文档 | `docs/features/frontend-engineering.md` | 修改：B-141I 行为边界 |
| 文档 | `docs/design/architecture-overview.md`, `docs/guides/testing.md` | 修改：Vue 浏览器文件夹上传 helper/组件说明 |
| 文档 | `CHANGELOG.md`, `docs/devlog/2026-05-26.md` | 修改：实施记录 |
| 文档 | `docs/BACKLOG.md`, `docs/plans/B-141-vue-browser-folder-import.md` | 修改/新增：计划联动 |

## 5. 冲突扫描

### 5.1 已扫描

| 路径 | 判断 |
|------|------|
| `docs/plans/B-141-vue-vite-foundation.md` | B-141A 已完成；B-141I 基于 Vue/Vite 骨架继续 |
| `docs/plans/B-141-vue-api-layout.md` | B-141B 已完成；B-141I 复用 API client、共享状态和 Library view |
| `docs/plans/B-141-vue-project-space.md` | B-141C 已完成；B-141I 成功后选择后端返回项目空间 |
| `docs/plans/B-141-vue-workbench-answer-entry.md` | B-141D 已完成；B-141I 不修改问答入口 |
| `docs/plans/B-141-vue-document-list-preview.md` | B-141E 已完成；B-141I 成功导入后刷新文档列表 |
| `docs/plans/B-141-vue-text-url-import.md` | B-141F 已完成；B-141I 扩展同一导入面板，但不改变文本/URL 导入契约 |
| `docs/plans/B-141-vue-import-batch-history.md` | B-141G 已完成；B-141I 成功导入后刷新批次历史 |
| `docs/plans/B-141-vue-file-upload-import.md` | B-141H 已完成；B-141I 增加独立文件夹 input，保持普通文件上传 input 不设置 `webkitdirectory` |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 UI 计划，未标记 Active/Interrupted |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 计划，未标记 Active/Interrupted |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active/Interrupted |

### 5.2 处理结论

| 计划 | 重叠点 | 处理 |
|------|--------|------|
| `docs/plans/B-141-vue-vite-foundation.md` | 同属 B-141，但该 plan 已完成 B-141A | 分区：B-141I 不重复修改 Vite/静态托管策略 |
| `docs/plans/B-141-vue-api-layout.md` | 同属 B-141，但该 plan 已完成 B-141B | 分区：B-141I 复用 API/state/layout 基础，只迁移浏览器文件夹上传导入 |
| `docs/plans/B-141-vue-project-space.md` | 同属 B-141，但该 plan 已完成 B-141C | 分区：B-141I 只在导入成功后选择返回项目，不重复迁移项目空间面板 |
| `docs/plans/B-141-vue-workbench-answer-entry.md` | 同属 B-141，但该 plan 已完成 B-141D | 分区：B-141I 不修改工作台问答入口 |
| `docs/plans/B-141-vue-document-list-preview.md` | 同属 B-141，但该 plan 已完成 B-141E | 分区：B-141I 只在导入成功后刷新文档列表，不扩展预览语义 |
| `docs/plans/B-141-vue-text-url-import.md` | 同属 B-141，但该 plan 已完成 B-141F | 分区：B-141I 在同一导入面板追加文件夹入口，不改变文本/URL 导入 |
| `docs/plans/B-141-vue-import-batch-history.md` | 同属 B-141，但该 plan 已完成 B-141G | 分区：B-141I 只在导入成功后刷新批次历史，不改变批次详情 |
| `docs/plans/B-141-vue-file-upload-import.md` | 同属 B-141，但该 plan 已完成 B-141H | 分区：B-141I 新增独立 `folderInput`，不改变普通 `fileInput` 的非目录语义 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 UI 计划，未标记 Active/Interrupted | 分区：B-141I 不修改 legacy desktop/UI 文档计划 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 计划，未标记 Active/Interrupted | 分区：B-141I 不修改 legacy `src/` |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active/Interrupted | 分区：B-141I 不修改数据库 schema |

## 6. 验收标准

- [ ] Vue 资料库页提供“选择本机文件夹导入”按钮和单独的 `webkitdirectory multiple` file input。
- [ ] 普通文件上传 input 仍不设置 `webkitdirectory`。
- [ ] 浏览器文件夹导入请求包含 `source_type=browser_folder_upload`。
- [ ] `webkitRelativePath` 的首段作为 `project_name`，发送给后端；文档 `relative_path` 去掉首段根目录。
- [ ] DOCX/PDF 文件以 `content_base64 + size` 上传，普通文本文件以 `content` 上传。
- [ ] 导入成功后选择后端返回项目，并刷新项目空间、当前项目、文档列表和导入批次历史。
- [ ] B-141I 不迁移同步当前项目目录、导入预检、文档集合、删除文档或数据库 schema。
- [ ] `webapp/static/` 仍保留为迁移期 fallback。
- [ ] 相关测试与文档同步完成。

## 7. 回流清单

删除或中断本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141I 浏览器文件夹上传导入迁移边界 | `docs/features/frontend-engineering.md` | [x] |
| Vue browser folder helper 和资料库导入组件边界 | `docs/design/architecture-overview.md` | [x] |
| B-141I Vue source/static contract 测试命令 | `docs/guides/testing.md` | [x] |
| 对外变更摘要 | `CHANGELOG.md` | [x] |
| 实施记录 | `docs/devlog/2026-05-26.md` | [x] |
| B-141 仍处于 doing，等待后续页面迁移 | `docs/BACKLOG.md` | [x] |

## 8. 执行记录

- 2026-05-26：用户继续 B-141 技术栈迁移，并要求整体完成后再推送；本切片继续按 plan 规则提交，但不推送。
- 2026-05-26：B-141I 选择“资料库浏览器文件夹上传导入”薄片，不迁移目录同步、导入预检、删除、集合或数据库 schema。
- 2026-05-26：冲突扫描发现 B-141A/B/C/D/E/F/G/H plan 已完成但保留，其他 superpowers 历史计划未标记 Active/Interrupted；按分区处理。
- 2026-05-26：创建 `docs/plans/B-141-vue-browser-folder-import.md`，并将 BACKLOG B-141 说明列追加本 plan 路径。
- 2026-05-26：确认 B-141I 红灯为 3 failed / 22 passed，失败点集中在缺少 `importBrowserFolder`、文件夹上传面板入口和 App 文件夹上传响应接入。
- 2026-05-26：新增 Vue 浏览器文件夹上传导入 helper、面板入口和 App 响应接入，聚焦测试 25 passed。
- 2026-05-26：同步功能文档、架构说明、测试指南、CHANGELOG 和 devlog 中的 B-141I 边界。

## 9. 状态快照

- **最后更新时间**：2026-05-26
- **进度**：已完成 6 / 7 项（见 § 3 勾选状态）
- **最新 commit**：`0c63878` — `feat: 接入 Vue 浏览器文件夹导入`
- **代码状态**：分支 `fix/url-virtual-source-preserve`；存在大量既有未提交改动；本轮只追加 Vue 资料库浏览器文件夹上传导入相关变更
- **下一步**：完成 B-141I 完整验证并提交收尾快照
- **续任务须知**：B-141I 不删除 `webapp/static/`，不迁移目录同步/预检/删除/集合，不修改数据库 schema，不新增 Pinia/Vue Router；技术栈迁移整体完成前不推送
