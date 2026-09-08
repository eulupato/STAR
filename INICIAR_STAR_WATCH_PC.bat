@echo off
setlocal
cd /d "%~dp0"

echo =====================================================
echo       STAR WATCH - FUNCTIONAL BETA / PC PREVIEW
echo =====================================================
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "clients\star_watch_pc.py"
) else (
    echo [ERRO] .venv nao encontrada.
    echo Execute CRIAR_AMBIENTE.bat primeiro.
    exit /b 1
)

endlocal
