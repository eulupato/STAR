@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   STAR WATCH APP V0.4 - SIMULADOR PC
echo ============================================================

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" clients\star_watch_app.py
) else (
    python clients\star_watch_app.py
)

if errorlevel 1 (
    echo.
    echo STAR Watch encerrou com erro.
    pause
)

endlocal
