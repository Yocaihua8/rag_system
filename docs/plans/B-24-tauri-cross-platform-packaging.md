# B-24 Tauri 跨平台桌面打包（macOS / Linux）

> 状态：Active
> 创建时间：2026-06-29
> 创建方：Codex
> 关联 BACKLOG：B-24
> 关联功能文档：docs/features/desktop-packaging.md
> 关联设计文档：docs/design/architecture-overview.md

## 1. 目标

在不破坏 B-145 Windows NSIS 打包链路的前提下，为 Tauri 2 桌面壳补齐 macOS `.dmg` 与 Linux `.AppImage` 的本机打包入口、sidecar 构建脚本、静态回归测试和发布文档。

## 2. 前置条件

- 已读取 `AGENTS.md`、`README.md`、`docs/BACKLOG.md`、`docs/features/desktop-packaging.md`、`docs/guides/release-process.md`、`docs/guides/testing.md`、`package.json`、`src-tauri/tauri.conf.json`、`tests/test_webapp/test_tauri_packaging.py`。
- 已用 Context7 查询 Tauri 2 文档，确认 `.dmg` 可通过 `tauri build -- --bundles dmg` 构建，AppImage 可通过 `tauri build -- --bundles appimage` 构建，sidecar 继续由 `bundle.externalBin` 注册。
- 当前 checkout 不是 linked worktree，且存在非 B-24 既有未提交改动；执行时只暂存 B-24 相关文件和 hunk。
- 本任务在 Windows 环境执行，不能真实产出 macOS `.dmg` 或 Linux `.AppImage`；验收以静态契约、`npm run build`、`npx tauri info` 和可运行的本机测试为准。

## 3. 任务拆解

- [ ] 补充 Tauri 跨平台打包红灯测试，覆盖 Unix sidecar 脚本、macOS/Linux npm scripts、文档契约和 Windows 链路兼容。
- [ ] 新增 `scripts/build-backend-sidecar.sh`，补 `package.json` 的 macOS/Linux 打包命令，并保持 Windows NSIS 命令不变。
- [ ] 同步桌面打包、发布流程、测试指南和 BACKLOG，完成验证后删除本 plan。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 脚本 | `scripts/build-backend-sidecar.sh` | 新增 |
| 配置 | `package.json` | 修改 |
| 测试 | `tests/test_webapp/test_tauri_packaging.py` | 修改 |
| 文档 | `docs/features/desktop-packaging.md` | 修改 |
| 文档 | `docs/guides/release-process.md` | 修改 |
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

创建本 plan 时扫描到 3 个 `docs/superpowers/plans/` 旧 plan，影响范围集中在 legacy 桌面端、领域模型与历史文档，不涉及 `src-tauri/`、`scripts/build-backend-sidecar.*`、`package.json` 或 B-24 文档。

## 6. 完成标准

- [ ] 功能行为符合 `docs/features/desktop-packaging.md` 的边界
- [ ] `tests/test_webapp/test_tauri_packaging.py` 通过
- [ ] `npm run build` 通过
- [ ] `npx tauri info` 可运行，或记录缺失工具链原因
- [ ] 相关文档已同步（见下方"回流清单"）
- [ ] BACKLOG 条目 `B-24` 状态已更新为 `done`

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| macOS `.dmg` / Linux `.AppImage` 打包入口与限制 | `docs/features/desktop-packaging.md` | [ ] |
| 发布流程跨平台桌面打包步骤 | `docs/guides/release-process.md` | [ ] |
| Tauri 打包验证命令 | `docs/guides/testing.md` | [ ] |
| B-24 完成状态 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-06-29：B-24 不尝试在 Windows 上交叉编译 `.dmg` / `.AppImage`；只补本机 macOS/Linux 打包入口和静态契约验证。
- 2026-06-29：保持 `npm run tauri:build:windows` 继续走 `scripts/build-backend-sidecar.ps1` + NSIS，不把 Linux/macOS bundle target 写成 Windows 默认构建目标。

## 9. 状态快照

- **最后更新**：2026-06-29 00:00
- **进度**：已完成 0 / 3 项（见 § 3 勾选状态）
- **最新 commit**：`N/A` — 尚未提交
- **代码状态**：`fix/b-08-concurrent-index`；工作区存在非 B-24 既有改动，需精确暂存
- **下一步**：补充 Tauri 跨平台打包红灯测试，覆盖 Unix sidecar 脚本、macOS/Linux npm scripts、文档契约和 Windows 链路兼容
- **续任务须知**：只暂存 B-24 相关文件和 `docs/BACKLOG.md` 的 B-24 hunk
