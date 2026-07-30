# Knowledge Island 安全政策
> Last Updated：2026-07-30
> Related：`docs/guides/security.md`、`docs/guides/support-policy.md`

## 支持范围

| 版本 | 安全维护状态 |
|------|--------------|
| `v2.0.x` | 当前维护线，按风险和维护能力提供修复 |
| `main` | 开发分支，不保证始终可发布 |
| `v1.x` 及更早 tag | 不提供常规安全修复；建议升级并重新导入数据 |

本项目以本地单用户使用为默认边界。默认 HTTP 服务绑定 `127.0.0.1:8765`，但 Docker 端口映射、远程访问、反向代理或用户自行修改绑定地址会扩大攻击面。

## 漏洞上报

请不要在公开 Issue、日志或截图中提交可直接利用的漏洞细节、Token、API Key、真实项目内容或个人数据。

1. 若仓库 GitHub **Security** 页面提供 “Report a vulnerability”，优先使用该私密入口。
2. 若没有可用私密入口，可创建不含利用细节的安全咨询 Issue，请维护者确认后续私密渠道。
3. 当前独立安全邮箱和固定响应人尚未公开核验，状态为 `TBD`。

上报建议包含受影响版本、攻击前提、影响范围、最小复现、建议缓解和是否已公开。维护者按实际可用时间尽力处理，不承诺固定 SLA；高风险问题在确认前不公开完整细节。

## 已落地安全边界

| 边界 | 当前实现 |
|------|----------|
| 本地监听 | 默认仅 `127.0.0.1:8765` |
| 可选认证 | `RAG_AUTH_ENABLED` 同时配合共享 API Key 与 HS256 JWT；默认关闭 |
| API Key | 模型 Profile 只保存 `env:*` / `saved:*` 引用，接口只返回配置状态和来源 |
| Agent 工具 | 白名单只有 `project_overview`、`search_sources`；无 shell、任意文件写入或业务写操作 |
| 项目隔离 | 资源读写校验 `project_id`；当前没有用户、团队、租户和 RBAC 表 |
| 网页抓取 | 只允许公网 HTTP/HTTPS 标准端口，限制重定向/响应大小并检查私网解析和 robots.txt |
| GitHub 导入 | 只接受 `github.com` HTTPS/SSH URL，拒绝 URL 内嵌凭据，使用浅克隆 |
| 文件导入 | 单文件默认上限 1 MB，跳过 `.git`、`.venv`、`node_modules` 和构建目录 |
| Obsidian | 只允许 loopback 服务；连接令牌放 Bearer header；发布执行路径、托管标记、revision 和 hash 校验 |
| v2 数据代际 | 正式 Web 启动拒绝把未标记为 v2 的非空旧库当作 v2 写入 |

## 已知限制

- 认证默认关闭；能访问本机账户或被暴露端口的主体可能读取本地项目数据。
- `/api/health` 仅说明进程响应，不验证 SQLite、模型、Embedding 或 Qdrant。
- Windows `v2.0.0` 安装包未做 Authenticode 签名。
- Tauri 打包配置/静态测试不替代安装包内 WebView 到 sidecar 的动态连通性和安全验证。
- 本项目没有声明适用的隐私、数据保留或行业合规承诺；处理敏感项目资料前由使用者自行评估。
- 第三方 LLM、Embedding、GitHub、Ollama、Obsidian 等组件的数据处理和漏洞响应受其各自政策约束。

## 依赖审计

```powershell
npm audit --audit-level=high
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\pip-audit.exe -r requirements.txt -r requirements-dev.txt --progress-spinner off
```

插件依赖在 `integrations/obsidian-plugin/` 单独执行 `npm audit`。审计项目声明依赖，不使用本机环境中无关的历史包替代项目基线。CI 配置了依赖审计，但每次报告只能引用当次实际执行结果。

## 安全变更要求

认证、权限、Agent 白名单、数据代际、插件令牌、发布写入边界或外部网络访问策略发生变化时，必须同步：

- `docs/guides/security.md`
- `docs/design/permission-matrix.md`
- 相关 API/数据库/功能文档
- 必要 ADR
- 安全测试和 `CHANGELOG.md`
