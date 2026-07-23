# B-165 Knowledge Island 2.0 发布验收

> ⚠️ 创建此文件前，必须已完成以下操作（AI 自检）：
> - [x] `docs/BACKLOG.md` 中 B-165 状态为 `doing`
> - [x] B-165 说明列已填入本文件路径
> - [x] 关联功能文档和设计文档已按实际范围填写

> 状态：Active
> 创建时间：2026-07-23
> 创建方：Codex
> 关联 BACKLOG：B-165
> 关联功能文档：docs/features/project-knowledge-coach.md, docs/features/frontend-engineering.md, docs/features/desktop-packaging.md
> 关联设计文档：docs/design/architecture-overview.md, docs/design/api-spec.md, docs/design/ui-wireframes.md

## 1. 目标

修复当前阻断完整验收的 Windows E2E 服务退出问题和 Tauri 静态测试旧契约，统一应用、OpenAPI 与桌面壳版本为 `2.0.0`，执行用户指定的后端、Vue、浏览器、Obsidian 插件、文档和 Tauri 验证，并把真实结果收口为仅限本地功能分支的发布候选证据。不得声称已创建 Git Tag、推送远端、合并 `main` 或生成未经本机工具链验证的原生产物。

## 2. 前置条件

- B-160～B-164 已完成，B-159 视觉基线受保护，B-157 保持 `wontfix`
- 旧 `runtime/app.db`、`runtime/webapp/knowledge_island.db` 和 `runtime/vectors/chroma.sqlite3` 的基线 SHA-256 已记录，验收后必须复核未变化
- Context7 因月度额度不可用；Obsidian 插件实现已依据官方文档、官方类型和本地测试验证

## 3. 任务拆解

- [x] 修复 Windows E2E webServer 退出清理和 Tauri sidecar 静态测试旧契约，并补充回归测试
- [x] 统一 Web、OpenAPI 与 Tauri 版本为 `2.0.0`，同步 CHANGELOG 和版本契约测试
- [x] 执行完整发布验收矩阵、复核旧运行时哈希和本机原生工具链边界，形成发布就绪记录并回流正式文档

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `tests/e2e/start-web-server.mjs` | 修复 Windows 信号清理与幂等退出 |
| 测试 | `tests/test_webapp/test_e2e_ui.py`, `tests/test_webapp/test_tauri_packaging.py`, `tests/test_webapp/test_fastapi_server.py`, `tests/test_webapp/test_v2_coach_end_to_end.py` | 更新 E2E、sidecar 与 OpenAPI 版本契约，并覆盖项目教练到 Obsidian 发布结果回传的后端集成闭环 |
| 配置 | `package.json`, `package-lock.json`, `src-tauri/tauri.conf.json`, `src-tauri/Cargo.toml`, `src-tauri/Cargo.lock`, `backend/api/openapi_schema.py` | 统一 `2.0.0` 版本 |
| 文档 | `CHANGELOG.md`, `docs/release/V2_0_0_READINESS_2026-07-24.md`, `docs/guides/release-process.md`, `docs/guides/setup.md`, `docs/features/desktop-packaging.md` | 记录发布候选边界与验证证据 |
| 文档 | `docs/README.md`, `docs/requirements/project-background-and-scope.md`, `docs/requirements/mvp-scope-freeze.md`, `docs/requirements/use-cases.md`, `docs/requirements/functional-modules.md` | 将产品范围、用例、模块和 B-165 状态回流为真实完成状态 |
| 文档 | `docs/design/architecture-overview.md`, `docs/design/codex-workspace-chat-import-design.md`, `docs/design/database-design.md`, `docs/design/risk-register.md`, `docs/design/ui-wireframes.md`, `docs/features/project-knowledge-coach.md`, `docs/features/frontend-engineering.md`, `docs/guides/testing.md` | 同步当前架构、数据代际、残余风险、界面和验证事实 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-164 已完成并删除其 plan |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

> 已扫描 `docs/plans/` 与 `docs/superpowers/plans/`；除说明生命周期规则的 `docs/plans/README.md` 外，没有其他 `Active` 或 `Interrupted` 执行 plan。

## 6. 完成标准

- [x] `npm run test:e2e` 浏览器用例和退出清理均成功，命令正常返回 0
- [x] 后端/Web、Vue、插件、文档和 Tauri 静态验证按用户指定矩阵通过
- [x] 应用、OpenAPI 与 Tauri 版本统一为 `2.0.0`
- [x] 旧 1.x 运行时三个基线文件的 SHA-256 未变化
- [x] 发布记录区分本地发布候选、原生产物、Git Tag、远端推送和 `main` 合并
- [x] 相关文档已同步（见下方回流清单）
- [ ] BACKLOG B-165 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| `v2.0.0` 功能变更与兼容边界 | `CHANGELOG.md`, `docs/requirements/mvp-scope-freeze.md` | [x] |
| 完整命令、测试数量和运行时哈希 | `docs/release/V2_0_0_READINESS_2026-07-24.md`, `docs/guides/testing.md` | [x] |
| Web/Tauri 版本、打包与本地发布边界 | `docs/features/desktop-packaging.md`, `docs/guides/release-process.md`, `docs/guides/setup.md` | [x] |
| B-165 当前完成状态 | `docs/README.md`, `docs/design/architecture-overview.md`, `docs/design/ui-wireframes.md`, `docs/features/project-knowledge-coach.md`, `docs/features/frontend-engineering.md` | [x] |
| 产品范围、用例、模块、数据与残余风险 | `docs/requirements/project-background-and-scope.md`, `docs/requirements/use-cases.md`, `docs/requirements/functional-modules.md`, `docs/design/database-design.md`, `docs/design/risk-register.md`, `docs/design/codex-workspace-chat-import-design.md` | [x] |

## 8. 执行记录

- 2026-07-23：B-164 浏览器 smoke 用例已通过，但 `tests/e2e/start-web-server.mjs` 在 Windows 上将清理信号再次转发给自身，导致 `npm run test:e2e` 无法正常退出；B-165 先修复验收工具再运行最终矩阵。
- 2026-07-23：`src-tauri/src/main.rs` 的 `.sidecar("knowledge-island-backend")` 是已修复的正确调用，`tauri.conf.json` 的 `externalBin` 仍应保留 `binaries/knowledge-island-backend`；只更新过时的静态测试断言。
- 2026-07-23：不改写 `docs/release/V1_0_0_READINESS_2026-07-01.md` 历史证据；本次另建 2.0 发布就绪记录。
- 2026-07-23：仅移除 wrapper 的二次信号仍不足以解决 Playwright 在 Windows 上等待进程树关闭的问题；最终由测试专用 FastAPI 外层提供 `/__e2e__/shutdown`，Playwright `globalTeardown` 在全套用例结束后主动关闭 Uvicorn，wrapper 同时保留幂等信号兜底。16 项 E2E/Tauri 静态回归通过，`npm run test:e2e` 的 1 项浏览器用例通过并在 10 秒内返回 0，端口无监听残留。
- 2026-07-23：根 npm 包、OpenAPI、Tauri 配置、Cargo manifest/lock 已统一为 `2.0.0`，Obsidian 插件原本已是 `2.0.0`；CHANGELOG 新增 2.0 功能、破坏性数据代际、兼容与安全边界。20 项 FastAPI/Tauri 契约、Vue 生产构建、文档一致性和 `cargo metadata` 通过。
- 2026-07-24：最终矩阵通过 533 项后端/Web pytest、22 个文件 92 项 Vue Vitest、52 模块生产构建、1 项 Playwright 浏览器主流程、17 项 Obsidian 插件测试、插件 typecheck/build、文档一致性及 37 项文档/Tauri 组合契约。Playwright 命令正常返回 0，18765 端口无监听残留。
- 2026-07-24：三个旧运行时文件的 SHA-256 与 B-161 前基线完全一致。`cargo metadata` 和 PyInstaller 预检通过；`npx tauri info` 输出诊断但未在 180 秒内正常结束，`cargo check` 因本机缺少 MSVC `link.exe` 失败，因此未执行或宣称 v2 原生安装包通过。
- 2026-07-24：提交 `7124958` 新增隔离数据库的“项目导入 → 分析 → 同步/流式问答 → 定向评估 → 技能差距 → 计划编辑/确认 → Obsidian 配对/预览/确认/结果回传”集成闭环，并形成 v2 本地候选 readiness；CHANGELOG 保持 `Unreleased`，目标版本为 `v2.0.0`。

## 9. 状态快照

- **最后更新**：2026-07-24
- **进度**：已完成 3 / 3 项
- **最新 commit**：`7124958` — test: 完成 v2.0.0 本地发布验收
- **代码状态**：`feature/project-knowledge-coach-v2`；功能、测试和正式文档已收口，待关闭 B-165
- **下一步**：将 BACKLOG B-165 更新为 `done`，删除本 plan 并提交治理收口
- **续任务须知**：正式 Tag、推送、合并、GitHub Release 和 v2 原生安装包均未执行；不得将本地候选写成正式发布
