@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
set "PORT=8080"

echo [backend] project: %cd%

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
  echo [backend] found existing process on :%PORT%, killing: %%p
  taskkill /PID %%p /F >nul 2>nul
)

set "PYTHONPATH=src"
set "PYTHON_BIN=D:\anaconda3\python.exe"

echo [backend] starting...
echo [backend] cmd: "%PYTHON_BIN%" -c "from harness_app.access.api_gateway.app import run; run()"
"%PYTHON_BIN%" -c "from harness_app.access.api_gateway.app import run; run()"

endlocal
