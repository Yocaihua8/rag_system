param(
    [string]$Python = ".venv\Scripts\python.exe",
    [string]$TargetTriple = "x86_64-pc-windows-msvc"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$TauriBinaryDir = Join-Path $ProjectRoot "src-tauri/binaries"
$BackendName = "knowledge-island-backend"
$DefaultWindowsSidecar = "knowledge-island-backend-x86_64-pc-windows-msvc.exe"
$TargetExeName = if ($TargetTriple -eq "x86_64-pc-windows-msvc") {
    $DefaultWindowsSidecar
} else {
    "$BackendName-$TargetTriple.exe"
}
$SourceExe = Join-Path $ProjectRoot "dist/$BackendName.exe"
$TargetExe = Join-Path $TauriBinaryDir $TargetExeName

Set-Location $ProjectRoot

if (-not (Test-Path $Python)) {
    $Python = "python"
}

Write-Host "Building Vue/Vite frontend..."
npm run build

Write-Host "Building FastAPI sidecar with PyInstaller..."
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --name $BackendName `
    --add-data "webapp/static_dist;webapp/static_dist" `
    app.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

if (-not (Test-Path $SourceExe)) {
    throw "Expected PyInstaller output was not found: $SourceExe"
}

New-Item -ItemType Directory -Force -Path $TauriBinaryDir | Out-Null
Copy-Item -Path $SourceExe -Destination $TargetExe -Force

Write-Host "Created Tauri sidecar: $TargetExe"
