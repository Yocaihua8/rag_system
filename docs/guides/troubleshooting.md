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
- 分块环境变量调整后资料没有变化：它们只在服务重启后的新导入、资料更新或缺失 chunk 回填时生效；已有 chunk 不会自动重建。
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

## 9. 备份脚本找不到数据库或恢复验证失败

- 默认脚本只读取仓库本地 `runtime/v2/app.db`；自定义 `RAG_RUNTIME_DIR` 时必须把对应 `<runtime>/app.db` 显式传给 `KI_DB_PATH`。
- Windows Git Bash 在线备份依赖 `cygpath -m` 把目标转换为 `sqlite3.exe` 可识别的路径；不要把 `/e/...` 等 POSIX 路径直接传给 SQLite dot-command。
- 缺少 `sqlite3` 时脚本会退回文件复制，必须先停止应用以避免复制运行中的数据库。
- SQLite 备份不包含 `runtime/v2/outputs/`、自定义输出目录或未显式声明的 Qdrant local 目录。
- 只在隔离目录恢复并检查 `PRAGMA integrity_check`、`data_generation=v2` 和样例数据；排障时不得覆盖活动 `app.db`。

## 10. 报告

提供 commit、系统、命令、前后端 URL、脱敏日志、预期/实际结果和已尝试步骤。安全问题按根 `SECURITY.md` 私密上报。
