# 开发环境与启动

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-21

## 1. 环境要求

- Python 3.10+（仓库默认以 3.11 为主）
- Web MVP 默认不需要 Ollama 或 API Key；配置 DeepSeek Key 后可启用真实 LLM 回答
- 可选：Ollama 本地服务（legacy PySide6 / 后续 RAG 能力）
- 可选：API Key（DeepSeek/OpenAI/兼容端点）

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

当前默认入口使用 Python 标准库 HTTP 服务、SQLite 和原生前端，不新增运行时依赖。Web 端 DeepSeek / OpenAI 兼容调用同样使用 Python 标准库，不依赖 `openai` SDK。旧 PySide6 桌面端代码仍保留在 `src/desktop/`，后续按功能迁移。

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
- 执行 `docker compose up --build -d`。
- 打开 `http://127.0.0.1:8765`。

Docker 模式下推荐优先使用 Web 侧栏的“选择文件夹导入”。浏览器会读取用户选择的本地项目文件夹，并把允许的文本文件和 DOCX 内容上传给本地服务入库；这种方式可以直接选择 `E:\Code\your-project`，不需要填写 Windows 路径。PDF 暂不做无依赖正文解析，会在导入结果中显示跳过原因。

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

也可以使用 Windows User 环境变量：

```powershell
[System.Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-xxx", "User")
[System.Environment]::SetEnvironmentVariable("RAG_LLM_PROVIDER", "api", "User")
```

重启终端后再运行 `app.py`。未配置 API Key 时，Web 端自动使用本地片段回答。

Windows 上应用会读取 User/Machine 级持久环境变量；如果当前终端没有继承新设置的 `DEEPSEEK_API_KEY`，`load_settings()` 仍会尝试从 Windows 持久环境中读取。

## 4. 常见校验

- 检查 `http://127.0.0.1:8765/api/health` 是否返回 `{"status": "ok"}`。
- 创建项目空间时，本地目录必须对当前后端进程真实存在；Docker 模式下 Windows 路径不会直接存在于容器内，推荐改用“选择文件夹导入”。
- Web MVP 无 Ollama、无 API Key 时仍可导入文本与 DOCX 正文并进行关键词问答。
- Web MVP 配置 DeepSeek Key 后，`/api/answer` 会优先请求 OpenAI-compatible Chat Completions；请求失败时回退到本地片段回答。
- 模型设置页可通过 `GET/POST /api/settings/llm` 读取或保存 API Base、模型名和 API Key 状态，并通过 `/api/settings/llm/test` 做连接测试。
