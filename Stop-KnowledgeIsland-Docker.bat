@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\docker_down.ps1"
if errorlevel 1 (
  echo Docker stop failed. See messages above.
  pause
  exit /b 1
)

endlocal
