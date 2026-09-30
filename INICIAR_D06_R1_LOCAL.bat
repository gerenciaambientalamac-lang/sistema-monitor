@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "PYTHON_EXE="
for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
if not defined PYTHON_EXE for /f "delims=" %%P in ('where python 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
if not defined PYTHON_EXE (
  echo ERROR: No se encontro Python.
  pause
  exit /b 1
)
set "LLE_BIND=127.0.0.1"
set "LLE_PORT=8001"
set "LLE_HTTPS=0"
start "LLE V5.6.26 D06-R1 - LOCAL" cmd /k "cd /d ^"%~dp0^" ^&^& set LLE_BIND=127.0.0.1 ^& set LLE_PORT=8001 ^& set LLE_HTTPS=0 ^& ^"%PYTHON_EXE%^" server.py"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8001/"
pause
