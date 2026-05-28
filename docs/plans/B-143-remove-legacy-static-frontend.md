# B-143 移除 legacy 静态前端 fallback

> 状态：Active
> 创建时间：2026-05-28
> 创建方：Codex
> 关联 BACKLOG：B-143
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：docs/design/architecture-overview.md, docs/features/fastapi-runtime.md

## 1. 目标

移除 `webapp/static/` 原生 HTML/CSS/JS 前端，FastAPI 只服务 Vue/Vite 生产构建产物 `webapp/static_dist/`。构建产物缺失时不再回退到 legacy UI，而是给出明确的构建提示，避免继续维护两套前端入口。

## 2. 前置条件

- `AGENTS.md`
- `CONTRIBUTING.md`
- `docs/README.md`
- `docs/BACKLOG.md`
- `docs/features/frontend-engineering.md`
- `docs/guides/setup.md`
- `docs/guides/testing.md`
- `tests/test_webapp/test_frontend_build.py`
- `tests/test_webapp/test_fastapi_server.py`

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。

- [ ] 用测试锁定新的静态服务策略：存在 `static_dist/index.html` 时服务 Vue 构建；缺失时返回构建提示；不再读取 legacy 静态目录。
- [ ] 调整 `webapp/server.py` 并删除 `webapp/static/` legacy 原生前端文件。
- [ ] 清理仅针对 legacy 静态前端的测试断言，保留 Vue 源码和构建链测试。
- [ ] 同步前端工程、运行时、启动和测试文档，完成 BACKLOG 回流并删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `webapp/server.py` | 修改：移除 legacy fallback，构建缺失时返回明确提示 |
| 代码 | `webapp/static/` | 删除：legacy 原生 HTML/CSS/JS 前端 |
| 测试 | `tests/test_webapp/test_frontend_build.py` | 修改：覆盖无 fallback 的静态服务策略 |
| 测试 | `tests/test_webapp/test_fastapi_server.py` | 修改：根页面测试改为基于临时 Vue 构建产物 |
| 测试 | `tests/test_webapp/test_frontend_static.py` | 删除或清空：legacy 静态前端断言不再适用 |
| 文档 | `docs/features/frontend-engineering.md` | 修改：说明 B-143 后仅保留 Vue 构建入口 |
| 文档 | `docs/guides/setup.md` | 修改：启动前需执行 `npm run build` |
| 文档 | `docs/guides/testing.md` | 修改：移除 legacy `webapp/static/js` 校验要求 |
| 文档 | `docs/design/architecture-overview.md` | 修改：展示层和静态服务策略改为 Vue-only |
| 文档 | `docs/features/fastapi-runtime.md` | 修改：运行时说明不再声明 `webapp/static/` 前端来源 |
| 文档 | `docs/BACKLOG.md` | 修改：B-143 状态流转 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-142 已完成并从 BACKLOG 标记为 done |

### 5.2 与现有 plan 的重叠

创建本 plan 时扫描 `docs/plans/` 与 `docs/superpowers/plans/`：现有三个 superpowers plan 是早期 desktop/legacy 领域计划，影响 `src/`、旧架构文档和 README；本任务影响 `webapp/`、`frontend` 构建服务测试和 Web 文档，未发现未完成的实现重叠。

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

## 6. 完成标准

全部勾选后方可删除本 plan 文件：

- [ ] FastAPI 不再回退服务 `webapp/static/`。
- [ ] `webapp/static/` legacy 原生前端文件已删除。
- [ ] Vue 构建产物存在时 `/` 返回 `static_dist/index.html`。
- [ ] Vue 构建产物缺失时 `/` 返回明确构建提示，不静默回退。
- [ ] 测试通过（参照 `docs/guides/testing.md` 最低要求）。
- [ ] 相关文档已同步（见下方“回流清单”）。
- [ ] BACKLOG 条目 B-143 状态已更新为 `done`。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| Vue-only 前端入口与无 legacy fallback 策略 | `docs/features/frontend-engineering.md` | [ ] |
| Web MVP 静态服务架构说明 | `docs/design/architecture-overview.md` | [ ] |
| FastAPI 运行时静态入口说明 | `docs/features/fastapi-runtime.md` | [ ] |
| 启动前构建要求 | `docs/guides/setup.md` | [ ] |
| 前端验证命令与 legacy 测试清理 | `docs/guides/testing.md` | [ ] |
| B-143 完成状态 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-05-28：启动 plan。`git status --short` 为空；未发现与 B-143 范围重叠的 Active/Interrupted plan。

## 9. 状态快照

- **最后更新**：2026-05-28 00:00
- **进度**：已完成 0 / 4 项（见 § 3 勾选状态）
- **最新 commit**：N/A
- **代码状态**：分支 `fix/b-142-vue-workbench-sse-sessions`；计划创建中；无未提交改动
- **下一步**：用测试锁定新的静态服务策略
- **续任务须知**：B-143 不改 API 契约、不改 SQLite schema、不改 Agent 工具权限；构建产物 `webapp/static_dist/` 仍不入库
