# 桌面应用

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：Tauri 桌面壳承载的本地 Knowledge Island 体验
> Related：`../design/system-design-overview.md`、`../adr/ADR-010-runtime-separation.md`、`../guides/setup.md`、`../guides/testing.md`

## 1. 用户目标

用户通过桌面窗口使用与浏览器一致的项目导入、问答、学习计划和 Obsidian 用户流程，不需要另行手动启动后端。

## 2. 当前能力

- Tauri WebView 直接加载 `frontend/dist/`，并启动只包含后端的 sidecar。
- 桌面端和浏览器复用同一 Vue 页面与 HTTP/SSE API，不复制领域逻辑或 SQLite 访问。
- sidecar 绑定 `127.0.0.1:8765`；CORS 允许 Tauri Origin，CSP 的 `connect-src` 只允许 Tauri IPC 和本机 API。
- Rust 壳负责窗口、托盘和 sidecar 生命周期。

## 3. 当前限制

- 当前壳没有完整的 sidecar readiness 等待和端口占用恢复；页面已加载不代表 API 已就绪。
- Windows x64 NSIS 历史版本已发布但未签名；它不证明当前 commit 的包已经重新验证。
- macOS/Linux 需要在对应目标平台构建与动态验证，Windows 结果不能替代。
- bundle 成功不等于安装后导入、REST、SSE、学习计划和 Obsidian 流程通过。
