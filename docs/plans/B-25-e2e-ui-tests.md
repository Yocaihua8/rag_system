# B-25 端到端 UI 自动化测试

> 状态：Active
> 创建时间：2026-06-29
> 创建方：Codex
> 关联 BACKLOG：B-25
> 关联功能文档：docs/guides/testing.md
> 关联设计文档：N/A（测试基础设施，不改变业务架构）

## 1. 目标

为 Web MVP 增加第一条可执行的浏览器端到端 UI 自动化测试链路，覆盖 Vue 生产构建、FastAPI 静态服务、项目空间创建、文本笔记导入和工作台问答的主流程。

## 2. 前置条件

- 已读取 `AGENTS.md`、`README.md`、`docs/BACKLOG.md`、`docs/guides/testing.md`、`docs/plans/README.md`、`docs/plans/plan-template.md`、`package.json`、`frontend/vite.config.js`、`frontend/src/` 主要页面组件和现有 `tests/test_webapp/` 静态契约测试。
- 已用 Context7 查询 Playwright 文档，确认 `webServer` 可启动本地服务并配合 `use.baseURL` 运行相对路径测试。
- 当前 checkout 不是 linked worktree，且存在非 B-25 既有未提交改动；执行时只暂存 B-25 相关文件和 `docs/BACKLOG.md` 的 B-25 hunk。
- 本任务不新增数据库 schema，不修改 API 契约，不引入真实外部 LLM 或网络服务依赖。

## 3. 任务拆解

- [x] 补充红灯契约测试，约束 Playwright 配置、npm scripts、E2E 测试文件、临时 DB 启动脚本和测试指南文档。
- [x] 实现 Playwright E2E 基础设施：依赖、配置、测试服务启动脚本、临时 DB 覆盖和首条浏览器主流程测试。
- [x] 同步测试指南，运行静态契约、浏览器 E2E、前端构建和相关 pytest 验证。
- [ ] 同步 BACKLOG 完成状态，删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 配置 | `package.json` / `package-lock.json` | 修改 |
| 配置 | `playwright.config.js` | 新增 |
| 测试 | `tests/test_webapp/test_e2e_ui.py` | 新增 |
| 测试 | `tests/e2e/web-mvp-smoke.spec.js` | 新增 |
| 测试脚本 | `tests/e2e/start-web-server.mjs` | 新增 |
| 测试脚本 | `tests/e2e/e2e_server.py` | 新增 |
| 配置 | `webapp/config.py` | 修改：允许 E2E 通过 `KI_DB_PATH` 覆盖默认 SQLite DB 路径 |
| 文档 | `docs/guides/testing.md` | 修改 |
| 文档 | `docs/BACKLOG.md` | 修改 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 无直接依赖 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

创建本 plan 时扫描到 3 个 `docs/superpowers/plans/` 旧 plan，影响范围集中在归档前 PySide6/legacy 领域模型与历史文档，不涉及 `tests/e2e/`、Playwright、当前 Vue/Vite Web MVP 测试入口或 B-25 文档。

## 6. 完成标准

- [x] `npm run test:e2e` 可启动临时测试服务并通过首条浏览器主流程测试。
- [x] E2E 服务使用临时 SQLite DB，不写入默认 `runtime/webapp/knowledge_island.db`。
- [x] `tests/test_webapp/test_e2e_ui.py` 通过。
- [x] `npm run build` 通过。
- [x] 相关文档已同步（见下方"回流清单"）。
- [ ] BACKLOG 条目 `B-25` 状态已更新为 `done`。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| E2E UI 测试命令、浏览器安装命令和适用场景 | `docs/guides/testing.md` | [x] |
| B-25 完成状态 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-06-29：选择 Playwright Test 作为首个浏览器 E2E 测试层，覆盖真实 Vue 生产构建和 FastAPI 测试服务；不扩展到多浏览器矩阵或视觉回归。
- 2026-06-29：E2E 服务需使用临时 DB 与临时项目目录，避免污染本地用户运行数据。
- 2026-06-29：红灯测试 `.venv\Scripts\python.exe -m pytest tests\test_webapp\test_e2e_ui.py -q` 按预期失败 6 项：缺少 npm scripts、`playwright.config.js`、`tests/e2e/` 启动脚本、首条 E2E spec、`KI_DB_PATH` 覆盖和测试指南说明。
- 2026-06-29：补齐 Playwright 配置、E2E 启动脚本、临时 DB 覆盖和首条 Web MVP smoke spec；静态契约 `.venv\Scripts\python.exe -m pytest tests\test_webapp\test_e2e_ui.py -q` 已通过 6 项。
- 2026-06-29：`npm run e2e:install` 下载 Chromium 10 分钟无输出后超时；本机改用 `KI_E2E_BROWSER_CHANNEL=chrome` 验证 `npm run test:e2e`，已启动临时 FastAPI 服务并通过 1 条 smoke 测试。
- 2026-06-29：复跑 `.venv\Scripts\python.exe -m pytest tests\test_webapp\test_frontend_build.py tests\test_webapp\test_fastapi_server.py tests\test_webapp\test_app_entrypoint.py -q`，通过 13 项。

## 9. 状态快照

- **最后更新**：2026-06-29 00:00
- **进度**：已完成 3 / 4 项（见 § 3 勾选状态）
- **最新 commit**：`df25b8b` — `test: 接入 Playwright 端到端 UI 测试`
- **代码状态**：`fix/b-08-concurrent-index`；工作区存在非 B-25 既有改动，需精确暂存
- **下一步**：同步 BACKLOG 完成状态，删除本 plan
- **续任务须知**：只暂存 B-25 相关文件和 `docs/BACKLOG.md` 的 B-25 hunk
