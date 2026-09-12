@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   STAR WATCH APP - PLASMA ORBIT UI
echo ============================================================

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" clients\star_watch_visual.py
) else (
    python clients\star_watch_visual.py
)

if errorlevel 1 (
    echo.
    echo STAR Watch encerrou com erro.
    pause
)

endlocal
