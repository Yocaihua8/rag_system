# B-133 GitHub Repo Import Plan

> 状态：Active
> 创建时间：2026-06-28
> 创建方：Codex
> 关联 BACKLOG：B-133
> 关联功能文档：docs/features/github-repo-import.md
> 关联设计文档：docs/design/api-spec.md；docs/design/new-architecture-design.md §5.7（用户指定，但当前分支未跟踪该文件，执行中不新增整份设计文档）

## 1. 目标

执行 B-133：新增 GitHub 仓库整体导入能力，使用户可以通过 GitHub clone URL 一键创建知识库项目，并复用现有目录导入链路摄入仓库中的 Markdown、代码和其他已支持文件类型。

## 2. 前置条件

- 已阅读用户提供的项目级 `AGENTS.md` 规则。
- 已阅读 `docs/BACKLOG.md`。
- 已阅读 `docs/features/github-repo-import.md`。
- 已阅读 `docs/requirements/functional-modules.md` 与 `docs/design/api-spec.md` 中现有导入接口描述。
- 已确认当前分支缺少用户指定的 `docs/design/new-architecture-design.md §5.7`，本任务不从其他工作区复制或新建该大型设计文档。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 任务 1：写 B-133 后端红灯测试，覆盖 GitHub URL 校验、clone runner 注入、API 响应和导入批次记录
- [x] 任务 2：实现 GitHub 仓库 clone + 目录导入后端能力，不修改数据库 schema、不接入 GitHub API
- [x] 任务 3：写 Vue 前端红灯测试，覆盖 API helper、导入面板表单和 App 事件串联
- [x] 任务 4：实现 Vue 资料库 GitHub 导入入口，成功后刷新并选中新建项目
- [x] 任务 5：同步正式文档并运行 B-133 相关验证清单
- [ ] 任务 6：关闭 B-133：BACKLOG 置 done、删除本 plan、提交最终收口

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|-------------|----------|
| 代码 | `webapp/github_import.py` | 新增 GitHub 仓库导入服务 |
| 代码 | `webapp/routes/imports.py` | 新增 `/api/import/github-repo` 路由 |
| 代码 | `frontend/src/api/imports.js` | 新增 GitHub 导入 API helper |
| 代码 | `frontend/src/components/DocumentImportPanel.vue` | 新增 GitHub 仓库导入表单 |
| 代码 | `frontend/src/views/LibraryView.vue` | 转发 GitHub 导入事件 |
| 代码 | `frontend/src/App.vue` | 调用导入 API 并刷新资料库状态 |
| 测试 | `tests/test_webapp/test_api.py` | 新增后端 API/服务测试 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 新增前端静态契约测试 |
| 文档 | `docs/features/github-repo-import.md` | 新增并补齐功能文档 |
| 文档 | `docs/features/README.md` | 补充功能文档索引 |
| 文档 | `docs/requirements/functional-modules.md` | 补充知识导入模块能力 |
| 文档 | `docs/design/api-spec.md` | 补充 GitHub 仓库导入 API 契约 |
| 文档 | `docs/BACKLOG.md` | B-133 状态流转与 plan 路径 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|----------|
| N/A | B-133 可基于现有目录导入链路独立实现 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|----------|
| `docs/plans/B-145-tauri-windows-packaging.md` | 同改 `docs/BACKLOG.md`；B-145 影响 `src-tauri/`、sidecar、桌面打包文档，不改导入 API 或 Vue 资料库导入表单 | 分区：B-133 只改导入链路与资料库入口，不触碰 `src-tauri/`、sidecar 脚本或 B-145 plan |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/github-repo-import.md` 的业务规则
- [ ] GitHub 导入后端测试通过
- [ ] Vue 资料库导入入口测试通过
- [ ] 不修改数据库 schema，不保存 GitHub 凭据，不触碰 `src/` legacy
- [x] 相关文档已同步（见下方"回流清单"）
- [ ] BACKLOG 条目 B-133 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| GitHub 仓库导入功能边界、非目标和页面入口 | `docs/features/github-repo-import.md` | [x] |
| 功能文档索引 | `docs/features/README.md` | [x] |
| 知识导入模块新增 GitHub 仓库来源 | `docs/requirements/functional-modules.md` | [x] |
| `/api/import/github-repo` 请求、响应和错误 | `docs/design/api-spec.md` | [x] |
| B-133 状态流转 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-06-28：创建 plan。用户指定参考 `docs/design/new-architecture-design.md §5.7`，但当前隔离 worktree 中该文件不存在；为避免混入其他工作区未跟踪的大型设计文档，本任务只同步已跟踪的 `docs/design/api-spec.md`、`docs/requirements/functional-modules.md` 和新功能文档。
- 2026-06-28：冲突扫描发现 B-145 plan 仍为 Interrupted，但其影响范围是 Tauri/sidecar 打包链路，与 B-133 导入 API 和资料库入口无代码重叠；采用分区策略。
- 2026-06-28：任务 1 红灯测试已运行：`& 'E:\Code\knowledage_island\.venv\Scripts\python.exe' -m pytest tests\test_webapp\test_api.py -q -k "github_repo_import"`，结果 3 failed，失败点符合预期：缺少 `webapp.github_import`，且 `/api/import/github-repo` 仍返回 404。
- 2026-06-28：任务 2 新增 `webapp/github_import.py` 和 `/api/import/github-repo`；使用受控 `runtime/webapp/github-repos` clone 目录、固定 `git clone` 参数列表和可注入 clone runner。复跑 `& 'E:\Code\knowledage_island\.venv\Scripts\python.exe' -m pytest tests\test_webapp\test_api.py -q -k "github_repo_import"` 结果 3 passed；复跑 `& 'E:\Code\knowledage_island\.venv\Scripts\python.exe' -m pytest tests\test_webapp\test_api.py tests\test_webapp\test_api_route_split.py -q` 结果 111 passed。
- 2026-06-28：任务 3 红灯测试已运行：`& 'E:\Code\knowledage_island\.venv\Scripts\python.exe' -m pytest tests\test_webapp\test_frontend_vue_app.py -q -k "github_repo"`，结果 3 failed，失败点符合预期：Vue API helper、DocumentImportPanel 和 App 事件链均未接入 GitHub 仓库导入。
- 2026-06-28：任务 4 新增 Vue GitHub 导入 helper、资料库导入表单、LibraryView 事件透传和 App 处理器。复跑 `& 'E:\Code\knowledage_island\.venv\Scripts\python.exe' -m pytest tests\test_webapp\test_frontend_vue_app.py -q -k "github_repo"` 结果 3 passed；复跑 `& 'E:\Code\knowledage_island\.venv\Scripts\python.exe' -m pytest tests\test_webapp\test_frontend_vue_app.py -q` 结果 78 passed；`npm install` 后 `npm run build` 通过。npm audit 报告现有依赖树 2 个风险（1 low, 1 high），未在本任务处理。
- 2026-06-28：任务 5 同步 `docs/requirements/functional-modules.md`、`docs/design/api-spec.md` 和 `docs/features/github-repo-import.md`。验证结果：`& 'E:\Code\knowledage_island\.venv\Scripts\python.exe' -m pytest tests\test_webapp -q` 为 315 passed；`npm run build` 通过。

## 9. 状态快照

- **最后更新**：2026-06-28 01:25
- **进度**：已完成 5 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`b5e4cf6` — docs: 同步 GitHub 仓库导入契约
- **代码状态**：`fix/B-133-github-repo-import` 分支；代码、测试和正式文档均已完成，待关闭 BACKLOG 并删除 plan
- **下一步**：任务 6：关闭 B-133：BACKLOG 置 done、删除本 plan、提交最终收口
- **续任务须知**：使用隔离 worktree `C:\Users\Lenovo\.config\superpowers\worktrees\knowledage_island\fix-B-133-github-repo-import`；不要修改原始 checkout 的未提交改动。
