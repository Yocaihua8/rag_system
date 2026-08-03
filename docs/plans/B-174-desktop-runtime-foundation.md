# B-174 桌面会话认证、随机端口与 v3 数据运维基础

> 状态：Active
> 创建时间：2026-08-03
> 创建方：Codex
> 关联 BACKLOG：B-174
> 关联功能文档：`../features/agent-tasks-and-runs.md`
> 关联设计文档：`../adr/ADR-010-runtime-separation.md`、`../design/permission-matrix.md`、`../design/database-design.md`

## 1. 目标

建立不依赖固定 8765 端口和长期共享 Key 的桌面后端启动边界，并为 v3 数据根提供可验证的存储预检、一致性备份和失败可回滚恢复。能力默认关闭，不在 B-177 正式切换前改变现有 Vue/Tauri 运行方式。

## 2. 前置条件

- v3 数据代际、Alembic revision 和固定 Agent 运行闭环已经通过全量门禁。
- B-175 React 工程已提交但等待用户高保真验收；本计划不修改其 UI、路由或演示状态。
- 当前 Tauri 仍使用 Vue 和固定 8765；B-174 只能建立可独立验证的非视觉能力，不能提前切换正式入口。

## 3. 任务拆解

每完成一项，立即执行：① 勾选此处 ② `git commit` 保存进度 ③ 更新 § 9 状态快照 ④ 追加当日 DevLog。

- [x] 记录桌面临时端口、进程期令牌和 Web 认证分界 ADR，冻结默认关闭与回滚规则。
- [x] 实现后端桌面模式配置、精确环回绑定、会话令牌校验和兼容认证测试。
- [ ] 实现 Tauri sidecar 随机端口/令牌生成、内存 bootstrap 与精确 capability；不切换正式前端。
- [ ] 实现 v3 存储目标预检、路径隔离和可用空间检查。
- [ ] 实现 v3 在线一致性备份、manifest/hash 校验和保留策略。
- [ ] 实现离线或受控停机恢复、失败回滚与代际/revision 复验。
- [ ] 完成 Python、Rust、仓库、真实 sidecar 和文档全量门禁并关闭 B-174。

## 4. 影响范围

| 类型 | 路径 / 模块 | 变更方向 |
|------|------------|---------|
| 后端 | `backend/__main__.py`、`backend/api/`、`backend/config/` | 新增默认关闭的 desktop mode、会话令牌与系统运维 API |
| 数据 | `backend/storage/v3/` | 新增预检、备份、校验和恢复协调，不修改业务 Schema |
| 桌面 | `src-tauri/` | 随机环回端口、进程期令牌与内存 bootstrap；正式入口保持 Vue |
| 测试 | `tests/backend/`、`tests/integration/`、`tests/repository/` | 覆盖认证、路径、备份恢复、sidecar 和能力边界 |
| 文档 | `docs/adr/`、`docs/design/`、`docs/guides/`、`CHANGELOG.md`、`docs/devlog/` | 同步安全、数据与运维事实 |

## 5. 依赖与冲突

### 5.1 依赖的其他 plan

| plan 文件 | 依赖原因 |
|-----------|---------|
| N/A | B-173 后端基础已完成；B-175 不阻塞默认关闭的桌面后端基础 |

### 5.2 与现有 plan 的重叠

| 冲突 plan | 重叠范围（文件 / 模块 / 接口） | 解决方式 |
|-----------|-------------------------------|---------|
| `B-175-react-frontend-foundation.md` | 最终 Tauri/React bootstrap 接线 | 分区：B-174 只建立默认关闭的后端与壳能力，不修改 React UI；B-175 转为 Interrupted 等待验收 |
| `B-178-guided-agent-conversation.md` | DevLog 和最终发布状态 | 分区：B-178 只等待 Sites 外部恢复，不修改仓库运行时 |

## 6. 完成标准

- [ ] Desktop mode 只监听 `127.0.0.1`，端口由壳动态选择，令牌只在父子进程内存/环境传递且日志不输出。
- [ ] Web mode 原 API Key/JWT 与 Obsidian 自认证边界保持兼容；desktop mode 未启用时行为不变。
- [ ] 备份经过 SQLite 在线备份、完整性、v3 代际、Alembic revision 和 manifest hash 验证。
- [ ] 恢复只接受已验证备份，失败时保留并恢复原数据，不触碰 v2 或相邻目录。
- [ ] Python、Rust、仓库、文档和真实 sidecar 门禁通过。
- [ ] BACKLOG 条目 B-174 已移除，完成事实已写入 `CHANGELOG.md` 与 Git 历史。

## 7. 回流清单

| 内容 | 目标文档 | 是否完成 |
|------|----------|----------|
| 桌面端口/令牌/认证边界 | `../adr/`、`../design/permission-matrix.md` | [x] |
| 存储预检、备份恢复合同 | `../design/database-design.md`、`../guides/runbook.md` | [ ] |
| 启动、测试和迁移边界 | `../guides/setup.md`、`../guides/testing.md`、`../guides/v3-upgrade.md` | [ ] |

## 8. 执行记录

- 2026-08-03：用户要求“继续完成后端”。按既定阶段顺序恢复 B-174；B-175 仅等待界面验收，因此中断而不删除。
- 当前固定 8765、无桌面会话令牌的 Tauri 行为继续作为 v2 正式基线；新增能力必须默认关闭，直到 B-177 明确切换。
- 2026-08-03：新增 ADR-018，冻结临时 loopback 端口、64 位十六进制进程期令牌、专用 Header、Web 认证分界和默认关闭规则。
- 2026-08-03：后端新增默认关闭的 desktop mode、严格令牌/端口配置、精确环回校验和专用 Header 认证；27 项定向测试覆盖 Web 兼容、API 文档、health、CORS 与 Obsidian 自认证边界。
- 2026-08-03：更新服务入口仓库契约后，全量 Python 后端、集成和仓库测试 688 项通过；三项文档门禁通过。

## 9. 状态快照

- **最后更新**：2026-08-03 09:55:41 +08:00
- **进度**：已完成 2 / 7 项（见 § 3 勾选状态）
- **最新 commit**：`06450b4` — 冻结桌面临时端点认证边界
- **代码状态**：`refactor/agent-v3`；后端 desktop mode 与认证测试待提交
- **下一步**：实现 Tauri sidecar 随机端口/令牌生成、内存 bootstrap 与精确 capability
- **续任务须知**：不得把令牌放入 CLI 参数、日志、SQLite 或前端持久存储；不得在本计划提前切换 Vue/Tauri/正式入口
