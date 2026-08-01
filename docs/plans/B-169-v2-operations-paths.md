# B-169 v2 数据库备份与结果导出路径修复

> 状态：Done
> 创建时间：2026-08-01
> 创建方：Codex
> 关联 BACKLOG：B-169
> 关联功能文档：`docs/features/result-export.md`
> 关联设计文档：`docs/design/api-spec.md`、`docs/design/risk-register.md`

## 1. 目标

将 ISSUE-006 中数据库备份与结果导出的路径漂移收口到当前 v2 运行时：保留主线已经采用的 `runtime/v2/app.db`、`runtime/v2/backups/` 和 `knowledge-island-v2-*` 命名，为 Windows Git Bash 调用 `sqlite3.exe` 增加兼容路径，并让结果导出默认使用活动配置的 `outputs_dir`。所有恢复测试只操作临时目录，不读取或覆盖正式数据库。

## 2. 前置条件

- 以 `main@26b02b7` 为基线，不整支合并包含交互学习历史的 `fix/issue-006-v2-paths`。
- 保持 `KI_DB_PATH`、`KI_BACKUP_DIR`、`KI_OUTPUT_DIR`、`RAG_OUTPUT_DIR` 和 Qdrant 显式备份边界兼容。
- 不修改数据库 Schema、公共 API 请求/响应、前端、Agent 权限或 chunk/retriever/top-k 活动链路。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。
未完成项不得删除。

- [x] 补齐 Windows SQLite 在线备份路径转换，并增加真实脚本执行、隔离恢复和数据完整性测试。
- [x] 让结果导出默认使用配置层 `outputs_dir`，保留显式环境变量覆盖优先级并补回归测试。
- [x] 按当前扁平文档体系回流运行、API、风险和 ISSUE 边界，不恢复已删除历史文档。
- [x] 运行专项、完整、依赖与文档门禁，完成 PR CI 后回流验收结果。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 脚本 | `ops/scripts/backup_db.sh` | 增加 Windows Git Bash 路径兼容 |
| 代码 | `backend/domain/result_export.py` | 复用活动配置输出目录 |
| 测试 | `tests/backend/test_result_export.py`、`tests/repository/test_ops_scripts.py` | 增加路径与真实恢复回归 |
| 文档 | `docs/BACKLOG.md`、`docs/features/result-export.md`、`docs/design/api-spec.md`、`docs/design/risk-register.md`、`docs/guides/runbook.md`、`docs/guides/troubleshooting.md`、`ops/README.md`、`CHANGELOG.md` | 回流当前行为与剩余问题边界 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 当前 `docs/plans/` 没有其他 Active/Interrupted plan。 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| 旧分支已删除的 `B-169-v2-operations-paths.md` | 旧测试目录、旧文档路径及交互学习祖先历史 | 以当前 main 新建 plan 并做语义移植；不 merge/cherry-pick 整支旧分支 |

## 6. 完成标准

- [x] Windows Git Bash + `sqlite3.exe` 在线备份使用可识别路径，Linux/macOS 行为不变。
- [x] 真实测试恢复隔离 SQLite 备份并验证 `PRAGMA integrity_check`、`data_generation=v2` 和样例数据。
- [x] 结果导出无显式覆盖时使用活动 `runtime/v2/outputs/`，覆盖变量优先级保持兼容。
- [x] 相关专项、完整测试、依赖审计和文档门禁通过。
- [x] 相关文档已同步，BACKLOG 条目 B-169 已移除，完成事实已写入 `CHANGELOG.md` 与 Git 历史。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| v2 默认备份路径、Windows 兼容与恢复边界 | `docs/guides/runbook.md`、`ops/README.md` | [x] |
| v2 结果输出目录与覆盖变量 | `docs/features/result-export.md`、`docs/design/api-spec.md` | [x] |
| 路径风险关闭与剩余配置问题拆分 | `docs/BACKLOG.md`、`docs/design/risk-register.md`、`docs/guides/troubleshooting.md`、`CHANGELOG.md` | [x] |

本任务不新增重大技术决策，不新增 ADR。

## 8. 执行记录

- 2026-08-01：确认旧 `fix/issue-006-v2-paths` 建立在未合并交互学习分支之上，不能整支合并；仅以旧提交作为语义来源。
- 2026-08-01：主线已采用 `runtime/v2/backups/` 与 `knowledge-island-v2-*`，本次不得被旧提交中的目录和文件名覆盖。
- 2026-08-01：冲突扫描确认没有其他 Active/Interrupted plan，B-171 交互学习按独立后续 PR 分区处理。
- 2026-08-01：Windows Git Bash 备份目标经 `cygpath -m` 转换；真实脚本测试在隔离临时项目中恢复备份并验证完整性、v2 标记和样例数据，结果为 5 passed。
- 2026-08-01：结果导出默认改用 `load_settings().outputs_dir`，显式覆盖顺序不变；配置/领域单测 8 passed，导出集成测试 9 passed、112 deselected。
- 2026-08-01：按当前文档体系同步 API、数据、功能、运行、安全、风险和排障事实；ISSUE-006 路径部分关闭，剩余配置接线拆为 ISSUE-009。占位符、链接、源码一致性与文档契约测试均通过。
- 2026-08-01：本地最终门禁通过：`npm ci`；npm audit 0 vulnerabilities；pip-audit 无已知漏洞；Python 完整套件 521 passed；Vue 22 files / 92 tests；生产构建 53 modules；Playwright 1 passed；三项文档门禁和 `git diff --check` 通过。当前仍需等待 PR 最终 SHA 的远端 CI，不能提前标记第 4 项完成。
- 2026-08-01：PR #6 首轮远端门禁在 `f2c486c6d70dc9134a689640be0f23631c2ccb77` 全部通过：CI/python-tests、CI/frontend-e2e 和 Docs Checks 均为 success，合并状态为 CLEAN。该证据完成第 4 项；生命周期清理提交会产生新的最终 SHA，仍须重新等待该 SHA 的远端门禁。
- 2026-08-01：完成事实已回流 `CHANGELOG.md` 与 Git 历史，B-169 已从 BACKLOG 和活动计划索引移除；本 plan 将在下一独立提交删除。

## 9. 状态快照

- **最后更新**：2026-08-01 15:06（Asia/Shanghai）
- **进度**：已完成 4 / 4 项（见 § 3 勾选状态）；完成标准和回流清单均已满足
- **最新 commit**：`9a6a783` — docs: 完成 B-169 v2 路径修复验收
- **代码状态**：`agent/b-169-v2-paths`；B-169 已完成并从 BACKLOG 与活动计划索引移除
- **下一步**：删除本 plan，推送最终 SHA 并重新等待 GitHub Actions
- **续任务须知**：测试必须使用临时项目和隔离数据库；不得读取或覆盖正式 `runtime/v2/app.db`。
