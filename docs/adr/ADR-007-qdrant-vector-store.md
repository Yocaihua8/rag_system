# ADR-007 Qdrant 本地向量存储

> 状态：Accepted
> Date：2026-06-28
> Owner：RAG 团队
> Related：docs/features/qdrant-vector-store.md, docs/design/architecture-overview.md, docs/design/database-design.md, docs/design/api-spec.md, docs/BACKLOG.md

## 1. 背景

Web MVP 原先把 chunk 向量存入 SQLite `chunk_vectors`，搜索时读取项目内全部向量并在 Python 中计算 cosine similarity。该方案依赖少、易备份，但在大型项目（> 5000 chunks）下查询耗时随 chunk 数线性增长，见 `docs/BACKLOG.md` 中的 ISSUE-002。

B-134 需要在保持本地优先、无独立服务依赖和现有 API 兼容的前提下，替换查询时的 SQLite 向量全扫描。

## 2. 决策结论

采用 **Qdrant Python client local mode** 作为 Web MVP 的可选向量索引 provider。

- 通过 `RAG_VECTOR_STORE_PROVIDER=qdrant` 启用，默认仍为 SQLite fallback。
- Qdrant 数据存储在本机目录，使用 `QdrantClient(path=...)`，不要求用户单独启动服务。
- `backend/providers/vector_store/QdrantVectorStore` 负责 collection 创建、point upsert、project filter 查询和删除。
- `backend/storage/knowledge_store.py` 继续写入 SQLite `chunk_vectors`，并在启用 Qdrant 时同步 upsert/delete Qdrant point。
- `backend/domain/search.py` 启用 Qdrant 时使用 Qdrant 返回的向量候选；Qdrant 未启用、不可用或查询失败时回退 SQLite `chunk_vectors`。

## 3. 备选方案

### 3.1 继续 SQLite 全扫描

- 优点：零新增 provider，导出恢复最简单。
- 缺点：大项目查询性能线性下降，无法解决 ISSUE-002。
- 未采用原因：无法满足 B-134 的性能目标。

### 3.2 ChromaDB

- 优点：Python 生态常见，已有历史依赖。
- 缺点：本项目当前 Web MVP 不依赖 ChromaDB；引入后仍需处理本地持久化、版本兼容和迁移边界。
- 未采用原因：B-134 明确要求 Qdrant 本地模式；Qdrant local mode 更贴合“无服务依赖 + HNSW”的目标。

### 3.3 Qdrant local mode

- 优点：HNSW 向量索引，Python client 支持本地 path 持久化，不需要独立 Qdrant 服务。
- 缺点：新增 `qdrant-client` 依赖；当前 sparse dict 向量需要转换为固定维度 dense vector。
- 采用原因：解决 SQLite 全扫描性能问题，同时保持本地运行和 API 兼容。

## 4. 影响

| 模块 | 影响 |
|------|------|
| `backend/providers/base.py` | 新增 `BaseVectorStore`、`VectorSearchHit`、`VectorUpsertRecord` |
| `backend/providers/vector_store/` | 新增 Qdrant 本地 provider |
| `backend/config/vector_store.py` | 新增 Qdrant 启用配置、软依赖检查和默认 provider 缓存 |
| `backend/storage/knowledge_store.py` | 文档入库、更新、删除、备份恢复同步 Qdrant；SQLite 写入仍为主兼容路径 |
| `backend/domain/search.py` | 启用 Qdrant 时使用 provider 候选；失败时回退 SQLite 向量扫描 |
| `requirements.txt` | 新增 `qdrant-client` |
| API | 不新增接口、不改请求参数、不改命中字段 |
| 数据库 | 不修改 SQLite schema |

## 5. 约束

- 默认不开启 Qdrant，避免改变现有安装后的行为。
- Qdrant 未安装、不可用、写入失败或查询失败时只打印 `WARNING`，不得阻断 Web MVP 启动、文档入库或检索。
- SQLite `chunk_vectors` 保留，继续用于备份恢复、项目健康统计和 fallback。
- `vector_provider` / `vector_model` 表示 embedding 来源，不表示 Qdrant provider。
- 不修改后端 API 路径、请求参数、响应字段或数据库 schema。

## 6. 回滚策略

- 将 `RAG_VECTOR_STORE_PROVIDER` 改回默认或移除，即可回退 SQLite `chunk_vectors` 检索。
- 已写入的 Qdrant 本地目录可删除；SQLite `chunk_vectors` 保留完整兼容副本。
- 如需代码回滚，删除 `backend/config/vector_store.py` 和 `backend/providers/vector_store/`，并恢复 `backend/storage/knowledge_store.py` / `backend/domain/search.py` 到仅 SQLite 路径。

## 7. 验证方式

- `tests/test_backend/test_qdrant_vector_store.py`
- `tests/test_webapp/test_vector_store_sync.py`
- `tests/test_webapp/test_search.py`
- `tests/test_webapp/test_api.py`
- `tests/test_webapp/test_docs_contract.py`
