@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0docker_up.ps1"
if errorlevel 1 (
  echo Docker startup failed. See messages above.
  pause
  exit /b 1
)

endlocal
