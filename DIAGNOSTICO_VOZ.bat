@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

if not exist ".venv\Scripts\python.exe" (
    echo .venv nao encontrada. Execute CRIAR_AMBIENTE.bat.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m voice.diagnostics
set "CODE=%ERRORLEVEL%"

echo.
if not "%CODE%"=="0" echo O diagnostico encontrou uma falha. A mensagem acima indica a etapa que falhou.
pause
exit /b %CODE%
