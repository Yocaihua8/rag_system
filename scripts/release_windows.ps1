param(
    [string]$PythonExe = ".venv\Scripts\python.exe",
    [string]$ProductName = "KnowledgeIsland",
    [string]$EntryPoint = "app.py",
    [string]$CacheRoot = "release-cache",
    [switch]$InstallPyInstaller,
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
$specFile = Join-Path $projectRoot ("{0}.spec" -f $ProductName)

$cacheRoot = Join-Path $projectRoot $CacheRoot
$pyiConfigDir = Join-Path $cacheRoot "pyinstaller-config"
$pyiPycacheDir = Join-Path $cacheRoot "pycache"
$tempDir = Join-Path $cacheRoot "tmp"
$xdgCacheDir = Join-Path $cacheRoot "xdg-cache"

function Set-LocalBuildEnv {
    param()

    New-Item -ItemType Directory -Path $pyiConfigDir, $pyiPycacheDir, $tempDir, $xdgCacheDir -Force | Out-Null

    $script:originalEnv = @{
        PYINSTALLER_CONFIG_DIR = $env:PYINSTALLER_CONFIG_DIR
        PYTHONPYCACHEPREFIX  = $env:PYTHONPYCACHEPREFIX
        XDG_CACHE_HOME       = $env:XDG_CACHE_HOME
        TEMP                 = $env:TEMP
        TMP                  = $env:TMP
    }

    $env:PYINSTALLER_CONFIG_DIR = $pyiConfigDir
    $env:PYTHONPYCACHEPREFIX  = $pyiPycacheDir
    $env:XDG_CACHE_HOME      = $xdgCacheDir
    $env:TEMP                = $tempDir
    $env:TMP                 = $tempDir
}

function Restore-BuildEnv {
    param()

    if ($null -eq $script:originalEnv) {
        return
    }

    foreach ($key in $script:originalEnv.Keys) {
        $value = $script:originalEnv[$key]
        if ($null -eq $value) {
            Remove-Item -LiteralPath "Env:$key" -ErrorAction SilentlyContinue
        } else {
            Set-Item -Path "Env:$key" -Value $value
        }
    }
}

Write-Host ("[release] project root: {0}" -f $projectRoot)
Write-Host ("[release] local build cache: {0}" -f $cacheRoot)

Set-LocalBuildEnv

try {
    if (-not (Test-Path -LiteralPath $PythonExe)) {
        throw ("[release] Python not found: {0}" -f $PythonExe)
    }

    $entryPath = Join-Path $projectRoot $EntryPoint
    if (-not (Test-Path -LiteralPath $entryPath)) {
        throw ("[release] Entry point not found: {0}" -f $entryPath)
    }

    if (-not $SkipCheck) {
        Write-Host "[release] running first-run checks..."
        & $PythonExe .\scripts\first_run_check.py
    }

    Write-Host "[release] checking pyinstaller..."
    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $pyInstallerVersion = & $PythonExe -m PyInstaller --version 2>&1
    $ErrorActionPreference = $previousErrorAction
    if ($LASTEXITCODE -ne 0) {
        if (-not $InstallPyInstaller) {
            throw ("[release] PyInstaller not detected. Run: {0} -m pip install pyinstaller, or re-run with -InstallPyInstaller" -f $PythonExe)
        }

        Write-Host "[release] PyInstaller not found. Installing..."
        & $PythonExe -m pip install pyinstaller
        if ($LASTEXITCODE -ne 0) {
            throw "[release] Failed to install PyInstaller. Please check network or permissions."
        }

        $previousErrorAction = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $pyInstallerVersion = & $PythonExe -m PyInstaller --version 2>&1
        $ErrorActionPreference = $previousErrorAction
        if ($LASTEXITCODE -ne 0) {
            throw ("[release] PyInstaller is still unavailable. Run: {0} -m pip install pyinstaller" -f $PythonExe)
        }
    }

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
        --name $ProductName `
        --paths "$projectRoot" `
        --collect-all "PySide6" `
        --collect-all "chromadb" `
        --collect-all "chromadb_rust_bindings" `
        --collect-submodules "src" `
        --distpath "$distDir" `
        --workpath "$buildDir" `
        $entryPath

    if ($LASTEXITCODE -ne 0) {
        throw "[release] PyInstaller build failed."
    }
}
finally {
    Restore-BuildEnv
}

$appDir = Join-Path $distDir $ProductName
if (-not (Test-Path -LiteralPath $appDir)) {
    throw ("[release] Build failed: output folder not found: {0}" -f $appDir)
}

$exeName = "$ProductName.exe"
$exePath = Join-Path $appDir $exeName
$runBat = Join-Path $appDir ("Run_{0}.bat" -f $ProductName)
$batContent = @(
    "@echo off"
    "setlocal"
    "cd /d %~dp0"
    'set "RAG_RUNTIME_DIR=%~dp0runtime"'
    "%~dp0$exeName"
    "endlocal"
) -join "`r`n"
Set-Content -LiteralPath $runBat -Value $batContent -Encoding ASCII

if (-not (Test-Path -LiteralPath $exePath)) {
    throw ("[release] Build failed: executable not found: {0}" -f $exePath)
}

if ($ZipOutput) {
    $zipPath = Join-Path $releaseRoot ("{0}_win64.zip" -f $ProductName)
    if (Test-Path -LiteralPath $zipPath) {
        Remove-Item -LiteralPath $zipPath -Force
    }
    Compress-Archive -Path (Join-Path $appDir "*") -DestinationPath $zipPath
    Write-Host ("[release] zip ready: {0}" -f $zipPath)
}

Write-Host ("[release] done. output: {0}" -f $appDir)
Write-Host ("[release] run: {0}" -f $runBat)
