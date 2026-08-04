# AGENTS.md

> 本文件为 AI 编码助手提供项目级操作上下文；人工贡献规范见 `CONTRIBUTING.md`。

## 1. 项目概述

Knowledge Island 当前正式版本为 `v2.0.0` 本地项目知识教练，并已进入 v3 通用项目 Agent 的分阶段重构。目标规格不等于当前可达实现；阶段事实以源码、测试、CHANGELOG 和当日 DevLog 为准。

| 项 | 当前值 |
|----|--------|
| 类型 | Web 全栈：FastAPI 后端 + Vue 3/Vite 前端 + Tauri 2 桌面壳 |
| 后端入口 | `python -m backend`，默认 `127.0.0.1:8765` |
| 前端入口 | `npm run frontend:dev`，默认 `127.0.0.1:5173` |
| 数据 | SQLite；默认 `runtime/v2/app.db` |
| 文档入口 | `docs/README.md` |

## 2. 工作前检查

开始任务前必须读取与任务相关的规则、文档、源码、测试和 Git 状态。若更深目录存在 `AGENTS.md` 或 `AGENTS.override.md`，以更具体规则为准。发现文档冲突时先指出，不擅自采用方便的一方。

不要把其他项目的业务、命名、目录、测试命令或发布假设带入本仓库。

除非用户明确要求直接执行，默认先给出：已读规则、任务理解、影响范围、最小方案、风险和待确认问题；确认后再修改。

## 3. 目录与职责

| 路径 | 职责 |
|------|------|
| `backend/` | Python 入口、依赖、API、routes、domain、storage、config、providers、后端镜像 |
| `frontend/` | Vue/Vite/Vitest/Playwright、`dist/`、Nginx、前端镜像 |
| `src-tauri/` | Tauri npm 工具、Rust 壳、sidecar 构建脚本 |
| `integrations/obsidian-plugin/` | 独立 desktop-only Obsidian 插件 |
| `ops/docker/` | Compose、环境样例、启停脚本 |
| `scripts/` | 文档链接、占位符、一致性和源码事实检查 |
| `tests/backend/` | 后端/provider 单元测试 |
| `tests/integration/` | API、SSE 与跨层集成测试 |
| `tests/repository/` | 仓库结构、构建、Docker、Tauri 与文档契约 |
| `tests/e2e/` | Playwright 浏览器流程与测试服务 |
| `docs/requirements/` | 产品背景、边界、用例和维护版本范围 |
| `docs/design/` | 完整系统、API、数据、权限、状态和 UI 契约 |
| `docs/features/` | 逐项用户能力规格 |
| `docs/adr/` | Accepted 架构决策与模板 |
| `docs/guides/` | 搭建、测试、运行、发布、安全和协作操作 |
| `docs/plans/` | Active/Interrupted plan 与模板；活动 plan 完成即删除 |
| `docs/devlog/` | 按开发日记录过程事实；使用 `YYYY/MM/YYYY-MM-DD.md` |

## 4. 架构不变量

- FastAPI 只提供 API、SSE 和接口文档；不托管 `frontend/dist/`，`GET /` 返回 404。
- Vue 统一通过 `VITE_API_BASE_URL` 构造绝对 `fetch` / `EventSource` URL；不在前端实现业务规则。
- CORS 使用精确 Origin allowlist；禁止通配符和 cookie credentials。
- `backend/api/` 与 `backend/routes/` 只做 HTTP 适配、校验和用例编排，不直接操作 SQLite。
- `backend/storage/` 是 SQLite 唯一读写入口，不承载页面规则或 HTTP 对象。
- Agent 工具只允许 `backend/domain/agent_tools.py` 中的只读白名单；禁止 shell 和写操作。
- Model Profile/SQLite 只保存 `env:*` / `saved:*` Key 引用，接口不得返回明文 Key；兼容全局 LLM 设置会把用户输入 Key 写入用户 appdata `.env`，修改该边界必须同步安全文档。
- Tauri 不复制业务逻辑；Obsidian 插件不能绕过用户确认或冲突校验。
- 默认 v2 数据根为 `runtime/v2/`；不得自动覆盖或迁移旧代际数据。

HTTP 方法、字段、响应结构、SQLite Schema 或 Agent 权限发生变化时，必须把兼容性和迁移边界写清；未获任务授权不得修改。

## 5. 开发命令

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements/dev.txt
npm ci
Copy-Item backend/.env.example backend/.env

.\.venv\Scripts\python.exe -m backend
npm run frontend:dev
```

根 npm workspace 只包含 `frontend` 和 `src-tauri`；Obsidian 插件独立安装和验证。

## 6. 测试与验证

| 类型 | 命令 |
|------|------|
| 后端/集成/仓库 | `.\.venv\Scripts\python.exe -m pytest tests/backend tests/integration tests/repository -q` |
| Vue 单测 | `npm run frontend:test` |
| Vue 构建 | `npm run frontend:build` |
| 浏览器 E2E | `npm run frontend:e2e` |
| Tauri Rust | `cargo check --manifest-path src-tauri/Cargo.toml` |
| Windows bundle | `npm run desktop:build:windows` |
| Obsidian 插件 | 在插件目录串行执行 `npm test`、`npm run typecheck`、`npm run build` |
| 文档 | 见 `docs/README.md § 6` |

代码行为变化时新增或更新相关测试。无法运行时必须说明计划命令、实际原因、关键报错和本地验证方式；未运行不得声称通过。

## 7. 文档联动

| 变化 | 同步文档 |
|------|----------|
| 产品范围、角色、版本边界 | `docs/requirements/` |
| 功能行为 | `docs/features/` |
| API | `docs/design/api-spec.md`；破坏性变化同步 `docs/design/api-changes.md` |
| 数据库 | `docs/design/database-design.md` |
| 页面/组件/跨模块边界 | `docs/design/`；必要时新增 ADR |
| 桌面/插件/GitHub | 对应功能规格及按操作目的归类的 `docs/guides/` |
| 启动、测试、Docker、发布、安全 | `docs/guides/` |
| 未完成事项 | `docs/BACKLOG.md` |
| 已完成变更 | `CHANGELOG.md` 与 Git 历史 |

每个实际开发日更新 `docs/devlog/YYYY/MM/YYYY-MM-DD.md`；DevLog 只记录过程、问题、临时决定和下一步，重大决定提升为 ADR，未完成事项进入 BACKLOG，用户可见完成事实进入 CHANGELOG。继续禁止 readiness 快照、已验收 preview 和完成 plan 归档。没有依据的事实写 `TBD`、`N/A` 或“待确认”。

## 8. Plan 与 BACKLOG

凡涉及代码或跨文件行为变更，先执行：

1. 在 `docs/BACKLOG.md` 查找匹配 `B-xxx`；没有则分配下一个 ID，状态设为 `doing`。
2. 扫描 `docs/plans/` 中状态为 `Active` 或 `Interrupted` 的 plan，比较影响范围；冲突时告知用户并确认等待、合并、覆盖或分区策略。
3. 以 `docs/plans/plan-template.md` 创建 `docs/plans/{B-ID}-{slug}.md`，填写关联文档、影响范围、冲突结论和回流清单。
4. 把 plan 路径写回 BACKLOG。

每完成 plan 中一项：勾选任务、提交该阶段、更新状态快照和当日 DevLog。中断时保留 plan 并记录下一步。完成时确认文档回流、记录 CHANGELOG、移除完成的 BACKLOG 行并删除 plan。

`docs/BACKLOG.md` 只保存未完成事项；完成历史只查 CHANGELOG 和 Git。

## 9. 修改边界

- 只修改任务直接相关文件，保持现有命名和风格，不做无关重构。
- 不用 mock 或假数据替代真实功能；不把后端业务逻辑写死在前端。
- 不引入大型依赖、不改变数据库 Schema、不删除或重命名公共 API，除非任务明确授权。
- 不提交 Key、密码、Token、用户 `.env` 或真实项目数据。
- 修改前检查工作区；发现不明的已有改动时不得覆盖。
- 删除历史/归档、生产数据、公共接口或其他难恢复内容前，必须取得用户对准确范围的明确授权并验证目标路径。
- 禁止向主分支直接推送；外部发布、合并和发布动作必须在授权范围内。

## 10. 完成输出

执行类任务最终说明：

1. 修改内容；
2. 修改文件（可按目录分组）；
3. 实际运行的验证和结果；
4. 文档同步情况；
5. 与本次任务直接相关的风险和后续建议。

只报告实际完成和实际验证的内容。
