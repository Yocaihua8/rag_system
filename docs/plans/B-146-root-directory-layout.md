# B-146 根目录结构收敛

> 状态：Active
> 创建时间：2026-05-28
> 创建方：Codex
> 关联 BACKLOG：B-146
> 关联功能文档：docs/features/fastapi-runtime.md, docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md

## 1. 目标

将根目录中仍混放的前端构建文件、Docker 运维入口和文档映射移动到现阶段职责目录，使根目录只保留项目说明、协作规则、依赖清单、环境模板和少量标准工具入口。完成后，前端 npm 配置位于 `frontend/`，Docker 运行入口位于 `ops/docker/`，文档映射位于 `docs/`，正式文档和测试命令全部同步。

## 2. 前置条件

- 已完成 B-145：后端包、测试目录、legacy 桌面端和历史文档目录命名已对齐。
- 本任务不修改 `/api/*` 契约、SQLite schema、Agent 工具权限或检索/回答业务规则。
- 本任务不删除 `.venv/`、`node_modules/`、`runtime/`、`release/`、`release-cache/` 等本地生成目录。

## 3. 任务拆解

- [ ] 创建红灯测试，锁定根目录新布局、前端 npm 配置位置、Docker 入口位置和 quickstart 文档位置。
- [ ] 移动前端 npm 配置、Docker 运维入口和文档映射文件，同步脚本路径、构建路径和 Docker Compose 路径。
- [ ] 同步正式文档、发布说明、测试指南和 devlog，更新 BACKLOG 并删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 配置 | `package.json`, `package-lock.json`, `vite.config.js` | 移动到 `frontend/` / 删除根 shim |
| 配置 | `Dockerfile`, `compose.yaml` | 移动到 `ops/docker/` |
| 脚本 | `Start-KnowledgeIsland-Docker.bat`, `Stop-KnowledgeIsland-Docker.bat`, `scripts/docker_up.ps1`, `scripts/docker_down.ps1` | 移动到 `ops/docker/` 并更新相对路径 |
| 文档 | `README-Docker-Quickstart.txt`, `template-mapping.md` | 移动到 `docs/guides/` 与 `docs/` |
| 测试 | `tests/backend/test_docker_startup.py`, `tests/frontend/test_frontend_build.py` | 更新路径断言 |
| 文档 | `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `docs/**/*.md`, `CHANGELOG.md` | 更新启动、构建、Docker 和目录说明 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-145 已完成并删除对应 plan。 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | 冲突扫描仅命中 `docs/plans/README.md` 的目录说明，不是活动任务 plan。 | N/A |

## 6. 完成标准

- [ ] 根目录不再包含前端 npm 配置、Vite shim、Dockerfile、Compose、Docker 双击脚本、Docker quickstart 和模板映射文件。
- [ ] `frontend/` 可独立承载 npm 配置，`npm --prefix frontend run build` 可生成 `backend/knowledge_island/static_dist/`。
- [ ] `ops/docker/` 承载 Dockerfile、Compose、PowerShell 脚本和双击包装入口，Docker 配置与镜像构建通过。
- [ ] Web MVP 后端/前端测试和 legacy 回归测试通过。
- [ ] 正式文档已同步，BACKLOG B-146 状态为 `done`。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 根目录职责、前端和 Docker 文件新位置 | `AGENTS.md`, `README.md`, `docs/README.md`, `docs/design/architecture-overview.md` | [ ] |
| 构建、启动、Docker 和发布命令 | `docs/guides/setup.md`, `docs/guides/testing.md`, `docs/guides/release-process.md`, `README.md`, `CONTRIBUTING.md` | [ ] |
| 前端工程与 FastAPI 静态服务路径 | `docs/features/frontend-engineering.md`, `docs/features/fastapi-runtime.md` | [ ] |
| 任务完成记录 | `docs/BACKLOG.md`, `docs/devlog/2026-05-28.md`, `CHANGELOG.md` | [ ] |

## 8. 执行记录

- 2026-05-28：用户确认执行根目录结构收敛；本任务只做文件位置、脚本路径、测试和文档同步，不改变业务契约。

## 9. 状态快照

- **最后更新**：2026-05-28 00:00
- **进度**：已完成 0 / 3 项（见 § 3 勾选状态）
- **最新 commit**：待提交 — 启动 B-146 根目录结构收敛计划
- **代码状态**：`fix/b-146-root-layout`；仅创建 BACKLOG/plan，尚未移动文件
- **下一步**：创建红灯测试，锁定根目录新布局、前端 npm 配置位置、Docker 入口位置和 quickstart 文档位置
- **续任务须知**：每完成 § 3 一项后按项目规则提交一次；不要修改 API 契约、数据库 schema 或 Agent 工具权限。
