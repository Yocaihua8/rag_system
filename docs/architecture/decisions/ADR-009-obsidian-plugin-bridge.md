# ADR-009 Obsidian 桌面插件桥与受控写回

> 状态：Accepted
> Date：2026-07-23
> Owner：RAG 团队
> Related：docs/integrations/obsidian.md, docs/architecture/overview.md, docs/architecture/backend/data.md, docs/architecture/backend/api.md, docs/BACKLOG.md

## 1. 背景

1.x 的 `/api/import/obsidian-vault` 是用户显式触发的一次性只读导入。2.0 需要接收 Vault 内 Markdown 的增量变化，并把项目理解、差距、学习计划和评估记录发布回 Obsidian。

由后端直接扫描或写入 Vault 会绕过 Obsidian 的文件事件、Frontmatter 和链接元数据，也难以可靠识别外部编辑与用户笔记。2.0 因此需要一个运行在 Obsidian 桌面端内的受控桥。该 ADR 冻结目标协议，不表示插件或接口已经实现。

## 2. 决策结论

### 2.1 桥接与配对

- 建立独立桌面插件工程；首版 `isDesktopOnly`，不支持移动端或社区市场发布。
- FastAPI 继续只监听 loopback。插件是 Vault 读取和写入的唯一执行方，后端不接收 Vault 根目录并直接访问文件系统。
- 每个 `project_id` 最多一个活动连接；已有活动连接时必须先显式撤销，不能静默替换。
- 主应用生成一次性限时配对码；插件用配对码换取随机连接令牌。配对码与令牌在服务端均只保存密码学哈希，明文只返回一次。
- 连接令牌只允许访问 `/api/obsidian/*` 且绑定项目与连接；不得访问通用管理或其他项目路由。

### 2.2 Vault 事件同步

- 插件在 `workspace.onLayoutReady()` 后通过 `registerEvent()` 订阅 Markdown `create / modify / rename / delete`，避免 Vault 初始化阶段的 `create` 事件风暴。
- 对后端统一发送 `upsert / rename / delete` 批量事件。每个事件包含连接内唯一 `event_id`、路径、旧路径（rename）、内容 hash、Frontmatter、标签及已解析/未解析 Wikilink；`upsert` 同时携带 Markdown 内容。
- 后端以 `(connection_id, event_id)` 幂等处理。重复事件返回第一次处理结果，不重复入库、改名或删除。
- 默认托管输出根为 `Knowledge Island/<项目名>/`，可在配对时修改。插件必须规范化用户路径，并将该根从反向摄入监听中排除。
- 来源重命名保留文档身份和来源映射；来源删除清理对应索引并使依赖分析进入 `stale`。

### 2.3 受控发布

发布状态统一为 `draft / confirmed / queued / applied / conflict / failed`，流程固定为：

1. 主应用请求预览，后端创建不可变发布修订，列出目标路径、内容、内容 hash 与预期 Vault hash。
2. 用户在主应用审阅内容和路径并显式确认；确认后进入 `queued`。
3. 插件轮询待执行修订，重新读取目标文件并校验路径、托管标记、稳定 ID 和当前 hash。
4. 插件使用 Obsidian Vault API 执行写入：后台正文变更使用 `Vault.process()`，Frontmatter 使用 `FileManager.processFrontMatter()`；单连接内按文件串行执行。
5. 插件回报每个修订的实际 hash 和结果；只有校验后的成功回报才能进入 `applied`。

默认输出：

- `项目理解.md`
- `知识覆盖与技能差距.md`
- `学习计划.md`
- `评估记录/<时间>.md`

所有可更新文件必须包含：

```yaml
knowledge_island_managed: true
knowledge_island_id: <stable-id>
knowledge_island_project_id: <project-id>
knowledge_island_artifact_type: <artifact-type>
knowledge_island_revision: <revision>
```

### 2.4 冲突与删除策略

- 目标路径必须是规范化的 Vault 相对路径，且仍位于连接的 `output_root` 内；绝对路径、`..` 越界或软链接逃逸必须拒绝。
- 新文件仅在目标不存在时创建。现有文件只有在托管标记为真、稳定 ID/项目 ID 匹配且当前 hash 等于预览记录时才能更新。
- 任一校验失败即返回 `conflict`，保留用户文件和不可变修订；首版不自动合并、不强制覆盖。
- 用户删除系统生成文件后，插件只回报删除，不自动重建。用户需在主应用重新预览并确认才能再次发布。
- 回滚通过选择历史不可变修订、生成新的预览/确认执行完成；不得改写历史修订。

### 2.5 官方 API 使用边界

- Vault 事件使用 `Plugin.registerEvent()` 管理生命周期：[Events](https://docs.obsidian.md/Plugins/Events)。
- 文件读写优先使用 Vault API；基于当前内容的后台修改使用 `Vault.process()`，避免陈旧读取覆盖：[Vault](https://docs.obsidian.md/Plugins/Vault)。
- Frontmatter 使用 `FileManager.processFrontMatter()`，用户路径使用 `normalizePath()`；不直接操作 `.obsidian` 或以 Node `fs` 绕过 Vault API：[Plugin guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)。

## 3. 备选方案

### 3.1 后端直接读写 Vault

- 优点：不需要插件。
- 缺点：绕过 Obsidian API，路径权限过大，无法可靠处理元数据、事件和并发编辑。
- 未采用原因：不满足受控写回和冲突保护。

### 3.2 只保留一次性导入

- 优点：边界最简单，不产生写回风险。
- 缺点：无法同步持续变化的笔记，也不能将确认后的学习产物发布回 Vault。
- 未采用原因：不能完成 2.0 学习闭环；该入口仍作为无插件 fallback 保留。

### 3.3 后端自动覆盖或自动合并

- 优点：流程更少。
- 缺点：可能破坏用户编辑；Markdown/Frontmatter 的语义合并不可稳定自动化。
- 未采用原因：本地个人数据安全优先，冲突必须由用户显式处理。

## 4. 影响

| 模块 | 目标影响 |
|------|----------|
| 插件 | 新增桌面插件工程、配对设置、事件队列、轮询和 Vault 写入 |
| 后端 | 新增 `/api/obsidian/*`、令牌校验、事件幂等和发布状态机 |
| 数据库 | 新增连接、事件、发布、不可变修订和执行结果实体 |
| Vue | 新增配对状态、输出目录、撤销连接、发布预览和冲突处理 |
| 现有导入 | `/api/import/obsidian-vault` 保持一次性只读语义 |

## 5. 风险与约束

- 令牌不得出现在日志、Frontmatter、Markdown、URL 查询参数或发布修订中。
- 托管输出根必须排除反向摄入，防止反馈循环。
- 插件离线时发布保持 `queued`，不得在未收到成功结果时显示为已应用。
- 插件只处理 Markdown；不删除或覆盖无托管标记的用户文件。
- 网络使用、读取范围和写入目录必须在插件 README/设置中明确披露。

## 6. 回滚策略

- 撤销连接令牌并禁用插件，停止新的事件同步和发布执行。
- 保留同步事件和不可变发布修订用于审计；不自动删除已写入 Vault 的 Markdown。
- 主应用继续提供现有一次性只读导入，不依赖插件即可使用基础资料导入。

## 7. 验证方式

- 验证配对码过期/复用、令牌哈希、撤销、路由范围和跨项目拒绝。
- 验证事件重复、离线重放、修改、重命名、删除、输出根排除与启动事件风暴保护。
- 验证新建、正常更新、未托管同名文件、稳定 ID 不符、外部编辑 hash 冲突、路径越界和插件离线。
- 验证预览、确认、排队、执行结果和历史修订回滚；失败/冲突不得改写用户文件。
- 使用独立测试 Vault 验证 `Vault.process()`、Frontmatter 更新和实际文件 hash，不在用户主 Vault 开发测试。
