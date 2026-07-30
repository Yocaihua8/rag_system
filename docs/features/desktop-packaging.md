# Desktop Packaging

> 状态：Draft
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：B-145 Tauri Windows 打包验证；B-24 macOS / Linux 原生桌面打包入口；B-152 macOS / Linux 原生验证预检；B-165 v2.0.0 本地候选静态门禁；B-166 Windows v2 原生安装包验证

## 1. 目标

B-145 验证 Knowledge Island 的 C 端 Windows 桌面发行链路，B-24 在同一条 Tauri sidecar 链路上补齐 macOS `.dmg` 和 Linux `.AppImage` 的本机打包入口：Tauri 2 负责桌面壳、窗口和系统托盘；FastAPI 以 PyInstaller sidecar 形式随应用启动；Vue/Vite 生产构建产物作为 WebView 页面。

本功能文档覆盖 Tauri MVP 0 的桌面包生成入口。First-Run Wizard、自动更新、代码签名、公证、Linux 发行版依赖安装包适配不在本阶段范围内。

## 2. 运行形态

| 模式 | 前端来源 | 后端来源 | 用途 |
|------|----------|----------|------|
| Web 开发 | Vite dev server | `.venv\Scripts\python.exe app.py` | 本地开发 |
| Web 生产 | `backend/static_dist/` | `.venv\Scripts\python.exe app.py` | 浏览器使用 |
| Tauri Windows 桌面 | `backend/static_dist/` | `src-tauri/binaries/knowledge-island-backend-*-windows-msvc.exe` | Windows NSIS 桌面包验证 |
| Tauri macOS / Linux 桌面 | `backend/static_dist/` | `src-tauri/binaries/knowledge-island-backend-<target-triple>` | macOS `.dmg` / Linux `.AppImage` 本机打包 |

Tauri 桌面模式不修改现有 HTTP API。Vue 内部请求仍访问 `http://127.0.0.1:8765/api/*`。

B-147 后，旧 PySide6 / 六边形 `src/` 代码已归档到 `archive/src-desktop-legacy/`。B-155 后 Tauri sidecar 只打包当前 `app.py`、`backend/` 和 Vue/Vite 构建产物，不依赖 legacy 桌面代码。

## 3. Windows 打包边界

- `npm run build` 生成 Vue/Vite 生产构建产物。
- `scripts/build-backend-sidecar.ps1` 使用 PyInstaller 打包 `app.py`，并把生成的 exe 复制到 `src-tauri/binaries/`，文件名带 Tauri target triple。
- `npm run tauri:build:windows` 调用后端 sidecar 打包，再执行 Tauri Windows 构建。
- `src-tauri/tauri.conf.json` 的默认 `bundle.targets` 保持 `["nsis"]`，避免影响现有 Windows installer 产物。
- Tauri 启动时拉起 sidecar；窗口关闭时隐藏到托盘；通过托盘菜单退出时结束应用。
- 本机执行 Tauri 构建需要 Rust/Cargo/rustup；缺失时可先用 `npx tauri info` 确认环境缺口。
- Windows 资源生成需要 `src-tauri/icons/icon.ico`；缺失时 `cargo check` 会在 Tauri build script 阶段失败。
- 首次 Windows installer 打包会下载并缓存 Tauri 管理的 NSIS 工具包；网络超时会阻塞 installer 生成，但不代表 Rust release exe 构建失败。
- B-166 本机验证使用 Visual Studio Build Tools 2022 `17.14.37`、MSVC `14.44.35207`、Windows 11 SDK `10.0.26100.0` 和 MSBuild `17.14.51.32402`；`cargo check` 与完整 NSIS 构建均已通过。
- 当前 v2 NSIS 的 Authenticode 状态为 `NotSigned`，代码签名仍不在本阶段范围内；同一核验文件作为 `v2.0.0` GitHub Release 的 Windows x64 资产发布。

## 4. macOS / Linux 打包边界

- `scripts/build-backend-sidecar.sh` 使用 PyInstaller 打包 `app.py`，使用 Unix 资源分隔符把 `backend/static_dist/` 打入 sidecar，并把产物复制到 `src-tauri/binaries/knowledge-island-backend-<target-triple>`。
- sidecar target triple 默认从 `rustc -vV` 的 `host` 字段读取；需要覆盖时可设置 `KI_TAURI_TARGET_TRIPLE`。
- `npm run tauri:build:macos` 调用 Unix sidecar 脚本后执行 `tauri build --bundles dmg`，用于在 macOS 本机构建 `.dmg`。
- `npm run tauri:build:linux` 调用 Unix sidecar 脚本后执行 `tauri build --bundles appimage`，用于在 Linux 本机构建 `.AppImage`。
- 本阶段不在 Windows 上交叉生成 macOS `.dmg` 或 Linux `.AppImage`；需在对应原生系统安装 Node.js / npm、Python 依赖、`requirements-dev.txt`、Rust/Cargo/rustup 和 Tauri 平台依赖后执行。
- B-24 不新增自动更新、签名、公证、Linux deb/rpm 包或发行版依赖安装脚本。
- B-152 在 Windows 本机补齐并静态验证 `bundle.icon`：`src-tauri/icons/32x32.png`、`128x128.png`、`128x128@2x.png`、`icon.icns`、`icon.ico`。`.dmg` 与 `.AppImage` 产物仍需在 macOS / Linux 原生系统或对应 CI runner 上生成后回填验证结果。
- B-152 新增手动 GitHub Actions workflow：`.github/workflows/tauri-packaging.yml`。该 workflow 通过 `workflow_dispatch` 在 `macos-latest` 运行 `npm run tauri:build:macos`，在 `ubuntu-latest` 运行 `npm run tauri:build:linux`，并上传 `.dmg` / `.AppImage` 产物作为验证证据。

## 5. 验收标准

- `src-tauri/` 存在 Tauri 2 最小壳配置。
- `src-tauri/tauri.conf.json` 声明 `bundle.externalBin`，并将 `frontendDist` 指向 Vue/Vite 生产构建产物。
- `src-tauri/icons/icon.ico` 存在，可用于 Windows resource 生成；`src-tauri/icons/icon.icns` 与 PNG 图标存在，可用于 macOS / Linux 原生 bundle。
- Windows sidecar 构建脚本生成 `knowledge-island-backend-x86_64-pc-windows-msvc.exe`。
- Unix sidecar 构建脚本生成 `src-tauri/binaries/knowledge-island-backend-<target-triple>`。
- `package.json` 提供 `npm run tauri:build:macos` 和 `npm run tauri:build:linux`，分别生成 macOS `.dmg` 与 Linux `.AppImage`。
- Tauri Rust 入口包含 sidecar 启动、托盘菜单和关闭隐藏逻辑。
- 文档和测试命令覆盖桌面打包链路。
- `.github/workflows/tauri-packaging.yml` 可手动触发 macOS / Linux 原生打包验证。
- 完整 Windows 打包可生成 `src-tauri/target/release/bundle/nsis/Knowledge Island_<version>_x64-setup.exe`。
- 完整 macOS 打包在 macOS 本机生成 `src-tauri/target/release/bundle/dmg/*.dmg`。
- 完整 Linux 打包在 Linux 本机生成 `src-tauri/target/release/bundle/appimage/*.AppImage`。

## 6. B-152 验证记录

| 日期 | 环境 | 命令 / 检查 | 结果 | 说明 |
|------|------|-------------|------|------|
| 2026-06-30 | Windows PowerShell | `tests/test_webapp/test_tauri_packaging.py` | 通过 | 覆盖 Tauri 配置、Windows/Unix sidecar 脚本、跨平台图标清单、手动原生验证 workflow 和文档命令 |
| 2026-06-30 | Windows PowerShell | `npm run build`、`npx tauri info`、`cargo check --manifest-path src-tauri\Cargo.toml` | 通过 | 本地预检通过；`npx tauri info` 提示 `@tauri-apps/cli` 有 2.11.4 新版，不阻断当前 2.11.3 验证 |
| 2026-06-30 | GitHub Actions | `Tauri Packaging` run 28454356098 | 通过 | run URL：`https://github.com/Yocaihua8/rag_system/actions/runs/28454356098` |
| 2026-06-30 | `macos-latest` runner | `npm run tauri:build:macos` | 通过 | job 84324919388；上传 artifact `knowledge-island-macos-dmg`，大小 33,063,225 bytes |
| 2026-06-30 | `ubuntu-latest` runner | `npm run tauri:build:linux` | 通过 | job 84324919349；上传 artifact `knowledge-island-linux-appimage`，大小 136,877,112 bytes |

## 7. B-165 v2.0.0 本地候选验证

| 日期 | 环境 | 命令 / 检查 | 结果 | 说明 |
|------|------|-------------|------|------|
| 2026-07-24 | Windows PowerShell | `pytest tests/test_webapp/test_tauri_packaging.py -q` | 通过，11 项 | 配置、sidecar 名称、图标、跨平台脚本、版本一致性和文档契约通过 |
| 2026-07-24 | Windows PowerShell | `npm run build`、`cargo metadata --no-deps --format-version 1 --manifest-path src-tauri/Cargo.toml` | 通过 | Vue 构建成功；Cargo 识别桌面 crate 版本 `2.0.0` |
| 2026-07-24 | Windows PowerShell | `npx tauri info` | 完成诊断输出，命令未正常收尾 | 检测到 Rust/Cargo/WebView2，但未检测到含 MSVC 与 Windows SDK 的 Visual Studio Build Tools |
| 2026-07-24 | Windows PowerShell | `cargo check --manifest-path src-tauri/Cargo.toml` | 未通过（环境阻断） | `link.exe not found`；因此未执行 `npm run tauri:build:windows`，未生成或宣称 v2 Windows installer |
| 2026-07-24 | Windows | macOS `.dmg` / Linux `.AppImage` | 未执行 | 当前系统不做跨平台原生构建；保留 B-152 的历史 CI 证据，不将其冒充 v2 产物 |

## 8. B-166 v2.0.0 Windows 原生候选验证

| 日期 | 环境 | 命令 / 检查 | 结果 | 说明 |
|------|------|-------------|------|------|
| 2026-07-30 | Windows PowerShell | Visual Studio Build Tools / VCTools / Windows SDK 安装核验 | 通过 | Build Tools `17.14.37`、MSVC `14.44.35207`、Windows 11 SDK `10.0.26100.0`、MSBuild `17.14.51.32402`；安装完整且无需重启 |
| 2026-07-30 | Windows PowerShell | `cargo check --manifest-path src-tauri/Cargo.toml` | 通过 | 用时 28.18 秒，原 `link.exe not found` 环境阻塞已解除 |
| 2026-07-30 | Windows PowerShell | `npm run tauri:build:windows` | 通过 | 用时 128.3 秒；完成 Vue 构建、PyInstaller sidecar、Rust release 与 NSIS bundle |
| 2026-07-30 | Windows PowerShell | NSIS 文件、SHA-256 与 Authenticode 核验 | 通过（未签名候选） | `Knowledge Island_2.0.0_x64-setup.exe` 为 48,948,957 字节；SHA-256 `BD68D8FD29C53231595E164867910425A5403809A80A933A891D8EF83878C98B`；状态 `NotSigned` |
| 2026-07-30 | Windows / 本地 CI | npm/pip 安全审计、Python/Vue/插件/Playwright 等价矩阵 | 通过 | npm 所有严重等级为 0、pip-audit 为 0 个已知漏洞；Python 533 项、Vue 22 文件/92 项、插件 17 项和 Chromium Playwright 1 项通过，详见 v2 readiness |
| 2026-07-30 | GitHub Actions | PR #4 `python-tests` / `frontend-e2e` | 通过 | 初始额度约束未实际阻止 runner；两项 hosted check 均通过。Tauri Packaging workflow 未运行，Windows 产物仍以本机原生构建为证据 |
| 2026-07-30 | Windows | macOS `.dmg` / Linux `.AppImage` v2 构建 | 未执行 | 当前不是对应原生系统；B-152 历史产物不能替代 v2 原生产物证据 |

当前 Windows NSIS 产物路径为：

`src-tauri/target/release/bundle/nsis/Knowledge Island_2.0.0_x64-setup.exe`

该产物证明 Windows v2 原生打包链路可用；PR #4 的两项 CI 检查已通过并合并 `main`，`v2.0.0` Tag 与 GitHub Release 已发布同一正式提交，Windows Release 资产保持上述大小、SHA-256 与未签名边界。
