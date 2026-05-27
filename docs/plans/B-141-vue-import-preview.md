# B-141 Vue Import Preview Implementation Plan

**Goal:** 完成 B-141K：把资料库页的“导入预检”入口迁移到 Vue。

**Architecture:** `frontend/src/api/imports.js` 包装既有 `GET /api/import/preview` 只读契约。`DocumentImportPanel.vue` 在本地目录区域提供预检入口和结果摘要，`App.vue` 读取当前 `selectedProjectId` 后保存预检状态。B-141K 不新增后端接口、不创建导入批次、不修改数据库 schema。

> 状态：Active
> 创建时间：2026-05-27
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md, docs/design/api-spec.md

## 1. 目标

完成 B-141K：在 Vue 资料库页中提供当前项目目录导入预检入口。用户选择已有项目空间后，可点击“预检当前项目目录”调用既有 `GET /api/import/preview?project_id=...`，只读展示预计可导入文件数、跳过数和跳过原因。本阶段不执行导入、不创建导入批次、不迁移删除文档、文档集合、项目改名/删除、后端行为或数据库 schema。

## 2. 前置条件

- B-141A 已完成：Vue + Vite 工程骨架和 FastAPI 静态托管策略已存在。
- B-141B 已完成：Vue API client、共享状态模型、AppShell 和四个基础 view 已存在。
- B-141C 已完成：Vue 资料库已有项目空间列表、选择和创建基础。
- B-141E 已完成：Vue 资料库已有文档列表和单文档预览。
- B-141F/G/H/I/J 已完成：Vue 资料库已有轻量导入、导入批次历史、普通文件上传、浏览器文件夹上传和当前目录同步。
- `GET /api/import/preview` 已在后端存在，且接口契约见 `docs/design/api-spec.md`。
- `webapp/static/` 仍作为完整业务 UI fallback 保留；B-141K 不删除 legacy 前端。

## 3. 任务拆解

- [x] 创建 B-141K plan，并将 BACKLOG 说明列追加本 plan 路径
- [x] 新增 Vue source/static contract 红灯测试，覆盖导入预检 API helper、面板入口和 App 状态接入
- [x] 实现 `previewProjectImport`、预检 UI、状态流和错误提示
- [x] 同步功能文档、架构/测试/devlog/CHANGELOG 中的 B-141K 说明
- [ ] 完成验证、提交 B-141K，并更新本 plan 快照；B-141 保持 `doing`

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/imports.js` | 修改：新增导入预检 API helper |
| 代码 | `frontend/src/components/DocumentImportPanel.vue` | 修改：新增预检入口和结果摘要 |
| 代码 | `frontend/src/views/LibraryView.vue` | 修改：透传预检状态和事件 |
| 代码 | `frontend/src/App.vue` | 修改：接入预检状态流 |
| 代码 | `frontend/src/state/app-state.js` | 修改：新增预检 UI 状态 |
| 代码 | `frontend/src/styles.css` | 修改：新增预检摘要和跳过明细样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 B-141K Vue source/static contract tests |
| 文档 | `docs/features/frontend-engineering.md` | 修改：B-141K 行为边界 |
| 文档 | `docs/design/architecture-overview.md` | 修改：Vue 导入 helper/组件职责说明 |
| 文档 | `docs/guides/testing.md` | 修改：Vue 导入预检验证说明 |
| 文档 | `CHANGELOG.md`, `docs/devlog/2026-05-27.md` | 修改/新增：记录 B-141K 实施结果 |
| 文档 | `docs/BACKLOG.md`, `docs/plans/B-141-vue-import-preview.md` | 修改/新增：计划联动 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-vite-foundation.md` | B-141A 已完成；B-141K 基于 Vue/Vite 骨架继续 |
| `docs/plans/B-141-vue-api-layout.md` | B-141B 已完成；B-141K 复用 API client、共享状态和 Library view |
| `docs/plans/B-141-vue-project-space.md` | B-141C 已完成；B-141K 复用当前项目选择状态 |
| `docs/plans/B-141-vue-document-list-preview.md` | B-141E 已完成；B-141K 不修改文档预览语义 |
| `docs/plans/B-141-vue-directory-sync.md` | B-141J 已完成；B-141K 和目录同步共用本地目录区域 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| B-141A/J 相关已完成 plan | 同属 B-141，但均已完成各自薄片 | 分区：B-141K 只迁移导入预检入口，不重复调整既有 Vue/Vite、项目、文档、导入或目录同步薄片 |
| 历史 superpowers 计划 | 未标记 Active/Interrupted | 分区：B-141K 不修改 legacy `src/`、数据库 schema 或历史 desktop UI |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/frontend-engineering.md` 的 B-141K 业务边界。
- [ ] `GET /api/import/preview` 仍为只读；Vue 预检不创建导入批次、不刷新文档列表为导入完成状态。
- [ ] 未选择项目空间时预检入口禁用，并沿用“请先创建或选择项目空间”校验。
- [ ] 测试通过（参照 `docs/guides/testing.md` 最低要求）。
- [ ] 相关文档已同步（见下方“回流清单”）。
- [ ] B-141 保持 `doing`，等待后续 Vue 页面迁移；不推送。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141K 导入预检迁移边界 | `docs/features/frontend-engineering.md` | [x] |
| Vue 导入 helper、导入面板和状态流职责 | `docs/design/architecture-overview.md` | [x] |
| B-141K Vue source/static contract 测试命令 | `docs/guides/testing.md` | [x] |
| B-141K 用户可见变更 | `CHANGELOG.md` | [x] |
| B-141K 执行记录与验证结果 | `docs/devlog/2026-05-27.md` | [x] |
| B-141 仍处于 doing，等待后续页面迁移 | `docs/BACKLOG.md` | [x] |

若产生了重大技术决策，必须在删除 plan 前新建对应 ADR。本切片预期不触发 ADR。

## 8. 执行记录

- 2026-05-27：用户继续 B-141 技术栈迁移，并要求整体完成后再推送；本切片继续按 plan 规则提交，但不推送。
- 2026-05-27：B-141K 选择“资料库导入预检”薄片，不迁移删除、集合、项目改名/删除、后端行为或数据库 schema。
- 2026-05-27：冲突扫描发现 B-141A/J 相关 plan 已完成但保留，其他 superpowers 历史计划未标记 Active/Interrupted；按分区处理。
- 2026-05-27：创建 `docs/plans/B-141-vue-import-preview.md`，并将 BACKLOG B-141 说明列追加本 plan 路径。
- 2026-05-27：确认 B-141K 红灯为 3 failed / 28 passed，失败点集中在缺少 `previewProjectImport`、导入面板预检入口和 App 预检状态接入。
- 2026-05-27：实现 Vue 导入预检 helper、导入面板入口、只读结果摘要和 App 状态接入；聚焦测试 `tests/test_webapp/test_frontend_vue_app.py` 为 31 passed，`npm run build` 成功。
- 2026-05-27：同步 `frontend-engineering`、架构说明、测试指南、CHANGELOG 和当日 devlog；`api-spec` 未改，因为后端 `GET /api/import/preview` 契约没有变化。

## 9. 状态快照

- **最后更新**：2026-05-27 13:55
- **进度**：已完成 4 / 5 项（见 § 3 勾选状态）
- **最新 commit**：`3dfb50d` — feat: 接入 Vue 导入预检
- **代码状态**：分支 `fix/url-virtual-source-preserve`；存在大量既有未提交改动；B-141K 文档同步已完成待提交
- **下一步**：完成验证、提交 B-141K，并更新本 plan 快照；B-141 保持 `doing`
- **续任务须知**：B-141K 不删除 `webapp/static/`，不迁移删除/集合/项目改名/删除，不修改后端 API 或数据库 schema，不新增 Pinia/Vue Router；技术栈迁移整体完成前不推送
