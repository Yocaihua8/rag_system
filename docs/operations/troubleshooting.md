# 故障排查

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：独立前后端、CORS、Docker、桌面和数据代际问题
> Related：`setup.md`、`docker.md`、`runbook.md`

## 1. 后端无法访问

```powershell
.\.venv\Scripts\python.exe -m backend
Invoke-RestMethod http://127.0.0.1:8765/api/health
Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
```

确认依赖来自 `backend/requirements/dev.txt`，端口未占用，启动目录为仓库根。`GET /` 返回 404 是正常设计，不是服务故障。

## 2. 页面可见但 API 请求失败

1. 在浏览器 Network 查看实际绝对 URL，应指向配置的 `VITE_API_BASE_URL`。
2. 确认后端健康，并检查浏览器控制台是否为 CORS 拒绝。
3. `KI_CORS_ORIGINS` 必须包含页面的完整 Origin（scheme、host、port），不是 API 地址。
4. 修改 API base 后重新构建/启动前端；该变量是构建配置。
5. SSE 失败时同时检查 EventSource URL、CORS 和认证参数，不只检查普通 fetch。

不要把关闭浏览器安全或放行 `*` 当作修复。

## 3. Docker

```powershell
docker compose --project-directory ops/docker -f ops/docker/compose.yaml config
docker compose --project-directory ops/docker -f ops/docker/compose.yaml ps
docker compose --project-directory ops/docker -f ops/docker/compose.yaml logs --tail 200 backend
docker compose --project-directory ops/docker -f ops/docker/compose.yaml logs --tail 200 frontend
```

若容器均健康但页面请求失败，检查 `KI_PUBLIC_API_URL` 是否对浏览器可达，以及 `KI_CORS_ORIGINS` 是否包含 4173 页面 Origin。前端没有 API 反向代理。

## 4. v2 数据代际拒绝启动

1. 检查 `RAG_RUNTIME_DIR` 是否误指向 1.x 非空目录。
2. 恢复默认 `runtime/v2/` 或使用隔离空目录。
3. 不删除、覆盖或自动迁移旧数据库。
4. 需要旧资料时使用支持的重新导入或项目导出/恢复流程。

## 5. 模型或向量能力失败

- 不把 `/api/health` 成功当作 Provider 就绪。
- 只确认环境变量是否存在，不打印值。
- LLM 失败应明确回退有来源的本地回答；Embedding 失败应回退 hashing，Qdrant 失败应回退 SQLite。
- 若降级没有发生，记录脱敏异常、provider、模型名和复现步骤。

## 6. Tauri

- `cargo check` 失败：确认 Rust target、C/C++ linker 和平台 SDK。
- bundle 缺 sidecar：检查 `src-tauri/scripts/` 输出文件名与 `externalBin` target triple。
- 安装后页面可见但 API 失败：检查 sidecar 进程、8765 监听、Tauri Origin CORS、CSP `connect-src` 和 EventSource。
- bundle 成功不能替代安装后动态验证。

## 7. 报告

提供 commit、系统、命令、前后端 URL、脱敏日志、预期/实际结果和已尝试步骤。安全问题按根 `SECURITY.md` 私密上报；不要粘贴 Key、Token 或敏感项目内容。
