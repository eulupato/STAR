@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

echo ================================================
echo       STAR V1.9 - VOZ LOCAL RAPIDA
echo ================================================
echo.
echo STT : faster-whisper tiny (PT-BR, local)
echo TTS : Piper PT-BR (local, rapido)
echo CLONE: Chatterbox opcional para voz clonada
 echo AUDIO: sounddevice
 echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERRO: .venv nao encontrada.
    echo Execute CRIAR_AMBIENTE.bat primeiro.
    pause
    exit /b 1
)

echo Instalando dependencias principais...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERRO ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo Baixando modelo Piper PT-BR...
".venv\Scripts\python.exe" -m piper.download_voices pt_BR-faber-medium --data-dir "%CD%\voice\models\piper"
if errorlevel 1 (
    echo ERRO ao baixar a voz Piper.
    pause
    exit /b 1
)

echo.
echo Preparando Whisper Tiny para evitar download na primeira fala...
".venv\Scripts\python.exe" -c "from faster_whisper import WhisperModel; WhisperModel('tiny',device='cpu',compute_type='int8')"
if errorlevel 1 (
    echo AVISO: nao foi possivel preparar o Whisper agora. Ele tentara baixar na primeira fala.
)

echo.
echo ================================================
echo       VOZ RAPIDA INSTALADA
 echo ================================================
echo.
echo A voz padrao agora e Piper e nao depende de servico externo.
echo O Chatterbox continua disponivel para futuras falas clonadas.
echo.
pause
endlocal
