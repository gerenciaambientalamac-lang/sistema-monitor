@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ==================================================
echo  LA LIBERTAD ESTE - V5.6.26 D06-R1
echo  LAN HTTPS / OFFLINE FIRST
echo ==================================================

set "PYTHON_EXE="
for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)" 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"
if not defined PYTHON_EXE for /f "delims=" %%P in ('where python 2^>nul') do if not defined PYTHON_EXE set "PYTHON_EXE=%%P"

if not defined PYTHON_EXE (
  echo ERROR: No se encontro Python.
  echo Instale Python 3.13 y vuelva a ejecutar este archivo.
  pause
  exit /b 1
)

echo Python: !PYTHON_EXE!

"%PYTHON_EXE%" -c "import cryptography" >nul 2>nul
if errorlevel 1 (
  echo [D06-R1] Instalando dependencia cryptography...
  "%PYTHON_EXE%" -m pip install --disable-pip-version-check --no-input cryptography
  if errorlevel 1 (
    echo ERROR: No se pudo instalar cryptography.
    echo La primera instalacion requiere Internet.
    pause
    exit /b 1
  )
)

if not exist "tls\cert.pem" (
  if not exist "tls" mkdir "tls"
  echo [D06-R1] Generando certificado HTTPS LAN...
  "%PYTHON_EXE%" "GENERAR_CERTIFICADO_LAN_D06.py"
  if errorlevel 1 (
    echo ERROR: Fallo la generacion del certificado HTTPS.
    pause
    exit /b 1
  )
)

set "LLE_BIND=0.0.0.0"
set "LLE_PORT=8001"
set "LLE_HTTPS=1"

set "SERVER_IP="
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /R /C:"IPv4.*:"') do (
  set "CAND=%%A"
  set "CAND=!CAND: =!"
  echo !CAND! | findstr /R /B /C:"192\.168\." /C:"10\." /C:"172\." >nul && if not defined SERVER_IP set "SERVER_IP=!CAND!"
)
if not defined SERVER_IP set "SERVER_IP=127.0.0.1"

echo.
echo URL LAN:
echo https://!SERVER_IP!:8001/
echo.
echo IMPORTANTE: esta consola mostrara cualquier error real del servidor.
echo No cierre esta ventana durante la prueba.
echo.

"%PYTHON_EXE%" server.py

set "RC=!ERRORLEVEL!"
echo.
echo ==================================================
echo El servidor termino. Codigo de salida: !RC!
echo ==================================================
pause
exit /b !RC!
