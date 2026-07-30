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
- [x] 完成 npm audit、pip-audit、Python 533 项、Vue 单测/构建、插件与 Playwright 本地 CI 等价矩阵
- [x] 补齐 MSVC / Windows SDK 后完成 `cargo check` 与 Windows Tauri 安装包验证
- [x] 同步 BACKLOG、readiness、测试/发布指南、桌面打包、README、CHANGELOG 和当日 devlog
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
| 文档 | `docs/README.md`, `docs/guides/setup.md`, `docs/features/frontend-engineering.md` | 当前候选边界、环境与前端依赖安全事实 |

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

- [x] 两个 high 漏洞及后续新增通告在当前锁文件的 `npm audit --audit-level=high` 中清零
- [x] `pip-audit`、Python/Vue/插件/Playwright 完整本地 CI 等价矩阵通过
- [x] Windows `cargo check` 与 `npm run tauri:build:windows` 通过并生成 NSIS 安装包
- [ ] PR 明确记录无 GitHub Actions 额度及本地验证命令、提交和结果
- [x] 相关文档已同步（见下方“回流清单”）
- [ ] BACKLOG 条目 B-166 状态已更新为 `done`
- [ ] `main`、`v2.0.0` Tag 和 GitHub Release 指向同一已验证发布提交

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 漏洞路径、修复版本与安全审计结果 | `docs/BACKLOG.md`, `CHANGELOG.md` | [x] |
| 本地 CI 等价矩阵及 GitHub Actions 额度边界 | `docs/release/V2_0_0_READINESS_2026-07-24.md`, `docs/guides/testing.md`, `docs/guides/release-process.md` | [x] |
| Windows 工具链与 NSIS 产物证据 | `docs/features/desktop-packaging.md`, `docs/release/V2_0_0_READINESS_2026-07-24.md` | [x] |
| 正式 v2 产品、安装与发布口径 | `README.md`, `CHANGELOG.md`, `docs/devlog/2026-07-30.md` | [x] |

## 8. 执行记录

- 2026-07-30：冲突扫描未发现 Active/Interrupted 任务 plan；三份 2026-05 superpowers plan 为无状态 legacy 残留，不涉及当前前端依赖与发布文件。
- 2026-07-30：GitHub Actions 额度不足是用户明确给出的发布约束；本任务不会把本地验证伪装成远端 green check，PR/readiness 将单独记录此例外。
- 2026-07-30：不改变根直接依赖版本，仅把锁文件允许范围内的 `brace-expansion` 从 `2.1.1` 升至 `2.1.2`、`postcss` 从 `8.5.15` 升至 `8.5.22`；`npm ci --offline` 与 `npm audit --offline --audit-level=high` 均报告 0 vulnerabilities。
- 2026-07-30：Vue 单测和构建首次验证被 Windows 路径联接的沙箱权限阻断：Node 将 `E:\Code\knowledage_island` 解析为 `E:\Dev\Projects\knowledage_island`，测试报模块不可访问，构建清理 `backend/static_dist` 报 EPERM；这不是依赖回归，需在获准的真实工作区路径权限下重跑。
- 2026-07-30：使用独立可写 `--basetemp` 后，`.venv\Scripts\python.exe -m pytest tests/test_backend tests/test_webapp -q` 实跑 `533 passed`；文档一致性脚本通过，文档/Tauri 契约 `37 passed`，Obsidian 插件 TypeScript 类型检查通过。
- 2026-07-30：插件 Vitest/构建与 Vue Vitest/构建仍被 Node/esbuild 对路径联接真实目录或沙箱父目录的访问限制阻断；在线 npm/pip 审计涉及向官方服务发送依赖元数据，Visual Studio Build Tools + Windows SDK 安装会更改系统并占用较大磁盘，三项均需用户明确批准后继续。
- 2026-07-30：用户明确批准在线依赖审计、真实路径 Node/Playwright 写入，以及 Visual Studio Build Tools、VCTools 与 Windows SDK 安装；plan 从 Interrupted 恢复为 Active，B-166 恢复为 doing。
- 2026-07-30：在线 npm 审计新增披露 `GHSA-mh99-v99m-4gvg`，原锁文件因 `minimatch@9.0.9 -> brace-expansion@2.1.2` 产生 6 个 high 传播节点。直接强制 `brace-expansion@5` 会破坏 9.0.9 的默认导入，升级 `js-beautify@2` 又会引入不兼容 CI Node 20 的依赖；最终用 `overrides.minimatch=9.0.8` 保持 9.x 上游约束，并自然解析到已修复的 `brace-expansion@5.0.9`。
- 2026-07-30：最终依赖树执行 `npm ci` 和在线 `npm audit --audit-level=high` 均通过，所有漏洞等级为 0；在线 `pip-audit` 报告 0 个已知漏洞。真实路径完成 Vue 22 文件 / 92 项单测、52 模块构建、Obsidian 插件 17 项测试 / typecheck / build，以及 Playwright Chromium 1 项主流程；另用 Node `v20.19.5` 复跑 92 项 Vue 单测通过。Python 533 项、文档一致性和 37 项文档/Tauri 契约继续通过。
- 2026-07-30：经用户批准安装 Visual Studio Build Tools 2022 `17.14.37`，核实 VCTools workload、MSVC `14.44.35207`、Windows 11 SDK `10.0.26100.0`、MSBuild `17.14.51.32402` 均可用，安装完整且无需重启。
- 2026-07-30：`cargo check --manifest-path src-tauri/Cargo.toml` 在 28.18 秒内通过；`npm run tauri:build:windows` 在 128.3 秒内完成 Vue 构建、PyInstaller sidecar、Rust release 与 NSIS bundle，生成 48,948,957 字节的 `Knowledge Island_2.0.0_x64-setup.exe`，SHA-256 为 `BD68D8FD29C53231595E164867910425A5403809A80A933A891D8EF83878C98B`。产物未签名，签名仍属于本阶段非目标。
- 2026-07-30：已同步 BACKLOG、readiness、测试/发布/环境指南、桌面与前端工程文档、README、CHANGELOG 和当日 devlog；明确本地候选与正式远端发布边界、Junction 真实路径、Actions 额度例外及未签名风险。`scripts/check_docs_consistency.py` 通过，文档与 Tauri 契约 `37 passed`。

## 9. 状态快照

- **最后更新**：2026-07-30 22:33
- **进度**：已完成 4 / 6 项（见 § 3 勾选状态）
- **最新 commit**：`1ecbc5c` — docs: 同步 v2.0.0 发布候选证据
- **代码状态**：`feature/project-knowledge-coach-v2`；依赖安全、本地 CI、Windows NSIS 和正式发布前文档回流均已完成并提交
- **下一步**：推送功能分支、创建 PR，记录本地 CI 证据并在无远端 CI 额度边界下合并 `main`
- **续任务须知**：当前工作区应保持干净；readiness 已明确本地候选、Actions 额度例外和未签名风险。下一步推送当前分支并以 PR head SHA 固定证据，人工复核后合并 `main`。
