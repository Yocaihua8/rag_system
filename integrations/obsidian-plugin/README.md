# Knowledge Island Bridge

Knowledge Island Bridge 是 Knowledge Island 2.0 的 Obsidian 桌面端配套插件。它只连接本机 loopback 服务，不支持移动端，也不面向 Obsidian 社区市场发布。

## 能力与边界

- 在 Vault 完成布局加载后监听 Markdown 的新增、修改、重命名和删除。
- 发送正文、Frontmatter、标签及已解析/未解析 Wikilink；离线时事件会保存在插件 `data.json`，恢复连接后按原 `event_id` 重放。
- 精确排除配置的 `Knowledge Island/<项目名>/` 输出根，避免系统产物被反向摄入。
- 轮询已经在 Knowledge Island 主应用中预览并确认的发布，逐文件串行执行。
- 只创建不存在的目标；更新已有文件前会校验输出路径、当前内容 hash、托管标记、稳定 ID、项目 ID 和产物类型。
- 冲突只回报，不自动合并、不强制覆盖。删除系统生成文件不会触发插件自动重建；如需重建，必须在主应用重新预览并确认。

插件不会把 Vault 根目录交给后端，也不会直接访问 `.obsidian` 或使用 Node `fs` 读写笔记。连接令牌仅通过 `Authorization: Bearer` 请求头发送，不写入笔记、Frontmatter、URL 或日志；为了离线恢复连接，令牌会保存在当前 Vault 的插件 `data.json` 中。服务端仅保存令牌哈希。

## 本地开发

```powershell
npm install
npm test
npm run typecheck
npm run build
```

构建产物为 `main.js`。本地测试时将 `main.js`、`manifest.json` 和可选的 `styles.css` 复制到独立测试 Vault 的 `.obsidian/plugins/knowledge-island-bridge/`。不要在主 Vault 中开发验证。

当前 Obsidian 官方类型仓库的 `main` 版本已指向 1.13.2，但 npm registry 截至本工程落地时最高只发布到 1.13.1；因此 lockfile 固定使用可安装、可验证的 `obsidian@1.13.1`，待 1.13.2 正式发布后再独立升级。

## 配对

1. 启动仅监听 loopback 的 Knowledge Island 本地服务。
2. 在主应用中为目标项目生成一次性、限时配对码。
3. 在插件设置中填写服务地址和配对码；输出目录留空时采用主应用生成的 `Knowledge Island/<项目名>/`，也可在配对前显式修改。
4. 配对成功后，插件持久化连接 ID、项目 ID 和令牌，并开始发送队列与轮询发布。

默认服务地址为 `http://127.0.0.1:8765`。插件只接受 `localhost`、`127.0.0.1` 或 `::1` 的 `http/https` 地址。
