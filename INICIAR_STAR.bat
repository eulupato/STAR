@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set "PY=.venv\Scripts\python.exe"

echo ============================================
echo        INICIANDO STAR V1.9 FINAL
echo ============================================
echo.

if not exist "%PY%" (
    echo ERRO: ambiente virtual principal nao encontrado.
    echo Execute CRIAR_AMBIENTE.bat uma vez.
    pause
    exit /b 1
)

rem Valida dependencias que fazem parte do caminho real de inicializacao.
rem SQLAlchemy e necessario pela persistencia; sem este check a falha aparecia
rem somente depois, durante os imports da interface/memoria.
"%PY%" -c "import PIL, sqlalchemy, sounddevice, soundfile, faster_whisper" >nul 2>&1
if errorlevel 1 (
    echo ERRO: dependencias principais incompletas.
    echo Execute CRIAR_AMBIENTE.bat e INSTALAR_VOZ.bat conforme necessario.
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
