# Obsidian 同步与受控发布

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：Vault 一次性导入、桌面插件增量同步与确认后发布
> Related：`project-space-ingestion.md`、`project-knowledge-coach.md`、`../design/api-spec.md`、`../guides/setup.md`、`../guides/security.md`

## 1. 两种用户流程

| 流程 | 当前入口 | 边界 |
|------|----------|------|
| 一次性只读导入 | 资料弹窗输入 Vault 路径 | 递归读取 Markdown/文本并跳过 `.obsidian` 等目录；不会建立连接或写回 |
| 桌面插件连接 | 设置页生成配对码，Obsidian 插件完成配对 | 增量同步 Vault 事件，并在用户确认后执行系统管理内容发布 |

Notion Markdown ZIP 的后端导入能力仍存在，但当前资料弹窗只显示“稍后支持”，因此不属于当前可达流程。

## 2. 配对与同步

- 每个项目最多一个活动连接；一次性配对码默认五分钟过期。
- 服务端只保存配对码和插件令牌的 SHA-256 哈希；明文令牌只在换取时返回一次。
- 插件在自己的 Vault 配置 `data.json` 中保存明文令牌以便离线恢复，需依赖本机 Vault 文件权限保护。
- 插件发送 `upsert`、`rename`、`delete` 事件；`event_id` 在连接内幂等，离线事件可在恢复连接后重放。
- Frontmatter、标签和 Wikilink 元数据可随事件发送；系统输出目录不反向摄入。

## 3. 受控发布

1. Web 端生成 Markdown 内容和目标路径预览。
2. 用户确认后发布进入 `queued`，不表示已经写入 Vault。
3. 插件领取任务，校验路径、系统管理标记、修订号和预期哈希后写入，再回传 `applied`、`conflict` 或 `failed`。

默认输出目录为 `Knowledge Island/<项目名>/`。可发布项目理解、知识覆盖与技能差距、学习计划和评估记录。无管理标记的同名文件、身份不符、用户外部编辑或越界路径一律停止覆盖；当前不自动合并冲突。

## 4. 当前可达与限制

- 资料弹窗展示连接状态；设置页可创建配对码、查看或撤销连接；学习计划页可预览并确认发布。
- 浏览器不持有插件令牌，也不调用事件同步、待执行领取或结果回传接口。
- 插件是 desktop-only 集成，仅支持桌面 Obsidian，不支持移动端或社区市场自动发布。
- 后端不直接扫描或写入 Vault；用户删除生成文件后不会自动重建。
