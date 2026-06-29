# Desktop Packaging

> 状态：Draft
> Owner：RAG 团队
> Last Updated：2026-06-29
> Scope：B-145 Tauri 桌面壳 — Windows 打包验证

## 1. 目标

B-145 验证 Knowledge Island 的 C 端 Windows 桌面发行链路：Tauri 2 负责桌面壳、窗口和系统托盘；FastAPI 以 PyInstaller sidecar 形式随应用启动；Vue/Vite 生产构建产物作为 WebView 页面。

本功能文档只覆盖 Tauri MVP 0。First-Run Wizard、自动更新、代码签名、macOS `.dmg` 和 Linux `.AppImage` 属于 B-148、B-149、B-150。

## 2. 运行形态

| 模式 | 前端来源 | 后端来源 | 用途 |
|------|----------|----------|------|
| Web 开发 | Vite dev server | `.venv\Scripts\python.exe app.py` | 本地开发 |
| Web 生产 | `webapp/static_dist/` | `.venv\Scripts\python.exe app.py` | 浏览器使用 |
| Tauri 桌面 | `webapp/static_dist/` | `src-tauri/binaries/knowledge-island-backend-*-windows-msvc.exe` | Windows 桌面包验证 |

Tauri 桌面模式不修改现有 HTTP API。Vue 内部请求仍访问 `http://127.0.0.1:8765/api/*`。

B-147 后，旧 PySide6 / 六边形 `src/` 代码已归档到 `archive/src-desktop-legacy/`。Tauri sidecar 只打包当前 `app.py`、`webapp/`、`backend/` 和 Vue/Vite 构建产物，不依赖 legacy 桌面代码。

## 3. Windows 打包边界

- `npm run build` 生成 Vue/Vite 生产构建产物。
- `scripts/build-backend-sidecar.ps1` 使用 PyInstaller 打包 `app.py`，并把生成的 exe 复制到 `src-tauri/binaries/`，文件名带 Tauri target triple。
- `npm run tauri:build:windows` 调用后端 sidecar 打包，再执行 Tauri Windows 构建。
- Tauri 启动时拉起 sidecar；窗口关闭时隐藏到托盘；通过托盘菜单退出时结束应用。
- 本机执行 Tauri 构建需要 Rust/Cargo/rustup；缺失时可先用 `npx tauri info` 确认环境缺口。
- Windows 资源生成需要 `src-tauri/icons/icon.ico`；缺失时 `cargo check` 会在 Tauri build script 阶段失败。
- 首次 Windows installer 打包会下载并缓存 Tauri 管理的 NSIS 工具包；网络超时会阻塞 installer 生成，但不代表 Rust release exe 构建失败。

## 4. 验收标准

- `src-tauri/` 存在 Tauri 2 最小壳配置。
- `src-tauri/tauri.conf.json` 声明 `bundle.externalBin`，并将 `frontendDist` 指向 Vue/Vite 生产构建产物。
- `src-tauri/icons/icon.ico` 存在，可用于 Windows resource 生成。
- Windows sidecar 构建脚本生成 `knowledge-island-backend-x86_64-pc-windows-msvc.exe`。
- Tauri Rust 入口包含 sidecar 启动、托盘菜单和关闭隐藏逻辑。
- 文档和测试命令覆盖桌面打包链路。
- 完整 Windows 打包可生成 `src-tauri/target/release/bundle/nsis/Knowledge Island_0.1.0_x64-setup.exe`。
