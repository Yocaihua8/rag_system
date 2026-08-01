# 风险登记
> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：Knowledge Island v2.0.0 当前实现、运行、数据、桌面、插件和治理风险
> Related：`architecture-overview.md`、`permission-matrix.md`、`../BACKLOG.md`、`../adr/ADR-008-project-knowledge-coach-v2.md`、`../adr/ADR-009-obsidian-plugin-bridge.md`

## 1. 当前活动风险

| ID | 风险 | 触发条件 | 影响 | 当前缓解 / 下一门禁 |
|----|------|----------|------|---------------------|
| R-01 | v2 备份范围不完整 | 自定义 `RAG_RUNTIME_DIR` 或 Qdrant local mode 未向独立脚本传入对应路径 | SQLite、导出文件或外部向量数据被遗漏；文件复制回退可能不一致 | 默认数据库路径已对齐并通过隔离恢复测试；自定义 DB/Qdrant 显式传路径，缺少 `sqlite3` 时先停机，导出文件单独纳入备份 |
| R-02 | Tauri API 连通性未动态覆盖 | 已配置绝对 8765 API URL、CORS 与 CSP，但安装后主流程尚未成为自动门禁 | 安装包启动但业务不可用 | 静态打包证据不作为动态证明；真实安装包主流程作为发布门禁 |
| R-03 | 可见 UI 与端到端能力不一致 | 未接线控件、参数不完整或未挂载 view 被当作已交付 | 用户操作失败、文档夸大 | 契约对照列出差距；未接线项进入 BACKLOG，完成后增加交互/E2E |
| R-04 | 健康检查过浅 | `/api/health` 返回 ok，但 SQLite/模型/向量不可用 | 运维误判可用性 | 文档称“活性检查”；发布/运维另做读写和主流程验证 |
| R-05 | 数据代际保护并非所有脚本共有 | 通过未传 `expected_generation="v2"` 的维护脚本初始化存储 | 旧库被误识别或写入 | 只对正式 Web 链路声明已保护；脚本入口单独审计和测试 |
| R-06 | 外部模型/Embedding 质量与可用性 | Key、网络、模型或 `/embeddings` 不可用 | 回答/检索质量下降 | 本地来源回答和 hashing-96 回退；UI/接口返回 provider 与 warning |
| R-07 | 可选向量/rerank 依赖不可用 | Qdrant 或 Cross-Encoder 依赖缺失/失败 | 大库性能或排序质量下降 | SQLite 兼容副本继续可用；rerank_score 允许为空 |
| R-08 | PDF 解析依赖缺失 | 未安装 `pymupdf` | PDF 被跳过 | 返回明确跳过原因，其他文件继续导入 |
| R-09 | 项目覆盖被误解为职业能力 | 把项目内评估直接外推 | 学习判断失真 | UI/文档持续标注“当前项目、当前来源版本” |
| R-10 | 后端认证与 Vue/SSE 未接凭证 | 启用 `RAG_AUTH_ENABLED=1` 后直接使用当前页面 | JSON 与问答 SSE 返回 401，主流程不可用 | 当前只承诺本地认证关闭模式；远程使用前补完整凭证链并验证 EventSource |
| R-11 | 兼容全局设置在磁盘保存 Key 明文 | 用户通过 `/api/settings/llm` 提交 API Key | 用户应用数据 `.env` 或备份泄露凭证 | 限制文件权限和备份范围；区分 Profile 引用与兼容明文保存 |
| R-12 | 仓库公开但无许可证 | 外部使用者把公开可读误解为已授权 | 法律和贡献边界不清 | README/许可证指南明确未授权状态；由所有者单独决定并落地 LICENSE |

## 2. Obsidian 与来源一致性

| 风险 | 触发条件 | 影响 | 已落地约束 |
|------|----------|------|------------|
| 连接令牌泄露 | Vault 插件 `data.json`、日志、URL 或明文共享 | 未授权同步/发布 | 令牌走 Bearer header、仅 loopback、可撤销；依赖 Vault 文件权限保护 |
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

新风险进入 [`../BACKLOG.md`](../BACKLOG.md)；重大技术取舍再创建 ADR。
