# 开发环境与启动

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-20

## 1. 环境要求

- Python 3.10+（仓库默认以 3.11 为主）
- Web MVP 默认不需要 Ollama 或 API Key
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

当前默认入口使用 Python 标准库 HTTP 服务、SQLite 和原生前端，不新增运行时依赖。旧 PySide6 桌面端代码仍保留在 `src/desktop/`，后续按功能迁移。

## 3. 常见校验

- 检查 `http://127.0.0.1:8765/api/health` 是否返回 `{"status": "ok"}`。
- 创建项目空间时，本地目录必须真实存在。
- Web MVP 无 Ollama 时仍可导入文本并进行关键词问答。
