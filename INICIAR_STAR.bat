@echo off
setlocal
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo Ambiente virtual nao encontrado. Criando automaticamente...
  where py >nul 2>nul
  if not errorlevel 1 (py -3 -m venv .venv) else (python -m venv .venv)
)
if not exist "%PY%" (
  echo Nao foi possivel criar o ambiente virtual.
  pause
  exit /b 1
)
echo Atualizando dependencias da STAR V1.8...
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo Falha ao instalar dependencias. Verifique sua conexao.
  pause
  exit /b 1
)
echo Iniciando STAR V1.8...
"%PY%" main.py
if errorlevel 1 (
  echo.
  echo STAR foi encerrada com erro. Veja a mensagem acima.
  pause
)
endlocal
