# B-141 Vue 3 + Vite Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first Vue 3 + Vite frontend foundation while keeping the current Web MVP API and legacy static UI compatible.

**Architecture:** `frontend/` owns the new Vue source and Vite config. Vite production builds into `webapp/static_dist/`; `webapp/server.py` serves that build when present and falls back to `webapp/static/` during migration. Existing `webapp/static/` business UI remains untouched in B-141A.

**Tech Stack:** Vue 3, Vite, npm, FastAPI `StaticFiles`, pytest.

---

> 状态：Active
> 创建时间：2026-05-26
> 创建方：Codex
> 关联 BACKLOG：B-141
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/adr/ADR-006-vue-vite-frontend.md, docs/design/architecture-overview.md, docs/guides/setup.md, docs/guides/testing.md

## 1. 目标

完成 B-141A：建立 Vue 3 + Vite 前端工程骨架，打通 npm 安装、生产构建、FastAPI 托管构建产物和 legacy fallback。完成后系统仍能通过 `python app.py` 使用当前 Web MVP；完整业务 UI 迁移留到 B-141B/B-141C。

## 2. 前置条件

- 已完成 B-139 FastAPI 运行时迁移。
- 已完成 B-140 可选认证中间件。
- 已确认 B-141 采用分片实施：先工程骨架，不迁移完整业务 UI。
- 已用 ctx7 查询 Vite 当前文档，确认 dev server proxy、`build.outDir`、`base` 和 backend integration 配置方式。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [x] 创建 ADR-006、前端工程化功能文档、B-141 plan，并将 BACKLOG 状态更新为 `doing`
- [ ] 先写前端工程骨架红灯测试，覆盖 `frontend/package.json`、Vite 配置、构建输出目录和后端静态 fallback 预期
- [ ] 新建 `frontend/` Vue 3 + Vite 最小工程与根 `package.json` / `package-lock.json`
- [ ] 修改 `webapp/server.py`，优先服务 `webapp/static_dist/`，缺失时回退 `webapp/static/`
- [ ] 同步架构、setup、testing、CHANGELOG、devlog 中的 B-141A 说明
- [ ] 运行 npm 构建、Web MVP 聚焦测试、legacy 回归和空白检查
- [ ] 更新 plan 状态快照，保留 B-141 为 `doing`，下一步指向 B-141B

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 前端 | `frontend/` | 新增 Vue 3 + Vite 工程骨架 |
| 前端 | `package.json`, `package-lock.json` | 新增 npm 脚本和依赖锁定 |
| 后端 | `webapp/server.py` | 修改静态目录选择逻辑 |
| 测试 | `tests/test_webapp/test_frontend_build.py` | 新增前端工程和静态服务测试 |
| 文档 | `docs/adr/ADR-006-vue-vite-frontend.md` | 新增前端选型 ADR |
| 文档 | `docs/features/frontend-engineering.md` | 新增前端工程化功能边界 |
| 文档 | `docs/design/architecture-overview.md` | 修改技术栈与静态服务说明 |
| 文档 | `docs/guides/setup.md`, `docs/guides/testing.md` | 修改 npm 构建和测试命令 |
| 文档 | `CHANGELOG.md`, `docs/devlog/2026-05-26.md` | 记录 B-141A 实施结果 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-139/B-140 已完成并删除对应 plan，B-141A 可基于当前 FastAPI + auth 状态继续 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/superpowers/plans/2026-05-11-project-knowledge-base-ui-skeleton.md` | 历史 desktop/UI 文档计划，未标记 Active，不修改 `frontend/` 或 `webapp/server.py` | 分区：B-141A 只处理 Web 前端工程骨架 |
| `docs/superpowers/plans/2026-05-11-project-knowledge-points.md` | 历史 src/application 与文档计划，未标记 Active | 分区：B-141A 不修改 legacy `src/` |
| `docs/superpowers/plans/2026-05-16-knowledge-island-core-models.md` | 历史 core model/schema 计划，未标记 Active | 分区：B-141A 不修改数据库 schema |

## 6. 完成标准

- [ ] `frontend/` 最小 Vue 应用可构建。
- [ ] `npm run build` 输出到 `webapp/static_dist/`。
- [ ] 构建产物存在时 FastAPI 首页来自 `static_dist`。
- [ ] 构建产物不存在时 FastAPI 首页回退 `webapp/static/`。
- [ ] `webapp/static/` 未在 B-141A 删除。
- [ ] 文档明确 B-141A 不是完整业务 UI 迁移。
- [ ] B-141 在 BACKLOG 中保持 `doing`，等待 B-141B/B-141C。

## 7. 回流清单

删除或中断本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 前端框架选型和回滚策略 | `docs/adr/ADR-006-vue-vite-frontend.md` | [x] |
| B-141A 功能边界 | `docs/features/frontend-engineering.md` | [x] |
| 技术栈与静态服务策略 | `docs/design/architecture-overview.md` | [ ] |
| npm 安装和构建步骤 | `docs/guides/setup.md` | [ ] |
| 前端构建测试命令 | `docs/guides/testing.md` | [ ] |
| 对外变更摘要 | `CHANGELOG.md` | [ ] |
| 实施记录 | `docs/devlog/2026-05-26.md` | [ ] |

## 8. 执行记录

- 2026-05-26 16:17：用户确认采用 B-141A 低风险分片方案：先创建 ADR-006、B-141 plan 和 Vue/Vite 骨架，不迁移完整业务 UI。
- 2026-05-26 16:17：冲突扫描发现 `docs/plans/` 无进行中计划；`docs/superpowers/plans/` 只有历史计划文件且未标记 Active/Interrupted，按分区处理。
- 2026-05-26 16:17：创建 ADR-006、`docs/features/frontend-engineering.md` 和 `docs/plans/B-141-vue-vite-foundation.md`，并将 BACKLOG B-141 状态切为 `doing`。

## 9. 状态快照

- **最后更新**：2026-05-26 16:17
- **进度**：已完成 1 / 7 项（见 § 3 勾选状态）
- **最新 commit**：`680e9a5` — docs: 创建 B-141 前端工程化计划
- **代码状态**：分支 `fix/url-virtual-source-preserve`；存在大量既有未提交改动；B-141A 将只追加前端工程化相关变更
- **下一步**：先写前端工程骨架红灯测试，覆盖 `frontend/package.json`、Vite 配置、构建输出目录和后端静态 fallback 预期
- **续任务须知**：B-141A 不删除 `webapp/static/`，不迁移完整业务 UI，不修改数据库 schema
