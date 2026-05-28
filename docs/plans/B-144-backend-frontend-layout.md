# B-144 前后端目录结构解耦

> 状态：Active
> 创建时间：2026-05-28
> 创建方：Codex
> 关联 BACKLOG：B-144
> 关联功能文档：docs/features/fastapi-runtime.md, docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md

## 1. 目标

把 FastAPI 后端运行时代码从仓库根层级的 `webapp/` 聚合到 `backend/webapp/`，把默认启动入口迁移到 `backend/app.py`，使仓库形成清晰的 `backend/` 与 `frontend/` 双目录边界。迁移后不改变 `/api/*` HTTP 契约、不修改 SQLite schema、不调整 Agent 工具权限。

## 2. 前置条件

- 已完成 B-143，legacy `webapp/static/` fallback 已删除。
- 当前工作区 clean。
- 先读 `AGENTS.md`、`CONTRIBUTING.md`、`docs/BACKLOG.md`、`docs/plans/README.md`、`docs/features/fastapi-runtime.md`、`docs/features/frontend-engineering.md`、`docs/design/architecture-overview.md`。

## 3. 任务拆解

- [x] 建立目录解耦红灯测试，覆盖后端源码归属、Vite 输出、Docker 启动和 Python import 路径。
- [ ] 迁移后端目录与启动链路，更新 imports、Vite 构建输出、Docker COPY/CMD 和测试引用。
- [ ] 同步正式文档，更新 BACKLOG/CHANGELOG/devlog，完成全量验证并删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `app.py` -> `backend/app.py` | 移动默认启动入口 |
| 代码 | `webapp/` -> `backend/webapp/` | 移动 FastAPI 后端运行时代码 |
| 代码 | `frontend/vite.config.js` | 修改构建输出到后端静态目录 |
| 代码 | `Dockerfile` | 修改后端复制路径、构建产物复制路径和启动 import |
| 测试 | `tests/test_webapp/` | 修改 import 路径和新增目录边界断言 |
| 文档 | `AGENTS.md`, `CONTRIBUTING.md`, `README.md`, `docs/*`, `CHANGELOG.md` | 同步后端目录、启动命令和构建输出说明 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-143 已完成，当前无未完成主动 plan |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | 无冲突；`docs/plans/` 仅有模板和 README，`docs/superpowers/plans/` 为历史完成计划，无 Active/Interrupted 状态 |

## 6. 完成标准

- [ ] 后端源码位于 `backend/webapp/`，根目录不再保留生产 `webapp/` 包。
- [ ] 默认启动命令和 Docker 容器从 `backend.webapp.server` 运行。
- [ ] Vite 构建产物输出到 `backend/webapp/static_dist/`。
- [ ] Web MVP 测试、legacy 业务层回归、`npm run build`、Docker 配置检查通过。
- [ ] 相关文档已同步。
- [ ] BACKLOG 条目 B-144 状态已更新为 `done`。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 后端目录改为 `backend/webapp/`，启动入口为 `backend/app.py` | `AGENTS.md`, `CONTRIBUTING.md`, `README.md`, `docs/guides/setup.md`, `docs/features/fastapi-runtime.md` | [ ] |
| 前端构建输出改为 `backend/webapp/static_dist/` | `docs/features/frontend-engineering.md`, `docs/guides/testing.md`, `docs/design/architecture-overview.md` | [ ] |
| B-144 完成记录和对外变更 | `docs/BACKLOG.md`, `docs/devlog/2026-05-28.md`, `CHANGELOG.md` | [ ] |

## 8. 执行记录

- 2026-05-28：用户确认 B-143 后继续处理前后端目录混用问题；将目录迁移拆为 B-144，不并入 B-143。

## 9. 状态快照

- **最后更新**：2026-05-28 15:40
- **进度**：已完成 1 / 3 项（见 § 3 勾选状态）
- **最新 commit**：`待本次提交生成` — 红灯测试覆盖 backend 目录、Vite 输出与 Docker 启动路径
- **代码状态**：fix/b-142-vue-workbench-sse-sessions；有未提交红灯测试和 plan 更新
- **下一步**：迁移后端目录与启动链路，更新 imports、Vite 构建输出、Docker COPY/CMD 和测试引用
- **续任务须知**：红灯命令为 `.venv\Scripts\python.exe -m pytest tests\test_webapp\test_backend_layout.py tests\test_webapp\test_app_entrypoint.py tests\test_webapp\test_frontend_build.py::test_vite_config_builds_into_backend_webapp_static_dist_and_proxies_api tests\test_webapp\test_docker_startup.py::test_dockerfile_runs_web_mvp_without_legacy_desktop_dependencies -q`，当前 6 failed，失败原因均为旧目录结构。
