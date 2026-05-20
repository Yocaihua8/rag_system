# 2026-05-20 本地 Web MVP 收口说明

> 目标：确认默认本地 Web MVP 可用于个人项目资料导入、检索、问答和来源查看
> Owner：RAG 团队
> 适用范围：`app.py` 启动的本机 Web 服务

## 1. 可交付范围

- 默认入口：运行 `app.py` 后启动 `http://127.0.0.1:8765`。
- 项目空间：创建、选择、改名、删除本地项目空间。
- 本地目录导入：导入 Markdown、TXT、代码与配置类文本文件。
- 导入保护：跳过常见依赖、缓存、版本库和本机工具配置目录；跳过超过 1MB 的单文件；读取失败单独展示错误。
- 增量导入：展示新增、更新、未变更、删除、跳过数量；源目录删除的文件会同步清理记录。
- 文档管理：查看已导入文件列表、路径过滤、数量提示、文件预览、移除单条文档记录。
- 检索问答：支持独立关键词检索；未配置模型时基于命中片段组合回答，配置 DeepSeek / OpenAI 兼容 API 后优先使用真实 LLM 并展示来源。
- 掌握评估：支持从已导入文件生成最小评估题，提交回答后给出规则化反馈和建议阅读来源。
- 首次引导：首页展示创建项目空间、导入目录、提问/评估、配置 DeepSeek 的最小步骤。
- 异常提示：无项目空间、目录不存在、空问题、空关键词、无文件、无来源等状态有明确提示。

## 2. 非承诺范围

- 不提供远程多用户部署和权限系统。
- 不承诺语义向量检索、Reranker 或云端 LLM 生成质量；真实 LLM 取决于用户配置的 API Key、网络和服务商状态。
- 发布脚本可生成 Windows 打包产物，但尚未完成安装器、桌面快捷方式或非技术用户一键安装流程。
- 不删除 legacy PySide6 桌面端代码；`src/desktop/` 仅作为迁移参考保留。

## 3. 验收命令

```powershell
.venv\Scripts\python.exe -m pytest tests\test_webapp -q
.venv\Scripts\python.exe -m pytest tests\test_domain tests\test_application tests\test_adapters -q
.venv\Scripts\python.exe scripts\check_docs_consistency.py
.venv\Scripts\python.exe -m compileall -q app.py webapp
node --check webapp\static\js\*.js
```

## 4. 浏览器验收清单

1. 启动 `app.py`，打开 `http://127.0.0.1:8765`。
2. 创建项目空间，路径填写一个真实存在的本地目录。
3. 点击“导入”，确认文件列表、导入统计、跳过详情和导入错误区域正常显示。
4. 点击文件列表中的文件，确认右侧文件预览显示正文。
5. 输入关键词并点击“搜索”，确认结果可点击并打开文件预览。
6. 输入问题并点击“提问”，确认回答、回答模式和来源列表同时出现。
7. 点击“开始评估”，确认生成题目；输入回答并提交，确认反馈、得分和建议阅读来源出现。
8. 删除或移动项目根目录后刷新页面，确认显示“目录不存在”，点击“导入”时前端直接阻止。

## 5. 当前风险

- 浏览器只能手动输入本地目录路径，尚未提供系统目录选择器。
- 未配置或无法访问 DeepSeek 时，问答会回退为关键词片段组合；复杂总结质量有限。
- 当前发布面向开发者或技术用户本机试用；Windows zip 产物需要实际打包验收后才能交给非技术用户。

## 6. Windows 打包验收记录

2026-05-20 已执行真实打包：

```powershell
.\scripts\release_windows.ps1 -SkipCheck -ZipOutput
```

结果：

- 产物目录：`release\dist\KnowledgeIsland`
- 启动入口：`release\dist\KnowledgeIsland\Run_KnowledgeIsland.bat`
- zip 包：`release\KnowledgeIsland_win64.zip`
- 打包后冒烟：运行 bat 后 `GET /api/health` 返回 `{"status":"ok"}`。
- 打包后功能冒烟：创建项目空间、导入 1 个文件、问答返回 1 个来源、掌握评估生成 1 道题。

限制：当前是 zip + bat 运行包，不是安装器；尚未提供桌面快捷方式自动创建。
