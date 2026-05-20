# 测试指南

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-05-20

## 1. 目标

优先验证“文档行为 → 用例行为 → 集成行为”三层是否一致，避免只测单点函数。

## 2. 命令建议

```bash
.venv\Scripts\python.exe -m pytest tests/test_webapp -q
.venv\Scripts\python.exe -m pytest tests/test_application/test_markdown_content.py -q
.venv\Scripts\python.exe -m pytest tests/test_application/test_ingestion_usecases.py -q
.venv\Scripts\python.exe -m pytest tests/test_adapters/test_storage.py tests/test_domain/test_models.py -q
```

## 3. 说明

- 受环境限制时，`pytest` 可能因依赖/网络导致不能完整运行，需在提交说明里写出失败原因与替代验证。
- 变更文档行为时，需复跑 markdown 安全与增量更新相关用例。
- 变更默认 Web MVP 的 API、导入、检索或回答行为时，必须复跑 `tests/test_webapp`。
- 变更 Web 端 LLM、掌握评估、首次引导或静态前端约束时，必须复跑 `tests/test_webapp`，并执行 `node --check webapp\static\js\*.js`。

## 4. 回归清单

- Markdown 安全渲染链路
- 增量增删改（含源文件删除）
- 向量检索 + 来源返回一致性
- 用例级错误消息与状态码（若有）
- Web MVP 创建项目空间、导入目录、问答来源返回
- Web MVP DeepSeek 配置存在时优先真实 LLM，失败时本地回退
- Web MVP 掌握评估入口、题目生成、回答反馈
- Web MVP 首次使用引导可见
