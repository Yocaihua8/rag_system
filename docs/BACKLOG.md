# BACKLOG

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Related：`features/README.md`、`design/architecture-overview.md`、`plans/README.md`

本文件只保存未完成、待验证、待决策或明确不处理的事项。完成并验证后删除对应条目，把对使用者/维护者有意义的事实写入 `CHANGELOG.md`；完整过程由 Git 历史保存。

## 1. 状态与规模

- `todo`：待开始
- `doing`：进行中
- `blocked`：存在外部阻塞
- `wontfix`：已明确暂不处理；仍保留是为了记录当前边界

优先级：`P0` 必须尽快处理、`P1` 重要、`P2` 常规、`P3` 长期。

规模：`XS` 少于半天、`S` 少于一天、`M` 少于三天、`L` 少于一周、`XL` 超过一周。

## 2. 待办

| ID | 类型 | 标题 | 状态 | 优先级 | 规模 | 负责人 | 关联文档 | 说明 |
|----|------|------|------|--------|------|--------|----------|------|
| B-173 | backend/refactor | v3 Agent 数据、API 与持久执行器 | doing | P0 | XL | Codex | `plans/B-173-v3-agent-runtime.md` | 建立独立 v3 数据根、SQLAlchemy/Alembic Schema、资源 API、持久任务执行、事件续传、审批与产物基础；不修改 Vue。 |
新增代码任务时，先分配下一个 `B-xxx`，状态设为 `doing`，并按 [`plans/README.md`](plans/README.md) 创建执行 plan。

## 3. 已知问题

### ISSUE-009：部分已加载配置未进入活动检索与分块链路

- **发现时间**：2026-08-01（从 ISSUE-006 拆分）
- **现象**：`RAG_CHUNK_SIZE`、`RAG_CHUNK_OVERLAP`、`RAG_RETRIEVER_KIND` 和 `RAG_TOP_K` 等配置可被 `load_settings()` 读取，但部分活动导入或检索链路仍使用固定值；实际分块仍可见 700/80 等硬编码。
- **影响范围**：配置可预期性、分块行为、检索策略与 top-k 调优；不影响 B-169 已修复的 v2 数据库备份和结果输出路径。
- **计划处理方式**：另建独立 B-ID 和 plan，先逐调用链确认哪些设置应进入活动行为，再补配置生效测试；不得在运维路径修复中顺带改变检索业务规则。

### ISSUE-008：当前主资料/聊天界面存在未接线或参数不完整的可见控件

- **发现时间**：2026-07-30
- **现象**：活动 `LibraryModal` 的“网页摘录”只提交 URL，但 API helper 同时要求非空 title/content；“选择资料”没有进入问答 payload；侧栏线程搜索和问题框部分工具按钮没有有效 handler。未挂载的兼容视图不能作为当前可达页面。
- **影响范围**：`frontend/src/components/LibraryModal.vue`、`WorkspaceSidebar.vue`、`QuestionComposer.vue`、`WorkbenchView.vue`、`frontend/src/App.vue`。
- **计划处理方式**：分别建立最小前端/联调任务，冻结交互和 API 契约后补参数、事件和 E2E；修复前功能文档不得描述为完整闭环。

### ISSUE-007：Tauri 安装后完整用户流程与非 Windows 平台仍需验证

- **发现时间**：2026-07-30
- **现象**：B-168 已用当前 Windows NSIS 安装包验证 sidecar 可启动，`/api/health` 返回 200 且根路由返回 404；尚未在已安装 WebView 中跑完 SSE 与核心用户流程，macOS/Linux bundle 也未验证。
- **影响范围**：`src-tauri/`、`frontend/src/api/`、Windows/macOS/Linux 原生运行时。
- **计划处理方式**：在 Windows 已安装 WebView 中补跑 SSE 与核心用户流程，并在 macOS/Linux 目标机完成 bundle、安装和动态连通性验证；未执行的平台不得声称通过。

### ISSUE-005：GitHub Actions 官方 Action 的 Node runtime 弃用警告

- **发现时间**：2026-07-30
- **现象**：CI 通过，但 GitHub 对部分官方 Action 的 Node 20 action runtime 给出弃用警告并由 runner 强制使用 Node 24。
- **影响范围**：`.github/workflows/ci.yml` 的 Action 运行时；不等同于应用测试使用的 Node 版本。
- **计划处理方式**：单独评估官方新版本并通过 PR 复跑 CI，不在无关任务中顺手升级。
