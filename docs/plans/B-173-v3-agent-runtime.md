# B-173 v3 Agent 数据、API 与持久执行器

> 状态：Active
> 创建时间：2026-08-02
> 创建方：Codex
> 关联 BACKLOG：B-173
> 关联功能文档：`../features/agent-tasks-and-runs.md`
> 关联设计文档：`../design/agent-runtime-and-tool-contract.md`、`../design/api-spec.md`、`../design/database-design.md`

## 1. 目标

在保持 v2 API/Vue 可运行的前提下，建立物理和语义隔离的 v3 后端：独立 SQLite 代际、可迁移 Schema、项目/任务/运行资源 API、持久执行器、可重放事件、审批与产物基础。首个真实闭环为“创建项目 → 创建任务 → 启动项目检查运行 → 持久执行 → SSE 回放 → 生成内部产物”。

## 2. 前置条件

- B-172 已关闭，ADR-012 至 ADR-015、runtime 合同和 v3 迁移指南已生效。
- 当前分支为 `refactor/agent-v3`，B-173 创建前工作区干净。
- 当前 Python venv 为 3.11.9；实现保持 3.11 可测试，正式目标和依赖声明为 Python 3.12。
- 当前环境已有 FastAPI 0.135.3、Pydantic 2.12.5、SQLAlchemy 2.0.49、AnyIO 4.13.0；Alembic 尚未安装。
- 已通过 Context7 复核 SQLAlchemy 2 Core 的显式事务、SQLite connect event 和自定义 BEGIN 方式。

## 3. 任务拆解

- [x] 增加明确后端依赖、v3 配置、SQLAlchemy Schema 与 Alembic 初始迁移，并实现 generation fail-closed。
- [x] 实现 v3 Store、领域状态、幂等项目/任务/运行/事件/审批/产物持久化。
- [x] 实现 lifespan executor、类型化 `project.inspect` 只读节点、并发/租约/恢复和 SSE 续传。
- [x] 暴露 `/api/v3` 项目、任务、运行控制、事件、审批、产物和工作流基础接口及真实 OpenAPI。
- [ ] 补齐后端/集成/仓库测试，校准 API/数据库/权限文档、DevLog 与 CHANGELOG。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|-------------|----------|
| 代码 | `backend/config/`、`backend/storage/v3/` | 新增独立配置、Schema、Alembic 与 Store |
| 代码 | `backend/domain/`、`backend/application/`、`backend/runtime/` | 新增状态、用例与持久执行器 |
| 代码 | `backend/api/v3/`、`backend/api/server.py` | 新增 v3 sub-app 并由主 lifespan 管理；v2 catch-all 保留 |
| 测试 | `tests/backend/`、`tests/integration/`、`tests/repository/` | 新增 v3 数据、执行、API、SSE 和依赖契约 |
| 文档 | API、数据库、权限、状态、测试、DevLog、CHANGELOG | 只写实际实现和兼容边界 |
| 前端 | `frontend/` | 不修改；P2 门禁继续有效 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-172 已完成并删除；所需决策已回流正式文档。 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围 | 解决方式 |
|-----------|----------|----------|
| N/A | N/A | 创建时无其他 Active/Interrupted plan。 |

## 6. 完成标准

- [x] v3 只打开 `data_generation=v3` 数据库，拒绝未标记/v2/未知代际且不修改原文件。
- [x] API 创建的任务由数据库队列和 lifespan executor 完成，不由 HTTP 或 SSE 连接直接执行。
- [x] 全局并发、租约、幂等、读取重试、恢复和事件游标测试通过。
- [x] 写动作拥有审批快照基础，不会在恢复时自动重放。
- [x] v2 API 测试继续通过，Vue 源码无变化。
- [ ] 文档与实际 OpenAPI/Schema 同步，完成事实进入 CHANGELOG 和 Git。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 实际 API 与 envelope | `../design/api-spec.md`、`../design/api-changes.md` | [ ] |
| v3 Schema、迁移和代际 | `../design/database-design.md` | [ ] |
| 执行、状态、审批和工具 | `../design/agent-runtime-and-tool-contract.md`、`../design/permission-matrix.md` | [ ] |
| 测试和运行命令 | `../guides/testing.md`、`../guides/runbook.md` | [ ] |
| 过程与完成事实 | `../devlog/2026/08/2026-08-02.md`、`../../CHANGELOG.md` | [ ] |

## 8. 执行记录

- 2026-08-02：决定 v3 不复用 `KnowledgeStore`，避免构造时写入 v2 标记和旧表。
- 2026-08-02：过渡期由主 FastAPI lifespan 管理 v3 executor，v2 路由继续保留；最终切换另行删除兼容实现。
- 2026-08-02：同项目 `project_write` / `external_write` 在 `BEGIN IMMEDIATE` 认领事务中串行；运行写步骤或 `recovery_required` 不确定写步骤都会保持写槽，读取任务和其他项目不受阻塞。
- 2026-08-02：Python 3.11 当前环境全量后端、集成和仓库验证为 653 项通过；Python 3.12 仍是后续独立验证边界。

## 9. 状态快照

- **最后更新**：2026-08-02 14:11 +08:00
- **进度**：已完成 4 / 5 项
- **最新 commit**：`c17cc91` — chore: 关闭 B-172 工程治理任务
- **代码状态**：v3 数据、Store、executor、API 和专项测试已完成，等待聚焦提交；Vue 未修改
- **下一步**：提交后端实现，再完成正式文档回流、门禁和 B-173 关闭
- **续任务须知**：只允许写 `runtime/v3` 或测试临时目录；不得删除 v2 DB，最终删除前必须重新只读校验
