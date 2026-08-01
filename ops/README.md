# 运维目录

`ops/` 只保存部署编排与本地维护脚本，不承载应用源码。

## Docker

前后端使用两个服务和两个镜像：

- `ops/docker/compose.yaml`：Compose 编排，前端默认 `4173`、后端默认 `8765`。
- `backend/Dockerfile`：API-only FastAPI 镜像。
- `frontend/Dockerfile`：构建 Vue 后由 Nginx 提供静态文件；不反向代理 API。
- `ops/docker/.env.example`：非敏感配置示例。

Windows：

```powershell
.\ops\docker\start.ps1
.\ops\docker\stop.ps1
```

Linux/macOS：

```bash
./ops/docker/start.sh
./ops/docker/stop.sh
```

前端通过构建时 `VITE_API_BASE_URL` 直接访问后端，容器默认公开地址为
`http://127.0.0.1:8765`。如果从其他主机访问，必须同时设置
`KI_PUBLIC_API_URL` 与精确的 `KI_CORS_ORIGINS`。

## 维护脚本

`ops/scripts/` 中的备份、运行时清理与索引重建脚本保持独立；使用前先查看脚本头部参数，并确认目标是 `runtime/v2/` 当前数据代际。

- `backup_db.sh` 默认读取 `runtime/v2/app.db`，写入 `runtime/v2/backups/knowledge-island-v2-<timestamp>.sqlite3`，并保留最近 7 份。
- 自定义运行时必须显式传 `KI_DB_PATH`；备份目录和保留数量分别由 `KI_BACKUP_DIR`、`KI_BACKUP_RETENTION` 覆盖。
- Windows Git Bash 调用 `sqlite3.exe` 时会使用 `cygpath -m` 转换在线备份目标；缺少 `sqlite3` 时退回文件复制并应先停机。
- Qdrant local 只有设置 `KI_QDRANT_DIR` 或 `RAG_QDRANT_PATH` 时才会单独打包；SQLite 备份不包含问答导出文件。
