# 风险登记
> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：Knowledge Island v2.0.0 当前实现、运行、数据、桌面、插件和治理风险
> Related：`../architecture/overview.md`、`../architecture/contracts/permissions.md`、`../BACKLOG.md`、`../architecture/decisions/ADR-008-project-knowledge-coach-v2.md`、`../architecture/decisions/ADR-009-obsidian-plugin-bridge.md`

## 1. 当前活动风险

| ID | 风险 | 触发条件 | 影响 | 当前缓解 / 下一门禁 |
|----|------|----------|------|---------------------|
| R-01 | v2 备份路径漂移 | 直接使用仍指向旧库的 `ops/scripts/backup_db.sh` | 备份遗漏当前 `runtime/v2/app.db` | runbook 明确禁止直接作为 v2 备份；代码修复和恢复演练进入 BACKLOG ISSUE-006 |
| R-02 | Tauri API 连通性未动态覆盖 | 已配置绝对 8765 API URL、CORS 与 CSP，但安装后主流程尚未成为自动门禁 | 安装包启动但业务不可用 | 静态打包证据不作为动态证明；真实安装包主流程为下一发布门禁，见 ISSUE-007 |
| R-03 | 可见 UI 与端到端能力不一致 | 未接线控件、参数不完整或未挂载 view 被当作已交付 | 用户操作失败、文档夸大 | 前后端契约对照列出差距；逐项补事件/API/E2E，见 ISSUE-008 |
| R-04 | 健康检查过浅 | `/api/health` 返回 ok，但 SQLite/模型/向量不可用 | 运维误判可用性 | 文档称“活性检查”；发布/运维另做读写和主流程验证 |
| R-05 | 数据代际保护并非所有脚本共有 | 通过未传 `expected_generation="v2"` 的维护脚本初始化存储 | 旧库被误识别或写入 | 只对正式 Web 链路声明已保护；脚本入口单独审计和测试 |
| R-06 | 外部模型/Embedding 质量与可用性 | Key、网络、模型或 `/embeddings` 不可用 | 回答/检索质量下降 | 本地来源回答和 hashing-96 回退；UI/接口返回 provider 与 warning |
| R-07 | 可选向量/rerank 依赖不可用 | Qdrant 或 Cross-Encoder 依赖缺失/失败 | 大库性能或排序质量下降 | SQLite 兼容副本继续可用；rerank_score 允许为空 |
| R-08 | PDF 解析依赖缺失 | 未安装 `pymupdf` | PDF 被跳过 | 返回明确跳过原因，其他文件继续导入 |
| R-09 | 项目覆盖被误解为职业能力 | 把项目内评估直接外推 | 学习判断失真 | UI/文档持续标注“当前项目、当前来源版本” |
| R-10 | 仓库公开但无许可证 | 外部使用者把公开可读误解为已授权 | 法律和贡献边界不清 | README/许可证指南明确未授权状态；由所有者单独决定并落地 LICENSE |

## 2. Obsidian 与来源一致性

| 风险 | 触发条件 | 影响 | 已落地约束 |
|------|----------|------|------------|
| 连接令牌泄露 | 日志、URL 或明文共享 | 未授权同步/发布 | 令牌走 Bearer header、仅 loopback、可撤销 |
| 同步重放 | 离线重试或重复事件 | 重复索引/删除 | 稳定 event_id、批量重放、幂等结果 |
| 反馈循环 | 插件生成目录再次被摄入 | 无限同步或重复资料 | 排除托管输出根 |
| 路径越界 | 绝对路径、`../` 或错误 output root | 用户文件风险 | 规范化、根目录包含校验、只允许 Markdown |
| 覆盖用户笔记 | 文件被外部修改或不是受管文件 | 数据丢失 | managed metadata + revision + hash；冲突只回报不覆盖 |
| 状态误读 | `queued` 被当作 `applied` | 后端/Vault 状态不一致 | 不可变发布修订，插件回报后才进入终态 |
| 来源陈旧 | 文档新增、修改、重命名或删除 | 分析和计划依据失真 | fingerprint 传播 `stale`，重新分析前不称最新 |

## 3. 发布与运维边界

- `v2.0.0` Tag、GitHub Release 和未签名 Windows NSIS 是历史已完成事实。
- macOS/Linux 历史构建或静态配置不替代当前 v2 原生产物。
- CI workflow 已配置不等于本次变更已通过；每次报告只引用当次真实命令/hosted job。
- Docker `/api/health` 只用于活性；备份、恢复、模型、向量和插件需独立验收。
- 当前没有正式值班、监控、Sentry、外部 SLA 或合规认证，不在模板中虚构。

## 4. 优先级

1. 数据污染、备份遗漏、Vault 越界/覆盖和未授权发布为 P0。
2. Tauri 主流程不可达、可见 UI 操作失败和来源陈旧为 P1。
3. 模型/向量降级、可选解析、性能和术语漂移为 P2。
4. 许可证、私密安全渠道和维护者继任属于治理门禁；对外扩大使用/贡献前必须有明确结论。

新风险进入 `docs/BACKLOG.md § 6`；重大技术取舍再创建 ADR。
