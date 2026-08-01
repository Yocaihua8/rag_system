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
