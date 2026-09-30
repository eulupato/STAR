@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "PY=.venv\Scripts\python.exe"
set "STAR_DEVICE_GATEWAY=1"

if not exist "%PY%" (
  echo [ERRO] Ambiente .venv nao encontrado. Execute CRIAR_AMBIENTE.bat.
  pause
  exit /b 1
)

"%PY%" main.py
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo [ERRO] STAR PC encerrou com codigo %RC%.
  pause
)
exit /b %RC%
