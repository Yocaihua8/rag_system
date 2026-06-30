# B-151 前端 Vitest 单元测试

> 状态：Active
> 创建时间：2026-06-30
> 创建方：Codex
> 关联 BACKLOG：B-151
> 关联功能文档：docs/features/frontend-engineering.md
> 关联设计文档：N/A

## 1. 目标

为 Vue/Vite 前端引入 Vitest 单元测试层，覆盖 API helper 的请求封装、错误归一化、参数校验和关键组件状态，使纯逻辑/组件状态测试与 Playwright E2E 主流程测试分层。

## 2. 前置条件

- 已读取 `AGENTS.md`、`README.md`、`CONTRIBUTING.md`、`docs/README.md`、`docs/BACKLOG.md`、`docs/guides/testing.md`、`docs/features/frontend-engineering.md`、`docs/plans/README.md`、`docs/plans/plan-template.md`。
- 已通过 Context7 查询 Vitest v4.1.6 文档：Vite 项目可在配置中设置 `test.environment = "jsdom"`，`package.json` 可增加 `test`/`test:run` 脚本。

## 3. 任务拆解

- [x] 引入 Vitest 测试配置和 API helper 单元测试
- [ ] 补充关键 Vue 组件状态测试并同步正式文档
- [ ] 完成验证、更新 BACKLOG 为 done 并删除本 plan

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `package.json` | 新增 Vitest 测试脚本与 devDependencies |
| 代码 | `package-lock.json` | 同步 npm 依赖锁定 |
| 代码 | `frontend/vite.config.js` | 新增 Vitest jsdom 测试配置 |
| 测试 | `frontend/src/api/*.test.js` | 新增 API helper 单元测试 |
| 测试 | `frontend/src/components/*.test.js` | 新增组件状态单元测试 |
| 文档 | `docs/guides/testing.md` | 记录 Vitest 单测命令和分层边界 |
| 文档 | `docs/features/frontend-engineering.md` | 记录 B-151 前端单测工程化边界 |
| 文档 | `docs/BACKLOG.md` | B-151 状态流转 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 无前置 plan 依赖 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | 已扫描 `docs/plans/` 与 `docs/superpowers/plans/`，未发现 Active/Interrupted plan 覆盖本次前端 Vitest 测试范围 | N/A |

## 6. 完成标准

- [ ] `npm run test:unit` 可运行 Vitest 单元测试并通过
- [ ] `npm run build` 仍可生成 `webapp/static_dist/`
- [ ] `docs/guides/testing.md` 已记录 Vitest 单测命令
- [ ] `docs/features/frontend-engineering.md` 已记录 B-151 测试分层
- [ ] BACKLOG 条目 B-151 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 前端 Vitest 单测命令和适用范围 | `docs/guides/testing.md` | [ ] |
| API helper 与组件状态单测边界 | `docs/features/frontend-engineering.md` | [ ] |
| B-151 完成状态 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-06-30：启动 B-151；Context7 选中 `/vitest-dev/vitest/v4.1.6`；本次不修改后端 API、SQLite schema 或 Agent 工具权限。

## 9. 状态快照

- **最后更新**：2026-06-30 21:56
- **进度**：已完成 1 / 3 项（见 § 3 勾选状态）
- **最新 commit**：本次提交后生成 — 引入 Vitest 测试配置和 API helper 单元测试
- **代码状态**：main；`npm run test:unit` 已通过 6 个文件、27 个测试；组件测试文件尚未提交，下一切片处理文档回流
- **下一步**：补充关键 Vue 组件状态测试并同步正式文档
- **续任务须知**：依赖安装曾因默认 npm audit/fund 请求超时，已用 `npm install -D vitest@^4.1.6 jsdom @vue/test-utils --no-audit --no-fund` 完成。
