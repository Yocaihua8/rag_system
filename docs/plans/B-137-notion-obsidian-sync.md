# B-137 Notion / Obsidian 本地导出同步

> 状态：Active
> 创建时间：2026-06-28
> 创建方：Codex
> 关联 BACKLOG：B-137
> 关联功能文档：docs/features/notion-obsidian-sync.md
> 关联设计文档：docs/design/api-spec.md

## 1. 目标

在 Web MVP 资料库导入流程中新增 Notion Markdown zip 与 Obsidian vault 两个本地导入入口，使用户可以把本地导出的知识库资料导入当前项目并进入既有 RAG 检索链路。

## 2. 前置条件

- 已读取 `AGENTS.md`、`docs/BACKLOG.md`、`docs/features/project-space-ingestion.md`、`docs/design/api-spec.md`。
- 当前 worktree：`fix/B-137-notion-obsidian-sync`。
- 当前基线缺少用户请求中提到的 `docs/design/new-architecture-design.md §5.7`；本 plan 先以 `docs/features/notion-obsidian-sync.md` 和现有 `docs/design/api-spec.md` 作为可提交契约，避免搬入主 checkout 未提交的大文档。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 任务 1：为 Notion zip / Obsidian vault 导入写后端红灯测试
- [x] 任务 2：实现 Notion zip 与 Obsidian vault 后端导入服务和 API
- [x] 任务 3：为 Vue 导入入口写红灯测试
- [ ] 任务 4：接入 Vue 资料库导入面板、API helper 和 App 刷新流程
- [ ] 任务 5：同步接口与功能文档，运行回归验证
- [ ] 任务 6：关闭 B-137，删除 plan

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `webapp/notion_obsidian_import.py` | 新增 |
| 代码 | `webapp/routes/imports.py` | 修改：新增两个导入 API 分支和批次来源 |
| 代码 | `webapp/source_import.py` / `webapp/ingestion.py` | 按需修改：保护 `notion-zip:` 虚拟来源或复用导入规则 |
| 代码 | `frontend/src/api/imports.js` 或现有导入 helper | 新增/修改：Notion zip 与 Obsidian vault API 调用 |
| 代码 | `frontend/src/components/DocumentImportPanel.vue` | 修改：新增两个导入入口 |
| 代码 | `frontend/src/App.vue` | 修改：接入事件与刷新流程 |
| 测试 | `tests/test_webapp/test_api.py` | 新增后端 API 行为测试 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 新增 Vue 契约测试 |
| 文档 | `docs/features/notion-obsidian-sync.md` | 新增/更新 |
| 文档 | `docs/features/README.md` | 修改：登记功能文档 |
| 文档 | `docs/design/api-spec.md` | 修改：新增接口契约 |
| 文档 | `docs/BACKLOG.md` | 修改：状态流转 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-137 可在当前 Web MVP 导入链路内独立实现 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| docs/plans/B-145-tauri-windows-packaging.md | 无直接重叠；B-145 影响 Tauri 打包与 sidecar，不改导入 API | 分区 |
| docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md | 历史桌面 UI plan，涉及 `src/desktop/`，不改 Web 导入链路 | 分区 |
| docs/superpowers/plans/2026-05-11-project-knowledge-points.md | 历史 legacy 知识点 plan，涉及 `src/`，不改 Web 导入链路 | 分区 |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/notion-obsidian-sync.md`
- [ ] 后端 API 测试覆盖成功导入、跳过不支持文件、缺失/非法参数
- [ ] Vue 契约测试覆盖 API helper、导入面板入口和 App 事件接线
- [ ] `tests/test_webapp` 相关测试通过
- [ ] `npm run build` 通过
- [ ] 文档已同步
- [ ] BACKLOG 条目 B-137 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-137 功能范围与非目标 | `docs/features/notion-obsidian-sync.md` | [ ] |
| Notion zip / Obsidian vault API 契约 | `docs/design/api-spec.md` | [ ] |
| 功能文档索引 | `docs/features/README.md` | [x] |
| BACKLOG 状态与完成说明 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-06-28：创建 plan 时发现当前 worktree 缺少 `docs/design/new-architecture-design.md`；按现有已跟踪文档落地 B-137 契约，避免吸收主 checkout 未提交大文档。

## 9. 状态快照

- **最后更新**：2026-06-28 22:49
- **进度**：已完成 3 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`ab6b7f2` — feat: 接入 Notion zip 与 Obsidian vault 导入接口
- **代码状态**：`fix/B-137-notion-obsidian-sync`；Vue 红灯测试已新增，尚未接前端实现
- **下一步**：任务 4：接入 Vue 资料库导入面板、API helper 和 App 刷新流程
- **续任务须知**：Vue 红灯命令：`E:\Code\knowledage_island\.venv\Scripts\python.exe -m pytest tests\test_webapp\test_frontend_vue_app.py::test_vue_import_api_helper_uses_notion_and_obsidian_contracts tests\test_webapp\test_frontend_vue_app.py::test_vue_document_import_panel_renders_notion_and_obsidian_import_controls tests\test_webapp\test_vue_app_handles_notion_and_obsidian_import_response_and_refreshes_library -q`；失败点为缺少新 helper、导入控件和 App 接线。
