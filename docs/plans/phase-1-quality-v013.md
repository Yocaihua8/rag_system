# Phase 1 质量层 v0.13.0

> 状态：Active
> 创建时间：2026-06-06
> 创建方：Codex
> 关联 BACKLOG：B-134, B-153, B-154, B-128, B-06, B-136, B-25
> 关联功能文档：docs/features/fastapi-runtime.md, docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md, docs/design/database-design.md, docs/design/api-spec.md

## 1. 目标

消除 ISSUE-002 中 SQLite 向量全扫描导致的大规模 chunk 检索性能瓶颈，并补齐 v0.13.0 所需的并发、质量指标、对话分支、运维接口、OpenAPI 和 E2E 基础设施。

完成后系统应处于：

- `KI_VECTOR_BACKEND=qdrant` 与 `KI_VECTOR_BACKEND=sqlite` 均可通过 `pytest tests/ -x`。
- Qdrant 后端可通过迁移脚本从 SQLite `chunk_vectors` 导入向量，SQLite 仍保留为降级后端。
- SQLite 连接启用 WAL、`synchronous=NORMAL` 和 `busy_timeout=5000`。
- 回答质量指标可写入并通过项目摘要接口聚合。
- 对话支持从历史消息派生新分支。
- `/api/admin/*` 运维接口、OpenAPI summary、静态 `docs/design/openapi.json`、E2E 测试和 `CHANGELOG.md` v0.13.0 发布说明完成。

## 2. 前置条件

- 当前分支：`feature/phase-1-quality`。
- 本 plan 已写回 `docs/BACKLOG.md` 相关条目。
- 不修改 `frontend/src/api/`、`frontend/src/state/`。
- 每完成 § 3 一个任务，必须运行 `pytest tests/ -x` 并通过后提交。
- Qdrant 相关实现前必须用 `ctx7` 查询当前 `qdrant-client` 文档。

## 3. 任务拆解

- [x] Task 1 WAL：在 `backend/knowledge_island/storage.py` 的 `_connect()` 连接建立后设置 `PRAGMA journal_mode=WAL`、`PRAGMA synchronous=NORMAL`、`PRAGMA busy_timeout=5000`；新增 `tests/backend/test_concurrent_access.py`，验证并发读写不抛出 `sqlite3.OperationalError: database is locked`；运行 `pytest tests/backend/test_concurrent_access.py` 和 `pytest tests/ -x`。
- [x] Task 2 Qdrant：按用户给定接口新建 `backend/knowledge_island/vector_backend.py`，实现 `sparse_to_dense()`、`dense_to_sparse()`、`SqliteVectorBackend`、`QdrantVectorBackend`、`get_vector_backend()`；改造 `search.py` 通过 `VectorBackend` 检索；改造 `ingestion.py` 或等价向量写入路径同步写 Qdrant；新增 `scripts/migrate_vectors_to_qdrant.py`；`requirements.txt` 追加 `qdrant-client>=1.9.0` 可选依赖；运行 `pytest tests/backend/`、`KI_VECTOR_BACKEND=qdrant python scripts/migrate_vectors_to_qdrant.py` 和 `pytest tests/ -x`。
- [x] Task 3 quality：为 `chat_messages` 增加 `quality_metrics` 字段；在回答完成后计算 `source_coverage`、`retrieval_top_score`、`has_sources`、`answer_length`；新增 `GET /api/projects/quality-summary`；在 `frontend/src/views/LibraryView.vue` 追加质量指标展示，不修改 `frontend/src/api/` 或 `frontend/src/state/`；运行 `pytest tests/backend/` 和 `pytest tests/ -x`。
- [x] Task 4 branch：为 `chat_messages` 增加 `parent_message_id`、`branch_id`、`is_active`；新增 `branch_chat_message()`；`GET /api/chat/messages` 支持 `include_branches=true`；新增 `POST /api/chat/messages/branch`；在 `frontend/src/views/WorkbenchView.vue` 增加历史消息编辑重发 UI，不修改 `frontend/src/api/` 或 `frontend/src/state/`；运行 `pytest tests/backend/` 和 `pytest tests/ -x`。
- [ ] Task 5 admin API：新增 `backend/knowledge_island/routes/admin.py` 和 `/api/admin/stats`、`/api/admin/rebuild-index` 等运维接口；注册路由；新增 `ops/scripts/backup_db.sh`、`ops/scripts/rebuild_index.sh`、`ops/scripts/cleanup_runtime.sh`；运行 `pytest tests/backend/` 和 `pytest tests/ -x`。
- [ ] Task 6 OpenAPI：为 `server.py` 的 `FastAPI(...)` 补全 title/description/version/docs_url/redoc_url；为所有 FastAPI endpoint 补 `summary` 和 tags；生成并提交 `docs/design/openapi.json`；验证 `/docs` 可访问且所有端点有 summary。
- [ ] Task 7 E2E：新增 `tests/e2e/conftest.py`、`tests/e2e/test_api_flows.py` 和 Playwright UI 骨架；运行 `pytest tests/e2e/test_api_flows.py -v`、`pytest tests/e2e/ -v` 和 `pytest tests/ -x`。
- [ ] 前端构建与发布收口：运行 `npm --prefix frontend run build`；追加 `CHANGELOG.md` v0.13.0 发布说明；确认 `git tag v0.13.0` 可创建。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `backend/knowledge_island/storage.py` | 修改 WAL、schema migration、质量指标存储 |
| 代码 | `backend/knowledge_island/search.py` | 修改为使用 VectorBackend |
| 代码 | `backend/knowledge_island/ingestion.py` | 修改为写入 VectorBackend |
| 代码 | `backend/knowledge_island/vector_backend.py` | 新增向量后端抽象与实现 |
| 代码 | `backend/knowledge_island/answers.py` | 修改回答质量指标计算 |
| 代码 | `backend/knowledge_island/routes/chat.py` | 修改对话分支端点 |
| 代码 | `backend/knowledge_island/routes/admin.py` | 新增运维端点 |
| 代码 | `backend/knowledge_island/server.py` | 修改路由挂载与 OpenAPI metadata |
| 代码 | `scripts/migrate_vectors_to_qdrant.py` | 新增迁移脚本 |
| 代码 | `ops/scripts/` | 新增运维脚本 |
| 前端 | `frontend/src/views/WorkbenchView.vue` | 修改对话分支 UI |
| 前端 | `frontend/src/views/LibraryView.vue` | 修改质量指标展示 |
| 前端 | `frontend/src/views/SettingsView.vue` | 修改系统维护区 |
| 测试 | `tests/backend/` | 新增/修改后端回归测试 |
| 测试 | `tests/e2e/` | 新增 E2E 测试 |
| 文档 | `docs/design/architecture-overview.md` | 同步向量后端架构 |
| 文档 | `docs/design/database-design.md` | 同步新增字段 |
| 文档 | `docs/design/api-spec.md` | 同步新增接口 |
| 文档 | `docs/design/openapi.json` | 新增 OpenAPI 导出 |
| 文档 | `docs/guides/testing.md` | 同步 E2E/验证命令 |
| 文档 | `CHANGELOG.md` | 追加 v0.13.0 发布说明 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 已在本分支合入当前 Web MVP 目录结构基线 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | 当前 `docs/plans/` 下无其他 Active/Interrupted 业务 plan | N/A |

## 6. 完成标准

- [ ] `KI_VECTOR_BACKEND=qdrant pytest tests/ -x` 通过。
- [ ] `KI_VECTOR_BACKEND=sqlite pytest tests/ -x` 通过。
- [ ] `pytest tests/e2e/test_api_flows.py -v` 通过。
- [ ] `npm --prefix frontend run build` 通过。
- [ ] `/docs` 所有端点有 `summary`。
- [ ] `docs/design/openapi.json` 已生成并提交。
- [ ] `CHANGELOG.md` 已追加 v0.13.0 发布说明。
- [ ] `git tag v0.13.0` 可创建。
- [ ] BACKLOG 相关条目按完成状态更新。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| SQLite WAL 连接策略 | `docs/design/database-design.md` | [x] |
| Qdrant/SQLite VectorBackend 架构 | `docs/design/architecture-overview.md` | [x] |
| 新 DB 字段：chat branch 与 quality_metrics | `docs/design/database-design.md` | [ ] |
| 新 API：chat branch、quality-summary、admin | `docs/design/api-spec.md` | [ ] |
| OpenAPI 静态导出 | `docs/design/openapi.json` | [ ] |
| E2E 与向量后端验证命令 | `docs/guides/testing.md` | [ ]（向量后端命令已补，E2E 待 Task 7） |
| v0.13.0 发布说明 | `CHANGELOG.md` | [ ] |

## 8. 执行记录

- 2026-06-06 00:10：用户要求从 `main` 新建分支；实际 `main` 仍是旧 `webapp/` 目录结构。已在 `feature/phase-1-quality` 合并 `fix/b-147-docs-consistency`，使本分支具备目标要求的 `backend/knowledge_island/` 与 `tests/backend/` 结构。
- 2026-06-06 00:21：Task 1 完成。`tests/backend/test_concurrent_access.py` 先验证 RED：`journal_mode` 为 `delete`；实现 WAL 后定向测试通过。完整 `pytest tests/ -x` 首次暴露 legacy vector_store 目录迁移缺口和 ProjectSpacePanel root_path 静态断言缺口，经用户确认后补回 legacy vector store 兼容包，并将项目目录展示改为 `root_path` 优先。最终 `pytest tests/ -x` 通过，494 passed。
- 2026-06-06 00:37：Task 2 完成。已按 ctx7 查询 `/qdrant/qdrant-client` 当前文档，采用 `QdrantClient(path=...)` local mode、`create_collection(VectorParams(...Distance.COSINE))`、`upsert(PointStruct)`、`query_points(...).points`。`tests/backend/test_vector_backend.py` 先 RED 后 GREEN；`KI_VECTOR_BACKEND=qdrant` 与 `KI_VECTOR_BACKEND=sqlite` 的 vector/search 相关后端测试均通过；迁移脚本在默认空库上输出 `迁移完成：0 条向量`；最终 `pytest tests/ -x` 通过，497 passed。
- 2026-06-06 01:07：Task 3 完成。`tests/backend/test_api_route_split.py::test_projects_route_module_handles_quality_summary` 与 `tests/backend/test_api.py::test_api_import_search_and_answer_flow` 先 RED：`create_chat_message` 不支持 `quality_metrics` 且回答消息未返回该字段；实现后定向测试通过。新增 `chat_messages.quality_metrics`、回答完成质量指标计算、`GET /api/projects/quality-summary` 和资料库 dashboard“回答有来源率”；未修改 `frontend/src/api/` 或 `frontend/src/state/`。最终 `pytest tests/backend/`、`pytest tests/ -x` 和 `npm --prefix frontend run build` 通过。
- 2026-06-06 01:19：Task 4 完成。`test_branch_chat_message_hides_following_messages_by_default` 与 `test_chat_route_module_handles_message_branching` 先 RED：`KnowledgeStore` 不存在 `branch_chat_message` 且 chat route 未注册 branch 端点；实现后定向测试通过。新增 `parent_message_id / branch_id / is_active`，默认聊天列表只返回 active 消息，`include_branches=true` 返回全部；Workbench 历史用户消息可 hover 编辑并调用 branch 端点。最终 `pytest tests/backend/`、`pytest tests/ -x` 和 `npm --prefix frontend run build` 通过。

## 9. 状态快照

- **最后更新**：2026-06-06 01:08
- **进度**：已完成 3 / 8 项（见 § 3 勾选状态）
- **最新 commit**：`474814a` — feat: 记录回答质量指标
- **代码状态**：`feature/phase-1-quality`；Task 3 已提交，工作区仅剩本状态快照更新
- **下一步**：Task 4 branch
- **续任务须知**：此 worktree 无本地 `.venv`，可暂用 `E:\Code\knowledage_island\.venv\Scripts\python.exe` 运行 pytest。
