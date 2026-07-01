# Security Policy

## 支持版本

| 版本 | 是否支持安全修复 |
|------|----------------|
| latest（main 分支）| ✅ 是 |
| 历史 tag | ❌ 否（请升级至最新版本）|

## 漏洞上报渠道

Knowledge Island 是一个**本地单机应用**，HTTP 服务仅监听 `127.0.0.1:8765`，不对外网暴露。但如发现安全问题，请通过以下方式上报：

- **GitHub Issues**（公开问题）：适用于一般性安全建议或配置风险，优先使用
- **私信 / Email**：如涉及可利用的高危漏洞，请在 Issue 中简述风险级别，再通过私信提供细节

请**不要**在公开 Issue 中直接贴出完整漏洞利用代码。

## 响应承诺

| 阶段 | 时效目标 |
|------|----------|
| 确认收到上报 | 3 个工作日内 |
| 初步评估与回复 | 7 个工作日内 |
| 修复发布（高危）| 30 天内 |

本项目为个人兼职维护，以上为尽力承诺，不作法律保证。

## 已知安全边界

以下是本项目**设计层面的安全约束**，属于有意为之：

| 约束 | 说明 |
|------|------|
| API Key 不明文持久化 | Profile 只保存引用（`env:*` / `saved:*`），任何 API 响应不含明文 Key |
| Agent 工具只读限制 | 白名单硬编码，不开放 shell 执行或任意文件写入 |
| 本机访问限制 | HTTP 服务绑定 `127.0.0.1`，不监听外网接口 |
| Markdown 渲染 XSS 防护 | HTML 渲染层禁止 `<script>` 注入，raw HTML 经过清洗 |
| 跨项目数据隔离 | API 层强制校验 `project_id`，拒绝跨项目资源访问 |

## 依赖安全审计基线

B-154 起，v1.0.0 发布前和 B-149 CI 必须执行以下依赖审计：

```powershell
npm audit --audit-level=high
$env:PYTHONUTF8 = "1"
.venv\Scripts\pip-audit.exe -r requirements.txt -r requirements-dev.txt --progress-spinner off
```

CI 上使用 Linux venv 路径：

```bash
.venv/bin/pip-audit -r requirements.txt -r requirements-dev.txt
```

审计口径：

- `npm audit --audit-level=high` 将高危及以上前端依赖漏洞作为阻断项。
- `pip-audit` 只审计项目声明依赖文件：`requirements.txt` 与 `requirements-dev.txt`。
- Windows 本机 requirements 文件含中文注释时需设置 `PYTHONUTF8=1`，CI 已统一设置。
- 不使用 `pip-audit --local` 作为项目基线，避免把本机 venv 中与项目声明无关的历史包计入发布门禁。
- `requirements-docker.txt` 当前是 Web 运行时子集；若后续出现 Docker-only 依赖，应在发布前补充单独审计命令。

## 不在安全范围内

以下不属于本项目的安全保证范围：

- **本机物理访问安全**：任何能访问本机的用户均可访问 `127.0.0.1:8765`，本项目不提供本机用户间的认证隔离
- **Docker 网络配置**：Docker 部署时如用户自行修改端口映射导致服务暴露，责任在用户
- **第三方 LLM API 安全**：DeepSeek / OpenAI 等外部服务的数据处理政策由各服务商负责
