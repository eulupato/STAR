@echo off
setlocal
cd /d "%~dp0"

set STAR_DEVICE_GATEWAY=1

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    echo [ERRO] .venv nao encontrada. Execute CRIAR_AMBIENTE.bat primeiro.
    exit /b 1
)

endlocal
