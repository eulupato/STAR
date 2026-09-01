@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set "PY=.venv\Scripts\python.exe"

if not exist "%PY%" (
    echo ERRO: ambiente virtual principal nao encontrado.
    echo Execute CRIAR_AMBIENTE.bat uma vez.
    pause
    exit /b 1
)

set "STAR_LABEL=STAR"
for /f "delims=" %%V in ('"%PY%" -c "from core.release import RELEASE; print(RELEASE.label)"') do set "STAR_LABEL=%%V"

echo ============================================
echo        INICIANDO %STAR_LABEL%
echo ============================================
echo.

"%PY%" -c "import PIL, sqlalchemy, numpy" >nul 2>&1
if errorlevel 1 (
    echo ERRO: dependencias essenciais da interface incompletas.
    echo Execute CRIAR_AMBIENTE.bat e tente novamente.
    pause
    exit /b 1
)

rem Voz e uma capacidade opcional: falhas de STT/TTS nao bloqueiam a interface.
"%PY%" -c "import sounddevice, soundfile, faster_whisper" >nul 2>&1
if errorlevel 1 (
    echo AVISO: componentes de voz incompletos. A STAR iniciara sem voz completa.
    echo Para habilitar voz depois, execute INSTALAR_VOZ.bat.
) else (
    "%PY%" -c "from voice.manager import VoiceManager; v=VoiceManager(); print('Voz:', v.tts_description); v.close()" 2>nul
)

echo.
"%PY%" main.py
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    echo STAR foi encerrada com erro. Veja a mensagem acima.
    pause
)

exit /b %RC%
