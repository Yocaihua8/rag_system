# BACKLOG

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Related：`product/features/README.md`、`architecture/overview.md`、`governance/plans/README.md`

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
| B-168 | refactor | 仓库结构、文档体系与前后端运行时重构 | doing | P0 | XL | RAG 团队 | `governance/plans/B-168-repository-structure-refactor.md` | 分离前后端依赖、构建产物和运行时，重组测试、运维与文档目录，删除失效历史；HTTP API、SQLite Schema 与 Agent 权限保持不变。 |

新增代码任务时，先分配下一个 `B-xxx`，状态设为 `doing`，并按 [`governance/plans/README.md`](governance/plans/README.md) 创建执行 plan。

## 3. 已知问题

### ISSUE-008：当前主资料/聊天界面存在未接线或参数不完整的可见控件

- **发现时间**：2026-07-30
- **现象**：活动 `LibraryModal` 的“网页摘录”只提交 URL，但 API helper 同时要求非空 title/content；“选择资料”没有进入问答 payload；侧栏线程搜索和问题框部分工具按钮没有有效 handler。未挂载的兼容视图不能作为当前可达页面。
- **影响范围**：`frontend/src/components/LibraryModal.vue`、`WorkspaceSidebar.vue`、`QuestionComposer.vue`、`WorkbenchView.vue`、`frontend/src/App.vue`。
- **计划处理方式**：分别建立最小前端/联调任务，冻结交互和 API 契约后补参数、事件和 E2E；修复前功能文档不得描述为完整闭环。

### ISSUE-007：Tauri 安装后 API 动态连通性仍需当前构建证明

- **发现时间**：2026-07-30
- **现象**：B-168 已明确 WebView 通过绝对 API base 访问 `127.0.0.1:8765` sidecar，但结构契约、bundle 成功不能替代安装后主流程验证。
- **影响范围**：`src-tauri/`、`frontend/src/api/`、Windows/macOS/Linux 原生运行时。
- **计划处理方式**：在目标平台安装当前 bundle，验证 sidecar 启动、CORS、SSE 和核心用户流程；未执行的平台不得声称通过。

### ISSUE-006：v2 输出路径与部分配置仍存在漂移

- **发现时间**：2026-07-30
- **现象**：正式数据库使用 `runtime/v2/app.db`，但结果导出仍写 `data/outputs/`；若干已加载的 chunk/retriever/top-k 配置未进入活动链路，实际分块固定为 700/80。
- **影响范围**：运行目录说明、配置可预期性和备份边界。
- **计划处理方式**：路径修复与配置接线拆成独立任务，补真实备份恢复/配置生效测试，不在仓库结构重构中静默改变业务行为。

### ISSUE-005：GitHub Actions 官方 Action 的 Node runtime 弃用警告

- **发现时间**：2026-07-30
- **现象**：CI 通过，但 GitHub 对部分官方 Action 的 Node 20 action runtime 给出弃用警告并由 runner 强制使用 Node 24。
- **影响范围**：`.github/workflows/ci.yml` 的 Action 运行时；不等同于应用测试使用的 Node 版本。
- **计划处理方式**：单独评估官方新版本并通过 PR 复跑 CI，不在无关任务中顺手升级。
