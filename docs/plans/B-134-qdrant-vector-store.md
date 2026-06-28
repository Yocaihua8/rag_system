# B-134 Qdrant 替换 SQLite 向量存储

> 状态：Active
> 创建时间：2026-06-28
> 创建方：Codex
> 关联 BACKLOG：B-134
> 关联功能文档：docs/features/qdrant-vector-store.md
> 关联设计文档：docs/design/architecture-overview.md, docs/design/database-design.md, docs/design/api-spec.md, docs/adr/ADR-007-qdrant-vector-store.md

## 1. 目标

将 Web MVP 当前基于 SQLite `chunk_vectors` 的查询时全量向量扫描，替换为 Qdrant 本地模式向量索引检索。完成后：

- 默认行为保持兼容；Qdrant 未启用或不可用时不阻断启动，并回退到现有 SQLite 向量扫描。
- 启用 Qdrant 时，`/api/search` 不再为了向量相似度遍历 `chunk_vectors` 全表，而是通过向量存储 provider 返回候选 chunk。
- 文档摄入、更新和删除能同步维护 Qdrant 中的 chunk 向量。
- `/api/search` 现有响应字段保持兼容，`vector_provider`、`vector_model`、`rerank_score` 等字段不回退。

## 2. 前置条件

- 已阅读 `AGENTS.md`。
- 已阅读 `docs/README.md`、`docs/guides/testing.md`、`docs/design/architecture-overview.md`、`docs/design/database-design.md`、`docs/design/api-spec.md`。
- 已用 Context7 查询 Qdrant Python client 文档，确认本地模式使用 `QdrantClient(path=...)`，通过 collection + `upsert` + `query_points` 实现本地 HNSW 检索。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。
未完成项不得删除。

- [x] 任务 1：写 B-134 红灯测试，覆盖启用向量存储 provider 时搜索不调用 SQLite `list_chunk_vector_records()` 全量扫描，并保持 hybrid ranking 与 SearchHit 字段兼容。
- [x] 任务 2：实现向量存储抽象与 `webapp/search.py` 集成；默认仍走 SQLite fallback，显式传入 provider 时使用 provider 候选。
- [ ] 任务 3：写 Qdrant provider 红灯测试，覆盖本地 collection 创建、upsert、query、软依赖缺失降级和向量维度转换。
- [ ] 任务 4：实现 `backend/providers/vector_store/` Qdrant 本地 provider、配置读取和依赖声明。
- [ ] 任务 5：写 storage 同步红灯测试，覆盖文档摄入/更新/删除时向量 provider 的 upsert/delete 调用，以及 provider 异常时不破坏 SQLite 写入。
- [ ] 任务 6：实现 `webapp/storage.py` 与 Qdrant provider 同步逻辑，保留 SQLite `chunk_vectors` 兼容数据和恢复路径。
- [ ] 任务 7：同步功能文档、设计文档、API/DB 说明和 ADR；运行相关验证；关闭 BACKLOG 并删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `backend/providers/base.py` | 追加 BaseVectorStore 抽象 |
| 代码 | `backend/providers/vector_store/` | 新增 Qdrant 本地 provider |
| 代码 | `webapp/search.py` | 接入向量 provider 候选检索，保留 SQLite fallback |
| 代码 | `webapp/storage.py` | 文档 chunk 向量写入/删除时同步 provider |
| 代码 | `webapp/server.py` | 仅在需要暴露 search debug 状态时做最小字段对齐；不改非静态/API 业务逻辑 |
| 代码 | `requirements.txt` | 新增 Qdrant Python client 依赖或软依赖说明 |
| 测试 | `tests/test_webapp/` | 新增/更新搜索与摄入相关测试 |
| 文档 | `docs/features/qdrant-vector-store.md` | 新增/更新正式功能说明 |
| 文档 | `docs/design/architecture-overview.md` | 更新向量存储状态和架构说明 |
| 文档 | `docs/design/database-design.md` | 说明 SQLite `chunk_vectors` 的兼容/回退角色 |
| 文档 | `docs/design/api-spec.md` | 同步 search/debug 返回字段或降级行为 |
| 文档 | `docs/adr/ADR-007-qdrant-vector-store.md`、`docs/adr/README.md` | 新增并索引 Qdrant 替换决策 |
| 文档 | `docs/BACKLOG.md` | B-134 状态流转 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-134 可在当前 worktree 独立执行；不依赖未完成 plan。 |

### 5.2 与现有 plan 的重叠

创建本 plan 时扫描到的潜在冲突及解决方式：

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-145-tauri-windows-packaging.md` | 仅 `docs/BACKLOG.md` 元数据可能重叠；代码范围为 `src-tauri/`、sidecar 打包脚本和桌面文档，和 B-134 向量检索无重叠。 | 分区：B-134 只修改向量检索/存储相关文件和自身 BACKLOG 行，不触碰 Tauri 打包文件。 |
| `docs/superpowers/plans/*` 旧 legacy plan | 主要涉及 `src/` legacy 目录；B-134 不修改 `src/`。 | 分区：保持 `src/` 只读，不纳入本任务。 |

## 6. 完成标准

全部勾选后方可删除本 plan 文件：

- [ ] 功能行为符合 `docs/features/qdrant-vector-store.md` 的业务规则。
- [ ] 测试通过（参照 `docs/guides/testing.md` 最低要求）。
- [ ] 相关文档已同步（见下方"回流清单"）。
- [ ] BACKLOG 条目 `B-134` 状态已更新为 `done`。

## 7. 回流清单

删除本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| Qdrant 启用条件、降级行为、同步规则 | `docs/features/qdrant-vector-store.md` | [ ] |
| 目标架构中的向量存储职责和 ISSUE-002 状态 | `docs/design/architecture-overview.md` | [ ] |
| `chunk_vectors` 兼容/回退定位 | `docs/design/database-design.md` | [ ] |
| `/api/search` 和 `/api/search/debug` 的向量字段兼容说明 | `docs/design/api-spec.md` | [ ] |
| Qdrant 替换 SQLite 向量扫描的架构决策 | `docs/adr/ADR-007-qdrant-vector-store.md`, `docs/adr/README.md` | [ ] |
| B-134 完成状态 | `docs/BACKLOG.md` | [ ] |

若产生了重大技术决策，**必须**在删除 plan 前新建对应 ADR。

## 8. 执行记录

- 2026-06-28：Context7 查询 `/qdrant/qdrant-client`，确认 Python client 支持 local mode `QdrantClient(path=...)`、`create_collection`、`upsert`、`query_points`。
- 2026-06-28：`docs/design/new-architecture-design.md` 在当前 worktree 不存在；B-134 行关联 `docs/design/architecture-overview.md`，本任务以该文件为正式设计入口。
- 2026-06-28：`docs/adr/README.md` 已存在 ADR-006，Qdrant 决策使用下一个编号 `ADR-007-qdrant-vector-store.md`。
- 2026-06-28：任务 1 红灯测试命令 `& E:\Code\knowledage_island\.venv\Scripts\python.exe -m pytest tests/test_webapp/test_search.py::test_search_uses_vector_store_provider_without_sqlite_vector_scan -q`；失败符合预期：`search_documents() got an unexpected keyword argument 'vector_store'`。
- 2026-06-28：任务 2 实现 `BaseVectorStore` / `VectorSearchHit` / `VectorUpsertRecord`，并让 `search_documents(..., vector_store=...)` 使用 provider 候选；验证 `tests/test_webapp/test_search.py` 20 passed。

## 9. 状态快照

> **每完成 § 3 中的一个任务后立即更新**，不等到中断时才填。
> 目的：无论因额度耗尽、开发者中断还是主动结束，下一个 session 都能从此处冷启动。
> 正常完成后随 plan 一起删除。

- **最后更新**：2026-06-28 00:00
- **进度**：已完成 1 / 7 项（见 § 3 勾选状态）
- **最新 commit**：`59ad73e` — test: 增加 Qdrant 检索红灯测试
- **代码状态**：`fix/B-134-qdrant-vector-store`；任务 1 已提交；§9 快照已更新；运行时代码尚未实现 provider 接口
- **下一步**：任务 2：实现向量存储抽象与 `webapp/search.py` 集成；默认仍走 SQLite fallback，显式传入 provider 时使用 provider 候选。
- **续任务须知**：在 worktree `C:\Users\Lenovo\.config\superpowers\worktrees\knowledage_island\fix-B-134-qdrant-vector-store` 执行；测试使用 `E:\Code\knowledage_island\.venv\Scripts\python.exe`；任务 1 红灯失败点为 `search_documents()` 缺少 `vector_store` 参数。
