@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "SERVER_IP="
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /R /C:"IPv4.*:"') do (
  set "CAND=%%A"
  set "CAND=!CAND: =!"
  echo !CAND! | findstr /R /B /C:"192\.168\." /C:"10\." /C:"172\." >nul && if not defined SERVER_IP set "SERVER_IP=!CAND!"
)
if not defined SERVER_IP set "SERVER_IP=127.0.0.1"
start "" "https://!SERVER_IP!:8001/01_SISTEMA_INSPECCIONES/"
exit /b 0
