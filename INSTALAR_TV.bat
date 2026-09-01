@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set "PY=.venv\Scripts\python.exe"

if not exist "%PY%" (
    echo ERRO: ambiente virtual principal nao encontrado.
    echo Execute CRIAR_AMBIENTE.bat primeiro.
    pause
    exit /b 1
)

echo Instalando backend opcional da STAR TV...
"%PY%" -m pip install -r requirements-media.txt
if errorlevel 1 (
    echo Falha ao instalar o backend da STAR TV.
    pause
    exit /b 1
)

echo.
echo STAR TV preparada. O WebView sera carregado somente quando usado.
pause
