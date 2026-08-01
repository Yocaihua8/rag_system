# 运维手册

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：本地与 Docker 前后端的启动、检查、停止和故障升级
> Related：`setup.md`、`docker.md`、`troubleshooting.md`、`security.md`

Knowledge Island 默认是本地单用户应用，没有已确认的生产值班、集中监控或自动回滚平台。

## 1. 服务清单

| 服务 | 位置 | 健康/入口 |
|------|------|-----------|
| FastAPI API | 本机或 backend 容器，8765 | `GET /api/health` |
| Vue 前端 | Vite 5173、preview/Docker 4173 | 静态首页 + 浏览器主流程 |
| SQLite | `runtime/v2/app.db` 或容器 volume | 无独立 readiness |
| 外部 Provider | 用户配置的 LLM/Embedding | 无统一健康检查 |

## 2. 本地启动

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

停止时在对应终端按 `Ctrl+C`。仓库不提供后台进程管理器。

## 3. Docker

```powershell
docker compose --project-directory ops/docker -f ops/docker/compose.yaml config
ops\docker\start.ps1
docker compose --project-directory ops/docker -f ops/docker/compose.yaml ps
ops\docker\stop.ps1
```

日志按服务查看，详见 [`docker.md`](docker.md)。停止不得默认删除 volume。

## 4. 最小就绪检查

1. 后端 `/api/health` 返回 `status=ok`。
2. 前端页面从配置的 API base 成功访问后端，没有 CORS 错误。
3. 使用隔离测试项目完成导入、检索/流式问答和来源展示。
4. 使用外部模型时确认 Provider 可用，但不要打印 Key。
5. 桌面模式额外验证 sidecar 启动和安装后 API/SSE 连通性。

## 5. 数据与回退

- 默认 v2 数据为 `runtime/v2/app.db` 及其向量目录。
- 回退源码前保存实际 `RAG_RUNTIME_DIR`，并用隔离数据目录验证旧版本兼容性。
- 不让旧版本直接覆盖 v2 数据，不把单纯文件复制称为已验证恢复。
- 项目导出/恢复 API 创建项目级副本，不等同于整库灾难恢复。

## 6. 故障升级

收集版本/commit、运行方式、前后端 URL、脱敏错误、重现步骤和已执行命令。不得复制凭证或真实敏感资料。处理顺序见 [`troubleshooting.md`](troubleshooting.md)；安全问题按根 [`SECURITY.md`](../../SECURITY.md) 上报。

当前无固定 SLA、值班人或告警阈值；这些字段保持 `TBD`，不得虚构。
