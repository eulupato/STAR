@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set "PY=.venv\Scripts\python.exe"

echo ============================================
echo        INICIANDO STAR V2.0 MIND
echo ============================================
echo.

if not exist "%PY%" (
    echo ERRO: ambiente virtual principal nao encontrado.
    echo Execute CRIAR_AMBIENTE.bat uma vez.
    pause
    exit /b 1
)

"%PY%" -c "import PIL, sounddevice, soundfile, faster_whisper" >nul 2>&1
if errorlevel 1 (
    echo ERRO: dependencias principais incompletas.
    echo Execute INSTALAR_VOZ.bat uma vez e tente novamente.
    pause
    exit /b 1
)

rem A voz e uma capacidade da STAR, nao uma condicao para abrir a interface.
rem O proprio VoiceManager resolve a referencia local e mostra estado degradado
rem caso Chatterbox/referencia ainda nao estejam disponiveis.
"%PY%" -c "from voice.manager import VoiceManager; v=VoiceManager(); print('Voz:', v.tts_description); v.close()" 2>nul

echo.
"%PY%" main.py
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    echo STAR foi encerrada com erro. Veja a mensagem acima.
    pause
)

exit /b %RC%
