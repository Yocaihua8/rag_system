# ADR-018 桌面临时端点与进程期会话令牌

> 状态：Accepted
> Date：2026-08-03
> Owner：RAG 团队
> Scope：Tauri sidecar 端口、桌面 API 认证、令牌传递与 Web 部署分界
> Related：`ADR-005-remote-auth.md`、`ADR-010-runtime-separation.md`、`ADR-015-v3-data-api-storage.md`、`../design/permission-matrix.md`、`../guides/runbook.md`

## 1. 背景

当前正式 Tauri/Vue 固定连接 `127.0.0.1:8765`，本地认证默认关闭。固定端口容易与其他进程冲突；仅依赖 loopback 也不能阻止同一用户会话中的其他本地进程调用 API。v3 桌面目标需要每次启动独立的端口和不可复用的进程期凭证，同时不能把桌面凭证混入 Web 部署的 API Key/JWT 边界。

## 2. 决策

1. 新增默认关闭的 desktop mode。只有父进程显式设置 `KI_DESKTOP_MODE=1` 时启用；普通 Web、Docker 和现有 Vue/Tauri 默认行为不变。
2. desktop mode 只允许绑定精确 `127.0.0.1`。父 Tauri 进程选择当次空闲的非零端口，通过子进程环境传递；端口不写入配置文件或数据库。
3. 父进程每次启动生成 32 字节密码学随机值并编码为 64 位小写十六进制 `KI_DESKTOP_STARTUP_TOKEN`。令牌通过子进程环境传递，不进入命令行参数、日志、SQLite、文件、URL、localStorage 或 sessionStorage。
4. desktop mode 的普通 API、SSE、文档和 health 都要求请求头 `X-KI-Desktop-Token` 精确匹配。CORS 预检继续由精确 Origin allowlist 处理；已有 Obsidian 自认证回调路由保持其独立令牌边界。
5. desktop mode 与 ADR-005 的 Web API Key/JWT 二选一：启用 desktop mode 时，以进程期桌面令牌作为主应用认证；未启用时继续使用现有可选 API Key/JWT。两套凭证不互相兑换或持久化。
6. Tauri 只在 Rust managed state 中保存当次 endpoint 和 token，并仅向 `main` WebView 暴露受控 bootstrap command。前端不得获得通用 shell、任意环境变量或进程管理权限。
7. B-174 先实现并独立验证该能力，但保持默认关闭；正式 Tauri/React 接线和 CSP 切换必须等待 B-177 门禁。

## 3. 原因

- 临时端口降低端口冲突，进程期令牌补足 loopback 不是认证的缺口。
- 环境传递避免令牌出现在进程命令行；内存 bootstrap 避免形成长期凭证文件。
- 桌面与 Web 认证分开，可以保留独立 Web 部署的 API Key/JWT 兼容性，也避免桌面客户端承担浏览器登录和刷新 Token 逻辑。
- 默认关闭让安全基础可以先落地和测试，不破坏当前固定端口 Vue/Tauri 正式版本。

## 4. 备选方案

| 方案 | 结论 | 原因 |
|------|------|------|
| 继续固定 8765 且不认证 | 拒绝 | 端口冲突和同用户本地进程访问风险未解决 |
| 把令牌放 URL/query 或命令行参数 | 拒绝 | 容易进入日志、历史、进程列表和错误报告 |
| 把令牌写临时文件或浏览器存储 | 拒绝 | 扩大残留、权限和备份泄露面 |
| desktop mode 叠加 API Key/JWT | 拒绝 | 本地启动需要两套长期凭证，增加配置和恢复复杂度 |
| 给 WebView 开放通用 shell/environment | 拒绝 | 超出 bootstrap 所需最小权限，破坏 Tauri capability 边界 |

## 5. 影响

- 后端需要增加 desktop mode 配置、环回绑定校验、专用 Header 和认证兼容测试。
- CORS allow headers 需要精确加入 `X-KI-Desktop-Token`；Origin 仍禁止通配符和 credentials。
- Tauri 需要生成随机端口/令牌、通过 sidecar 环境传递并管理内存 bootstrap。
- CSP 在正式随机端口切换时需要允许 loopback 动态端口；这项变化必须与桌面令牌和真实安装包测试同时落地，不能提前放宽。
- 当前 Vue、固定 8765 和无令牌正式桌面路径继续保留，直到 B-177 明确切换。

## 6. 验证

- 配置测试拒绝短令牌、非十六进制令牌、非 loopback host、零端口和越界端口。
- 集成测试验证 missing/invalid/correct desktop token、health/docs/v2/v3 API、CORS preflight、Web API Key/JWT 兼容和 Obsidian 自认证例外。
- Rust 测试验证端口为 loopback 临时端口、令牌长度/字符集、bootstrap 仅内存保存且日志不包含令牌。
- 最终桌面门禁验证 sidecar 启动、真实 API/SSE、退出清理和端口复用；静态配置检查不能替代动态证明。

## 7. 回滚

保持或恢复 `KI_DESKTOP_MODE` 未启用即可回到当前 Web/固定端口行为。B-177 正式切换前不删除固定 8765 配置；回滚不得把进程期令牌写入长期配置作为兼容方案。

## 8. 与既有 ADR 的关系

- ADR-010 的前后端分离、API-only sidecar 和 loopback 原则继续有效；其中“Tauri 固定连接 8765”仅作为当前 v2 兼容事实，v3 目标由本 ADR 取代。
- ADR-005 的 API Key/JWT 继续适用于独立 Web 部署；不作为 desktop mode 的第二重凭证。
- ADR-015 的 v3 数据和 `/api/v3` 命名空间不变；桌面令牌在主 FastAPI 中间件统一保护 v2/v3 API。
