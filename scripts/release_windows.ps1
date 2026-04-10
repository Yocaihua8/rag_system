param(
    [string]$PythonExe = ".venv\Scripts\python.exe",
    [switch]$SkipCheck,
    [switch]$ZipOutput
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir "..")
Set-Location $projectRoot

$releaseRoot = Join-Path $projectRoot "release"
$buildDir = Join-Path $releaseRoot "build"
$distDir = Join-Path $releaseRoot "dist"
$specFile = Join-Path $projectRoot "RAGDesktop.spec"

Write-Host "[release] project root: $projectRoot"

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "[release] 未找到 Python: $PythonExe"
}

if (-not $SkipCheck) {
    Write-Host "[release] running first-run checks..."
    & $PythonExe .\scripts\first_run_check.py
}

Write-Host "[release] checking pyinstaller..."
& $PythonExe -m PyInstaller --version | Out-Null

if (Test-Path -LiteralPath $buildDir) {
    Remove-Item -LiteralPath $buildDir -Recurse -Force
}
if (Test-Path -LiteralPath $distDir) {
    Remove-Item -LiteralPath $distDir -Recurse -Force
}
if (Test-Path -LiteralPath $specFile) {
    Remove-Item -LiteralPath $specFile -Force
}

Write-Host "[release] building executable..."
& $PythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name "RAGDesktop" `
    --paths "$projectRoot" `
    --collect-all "PySide6" `
    --collect-submodules "desktop" `
    --collect-submodules "backend" `
    --distpath "$distDir" `
    --workpath "$buildDir" `
    .\desktop\main.py

$appDir = Join-Path $distDir "RAGDesktop"
if (-not (Test-Path -LiteralPath $appDir)) {
    throw "[release] 打包失败：未找到目录 $appDir"
}

$runBat = Join-Path $appDir "Run_RAGDesktop.bat"
$batContent = @"
@echo off
setlocal
cd /d %~dp0
RAGDesktop.exe
endlocal
"@
Set-Content -LiteralPath $runBat -Value $batContent -Encoding ASCII

if ($ZipOutput) {
    $zipPath = Join-Path $releaseRoot "RAGDesktop_win64.zip"
    if (Test-Path -LiteralPath $zipPath) {
        Remove-Item -LiteralPath $zipPath -Force
    }
    Compress-Archive -Path (Join-Path $appDir "*") -DestinationPath $zipPath
    Write-Host "[release] zip ready: $zipPath"
}

Write-Host "[release] done. output: $appDir"
Write-Host "[release] run: $runBat"
