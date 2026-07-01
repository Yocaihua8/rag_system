# ops 维护脚本

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-29
> Scope：B-06 本地维护脚本与索引重建管理入口
> Related：ops/README.md, docs/design/api-spec.md, docs/design/architecture-overview.md, docs/BACKLOG.md

## 1. 功能定位

B-06 为本地 Knowledge Island Web MVP 补齐最小运维维护能力。它面向本机开发者或本地部署维护者，不新增前端页面，不新增数据库 schema，不改变普通用户导入、检索和问答流程。

## 2. 用户可见行为

- `ops/scripts/backup_db.sh` 可备份当前 SQLite 数据库，默认路径为 `runtime/webapp/knowledge_island.db`；存在 `KI_QDRANT_DIR` 或 `RAG_QDRANT_PATH` 指向的 Qdrant local 目录时一并打包向量存储目录。
- `ops/scripts/cleanup_runtime.sh` 只清理 runtime 下的临时文件、缓存和 Python 字节码，不删除 SQLite 数据库、`runtime/backups`、Qdrant 数据目录或用户导入内容。
- `ops/scripts/rebuild_index.sh` 调用本地 `POST /api/admin/rebuild-index`，由后端基于 SQLite 已存文档内容重建 chunk 与向量索引；未传项目 ID 时重建全部项目，传 `KI_PROJECT_ID` 或第一个脚本参数时只重建指定项目。
- 启用认证时，`rebuild_index.sh` 需要携带 API Key 或 Bearer Token；脚本不得保存或输出密钥明文。

## 3. 非目标

- 不提供远程多用户运维后台。
- 不新增前端运维页面。
- 不修改 SQLite schema。
- 不新增 Agent 工具或扩大 Agent 写权限。
- 不重新扫描文件系统导入文档；索引重建只使用数据库中已保存的文档正文。
- 不实现异步任务队列、进度查询、取消任务或定时备份。

## 4. 架构落点

维护脚本位于 `ops/scripts/`，通过环境变量接收路径和服务地址。后端维护入口位于 `backend/routes/admin.py`，由 `backend.routes.dispatch_to_routes()` 分发；路由层只做参数解析和 JSON 响应封装，索引重建能力由 `KnowledgeStore` 暴露的数据维护方法完成。

`POST /api/admin/rebuild-index` 属于本地维护 API，复用 B-140 认证中间件的 `/api/*` 保护规则；默认认证关闭时保持本地开发便利，开启认证后需要 `X-API-Key` 或 `Authorization: Bearer`。

## 5. 验收标准

- 三个 shell 脚本存在且包含 `set -euo pipefail`、路径保护和清晰错误输出。
- `POST /api/admin/rebuild-index` 能在指定 `project_id` 时只重建该项目文档；不指定时重建全部项目文档。
- 索引重建后 `document_chunks` 与 `chunk_vectors` 与文档正文重新对齐。
- `/openapi.json` 和 `docs/design/api-spec.md` 均包含新增 admin API。
- 相关 `tests/test_webapp` 通过，或明确记录环境导致的失败。

## 6. 脚本参数

| 脚本 | 参数 / 环境变量 | 说明 |
|------|----------------|------|
| `backup_db.sh` | `KI_DB_PATH`、`KI_BACKUP_DIR`、`KI_BACKUP_RETENTION`、`KI_QDRANT_DIR` / `RAG_QDRANT_PATH` | 覆盖默认 DB、备份目录、保留份数和 Qdrant local 目录 |
| `cleanup_runtime.sh` | `KI_RUNTIME_DIR`、`KI_BACKUP_DIR`、`KI_QDRANT_DIR` / `RAG_QDRANT_PATH` | 仅允许清理仓库 `runtime/` 内的临时文件 |
| `rebuild_index.sh` | `KI_BASE_URL`、`KI_PROJECT_ID`、`KI_API_KEY`、`KI_BEARER_TOKEN` | 配置本地服务地址、项目范围和认证凭证 |
