# B-06 ops maintenance scripts

> 状态：Active
> 创建时间：2026-06-29
> 创建方：Codex
> 关联 BACKLOG：B-06
> 关联功能文档：docs/features/ops-maintenance.md
> 关联设计文档：docs/design/api-spec.md, docs/design/architecture-overview.md

## 1. 目标

补齐本地运维维护脚本与其依赖的后端维护入口。完成后，仓库应提供可执行的数据库备份、runtime 清理和一键索引重建脚本；`POST /api/admin/rebuild-index` 能基于 SQLite 已存文档重新生成 chunk 与向量索引，不引入数据库 schema 变更。

## 2. 前置条件

- 已读取 `AGENTS.md`、`docs/BACKLOG.md`、`ops/README.md`。
- 已确认 `ops/scripts/` 当前不存在。
- 已确认 `POST /api/admin/rebuild-index` 当前不存在。
- 当前工作区存在用户未提交改动，执行时只处理 B-06 相关路径并避免 staging 无关改动。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建本 plan、关联 B-06，并新增 ops 维护功能文档占位
- [x] 以 TDD 补齐 `POST /api/admin/rebuild-index` 管理端点与索引重建逻辑
- [ ] 以 TDD 补齐 `ops/scripts/backup_db.sh`、`cleanup_runtime.sh`、`rebuild_index.sh`
- [ ] 同步 `ops/README.md`、API/架构/OpenAPI 文档并完成 B-06 收尾

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `webapp/routes/` | 新增 admin 路由分支并接入分发 |
| 代码 | `webapp/storage.py` | 暴露维护用索引重建能力，不改 schema |
| 代码 | `webapp/openapi_schema.py` | 新增 admin rebuild-index operation |
| 脚本 | `ops/scripts/*.sh` | 新增维护脚本 |
| 测试 | `tests/test_webapp/` | 新增/更新 admin endpoint 与 ops scripts 测试 |
| 文档 | `docs/features/ops-maintenance.md` | 新增功能文档 |
| 文档 | `ops/README.md` | 将规划脚本更新为已实现用法 |
| 文档 | `docs/design/api-spec.md` | 记录新增 admin API |
| 文档 | `docs/design/architecture-overview.md` | 记录维护入口架构落点 |
| 文档 | `docs/BACKLOG.md` | B-06 状态与完成说明 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | N/A |

### 5.2 与现有 plan 的重叠

创建本 plan 时扫描 `docs/plans/` 与 `docs/superpowers/plans/`：`docs/plans/` 只有模板和 README；`docs/superpowers/plans/` 中历史 plan 面向已归档桌面阶段模型/UI，不覆盖 `ops/`、当前 FastAPI admin 路由或 Web MVP 索引维护。本任务无未完成冲突。

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

## 6. 完成标准

全部勾选后方可删除本 plan 文件：

- [ ] 功能行为符合 `docs/features/ops-maintenance.md` 的规则
- [ ] 测试通过（参照 `docs/guides/testing.md` 最低要求）
- [ ] 相关文档已同步（见下方"回流清单"）
- [ ] BACKLOG 条目 `B-06` 状态已更新为 `done`

## 7. 回流清单

删除本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 三个 ops 脚本用途、参数和限制 | `ops/README.md` | [ ] |
| ops 维护能力边界 | `docs/features/ops-maintenance.md` | [ ] |
| `POST /api/admin/rebuild-index` 契约 | `docs/design/api-spec.md` | [ ] |
| admin 路由与索引维护架构落点 | `docs/design/architecture-overview.md` | [ ] |
| OpenAPI operation | `webapp/openapi_schema.py` | [ ] |

若产生了重大技术决策，必须在删除 plan 前新建对应 ADR。

## 8. 执行记录

- 2026-06-29：当前任务不修改 SQLite schema；索引重建基于 SQLite 已存文档内容，不重新扫描文件系统。
- 2026-06-29：当前任务不新增 Agent 工具，不改变只读工具白名单。

## 9. 状态快照

- **最后更新**：2026-06-29 00:00
- **进度**：已完成 2 / 4 项（见 § 3 勾选状态）
- **最新 commit**：待提交 — feat: 增加索引重建管理端点
- **代码状态**：`fix/b-08-concurrent-index`；存在用户未提交改动；admin rebuild-index 代码和测试已完成
- **下一步**：以 TDD 补齐 `ops/scripts/backup_db.sh`、`cleanup_runtime.sh`、`rebuild_index.sh`
- **续任务须知**：工作区已有用户改动，提交时必须精确 staging。
