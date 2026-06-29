知识岛 Docker 快速开始

适用对象：
不想安装 Python、不想配置虚拟环境，只想先把本地 Web MVP 跑起来的用户。

前置要求：
1. 已安装 Docker Desktop 或 Docker Engine。
2. Docker 已经启动。
3. 如果要使用 DeepSeek 真实回答，准备好 DEEPSEEK_API_KEY 或 RAG_LLM_API_KEY。
4. 如果要使用真实 Embedding，准备好 RAG_EMBED_PROVIDER、RAG_EMBED_API_BASE、RAG_EMBED_API_MODEL、RAG_EMBED_API_KEY。

启动：
1. Windows 可双击 Start-KnowledgeIsland-Docker.bat。
2. Windows PowerShell 可执行：.\scripts\docker_up.ps1
3. Linux / macOS 可执行：./scripts/docker_up.sh
4. 通用 Compose 命令：docker compose --project-directory . -f compose.yaml up --build -d
5. 首次启动会构建镜像并生成 Vue 前端产物，可能需要等待几分钟。
6. 浏览器打开 http://127.0.0.1:8765。

导入文件：
推荐方式：
1. 打开 Web 页面后，点击“选择本机文件夹导入”。
2. 选择你的本地项目文件夹，例如 E:\Code\your-project。
3. 浏览器会把允许的文本文件、DOCX 和 PDF 二进制内容上传到本地服务并入库。
4. PDF 正文抽取需要可选 pymupdf；未安装时会在跳过明细里显示原因，不影响其他文件导入。

挂载目录方式：
1. 把要导入的 Markdown、TXT、DOCX、代码或配置文件放入 docker-workspace 文件夹。
2. 在 Web 页面创建项目空间。
3. 项目空间目录填写 /workspace。
4. 点击“同步当前项目目录”。

停止：
1. Windows 可双击 Stop-KnowledgeIsland-Docker.bat。
2. Windows PowerShell 可执行：.\scripts\docker_down.ps1
3. Linux / macOS 可执行：./scripts/docker_down.sh
4. 通用 Compose 命令：docker compose --project-directory . -f compose.yaml down

数据位置：
- 容器内运行数据：/app/runtime
- 默认持久化卷：ki-runtime
- 默认导入目录：docker-workspace
- 容器内导入路径：/workspace

注意：
- Docker 模式下，Web 页面里的目录要填写容器路径 /workspace，不要填写 Windows 路径。
- 如果不想理解 Docker 路径，直接使用“选择本机文件夹导入”。
- Docker 镜像会在构建阶段生成 webapp/static_dist，不需要你在宿主机提前运行 npm run build。
- 启动脚本会读取 DEEPSEEK_API_KEY 和 RAG_EMBED_API_KEY 并传给容器，但不会在命令窗口打印 Key。
- Embedding 服务必须支持 OpenAI-compatible /embeddings；未配置或失败时会回退本地向量。
- 如果启动失败，请先确认 Docker 是否正在运行，再执行 docker compose --project-directory . -f compose.yaml logs -f web 查看日志。
