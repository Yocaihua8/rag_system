# 开源许可证选择指南

> 状态：Active
> Owner：RAG 团队
> Last Updated：2026-07-30
> Scope：Knowledge Island 公开仓库的许可证决策、落地与发布前核对
> Related：`open-source-governance.md`、`../../SECURITY.md`、`../../CONTRIBUTING.md`、`../../README.md`

本文档记录当前许可证状态和后续决策步骤，不提供法律意见，也不把公开仓库状态等同于开源授权。

## 1. 当前事实与结论

- GitHub 仓库 `Yocaihua8/rag_system` 当前公开可见。
- 仓库根目录当前没有 `LICENSE` 文件。
- `src-tauri/Cargo.toml` 的 `license` 字段当前为 `UNLICENSED`。
- 根目录 `package.json` 标记为 `"private": true`，不代表代码已经获得开源许可证。
- 因此，Knowledge Island 当前是“源代码公开但许可证未决”，不能宣称已经按 OSI 许可证开源。
- 在许可证决策落地前，不应把仓库内容的使用、修改、再分发或商业使用描述为已获授权。

权威参考入口：

- [OSI Approved Licenses](https://opensource.org/licenses)
- [SPDX License List](https://spdx.org/licenses/)
- [GitHub：Licensing a repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)

## 2. 决策记录

| 项目 | 当前结论 |
|------|----------|
| 项目名称 | Knowledge Island |
| 许可证 SPDX 标识 | TBD |
| 许可证完整名称 | TBD |
| 选择原因 | TBD；需由有权授权的维护者结合分发目标、专利条款、互惠要求和依赖兼容性决定 |
| 适用范围 | TBD；代码、文档、示例、模型、数据和素材需分别确认 |
| 版权主体 | TBD |
| 决策人 | 项目维护者；具体责任人 TBD |
| 决策日期 | TBD |
| 法务 / 组织政策核对 | N/A；当前未发现已完成的法务或组织政策审查记录 |

## 3. 选择时的检查维度

| 维度 | 需要回答的问题 |
|------|----------------|
| 使用与分发 | 是否允许商业使用、修改、再分发和私有使用？ |
| 互惠要求 | 修改或衍生作品是否必须以相同许可证公开，适用范围是什么？ |
| 专利条款 | 是否需要明确的专利授权、终止或报复条款？ |
| 通知义务 | 分发源码、Windows 安装包、容器镜像时需保留哪些版权、许可证或 NOTICE 内容？ |
| 依赖兼容性 | Python、npm、Rust/Tauri 依赖及复制内容的许可证是否兼容？ |
| 贡献模式 | 外部贡献采用同一许可证、DCO、CLA，还是其他书面约定？ |
| 非代码资产 | 文档、示例、模型、数据、字体、图片和商标是否需要单独授权？ |
| 组织约束 | 雇主、客户、学校、资助方或合同是否限制授权权利？当前结论为 TBD。 |

不要只凭“宽松”或“强 copyleft”等标签做决定；最终应阅读所选许可证的完整正文和适用条件。

## 4. 落地步骤

1. 由有权授权的维护者确认版权主体、分发目标和适用范围。
2. 完成直接依赖、复制代码、文档和非代码资产的许可证清单与兼容性核对。
3. 从 OSI / SPDX 等权威来源取得所选许可证的标准完整文本。
4. 将完整许可证文本保存为仓库根目录 `LICENSE`，只替换许可证明确允许填写的字段。
5. 将根目录 `README.md`、`src-tauri/Cargo.toml` 及其他实际发布元数据统一为同一 SPDX 标识；是否调整 `package.json` 的 `private` 属性应由发布方式决定，不能自动修改。
6. 如第三方条款要求，新增 `NOTICE` 或 `THIRD_PARTY_NOTICES` 并记录来源、版本和许可证。
7. 在 `CONTRIBUTING.md` 中写清外部贡献的授权方式。
8. 检查源码包、GitHub Release、Windows 安装包和容器镜像是否包含必须分发的许可证与通知文件。

## 5. 不应自动化的行为

- 不根据项目名称、公开状态或技术栈自动替维护者选择许可证。
- 不生成占位 `LICENSE` 并声称项目已经开源。
- 不删除或改写第三方版权、许可证或 NOTICE 内容。
- 不把代码许可证自动套用于字体、图片、数据集、模型或商标。
- 不在未理解法律影响时拼接多个许可证或附加用途限制。
- 不把 `Cargo.toml` 的 `UNLICENSED` 改成猜测的 SPDX 标识。

## 6. 发布与治理检查清单

- [ ] 已明确许可证 SPDX 标识、版权主体、决策人和决策日期。
- [ ] 仓库根目录存在真实、完整的许可证文件。
- [ ] README、发布元数据和 LICENSE 的许可证标识一致。
- [ ] 项目有权授权全部纳入范围的自有内容。
- [ ] 第三方依赖和复制内容已完成兼容性与通知义务检查。
- [ ] 外部贡献的授权方式已在贡献指南中写清。
- [ ] 模型、数据、字体、图片和商标等非代码资产已单独确认。
- [ ] 发布制品已包含其许可证要求的文件。

在以上清单完成前，许可证状态保持 `TBD / UNLICENSED`，公开仓库只代表可以查看源码。
