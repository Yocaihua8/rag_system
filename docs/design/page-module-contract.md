# 页面模块契约

> 状态：Draft
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：{{PAGE_OR_FLOW}}
> Related：`ui-wireframes.md`、`component-api-contract.md`、{{RELATED_DOCS}}

本文档用于多人并行开发同一个页面前，先冻结页面模块顺序、文件边界、命名边界和验收口径。它适合首页改版、页面复刻、活动页、工作台首页等高冲突场景。

## 1. 基本信息

| 项 | 内容 |
|----|------|
| 页面名称 | {{PAGE_NAME}} |
| 路由 / 入口 | `{{ROUTE_OR_ENTRY}}` |
| 页面编排文件 | `{{PAGE_COMPOSITION_FILE}}` |
| 集成负责人 | {{INTEGRATION_OWNER}} |
| 页面验收负责人 | {{ACCEPTANCE_OWNER}} |
| 视觉稿 / 参考链接 | {{DESIGN_REFERENCE}} |
| 关联线框图 | `ui-wireframes.md#{{ANCHOR}}` |

## 2. 页面模块顺序

页面模块顺序由集成负责人维护。模块负责人只能修改自己负责的模块文件，不直接调整页面编排顺序。

| 顺序 | 模块标识 | 页面区域 | 对应组件 | 模块负责人 | 是否必需 | 验收点 |
|------|----------|----------|----------|------------|----------|--------|
| 1 | `{{MODULE_KEY}}` | {{PAGE_AREA}} | `{{COMPONENT_PATH}}` | RAG 团队 | 是 / 否 | {{ACCEPTANCE_POINT}} |
| 2 | `{{MODULE_KEY}}` | {{PAGE_AREA}} | `{{COMPONENT_PATH}}` | RAG 团队 | 是 / 否 | {{ACCEPTANCE_POINT}} |

## 3. `data-*` 标识命名

`data-*` 用于自动化测试、截图定位和冲突排查，不能随意重命名。

| 类型 | 命名规则 | 示例 | 说明 |
|------|----------|------|------|
| 页面容器 | `data-page="{{PAGE_KEY}}"` | `data-page="home"` | 每个页面唯一 |
| 模块容器 | `data-{{PAGE_KEY}}-panel="{{MODULE_KEY}}"` | `data-home-panel="banner"` | 每个模块唯一 |
| 关键动作 | `data-action="{{ACTION_KEY}}"` | `data-action="open-service"` | 与按钮/交互绑定 |
| 列表项 | `data-item="{{ITEM_KEY}}"` | `data-item="service-card"` | 仅用于稳定定位 |

新增或修改 `data-*` 前必须同步本表，并更新对应测试。

## 4. 模块对应组件

| 模块标识 | 组件路径 | 组件 API 契约 | 样式入口 | 测试文件 | mock 数据 |
|----------|----------|---------------|----------|----------|-----------|
| `{{MODULE_KEY}}` | `{{COMPONENT_PATH}}` | `component-api-contract.md#{{ANCHOR}}` | `{{STYLE_PATH}}` | `{{TEST_PATH}}` | `{{MOCK_PATH_OR_NA}}` |

若同名组件可能被实现成不同职责（例如单卡片 vs 列表容器），必须先在组件 API 契约中明确职责，再开始编码。

## 5. 文件修改边界

### 5.1 模块负责人允许修改文件

| 负责人 | 允许修改文件 | 禁止修改文件 | 说明 |
|--------|--------------|--------------|------|
| RAG 团队 | `{{COMPONENT_FILE}}`、`{{COMPONENT_TEST}}`、`{{MODULE_STYLE}}` | `{{PAGE_COMPOSITION_FILE}}`、`{{GLOBAL_STYLE_FILE}}` | {{NOTE}} |

### 5.2 集成负责人专属文件

以下文件只能由集成负责人修改，其他成员如需调整必须先在 PR 中说明原因：

| 文件 | 负责人 | 可修改内容 | 禁止事项 |
|------|--------|------------|----------|
| `{{PAGE_COMPOSITION_FILE}}` | {{INTEGRATION_OWNER}} | 页面模块顺序、统一 props 传递、页面级状态 | 不直接写模块内部业务逻辑 |
| `{{PAGE_TEST_FILE}}` | {{INTEGRATION_OWNER}} | 页面级验收测试口径、模块顺序断言 | 不替模块负责人补业务测试 |
| `{{GLOBAL_STYLE_FILE}}` | {{INTEGRATION_OWNER}} | 设计 token、reset、全局变量 | 不写模块私有样式 |

## 6. 命名与样式边界

| 类别 | 规则 | 禁止 |
|------|------|------|
| 模块名 | 使用稳定业务语义，统一 kebab-case | 同一模块多套名字 |
| CSS class | 模块私有样式使用 `{{PAGE_KEY}}-{{MODULE_KEY}}-*` 前缀 | 无前缀类名、覆盖其他模块样式 |
| 公共样式 | 默认不修改 `{{GLOBAL_STYLE_FILE}}`，确需修改时由集成负责人评审 | 为单个模块改全局样式 |
| 测试命名 | 页面测试只验证模块顺序、关键入口和验收口径 | 用页面测试覆盖每个组件内部实现 |

## 7. 页面验收测试口径

页面验收测试口径必须由团队共享，不能变成每个成员各写一套验收标准。

| 验收项 | 验证方式 | 负责人 | 最低通过标准 |
|--------|----------|--------|--------------|
| 模块顺序 | `{{PAGE_TEST_COMMAND}}` | {{INTEGRATION_OWNER}} | 顺序与 § 2 一致 |
| `data-*` 标识 | `{{PAGE_TEST_COMMAND}}` | {{INTEGRATION_OWNER}} | 页面和模块标识均存在 |
| 视觉主路径 | 截图 / 人工验收 | {{ACCEPTANCE_OWNER}} | 与参考图主结构一致 |
| 响应式断点 | `{{RESPONSIVE_CHECK}}` | {{ACCEPTANCE_OWNER}} | 移动端和桌面端不重叠 |
| 回归测试 | `{{TEST_COMMAND}}` | RAG 团队 | 页面级测试通过 |

## 8. AI 编程边界

- AI 只能在本契约列出的允许修改文件内工作。
- AI 不得擅自新增模块名、`data-*`、CSS class 前缀或组件职责。
- AI 不得把模块私有样式写入公共样式文件。
- AI 不得把页面编排文件改成模块内部实现文件。
- 若任务需要越过文件边界，必须先更新本契约并在 PR 中说明。

## 9. 提交前检查清单

- [ ] 页面模块顺序与 § 2 一致
- [ ] 新增 / 修改的 `data-*` 已写入 § 3
- [ ] 每个模块对应组件已写入 § 4
- [ ] 本次修改未越过 § 5 文件边界
- [ ] 未直接修改公共样式，或已由集成负责人确认
- [ ] 页面验收测试口径已同步到测试文件
- [ ] PR 已附关键截图或说明截图不适用的原因

---

## 附录：填写示例

下方为首页复刻的简化示例。复制模板时请删除本附录。

```markdown
## 2. 页面模块顺序

| 顺序 | 模块标识 | 页面区域 | 对应组件 | 模块负责人 | 是否必需 | 验收点 |
|------|----------|----------|----------|------------|----------|--------|
| 1 | `banner` | 顶部主视觉 | `src/components/home/HomeBanner.vue` | 张三 | 是 | 首屏展示主标题和行动按钮 |
| 2 | `service-list` | 服务入口 | `src/components/home/ServiceList.vue` | 李四 | 是 | 至少展示 4 个服务入口 |

## 5.2 集成负责人专属文件

| 文件 | 负责人 | 可修改内容 | 禁止事项 |
|------|--------|------------|----------|
| `src/views/HomeView.vue` | 王五 | 页面模块顺序和页面级数据下发 | 不直接改服务卡片内部布局 |
| `src/views/HomeView.spec.ts` | 王五 | 页面模块顺序断言 | 不替各组件补组件级断言 |
| `src/styles/global.scss` | 王五 | 全局 token | 不写 `.service-card` 私有样式 |
```
