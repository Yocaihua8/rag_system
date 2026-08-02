# Agent Runtime 与工具契约

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-02
> Scope：v3 任务执行、持久状态、工作流节点、审批和工具安全边界
> Related：`../requirements/agent-product-v3.md`、`../features/agent-tasks-and-runs.md`、`api-spec.md`、`database-design.md`、`permission-matrix.md`

## 1. 职责边界

| 层 | 职责 | 禁止事项 |
|----|------|----------|
| HTTP/API | 请求校验、鉴权、错误映射、SSE 输出和用例调用 | 直接执行步骤或操作 SQLite |
| Application | 创建任务、运行、审批、工作流发布等用例编排 | 承载 HTTP 对象或 UI 文案 |
| Domain/Workflow | 状态转换、DAG 校验、节点定义、重试与审批规则 | 访问数据库或任意外部资源 |
| Worker | 租约领取、容量控制、取消、恢复和节点调用 | 以内存状态代替持久状态 |
| Infrastructure | SQLite、模型、检索、解析、文件和连接器适配 | 绕过领域权限或审批 |

HTTP 创建运行时只提交持久状态；执行器由应用 lifespan 启动并从数据库领取步骤。浏览器或 SSE 连接断开不能取消持久运行。

## 2. 核心实体和状态

### Task 与 Run

- Task 固定绑定 `project_id`，保存任务标题、消息和最近运行。
- Run 固定绑定 Task、工作流发布版本和深度档位。
- Task/Run：`queued / running / waiting_approval / paused / completed / failed / cancelled`。
- Run 在应用重启恢复期间可以为 `recovering`。

### Step

状态为 `pending / queued / running / waiting_approval / succeeded / failed / skipped / cancelled / recovery_required`。步骤尝试独立保存开始/结束时间、租约、错误和结果摘要。

### Approval 与 Artifact

- Approval：`pending / approved / rejected / expired`。
- Artifact：`draft / ready / exported / failed`。
- 审批决议和产物导出都是幂等写操作，结果写入只追加事件。

## 3. 调度和恢复

- 全局最多两个读取/分析步骤并行。
- 同一项目的写步骤通过数据库事务锁串行，不能只使用进程内互斥锁。
- 运行暂停后不再领取新步骤；当前可取消读取步骤按节点能力安全取消。
- 等待审批的步骤释放全局运行槽。
- 读取/分析失败最多自动重试两次，并为每次尝试创建独立记录。
- 写步骤开始后不自动重试；应用重启时仍为 `running` 的写步骤转为 `recovery_required`。
- worker 使用有限租约和心跳；过期读取租约可以重新领取，写租约不能在结果不明确时自动领取。

## 4. 事件与 SSE

`agent_events` 为每个 Run 保存单调递增的 `sequence`。事件至少包含：

```text
id, run_id, step_id?, sequence, event_type, payload, created_at
```

- 服务端先提交状态和事件，再向 SSE 客户端发送。
- 客户端通过 `Last-Event-ID` 或 `after_sequence` 恢复；重复序号必须忽略。
- 事件 payload 使用 Pydantic discriminated union；事件中不得出现 API Key、令牌、完整敏感输入或任意本地绝对路径。
- 断开 SSE 不影响 Run；Run 终态后事件历史仍可读取。

## 5. 工作流版本

- Workflow Definition 保存身份、名称、归档状态和当前发布版本引用。
- Workflow Version 保存不可变 DAG、版本号和内容 checksum。
- 编辑发布版本时复制为新草稿；发布不能原地改变历史版本。
- v3 首版只允许一个 `trigger.manual`，且必须存在至少一个可达终点。
- 校验必须拒绝循环、孤立节点、无效边、端口类型不匹配、必填参数缺失、无效资源引用和未受审批保护的写节点。

## 6. 节点注册表

首版只允许以下节点类型：

| 分类 | 节点 |
|------|------|
| 触发 | `trigger.manual` |
| Agent | `agent.plan` |
| 来源 | `source.search`、`source.read` |
| 分析 | `project.analyze`、`insight.assess`、`learning.plan` |
| 模型 | `llm.synthesize`、`llm.compare` |
| 产物 | `artifact.create`、`artifact.export` |
| 确认/集成 | `approval.request`、`obsidian.publish` |
| 控制 | `control.branch`、`control.join` |

每个节点声明版本、输入/输出端口、Pydantic 配置模型、读写类别、可重试性、取消能力和执行器。不存在“自定义脚本”或可传任意 URL/命令/路径的配置。

## 7. 权限与路径

- 读取节点只能访问任务项目已登记的来源和用户授权根目录。
- 文件路径先解析真实路径，再验证位于授权根内；符号链接不能逃逸。
- 项目文件、外部系统、导出和发布写操作必须通过 `approval.request`。
- 审批冻结 node type、目标、参数、资源版本和 request hash；任何变化都要求新审批。
- Desktop sidecar 只监听随机 `127.0.0.1` 端口，并校验每次启动生成的令牌。
- Web 部署使用独立认证，不能接受 Desktop 启动令牌。

## 8. 深度档位

| 档位 | 最多步骤 | 最多检索轮次 |
|------|----------|--------------|
| Quick | 4 | 1 |
| Standard | 8 | 3 |
| Deep | 16 | 6 |

档位是上限，不要求用满。运行创建后保存实际档位，worker 不接受前端临时扩大上限。

## 9. 当前实现状态

本文是 v3 后端阶段的目标合同。当前 v2 只读 Agent 工具保持现状，直到 v3 垂直切片通过测试并完成切换；不能依据本文宣称 v3 已经可用。
