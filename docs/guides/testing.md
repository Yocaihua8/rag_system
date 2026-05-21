# 测试指南

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-21

## 1. 目标

优先验证“文档行为 → 用例行为 → 集成行为”三层是否一致，避免只测单点函数。

## 2. 命令建议

```bash
.venv\Scripts\python.exe -m pytest tests/test_webapp -q
.venv\Scripts\python.exe -m pytest tests/test_application/test_markdown_content.py -q
.venv\Scripts\python.exe -m pytest tests/test_application/test_ingestion_usecases.py -q
.venv\Scripts\python.exe -m pytest tests/test_adapters/test_storage.py tests/test_domain/test_models.py -q
docker compose config
```

## 3. 说明

- 受环境限制时，`pytest` 可能因依赖/网络导致不能完整运行，需在提交说明里写出失败原因与替代验证。
- 变更文档行为时，需复跑 markdown 安全与增量更新相关用例。
- 变更默认 Web MVP 的 API、导入、检索、回答或聊天记录行为时，必须复跑 `tests/test_webapp`。
- 变更 Web RAG 分块、embedding provider、向量索引、搜索排序或来源字段时，必须覆盖 chunk 生成、向量持久化、API embedding 请求体、失败回退、文档更新后 chunk/vector 重建、搜索响应 `chunk_id/chunk_index/retrieval/keyword_score/vector_score/vector_provider/vector_model` 和问答来源兼容。
- 变更浏览器文件夹导入时，必须覆盖 `/api/import/upload`、前端 `webkitdirectory` 入口和导入规则跳过行为。
- 变更 Web 文档处理管线时，必须覆盖 DOCX 正文抽取、PDF 明确跳过、浏览器上传 `content_base64` 和普通文本导入兼容行为。
- 变更模型设置页时，必须覆盖 `/api/settings/llm`、`/api/settings/llm/test`、Key 不回显和前端设置入口。
- 变更 Agent 工具能力时，必须覆盖 `/api/agent/tools`、`/api/agent/tools/run`、只读工具白名单、未知工具拒绝和 `agent_tool_runs` 审计记录。
- 变更 Web 端 LLM、掌握评估、首次引导或静态前端约束时，必须复跑 `tests/test_webapp`，并执行 `Get-ChildItem webapp\static\js\*.js | ForEach-Object { node --check $_.FullName }`。
- 变更 Docker 启停入口时，必须复跑 `tests/test_webapp/test_docker_startup.py`，并至少真实执行一次启动或停止脚本。

## 4. 回归清单

- Markdown 安全渲染链路
- 增量增删改（含源文件删除）
- 向量检索 + 来源返回一致性
- 用例级错误消息与状态码（若有）
- Web MVP 创建项目空间、导入目录、分块生成、向量索引生成、问答来源返回
- Web MVP 提问后可持久化聊天记录，并能按项目重新加载 `question/answer/mode/provider/sources`；真实 LLM prompt 会包含最近 3 轮历史
- Web MVP Agent 工具只开放只读项目概览和来源检索，未知工具会被拒绝并记录审计
- Web MVP 浏览器文件夹导入可创建上传项目，并按后缀、忽略目录和大小规则跳过文件；DOCX 可抽取正文，PDF 有明确跳过原因
- Web MVP DeepSeek 配置存在时优先真实 LLM，失败时本地回退
- Web MVP 模型设置页可保存 API Base / 模型名 / Key，且不回显 Key 明文
- Web MVP 掌握评估入口、题目生成、回答反馈
- Web MVP 首次使用引导可见
- Docker 一键启动文件存在且端口、运行时目录、导入目录、DeepSeek 环境变量映射、双击启动/停止入口符合约定
