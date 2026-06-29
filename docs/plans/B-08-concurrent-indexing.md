# B-08 多工作区并发索引执行计划

> 状态：Active
> 创建时间：2026-06-29
> 创建方：Codex
> 关联 BACKLOG：B-08
> 关联功能文档：docs/features/concurrent-indexing.md
> 关联设计文档：docs/design/architecture-overview.md, docs/design/api-spec.md, docs/design/import-batches-design.md

## 1. 目标

在不引入外部消息队列、不修改 SQLite schema 的前提下，为 Web MVP 导入链路补充进程内轻量并发索引：跨项目空间可并发执行，同一项目空间串行执行，既有 `/api/import*` 同步响应契约保持兼容。

## 2. 前置条件

- 已确认用户要求：执行 B-08，按推荐范围。
- 已读取 `AGENTS.md`、`docs/BACKLOG.md`、`docs/design/architecture-overview.md`、`docs/design/api-spec.md`、`docs/design/import-batches-design.md`。
- 当前分支：`fix/b-08-concurrent-index`
- 当前存在用户未提交改动：`docs/BACKLOG.md`、`docs/architecture/*`、`docs/guides/release-process.md`、`ops/README.md`、`scripts/check_docs_consistency.py`；执行中只暂存 B-08 相关变更。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 后端摄入协调器：先写失败测试，再新增项目级导入锁，保证同项目串行、跨项目不互相阻塞。
- [x] FastAPI 分发线程池：先写失败测试，再把 `/api/*` 同步业务分发移入线程池，避免导入阻塞事件循环。
- [ ] 文档与收口：同步功能/架构/API/批次设计/测试文档，运行验证，BACKLOG 置 `done`，删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `webapp/indexing.py` | 新增进程内项目级摄入协调器 |
| 代码 | `webapp/routes/imports.py` | 在导入写入入口包裹项目级串行保护 |
| 代码 | `webapp/server.py` | `/api/*` 同步分发移入线程池 |
| 代码 | `webapp/storage.py` | 增加 SQLite busy timeout，降低并发写入锁冲突风险 |
| 测试 | `tests/test_webapp/test_indexing.py` | 新增并发摄入协调器与导入路由并发测试 |
| 测试 | `tests/test_webapp/test_fastapi_server.py` | 覆盖 API 分发线程池约束 |
| 文档 | `docs/features/concurrent-indexing.md` | 新增 B-08 功能说明 |
| 文档 | `docs/features/README.md` | 补充功能文档索引 |
| 文档 | `docs/design/architecture-overview.md` | 同步单进程内轻量并发索引架构 |
| 文档 | `docs/design/api-spec.md` | 同步导入接口兼容性和并发边界 |
| 文档 | `docs/design/import-batches-design.md` | 同步批次历史与并发索引关系 |
| 文档 | `docs/guides/testing.md` | 同步导入并发相关测试要求 |
| 文档 | `docs/BACKLOG.md` | B-08 状态流转 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | N/A |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | legacy `src/desktop` UI，与 Web MVP 导入链路无重叠 | N/A |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | legacy `src/` 领域模型，与 Web MVP 导入链路无重叠 | N/A |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | legacy `src/` 数据模型，与 Web MVP 导入链路无重叠 | N/A |

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/concurrent-indexing.md` 的业务规则
- [ ] 相关单元/集成测试通过
- [ ] 全量 Web MVP 测试通过
- [ ] 相关文档已同步（见下方"回流清单"）
- [ ] BACKLOG 条目 `B-08` 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| B-08 并发索引行为、范围和非目标 | `docs/features/concurrent-indexing.md` | [ ] |
| 单进程轻量队列与导入协调器架构 | `docs/design/architecture-overview.md` | [ ] |
| `/api/import*` 兼容契约与并发边界 | `docs/design/api-spec.md` | [ ] |
| 导入批次历史与并发任务关系 | `docs/design/import-batches-design.md` | [ ] |
| 并发索引测试要求 | `docs/guides/testing.md` | [ ] |
| 功能文档索引 | `docs/features/README.md` | [ ] |

## 8. 执行记录

- 2026-06-29：用户确认执行推荐范围；第一片不改 SQLite schema，不新增持久化 job 表。
- 2026-06-29：当前存在用户未提交文档改动，提交时需只暂存 B-08 相关变更。

## 9. 状态快照

- **最后更新**：2026-06-29 00:00
- **进度**：已完成 2 / 3 项（见 § 3 勾选状态）
- **最新 commit**：`PENDING` — feat: 将同步 API 分发移入线程池
- **代码状态**：`fix/b-08-concurrent-index`；存在用户未提交改动；FastAPI 线程池分发已完成待提交
- **下一步**：文档与收口：同步功能/架构/API/批次设计/测试文档，运行验证，BACKLOG 置 `done`，删除本 plan。
- **续任务须知**：提交时避免暂存非 B-08 既有改动；不要把既有 docs/architecture、ops、release-process、check_docs_consistency 改动混入提交。
