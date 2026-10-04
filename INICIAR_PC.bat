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

"%PY%" star_world_launcher.py
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo [ERRO] STAR WORLD encerrou com codigo %RC%.
  echo Para forcar temporariamente a interface classica:
  echo   set STAR_PC_CLASSIC=1
  pause
)
exit /b %RC%
