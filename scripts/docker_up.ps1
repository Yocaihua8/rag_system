param(
    [string]$WorkspacePath = "docker-workspace",
    [switch]$NoOpen
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$composeFile = Join-Path $projectRoot "compose.yaml"
Set-Location $projectRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "未找到 docker 命令。请先安装并启动 Docker Desktop。"
}

$workspace = Join-Path $projectRoot $WorkspacePath
New-Item -ItemType Directory -Path $workspace -Force | Out-Null

if (-not $env:DEEPSEEK_API_KEY) {
    $userKey = [Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY', 'User')
    if ($userKey) {
        $env:DEEPSEEK_API_KEY = $userKey
    }
}

if (-not $env:RAG_EMBED_API_KEY) {
    $embedKey = [Environment]::GetEnvironmentVariable('RAG_EMBED_API_KEY', 'User')
    if ($embedKey) {
        $env:RAG_EMBED_API_KEY = $embedKey
    }
}

if (-not $env:RAG_LLM_PROVIDER) {
    $env:RAG_LLM_PROVIDER = "api"
}

if (-not $env:KNOWLEDGE_ISLAND_WORKSPACE) {
    $env:KNOWLEDGE_ISLAND_WORKSPACE = $workspace
}

docker compose --project-directory $projectRoot -f $composeFile up --build -d

Write-Host "知识岛 Docker Web 已启动：http://127.0.0.1:8765"
Write-Host "Docker 内导入目录请填写：/workspace"
Write-Host "宿主机对应目录：$workspace"

if (-not $NoOpen) {
    Start-Process "http://127.0.0.1:8765"
}
