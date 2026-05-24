# 功能模块说明

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-22
> Scope：本地 Web MVP 当前可见功能边界

## 1. 模块清单

| 模块 | 当前状态 | 说明 |
|------|----------|------|
| 项目空间（Project） | 已实现（Web MVP） | 支持创建、选择、改名、删除、最近项目恢复；legacy `Workspace` 兼容层保留 |
| 文档导入与扫描 | 已实现（Web MVP） | 支持本地目录导入、浏览器文件夹导入、文本笔记导入、增量统计、删除检测和跳过/错误明细 |
| 文档处理 | 已实现（Web MVP） | 支持文本类文件、DOCX 正文抽取和可选 `pymupdf` PDF 正文抽取；失败时明确跳过 |
| RAG 分块检索 | 已实现（Web MVP） | 导入时生成 `document_chunks` 与 `chunk_vectors`，检索使用 keyword + vector 混合召回 |
| 知识库问答 | 已实现（Web MVP） | 本地片段组合回答与 OpenAI-compatible LLM 回答并存，返回来源、来源质量和聊天记录 |
| 检索调试与复盘 | 已实现（Web MVP） | 支持临时调整检索参数、查看命中分数和保存检索复盘快照 |
| Agent 只读工具 | 已实现（Web MVP） | 只开放项目概览和来源检索，记录工具审计；不开放 shell 或任意写入 |
| 掌握评估 | 最小闭环（Web MVP） | 从已导入文件生成题目并规则化评分；不同于 legacy 完整 Knowledge Mastery 模型 |
| 标签、知识点、知识图谱 | legacy / 模型储备 | `src/` 分层模型与部分存储保留，Web MVP 尚未完成完整 UI 闭环 |
| 生成能力（简历/JD/面试） | 历史兼容 | 不属于当前 Web MVP 主线，后续如恢复需单独进入 Backlog |
| 非技术用户发布体验 | 部分实现 | 已有 Windows zip/bat、Docker Compose 和 Docker 双击入口；安装器、桌面快捷方式仍非承诺范围 |

## 2. 模块边界

- 当前默认 Web MVP 模块边界：
  - `webapp/server.py` 负责 HTTP server 与静态文件服务。
  - `webapp/api.py` 负责 API 路由分发，不直接写 SQLite。
  - `webapp/storage.py` 负责 SQLite schema 与读写。
  - `webapp/ingestion.py`、`webapp/upload_import.py`、`webapp/source_import.py` 负责不同来源的资料入库。
  - `webapp/search.py` 负责检索和排序。
  - `webapp/answers.py` 负责基于检索片段生成回答。
  - `webapp/static/js/*.js` 按 API、状态、项目、问答、渲染拆分前端逻辑。
- legacy 桌面端模块边界：
  - `src/application/*` 负责流程编排与事务边界。
  - `src/adapters/*` 负责持久化、向量和 LLM 接入。
  - `src/desktop/*` 负责 UI 交互，不直接承载规则决策。

## 3. 不纳入当前说明

- 模块拆解不在此处放置后续路线；后续需求改为 `BACKLOG.md` 项目条目。
- 任何未在上述模块状态表出现的功能默认为“研发中或规划中”。
