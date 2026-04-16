@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0\portal-front"
set "PORT=5173"

echo [frontend] project: %cd%

for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
  echo [frontend] found existing process on :%PORT%, killing: %%p
  taskkill /PID %%p /F >nul 2>nul
)

echo [frontend] starting...
echo [frontend] cmd: npm run dev
npm run dev

endlocal
