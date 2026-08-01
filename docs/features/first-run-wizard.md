# 首次运行引导

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：首次使用时检查 Ollama、拉取推荐模型并创建项目
> Related：`project-space-ingestion.md`、`../design/api-spec.md`、`../guides/setup.md`、`../guides/troubleshooting.md`

## 1. 当前可达

教练工作台在没有项目且尚未关闭引导时挂载 `FirstRunWizard`：

1. 调用 `GET /api/ollama/status` 查看 Ollama 是否可用和本地模型。
2. 用户选择推荐模型后，调用 `POST /api/ollama/pull` 并通过 SSE 展示下载状态。
3. 用户填写名称与本地路径，复用项目创建流程创建第一个项目。

推荐列表当前为 `qwen2.5:3b`、`qwen2.5:7b` 和 `deepseek-r1:8b`。Ollama 不可达时给出明确状态，不阻止本地 Web 应用启动。

## 2. 边界

- 引导不安装或自动启动 Ollama，不执行任意 shell。
- 引导关闭状态只属于当前前端会话状态，不是跨设备账户偏好。
- 项目创建与模型拉取复用既有 API，不新增数据库结构或 Agent 权限。
