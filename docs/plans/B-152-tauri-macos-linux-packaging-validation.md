# B-152 macOS/Linux Tauri 打包原生验证

> 状态：Active
> 创建时间：2026-06-30
> 创建方：Codex
> 关联 BACKLOG：B-152
> 关联功能文档：docs/features/desktop-packaging.md
> 关联设计文档：N/A（不变更 API、数据库或架构边界）

## 1. 目标

补齐 Tauri macOS/Linux 打包链路中当前仓库可静态验证的图标、配置、测试和文档记录，并在无法访问目标原生系统时明确记录未完成的 `.dmg` / `.AppImage` 原生验证边界。

## 2. 前置条件

- 已读取 `AGENTS.md`、`docs/README.md`、`CONTRIBUTING.md`、`docs/BACKLOG.md`、`docs/features/desktop-packaging.md`、`docs/guides/setup.md`、`docs/guides/testing.md`、`docs/guides/release-process.md`。
- 当前执行环境为 Windows PowerShell；无法在本机会话中直接生成 macOS `.dmg` 或 Linux `.AppImage`。
- Context7 查询 Tauri 文档时返回 `fetch failed`；后续以本地 Tauri CLI `--help` 与仓库配置测试为准。

## 3. 任务拆解

- [ ] 补齐 macOS/Linux Tauri 图标与配置静态测试，运行本地可执行验证，并同步桌面打包文档与 BACKLOG 状态。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `src-tauri/tauri.conf.json` | 修改：显式声明跨平台 bundle icon |
| 资源 | `src-tauri/icons/` | 新增：Tauri 生成的 macOS/Linux/Windows 图标资源 |
| 测试 | `tests/test_webapp/test_tauri_packaging.py` | 修改：覆盖跨平台图标配置和资源存在性 |
| 文档 | `docs/features/desktop-packaging.md` | 修改：记录 B-152 本地验证范围、平台限制和待原生验证项 |
| 文档 | `docs/guides/setup.md` | 修改：补充 Unix 图标与原生验证说明 |
| 文档 | `docs/guides/testing.md` | 修改：补充 B-152 验证口径 |
| 文档 | `docs/BACKLOG.md` | 修改：任务状态流转 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | 无未完成依赖 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| N/A | N/A | N/A |

## 6. 完成标准

- [ ] `src-tauri/tauri.conf.json` 显式声明跨平台 `bundle.icon`。
- [ ] `src-tauri/icons/` 包含 macOS/Linux 可用图标资源。
- [ ] `tests/test_webapp/test_tauri_packaging.py` 覆盖跨平台图标配置和资源存在性。
- [ ] 本地运行 `tests/test_webapp/test_tauri_packaging.py`、`npm run build`、`npx tauri info`。
- [ ] 文档记录 Windows 本机无法完成 macOS/Linux 原生产物验证的原因和后续原生系统验证命令。
- [ ] BACKLOG 条目 B-152 状态已按实际结果更新。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 跨平台图标配置和资源要求 | `docs/features/desktop-packaging.md` | [ ] |
| B-152 本地验证口径和非目标平台限制 | `docs/guides/testing.md` | [ ] |
| macOS/Linux 原生打包操作说明 | `docs/guides/setup.md` | [ ] |

## 8. 执行记录

- 2026-06-30：当前会话运行在 Windows，不能直接生成 macOS `.dmg` 或 Linux `.AppImage`；本 plan 将如实区分“本地静态/预检完成”和“原生产物待目标系统验证”。
- 2026-06-30：本地补齐 Tauri 桌面 bundle 图标，修正 macOS/Linux npm 脚本中的 `tauri build -- --bundles ...` 参数位置，新增手动 GitHub Actions 原生打包 workflow。
- 2026-06-30：本地验证已通过 `tests/test_webapp/test_tauri_packaging.py`、`npm run build`、`npx tauri info`、`cargo check --manifest-path src-tauri\Cargo.toml`、`scripts/check_docs_consistency.py`。

## 9. 状态快照

- **最后更新**：2026-06-30 00:00
- **进度**：已完成 0 / 1 项（见 § 3 勾选状态）
- **最新 commit**：N/A
- **代码状态**：main；本地有待提交改动；本地分支较 `origin/main` ahead 3
- **下一步**：提交并推送本地预检改动，触发 `.github/workflows/tauri-packaging.yml`，等待 macOS / Linux runner 结果
- **续任务须知**：GitHub Actions 通过后，将 run URL、`.dmg` / `.AppImage` 产物证据回流到 `docs/features/desktop-packaging.md`，再将 B-152 标记为完成并删除本 plan；若失败，保留 B-152 为 `doing` 或 `blocked` 并记录失败日志
