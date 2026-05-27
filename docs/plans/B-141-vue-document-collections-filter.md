# B-141 Vue Document Collections Filter Implementation Plan

**Goal:** 完成 B-141L：把资料库页的文档集合只读列表和文档列表筛选迁移到 Vue。

**Architecture:** 新增 Vue 文档集合 API helper，包装既有 `GET /api/document-collections`。新增 `DocumentCollectionPanel.vue` 只展示集合筛选入口、集合列表和文档数；`App.vue` 维护 `documentCollections`、`selectedDocumentCollectionId`、加载/错误状态，并把选择结果传给既有 `listDocuments(projectId, collectionId)`。B-141L 不实现新建/编辑/删除集合，也不实现加入/移出文档。

> 状态：Active
> 创建时间：2026-05-27
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/document-collections-design.md, docs/design/architecture-overview.md

## 1. 目标

完成 B-141L：在 Vue 资料库页中提供文档集合只读筛选。用户选择项目空间后，可看到“全部文档 / 未分组 / 指定集合”的筛选入口和集合列表；选择筛选项后，Vue 复用既有 `GET /api/documents?project_id=...&collection_id=...` 重新加载文档列表。本阶段不迁移集合新建、更新、删除、加入文档或移出文档，不修改后端行为或数据库 schema。

## 2. 前置条件

- B-141A/K 已完成：Vue + Vite 工程骨架、资料库项目空间、文档浏览、导入区域和导入批次历史已存在。
- `frontend/src/api/documents.js` 已支持 `listDocuments(projectId, collectionId)`。
- 后端 `GET /api/document-collections?project_id=...` 和 `GET /api/documents?collection_id=...` 已存在，接口契约见 `docs/design/api-spec.md` 和 `docs/design/document-collections-design.md`。
- `webapp/static/` 仍作为完整业务 UI fallback 保留；B-141L 不删除 legacy 前端。

## 3. 任务拆解

- [x] 创建 B-141L plan，并将 BACKLOG 说明列追加本 plan 路径
- [x] 新增 Vue source/static contract 红灯测试，覆盖集合 API helper、集合筛选面板和 App 状态接入
- [x] 实现集合列表读取、筛选 UI 和文档列表过滤状态流
- [ ] 同步功能文档、架构/测试/devlog/CHANGELOG 中的 B-141L 说明
- [ ] 完成验证、提交 B-141L，并更新本 plan 快照；B-141 保持 `doing`

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `frontend/src/api/document-collections.js` | 新增：文档集合只读 API helper |
| 代码 | `frontend/src/components/DocumentCollectionPanel.vue` | 新增：集合筛选和集合列表 UI |
| 代码 | `frontend/src/views/LibraryView.vue` | 修改：组合集合面板并透传状态/事件 |
| 代码 | `frontend/src/App.vue` | 修改：接入集合读取与筛选状态流 |
| 代码 | `frontend/src/state/app-state.js` | 修改：补齐集合加载/错误状态 |
| 代码 | `frontend/src/styles.css` | 修改：新增集合面板列表样式 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 修改：增加 B-141L Vue source/static contract tests |
| 文档 | `docs/features/frontend-engineering.md` | 修改：B-141L 行为边界 |
| 文档 | `docs/design/architecture-overview.md` | 修改：Vue 文档集合 helper/组件职责说明 |
| 文档 | `docs/guides/testing.md` | 修改：Vue 文档集合筛选验证说明 |
| 文档 | `CHANGELOG.md`, `docs/devlog/2026-05-27.md` | 修改：记录 B-141L 实施结果 |
| 文档 | `docs/BACKLOG.md`, `docs/plans/B-141-vue-document-collections-filter.md` | 修改/新增：计划联动 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| `docs/plans/B-141-vue-vite-foundation.md` | B-141A 已完成；B-141L 基于 Vue/Vite 骨架继续 |
| `docs/plans/B-141-vue-api-layout.md` | B-141B 已完成；B-141L 复用 API client、共享状态和 Library view |
| `docs/plans/B-141-vue-project-space.md` | B-141C 已完成；B-141L 复用当前项目选择状态 |
| `docs/plans/B-141-vue-document-list-preview.md` | B-141E 已完成；B-141L 复用文档列表和 `collection_id` 参数 |
| `docs/plans/B-141-vue-import-preview.md` | B-141K 已完成；B-141L 在同一资料库页继续迁移集合管理入口 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| B-141A/K 相关已完成 plan | 同属 B-141，但均已完成各自薄片 | 分区：B-141L 只迁移文档集合只读筛选，不重复调整既有 Vue/Vite、项目、文档、导入或批次薄片 |
| 历史 superpowers 计划 | 未标记 Active/Interrupted | 分区：B-141L 不修改 legacy `src/`、数据库 schema 或历史 desktop UI |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/frontend-engineering.md` 和 `docs/design/document-collections-design.md` 的 B-141L 边界。
- [ ] Vue 资料库可读取当前项目集合列表，并显示“全部文档 / 未分组 / 指定集合”筛选入口。
- [ ] 选择筛选项后调用既有文档列表 helper，按 `collection_id` 刷新文档列表和清空当前预览。
- [ ] B-141L 不提供集合新建、编辑、删除、加入文档或移出文档入口。
- [ ] 测试通过（参照 `docs/guides/testing.md` 最低要求）。
- [ ] 相关文档已同步（见下方“回流清单”）。
- [ ] B-141 保持 `doing`，等待后续 Vue 页面迁移；不推送。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-141L 文档集合只读筛选迁移边界 | `docs/features/frontend-engineering.md` | [ ] |
| Vue 文档集合 helper、集合面板和状态流职责 | `docs/design/architecture-overview.md` | [ ] |
| B-141L Vue source/static contract 测试命令 | `docs/guides/testing.md` | [ ] |
| B-141L 用户可见变更 | `CHANGELOG.md` | [ ] |
| B-141L 执行记录与验证结果 | `docs/devlog/2026-05-27.md` | [ ] |
| B-141 仍处于 doing，等待后续页面迁移 | `docs/BACKLOG.md` | [x] |

若产生了重大技术决策，必须在删除 plan 前新建对应 ADR。本切片预期不触发 ADR。

## 8. 执行记录

- 2026-05-27：用户继续 B-141 技术栈迁移，并要求整体完成后再推送；本切片继续按 plan 规则提交，但不推送。
- 2026-05-27：B-141L 选择“资料库文档集合只读筛选”薄片，不迁移集合 CRUD、加入/移出文档、后端行为或数据库 schema。
- 2026-05-27：冲突扫描发现 B-141A/K 相关 plan 已完成但保留，其他 superpowers 历史计划未标记 Active/Interrupted；按分区处理。
- 2026-05-27：创建 `docs/plans/B-141-vue-document-collections-filter.md`，并将 BACKLOG B-141 说明列追加本 plan 路径。
- 2026-05-27：确认 B-141L 红灯为 3 failed / 31 passed，失败点集中在缺少 `document-collections.js`、`DocumentCollectionPanel.vue` 和 App 集合状态接入。
- 2026-05-27：实现 Vue 文档集合只读 helper、集合筛选面板和 App 筛选状态；聚焦测试 `tests/test_webapp/test_frontend_vue_app.py` 为 34 passed，`npm run build` 成功。

## 9. 状态快照

- **最后更新**：2026-05-27 14:03
- **进度**：已完成 3 / 5 项（见 § 3 勾选状态）
- **最新 commit**：`cb947f0` — test: 覆盖 Vue 文档集合筛选入口
- **代码状态**：分支 `fix/url-virtual-source-preserve`；存在大量既有未提交改动；B-141L 文档集合筛选实现已完成待提交
- **下一步**：同步功能文档、架构/测试/devlog/CHANGELOG 中的 B-141L 说明
- **续任务须知**：B-141L 不删除 `webapp/static/`，不迁移集合 CRUD 或加入/移出文档，不修改后端 API 或数据库 schema，不新增 Pinia/Vue Router；技术栈迁移整体完成前不推送
