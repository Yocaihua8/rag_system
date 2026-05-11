# RAG 全流程设计

> **版本**：v2.0
> **日期**：2026-04
> **状态**：Active

---

## 1. 完整流水线总览

标准 RAG 分为两个阶段：**离线索引（Indexing）** 和 **在线查询（Querying）**。

```
════════════════════════ 离线阶段（Indexing） ════════════════════════

  原始文件（.md / .pdf / .docx / .txt …）
        │
        ▼  步骤 ①  文档加载（Document Loading）
  原始文本 + 文件元数据
        │
        ▼  步骤 ②  文本清洗 / 预处理（Preprocessing）
  清洗后文本 + 推断标签 + 领域
        │
        ▼  步骤 ③  分块（Chunking）
  Chunk 列表（含 chunk_id / document_id / domain / tags / content）
        │
        ▼  步骤 ④  文本嵌入（Embedding）        ← ★ 之前缺失
  每个 Chunk 的稠密向量（768 维）
        │
        ▼  步骤 ⑤  向量存储（Vector Store）     ← ★ 之前缺失
  向量写入 ChromaDB（按 workspace_id 分区）
  Chunk 元数据写入 SQLite

════════════════════════ 在线阶段（Querying） ════════════════════════

  用户输入问题
        │
        ▼  步骤 ⑥  查询嵌入（Query Embedding）  ← ★ 之前缺失
  问题向量（768 维）
        │
        ▼  步骤 ⑦  语义检索（Semantic Retrieval）← ★ 之前缺失
  按余弦相似度取 Top-K Chunk
        │
        ▼  步骤 ⑧  上下文构建（Context Assembly）
  Prompt = System Prompt + 检索到的 Chunk 内容 + 用户问题
        │
        ▼  步骤 ⑨  LLM 生成（Generation）
  模型输出答案（流式返回）
        │
        ▼  步骤 ⑩  结果返回与溯源（Response + Citations）
  答案文本 + 来源 Chunk 列表
```

---

## 2. 各步骤详解

### 步骤 ① — 文档加载（Document Loading）

**负责类**：`IngestWorkspaceUseCase`（调用 `IngestionService.scan()`）

**支持格式**：

| 格式 | 说明 |
|------|------|
| `.md` | 主力格式，支持 YAML frontmatter 提取 |
| `.txt` | 纯文本 |
| `.pdf` | 提取文字层（非扫描件） |
| `.docx` | Word 文档 |
| `.json` / `.yaml` | 配置与数据文件 |
| `.py` / `.ts` / `.java` | 代码文件 |

**输出**：`Document(id, title, domain, source_path, content, tags, created_at)`

---

### 步骤 ② — 文本清洗 / 预处理（Preprocessing）

**负责模块**：`src/domain/services/tagger.py`

- `infer_domain(file_path, content) -> str`：根据目录名和内容关键词推断领域（resume / jd / notes / paper 等）
- `build_tags(file_path, content) -> List[str]`：提取技术标签（Python / FastAPI / Vue …）
- 不修改原始文本内容，仅丰富元数据

---

### 步骤 ③ — 分块（Chunking）

**负责模块**：`src/domain/services/chunker.py`

**策略**：滑动窗口按字符切分

```
chunk_size    = 512 字符（可配）
chunk_overlap = 64 字符（可配）
```

**输出**：`Chunk(chunk_id, document_id, workspace_id, domain, tags, content, order)`

**约束**：
- 每个 Chunk 保留父 Document 的 domain 和 tags
- Chunk 长度不得超过 Embedding 模型的 token 限制（nomic-embed-text = 8192 token）

---

### 步骤 ④ — 文本嵌入（Embedding）★ 新增

**负责接口**：`IEmbedder`
**默认实现**：`OllamaEmbedder`（调用 Ollama Embedding API）

**模型**：`nomic-embed-text`（本地运行，768 维，支持中英文）

```python
# 调用示例
embedder = OllamaEmbedder(host="http://localhost:11434",
                           model="nomic-embed-text")

result: EmbeddingResult = embedder.embed("带领 5 人团队完成项目交付")
# result.vector: List[float]，长度 768
```

**批量处理**：`embed_batch()` 一次调用嵌入多个 Chunk，减少 HTTP 往返。
**耗时估算**：nomic-embed-text 在 CPU 上约 20ms/chunk，1000 个 Chunk ≈ 20s（在 Worker 线程中执行，不阻塞 UI）。

---

### 步骤 ⑤ — 向量存储（Vector Store）★ 新增

**负责接口**：`IVectorStore`
**默认实现**：`ChromaVectorStore`

**ChromaDB 配置**：

```
持久化目录：runtime/vectors/
Collection 命名：workspace_{workspace_id}
距离函数：cosine（余弦相似度）
```

**存储内容**：

| 字段 | 说明 |
|------|------|
| `id` | chunk_id |
| `embedding` | 768 维向量 |
| `metadata.domain` | 用于过滤 |
| `metadata.tags` | 用于过滤 |
| `metadata.workspace_id` | 用于隔离 |

**备选**：`NumpyVectorStore`（内存 + pickle 持久化，无第三方依赖，适合小数据集 / 测试）

**索引生命周期**：

```
首次摄入 → clear(workspace_id) → upsert_batch(all_chunks)
重新索引 → clear(workspace_id) → upsert_batch(all_chunks)
删除工作区 → delete_by_workspace(workspace_id)
```

---

### 步骤 ⑥ — 查询嵌入（Query Embedding）★ 新增

同步使用步骤 ④ 的 `IEmbedder`，对用户输入的问题生成查询向量。

```python
query_vector = embedder.embed(question).vector
```

**注意**：查询 Embedding 和文档 Embedding 必须使用同一模型，否则向量空间不兼容。

---

### 步骤 ⑦ — 语义检索（Semantic Retrieval）★ 新增

**负责接口**：`IRetriever`
**默认实现**：`VectorRetriever`

```python
class VectorRetriever(IRetriever):
    def search(self, query: RetrievalQuery) -> RetrievalResult:
        # 1. 嵌入查询
        q_vector = self._embedder.embed(query.question).vector

        # 2. 向量相似度搜索
        raw = self._vector_store.search(
            query_vector=q_vector,
            top_k=query.top_k * 2,      # 多取一些供后续过滤
            workspace_id=query.workspace_id
        )

        # 3. 按 domain / tags 过滤（可选）
        filtered = self._apply_filters(raw, query.domains, query.tags)

        # 4. 取最终 Top-K，加载完整 Chunk 内容
        top = filtered[:query.top_k]
        chunks = [self._chunk_store.get(r.chunk_id) for r in top]
        scores = [r.score for r in top]

        return RetrievalResult(chunks=chunks, scores=scores)
```

**VectorRetriever vs KeywordRetriever 对比**：

| 能力 | VectorRetriever | KeywordRetriever |
|------|----------------|-----------------|
| 语义理解 | ✅ 语义相似度 | ❌ 词频重叠 |
| 同义词 | ✅ 自然处理 | ❌ 需手写 SYNONYMS |
| 跨语言 | ✅ 中英文同向量空间 | ❌ 分开处理 |
| 离线可用 | ✅（Ollama 本地） | ✅ |
| 启动速度 | 需 Ollama 运行 | 无需模型 |
| 适用场景 | 默认，生产使用 | Ollama 不可用时降级 |

---

### 步骤 ⑧ — 上下文构建（Context Assembly）

**负责**：`QueryKnowledgeBaseUseCase._build_prompt()`

```python
SYSTEM_PROMPT = """你是一位专业的职业发展助手。
基于用户的知识库内容，准确、简洁地回答问题。
如果知识库中没有相关信息，请明确说明，不要编造内容。"""

def _build_prompt(self, question: str, chunks: List[Chunk]) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[来源 {i}] 领域：{chunk.domain} | 标签：{', '.join(chunk.tags)}\n"
            f"{chunk.content}"
        )
    context = "\n\n---\n\n".join(context_parts)
    return f"参考资料：\n\n{context}\n\n问题：{question}"
```

**Token 预算**：

```
System Prompt   ≈  100 tokens
Context（8块）  ≈  2000 tokens（每块约 250 tokens）
用户问题        ≈  50 tokens
─────────────────────────────
总输入          ≈  2150 tokens（远低于 qwen2.5:7b 的 32k 上下文）
```

---

### 步骤 ⑨ — LLM 生成（Generation）

**负责接口**：`ILLMClient`
**默认实现**：`OllamaAdapter`

**流式输出**：`QueryWorker` 使用 `llm_client.stream()` 逐 token 发信号给 UI，避免等待感。

```python
# src/desktop/workers/query_worker.py
class QueryWorker(BaseWorker):
    token_received = Signal(str)   # 每个 token 片段

    def _execute(self) -> QueryResponse:
        result = self._use_case.execute_streaming(
            request=self._request,
            on_token=lambda t: self.token_received.emit(t)
        )
        return result
```

---

### 步骤 ⑩ — 结果返回与溯源（Response + Citations）

**QueryResponse 结构**：

```python
@dataclass(frozen=True)
class QueryResponse:
    answer: str                 # LLM 生成的完整答案
    sources: List[Chunk]        # 检索到的原始 Chunk（用于引用展示）
    scores: List[float]         # 每个 Chunk 的相似度分数
    model_used: str             # 实际使用的模型名
    retrieval_ms: int           # 检索耗时（毫秒）
    generation_ms: int          # LLM 生成耗时（毫秒）
```

**UI 展示**：
- 答案区：Markdown 渲染
- 来源列表：显示每个 Chunk 的来源文件、领域、相似度分数
- 点击来源可展开查看原文

---

## 3. 生成类流水线（区别于问答）

问答（Query）侧重**开放式检索 + LLM 总结**。
生成（Generation）侧重**结构化输出**，步骤如下：

```
用户填写目标（关键词 / JD / 项目名）
        │
        ▼  步骤 ①  有针对性检索（指定 domain / tags）
  相关 Chunk（domain=resume 或 domain=jd）
        │
        ▼  步骤 ②  领域分析（domain/services/jd_analyzer.py）
  覆盖率报告 / Gap 分析 / 指标建议
        │
        ▼  步骤 ③  构建结构化 Prompt（模板 + 分析结果 + Chunk）
        │
        ▼  步骤 ④  LLM 生成结构化 Markdown
        │
        ▼  步骤 ⑤  返回 GenerationResult（markdown + 来源数）
```

---

## 4. 首次运行引导（OnboardingWizard）

首次启动时，向量库和 Embedding 模型均未就绪，需引导用户完成：

```
步骤 1  设置知识库根目录（kb_root）
         → 写入 appdata/.env

步骤 2  验证 Ollama 可用性（OllamaAdapter.is_available()）
         → 如不可用，显示安装指引

步骤 3  检查 Embedding 模型是否已拉取
         → 如未拉取，提示运行：ollama pull nomic-embed-text

步骤 4  首次索引（可选）
         → 触发 IngestWorkspaceUseCase，显示进度

完成 → 进入主界面
```

---

## 5. 降级策略

Ollama 或向量服务不可用时，系统应优雅降级而非崩溃：

| 场景 | 降级行为 |
|------|---------|
| Ollama 不可用 | 检索仍可进行，LLM 功能禁用，UI 展示警告 |
| Embedding 模型未拉取 | 新摄入禁用，已有向量仍可查询 |
| ChromaDB 损坏 | 自动切换 `KeywordRetriever`，提示用户重建索引 |
| 知识库目录不存在 | 提示选择目录，不崩溃 |

---

## 6. 性能参考（本地 CPU，单工作区 1000 个 Chunk）

| 操作 | 预计耗时 |
|------|---------|
| 扫描文件 | < 1s |
| 分块（1000 chunks） | < 1s |
| Embedding（1000 chunks，nomic-embed-text） | 15～30s |
| 写入 ChromaDB | < 2s |
| 查询 Embedding | < 100ms |
| 向量检索 Top-8 | < 50ms |
| LLM 生成（qwen2.5:7b，CPU） | 10～60s |
| **总问答延迟** | **10～60s**（主要是 LLM） |

所有耗时操作均在 QThread Worker 内执行，不阻塞 UI。

## 项目知识库与掌握评估扩展

项目知识库助手在标准 RAG 流程之上增加两条计划中的应用链路：

```text
项目导入 → 项目知识点提炼 → 项目问答
项目知识点 → 自动出题 → 用户回答 → 回答评估 → 能力差距报告
```

第一版评估链路必须保留来源：

- 每个项目知识点关联来源文件或来源片段。
- 每道评估题关联知识点和来源。
- 每次回答评估展示参考要点、判断原因和建议阅读文件。

这能避免评估结果变成不可追踪的 AI 结论。
