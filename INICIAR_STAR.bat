@echo off
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo Ambiente virtual nao encontrado. Execute CRIAR_AMBIENTE.bat.
  pause
  exit /b 1
)
echo ============================================
echo        INICIANDO STAR V1.9
echo ============================================
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Falha ao atualizar dependencias.
  pause
  exit /b 1
)
"%PY%" main.py
if errorlevel 1 (
  echo.
  echo STAR foi encerrada com erro. Veja a mensagem acima.
  pause
)
endlocal
