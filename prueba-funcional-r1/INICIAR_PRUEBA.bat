@echo off
title LA LIBERTAD ESTE - PRUEBA FUNCIONAL R1
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py servidor.py
  goto :eof
)
where python >nul 2>nul
if %errorlevel%==0 (
  python servidor.py
  goto :eof
)
echo.
echo ERROR: No se encontro Python.
echo Instale Python 3 y vuelva a ejecutar este archivo.
pause
