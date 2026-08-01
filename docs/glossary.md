# Knowledge Island 术语表
> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-08-01
> Scope：当前 UI、HTTP API、SQLite、教练评估、Tauri 与 Obsidian 桥的统一词汇
> Related：`requirements/project-background-and-scope.md`、`design/api-spec.md`、`design/database-design.md`

同一概念在界面、接口、代码和文档中应使用一致名称。历史材料可以保留当时用词，但当前入口应链接本表说明兼容关系。

## 1. 产品与界面

| 术语 | 代码/缩写 | 定义 | 使用示例 |
|------|-----------|------|----------|
| Knowledge Island | KI | 当前本地项目知识教练产品 | `v2.0.0` |
| 教练 | `coach` | 当前问答工作台，围绕所选项目和真实来源建立项目理解 | 一级入口“教练” |
| 学习地图 | `learning-map` | 展示项目分析、知识点、技能映射、覆盖和评估记录 | Vue `LearningMapView` |
| 学习计划 | `learning-plan` | 可生成、编辑、确认和跟踪的项目学习任务版本 | Vue `LearningPlanView` |
| 资料 | Library | 当前通过模态框进入的项目文档与导入入口 | `LibraryModal` |
| 设置 | `settings` | 模型、Prompt、Obsidian 配对和高级选项入口 | Vue `SettingsView` |

## 2. 领域与数据

| 术语 | 代码/缩写 | 定义 | 权威位置 |
|------|-----------|------|----------|
| 项目 / 工作区 | `project`, `project_id` | 资料、聊天、分析和学习进度的隔离边界；UI 可称工作区，持久层统一使用 project | `design/database-design.md` |
| 文档 | `document` | 已导入项目的一份来源记录，不等同于磁盘文件本身 | `documents` 表 |
| 文档集合 | `collection` | 项目内文档的轻量分组；删除集合不删除文档 | `document_collections` |
| 分块 | chunk | 从文档正文切出的检索单位 | `document_chunks` |
| 来源 | source | 支撑回答、分析、评估或计划结论的文档/分块定位 | API `sources` |
| 导入批次 | import batch | 一次导入的来源类型、状态、统计、跳过和错误摘要 | `import_batches` |
| 模型 Profile | model profile | LLM provider、地址、模型、生成参数和 Key 引用的组合 | `model_profiles` |
| Prompt 预设 | prompt preset | 项目级回答风格和任务说明；不能覆盖固定来源约束 | `prompt_presets` |
| 数据代际 | data generation | 用 `app_metadata.data_generation` 标识的运行库代际；当前正式 Web 要求 `v2` | `runtime/v2/app.db` |

## 3. 教练与评估

| 术语 | 代码/缩写 | 定义 | 边界 |
|------|-----------|------|------|
| 项目分析 | project analysis | 基于当前项目来源生成概览、知识点和技能映射 | 规则基线为 `rules-v1`，LLM 只做可选增强 |
| 项目知识点 | knowledge point | 可由来源定位和解释的项目内概念、流程或代码位置 | 不代表通用技能等级 |
| 通用技能 | skill | 从项目知识点聚合出的语言、框架、数据、测试等技能维度 | 只解释当前项目差距 |
| 项目覆盖 | coverage | 当前来源和评估对项目知识点的覆盖结果 | 不等同职业能力 |
| 陈旧 | `stale` | 来源 fingerprint 变化后，旧分析不再是当前结果 | 需重新分析 |
| 教练评估 | coach assessment | 面向知识点或技能、受来源约束的定向评估 | 与兼容 `/api/assessment/*` 分开 |
| 学习计划版本 | learning plan version | 可编辑、确认并保留历史来源的任务集合 | 确认后才可预览发布 |

## 4. 运行与集成

| 术语 | 代码/缩写 | 定义 | 边界 |
|------|-----------|------|------|
| 本地回答 | `local` | 没有可用模型时，由来源片段组合的回答 | 不是远程 LLM |
| 模型回答 | `api` | Ollama 或 OpenAI-compatible 模型成功生成的回答 | 必须保留来源约束 |
| 回退回答 | `fallback` | 模型调用失败后使用本地组合并带 warning | 不得伪装为模型成功 |
| Tauri sidecar | sidecar | 桌面壳启动的 `knowledge-island-backend` 后端进程 | 桌面壳本身不承载业务命令 |
| Obsidian 连接 | connection | 插件配对后保存的项目、连接令牌和输出根关系 | 令牌仅用于插件 API |
| 发布 | publication | 主应用预览并确认、插件拉取后执行的受管 Markdown 写入 | `queued` 不等于 `applied` |
| 托管文件 | managed file | 含稳定系统标记、revision 和 hash 的插件输出文件 | 冲突时不覆盖 |

## 5. 兼容和废弃用词

| 旧用词 | 当前用词 | 生效日期 | 说明 |
|--------|----------|----------|------|
| “当前 1.x / 2.0 目标” | “当前 v2.0.0 / 1.x 兼容基线” | 2026-07-30 | v2.0.0 已发布，不再作为未来目标描述 |
| 项目空间 | 项目 / 工作区 | 2026-07-30 | `project_id` 是内部稳定边界，UI 可使用“工作区” |
| 聊 / 库 / 设 | 教练 / 学习地图 / 学习计划 / 资料 / 设置 | 2026-07-30 | 当前一级入口已切换 |
| PySide6 桌面端 | legacy 桌面实现 | 2026-05-26 | 已归档，不是当前入口 |
| “Obsidian 双向同步” | 增量来源同步 + 受控发布 | 2026-07-23 | 两条链路权限和状态不同，不能用一个模糊词概括 |
