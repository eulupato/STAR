@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set "PY=.venv\Scripts\python.exe"

if not exist "%PY%" (
    echo Ambiente virtual nao encontrado. Execute CRIAR_AMBIENTE.bat uma vez.
    pause
    exit /b 1
)

"%PY%" -c "import PIL, sounddevice, soundfile, faster_whisper" >nul 2>&1
if errorlevel 1 (
    echo Dependencias da STAR incompletas.
    echo Execute INSTALAR_VOZ.bat uma vez e tente novamente.
    pause
    exit /b 1
)

if not exist ".voice_venv\Scripts\python.exe" (
    echo Chatterbox nao configurado.
    echo Execute INSTALAR_VOZ.bat uma vez e tente novamente.
    pause
    exit /b 1
)

if not exist "voice\reference\star_reference.mp3" (
    echo Audio de referencia da voz nao encontrado.
    echo Verifique voice\reference\star_reference.mp3
    pause
    exit /b 1
)

echo ============================================
echo        INICIANDO STAR V1.9
 echo ============================================
"%PY%" main.py
if errorlevel 1 (
    echo.
    echo STAR foi encerrada com erro. Veja a mensagem acima.
    pause
)
endlocal
