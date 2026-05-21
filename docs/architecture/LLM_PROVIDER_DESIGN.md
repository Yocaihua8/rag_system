# LLM Provider 设计文档

> **状态**：设计确定，实现中（B-11）
> **创建**：2026-04-16
> **最后更新**：2026-04-16（补充环境变量安全策略）

---

## 问题背景

原版本 LLM 层只支持本地 Ollama，用户必须在本机运行 Ollama 服务才能使用问答和生成功能。许多用户希望直接使用云端 API（DeepSeek、OpenAI 等），无需本地运行大模型。部分安全敏感用户不希望 API Key 写入任何文件，需要支持纯环境变量注入。

---

## 设计目标

1. 支持多个 LLM 提供商，用户在设置页切换，**重启后生效**
2. 不破坏现有 Ollama 流程
3. Embedding 与 LLM 提供商解耦——云端 LLM + 本地 Ollama Embedding 是合理的混合模式
4. **API Key 零文件风险**：优先从 OS 环境变量读取，用户可完全不经由 UI 配置

---

## API Key 安全策略

### 读取优先级（与现有 load_settings() 保持一致）

```
OS 环境变量  >  appdata/.env  >  项目根 .env  >  defaults.py
```

用户有三种配置方式，安全级别递增：

| 方式 | 操作 | API Key 存储位置 | 风险 |
|------|------|----------------|------|
| 通过设置页填写 | UI 输入，点保存 | `~/.config/KnowledgeIsland/.env` | 明文文件，仅本机可读 |
| 写入项目 .env | 手动编辑 `.env` | 项目目录，需注意 .gitignore | 若提交 Git 有泄露风险 |
| **OS 环境变量** | 系统/终端设置 | 内存，不写磁盘 | **最安全，推荐** |

### OS 环境变量设置方法

**Windows（永久，当前用户）：**
```powershell
[System.Environment]::SetEnvironmentVariable("RAG_LLM_API_KEY", "sk-xxx", "User")
[System.Environment]::SetEnvironmentVariable("RAG_LLM_PROVIDER", "api", "User")
```

现阶段兼容已有的本机 DeepSeek Key 变量名，无需把 Key 写入项目文件：

```powershell
[System.Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-xxx", "User")
# 兼容别名：DEEPSEEK_APIKEY / deepseekapikey
```

当检测到 `DEEPSEEK_API_KEY` / `DEEPSEEK_APIKEY` / `deepseekapikey`，且没有显式设置 `RAG_LLM_PROVIDER` 时，`load_settings()` 默认使用 `api` provider、DeepSeek 默认地址和 `deepseek-chat` 模型。

Windows 场景下，`load_settings()` 不只读取当前进程 `os.environ`，还会读取 User/Machine 级持久环境变量。这样用户通过系统设置写入 `DEEPSEEK_API_KEY` 后，即使已经打开的 Codex/终端进程没有继承新变量，Web 端仍能识别该 Key。当前进程环境变量仍拥有更高优先级。

**macOS / Linux：**
```bash
export RAG_LLM_API_KEY=sk-xxx
export RAG_LLM_PROVIDER=api
# 写入 ~/.zshrc 或 ~/.bashrc 使其持久化
```

### 设置页 UI 的安全感知行为

- **检测到环境变量**：API Key 字段显示 `● 已从系统环境变量读取（安全）`，字段禁用，无法通过 UI 修改（防止意外覆盖）
- **未检测到环境变量**：显示可编辑的密文输入框，保存时写入 `appdata/.env`
- 任何情况下均**不在 UI 上回显 API Key 明文**

---

## 架构决策

### LLM 提供商 vs Embedding 提供商独立配置

```
llm_provider   = "ollama" | "api"     # 控制问答/生成用哪个后端
embed_provider = "ollama" | "none"    # 控制向量索引用哪个 Embedder
```

两者独立，允许：
- 全 Ollama（原有模式）
- 云端 LLM + 本地 Ollama Embedding（推荐混合模式）
- 纯关键词检索 + 云端 LLM（Ollama 完全离线时的降级）

当 `embed_provider=none` 时，`AppContainer.build()` 自动降级为 `KeywordRetriever`。

### 新增配置字段

| 字段 | 环境变量 | 默认值 | 说明 |
|------|---------|--------|------|
| `llm_provider` | `RAG_LLM_PROVIDER` | `"ollama"` | `"ollama"` 或 `"api"` |
| `llm_api_key` | `RAG_LLM_API_KEY` | `""` | API Key；优先读 OS 环境变量，兼容 DeepSeek Key 别名 |
| `llm_api_base` | `RAG_LLM_API_BASE` | `"https://api.deepseek.com/v1"` | OpenAI 兼容接口地址 |
| `llm_api_model` | `RAG_LLM_API_MODEL` | `"deepseek-chat"` | 云端模型名 |
| `embed_provider` | `RAG_EMBED_PROVIDER` | `"ollama"` | `"ollama"` 或 `"none"` |

**`llm_api_key` 的特殊处理**：`load_settings()` 已按优先级合并所有来源。通用变量 `RAG_LLM_API_KEY` 仍是正式配置；为适配现阶段本机环境，也兼容 `DEEPSEEK_API_KEY` / `DEEPSEEK_APIKEY` / `deepseekapikey`。Windows 下还会补读 User/Machine 持久环境。来源感知仅在 UI 层需要（用于决定是否禁用输入框），通过 `get_api_key_env_name()` 判断。

### 新增适配器

```
src/adapters/llm/openai_compat_adapter.py
  └── OpenAICompatAdapter(ILLMClient)
        - generate()：POST /chat/completions（非流式）
        - stream()：POST /chat/completions（stream=True，SSE 解析）
        - is_available()：检查 api_key 非空且能 ping 通接口
        - list_models()：返回配置的模型名
```

**依赖**：使用 `openai` Python SDK，通过 `base_url` 参数切换接口地址（DeepSeek / 通义 / Moonshot / Kimi 均兼容）。

### AppContainer.build() 路由逻辑

```python
# LLM 路由
if settings.llm_provider == "api" and settings.llm_api_key:
    llm_client = OpenAICompatAdapter(
        api_key=settings.llm_api_key,
        base_url=settings.llm_api_base,
        model=settings.llm_api_model,
    )
else:
    llm_client = OllamaAdapter(host=settings.ollama_host)

# Embedding 路由（独立）
if settings.embed_provider == "ollama":
    embedder = OllamaEmbedder(...)
    vector_store = ChromaVectorStore(...)
    retriever = VectorRetriever(...)
else:
    embedder = DummyEmbedder(...)
    vector_store = NumpyVectorStore()
    retriever = KeywordRetriever()
```

### 设置页 UI

```
── LLM 提供商 ────────────────────────────────────
  ○ 本地 Ollama    ● 云端 API（OpenAI 兼容）

  （切换到"云端 API"后展开以下字段）

  API 地址：  [ https://api.deepseek.com/v1        ]
              常用：DeepSeek / OpenAI / 通义千问 / Kimi

  API Key：   [●●●●●●●●●●●●●●●●  ]  [显示]
              或显示：● 已从系统环境变量读取（安全）

  模型名称：  [ deepseek-chat                      ]

── Embedding 提供商 ──────────────────────────────
  ○ 本地 Ollama（向量检索）   ● 关键词检索（无需 Ollama）
```

---

## 不在此版本实现的

- 多 API Key 管理（轮询/负载均衡）
- 云端 Embedding（OpenAI text-embedding-ada-002 等）
- 运行时热切换（无需重启）
- API 用量统计 / 费用估算

---

## 影响范围

| 文件 | 变更类型 |
|------|---------|
| `src/config/defaults.py` | 新增 5 个默认值 |
| `src/config/settings.py` | `AppSettings` 新增 5 个字段 |
| `src/adapters/llm/openai_compat_adapter.py` | 新建 |
| `src/application/container.py` | LLM + Embed 路由逻辑 |
| `src/application/settings_usecases.py` | 新增 5 个 save 方法 |
| `src/desktop/views/settings_view.py` | 重写，新增 LLM 提供商分组 + 环境变量感知 |
