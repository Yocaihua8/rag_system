param(
    [string]$WorkspacePath = "docker-workspace",
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$composeFile = Join-Path $PSScriptRoot "compose.yaml"
$workspace = Join-Path $repositoryRoot $WorkspacePath

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "未找到 docker 命令。请先安装并启动 Docker Desktop。"
}

New-Item -ItemType Directory -Path $workspace -Force | Out-Null
$env:KNOWLEDGE_ISLAND_WORKSPACE = $workspace
$env:RAG_LLM_PROVIDER = if ($env:RAG_LLM_PROVIDER) { $env:RAG_LLM_PROVIDER } else { "api" }

docker compose --project-directory $repositoryRoot -f $composeFile up --build -d

$webPort = if ($env:KI_WEB_PORT) { $env:KI_WEB_PORT } else { "4173" }
$apiPort = if ($env:KI_API_PORT) { $env:KI_API_PORT } else { "8765" }
Write-Host "前端已启动：http://127.0.0.1:$webPort"
Write-Host "后端 API：http://127.0.0.1:$apiPort"
Write-Host "Docker 内导入目录：/workspace"
Write-Host "宿主机对应目录：$workspace"

if (-not $NoOpen) {
    Start-Process "http://127.0.0.1:$webPort"
}
