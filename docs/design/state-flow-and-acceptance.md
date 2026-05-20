# 状态流转与验收标准

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-16
> Scope：核心流程可验收行为

## 1. 摄入流程状态

```text
scan -> parse -> normalize -> split -> embed -> index -> done/failed
```

- `scan`：发现新增/修改/删除文件。
- `parse`：文件解析失败时进入 `warn`，不阻塞全量。
- `normalize`：生成 `normalized_markdown / plain_text / rendered_html`。
- `split`：生成 chunk 与 heading path。
- `embed`：可配置向量化或降级。
- `index`：向量索引更新或清理。
- `done`：写入 `documents/chunks` 成功，更新 ingest 报告。

## 2. 问答流程

```text
question -> embed_query -> retrieve -> build_prompt -> generate -> render_sources
```

验收要求：

- 命中为空时返回“缺少来源”提示，不展示伪造答案。
- 命中来源文件与 chunk 信息一致。

## 3. 关键验收标准

| 场景 | 通过标准 |
|------|----------|
| 增量更新 | 变更文件重建并清理旧 chunks；未变更文件不重建 |
| 文件删除 | documents/chunks/retriever/source 级联清理 |
| HTML 安全 | `script/style`、事件属性不得执行 |
| 成功率 | 单文件解析失败不影响其他文件入库 |
