@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   STAR WATCH APP - PLASMA ORBIT UI + IDIOMAS
echo ============================================================

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" clients\star_watch_language.py
) else (
    python clients\star_watch_language.py
)

if errorlevel 1 (
    echo.
    echo STAR Watch encerrou com erro.
    pause
)

endlocal
