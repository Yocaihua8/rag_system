# 故障排查

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：独立前后端、CORS、Docker、桌面、插件、依赖和数据问题
> Related：`setup.md`、`runbook.md`、`security.md`

## 1. 后端无法访问

```powershell
.\.venv\Scripts\python.exe -m backend
Invoke-RestMethod http://127.0.0.1:8765/api/health
Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
```

确认依赖来自 `backend/requirements/dev.txt`、端口未占用、启动目录为仓库根。`GET /` 返回 404 是正常设计。

## 2. 页面可见但 API 失败

1. 浏览器 Network 中的 URL 应指向配置的 `VITE_API_BASE_URL`，不是相对 `/api`。
2. 确认后端健康，并检查 CORS 拒绝；`KI_CORS_ORIGINS` 需要页面完整 Origin，而不是 API 地址。
3. 修改 API base 后重新启动或构建前端。
4. SSE 失败时同时检查 EventSource URL、CORS 和认证。当前原生 EventSource 未接自定义认证 header，启用认证时不是单纯 CORS 问题。

不要用关闭浏览器安全或允许 `*` 解决问题。

## 3. Docker

```powershell
docker compose --project-directory ops/docker -f ops/docker/compose.yaml config
docker compose --project-directory ops/docker -f ops/docker/compose.yaml ps
docker compose --project-directory ops/docker -f ops/docker/compose.yaml logs --tail 200 backend
docker compose --project-directory ops/docker -f ops/docker/compose.yaml logs --tail 200 frontend
```

若两个容器都健康但页面请求失败，检查 `KI_PUBLIC_API_URL` 是否从浏览器可达、`KI_CORS_ORIGINS` 是否含 4173 Origin。前端 Nginx 不代理 API。

## 4. v2 数据拒绝启动

1. 检查 `RAG_RUNTIME_DIR` 是否误指向 1.x 非空目录。
2. 恢复默认 `runtime/v2/` 或使用隔离空目录。
3. 不删除、覆盖或自动迁移旧数据库。
4. 需要旧资料时使用重新导入或已验证的项目导出/恢复流程。

## 5. 导入与可选依赖

- PDF 无正文：检查是否安装 `pymupdf`；它不在 requirements 中。
- 中文关键词效果没有变化：`jieba` 虽已安装，但当前源码未调用，不能靠重装启用。
- 分块环境变量没有效果：当前实际分块仍固定为 700/80，配置尚未接线。
- URL 摘录卡片失败：当前资料弹窗只提交 URL，而 helper 还要求标题和正文；改用已接通导入入口并记录该部分接线问题。

## 6. 模型、向量与 reranker

- `/api/health` 成功不代表 LLM/Embedding Provider 就绪；只检查变量是否存在，不打印值。
- LLM 失败应返回有来源的本地降级；Embedding API 失败应回退 hashing。
- Qdrant 只在 `RAG_VECTOR_STORE_PROVIDER=qdrant` 时启用；失败应回退 SQLite。检查 `RAG_QDRANT_PATH` 和日志 warning。
- Cross-Encoder 需要额外安装 `sentence-transformers`；未安装时 reranker 被跳过。
- Pinia 已声明但当前未使用，前端状态问题不应按 Pinia store 调试。

## 7. 桌面应用

- `cargo check` 失败：确认 Rust target、C/C++ linker 和平台 SDK。
- bundle 缺 sidecar：检查 `src-tauri/scripts/` 产物名与 `externalBin` target triple。
- 安装后页面可见但 API 失败：检查 sidecar 进程、8765 端口、Tauri Origin CORS、CSP 和 EventSource。
- 当前没有完整 readiness 等待；启动初期失败时先确认 sidecar 实际就绪，不把 bundle 成功当动态验证。

## 8. Obsidian 插件

- 先串行运行插件 `test`、`typecheck`、`build`，不要使用根前端构建命令替代插件构建。
- 配对失败时检查配对码是否过期、当前项目是否已有活动连接，以及后端 loopback 可达性。
- 发布停在 `queued` 表示等待插件执行，不代表写入失败；查看插件连接与待执行领取。
- `conflict` 时检查目标路径、管理标记、文件身份和外部编辑哈希，不手工绕过覆盖保护。

## 9. 报告

提供 commit、系统、命令、前后端 URL、脱敏日志、预期/实际结果和已尝试步骤。安全问题按根 `SECURITY.md` 私密上报。
