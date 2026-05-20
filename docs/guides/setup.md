# 开发环境与启动

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-20

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

启用 DeepSeek 真实回答（可选）：

```powershell
[System.Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-xxx", "User")
[System.Environment]::SetEnvironmentVariable("RAG_LLM_PROVIDER", "api", "User")
```

重启终端后再运行 `app.py`。未配置 API Key 时，Web 端自动使用本地片段回答。

## 3. 常见校验

- 检查 `http://127.0.0.1:8765/api/health` 是否返回 `{"status": "ok"}`。
- 创建项目空间时，本地目录必须真实存在。
- Web MVP 无 Ollama、无 API Key 时仍可导入文本并进行关键词问答。
- Web MVP 配置 DeepSeek Key 后，`/api/answer` 会优先请求 OpenAI-compatible Chat Completions；请求失败时回退到本地片段回答。
