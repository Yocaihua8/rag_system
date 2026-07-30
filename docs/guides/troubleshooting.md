# 故障排查

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：Knowledge Island 本地 Web、Docker、认证、v2 数据路径和模型调用的常见故障排查
> Related：`runbook.md`、`support-policy.md`、`setup.md`、`security.md`、`../design/api-spec.md`、`../design/database-design.md`

本文档只包含当前仓库可执行或可核对的排查步骤。所有命令默认从仓库根目录运行；涉及数据库、volume 或凭证时先确认目标，禁止通过删除文件来“验证”问题。

## 1. 使用方式

1. 记录版本、运行方式、发生时间、现象和影响范围。
2. 先执行只读检查，再决定是否重启或改变配置。
3. 本地运行查看启动终端；Docker 运行查看 Compose 状态和日志。
4. 不在日志、截图、Issue 或聊天中粘贴 API Key、JWT secret、Bearer Token 或私密文档。
5. `/api/health` 只验证 HTTP 活性；成功不等于 SQLite、外部 Provider 或完整问答链路就绪。
6. 无法闭环时按 § 9 收集脱敏信息并升级。

## 2. 快速分级

| 级别 | 判断标准 | 处理时限 | 升级对象 |
|------|----------|----------|----------|
| P0 | 可利用安全问题、明确数据破坏风险、主流程完全不可用 | TBD；无承诺 SLA，发现后尽快限制影响 | 安全负责人 TBD / RAG 团队 |
| P1 | 导入、检索、问答或当前发布安装链路的重要功能不可用 | TBD；无承诺 SLA | RAG 团队 |
| P2 | 局部异常且有规避方式 | TBD；无承诺 SLA | RAG 团队 / BACKLOG |
| P3 | 咨询、文档或低风险体验问题 | TBD；无承诺 SLA | GitHub Issue |

## 3. 本地服务无法访问

**现象**

- 浏览器无法打开 `http://127.0.0.1:8765`。
- `Invoke-RestMethod` 返回连接失败。
- 启动终端立即退出。

**只读检查**

```powershell
Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue
Get-Process python -ErrorAction SilentlyContinue
Test-Path .venv\Scripts\python.exe
.venv\Scripts\python.exe --version
```

如果端口已经由其他进程监听，先识别进程，不要直接终止未知进程：

```powershell
Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue |
  Select-Object LocalAddress, LocalPort, State, OwningProcess
```

**处理步骤**

1. 确认当前目录是仓库根目录，且 `.venv` 依赖已按 `setup.md` 安装。
2. 在可观察终端中启动：

   ```powershell
   .venv\Scripts\python.exe app.py
   ```

3. 保留终端中的完整异常文本，不要只记录“启动失败”。
4. 另开终端检查：

   ```powershell
   Invoke-RestMethod http://127.0.0.1:8765/api/health
   ```

**验证**

- HTTP 返回对象的 `status` 为 `ok`。
- 浏览器能打开首页。
- 再完成一次隔离测试项目的导入与来源约束问答，才能确认核心业务可用。

## 4. 启动时提示数据代际或数据库不兼容

**现象**

- 应用在建表或初始化前拒绝启动。
- 错误提示当前数据库没有 v2 数据代际标记或目录不兼容。

**可能原因**

- `RAG_RUNTIME_DIR` 指向 1.x 的 `runtime/` 或其他非空旧数据库目录。
- 将 `runtime/app.db` 或 `runtime/webapp/knowledge_island.db` 复制成了 v2 `app.db`。
- Docker volume 或自定义数据目录来自旧版本。

**只读检查**

```powershell
Get-Item Env:RAG_RUNTIME_DIR -ErrorAction SilentlyContinue
Test-Path runtime\v2\app.db
Test-Path runtime\app.db
Test-Path runtime\webapp\knowledge_island.db
Get-Item runtime\v2\app.db -ErrorAction SilentlyContinue |
  Select-Object FullName, Length, LastWriteTime
```

**处理步骤**

1. 停止应用，保留当前所有数据库和向量目录。
2. 移除错误的 `RAG_RUNTIME_DIR` 会话配置，或把它改为一个独立、明确的 v2 目录；不要指向 1.x 数据。
3. 不删除、不覆盖、不原地升级旧数据库。
4. 旧项目内容需要进入 v2 时，使用当前支持的重新导入或项目导出 / 恢复流程。
5. 如果必须进行数据库级迁移，先建立独立 BACKLOG / plan 和迁移文档，不在排障过程中修改 Schema。

**验证**

- 应用使用默认 `runtime/v2/app.db` 或已确认的隔离 v2 目录启动。
- 旧 `runtime/app.db`、`runtime/webapp/knowledge_island.db` 的大小和修改时间未变化。

## 5. Docker 容器未启动或不健康

**只读检查**

```powershell
docker compose --project-directory . -f compose.yaml config
docker compose --project-directory . -f compose.yaml ps
docker compose --project-directory . -f compose.yaml logs --tail 200 web
docker compose --project-directory . -f compose.yaml port web 8765
```

**常见原因**

| 信号 | 可能原因 | 处理 |
|------|----------|------|
| 镜像构建失败 | 网络、npm / pip 依赖或 Docker daemon 问题 | 保留失败步骤和日志，先修复依赖或 daemon |
| 宿主机端口冲突 | 8765 已被本地 Python 或其他服务占用 | 识别 Owner 后停止自己启动的重复实例，或显式选择其他 `KI_PORT` |
| Provider 配置错误 | 模型 Key / Base URL / Model 不匹配 | 只核对变量存在性和非敏感配置，不打印 Key |
| health 为 healthy 但问答失败 | `/api/health` 不检查 SQLite 或 Provider | 转到 § 7 做核心流程排查 |

重新启动：

```powershell
docker compose --project-directory . -f compose.yaml up --build -d
docker compose --project-directory . -f compose.yaml ps
```

停止但保留 volume：

```powershell
docker compose --project-directory . -f compose.yaml down
```

不要使用 `down -v` 处理普通启动故障；该参数会删除 `ki-runtime` volume。

**网络提醒**

当前 Compose 端口写法没有限定宿主机 IP。`docker compose port web 8765` 只显示映射，仍需结合操作系统防火墙确认是否被局域网访问；暴露到非可信网络时必须启用认证并配置受控 TLS 边界。

## 6. API 返回 401

**现象**

- `/api/projects`、`/docs` 或其他受保护接口返回 `{"error":"authentication required"}` 或 `{"error":"invalid credentials"}`。
- `/api/health` 仍然成功。

**只读检查**

只检查是否配置，不输出敏感值：

```powershell
$env:RAG_AUTH_ENABLED
[bool]$env:RAG_AUTH_API_KEY
[bool]$env:RAG_AUTH_JWT_SECRET
$env:RAG_AUTH_JWT_TTL_SECONDS
```

**处理步骤**

1. 确认是否有意启用 `RAG_AUTH_ENABLED=1`。
2. 启用认证时，确认 API Key 和 JWT secret 都存在；缺少任一项会导致启动配置错误。
3. 调用受保护 API 时使用正确的 `X-API-Key` 或 `Authorization: Bearer <jwt>`，不要把凭证写入脚本仓库或命令历史示例。
4. JWT 过期后重新通过 `POST /api/auth/token` 换取；当前没有 Refresh Token。
5. 如果密钥可能泄漏，轮换 API Key 与 JWT secret 并重启服务；当前没有服务端 Token 撤销列表。

**验证**

- `/api/health` 无凭证仍返回 200。
- 受保护接口无凭证返回 401。
- 携带有效凭证的受保护接口返回其正常业务响应。

## 7. 健康检查正常但导入、检索或问答失败

**排查顺序**

1. 明确失败环节：项目创建、文件读取、正文抽取、分块、向量、检索、LLM 调用或 SSE 渲染。
2. 查看启动终端或 Docker 日志中的脱敏错误。
3. 核对实际数据目录：

   ```powershell
   Get-Item Env:RAG_RUNTIME_DIR -ErrorAction SilentlyContinue
   Get-Item runtime\v2\app.db -ErrorAction SilentlyContinue |
     Select-Object FullName, Length, LastWriteTime
   ```

4. 核对 Provider 名称、Base URL 和 Model；只判断 API Key 是否存在，不显示值。
5. 使用一份非敏感的小型 `.md` 或 `.txt` 文件创建隔离项目，复现“导入 → 问答 → 来源展示”。
6. PDF 解析失败时确认可选 `pymupdf` 是否安装；中文关键词质量异常时确认可选 `jieba`，不要把可选依赖缺失误判为数据库故障。
7. 只有确定索引损坏且数据已保护时，才评估 `POST /api/admin/rebuild-index`；该操作会重建 chunk 和向量，不应作为第一排障步骤。

**Provider 边界**

- 第三方 LLM / Embedding 服务的状态、配额和内容政策不由本项目控制。
- Provider 错误报告应包含脱敏状态码、模型名和时间范围，不包含请求正文或 Key。
- `/api/health` 不会提前发现 Provider 故障。

## 8. 备份脚本找不到数据库或备份内容不确定

**已知原因**

`ops/scripts/backup_db.sh` 当前默认数据库路径为 `runtime/webapp/knowledge_island.db`，但 v2 本地默认路径是 `runtime/v2/app.db`。这是已确认的路径漂移。

**安全边界**

- 不要反复无参数运行脚本，也不要因为“生成了文件”就认定 v2 已备份。
- 在脚本默认值修复并完成恢复演练前，本项目不能声称该脚本是安全的 v2 灾备流程。
- 即使显式设置 `KI_DB_PATH`，也要先确认实际 `RAG_RUNTIME_DIR`；未安装 `sqlite3` 时脚本退回文件复制，运行中的数据库副本可能不一致。
- 脚本对 Qdrant 目录的打包依赖显式路径，未配置时不会自动证明向量数据已备份。
- 项目导出 / 恢复接口恢复为新项目空间，不是整库恢复替代品。

**只读核对**

```powershell
Get-Item Env:RAG_RUNTIME_DIR -ErrorAction SilentlyContinue
Get-Item runtime\v2\app.db -ErrorAction SilentlyContinue |
  Select-Object FullName, Length, LastWriteTime
Select-String -Path ops\scripts\backup_db.sh -Pattern 'DB_PATH='
```

需要灾备时，应先创建专门任务修正路径、定义停机 / 在线备份策略，并在隔离目录实际演练恢复。排障过程不得直接覆盖现有 `app.db`。

## 9. 收集信息与升级

无法本地闭环时，至少收集：

- 时间范围和时区。
- 版本号或 commit：

  ```powershell
  git rev-parse --short HEAD
  git status --short
  ```

- 运行方式：本地 Web、Docker、Tauri 或 Obsidian Bridge。
- 操作系统与相关工具版本：

  ```powershell
  python --version
  node --version
  docker version
  ```

  Docker 未安装或未运行时，将该项记为 N/A。

- 实际 `RAG_RUNTIME_DIR` 是否设置；不要附数据库文件本身，除非已确认传输方式和数据权限。
- 脱敏错误日志、HTTP 状态和最小复现步骤。
- 已尝试的只读检查与处理结果。
- 是否能在隔离数据目录和非敏感样例中复现。
- Request ID / Trace ID：N/A；当前没有统一追踪 ID。

升级入口：

| 条件 | 升级给谁 | 需要附带的信息 |
|------|----------|----------------|
| 可复现的一般缺陷 | GitHub Issue / RAG 团队 | 版本、环境、步骤、脱敏错误、影响范围 |
| 可利用安全问题或凭证泄漏 | 安全负责人 TBD；不要公开细节 | 私密报告、影响版本、泄漏范围、临时限制措施 |
| 数据损坏或恢复需求 | RAG 团队 | 实际数据目录、应用是否已停止、备份来源、文件哈希 |
| 第三方 Provider 故障 | 对应 Provider 支持；本项目记录集成影响 | 脱敏状态码、模型名、时间范围，不含文档正文或 Key |

## 10. 防复发回流

- 可修复缺陷或技术债：创建或更新 `../BACKLOG.md` 条目。
- 需要独立架构决策：按项目规则创建 RFC / ADR。
- 造成较大影响并需要根因分析：基于 `../devlog/postmortem-template.md` 创建单独复盘。
- 稳定、可重复的排查步骤：更新本文件或 `runbook.md`。
- 接口、数据、认证或发布边界变化：同步对应设计和指南文档。
