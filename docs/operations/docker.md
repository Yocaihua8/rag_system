# Docker 双服务运行

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：`ops/docker/` 中的前端与后端 Compose 运行边界
> Related：`setup.md`、`runbook.md`、`../architecture/decisions/ADR-010-runtime-separation.md`

## 1. 服务

| 服务 | 镜像来源 | 宿主端口 | 健康检查 |
|------|----------|----------|----------|
| `backend` | `backend/Dockerfile` | `${KI_API_PORT:-8765}` | `GET /api/health` |
| `frontend` | `frontend/Dockerfile` + Nginx | `${KI_WEB_PORT:-4173}` | 前端静态首页 |

前端镜像在构建时写入公开 API 地址，默认由 `KI_PUBLIC_API_URL=http://127.0.0.1:8765` 提供给 `VITE_API_BASE_URL`。Nginx 只服务静态文件，不代理 `/api`。

## 2. 配置与启动

```powershell
Copy-Item ops/docker/.env.example ops/docker/.env
docker compose --project-directory ops/docker -f ops/docker/compose.yaml config
ops\docker\start.ps1
```

访问：

- 前端：`http://127.0.0.1:4173`
- 后端健康：`http://127.0.0.1:8765/api/health`
- API 文档：`http://127.0.0.1:8765/docs`

若使用远程主机名或反向代理，`KI_PUBLIC_API_URL` 必须是浏览器可达地址，`KI_CORS_ORIGINS` 必须精确包含前端页面 Origin。不要使用 `*`。

## 3. 检查与日志

```powershell
docker compose --project-directory ops/docker -f ops/docker/compose.yaml ps
docker compose --project-directory ops/docker -f ops/docker/compose.yaml logs --tail 200 backend
docker compose --project-directory ops/docker -f ops/docker/compose.yaml logs --tail 200 frontend
```

两个容器都健康后，再从 4173 页面执行真实 API/SSE 冒烟。单独健康不代表跨域配置正确。

## 4. 停止与数据

```powershell
ops\docker\stop.ps1
```

正常停止保留运行 volume。不要添加 `-v`，除非用户明确授权删除准确的持久化数据并已验证备份。

用户 `.env`、`runtime/` 和导入资料不属于源码清理范围；不要打印凭证内容。
