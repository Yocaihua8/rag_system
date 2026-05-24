# Web 项目级 Prompt 设置设计

> 状态：Design
> Owner：RAG 团队
> Last Updated：2026-05-24
> Scope：B-109，仅设计项目级 Prompt / 助手预设的数据结构和问答注入边界；本文件不代表已建表或已实现 UI。

## 1. 背景

当前 Web MVP 的 `/api/answer` 已支持项目资料检索、当前会话最近 3 轮上下文、工具来源回填、项目级检索默认值和回答可观察性。真实 LLM prompt 由来源片段、最近对话和当前问题组成，用户暂时不能为不同问答场景设置回答风格或任务边界。

Cherry Studio、AnythingLLM 这类工具通常支持助手预设或系统提示词。知识岛当前是本地个人应用，不需要做复杂 Prompt 市场或多用户助手管理，但需要一个可控的项目级 Prompt 设置，用于区分“项目问答”“代码解释”“学习复盘”等常见场景。

B-109 的目标是先设计数据结构和注入边界，不直接建表。实际落地应由 B-110 执行。

## 2. 设计目标

- 支持每个项目空间保存多个 Prompt 预设。
- 支持选择一个当前默认 Prompt 预设，用于后续 `/api/answer`。
- 预设只影响回答风格、回答结构和任务说明，不允许绕过来源片段约束。
- 预设不保存 API Key、模型配置或外部服务凭证。
- 预设不触发工具自动执行，不扩大 Agent 工具权限。
- 兼容当前默认行为：未选择预设时继续使用现有 prompt 逻辑。

## 3. 非目标

- 不做 Prompt 市场、共享、导入第三方助手或云同步。
- 不做多模型 Profile；这属于 B-111/B-112。
- 不做复杂变量模板引擎；第一片只支持少量受控变量。
- 不让 Prompt 预设改变检索参数；检索参数继续由 B-105 的项目级默认值负责。
- 不让 Prompt 预设改变工具执行权限；工具仍由用户手动运行。
- B-109 不建表、不改接口、不改 prompt 注入代码。

## 4. 数据模型建议

后续 B-110 可新增 `prompt_presets` 表：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT PRIMARY KEY | Prompt 预设 ID |
| `project_id` | TEXT NOT NULL | 所属项目空间 |
| `name` | TEXT NOT NULL | 预设名称，例如“项目问答” |
| `description` | TEXT NOT NULL DEFAULT '' | 简短说明 |
| `system_prompt` | TEXT NOT NULL | 系统/助手行为说明 |
| `answer_format` | TEXT NOT NULL DEFAULT '' | 可选回答结构要求 |
| `created_at` | TEXT NOT NULL | 创建时间 |
| `updated_at` | TEXT NOT NULL | 更新时间 |

后续可在 `projects` 表增加可空字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `default_prompt_preset_id` | TEXT NULL | 当前项目默认 Prompt 预设 |

约束建议：

- `prompt_presets.project_id` 外键指向 `projects.id`，删除项目时级联清理。
- `projects.default_prompt_preset_id` 可为空；为空时使用现有默认 prompt。
- 后端保存时限制 `system_prompt` 和 `answer_format` 长度，避免 prompt 无限膨胀。
- 预设名称在同项目内建议唯一，但第一片可只做前端提示，不强制复杂去重。

## 5. 内置预设建议

B-110 第一片可提供 3 个本地默认预设模板，用户可复制后编辑：

| 名称 | 用途 | 边界 |
|------|------|------|
| 项目问答 | 回答“这个项目是什么、怎么运行、接口在哪里” | 强调引用来源，资料不足时说明缺口 |
| 代码解释 | 解释文件、函数、模块职责 | 要求指出文件路径和依据片段，不臆测未检索到的代码 |
| 学习复盘 | 把项目内容转成学习提纲和检查点 | 不替代掌握评估，不生成无来源结论 |

这些模板应存放在代码常量或文档中，B-110 可以在项目首次打开 Prompt 设置页时展示，不需要预先写入数据库。

## 6. Prompt 注入边界

后续 `/api/answer` 的 prompt 构造建议分层：

1. 固定安全边界：只能基于已检索来源回答；资料不足必须说明不足；不能伪造来源。
2. 项目级 Prompt 预设：当前选中预设的 `system_prompt` 和 `answer_format`。
3. 当前会话最近 3 轮上下文：沿用 B-108 的 `session_id` 范围。
4. 本轮来源片段：沿用当前 RAG 命中结果和工具回填来源。
5. 当前问题。

优先级建议：

- 固定安全边界优先级最高，用户 Prompt 不能覆盖。
- 用户 Prompt 可以要求更详细、更简洁、用步骤化结构回答。
- 用户 Prompt 不可以要求忽略来源、编造结论、自动运行工具或泄露配置。
- 如果用户 Prompt 与固定边界冲突，后端仍应保留固定边界。

## 7. API 设计建议

B-110 第一片建议新增以下接口：

| 方法 | 路径 | 请求 | 成功响应 | 说明 |
|------|------|------|----------|------|
| GET | `/api/prompt-presets?project_id=...` | query `project_id` | `{"presets":[...],"default_preset_id":"..."}` | 列出当前项目预设 |
| POST | `/api/prompt-presets` | `project_id`、`name`、`description`、`system_prompt`、`answer_format` | `{"preset":...}` | 新增预设 |
| POST | `/api/prompt-presets/update` | `preset_id`、字段 | `{"preset":...}` | 更新预设 |
| POST | `/api/prompt-presets/delete` | `preset_id` | `{"deleted":true,"presets":[...]}` | 删除预设 |
| POST | `/api/prompt-presets/default` | `project_id`、`preset_id`（可空） | `{"default_preset_id":"..."}` | 设置或清空默认预设 |

错误边界：

- 缺少 `project_id` 返回 `400 project_id is required`。
- 项目不存在返回 `404 project not found`。
- 预设不存在或不属于项目返回 `404 prompt preset not found`。
- `name` 或 `system_prompt` 为空返回 `400 name is required` / `400 system_prompt is required`。

## 8. 前端交互建议

B-110 第一片建议在设置页或工作台侧边区域增加“Prompt 预设”小节：

- 列出当前项目预设。
- 支持新增、编辑、删除。
- 支持选择默认预设和清空默认预设。
- 展示内置模板入口：“复制项目问答 / 代码解释 / 学习复盘模板”。
- 提问区只展示当前默认预设名称，不提供复杂编辑器。

第一片不建议做富文本编辑、变量自动补全、Prompt 调试运行记录、版本历史或导入导出。

## 9. 与现有能力的关系

- 与 B-105 项目级检索默认值：Prompt 不改变检索参数。
- 与 B-108 多会话：Prompt 默认值按项目保存，不随会话变化；后续可设计会话级覆盖，但不进入第一片。
- 与 Agent 工具：Prompt 不能自动运行工具，只能建议用户手动运行现有只读工具。
- 与回答反馈：反馈记录不直接改 Prompt；后续可以人工复盘后调整预设。
- 与备份导出：如果后续导出 Prompt 预设，不应包含 API Key 或模型凭证。

## 10. 测试建议

B-110 实现时至少覆盖：

- Prompt 预设新增、列表、更新、删除。
- 默认预设设置和清空。
- 跨项目预设访问返回 404。
- `/api/answer` 使用当前项目默认预设，且未选预设时保持现有行为。
- 固定来源约束仍出现在最终 prompt 中，用户预设不能覆盖。
- 前端能创建、编辑、删除、选择默认预设。
- 文档契约覆盖接口、数据库字段和“不保存 API Key”的边界。

## 11. 风险

- 如果把用户 Prompt 直接放在最高优先级，可能削弱来源约束，导致模型编造。
- 如果第一片做复杂模板变量，会扩大实现范围并增加 prompt 注入风险。
- 如果 Prompt 默认值按会话保存，会和 B-108 的会话模型耦合过深，建议后续再设计。
- 如果把 Prompt 设置和模型 Profile 混在一起，容易误保存敏感配置；应保持边界分离。
