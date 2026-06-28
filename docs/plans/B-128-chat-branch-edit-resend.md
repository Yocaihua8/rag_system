# B-128 对话分支与历史消息编辑重发

> 状态：Active
> 创建时间：2026-06-28
> 创建方：Codex
> 关联 BACKLOG：B-128
> 关联功能文档：docs/features/chat-branching.md
> 关联设计文档：docs/design/new-architecture-design.md §5.5.3, docs/design/api-spec.md, docs/design/database-design.md

## 1. 目标

在现有聊天会话与问答链路上支持“编辑历史消息并重发”，保存新生成的分支消息，同时保留原消息和原会话历史。

## 2. 前置条件

- 已读取 `AGENTS.md`、`docs/BACKLOG.md`、`docs/design/new-architecture-design.md §5.5.3`。
- B-145 当前为 `blocked`，影响 `src-tauri/` 和打包脚本，不阻塞本任务。
- 工作区已有未提交的 B-142/BACKLOG/前端相关改动；本任务提交时必须按 B-128 hunk 精准暂存，避免吸收无关改动。
- B-128 会触及 `chat_messages` SQLite schema；依据 `new-architecture-design.md §5.5.3` 执行，生产代码改 schema 前需在执行记录中标明确认依据。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照。
未完成项不得删除。

- [x] 任务 1：写 B-128 红灯测试
- [x] 任务 2：扩展 `ChatMessage` 模型、SQLite 字段迁移和存储层分支写入
- [x] 任务 3：让 `/api/answer` 与 `/api/answer/stream` 接收 `parent_message_id` 并保存分支消息
- [x] 任务 4：在 Vue 工作台接入历史消息编辑重发 UI 和 API helper
- [ ] 任务 5：同步 API、数据库、功能文档和前端工程文档
- [ ] 任务 6：运行回归验证并关闭 B-128

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 代码 | `webapp/models.py` | 修改 `ChatMessage` 字段和序列化 |
| 代码 | `webapp/storage.py` | 新增 `parent_message_id`、`branch_index` 字段迁移与写入/读取 |
| 代码 | `webapp/answer_api.py` | 校验 `parent_message_id`，将分支信息传入消息保存 |
| 代码 | `webapp/api.py` | SSE query 增加 `parent_message_id` |
| 代码 | `frontend/src/api/answer.js` | 问答 helper 透传 `parent_message_id` |
| 代码 | `frontend/src/components/ChatThread.vue` | 历史消息编辑重发入口 |
| 代码 | `frontend/src/views/WorkbenchView.vue` | 事件透传 |
| 代码 | `frontend/src/App.vue` | 编辑重发状态和提交处理 |
| 测试 | `tests/test_webapp/test_chat_history.py` | 后端红灯与回归测试 |
| 测试 | `tests/test_webapp/test_api.py` | `/api/answer` 和 SSE 分支参数测试 |
| 测试 | `tests/test_webapp/test_frontend_vue_app.py` | Vue helper/UI 静态契约测试 |
| 文档 | `docs/features/chat-branching.md` | 新增/完善功能文档 |
| 文档 | `docs/design/api-spec.md` | 同步 API 契约 |
| 文档 | `docs/design/database-design.md` | 同步 SQLite 字段 |
| 文档 | `docs/features/frontend-engineering.md` | 同步 Vue 工作台行为 |
| 文档 | `docs/BACKLOG.md` | B-128 状态与完成记录 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-128 可在当前 Web MVP 聊天/问答链路上独立实现 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `docs/plans/B-145-tauri-windows-packaging.md` | 仅共享 `docs/BACKLOG.md` 和设计文档引用；B-145 代码范围是 `src-tauri/`、打包脚本和桌面文档 | 分区：B-128 不改 Tauri 打包文件；B-145 仍因 Rust/Cargo blocked |
| 当前未提交 B-142 前端工作区改动 | `frontend/src/App.vue`、`frontend/src/api/answer.js`、`frontend/src/components/ChatThread.vue`、`frontend/src/views/WorkbenchView.vue`、`tests/test_webapp/test_frontend_vue_app.py` | 分区：先做后端红灯与实现；前端任务执行时只追加 B-128 hunk，不回退或重写既有 B-142 改动 |

## 6. 完成标准

全部勾选后方可删除本 plan 文件：

- [ ] 功能行为符合 `docs/features/chat-branching.md` 的业务规则
- [ ] `tests/test_webapp` 相关测试通过，必要时运行全量 Web MVP 回归
- [ ] 相关文档已同步（见下方“回流清单”）
- [ ] BACKLOG 条目 `B-128` 状态已更新为 `done`

## 7. 回流清单

删除本文件前，确认以下内容已写入正式文档：

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 历史消息编辑重发的用户行为、边界和非目标 | `docs/features/chat-branching.md` | [ ] |
| `parent_message_id` / `branch_index` 响应字段和问答请求参数 | `docs/design/api-spec.md` | [ ] |
| `chat_messages` 新增字段、默认值和迁移方式 | `docs/design/database-design.md` | [ ] |
| Vue 工作台新增编辑重发入口 | `docs/features/frontend-engineering.md` | [ ] |
| B-128 完成状态 | `docs/BACKLOG.md` | [ ] |

## 8. 执行记录

- 2026-06-28：B-128 依据 `docs/BACKLOG.md` 中首个可执行 `todo` 启动；B-145 保持 blocked。
- 2026-06-28：工作区存在未提交的 BACKLOG 重排和 B-142 前端改动，后续提交必须避免整文件吸收。
- 2026-06-28：任务 1 红灯测试已添加。目标命令运行结果为 4 failed，失败点分别是 `create_chat_message()` 不接受 `parent_message_id`、响应 `message` 缺少 `parent_message_id`、跨会话父消息未返回 `404 parent chat message not found`、SSE `done` 缺少分支字段。
- 2026-06-28：任务 2 依据 `docs/design/new-architecture-design.md §5.5.3` 修改 `chat_messages` schema，新增 `parent_message_id` 与 `branch_index`；旧消息默认 `parent_message_id=""`、`branch_index=0`。
- 2026-06-28：任务 3 将 `parent_message_id` 接入 `/api/answer` 与 `/api/answer/stream`，校验父消息同项目同会话。`tests/test_webapp/test_chat_history.py -q` 通过 15 项。
- 2026-06-28：任务 4 需要修改 `frontend/src/components/ChatThread.vue`，但该文件当前为未跟踪的 B-142 工作区文件；直接提交会把整份 B-142 组件并入 B-128，违反“不要吸收无关改动”。任务暂停，等待 B-142 前端文件先提交/合并，或用户明确允许 B-128 吸收这些前端文件。
- 2026-06-28：用户选择方案 1，已先提交 B-142 前端会话迁移 `953bba6`，`ChatThread.vue` 等文件已纳入版本控制；恢复任务 4。
- 2026-06-28：任务 4 完成 Vue 编辑重发入口。`tests/test_webapp/test_frontend_vue_app.py -q` 通过 72 项；`npm run build` 在实现后通过。

## 9. 状态快照

- **最后更新**：2026-06-28 22:05
- **进度**：已完成 4 / 6 项（见 § 3 勾选状态）
- **最新 commit**：待提交 — feat: 接入对话编辑重发前端入口
- **代码状态**：分支 `fix/B-128-chat-branch-edit-resend`；B-128 后端和前端交互已实现；文档同步与关闭流程待做
- **下一步**：任务 5：同步 API、数据库、功能文档和前端工程文档
- **续任务须知**：任务 5 需同步 `docs/design/api-spec.md`、`docs/design/database-design.md`、`docs/features/chat-branching.md`、`docs/features/frontend-engineering.md`，并谨慎处理 `docs/BACKLOG.md` 当前仍有未提交重排。
