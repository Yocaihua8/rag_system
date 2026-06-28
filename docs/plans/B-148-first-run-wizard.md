# B-148 First-Run Wizard Plan

> 状态：Active
> 创建时间：2026-06-28
> 创建方：Codex
> 关联 BACKLOG：B-148
> 关联功能文档：docs/features/first-run-wizard.md
> 关联设计文档：docs/design/new-architecture-design.md §23.6, docs/design/api-spec.md

## 1. 目标

执行 B-148：新增 First-Run Wizard 的 Ollama 检测、模型拉取进度接口和前端向导入口，让 Tauri/Web 首次使用能引导用户完成本地模型准备和第一个知识库创建。

## 2. 前置条件

- 已阅读 `AGENTS.md`
- 已阅读 `docs/BACKLOG.md`
- 已阅读 `docs/design/new-architecture-design.md §23.6`
- 已确认 B-145 当前因缺 Rust/Cargo 阻塞，本任务与其分区执行
- 已通过 ctx7 查询 Ollama 官方 API：`GET /api/tags` 返回本地模型；`POST /api/pull` 流式返回 JSON 行进度

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 任务 1：写 B-148 后端红灯测试，覆盖 `GET /api/ollama/status`、`POST /api/ollama/pull` SSE 和无效模型拒绝
- [x] 任务 2：实现后端 Ollama 状态与拉取流，新增最小白名单推荐模型，不修改数据库 schema
- [x] 任务 3：写前端 API/helper 红灯测试并新增 `frontend/src/api/ollama.js`
- [x] 任务 4：接入 First-Run Wizard 前端入口，展示 Ollama 状态、模型拉取进度和创建知识库引导
- [x] 任务 5：同步 API、功能、setup/testing 文档和 BACKLOG 状态
- [ ] 任务 6：运行 B-148 验证清单，关闭 BACKLOG 状态并删除本 plan

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|-------------|----------|
| 代码 | `webapp/routes/ollama.py` | 新增 Ollama 状态/拉取路由逻辑 |
| 代码 | `webapp/routes/__init__.py` | 接入 Ollama JSON 路由 |
| 代码 | `webapp/server.py` | 新增 `/api/ollama/pull` SSE route |
| 代码 | `backend/providers/llm/ollama.py` | 复用或补充 Ollama HTTP helper |
| 前端 | `frontend/src/api/ollama.js` | 新增 Ollama Wizard API helper |
| 前端 | `frontend/src/` | 后续接入 First-Run Wizard UI；当前工作区已有前端脏改动，修改前需逐文件确认 |
| 测试 | `tests/test_webapp/test_ollama_wizard.py` | 新增后端接口测试 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | 后续补前端源码约束 |
| 文档 | `docs/features/first-run-wizard.md` | 新增功能文档 |
| 文档 | `docs/design/api-spec.md` | 新增接口契约 |
| 文档 | `docs/guides/setup.md`、`docs/guides/testing.md` | 补充使用/验证说明 |
| 文档 | `docs/BACKLOG.md` | B-148 状态流转与 plan 路径 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|----------|
| `docs/plans/B-145-tauri-windows-packaging.md` | B-145 被 Rust/Cargo 工具链阻塞；B-148 不依赖 installer 生成，可在 Web/Tauri 共用 API 层继续推进 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|----------|
| `docs/plans/B-145-tauri-windows-packaging.md` | 同属 Tauri 线，可能共同更新 BACKLOG 和 new architecture 文档；代码范围分别为 `src-tauri/scripts` 与 Ollama/API/Wizard | 分区：B-145 继续只处理打包工具链；B-148 只处理 First-Run Wizard |
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 旧 UI 计划，不涉及 Ollama Wizard 现行文件 | N/A |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 旧知识点计划，不涉及 Ollama Wizard | N/A |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 旧核心模型计划，不涉及 Ollama Wizard | N/A |

## 6. 完成标准

- [ ] `GET /api/ollama/status` 返回可用状态、本地模型和推荐模型
- [ ] `POST /api/ollama/pull` 以 SSE 返回 progress/done/error 事件
- [ ] 未安装或不可达 Ollama 不导致 Web MVP 启动失败
- [ ] 前端 Wizard 可显示检测结果、拉取进度，并引导创建第一个知识库
- [ ] 相关测试通过
- [ ] 相关文档已同步
- [ ] BACKLOG 条目 B-148 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| First-Run Wizard 范围与流程 | `docs/features/first-run-wizard.md` | [x] |
| `GET /api/ollama/status` 与 `POST /api/ollama/pull` 契约 | `docs/design/api-spec.md` | [x] |
| 本地 Ollama 首次配置说明 | `docs/guides/setup.md` | [x] |
| B-148 测试命令 | `docs/guides/testing.md` | [x] |
| §23.6 实际接口与前端入口 | `docs/design/new-architecture-design.md` | [ ] 未提交：该文件当前为 122KB 未跟踪整文件，避免在 B-148 吸收非本任务内容 |

## 8. 执行记录

- 2026-06-28：创建 plan。当前工作区存在多处前端未提交改动，B-148 前端任务必须逐文件读取后再编辑；后端任务先行以降低冲突。
- 2026-06-28：任务 1 红灯测试已运行：`.venv\Scripts\python.exe -m pytest tests\test_webapp\test_ollama_wizard.py -q`，结果 4 failed；失败点符合预期，均为 `/api/ollama/status`、`/api/ollama/pull` 尚未实现而返回 404。
- 2026-06-28：任务 2 后端实现已完成；`.venv\Scripts\python.exe -m pytest tests\test_webapp\test_ollama_wizard.py -q` 通过 4 项，`.venv\Scripts\python.exe -m pytest tests\test_backend\test_ollama_llm.py -q` 通过 5 项。
- 2026-06-28：任务 3 前端 helper 红灯测试已先失败于 `frontend/src/api/ollama.js` 缺失；新增 helper 后，`.venv\Scripts\python.exe -m pytest tests\test_webapp\test_frontend_ollama_api.py tests\test_webapp\test_ollama_wizard.py -q` 通过 5 项。
- 2026-06-28：任务 4 Wizard UI 红灯测试已先失败于组件和接入缺失；新增 `FirstRunWizard`、App 状态/事件和 Workbench 入口后，`.venv\Scripts\python.exe -m pytest tests\test_webapp\test_frontend_first_run_wizard.py tests\test_webapp\test_frontend_ollama_api.py tests\test_webapp\test_ollama_wizard.py -q` 通过 8 项，`npm run build` 通过。
- 2026-06-28：任务 5 已同步 `docs/features/first-run-wizard.md`、`docs/design/api-spec.md`、`docs/guides/setup.md`、`docs/guides/testing.md`；`docs/design/new-architecture-design.md` 当前为未跟踪整文件，未纳入本次提交以避免吸收非 B-148 内容。

## 9. 状态快照

- **最后更新**：2026-06-28 16:05
- **进度**：已完成 4 / 6 项（见 § 3 勾选状态）
- **最新 commit**：53a2a1a
- **代码状态**：`main` 分支；工作区已有与 B-148 无关或待确认的未提交改动
- **下一步**：任务 5：同步 API、功能、setup/testing 文档和 BACKLOG 状态
- **续任务须知**：不要修改数据库 schema；不要扩大 Agent 工具权限；前端文件当前较脏，先从后端可测接口开始
