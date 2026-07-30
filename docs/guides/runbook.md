# 运维手册 Runbook

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：Knowledge Island 本地 Web、Docker 自托管实例的启动、检查、停止与故障升级
> Related：`setup.md`、`release-process.md`、`troubleshooting.md`、`security.md`、`../../ops/README.md`、`../design/architecture-overview.md`

Knowledge Island 默认是本地单用户应用，不存在已确认的生产值班、监控或自动回滚平台。本手册只记录当前仓库可验证的操作；涉及数据的命令必须先确认实际运行目录。

## 1. 服务清单

| 服务 | 角色 | 运行位置 | 健康检查 | Owner |
|------|------|----------|----------|-------|
| FastAPI / Uvicorn Web | 当前 Web、API 和静态前端入口 | 本机 `127.0.0.1:8765`，由 `app.py` 启动 | `GET http://127.0.0.1:8765/api/health` | RAG 团队 |
| Compose `web` | Docker 自托管入口 | 容器内 `0.0.0.0:8765`；宿主机映射为 `${KI_PORT:-8765}:8765`，当前未限定宿主机 IP | 同上；Compose 也调用该路径 | RAG 团队 |
| SQLite | 应用数据存储 | 本机默认 `runtime/v2/app.db`；Docker 为 `ki-runtime` volume 内 `/app/runtime/app.db` | 无独立 readiness 检查 | RAG 团队 |
| 外部 LLM / Embedding Provider | 可选问答与向量服务 | 由本地环境变量配置的第三方服务 | 无统一健康检查 | 第三方服务 Owner；本项目配置 Owner 为 RAG 团队 |

`/api/health` 当前只返回 `{"status":"ok"}`，只能证明 HTTP 进程可响应；它不检查 SQLite 可读写、模型凭证、外部 Provider、磁盘空间或完整问答链路。

## 2. 常用入口

| 名称 | 当前入口 |
|------|----------|
| 本地应用 | `http://127.0.0.1:8765` |
| FastAPI 文档 | `http://127.0.0.1:8765/docs`；认证启用时需要凭证 |
| CI | `https://github.com/Yocaihua8/rag_system/actions` |
| 发布记录 | `https://github.com/Yocaihua8/rag_system/releases` |
| 独立监控面板 | N/A；仓库未配置 |
| 集中日志查询 | N/A；本地启动查看当前终端输出，Docker 使用 `docker compose logs` |
| 告警配置 | N/A；仓库未配置 |
| 错误追踪平台 | N/A；仓库未配置 |
| 值班或紧急联系人 | TBD |

## 3. 启动、检查与停止

### 3.1 本地 Windows 启动

从仓库根目录执行：

```powershell
.venv\Scripts\python.exe app.py
```

另开终端检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/health
Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
```

预期健康响应的 `status` 为 `ok`。完成导入和来源约束问答的最小冒烟前，不能据此判定业务就绪。

停止方式：在启动进程所在终端按 `Ctrl+C`。仓库没有本地 Web 进程管理器或自动重启服务。

### 3.2 Docker 启动

```powershell
docker compose --project-directory . -f compose.yaml config
docker compose --project-directory . -f compose.yaml up --build -d
docker compose --project-directory . -f compose.yaml ps
docker compose --project-directory . -f compose.yaml logs --tail 200 web
```

检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/health
```

停止容器但保留命名 volume：

```powershell
docker compose --project-directory . -f compose.yaml down
```

不要附加 `-v`，除非已经确认要删除 `ki-runtime` 持久数据并完成了可验证的备份。

### 3.3 回滚边界

当前没有自动部署、镜像仓库回滚或数据库跨代回滚机制。源码版本回退只能在保留当前工作区和数据后，按 `release-process.md` 选择已知 Tag 重新构建。

- `v2.0.0` 正式 Tag / Release 已存在。
- 回退源码前先单独保存 `runtime/v2/` 或实际 `RAG_RUNTIME_DIR`。
- 不得让回退版本覆盖 `runtime/app.db`、`runtime/webapp/knowledge_island.db` 或 `runtime/v2/app.db`。
- 未验证旧版本与当前数据库兼容性时，应使用隔离的数据目录启动，不得直接复用现有数据库。

## 4. 数据备份与恢复边界

### 4.1 当前已知路径

| 场景 | 数据位置 |
|------|----------|
| 本地默认 v2 | `runtime/v2/app.db`，向量目录派生于 `runtime/v2/vectors/` |
| 显式配置 | `RAG_RUNTIME_DIR` 下的 `app.db` 和相关子目录 |
| Docker | `ki-runtime` volume 内 `/app/runtime/app.db` |
| 1.x 历史数据 | `runtime/app.db`、`runtime/webapp/knowledge_island.db` 等；不得自动迁移或覆盖 |

### 4.2 备份脚本路径漂移风险

`ops/scripts/backup_db.sh` 当前默认值仍是 `runtime/webapp/knowledge_island.db`，与 v2 默认 `runtime/v2/app.db` 不一致。`ops/README.md` 中的无参数示例因此不能作为 v2 安全备份证明。

- 在修复脚本默认值并完成恢复演练前，不要把无参数运行该脚本当作有效 v2 备份。
- 即使显式传入 `KI_DB_PATH`，也必须确认应用是否已停止、输出文件是否可打开、所需向量数据是否一并保存。
- 脚本缺少 `sqlite3` 时会退回文件复制，并明确要求停止应用才能获得一致副本。
- 当前没有从该脚本产物恢复 v2 环境的自动化验证记录，因此本手册不提供“已验证安全”的恢复命令。
- 项目导出 / 恢复 API 会把备份恢复成新项目空间，不等同于整库灾难恢复。

## 5. 故障响应

### 5.1 HTTP 无法访问

1. 执行 `Get-NetTCPConnection -LocalPort 8765 -ErrorAction SilentlyContinue`，确认端口是否监听。
2. 本地运行时查看启动终端的最后一条异常；Docker 运行时执行 `docker compose -f compose.yaml logs --tail 200 web`。
3. 确认当前命令在仓库根目录执行，Python 虚拟环境依赖已安装。
4. 确认端口未被其他进程占用，再按 § 3 重启。
5. 仍无法恢复时按 `troubleshooting.md` 收集版本、命令和完整错误信息。

### 5.2 健康检查正常但问答失败

1. 不把 `/api/health` 的成功当作 Provider 或数据库就绪。
2. 查看启动终端或 Docker 日志中的具体 HTTP 状态和 Provider 错误，但不要复制或输出 API Key。
3. 只检查凭证环境变量是否存在，不打印其值。
4. 使用本地文档完成“导入 → 检索 / 问答 → 来源展示”最小冒烟。
5. 若第三方 Provider 不可用，记录服务、时间范围、模型配置名称和脱敏错误；第三方恢复时间为 N/A。

### 5.3 v2 数据代际拒绝启动

1. 检查是否把 `RAG_RUNTIME_DIR` 指向了 1.x 非空数据库目录。
2. 恢复默认 `runtime/v2/` 或创建隔离的空 v2 目录。
3. 不删除、改写或自动迁移旧数据库。
4. 需要旧数据时按产品当前支持的重新导入或项目导出 / 恢复能力处理，不能直接替换数据库文件。

## 6. 容量、监控与值班

| 项目 | 当前状态 | 阈值 / SLA | 处置 |
|------|----------|------------|------|
| 本地磁盘 | 由用户主机管理 | TBD；无自动告警 | 定期检查 `runtime/v2/` 或 Docker volume 大小，空间不足前停止写入并保存数据 |
| SQLite 大小 | 无独立监控 | TBD | 记录数据库大小和增长来源，不在运行中直接删除表或文件 |
| 外部 Provider 限额 | 由第三方账户管理 | N/A | 查看第三方控制台；本项目不承诺配额或恢复时间 |
| 自动扩缩容 | N/A | N/A | 当前是本地单实例应用 |
| 7×24 值班 | N/A | 无承诺 SLA | 紧急联系人和交接制度为 TBD |

如未来建立长期运行环境、监控或值班机制，必须先补充实际监控链接、告警阈值、负责人和经过演练的处置步骤。

## 7. 交接记录模板

```markdown
日期：YYYY-MM-DD
交班人：TBD
接班人：TBD
版本 / commit：
运行方式：本地 / Docker
实际数据目录：

### 进行中问题
- 问题、影响、负责人、下一步

### 待观察
- 指标或现象、观察条件

### 本次已处理
- 实际执行命令、结果、未覆盖边界
```
