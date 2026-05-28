# 2026-05-20 本地 Web MVP 收口说明

> 目标：确认默认本地 Web MVP 可用于个人项目资料导入、检索、问答和来源查看
> Owner：RAG 团队
> 适用范围：`app.py` 启动的本机 Web 服务
> 说明：本文是 2026-05-20 收口快照；2026-05-22 后新增能力以 `README.md`、`docs/design/api-spec.md`、`docs/BACKLOG.md`、`docs/DEVLOG.md` 和 `CHANGELOG.md` 为准。

## 1. 可交付范围

- 默认入口：运行 `app.py` 后启动 `http://127.0.0.1:8765`。
- 项目空间：创建、选择、改名、删除本地项目空间。
- 本地目录导入：导入 Markdown、TXT、DOCX、代码与配置类文件；PDF 暂无无依赖正文解析，会显示明确跳过原因。
- 浏览器文件夹导入：Docker 模式下可通过“选择文件夹导入”直接选择 Windows 本地目录，浏览器上传文本或 DOCX 内容入库。
- 导入保护：跳过常见依赖、缓存、版本库和本机工具配置目录；跳过超过 1MB 的单文件；读取失败单独展示错误。
- 增量导入：展示新增、更新、未变更、删除、跳过数量；源目录删除的文件会同步清理记录。
- 文档管理：查看已导入文件列表、路径过滤、数量提示、文件预览、移除单条文档记录。
- 检索问答：支持独立关键词检索；未配置模型时基于命中片段组合回答，配置 DeepSeek / OpenAI 兼容 API 后优先使用真实 LLM 并展示来源。
- 掌握评估：支持从已导入文件生成最小评估题，提交回答后给出规则化反馈和建议阅读来源。
- 首次引导：首页展示创建项目空间、导入目录、提问/评估、配置 DeepSeek 的最小步骤。
- 异常提示：无项目空间、目录不存在、空问题、空关键词、无文件、无来源等状态有明确提示。

## 2. 非承诺范围

- 不提供远程多用户部署和权限系统。
- 不承诺高质量语义检索、Reranker 或云端 LLM 生成质量；2026-05-22 后 Web MVP 已具备轻量向量召回，可使用本地 hashing 向量或用户配置的 OpenAI-compatible Embeddings。
- 发布脚本可生成 Windows 打包产物，Docker 模式已提供双击启动/停止入口；但尚未完成安装器、桌面快捷方式或非技术用户一键安装流程。
- 不删除 legacy PySide6 桌面端代码；`src/desktop/` 仅作为迁移参考保留。

## 2.1 后续已补充能力（截至 2026-05-22）

- 浏览器文件夹导入已支持 DOCX/PDF 二进制上传；PDF 正文抽取依赖可选 `pymupdf`，未安装时仍明确跳过。
- Web MVP 已接入 `document_chunks` 与 `chunk_vectors`，检索和问答按 chunk 片段做 keyword + vector 混合召回。
- 工作台已补充检索调试、来源质量提示和检索复盘保存。
- 资料库页已补充文本笔记导入，使用 `note:` 虚拟来源并避免被目录同步误删。
- Agent 只读工具已补充运行历史和 `search_sources` 工具来源回填到下一轮问答上下文。
- 首次使用引导已改为设置页创建项目空间、选择本机文件夹导入、提问/评估和设置页配置模型；关键异步按钮运行中会禁用并显示进行中状态。

## 3. 验收命令

```powershell
.venv\Scripts\python.exe -m pytest tests\test_webapp -q
.venv\Scripts\python.exe -m pytest tests\test_domain tests\test_application tests\test_adapters -q
.venv\Scripts\python.exe scripts\check_docs_consistency.py
.venv\Scripts\python.exe -m compileall -q app.py webapp
Get-ChildItem webapp\static\js\*.js | ForEach-Object { node --check $_.FullName }
.\scripts\docker_down.ps1
.\scripts\docker_up.ps1 -NoOpen
```

## 4. 浏览器验收清单

1. 启动 `app.py`，打开 `http://127.0.0.1:8765`。
2. 点击“选择本机文件夹导入”，选择一个包含 Markdown、TXT、DOCX、PDF 或代码文件的本地项目目录，确认自动创建项目空间并显示导入统计。
3. 如需验证挂载目录导入，再创建项目空间，路径填写一个真实存在且对后端可见的目录，点击“导入”。
4. 点击文件列表中的文件，确认右侧文件预览显示正文。
5. 输入关键词并点击“搜索”，确认结果可点击并打开文件预览。
6. 输入问题并点击“提问”，确认回答、回答模式和来源列表同时出现。
7. 点击“开始评估”，确认生成题目；输入回答并提交，确认反馈、得分和建议阅读来源出现。
8. 删除或移动项目根目录后刷新页面，确认显示“目录不存在”，点击“导入”时前端直接阻止。

## 5. 当前风险

- 浏览器文件夹导入依赖 Chromium/Edge 等支持 `webkitdirectory` 的浏览器；不支持该能力的浏览器仍可使用挂载目录导入。
- PDF 正文抽取依赖可选 `pymupdf`；未安装解析器、PDF 无文本或文件无效时仍会明确跳过。
- 未配置或无法访问 DeepSeek 时，问答会回退为关键词片段组合；复杂总结质量有限。
- 当前发布面向开发者或技术用户本机试用；Windows zip 产物需要实际打包验收后才能交给非技术用户。

## 6. Windows 打包验收记录

2026-05-20 已执行真实打包：

```powershell
.\scripts\release_windows.ps1 -SkipCheck -ZipOutput
```

结果：

- 产物目录：`release\dist\KnowledgeIsland`
- 启动入口：`release\dist\KnowledgeIsland\Run_KnowledgeIsland.bat`
- zip 包：`release\KnowledgeIsland_win64.zip`
- 打包后冒烟：运行 bat 后 `GET /api/health` 返回 `{"status":"ok"}`。
- 打包后功能冒烟：创建项目空间、导入 1 个文件、问答返回 1 个来源、掌握评估生成 1 道题。

限制：当前是 zip + bat 运行包，不是安装器；尚未提供桌面快捷方式自动创建。

## 7. Docker 一键启动验收记录

2026-05-21 已执行真实 Docker 启动：

```powershell
.\scripts\docker_up.ps1 -NoOpen
```

结果：

- Compose 服务：`knowledge-island-web`
- 镜像：`knowledge-island-web:local`
- 访问地址：`http://127.0.0.1:8765`
- 健康状态：`healthy`
- DeepSeek Key 注入：已检测到布尔值 `True`，未输出 Key
- Docker 导入目录：容器内 `/workspace`，宿主机 `docker-workspace/`
- 功能冒烟：创建项目空间、导入 1 个文件、DeepSeek 问答 `answerMode=api/provider=deepseek`、来源数 1

限制：Docker 模式仍需用户安装并启动 Docker Desktop；使用挂载目录导入时，Web 页面中本地目录需填写容器路径 `/workspace`，不是 Windows 原始路径。普通用户优先使用“选择本机文件夹导入”。

## 8. Docker 双击入口验收记录

2026-05-21 已补充 Docker 双击入口：

- 启动入口：`Start-KnowledgeIsland-Docker.bat`
- 停止入口：`Stop-KnowledgeIsland-Docker.bat`
- 快速开始：`README-Docker-Quickstart.txt`
- 停止脚本：`scripts/docker_down.ps1`

限制：双击入口不是安装器；仍需要用户先安装并启动 Docker Desktop。
