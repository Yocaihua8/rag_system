# 项目知识库助手

基于六边形架构（Hexagonal Architecture）的本地项目知识库桌面应用。
第一版目标是导入代码项目，建立可问答的项目知识库，并通过掌握评估帮助用户理解自己与项目要求之间的差距。

---

## 功能概览

| 功能 | 说明 |
|------|------|
| **项目管理** | 创建多个项目工作区，每个工作区指向一个代码项目目录 |
| **项目导入** | 扫描 README、docs、源码、配置文件和测试文件；依赖目录过滤为后续优化项 |
| **项目问答** | 基于向量检索或关键词检索回答项目问题，并展示来源片段 |
| **掌握评估** | 第一版目标中：围绕项目知识点生成评估题，记录掌握情况和能力差距 |
| **知识库管理** | 查看项目状态和文件处理情况；项目知识点与评估题库为第一版目标 |
| **输出工具** | 简历、JD 匹配、面试脚本作为后续输出能力保留 |

---

## 安装

### 前置要求

- Python 3.10+
- [Ollama](https://ollama.com)（本地推理，可选）

### 1. 克隆并创建虚拟环境

```bash
git clone <repo-url>
cd rag_system
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

> **最小依赖**（关键词检索 + Ollama 模式）：PySide6、chromadb、sentence-transformers
> **云端 API 模式**还需要：`pip install openai`

### 3. 配置（可选）

复制 `.env.example` 为 `.env`，按需修改：

```bash
cp .env.example .env
```

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RAG_KB_ROOT` | `~/CareerAssistantKB` | 知识库根目录 |
| `RAG_OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务地址 |
| `RAG_OLLAMA_MODEL` | `qwen2.5:7b` | 生成模型 |
| `RAG_EMBEDDING_MODEL` | `nomic-embed-text` | 嵌入模型 |
| `RAG_RETRIEVER_KIND` | `vector` | `vector`（ChromaDB）或 `keyword` |
| `RAG_LLM_PROVIDER` | `ollama` | `ollama` 或 `api` |
| `RAG_LLM_API_KEY` | _(空)_ | 云端 API Key（见安全说明） |
| `RAG_LLM_API_BASE` | `https://api.deepseek.com/v1` | API 地址 |
| `RAG_LLM_API_MODEL` | `deepseek-chat` | 云端模型名 |

---

## 启动

```bash
# Windows
.venv\Scripts\python.exe app.py

# macOS / Linux
.venv/bin/python app.py
```

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

在 **设置 → LLM 提供商** 中选择「API 模式」，填入：

| 字段 | DeepSeek | OpenAI | 通义千问 | Kimi |
|------|----------|--------|----------|------|
| API 地址 | `https://api.deepseek.com/v1` | `https://api.openai.com/v1` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `https://api.moonshot.cn/v1` |
| 模型 | `deepseek-chat` | `gpt-4o-mini` | `qwen-plus` | `moonshot-v1-8k` |

### API Key 安全说明

配置 API Key 有三种方式（优先级从高到低）：

1. **OS 环境变量**（推荐）：`RAG_LLM_API_KEY=sk-xxx`
   Key 不写入任何文件，UI 中自动显示「已从环境变量读取」并禁用输入框
2. **`.env` 文件**：写入项目根目录的 `.env`（已在 `.gitignore` 中排除）
3. **设置界面**：直接在 UI 中填写（存储在 appdata 目录）

---

## 项目结构

```
rag_system/
├── app.py                    # 程序入口
├── src/
│   ├── config/               # 配置层（defaults / settings / paths）
│   ├── domain/               # 领域层：不可变数据模型 + 业务错误
│   │   ├── models/           #   Workspace / Document / Chunk / Task / ConversationRecord
│   │   └── errors.py         #   NotFoundError / ValidationError / ...
│   ├── ports/                # 端口层：接口定义（IWorkspaceStore / ILLMClient / ...）
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
│   └── desktop/              # 桌面层：PySide6 UI
│       ├── bootstrap.py      #   程序启动入口
│       ├── style.py          #   全局 QSS 主题（Codex 暗色风格）
│       ├── views/            #   MainWindow / 各功能视图 / 使用指引
│       ├── controllers/      #   Controller（UI → UseCase 桥接）
│       └── workers/          #   QThread Worker（I/O 异步化）
├── tests/
│   ├── conftest.py           # 共用 Fixtures（内存 SQLite + FakeLLM）
│   ├── test_domain/          # 领域模型测试
│   ├── test_adapters/        # SQLite Store 测试
│   └── test_application/     # 用例测试（工作区 / 摄入 / 查询）
├── docs/
│   ├── BACKLOG.md            # 待办事项
│   ├── DEVLOG.md             # 开发日志
│   └── architecture/         # 架构设计文档
├── data/                     # 示例数据 / 输出目录
├── runtime/                  # 运行时产物（db / vector store / logs）
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
.venv/Scripts/python.exe -m pytest tests/ -v
# 72 passed，零网络依赖，<1s
```

---

## 开发文档

| 文档 | 内容 |
|------|------|
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | 整体架构说明 |
| `docs/architecture/LLM_PROVIDER_DESIGN.md` | LLM 提供商路由 + API Key 安全设计 |
| `docs/architecture/RAG_PIPELINE.md` | RAG 检索增强生成流程 |
| `docs/DEVLOG.md` | 逐步开发日志 |
| `docs/BACKLOG.md` | 待办事项与优先级 |
