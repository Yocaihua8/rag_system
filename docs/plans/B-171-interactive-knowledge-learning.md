# B-171 逐知识点交互学习流程与只读 SQL 练习

> 状态：Done（待生命周期清理）
> 创建时间：2026-08-01
> 创建方：Codex
> 关联 BACKLOG：B-171
> 关联功能文档：`docs/features/project-knowledge-coach.md`
> 关联设计文档：`docs/design/api-spec.md`、`docs/design/database-design.md`、`docs/design/ui-wireframes.md`、`docs/design/state-flow-and-acceptance.md`、`docs/adr/ADR-011-interactive-learning-sql-sandbox.md`

## 1. 目标

在当前项目知识教练内增加从教练、学习地图或确认学习计划任务启动的逐知识点学习会话。会话一次只公开一个知识点和一道题，持久化每次 attempt，支持有限重试、来源过期只读、确定性 SQL 查询评分，并把当前分析运行下的有效结果联动到知识覆盖和学习计划进度。

## 2. 前置条件

- 以已通过 PR #6 合并后 CI 的 `main@667a325` 为基线。
- 旧 `feature/b-168-interactive-knowledge-learning` 只作为语义来源，不整支 merge 或 cherry-pick，不恢复旧 B-168、旧 ADR-010、旧测试目录和已删除文档体系。
- 保留当前 FastAPI API-only、Vue 绝对 API URL、精确 CORS、`runtime/v2/` 数据代际、旧 Coach API 和 legacy API 边界。
- 所有 SQLite、pytest 与 E2E 验证必须使用隔离临时数据库，不读取或覆盖正式 `runtime/v2/app.db`。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。
未完成项不得删除。

- [x] 语义移植学习会话、步骤、练习、attempt 领域模型、六张增量表和四个 Coach API。
- [x] 语义移植临时 SQLite 只读沙箱、确定性评分、SQL 练习生成和安全专项测试。
- [x] 接入 Vue 逐知识点覆盖层、三个现有入口、绝对 API URL 单测与双运行时 Playwright 闭环。
- [x] 合并有效 attempt 掌握证据、联动确认学习计划进度并按当前文档体系完成 ADR/规格回流。
- [x] 运行专项、完整、依赖与文档门禁，完成 PR 最终 SHA 与 main 合并提交 CI。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|-------------|---------|
| 后端领域 | `backend/domain/coach_models.py`、`backend/domain/coach_learning.py`、`backend/domain/sql_learning.py`、`backend/domain/coach_assessment.py` | 新增七态会话、exercise、attempt、确定性评分与掌握证据 |
| 后端存储 | `backend/storage/coach_progress_store.py` | 增量新增六张 `coach_learning_*` 表及事务方法 |
| HTTP 契约 | `backend/routes/coach.py`、`backend/api/openapi_schema.py` | 新增四个学习会话 API，不修改旧接口 |
| Vue | `frontend/src/` | 新增学习覆盖层、API helper 与三个现有入口，保留绝对 API URL |
| 测试 | `tests/backend/`、`tests/integration/`、`tests/repository/`、`tests/e2e/`、`frontend/src/**/*.test.js` | 新增领域、存储、API、SQL 安全、Vue 和浏览器闭环 |
| 文档 | Coach 功能、需求、API、数据库、线框、状态流、架构、安全、测试、ADR、CHANGELOG、BACKLOG | 按当前扁平文档体系回流 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 当前没有其他 Active/Interrupted plan；B-169 已合并并完成生命周期清理。 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| 旧分支已删除的 `B-168-interactive-knowledge-learning.md` | Coach、前端、测试、文档编号和运行时请求假设 | 仅语义移植；使用 B-171/ADR-011 和当前目录/绝对 URL 契约，不整支合并 |
| N/A | 当前 `docs/plans/` 没有其他 Active/Interrupted plan | N/A |

## 6. 完成标准

- [x] 功能行为符合 `docs/features/project-knowledge-coach.md` 的项目内学习与来源规则。
- [x] 六张新表只做增量初始化，不改写旧评估数据或正式运行库。
- [x] 四个新 API、旧 Coach API 和 legacy API 契约测试通过。
- [x] SQL 沙箱安全、确定性评分和正式数据库隔离测试通过。
- [x] Vue 单测、构建、Playwright 学习闭环和无新增一级导航验证通过。
- [x] 后端/集成/仓库完整 pytest、依赖审计与文档一致性门禁通过。
- [x] ADR-011 已根据当前实现证据决议，相关文档已同步。
- [ ] BACKLOG 条目 B-171 已移除，完成事实已写入 `CHANGELOG.md` 与 Git 历史。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 学习会话、attempt、重试、答案揭示和掌握证据规则 | `docs/features/project-knowledge-coach.md`、`docs/requirements/functional-modules.md` | [x] |
| 四个学习会话 API 与兼容错误语义 | `docs/design/api-spec.md` | [x] |
| 六张新表、索引、增量初始化与回滚边界 | `docs/design/database-design.md` | [x] |
| 七态状态机和验收条件 | `docs/design/state-flow-and-acceptance.md` | [x] |
| 覆盖层、样例表、恢复、只读和现有入口交互 | `docs/design/ui-wireframes.md` | [x] |
| SQL 沙箱、模块边界和安全限制 | `docs/adr/ADR-011-interactive-learning-sql-sandbox.md`、`docs/design/architecture-overview.md`、`docs/guides/security.md` | [x] |
| 新增测试矩阵和验证结果 | `docs/guides/testing.md` | [x] |
| 对外变更、任务状态和执行记录 | `CHANGELOG.md`、`docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-08-01：用户确认将旧冲突分支拆为两个独立 PR；B-169 已完成、合并并通过 main CI，B-171 从该最新主线启动。
- 2026-08-01：冲突审查确认旧后端语义可移植，但旧测试目录、旧文档编号、旧同源 API URL 和静态托管假设不得恢复。
- 2026-08-01：ADR-011 先以 Proposed 建立；只有当前主线实现和完整门禁产生证据后才转 Accepted。
- 2026-08-01：逐知识点覆盖层已接入教练、学习地图和确认计划入口；保留 `apiUrl()` 绝对请求，E2E 页面使用 4173、API 使用 `KI_E2E_API_BASE_URL`（默认 18765）。前端单测 24 files / 105 tests、生产构建与 E2E 语法/发现检查通过；真实 E2E 等后端整合后执行。
- 2026-08-01：七态学习会话、六张增量表、四个 Coach API、临时 SQLite 只读沙箱和确定性评分已按最终旧分支语义移植到当前目录；保留当前 API-only FastAPI 契约。B-171 专项 82 passed，既有评估/学习计划回归 34 passed，合计 116 passed。
- 2026-08-01：按当前扁平文档体系回流功能、需求、API、数据库、状态、UI、架构、安全和测试契约；源码派生事实更新为 90 paths / 98 operations / 43 tables，ADR-011 根据当前实现与验证证据转为 Accepted。
- 2026-08-01：真实双运行时 Playwright 2 passed；Vue 24 files / 105 tests，生产构建 56 modules，Cargo check、npm audit（0 vulnerabilities）、pip-audit（无已知漏洞）和三项文档门禁通过。完整 Python 首轮为 586 passed / 1 failed，定位到仓库静态测试仍匹配旧二项加载字符串；改为校验计划、活动会话和 Obsidian 三项调用后，该文件 88 passed，最终完整套件 587 passed。
- 2026-08-01：PR #7 首轮远端门禁在 `5c22ea86553f3e01caf05fa3e543ebc08864bbc6` 全部通过：CI/python-tests、CI/frontend-e2e 和 Docs Checks 均为 success，合并状态为 CLEAN。该证据完成第 5 项；生命周期清理会产生新的最终 SHA，仍须重新等待该 SHA 的远端门禁。

## 9. 状态快照

- **最后更新**：2026-08-01 16:11（Asia/Shanghai）
- **进度**：已完成 5 / 5 项（见 § 3 勾选状态）；仅剩 plan 生命周期清理
- **最新 commit**：`5c22ea8` — docs: 记录 B-171 本地完整验收
- **代码状态**：`agent/b-171-interactive-learning`；实现、文档、本地门禁和 PR #7 首轮远端门禁均已完成
- **下一步**：移除 B-171 BACKLOG 行、更新活动计划索引并删除本 plan，再重新等待最终 SHA 的 GitHub Actions
- **续任务须知**：保留 `apiUrl()`/`VITE_API_BASE_URL` 与 API-only FastAPI；测试使用工作区隔离 basetemp/数据库；不得读取或覆盖正式运行库。
