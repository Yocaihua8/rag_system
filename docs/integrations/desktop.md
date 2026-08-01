# Tauri 桌面集成

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：Tauri 2 WebView、前端产物、后端 sidecar、CSP 与平台验证
> Related：`../architecture/decisions/ADR-010-runtime-separation.md`、`../operations/setup.md`、`../operations/testing.md`

## 1. 组成

| 组件 | 当前边界 |
|------|----------|
| WebView | 直接打包 `frontend/dist/` |
| 后端 | PyInstaller sidecar，只包含 `backend/` 运行时 |
| npm 工具 | `src-tauri/package.json` workspace 中的 Tauri CLI |
| Rust | `src-tauri/src/` 管理窗口、托盘和 sidecar 生命周期 |

Tauri 不复制领域业务、SQLite 访问或 API 状态机。前端通过绝对 `http://127.0.0.1:8765` 访问 sidecar。

## 2. 构建

```powershell
npm run frontend:build
cargo check --manifest-path src-tauri/Cargo.toml
npm run desktop:dev
npm run desktop:build:windows
```

sidecar 脚本位于 `src-tauri/scripts/`，以 `backend/__main__.py` 为入口，产物进入 `src-tauri/binaries/`。前端不打入 sidecar。

macOS/Linux 必须在目标平台安装对应 Tauri 系统依赖后运行各自 workspace 构建命令；Windows 结果不替代其他平台。

## 3. 网络与 CSP

- 后端只监听 loopback `127.0.0.1:8765`。
- 后端 CORS 默认允许 Tauri Origin。
- CSP `connect-src` 仅允许 Tauri IPC 与 `http://127.0.0.1:8765`；不得为方便调试放宽为任意网络。
- 浏览器和 Tauri 使用相同 API helper，不依赖 Vite proxy。

## 4. 验证边界

结构契约、`cargo check`、sidecar 构建和 bundle 是不同门禁。发布前还需在安装后的应用中验证：

1. sidecar 成功启动并退出清理；
2. WebView 到 8765 的 CORS 和认证 header；
3. REST 与 SSE；
4. 导入、问答、学习计划和 Obsidian 用户流程；
5. 安装包签名状态。

`v2.0.0` 的 Windows x64 NSIS 已发布但未签名。历史 macOS/Linux 产物不作为当前重构后包的通过证据。
