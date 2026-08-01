# 检索与有来源问答

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：项目内搜索、流式问答、来源与可选检索增强
> Related：`project-space-ingestion.md`、`chat-branching.md`、`../design/api-spec.md`、`../design/database-design.md`

## 1. 用户目标

用户在当前项目内搜索资料或提出问题，系统返回来源片段、检索状态和回答；资料不足或外部模型不可用时，必须明确降级，不编造来源。

## 2. 当前可达流程

- 教练工作台通过 SSE 展示增量回答，并在完成事件中接收回答、消息、来源和观测信息。
- 非流式问答、搜索和检索诊断 API 同时保留；字段以 [`../design/api-spec.md`](../design/api-spec.md) 为准。
- 来源抽屉展示服务端返回的真实文件路径、片段与定位。
- 资料弹窗允许选择集合或文档用于浏览，但当前问答 payload 没有携带该选择；界面上的资料选择不能描述为已限制问答范围。

## 3. 检索链路

- 基线候选由关键词与向量检索组成，并按当前检索设置合并排序。
- `jieba` 已列入 `backend/requirements/base.txt`，但当前源码没有调用它；中文分词增强尚未生效。
- 默认向量兼容路径保存在 SQLite。`qdrant-client` 已列入基础依赖，但只有 `RAG_VECTOR_STORE_PROVIDER=qdrant` 时启用 Qdrant local mode；写入/查询失败回退 SQLite。
- 启用 Qdrant 时，SQLite 仍保存 chunk 与向量兼容副本；Qdrant 不改变 HTTP 字段，`vector_provider`/`vector_model` 表示 embedding 来源，不表示向量数据库。
- `sentence-transformers` 不在基础依赖中；只有另外安装且启用 reranker 时才使用 Cross-Encoder，缺失时跳过 rerank。
- 旧数据库若已经存在兼容的 `graph_nodes`/`graph_edges`，系统可只读扩展一跳候选；当前 v2 Schema 不创建这两张表，也不自动生成图谱，因此新安装默认没有图增强。

## 4. 回答与降级

- 回答使用当前项目来源、最近会话上下文、当前 Prompt 预设和可选只读工具上下文。
- 外部 LLM 不可用时返回本地、有来源的降级结果和 warning。
- Embedding API 不可用时回退本地 hashing；Qdrant 不可用时回退 SQLite；reranker 依赖缺失时跳过该阶段。
- SSE 使用 `token`、`done`、`answer_error` 事件；`done` 的最终业务载荷与非流式回答保持一致。

## 5. 边界

- 图增强不是新 v2 数据库的默认能力，也不支持二跳以上遍历。
- 当前没有把资料弹窗选择接入回答范围。
- 本能力不承诺跨项目搜索、远程知识同步或无来源生成。
