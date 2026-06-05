# ops

工程运维目录（目标态）：

- `scripts/`：发布、体检、初始化、验收脚本

当前脚本：

- `scripts/backup_db.sh`：通过 `sqlite3 .dump` 备份 `KI_DB_PATH`，并在存在 Qdrant local 目录时打包 `KI_QDRANT_DIR`；默认保留最近 7 份。
- `scripts/rebuild_index.sh`：调用本地 `POST /api/admin/rebuild-index`，重建当前 `VectorBackend` 索引。
- `scripts/cleanup_runtime.sh`：清理 `runtime/` 下临时文件和 `__pycache__`，不删除数据库或 Qdrant 数据目录。

脚本默认面向 Bash 环境；Windows 本地开发可通过 Git Bash、WSL 或 CI shell 执行。

