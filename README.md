# 知识岛 Knowledge Island

知识岛是一个本地优先的个人 AI 第二大脑应用。它不是阶段性学习分析系统的知识库模块，也不是普通 RAG Demo；当前默认入口已切换为本地 Web MVP（Python 标准库 HTTP 服务 + SQLite + 原生 HTML/CSS/JS），先保证本地项目、文档、笔记和代码资料能快速导入、检索、问答并展示来源。

旧 PySide6 桌面端代码暂时保留在 `src/desktop/` 作为 legacy 参考，不再是默认启动入口。

---

## 功能概览

| 功能 | 说明 |
|------|------|
| **项目空间** | 在 Web 页面中创建本地项目空间，绑定一个本地目录 |
| **当前目录显示** | 项目工具栏下方显示当前项目空间绑定的本地目录；目录被移动或删除时提示“目录不存在”，并阻止继续导入 |
| **最近项目恢复** | 浏览器会记住最近选中的项目空间，刷新页面后自动恢复 |
| **项目空间改名** | 可在 Web 页面中修改当前项目空间名称，不影响绑定目录和已导入文档 |
| **项目空间删除** | 可删除误创建的项目空间，删除前会二次确认，并同步删除其文档记录 |
| **文档导入** | Web MVP 支持 Markdown、TXT、代码与配置文本导入，默认跳过 `.git`、`.venv`、`node_modules`、`.claude`、`.codex`、`.agents`、`.vscode`、`.idea`、`__pycache__` 等目录，并跳过超过 1MB 的单个文本文件 |
| **浏览器文件夹导入** | Docker 模式下可点击“选择文件夹导入”，浏览器读取用户授权的本地项目文件夹并上传文本内容入库，不需要在页面填写 Windows 路径 |
| **导入结果可视化** | 导入后在侧栏展示当前项目空间已入库文件列表，并显示新增、更新、未变更、删除、跳过数量 |
| **跳过详情** | 导入后展示被跳过文件的路径和原因，例如文件超过 1MB |
| **导入错误** | 导入后单独展示读取失败等错误信息，避免和普通跳过文件混在一起 |
| **文件预览** | 点击已导入文件后，在侧栏查看该文件正文预览 |
| **文档记录移除** | 可从当前项目空间移除单个已导入文档记录，不删除磁盘源文件 |
| **文件路径过滤** | 已导入文件列表支持按路径本地过滤，便于在大量文件中快速定位 |
| **文件数量提示** | 已导入文件列表显示当前过滤结果数和总文件数 |
| **独立检索** | 不提问也可直接搜索文件片段，并点击结果打开文件预览 |
| **关键词检索** | 基于 SQLite 中的文本内容做本地关键词排序，不依赖 Ollama 或云端 API |
| **空状态提示** | 无文件、无检索结果、无来源、无跳过文件时显示明确提示 |
| **知识库问答** | 默认基于检索片段组合回答；配置 DeepSeek / OpenAI 兼容 API 后优先使用真实 LLM，并保留来源文件与片段 |
| **掌握评估** | Web 端可从已导入文件生成最小评估题，提交回答后给出规则化反馈和建议阅读来源 |
| **首次使用引导** | Web 首页展示创建项目空间、导入目录、提问/评估、配置 DeepSeek 的最小步骤 |
| **格式标准化** | legacy PySide6 链路已支持 `raw_content / normalized_markdown / plain_text / rendered_html`，Web MVP 后续迁移 |
| **知识掌握地图** | 已新增 SkillArea / KnowledgePoint / MasteryRecord / Evidence 的数据模型与状态定义 |
| **轻量知识图谱** | 计划用 SQLite 关系表表达 Project、Document、KnowledgePoint、Evidence 等节点关系 |

---

## 安装

### 前置要求

- Python 3.10+
- [Ollama](https://ollama.com)（本地推理，可选）

### 1. 克隆并创建虚拟环境

```bash
git clone <repo-url>
cd knowledage_island
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

> **Web MVP 最小依赖**：仅 Python 标准库，不需要新增运行时依赖。
> **legacy PySide6** 仍需要 PySide6、chromadb、sentence-transformers、openai 等依赖。Web 端 DeepSeek 调用使用 Python 标准库 `urllib`，不依赖 `openai` SDK。

### 3. 配置（可选）

复制 `.env.example` 为 `.env`，按需修改：

```bash
cp .env.example .env
```

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RAG_KB_ROOT` | `~/KnowledgeIslandKB` | 知识库根目录 |
| `RAG_OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务地址 |
| `RAG_OLLAMA_MODEL` | `qwen2.5:7b` | 生成模型 |
| `RAG_EMBEDDING_MODEL` | `nomic-embed-text` | 嵌入模型 |
| `RAG_RETRIEVER_KIND` | `vector` | `vector`（ChromaDB）或 `keyword` |
| `RAG_LLM_PROVIDER` | `ollama` | `ollama` 或 `api` |
| `RAG_LLM_API_KEY` | _(空)_ | 云端 API Key（见安全说明）；兼容本机 DeepSeek Key 别名 |
| `RAG_LLM_API_BASE` | `https://api.deepseek.com/v1` | API 地址 |
| `RAG_LLM_API_MODEL` | `deepseek-chat` | 云端模型名 |

Web 端问答会优先读取这些变量。未配置 API Key 时，自动回退到本地片段组合回答。

---

## 启动

```bash
# Windows
.venv\Scripts\python.exe app.py

# macOS / Linux
.venv/bin/python app.py
```

启动后打开：

```text
http://127.0.0.1:8765
```

## Docker 一键启动

非技术用户可先阅读根目录：

```text
README-Docker-Quickstart.txt
```

然后双击启动：

```text
Start-KnowledgeIsland-Docker.bat
```

停止服务：

```text
Stop-KnowledgeIsland-Docker.bat
```

Windows PowerShell：

```powershell
.\scripts\docker_up.ps1
```

脚本会执行 `docker compose up --build -d`，启动后打开：

```text
http://127.0.0.1:8765
```

Docker 模式下，Web 页面创建项目空间时，本地目录请填写容器内路径：

```text
/workspace
```

宿主机对应目录默认为仓库根目录下的 `docker-workspace/`。把要导入的 Markdown、TXT、代码和配置文件放到该目录后，在 Web 页面点击“导入”。

如果要直接导入 `E:\Code\your-project` 这类 Windows 本地目录，推荐点击 Web 侧栏的“选择文件夹导入”。浏览器会请求选择一个本地项目文件夹，并把允许的文本文件内容上传给本地服务入库；这种方式不需要在页面填写 Windows 路径。

如果 Windows User 环境变量里存在 `DEEPSEEK_API_KEY`，一键脚本会注入给 Docker Compose，但不会打印 Key。运行数据持久化到 `runtime/docker/`。

---

## Ollama 配置

本地模式需要先安装并启动 Ollama，拉取所需模型：

```bash
# 启动 Ollama 服务
ollama serve

# 拉取生成模型（二选一）
ollama pull qwen2.5:7b
ollama pull llama3.2:3b

# 拉取嵌入模型（向量检索时必须）
ollama pull nomic-embed-text
```

启动应用后，在 **设置 → Ollama 本地配置** 中确认地址与模型名一致。

---

## 云端 API 配置

Web 端可通过系统环境变量直接启用 DeepSeek / OpenAI 兼容 API；legacy 桌面端也可在 **设置 → LLM 提供商** 中选择「API 模式」。

| 字段 | DeepSeek | OpenAI | 通义千问 | Kimi |
|------|----------|--------|----------|------|
| API 地址 | `https://api.deepseek.com/v1` | `https://api.openai.com/v1` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `https://api.moonshot.cn/v1` |
| 模型 | `deepseek-chat` | `gpt-4o-mini` | `qwen-plus` | `moonshot-v1-8k` |

### API Key 安全说明

配置 API Key 有三种方式（优先级从高到低）：

1. **OS 环境变量**（推荐）：`RAG_LLM_API_KEY=sk-xxx`
   Key 不写入任何文件，UI 中自动显示「已从环境变量读取」并禁用输入框
   现阶段也兼容已有的本机 DeepSeek Key 变量：`DEEPSEEK_API_KEY` / `DEEPSEEK_APIKEY` / `deepseekapikey`。检测到这些变量时，默认切到 `api` provider，并使用 DeepSeek 默认地址与模型；如需强制不用云端，可显式设置 `RAG_LLM_PROVIDER=ollama`。
   Windows 上会额外读取 User/Machine 级持久环境变量；即使当前终端或 Codex 进程未继承新变量，应用也能识别已保存的 `DEEPSEEK_API_KEY`。
2. **`.env` 文件**：写入项目根目录的 `.env`（已在 `.gitignore` 中排除）
3. **设置界面**：直接在 UI 中填写（存储在 appdata 目录）

Windows PowerShell 示例：

```powershell
[System.Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-xxx", "User")
[System.Environment]::SetEnvironmentVariable("RAG_LLM_PROVIDER", "api", "User")
```

---

## 项目结构

```
knowledage_island/
├── app.py                    # 默认 Web MVP 程序入口
├── Dockerfile                # Web MVP 容器镜像
├── compose.yaml              # Docker Compose 一键启动
├── webapp/                   # 默认 Web MVP 技术栈
│   ├── server.py             # HTTP server + 静态文件服务
│   ├── api.py                # API 路由分发
│   ├── storage.py            # SQLite schema 与读写
│   ├── ingestion.py          # 本地目录文本导入
│   ├── import_rules.py       # 导入后缀、排除目录、文件大小上限
│   ├── search.py             # 关键词检索与排序
│   ├── answers.py            # LLM 优先回答与本地片段回退
│   ├── llm.py                # OpenAI-compatible Chat Completions 标准库客户端
│   ├── assessment.py         # Web 掌握评估最小闭环
│   └── static/               # 原生 HTML/CSS/JS 前端
├── src/
│   ├── config/               # 配置层（defaults / settings / paths）
│   ├── domain/               # 领域层：不可变数据模型 + 业务错误
│   │   ├── models/           #   Project / Document / Chunk / Tag / Source / Workspace / Task / Mastery
│   │   └── errors.py         #   NotFoundError / ValidationError / ...
│   ├── ports/                # 端口层：接口定义（IWorkspaceStore 兼容层 / ILLMClient / ...）
│   ├── adapters/             # 适配器层：具体实现
│   │   ├── storage/          #   SQLite（5 个 Store）
│   │   ├── llm/              #   OllamaAdapter / OpenAICompatAdapter
│   │   ├── embedding/        #   OllamaEmbedder / DummyEmbedder
│   │   ├── retrieval/        #   VectorRetriever / KeywordRetriever
│   │   └── vector_store/     #   ChromaVectorStore / NumpyVectorStore
│   ├── application/          # 应用层：用例 + 依赖组装
│   │   ├── container.py      #   AppContainer（唯一 Composition Root）
│   │   ├── workspace_usecases.py
│   │   ├── ingestion_usecases.py
│   │   ├── query_usecases.py
│   │   ├── generation_usecases.py
│   │   └── settings_usecases.py
│   └── desktop/              # legacy 桌面层：PySide6 UI
│       ├── bootstrap.py      #   程序启动入口
│       ├── style.py          #   全局 QSS 主题（Codex 暗色风格）
│       ├── views/            #   MainWindow / 各功能视图 / 使用指引
│       ├── controllers/      #   Controller（UI → UseCase 桥接）
│       └── workers/          #   QThread Worker（I/O 异步化）
├── tests/
│   ├── conftest.py           # 共用 Fixtures（内存 SQLite + FakeLLM）
│   ├── test_domain/          # 领域模型测试
│   ├── test_adapters/        # SQLite Store 测试
│   ├── test_application/     # 用例测试（项目空间兼容层 / 摄入 / 查询）
│   └── test_webapp/          # Web MVP API、导入、检索与前端静态约束测试
├── docs/
│   ├── BACKLOG.md
│   ├── DEVLOG.md
│   ├── design/api-spec.md
│   ├── devlog/2026-05-20.md
│   ├── guides/setup.md
│   ├── guides/testing.md
│   ├── release/WEB_MVP_READINESS_2026-05-20.md
│   └── architecture/              # 历史架构文档（兼容保留）
├── data/                     # 示例数据 / 输出目录
├── runtime/                  # 运行时产物（db / vector store / logs）
├── docker-workspace/         # Docker 模式默认导入目录（本地忽略）
└── .env.example              # 环境变量示例
```

### 架构原则

- **六边形架构**：`domain` → `ports` → `adapters`，依赖方向单向向内
- **唯一组装点**：只有 `AppContainer` 可以 import adapter 类
- **不可变模型**：所有领域对象使用 `@dataclass(frozen=True)`，跨线程安全
- **Qt 线程隔离**：所有 I/O 在 `QThread` Worker 中执行，通过 Signal 返回结果

---

## 运行测试

```bash
.venv/Scripts/python.exe -m pytest tests/test_webapp -q
# 当前测试基线以实际运行结果为准
```

---

## 开发文档

| 文档 | 内容 |
|------|------|
| `docs/design/api-spec.md` | 本地 Web MVP HTTP API 与 legacy 进程内接口契约 |
| `docs/guides/setup.md` | 环境启动指引 |
| `docs/guides/testing.md` | 测试与验证方式 |
| `docs/release/WEB_MVP_READINESS_2026-05-20.md` | 本地 Web MVP 收口与浏览器验收清单 |
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | 整体架构说明 |
| `docs/architecture/LLM_PROVIDER_DESIGN.md` | LLM 提供商路由 + API Key 安全设计 |
| `docs/architecture/RAG_PIPELINE.md` | RAG 检索增强生成流程 |
| `docs/DEVLOG.md` | 逐步开发日志 |
| `docs/BACKLOG.md` | 待办事项与优先级 |
