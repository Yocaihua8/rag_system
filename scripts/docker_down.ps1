param(
    [switch]$RemoveVolumes
)

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $projectRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "未找到 docker 命令。请先安装并启动 Docker Desktop。"
}

if ($RemoveVolumes) {
    docker compose down --volumes
} else {
    docker compose down
}

Write-Host "知识岛 Docker Web 已停止。"
