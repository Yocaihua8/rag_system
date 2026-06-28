# First-Run Wizard

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-06-28
> Scope：B-148 First-Run Wizard（首次运行向导）

## 1. 目标

B-148 面向 Tauri MVP 1 的首次运行体验：帮助用户确认本机 Ollama 状态、拉取推荐模型，并创建第一个知识库。该向导只编排现有 Web MVP 能力，不修改数据库 schema，不扩大 Agent 工具权限。

## 2. 用户流程

1. 检测 Ollama：前端 `FirstRunWizard` 调用 `GET /api/ollama/status`，显示服务是否可用和本地模型列表。
2. 拉取默认模型：用户选择推荐模型后，前端调用 `POST /api/ollama/pull`，用 SSE 展示 `status`、`completed`、`total` 和 `progress`。
3. 创建第一个知识库：Wizard 复用现有项目空间创建事件，不新增专用数据库结构。

## 3. 后端接口

| 接口 | 说明 |
|------|------|
| `GET /api/ollama/status` | 返回 `{available, host, models, recommended_models}` |
| `POST /api/ollama/pull` | SSE 返回模型拉取进度；请求体包含 `model` |

推荐模型第一版固定为 `qwen2.5:3b`、`qwen2.5:7b`、`deepseek-r1:8b`。Ollama 不可达时，接口返回明确状态或 SSE 错误事件，不阻断 Web MVP 启动。

## 4. 前端入口

| 文件 | 说明 |
|------|------|
| `frontend/src/api/ollama.js` | 封装 Ollama 状态检测和模型拉取 SSE 解析 |
| `frontend/src/components/FirstRunWizard.vue` | 展示 Ollama 检测、推荐模型下载和第一个知识库创建入口 |
| `frontend/src/App.vue` | 启动时检测 Ollama，并维护 Wizard 状态、模型拉取进度和关闭状态 |
| `frontend/src/views/WorkbenchView.vue` | 在工作台顶部挂载 First-Run Wizard |

## 5. 非目标

- 不自动安装 Ollama。
- 不自动启动 `ollama serve`。
- 不新增任意 shell 执行能力。
- 不修改现有 `/api/projects`、`/api/import`、`/api/answer` 契约。
- 不把模型下载逻辑写死在前端；前端只调用后端白名单接口。
