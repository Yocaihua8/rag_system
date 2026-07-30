# 组件 API 契约

> 状态：Draft
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：{{COMPONENT_OR_MODULE}}
> Related：`page-module-contract.md`、{{RELATED_DOCS}}

本文档用于冻结组件职责和对外 API，避免多人或 AI 把同名组件实现成不同职责。它适合可复用组件、页面模块组件、列表项、卡片、弹窗和表单组件。

## 1. 组件职责

| 项 | 内容 |
|----|------|
| 组件名称 | `{{COMPONENT_NAME}}` |
| 文件路径 | `{{COMPONENT_PATH}}` |
| 所属页面 / 模块 | {{PAGE_OR_MODULE}} |
| 组件类型 | 单组件 / 列表容器 / 页面模块 / 表单 / 弹窗 |
| 主要职责 | {{PRIMARY_RESPONSIBILITY}} |
| 不负责 | {{OUT_OF_SCOPE}} |
| 默认负责人 | RAG 团队 |

同名组件只能有一个职责定义。若需要列表容器和单卡片，应拆成两个组件名，例如 `ServiceList` 与 `ServiceCard`。

## 2. props

| prop | 类型 | 必填 | 默认值 | 来源 | 说明 |
|------|------|------|--------|------|------|
| `{{PROP_NAME}}` | `{{TYPE}}` | 是 / 否 | {{DEFAULT_OR_NA}} | {{SOURCE}} | {{DESCRIPTION}} |

规则：

- 新增、删除或重命名 props 前，必须更新本表和调用方。
- props 只描述输入，不承载组件内部状态机。
- 禁止 AI 为了当前页面临时追加未评审 props。

## 3. emits

| 事件名 | 触发时机 | payload 类型 | 使用方 | 说明 |
|--------|----------|--------------|--------|------|
| `{{EVENT_NAME}}` | {{WHEN}} | `{{PAYLOAD_TYPE}}` | {{CONSUMER}} | {{DESCRIPTION}} |

规则：

- emits 必须语义稳定，避免 `change`、`click` 这类无法说明业务意图的事件名。
- payload 字段变更视为组件 API 变更，必须同步测试和 PR 说明。

## 4. slots

| slot | 作用 | 默认内容 | 允许内容 | 禁止内容 |
|------|------|----------|----------|----------|
| `{{SLOT_NAME}}` | {{PURPOSE}} | {{DEFAULT_CONTENT_OR_NA}} | {{ALLOWED_CONTENT}} | {{FORBIDDEN_CONTENT}} |

无 slots 时填 `N/A`，不要留空。

## 5. CSS class 前缀

| 类别 | 前缀 / 命名 | 示例 | 说明 |
|------|-------------|------|------|
| 根节点 | `{{COMPONENT_PREFIX}}` | `.service-card` | 组件唯一根类 |
| 子元素 | `{{COMPONENT_PREFIX}}__{{ELEMENT}}` | `.service-card__title` | 组件内部元素 |
| 状态 | `{{COMPONENT_PREFIX}}--{{STATE}}` | `.service-card--active` | 视觉状态 |
| 测试定位 | `data-testid="{{TEST_ID}}"` 或项目约定 | `data-testid="service-card"` | 稳定测试定位 |

组件私有样式应放在 `{{STYLE_PATH}}` 或组件局部样式中。禁止为了单个组件修改公共样式文件。

## 6. mock 数据依赖

| 数据项 | mock 文件 | 真实来源 | 是否允许组件内兜底 | 说明 |
|--------|-----------|----------|--------------------|------|
| {{DATA_NAME}} | `{{MOCK_PATH_OR_NA}}` | {{REAL_SOURCE}} | 是 / 否 | {{DESCRIPTION}} |

规则：

- mock 数据只用于开发、测试或 story，不作为真实业务默认值。
- 组件不得把 mock 数据写死在模板里。
- mock 字段变更必须同步 props、测试和相关页面契约。

## 7. 测试要求

| 测试类型 | 文件 | 必测内容 | 命令 |
|----------|------|----------|------|
| 组件单测 | `{{COMPONENT_TEST_PATH}}` | props 渲染、emits、边界状态 | `{{TEST_COMMAND}}` |
| 页面集成 | `{{PAGE_TEST_PATH}}` | 页面是否正确装配该组件 | `{{PAGE_TEST_COMMAND}}` |
| 视觉验收 | {{SCREENSHOT_OR_STORY}} | 主状态截图 | {{VISUAL_CHECK_COMMAND_OR_MANUAL}} |

最低要求：

- props 的必填 / 默认值至少覆盖一条测试。
- 每个 emits 至少有一条触发测试。
- 空状态、加载状态、错误状态按组件职责覆盖。

## 8. 禁止 AI 擅自改变的接口

以下变更必须先更新本契约并获得 Reviewer 确认：

- 重命名组件文件或默认导出名。
- 把单卡片组件改成列表容器，或把列表容器改成单卡片。
- 新增、删除、重命名 props。
- 修改 emits 名称或 payload 结构。
- 修改 slots 名称或语义。
- 修改 CSS class 前缀或删除测试依赖的 `data-*` / `data-testid`。
- 引入真实 API 请求、全局状态或公共样式耦合。

## 9. 提交前检查清单

- [ ] 组件职责与 § 1 一致
- [ ] props / emits / slots 变更已同步本契约
- [ ] CSS class 前缀未污染其他组件
- [ ] mock 数据没有替代真实数据流
- [ ] 测试覆盖组件 API 的主路径和边界状态
- [ ] PR 已说明是否修改组件 API

---

## 附录：填写示例

下方为服务卡片组件的简化示例。复制模板时请删除本附录。

```markdown
## 1. 组件职责

| 项 | 内容 |
|----|------|
| 组件名称 | `ServiceCard` |
| 组件类型 | 单组件 |
| 主要职责 | 展示一个服务入口，包括图标、名称、描述和点击事件 |
| 不负责 | 不负责轮播、分页或接口请求 |

## 2. props

| prop | 类型 | 必填 | 默认值 | 来源 | 说明 |
|------|------|------|--------|------|------|
| `service` | `ServiceCardItem` | 是 | N/A | 父组件传入 | 单个服务入口数据 |

## 3. emits

| 事件名 | 触发时机 | payload 类型 | 使用方 | 说明 |
|--------|----------|--------------|--------|------|
| `select` | 用户点击卡片 | `{ id: string }` | 页面模块 | 通知父组件选择服务 |
```
