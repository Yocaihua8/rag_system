# 系统设计总览

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-22
> Scope：知识岛本地 Web MVP 与知识流水线
> Related：`design/architecture-overview.md`

## 1. 设计结论

知识岛当前采用以本地 Web MVP 为默认交付边界的“本地优先 AI 助手”系统设计。核心目标是降低“文件到知识”的认知成本，且不要求联网数据库即可完成常态使用。

```text
[本地文件系统/浏览器上传/文本笔记] -> [文档入库/标准化]
                                      -> [SQLite 文档分块 + 向量]
                                      -> [检索 + 回答 + 复盘]
                                      -> [本机浏览器 Web UI]
```

## 2. 系统边界

- 输入边界：本地目录、浏览器授权文件夹上传、文本笔记与本地设置。
- 处理边界：Web MVP 使用 SQLite、hashing 向量或 OpenAI-compatible embeddings、OpenAI-compatible Chat Completions；legacy 桌面链路仍保留 ChromaVector/Numpy Store、Ollama 等适配器。
- 输出边界：本机浏览器 Web UI 回显、索引结果、检索调试、问答来源、聊天记录、Agent 只读工具审计与检索复盘。

## 3. 关键协作点

- Web MVP 文档标准化、检索、问答是同一个业务链路：`import -> process -> split -> embed/hash -> retrieve -> answer/review`。
- 项目空间与知识模型是长期演进入口；现有 legacy 兼容层 `Workspace` 保持稳定。
- `src/desktop/` 暂时作为 legacy 参考保留，不作为当前默认启动入口。

## 4. 非功能性约束

- 大文件扫描不应阻塞主线程。
- 单文件解析失败不应中断整批扫描；应记录并继续。
- HTML 渲染必须安全边界化，禁止脚本执行。
