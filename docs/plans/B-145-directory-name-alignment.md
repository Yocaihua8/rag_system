# B-145 目录命名与当前 Web MVP 阶段对齐

> 状态：Active
> 创建时间：2026-05-28
> 创建方：Codex
> 关联 BACKLOG：B-145
> 关联功能文档：docs/features/fastapi-runtime.md, docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md

## 1. 目标

将仍带旧阶段含义的目录名对齐到当前 Web MVP 阶段，使后端包、前端工程、测试目录、legacy 桌面端和历史文档归档边界清晰。完成后默认运行时代码应位于 `backend/knowledge_island/`，Vue 源码仍位于 `frontend/`，legacy 桌面端位于 `legacy/desktop/`，历史架构与发布快照位于 `docs/archive/`。

## 2. 前置条件

- 已完成 B-143：legacy 静态前端 fallback 已移除。
- 已完成 B-144：后端已聚合到 `backend/`。
- 本任务不修改 `/api/*` 契约、SQLite schema、Agent 工具权限或检索/回答业务规则。

## 3. 任务拆解

- [x] 创建红灯测试，锁定 `backend/knowledge_island/`、新测试目录和 legacy/archive 目录边界。
- [x] 迁移后端包目录与测试目录命名，同步 import、Vite 输出、Docker 和构建提示。
- [x] 归档 legacy 桌面端与历史文档目录，同步 Docker/测试/脚本引用。
- [ ] 同步正式文档、运行验证、更新 BACKLOG 并删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `backend/webapp/` -> `backend/knowledge_island/` | 重命名 |
| 代码 | `src/` -> `legacy/desktop/` | 重命名 |
| 测试 | `tests/test_webapp/` -> `tests/backend/`, `tests/frontend/` | 重命名 / 拆分 |
| 配置 | `frontend/vite.config.js`, `Dockerfile`, `.gitignore`, `.dockerignore`, `compose.yaml` | 更新路径 |
| 文档 | `docs/architecture/`, `docs/release/` -> `docs/archive/architecture/`, `docs/archive/release/` | 归档 |
| 文档 | `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `docs/**/*.md`, `CHANGELOG.md` | 更新目录说明 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-143 与 B-144 已完成并删除对应 plan。 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md | 历史 legacy 桌面端 `src/desktop` 计划文件仍残留，但无 `状态：Active` / `Interrupted` 标记，且对应任务已不属于当前默认 Web MVP 入口。 | 视为历史残留；本 plan 只归档 legacy 目录名，不修改 legacy 业务行为。 |
| docs/superpowers/plans/2026-05-11-project-knowledge-points.md | 历史 legacy 六边形架构计划文件仍残留，但无 `状态：Active` / `Interrupted` 标记。 | 视为历史残留；本 plan 保持 legacy 回归测试可运行。 |
| docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md | 历史 legacy 模型计划文件仍残留，但无 `状态：Active` / `Interrupted` 标记。 | 视为历史残留；本 plan 不改 legacy domain/schema。 |

## 6. 完成标准

- [ ] 后端运行时代码目录为 `backend/knowledge_island/`，不存在被 import 使用的 `backend/webapp/`。
- [ ] Web MVP 测试目录不再使用 `tests/test_webapp/` 旧阶段命名。
- [ ] Legacy 桌面端代码位于 `legacy/desktop/`，历史文档位于 `docs/archive/`。
- [ ] Vite 构建、Docker 构建、Web MVP 测试和 legacy 回归测试通过。
- [ ] 正式文档已同步，BACKLOG B-145 状态为 `done`。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 当前目录结构与启动入口 | `AGENTS.md`, `README.md`, `docs/README.md` | [ ] |
| 后端包名、构建输出和 Docker 路径 | `docs/features/fastapi-runtime.md`, `docs/features/frontend-engineering.md`, `docs/guides/setup.md` | [ ] |
| 架构边界和 legacy/archive 归档说明 | `docs/design/architecture-overview.md`, `docs/design/system-design-overview.md` | [ ] |
| 测试命令与测试目录 | `docs/guides/testing.md` | [ ] |
| 任务完成记录 | `docs/BACKLOG.md`, `docs/devlog/2026-05-28.md`, `CHANGELOG.md` | [ ] |

## 8. 执行记录

- 2026-05-28：用户确认按当前 Web MVP 阶段统一目录命名；本任务只做路径和引用迁移，不改变业务契约。
- 2026-05-28：红灯验证命令 `.venv\Scripts\python.exe -m pytest tests\test_webapp\test_backend_layout.py tests\test_webapp\test_app_entrypoint.py tests\test_webapp\test_frontend_build.py::test_vite_config_builds_into_backend_knowledge_island_static_dist_and_proxies_api tests\test_webapp\test_docker_startup.py::test_dockerfile_runs_web_mvp_without_legacy_desktop_dependencies -q`，结果 6 failed / 2 passed；失败原因均为旧目录名仍存在或新目录/import/output 尚未落地。
- 2026-05-28：后端包迁移到 `backend/knowledge_island/`，Web MVP 测试目录拆为 `tests/backend/` 与 `tests/frontend/`；聚焦验证 `.venv\Scripts\python.exe -m pytest tests\backend\test_backend_layout.py::test_backend_runtime_is_grouped_under_backend_directory tests\backend\test_backend_layout.py::test_backend_app_import_exposes_fastapi_app tests\backend\test_backend_layout.py::test_backend_server_import_exposes_app_factory tests\backend\test_backend_layout.py::test_backend_runtime_dir_stays_under_project_root_runtime tests\backend\test_app_entrypoint.py tests\frontend\test_frontend_build.py::test_vite_config_builds_into_backend_knowledge_island_static_dist_and_proxies_api tests\backend\test_docker_startup.py::test_dockerfile_runs_web_mvp_without_legacy_desktop_dependencies -q`，7 passed。
- 2026-05-28：legacy 桌面端迁移到 `legacy/desktop/`，历史 `docs/architecture/` 与 `docs/release/` 归档到 `docs/archive/`；验证 `.venv\Scripts\python.exe -m pytest tests\test_application tests\test_domain tests\test_adapters -q`，179 passed；验证 `.venv\Scripts\python.exe -m pytest tests\test_desktop -q`，10 passed。

## 9. 状态快照

- **最后更新**：2026-05-28 00:00
- **进度**：已完成 3 / 4 项（见 § 3 勾选状态）
- **最新 commit**：待提交 — archive legacy desktop and historical docs
- **代码状态**：`fix/b-145-directory-naming`；代码目录已迁移，正式文档尚未全面同步
- **下一步**：同步正式文档、运行验证、更新 BACKLOG 并删除本 plan
- **续任务须知**：每完成 § 3 一项后按项目规则提交一次；不要修改 API 契约、数据库 schema 或 Agent 工具权限。
