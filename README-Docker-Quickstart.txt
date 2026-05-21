知识岛 Docker 快速开始

适用对象：
不想安装 Python、不想配置虚拟环境，只想先把本地 Web MVP 跑起来的用户。

前置要求：
1. 已安装 Docker Desktop。
2. Docker Desktop 已经启动。
3. 如果要使用 DeepSeek 真实回答，Windows User 环境变量里已经配置 DEEPSEEK_API_KEY。
4. 如果要使用真实 Embedding，Windows User 环境变量里已经配置 RAG_EMBED_PROVIDER、RAG_EMBED_API_BASE、RAG_EMBED_API_MODEL、RAG_EMBED_API_KEY。

启动：
1. 双击 Start-KnowledgeIsland-Docker.bat。
2. 等待命令窗口显示 Docker Web 已启动。
3. 浏览器打开 http://127.0.0.1:8765。

导入文件：
推荐方式：
1. 打开 Web 页面后，点击“选择文件夹导入”。
2. 选择你的本地项目文件夹，例如 E:\Code\your-project。
3. 浏览器会把允许的文本文件和 DOCX 内容上传到本地服务并入库。
4. PDF 暂不做无依赖正文解析，如被选择会在跳过明细里显示原因。

高级方式：
1. 把要导入的 Markdown、TXT、DOCX、代码或配置文件放入 docker-workspace 文件夹。
2. 在 Web 页面创建项目空间。
3. 项目空间目录填写 /workspace。
4. 点击导入。

停止：
双击 Stop-KnowledgeIsland-Docker.bat。

数据位置：
- 导入目录：docker-workspace
- 容器内路径：/workspace
- 运行数据：runtime/docker

注意：
- Docker 模式下，Web 页面里的目录要填写容器路径 /workspace，不要填写 Windows 路径。
- 如果不想理解 Docker 路径，直接使用“选择文件夹导入”。
- 启动脚本会读取 DEEPSEEK_API_KEY 并传给容器，但不会在命令窗口打印 Key。
- 启动脚本会读取 RAG_EMBED_API_KEY 并传给容器，但不会在命令窗口打印 Key。
- Embedding 服务必须支持 OpenAI-compatible /embeddings；未配置或失败时会回退本地向量。
- 如果启动失败，请先确认 Docker Desktop 是否正在运行。
