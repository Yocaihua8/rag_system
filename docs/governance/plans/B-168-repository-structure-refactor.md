# B-168 仓库结构、文档体系与前后端运行时重构

> 状态：Active
> 创建时间：2026-08-01
> 创建方：Codex
> 关联 BACKLOG：B-168
> 关联功能文档：`docs/product/features/frontend-engineering.md`
> 关联设计文档：`docs/architecture/overview.md`、`docs/architecture/backend/api.md`

## 1. 目标

将仓库整理为职责清晰的后端、前端、桌面、集成、运维、工具、测试和文档分区；拆开前后端依赖、构建产物及运行时，通过显式 API base 与受限 CORS 通信。删除已失效的旧代码、历史文档、发布快照、DevLog、原型和旧工具计划，同时保持现有 HTTP 方法、字段、响应结构、SQLite Schema 与 Agent 权限白名单不变。

## 2. 前置条件

- 用户已明确确认本任务覆盖现有“禁止批量删除归档”的项目规则，删除内容仍可从 Git 历史恢复。
- 当前基线为 `main@05ba05a`，本地领先 `origin/main` 的 6 个 B-167 提交必须完整保留且不得重写。
- `runtime/`、`data/`、`.venv/`、`node_modules/`、`tmp/` 和用户 `.env` 不在历史清理范围内。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 建立 B-168 分支、BACKLOG 与执行 plan，锁定删除边界和冲突扫描结论
- [x] 分离后端入口、依赖、API-only 服务与受限 CORS，并补齐后端契约测试
- [x] 分离前端、npm workspace、E2E、Docker 与 Tauri 构建运行边界
- [x] 分类测试和工具，删除旧代码、可再生成产物及无引用 1.x 工具
- [x] 重构文档目录，回流有效 v2 事实，删除历史体系并新增 ADR-010
- [ ] 运行完整验证矩阵，清理 B-168 活动记录与 plan

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|-------------|---------|
| 后端 | `backend/`、根 `app.py`、根 requirements | 新增入口、迁移依赖、API-only、CORS、删除旧入口 |
| 前端 | `frontend/`、根 npm/Vite/Playwright 配置 | workspace 拆分、绝对 API URL、独立构建产物 |
| 桌面 | `src-tauri/` | 独立工具链、前端产物与 sidecar 边界、CSP |
| 运维 | `ops/docker/`、根 Docker/Compose 文件 | 双服务、双镜像、双健康检查、迁移脚本 |
| 测试 | `tests/`、`e2e/` | 按 backend/integration/repository/e2e 分类并更新契约 |
| 工具 | `tools/docs/`、`scripts/` | 文档工具迁移，删除失效 1.x 工具 |
| 历史 | `archive/`、`legacy/`、可再生成根目录产物 | 删除 |
| 文档 | `docs/`、`README.md`、`CHANGELOG.md`、`AGENTS.md`、`CONTRIBUTING.md` | 新目录体系、当前事实回流、治理规则更新 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 无前置 plan；B-167 已完成并保留其 6 个本地提交 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | 未发现状态为 Active 或 Interrupted 的任务 plan；`docs/superpowers/plans/` 仅含无状态历史文件 | N/A |

## 6. 完成标准

- [x] 后端以 `python -m backend` 启动，根路由 404，CORS、OPTIONS、SSE 与认证头契约通过
- [x] 前端通过 `VITE_API_BASE_URL` 使用绝对 API URL，并独立构建到 `frontend/dist/`
- [ ] Docker、Tauri、E2E 和 Obsidian 插件验证路径符合目标边界
- [ ] HTTP API、SQLite Schema 与 Agent 权限白名单未发生变化
- [x] 文档索引、元数据、链接、占位符、当前事实和根目录 allowlist 检查通过
- [ ] BACKLOG 仅保留未完成事项，B-168 完成事实写入 `CHANGELOG.md` 后移除活动条目

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 新仓库目录、启动和验证命令 | `README.md`、`docs/README.md`、`docs/operations/setup.md`、`docs/operations/testing.md` | [x] |
| API-only 运行时、CORS、端口与 Tauri 边界 | `docs/architecture/overview.md`、`docs/architecture/backend/api.md`、`docs/architecture/decisions/ADR-010-runtime-separation.md` | [x] |
| Docker 双服务与日常运维 | `docs/operations/docker.md`、`docs/operations/runbook.md` | [x] |
| 当前产品、功能、集成与发布边界 | `docs/product/`、`docs/integrations/`、`CHANGELOG.md` | [x] |
| 活动事项与治理生命周期 | `docs/BACKLOG.md`、`AGENTS.md`、`docs/governance/plans/README.md` | [x] |

## 8. 执行记录

- 用户已明确授权删除 `archive/src-desktop-legacy/`、`Git 历史`、`docs/release/`、`docs/previews/`、`docs/superpowers/`、旧 `docs/architecture/`、Archived 设计和 `.docs-template/`，因此本 plan 对相冲突的旧保护规则具有本任务内优先级。
- 不提供旧启动命令、旧 npm scripts 或根 Docker 路径的兼容壳。

## 9. 状态快照

- **最后更新**：2026-08-01
- **进度**：已完成 4 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`c7cdcbc` — `refactor: 分类测试工具并删除旧归档`
- **代码状态**：`refactor/repository-structure`；前后端运行时、旧归档清理、测试与文档工具分类均已分阶段提交，18 项仓库治理契约通过
- **下一步**：重构文档目录，回流有效 v2 事实，删除历史体系并新增 ADR-010
- **续任务须知**：保留 6 个未推送 B-167 提交；本任务不推送、不建 PR、不合并、不发布
