# 项目背景与范围

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-22
> Scope：知识岛当前实施边界
> Related：`requirements/functional-modules.md`

## 1. 项目结论

知识岛（Knowledge Island）是本地优先的个人 AI 第二大脑 / 项目知识库助手。当前默认交付形态是本地 Web MVP：通过 `app.py` 启动本机 HTTP 服务，在浏览器中完成项目空间、资料导入、检索、问答、来源查看、检索复盘和掌握评估。

核心目标是把本地项目文件、文档、笔记和代码资料沉淀为可检索知识资产，形成：导入 → 标准化 → 分块/向量 → 检索 → 问答与知识复盘的闭环。

## 2. 当前实现范围（本地优先）

- 本地 Web MVP：Python 标准库 HTTP 服务 + SQLite + 原生 HTML/CSS/JavaScript。
- 项目空间创建、选择、改名、删除和最近项目恢复。
- 本地目录导入、浏览器文件夹导入、文本笔记导入。
- 本地文件（`.md/.txt/.py/.ts/.json/.yaml/.yml/.pdf/.docx` 等）导入；PDF 正文抽取依赖可选 `pymupdf`，未安装时明确跳过。
- SQLite 文档、分块、向量、聊天记录、Agent 只读工具审计和检索复盘存储。
- keyword + vector 混合检索，支持检索调试、来源质量提示和检索复盘。
- 知识库问答：未配置模型时基于检索片段组合回答，配置 OpenAI-compatible LLM 后优先真实模型回答。
- Web 最小掌握评估：从已导入文件生成题目，提交回答后给出规则化反馈和建议阅读来源。

旧 PySide6 桌面端代码暂时保留在 `src/desktop/`，作为 legacy 参考和后续迁移来源，不是当前默认入口。

## 3. 非目标范围

- 分布式多人协同（当前无服务端多人同步）。
- 云端知识库托管（当前仅提供本地数据库/向量目录）。
- 完整 OCR（解析依赖暂时存在降级）。
- 公开 API 服务（当前 HTTP API 仅用于本机 Web MVP，不承诺远程多用户调用）。
- 旧简历 / JD / 面试脚本增强不进入当前主线；如保留，只作为历史兼容或后续输出工具。

## 4. 关键边界

- 当前默认运行边界以 `app.py` -> `webapp.server.run_server()` -> `webapp.api.dispatch()` 为准。
- Web MVP 保持轻量实现，不引入大型 Web 框架或运行时依赖。
- legacy 代码继续遵守分层 + 端口适配约束，但新任务不要在未确认迁移范围时同时修改 `webapp/` 和 `src/desktop/`。
- 兼容层继续保留 `Workspace`，新语义逐步收敛到 `Project`。
- 未完成能力（如完整知识图谱问答、能力差距可视化）写入 `BACKLOG.md`，不在现有“定稿行为”文档内宣称已上线。
