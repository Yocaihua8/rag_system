# 测试指南

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：v2/v3 后端、前端、E2E、Docker、桌面、插件和文档验证
> Related：`setup.md`、`../design/api-spec.md`、`../design/agent-runtime-and-tool-contract.md`、`../features/desktop-app.md`

## 1. 基础矩阵

```powershell
.\.venv\Scripts\python.exe -m pytest tests/backend tests/integration tests/repository -q
npm run frontend:test
npm run frontend:build
npm run frontend:e2e
npm run frontend-v3:typecheck
npm run frontend-v3:test
npm run frontend-v3:build
npm run frontend-v3:e2e
git diff --check
```

E2E 用例位于 `tests/e2e/`，默认使用 4173 前端和隔离的 18765 后端，覆盖真实跨域导入、问答/SSE、逐点学习、学习计划和 Obsidian 用户侧流程。`frontend/scripts/run-e2e.mjs` 为每次运行创建系统临时数据库，不复用正式 `runtime/v2/app.db`。

React v3 E2E 由 `frontend-v3/scripts/run-e2e.mjs` 默认启动 4174 前端和隔离的 18766 后端，使用系统临时目录中的独立 v2/v3 数据库与项目 fixture，覆盖项目创建、任务原子首消息、固定 Run、SSE、结果内容、刷新恢复、离线草稿和响应式。端口被占用时通过 `KI_V3_E2E_FRONTEND_PORT`、`KI_V3_E2E_BACKEND_PORT` 显式改用空闲端口；预览使用 strict port，不会静默连接其他服务。运行器不读取或修改正式 `runtime/v2/app.db`、`runtime/v3/app.db`。

当前 CI 和本地 venv 验证基线是 Python 3.11；v3 正式目标为 Python 3.12，但本阶段不能把 3.11 结果写成 3.12 已通过。`backend/requirements/base.txt` 已包含 SQLAlchemy 2 与 Alembic 运行依赖。

## 2. 关键契约

| 改动 | 至少验证 |
|------|----------|
| FastAPI/CORS | 根路由 404、允许/拒绝 Origin、OPTIONS、认证头、SSE |
| API/领域 | 对应后端和集成测试；方法、字段、错误保持兼容 |
| 存储 | 当前 Schema、迁移、CRUD 与 v2 数据代际 |
| v3 数据 | SQLAlchemy metadata/Alembic head、19 张业务表与 2 张治理表、generation fail-closed、WAL/外键/事务、幂等与 CAS；v2 哨兵保持不变 |
| v3 API | `/api/v3` 的真实 OpenAPI、envelope、request ID、幂等冲突、项目/任务/按任务查询运行、controls/retry、审批/产物读取，以及工作流版本化 CRUD/发布/绑定/归档边界 |
| v3 执行 | 固定四步 `project.inspect.v1`、租约/心跳/恢复、步骤尝试、SSE 续传、绝对路径/正文不泄漏、产物与 Agent 消息持久化 |
| React v3 | TS6 typecheck、OpenAPI 重复生成、API/SSE reducer、四个一级页面、320px–桌面响应式与真实 v3 E2E；缺失能力无演示回退 |
| 逐点学习 | 七态会话、当前步骤公开范围、三次 attempt、幂等/CAS、reveal 证据资格、stale 只读、覆盖投影和确认计划任务单调联动 |
| SQL 练习 | fixture hash、只读临时库、结果与必要语义评分、多语句/写操作/Schema/危险函数阻断、时间/VM/行列/字节上限、正式数据库哨兵不变 |
| 前端 API | `fetch` 与 `EventSource` 都断言绝对 API URL |
| 前端页面 | 三个现有学习入口、当前步骤/一道题、原始 SQL、防重复提交、冲突恢复、终态/stale 和计划刷新相关 Vitest、构建与 Playwright 主流程 |
| 仓库/文档 | `tests/repository/`、根 allowlist、源码派生契约、链接与占位符 |

## 3. v3 Agent alpha 专项

所有 v3 测试都必须把 v2 与 v3 数据库指向系统临时目录，并使用独立 `--basetemp`。不得复用 `runtime/v2/app.db`、`runtime/v3/app.db` 或仓库内固定 pytest 临时目录：

```powershell
$b173TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("knowledge-island-b173-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $b173TempDir | Out-Null
$env:KI_DB_PATH = Join-Path $b173TempDir "v2.db"
$env:KI_V3_DB_PATH = Join-Path $b173TempDir "v3\app.db"

.\.venv\Scripts\python.exe -m pytest tests/backend/test_v3_runtime_settings.py tests/backend/test_v3_agent_store.py tests/backend/test_v3_workflow_validation.py tests/backend/test_v3_agent_application.py tests/backend/test_v3_project_inspector.py tests/backend/test_v3_executor.py tests/integration/test_v3_api_contract.py tests/integration/test_v3_workflow_api.py tests/integration/test_v3_agent_end_to_end.py tests/repository/test_repository_layout.py -q --basetemp (Join-Path $b173TempDir "pytest")
```

专项至少覆盖：

- 未标记、v2 或未知代际数据库被只读拒绝且文件 hash/哨兵不变；全新数据库升级到 `0001_v3_initial`；
- Project/Task/Message/Run 的幂等回放和同 Key 异载荷冲突，状态控制的 `expected_version`；
- workflow validate 对安全 allowlist、循环、孤立节点、端口类型和未受审批保护写节点的拒绝；工作流创建、不可变 draft、checksum/version 发布、项目绑定、归档后拒绝新草稿和历史 Version 保留；
- `project.inspect.v1` 四步持久执行、按 Task 恢复最近 Run、重试/租约/暂停/取消竞争、产物与 Agent 消息生成，以及事件 `Last-Event-ID` / `after_sequence` 回放；
- 项目检查不读取正文、不跟随目录符号链接，产物和 SSE 不包含项目绝对路径；
- v2 API 和 Vue 文件未被 v3 测试或迁移改写。

专项命令定义验证范围，不代表当前 Python 3.11、目标 Python 3.12 或完整回归已经通过；最终结果必须按实际命令输出记录。

## 4. 逐点学习专项

所有会导入 `backend.api.server` 的 pytest 必须在进程启动前把 `KI_DB_PATH` 指向正式运行目录之外的临时文件，并使用独立 `--basetemp`：

```powershell
$b171TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("knowledge-island-b171-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $b171TempDir | Out-Null
$env:KI_DB_PATH = Join-Path $b171TempDir "api.db"

.\.venv\Scripts\python.exe -m pytest tests/backend/test_coach_learning_storage.py tests/backend/test_coach_learning.py tests/backend/test_coach_learning_sql_integration.py tests/backend/test_sql_learning.py tests/backend/test_coach_learning_coverage.py tests/backend/test_coach_assessment.py tests/integration/test_coach_learning_api.py tests/integration/test_coach_learning_plan_api.py tests/integration/test_coach_api.py tests/integration/test_coach_assessment_api.py -q --basetemp (Join-Path $b171TempDir "pytest")

npm run frontend:test -- src/App.coach-learning.test.js src/api/coach.test.js src/components/CoachLearningSessionOverlay.test.js src/components/QuestionComposer.test.js src/state/app-state.test.js src/views/WorkbenchView.test.js src/views/LearningMapView.test.js src/views/LearningPlanView.test.js
npm run frontend:build

$env:CI = "1"
$env:KI_E2E_BACKEND_PORT = "18770"
$env:KI_E2E_FRONTEND_PORT = "4178"
npm run frontend:e2e
```

- 后端专项覆盖六表增量初始化、创建/恢复/完成/放弃、七态迁移、attempt 幂等与 payload 冲突、CAS、项目/分析运行隔离、stale 只读、掌握证据投影和确认计划任务联动。
- SQL 专项覆盖正确/等价/错误/语法答案、排序、空结果、`NULL`、聚合、JOIN，以及多语句、DML、DDL、`PRAGMA`、`ATTACH/DETACH`、递归 CTE、虚表、危险函数和各资源上限。
- API 专项覆盖四个学习会话操作、OpenAPI 清单、请求校验、状态码、幂等冲突的最新会话快照，并回归旧 Coach 评估和 legacy `/api/assessment/*`。
- Vue 专项覆盖活动会话恢复、三个入口、服务端允许动作、结构化 fixture、原始多行 SQL、提交防重、具体反馈、reveal 证据提示和终态/stale 文案。
- Playwright 全套包含从确认学习计划任务启动 SQL 学习、错误作答、重试、页面恢复、正确作答、会话完成和计划任务刷新。端口必须空闲；运行器仍自行创建系统临时数据库。

专项命令只定义待执行范围，不代表检查已经通过。完整回归仍执行 § 1 的后端/集成/仓库、前端单测、构建和 E2E 命令。

## 5. 依赖审计

```powershell
python scripts/check_npm_audit.py
.\.venv\Scripts\pip-audit.exe -r backend/requirements/base.txt --progress-spinner off
npm --prefix integrations/obsidian-plugin audit --audit-level=high
```

根 npm 审计脚本只允许 ADR-014 记录的 React Router RSC 公告例外，并同时静态拒绝任何 RSC/server 入口；出现其他包、其他公告、数量变化或扫描命中都会失败。它仍会明确报告 2 个 high，不能写成零漏洞。生产 Python 审计使用 `base.txt`；`dev.txt` 还包含测试和打包工具，不能代替生产依赖范围。只记录本次实际输出。

## 6. Docker

```powershell
docker compose --project-directory ops/docker -f ops/docker/compose.yaml config
docker compose --project-directory ops/docker -f ops/docker/compose.yaml build
ops\docker\start.ps1 -NoOpen
docker compose --project-directory ops/docker -f ops/docker/compose.yaml ps
ops\docker\stop.ps1
```

两个服务各自健康后，从 4173 页面完成对 8765 API 的真实 REST/SSE 冒烟。停止时不传 `-RemoveVolumes`，除非用户明确授权删除准确 volume。

## 7. 桌面

```powershell
.\.venv\Scripts\python.exe -m pytest tests/repository -k tauri -q
cargo check --manifest-path src-tauri/Cargo.toml
npm run desktop:build:windows
```

结构测试、Cargo、sidecar、bundle 和安装后动态连通性是不同门禁；目标平台结果不能互相替代。

## 8. Obsidian 插件

插件在自身目录独立并串行验证：

```powershell
Push-Location integrations/obsidian-plugin
npm test
npm run typecheck
npm run build
Pop-Location
```

## 9. 文档

```powershell
pwsh -NoProfile -File scripts/check-placeholders.ps1
pwsh -NoProfile -File scripts/check-doc-links.ps1
.\.venv\Scripts\python.exe scripts/check_docs_consistency.py
```

文档门禁还应检查 API 路径/操作数量、SQLite 表与关键字段、包/脚本命令、源码内文档路径、最近一级索引引用、旧目录引用和活动文档占位符。

## 10. CI 覆盖边界

当前 GitHub Actions 会运行受控 npm 审计策略、Vue 与 React v3 构建/单测、Python 依赖审计、后端/集成/仓库测试、文档一致性和两套 Playwright E2E。默认 CI **不运行** Docker 镜像/健康检查、Cargo/Tauri bundle 或 Obsidian 插件 test/typecheck/build；发布前必须另外执行并记录这些门禁。

## 11. 记录要求

只记录实际运行的命令、commit、环境、通过/失败数量和未覆盖边界。未运行、被环境阻断或只完成静态检查时，不得写成完整通过。
