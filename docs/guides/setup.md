# 开发环境与启动

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-24

## 1. 环境要求

- Python 3.10+（仓库默认以 3.11 为主）
- Web MVP 默认不需要 Ollama 或 API Key；配置 DeepSeek Key 后可启用真实 LLM 回答
- 可选：Ollama 本地服务（legacy PySide6 / 后续 RAG 能力）
- 可选：API Key（DeepSeek/OpenAI/兼容端点）
- 可选：`pymupdf`（Web MVP PDF 正文抽取；未安装时 PDF 会明确跳过）

## 2. 最小启动步骤

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
cp .env .env.local # 按需
```

启动默认 Web MVP：

```bash
.venv\Scripts\python.exe app.py
```

浏览器打开：

```text
http://127.0.0.1:8765
```

当前默认入口使用 Python 标准库 HTTP 服务、SQLite 和原生前端，不新增必需运行时依赖。Web 端 DeepSeek / OpenAI 兼容调用同样使用 Python 标准库，不依赖 `openai` SDK。PDF 正文抽取是可选能力，需要额外执行 `pip install pymupdf`；未安装时 PDF 会返回 `pdf extraction requires optional parser` 并继续处理其他文件。旧 PySide6 桌面端代码仍保留在 `src/desktop/`，后续按功能迁移。

## 3. Docker 一键启动

非技术用户优先使用根目录双击入口：

```text
Start-KnowledgeIsland-Docker.bat
Stop-KnowledgeIsland-Docker.bat
README-Docker-Quickstart.txt
```

双击启动后访问：

```text
http://127.0.0.1:8765
```

Windows PowerShell：

```powershell
.\scripts\docker_up.ps1
```

脚本会：

- 创建 `docker-workspace/` 作为 Docker 模式默认导入目录。
- 创建 `runtime/docker/` 作为容器运行时持久化目录。
- 从 Windows User 环境读取 `DEEPSEEK_API_KEY` 并注入给 Compose（不打印 Key）。
- 从 Windows User 环境读取 `RAG_EMBED_API_KEY` 并注入给 Compose（不打印 Key）。
- 执行 `docker compose up --build -d`。
- 打开 `http://127.0.0.1:8765`。

Docker 模式下推荐优先使用 Web 侧栏的“选择本机文件夹导入”。浏览器会读取用户选择的本地项目文件夹，并把允许的文本文件、DOCX 和 PDF 二进制内容上传给本地服务入库；这种方式可以直接选择 `E:\Code\your-project`，不需要填写 Windows 路径。PDF 正文抽取需要镜像或运行环境安装可选 `pymupdf`，未安装时会在导入结果中显示跳过原因。

如果继续使用挂载目录导入，Web 页面创建项目空间时目录填写：

```text
/workspace
```

该路径对应宿主机的 `docker-workspace/`。如果要导入其他宿主机目录，可设置：

```powershell
$env:KNOWLEDGE_ISLAND_WORKSPACE="E:\Code\your-project"
.\scripts\docker_up.ps1
```

也可以直接使用 Compose：

```powershell
docker compose up --build -d
docker compose logs -f web
docker compose down
```

启用 DeepSeek 真实回答（可选）：

推荐方式是在 Web 页面打开 **设置 → 模型设置**，填写 API 地址、模型名和 API Key，然后点击“测试连接”。页面不会回显 API Key 明文。

同一个设置页也提供 **Prompt 预设**。可为当前项目空间保存“项目问答 / 代码解释 / 学习复盘”等本地预设，并选择一个默认预设影响真实 LLM 的回答风格和结构；该功能不需要新增依赖，不保存 API Key，也不会改变检索参数。

也可以使用 Windows User 环境变量：

```powershell
[System.Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-xxx", "User")
[System.Environment]::SetEnvironmentVariable("RAG_LLM_PROVIDER", "api", "User")
```

重启终端后再运行 `app.py`。未配置 API Key 时，Web 端自动使用本地片段回答。

Windows 上应用会读取 User/Machine 级持久环境变量；如果当前终端没有继承新设置的 `DEEPSEEK_API_KEY`，`load_settings()` 仍会尝试从 Windows 持久环境中读取。

启用真实 Embedding（可选）：

```powershell
[System.Environment]::SetEnvironmentVariable("RAG_EMBED_PROVIDER", "api", "User")
[System.Environment]::SetEnvironmentVariable("RAG_EMBED_API_BASE", "https://api.openai.com/v1", "User")
[System.Environment]::SetEnvironmentVariable("RAG_EMBED_API_MODEL", "text-embedding-3-small", "User")
[System.Environment]::SetEnvironmentVariable("RAG_EMBED_API_KEY", "sk-xxx", "User")
```

Embedding 服务必须支持 OpenAI-compatible `/embeddings`。未配置或请求失败时，Web MVP 会回退到本地 hashing 向量，导入不中断。

## 4. 常见校验

- 检查 `http://127.0.0.1:8765/api/health` 是否返回 `{"status": "ok"}`。
- 创建项目空间时，本地目录必须对当前后端进程真实存在；Docker 模式下 Windows 路径不会直接存在于容器内，推荐改用“选择本机文件夹导入”。
- Web MVP 无 Ollama、无 API Key 时仍可导入文本与 DOCX 正文并进行关键词问答。
- Web MVP 配置 DeepSeek Key 后，`/api/answer` 会优先请求 OpenAI-compatible Chat Completions；请求失败时回退到本地片段回答。
- Web MVP 每次提问后会在 SQLite 中保存当前项目的聊天记录；刷新页面或切换项目后，工作台会通过 `/api/chat/messages` 重新加载最近对话。真实 LLM 回答会带入同项目最近 3 轮历史作为上下文。
- Web MVP 工作台的 Agent 工具当前只开放只读 `project_overview` 和 `search_sources`，会写入 `agent_tool_runs` 审计记录；不开放 shell、任意命令执行或任意文件写入。
- Web MVP 工作台会通过 `/api/agent/tools/runs` 展示当前项目工具运行历史，用于查看工具名、状态、查询参数和错误原因。
- Web MVP 问答没有可用来源时，回答区显示建议工具 `search_sources` 和查询词，并提供按钮让用户手动运行；不会自动执行工具。
- Web MVP 用户运行 `search_sources` 后，下一轮问答会显式携带该 `tool_run_id`，把工具命中的来源片段合并进回答上下文；跨项目或非成功工具记录会被拒绝。
- Web MVP 工作台提供检索调试区域，可用当前查询词临时调整 `top_k`、最低分、关键词/向量开关，并查看命中 chunk、分数、来源质量和上下文预览；这些参数不持久化。
- Web MVP 工作台可将一次检索诊断保存为检索复盘记录，记录查询词、参数、命中来源、来源质量和人工备注，便于后续补资料或调参。
- Web MVP 配置 `RAG_EMBED_PROVIDER=api` 和 `RAG_EMBED_API_KEY` 后，导入 chunk 时会优先请求 OpenAI-compatible Embeddings；请求失败时回退本地向量。
- Web MVP 资料库页可直接导入文本笔记；笔记会作为当前项目空间的 `note:` 虚拟来源参与检索和问答，不依赖磁盘文件是否存在。
- 模型设置页可通过 `GET/POST /api/settings/llm` 读取或保存 API Base、模型名和 API Key 状态，并通过 `/api/settings/llm/test` 做连接测试。
