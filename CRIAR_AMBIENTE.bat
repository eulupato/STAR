@echo off
setlocal
cd /d "%~dp0"
set "LEGACY_PATH=C:\Development\Projects\STAR\.venv"

if exist ".venv\pyvenv.cfg" (
    findstr /i /c:"%LEGACY_PATH%" ".venv\pyvenv.cfg" >nul
    if not errorlevel 1 (
        echo Ambiente .venv em caminho legado detectado. Recriando em D:\STAR...
        rmdir /s /q ".venv"
    )
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m venv .venv
) else (
    python -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Ambiente da STAR criado.
echo Agora use INICIAR_PC.bat, INICIAR_MOBILE.bat ou INICIAR_WATCH.bat
pause
endlocal
