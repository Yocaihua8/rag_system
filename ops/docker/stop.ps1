param(
    [switch]$RemoveVolumes
)

$ErrorActionPreference = "Stop"

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$composeFile = Join-Path $PSScriptRoot "compose.yaml"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "未找到 docker 命令。请先安装并启动 Docker Desktop。"
}

if ($RemoveVolumes) {
    docker compose --project-directory $repositoryRoot -f $composeFile down --volumes
} else {
    docker compose --project-directory $repositoryRoot -f $composeFile down
}

Write-Host "Knowledge Island 前后端容器已停止。"
