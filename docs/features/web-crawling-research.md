# 网页自动抓取研究

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-30
> Scope：B-119 网页自动抓取研究结论；本文件不代表已实现网页自动抓取
> Related：docs/requirements/project-background-and-scope.md, docs/requirements/functional-modules.md, docs/design/api-spec.md, docs/design/system-design-overview.md, docs/BACKLOG.md

## 1. 研究结论

B-119 结论：Knowledge Island 当前继续保持**手动 URL 摘录**能力，不在当前版本实现网页自动抓取、递归爬虫、动态页面渲染抓取或登录态网页抓取。

当前 `POST /api/import/url` 的定位保持不变：

- 用户手动填写 URL、标题和正文。
- 后端只保存用户提交的正文，不访问远端网页。
- `url:` 虚拟来源只用于标记来源，不代表系统具备联网抓取能力。
- 不新增 API、不新增数据库 schema、不新增运行时依赖。

网页自动抓取可以作为 B-132 的未来可选能力继续规划，但必须先满足显式启用、robots.txt 检查、SSRF 防护、请求限流、内容净化、版权/服务条款提示和可降级依赖隔离。未满足这些条件前，不应把"粘贴 URL"升级为"服务端自动访问 URL"。

## 2. 当前基线

| 领域 | 当前状态 |
|------|----------|
| 导入入口 | `/api/import/url` 接收 `url/title/content`，保存为 URL 摘录 |
| 网络行为 | 后端不联网、不请求 URL、不解析远端 HTML |
| 来源标记 | 文档来源路径使用 `url:` 虚拟来源，`relative_path` 为 `urls/<url-hash>.txt` |
| 批次类型 | `source_type` 使用 `url_excerpt`，表达"用户摘录"而不是"系统抓取" |
| 前端体验 | 用户在资料库页填写 URL 摘录表单，提交后刷新文档列表和批次历史 |
| 安全边界 | 现有系统仍是本地优先应用，默认不对外爬取第三方站点 |

这组边界与项目本期目标一致：导入本地文件、笔记和用户主动提供的文本，避免在 Web MVP 中引入不可控网络访问。

## 3. 风险评估

| 风险 | 影响 | B-132 前置约束 |
|------|------|----------------|
| robots.txt / 站点规则 | 站点可能禁止抓取特定路径；robots 不是授权机制，不能替代权限判断 | 抓取前读取并遵守 robots.txt；被拒绝时不抓取并提示用户 |
| 服务条款 / 版权 | 自动下载网页正文可能违反站点条款或版权使用边界 | UI 明确提示用户确认有权导入；保存来源 URL 和抓取时间 |
| SSRF | 用户提交 URL 后，服务端可能被诱导访问内网、localhost、云元数据或非 HTTP 资源 | 仅允许 `http/https`；禁止私网、回环、链路本地、保留地址；重定向后重新校验 |
| 隐私与认证 | 登录态网页、Cookie、内网页面可能把敏感内容带入知识库 | 不使用浏览器用户配置文件；不导入 Cookie；不支持登录态抓取 |
| 资源消耗 | 大页面、慢响应、无限重定向或动态页面会阻塞导入 | 设置超时、最大响应大小、最大重定向次数、并发上限和失败降级 |
| 内容安全 | HTML/script/style/二进制内容直接进入索引会污染 prompt 或检索 | 只保留正文文本；清理脚本、样式、表单、事件属性和超长内容 |
| 依赖复杂度 | Playwright 需要浏览器运行时，安装体积和跨平台打包成本高 | 默认不依赖 Playwright；如启用，必须作为可选依赖和单独验证链路 |
| 抓取质量 | 动态页面、反爬、分页、懒加载、PDF/图片内容不稳定 | 首个实现只支持单 URL 静态正文抽取；动态渲染留作高级选项 |

## 4. 方案判断

| 方案 | 判断 | 说明 |
|------|------|------|
| 保持手动 URL 摘录 | 推荐当前采用 | 零新增网络面，符合本地优先和最小依赖原则 |
| 单 URL 静态 HTTP 抓取 | 可作为 B-132 第一片 | 适合公开 HTML/纯文本页面；必须先做 URL 校验、robots 和大小/超时限制 |
| Playwright 动态渲染抓取 | 仅适合后续高级可选项 | 可处理 JS 渲染页面，但会带来浏览器下载、打包、资源消耗和安全隔离成本 |
| 递归爬虫 / sitemap 扫描 | 不进入当前路线 | 复杂度、合规和负载风险明显高于个人本地 RAG 的当前收益 |
| 登录态浏览器抓取 | 明确拒绝 | Cookie、账号权限和隐私边界不适合 Web MVP 默认能力 |

## 5. B-132 最小安全切片

若未来执行 B-132，推荐只做"用户手动触发的单 URL 抓取预览"：

1. 默认关闭；没有配置时 `/api/import/url` 行为完全不变。
2. 新增独立入口，例如 `/api/import/web-fetch/preview` 和 `/api/import/web-fetch/commit`，不复用 `url_excerpt` 的语义。
3. 用户每次输入一个 URL 并手动点击预览；系统不得后台递归抓取页面链接。
4. URL 校验只接受 `http` / `https`，拒绝凭据；非标准端口默认不放开，未来如确需支持必须单独配置 allowlist；拒绝 `file:`、`data:`、`gopher:` 等非 Web scheme。
5. DNS 解析和每次重定向后都检查目标 IP，拒绝回环、私网、链路本地、保留地址和本机 host。
6. 访问前读取 robots.txt，按固定 user-agent 判断是否允许抓取；禁止时返回可解释错误。
7. 设置请求超时、响应大小上限、最大重定向次数、content-type allowlist 和单项目并发上限。
8. 只抽取 `text/html`、`text/plain`、`text/markdown` 等文本内容；HTML 先净化再转正文。
9. 预览页展示标题、URL、正文长度、robots 状态、抓取时间和可能的版权/服务条款提示。
10. 用户确认后才入库；保存 `source_url`、`fetched_at`、`content_hash`、HTTP 状态和抽取器版本。
11. 失败不影响手动 URL 摘录、文件导入、检索和问答主流程。

这个切片解决的是"从公开网页取一份用户确认的正文快照"，不是通用爬虫平台。

## 6. 明确非目标

B-119 / B-132 后续不应直接包含：

- 自动递归抓取站内链接。
- sitemap 扫描、定时监控、持续同步和增量网页爬取。
- 登录页面、付费墙、论坛私信、云文档登录态内容。
- 导入浏览器 Cookie、浏览器 Profile 或系统代理凭据。
- 绕过 robots.txt、反爬机制、验证码或访问限制。
- 把原始 HTML、script、style 或二进制资源直接写入知识库。
- 把抓取能力暴露给 Agent 自动调用。
- 让模型根据回答过程自行决定访问外部 URL。

## 7. 验收建议

若未来新建实现任务，最低测试应覆盖：

- 默认关闭自动抓取时，现有 `POST /api/import/url` 仍只保存手动正文且不发起网络请求。
- robots.txt 禁止目标路径时，预览接口返回拒绝状态，不写入文档。
- `localhost`、`127.0.0.1`、`::1`、私网地址、链路本地地址和重定向到这些地址的 URL 均被拒绝。
- 非 `http/https` scheme 被拒绝。
- 超时、响应过大、content-type 不匹配、重定向过多时失败降级，并写入可诊断错误。
- HTML 中的 script/style/form/event handler 不进入最终正文。
- 预览成功后未点击确认不会创建文档、chunk、vector 或批次记录。
- 抓取成功入库后，来源、抓取时间、正文 hash 和批次历史可追踪。
- 抓取失败不影响文件上传、目录同步、文本笔记和手动 URL 摘录。

## 8. 参考资料

- [RFC 9309 Robots Exclusion Protocol](https://www.rfc-editor.org/rfc/rfc9309)：robots.txt 的标准语义和限制。
- [Python `urllib.robotparser`](https://docs.python.org/3/library/urllib.robotparser.html)：Python 标准库提供的 robots.txt 解析入口，可用于 `can_fetch` 判断。
- [OWASP SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)：用户可控 URL 触发服务端请求时需要的 SSRF 防护思路。
- [Playwright Python README](https://github.com/microsoft/playwright-python/blob/main/README.md)：Playwright Python 需要安装浏览器运行时，可导航页面并抽取动态页面，但应作为可选高级依赖评估。
