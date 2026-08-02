# 运行与维护手册

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：v2/v3 本地与 Docker 启停、健康检查、备份、清理和索引重建
> Related：`setup.md`、`testing.md`、`troubleshooting.md`、`security.md`、`../design/agent-runtime-and-tool-contract.md`

Knowledge Island 默认是本地单用户应用，没有已确认的生产值班、集中监控或自动回滚平台。

## 1. 服务与数据

| 对象 | 默认位置/入口 | 就绪判断 |
|------|---------------|----------|
| FastAPI API | `127.0.0.1:8765` | `GET /api/health` |
| v3 Agent API（alpha） | `/api/v3`；同一 FastAPI 进程 | `GET /api/v3/health` 返回 v3 revision 且 `executor_running=true` |
| Vue 前端 | Vite 5173；preview/Docker 4173 | 页面加载且能调用 API |
| v2 SQLite | `runtime/v2/app.db` | 无独立 readiness |
| v3 SQLite | `runtime/v3/app.db` | 启动时通过 generation 与 Alembic head 校验 |
| Qdrant local | 默认关闭；配置路径后启用 | 实际检索且无回退 warning |
| 问答导出 | `runtime/v2/outputs/` | 不属于 SQLite 备份脚本范围 |

## 2. 本地启停

```powershell
# 终端一
.\.venv\Scripts\python.exe -m backend

# 终端二
npm run frontend:dev
```

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/health
Get-NetTCPConnection -LocalPort 8765,5173 -State Listen -ErrorAction SilentlyContinue
```

在各终端按 `Ctrl+C` 停止。仓库不提供后台进程管理器。

正常 `python -m backend` 在保留 v2 Store/路由的同时初始化 v3 Store，并由 FastAPI lifespan 启动持久 executor。v3 初始化遇到未标记、v2、未知代际或 Alembic revision 不匹配的数据库会拒绝启动；不要通过删除、覆盖或把 v2 文件改名为 v3 来绕过。

## 3. Docker 启停与日志

```powershell
docker compose --project-directory ops/docker -f ops/docker/compose.yaml config
ops\docker\start.ps1 -NoOpen
docker compose --project-directory ops/docker -f ops/docker/compose.yaml ps
docker compose --project-directory ops/docker -f ops/docker/compose.yaml logs --tail 200 backend
docker compose --project-directory ops/docker -f ops/docker/compose.yaml logs --tail 200 frontend
ops\docker\stop.ps1
```

前端和后端各有健康检查，但仍需从 4173 页面访问 8765 API 验证跨域。正常停止保留 volume；`stop.ps1 -RemoveVolumes` 会删除 volume，只有在准确确认目标和备份后才可使用。

## 4. 最小就绪检查

1. `/api/health` 返回 `status=ok`。
2. 前端从配置的绝对 API base 访问后端，无 CORS 错误。
3. 使用隔离项目完成导入、检索、SSE 问答和来源展示。
4. 使用外部 Provider 时单独验证 Provider；不要打印 Key。
5. 桌面模式额外验证 sidecar 启动、8765 监听和退出清理。

v3 alpha 另做以下最小检查：

1. `/api/v3/health` 返回 `data_generation=v3`、`schema_revision=0001_v3_initial` 和 `executor_running=true`。
2. health 只证明 v3 数据库初始化和 executor 已启动，不代表项目检查、SSE、审批或产物链都成功。
3. 完整冒烟必须使用隔离项目创建 Project → Task → `project.inspect.v1` Run，等待终态后检查 Steps、SSE 回放和 `project_inspection` Artifact；不能使用真实敏感项目目录。
4. 当前 Vue 未接 v3；页面可用不能作为 v3 API 或 executor 的验收证据。

## 5. v3 alpha 配置与恢复边界

| 配置 | 默认值 | 范围 |
|------|--------|------|
| `KI_DATA_ROOT` | `runtime/v3/` | v3 vectors/artifacts/logs/backups 根；不得指向 v2 活动目录 |
| `KI_V3_DB_PATH` | `<v3-data-root>/app.db` | 只覆盖 v3 SQLite 文件 |
| `KI_AGENT_MAX_CONCURRENCY` | `2` | 允许 1-2 |
| `KI_AGENT_LEASE_SECONDS` | `30` | 允许 5-3600 秒 |
| `KI_AGENT_POLL_INTERVAL_MS` | `100` | 允许 10-60000ms |

executor 使用数据库租约和心跳。进程异常退出后，下次启动会检查过期运行：可安全重放的读/分析步骤可以恢复，结果不明确的写步骤不得自动重放。当前真实 `project.inspect.v1` 只有只读/分析步骤；审批写回、外部发布和文件导出尚未形成可执行工作流。

若 v3 启动失败：

1. 停止反复启动，记录脱敏错误、数据库准确路径和 commit；
2. 只读确认目标是否为预期 v3 文件，不得运行 v2 迁移或手工改 `app_metadata` / `alembic_version`；
3. 对有价值文件先做可恢复副本，再在隔离目录验证；
4. 未确认代际和 revision 前，不删除、不覆盖、不执行 downgrade。

## 6. v2 备份

维护脚本在 `ops/scripts/`，需从 Bash、Git Bash 或 WSL 执行：

```bash
bash ops/scripts/backup_db.sh
```

- 默认数据库：`runtime/v2/app.db`。
- 默认备份目录：`runtime/v2/backups/`。
- 默认保留 7 份，可用 `KI_BACKUP_RETENTION` 覆盖。
- 有 `sqlite3` 时使用在线 `.backup`；Git Bash 调用 Windows `sqlite3.exe` 时脚本会用 `cygpath -m` 转换目标路径。没有 `sqlite3` 时退回文件复制，此时应先停止应用以获得一致副本。
- 使用 Qdrant local mode 时设置 `KI_QDRANT_DIR` 或 `RAG_QDRANT_PATH`，脚本会另外打包该目录。
- `runtime/v2/outputs/` 或自定义输出目录、用户导入原始文件和未提交 `.env` 不在 SQLite 备份内。

仓库测试会在临时项目中实际运行脚本，把备份复制为独立数据库，并验证 `PRAGMA integrity_check=ok`、`app_metadata.data_generation=v2` 和样例数据。可运行：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/repository/test_ops_scripts.py -q -rs
```

实际恢复前必须停止写入、保留现有数据副本，并先在隔离目录重复上述完整性、代际和样例数据验证；不得直接覆盖活动 `runtime/v2/app.db`。使用 Qdrant local mode 时还要恢复同一时间点的向量目录。仓库没有“一键恢复即保证兼容”的脚本。

现有 `backup_db.sh`、恢复测试和 7 份保留策略只覆盖 v2，不是 v3 备份证据。v3 当前没有经过仓库恢复测试的自动备份脚本；需要保留 alpha 数据时，应先停止应用并对 `runtime/v3/app.db` 做 SQLite 一致性备份，同时记录 Alembic revision。`runtime/v3/vectors/`、`artifacts/`、`logs/` 和 `backups/` 当前为独立目录，其中内部项目检查产物正文仍保存在 SQLite；不要假定复制预留目录即可恢复运行。

## 7. 临时文件清理

```bash
bash ops/scripts/cleanup_runtime.sh
```

脚本只允许处理仓库 `runtime/` 内的 `__pycache__`、pytest cache、`.pyc` 和临时文件，并排除数据库、`runtime/v2/backups/` 和配置的 Qdrant 目录。不要把它用于任意外部路径。

现有清理脚本排除数据库和 v2 备份，但尚未声明 v3 数据清理契约；不要用它删除 `runtime/v3/` 内容。

## 8. 索引重建

先启动后端，再执行：

```bash
bash ops/scripts/rebuild_index.sh
KI_PROJECT_ID=<project-id> bash ops/scripts/rebuild_index.sh
```

脚本调用 `POST /api/admin/rebuild-index`，只使用 SQLite 已保存正文重建 chunk 与向量，不重新扫描文件系统。启用认证时通过 `KI_API_KEY` 或 `KI_BEARER_TOKEN` 临时提供凭证；脚本不保存或输出它们。

索引重建接口仍服务 v2 SQLite/Qdrant，不处理 v3 `sources/documents/chunk_vectors`，也不会重新执行 Agent Run。

## 9. 故障升级

收集 commit、运行方式、系统、前后端 URL、脱敏日志、重现步骤和已执行命令。不得复制凭证或真实敏感资料。当前 SLA、值班人和告警阈值均为 `TBD`。
