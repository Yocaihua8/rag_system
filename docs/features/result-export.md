# 结果导出

> 状态：Draft
> Owner：RAG 团队
> Last Updated：2026-06-29
> Scope：B-07 生成结果导出为 Markdown / PDF
> Related：docs/design/api-spec.md, docs/BACKLOG.md

## 1. 功能定位

B-07 面向本地 Knowledge Island Web MVP 的问答结果归档场景，支持将已生成的回答结果导出到本地 `data/outputs/` 目录。

## 2. 待实现范围

- 支持 Markdown 与 PDF 两种导出格式。
- 导出内容来自已生成的问答消息，包含问题、回答和引用来源。
- 导出接口写入本地输出目录，并返回文件名、路径、格式、MIME 类型和文件大小。

## 3. 非目标

- 不新增数据库 schema。
- 不实现远程对象存储、邮件分享或云端同步。
- 不实现批量导出、导出历史列表或文件删除管理。
- 不引入大型 PDF 渲染依赖。
