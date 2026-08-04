param(
    [string]$Python = ".venv\Scripts\python.exe",
    [string]$TargetTriple = "x86_64-pc-windows-msvc"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$TauriRoot = Join-Path $ProjectRoot "src-tauri"
$TauriBinaryDir = Join-Path $TauriRoot "binaries"
$BuildRoot = Join-Path $TauriRoot "build\sidecar"
$BackendName = "knowledge-island-backend"
$TargetExeName = "$BackendName-$TargetTriple.exe"
$SourceExe = Join-Path $BuildRoot "dist\$BackendName.exe"
$TargetExe = Join-Path $TauriBinaryDir $TargetExeName

Set-Location $ProjectRoot

if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}

Write-Host "Building API-only FastAPI sidecar with PyInstaller..."
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name $BackendName `
    --paths $ProjectRoot `
    --add-data "$ProjectRoot\backend\alembic.ini;backend" `
    --add-data "$ProjectRoot\backend\storage\v3\migrations;backend/storage/v3/migrations" `
    --distpath (Join-Path $BuildRoot "dist") `
    --workpath (Join-Path $BuildRoot "work") `
    --specpath (Join-Path $BuildRoot "spec") `
    backend/__main__.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

if (-not (Test-Path -LiteralPath $SourceExe)) {
    throw "Expected PyInstaller output was not found: $SourceExe"
}

New-Item -ItemType Directory -Force -Path $TauriBinaryDir | Out-Null
Copy-Item -LiteralPath $SourceExe -Destination $TargetExe -Force

Write-Host "Created Tauri sidecar: $TargetExe"
