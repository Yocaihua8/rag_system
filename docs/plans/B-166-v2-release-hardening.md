# B-166 v2.0.0 依赖安全修复与正式发布

> 状态：Active
> 创建时间：2026-07-30
> 创建方：Codex
> 关联 BACKLOG：B-166
> 关联功能文档：docs/features/frontend-engineering.md, docs/features/desktop-packaging.md
> 关联设计文档：N/A（不改 API、数据库 Schema 或架构边界）

## 1. 目标

以最小兼容升级修复根前端锁文件中的两个 high 漏洞，完成 npm/pip 安全审计、Python/Vue/插件/Playwright 本地 CI 等价矩阵和 Windows Tauri 原生包验证；在 GitHub Actions 额度已用完的明确边界下，把本地验证证据写入 PR 与发布文档，随后合并 `main`、创建 `v2.0.0` Tag 和 GitHub Release。

## 2. 前置条件

- 已读取 `AGENTS.md`、`CONTRIBUTING.md`、`docs/guides/testing.md`、`docs/guides/release-process.md` 与 v2 readiness。
- 当前分支为 `feature/project-knowledge-coach-v2`，工作区在任务开始时干净，起点提交为 `85ae4b4`。
- 用户已明确 GitHub Actions 额度用完，要求以完整本地 CI 测试通过作为合并前门禁。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。
未完成项不得删除。

- [x] 登记安全问题并完成 `brace-expansion` / `postcss` 最小兼容升级
- [ ] 完成 npm audit、pip-audit、Python 533 项、Vue 单测/构建、插件与 Playwright 本地 CI 等价矩阵
- [ ] 补齐 MSVC / Windows SDK 后完成 `cargo check` 与 Windows Tauri 安装包验证
- [ ] 同步 BACKLOG、readiness、测试/发布指南、桌面打包、README、CHANGELOG 和当日 devlog
- [ ] 推送功能分支、创建 PR，记录本地 CI 证据并在无远端 CI 额度边界下合并 `main`
- [ ] 创建并推送 `v2.0.0` Tag，创建 GitHub Release，完成发布后审计

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 依赖 | `package-lock.json`（必要时 `package.json`） | 最小兼容升级 |
| 文档 | `docs/BACKLOG.md` | B-166 与 ISSUE-004 生命周期 |
| 文档 | `docs/release/V2_0_0_READINESS_2026-07-24.md` | 安全、本地 CI、Windows 包和正式发布证据 |
| 文档 | `docs/guides/testing.md`, `docs/guides/release-process.md` | GitHub Actions 额度边界与本地等价门禁 |
| 文档 | `docs/features/desktop-packaging.md` | v2 Windows 原生包结果 |
| 文档 | `README.md`, `CHANGELOG.md`, `docs/devlog/2026-07-30.md` | 正式版本口径与发布记录 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-160～B-165 已完成，本任务从其本地候选结果继续收口 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | 未发现状态为 Active 或 Interrupted 的任务 plan；`docs/superpowers/plans/` 三份 2026-05 无状态 legacy 计划仅涉及已归档 PySide6 路径 | N/A |

## 6. 完成标准

- [ ] 两个 high 漏洞在当前锁文件的 `npm audit --audit-level=high` 中清零
- [ ] `pip-audit`、Python/Vue/插件/Playwright 完整本地 CI 等价矩阵通过
- [ ] Windows `cargo check` 与 `npm run tauri:build:windows` 通过并生成 NSIS 安装包
- [ ] PR 明确记录无 GitHub Actions 额度及本地验证命令、提交和结果
- [ ] 相关文档已同步（见下方“回流清单”）
- [ ] BACKLOG 条目 B-166 状态已更新为 `done`
- [ ] `main`、`v2.0.0` Tag 和 GitHub Release 指向同一已验证发布提交

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 漏洞路径、修复版本与安全审计结果 | `docs/BACKLOG.md`, `CHANGELOG.md` | [ ] |
| 本地 CI 等价矩阵及 GitHub Actions 额度边界 | `docs/release/V2_0_0_READINESS_2026-07-24.md`, `docs/guides/testing.md`, `docs/guides/release-process.md` | [ ] |
| Windows 工具链与 NSIS 产物证据 | `docs/features/desktop-packaging.md`, `docs/release/V2_0_0_READINESS_2026-07-24.md` | [ ] |
| 正式 v2 产品、安装与发布口径 | `README.md`, `CHANGELOG.md`, `docs/devlog/2026-07-30.md` | [ ] |

## 8. 执行记录

- 2026-07-30：冲突扫描未发现 Active/Interrupted 任务 plan；三份 2026-05 superpowers plan 为无状态 legacy 残留，不涉及当前前端依赖与发布文件。
- 2026-07-30：GitHub Actions 额度不足是用户明确给出的发布约束；本任务不会把本地验证伪装成远端 green check，PR/readiness 将单独记录此例外。
- 2026-07-30：不改变根直接依赖版本，仅把锁文件允许范围内的 `brace-expansion` 从 `2.1.1` 升至 `2.1.2`、`postcss` 从 `8.5.15` 升至 `8.5.22`；`npm ci --offline` 与 `npm audit --offline --audit-level=high` 均报告 0 vulnerabilities。
- 2026-07-30：Vue 单测和构建首次验证被 Windows 路径联接的沙箱权限阻断：Node 将 `E:\Code\knowledage_island` 解析为 `E:\Dev\Projects\knowledage_island`，测试报模块不可访问，构建清理 `backend/static_dist` 报 EPERM；这不是依赖回归，需在获准的真实工作区路径权限下重跑。

## 9. 状态快照

- **最后更新**：2026-07-30 11:49
- **进度**：已完成 1 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`493794f` — fix: 修复前端依赖高危漏洞
- **代码状态**：`feature/project-knowledge-coach-v2`；依赖安全修复已提交，工作区仅有本状态快照待提交
- **下一步**：完成 npm audit、pip-audit、Python 533 项、Vue 单测/构建、插件与 Playwright 本地 CI 等价矩阵
- **续任务须知**：锁文件和本机 `node_modules` 已解析为 `brace-expansion@2.1.2`、`postcss@8.5.22`；联网 audit 需用户明确允许依赖元数据外发。当前工作区是指向 `E:\Dev\Projects\knowledage_island` 的路径联接，默认沙箱阻断 Node 对真实路径读写，完整前端验证需显式批准。
