# B-139 FastAPI 迁移计划

> 状态：Active
> 创建时间：2026-05-26
> 创建方：Codex
> 关联 BACKLOG：B-139
> 关联功能文档：docs/features/fastapi-runtime.md
> 关联设计文档：docs/adr/ADR-001-fastapi-migration.md, docs/design/architecture-overview.md, docs/design/api-spec.md, docs/guides/setup.md, docs/guides/testing.md

## 1. 目标

将当前 Web MVP 的 HTTP 服务层从 Python stdlib `http.server` 迁移到 FastAPI + Uvicorn。迁移完成后，现有 API 路径、请求字段、响应字段和静态前端入口保持兼容；`storage.py`、检索、导入、回答等业务层不做结构性改动；`/api/answer/stream` 使用 FastAPI `StreamingResponse` 输出现有 SSE 事件。

## 2. 前置条件

- 已读取 `AGENTS.md`、`CONTRIBUTING.md`、`docs/README.md`、`docs/BACKLOG.md`。
- 已读取 `docs/adr/ADR-001-fastapi-migration.md`，确认 B-139 不包含 B-140 认证和 B-141 Vue 前端工程化。
- 已用 Context7 查询 FastAPI 当前文档，确认 `APIRouter`、请求体、`JSONResponse` 和 Uvicorn/FastAPI 运行方式。
- 当前工作区存在大量既有未提交改动；本 plan 只追加 B-139 相关文件和后续迁移改动，不回滚既有内容。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 B-139 plan、补充运行时规格文档，并将 BACKLOG 状态更新为 `doing`
- [ ] 先写 FastAPI 服务层失败测试，覆盖健康检查、静态首页、未知 API、SSE Content-Type
- [ ] 新增 FastAPI + Uvicorn 依赖，并把 `webapp/server.py` 迁移为 FastAPI app + 兼容 dispatch 入口
- [ ] 将 `app.py` 启动入口改为 Uvicorn，并保持 `python app.py` 本地启动方式
- [ ] 同步正式文档：架构、API、setup/testing、CHANGELOG/devlog 中与 B-139 直接相关的说明
- [ ] 运行 Web MVP 与 legacy 回归验证，修复仅由 B-139 引入的回归
- [ ] 完成回流清单，删除本 plan，并将 B-139 状态改为 `done`

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `app.py` | 修改：启动 Uvicorn |
| 代码 | `webapp/server.py` | 修改：FastAPI app、静态文件、JSON API、SSE |
| 代码 | `requirements.txt` | 修改：新增 FastAPI/Uvicorn 依赖 |
| 测试 | `tests/test_webapp/test_fastapi_server.py` | 新增：服务层兼容测试 |
| 文档 | `docs/features/fastapi-runtime.md` | 新增：运行时迁移边界 |
| 文档 | `docs/features/README.md` | 修改：索引新文档 |
| 文档 | `docs/design/architecture-overview.md` | 修改：接口层技术栈更新 |
| 文档 | `docs/design/api-spec.md` | 修改：入口与 OpenAPI/SSE 说明 |
| 文档 | `docs/guides/setup.md` | 修改：启动命令与依赖说明 |
| 文档 | `docs/guides/testing.md` | 修改：B-139 验证命令 |
| 文档 | `CHANGELOG.md`, `docs/devlog/2026-05-26.md` | 修改：记录迁移实施结果 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-138 路由拆分已在当前工作区体现，B-139 直接基于当前未提交状态继续 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 desktop/UI 文档计划，可能触及 README/BACKLOG/devlog；不触及 FastAPI server 迁移核心文件 | 分区：B-139 只改 Web HTTP 运行时和对应正式文档 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 与文档计划；不触及 `webapp/server.py` / `app.py` | 分区：B-139 不修改 legacy `src/` |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划；不触及 FastAPI server 迁移核心文件 | 分区：B-139 不修改数据库 schema |

## 6. 完成标准

全部勾选后方可删除本 plan 文件：

- [ ] `python app.py` 能通过 Uvicorn 启动本地 Web 服务
- [ ] `/api/health` 返回 `{"status":"ok"}`
- [ ] `/api/answer/stream` 继续返回 `text/event-stream`，事件名保持 `token/done/answer_error`
- [ ] `webapp/static/` 在 B-141 前继续可访问
- [ ] `storage.py` 和数据库 schema 未因 B-139 修改
- [ ] 测试通过（参照 `docs/guides/testing.md` 最低要求）
- [ ] 相关文档已同步（见下方"回流清单"）
- [ ] BACKLOG 条目 `B-139` 状态已更新为 `done`

## 7. 回流清单

删除本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| FastAPI 运行时边界和非目标 | `docs/features/fastapi-runtime.md` | [ ] |
| HTTP 服务层技术栈从 stdlib 改为 FastAPI + Uvicorn | `docs/design/architecture-overview.md` | [ ] |
| 本地 Web API 入口、OpenAPI 文档和 SSE 说明 | `docs/design/api-spec.md` | [ ] |
| 安装依赖与启动方式 | `docs/guides/setup.md` | [ ] |
| B-139 验证命令 | `docs/guides/testing.md` | [ ] |
| 对外变更摘要 | `CHANGELOG.md` | [ ] |
| 实施记录 | `docs/devlog/2026-05-26.md` | [ ] |

## 8. 执行记录

- 2026-05-26 15:17：用户确认开始 B-139，并允许 plan/BACKLOG 修改与小步提交。
- 2026-05-26 15:17：冲突扫描发现 `docs/superpowers/plans/` 下存在历史计划文件，但无明确 `状态：Active/Interrupted` 头部，且核心影响范围与 B-139 不重叠；按分区处理。

## 9. 状态快照

- **最后更新**：2026-05-26 15:17
- **进度**：已完成 1 / 7 项（见 § 3 勾选状态）
- **最新 commit**：`6e9b2d7` — 当前任务开始前基线
- **代码状态**：分支 `fix/url-virtual-source-preserve`；存在大量既有未提交改动；B-139 将只追加相关变更
- **下一步**：先写 FastAPI 服务层失败测试，覆盖健康检查、静态首页、未知 API、SSE Content-Type
- **续任务须知**：B-139 不包含认证中间件和 Vue 前端工程化；不要修改 `src/` legacy 代码或数据库 schema
