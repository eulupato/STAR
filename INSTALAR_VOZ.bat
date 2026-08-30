@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

echo ================================================
echo      STAR V1.9 - VOZ LOCAL RAPIDA
echo ================================================
echo.
echo ENTRADA : faster-whisper tiny (PT-BR, local)
echo SAIDA   : Piper PT-BR (local, rapido)
echo FALLBACK: Windows SAPI via pyttsx3
 echo CLONE   : Chatterbox fica fora do fluxo rapido
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERRO: .venv nao encontrada.
    echo Execute CRIAR_AMBIENTE.bat primeiro.
    pause
    exit /b 1
)

echo Instalando dependencias da STAR...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERRO ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo Baixando modelo Piper PT-BR apenas se necessario...
".venv\Scripts\python.exe" voice\install_models.py
if errorlevel 1 (
    echo ERRO ao preparar o Piper.
    pause
    exit /b 1
)

echo.
echo Preparando Whisper Tiny para a primeira fala...
".venv\Scripts\python.exe" -c "from faster_whisper import WhisperModel; WhisperModel('tiny',device='cpu',compute_type='int8')"
if errorlevel 1 (
    echo AVISO: nao foi possivel preparar o Whisper agora.
)

echo.
echo ================================================
echo          VOZ V1.9 PRONTA
 echo ================================================
echo Piper sera o TTS padrao porque responde muito mais rapido em CPU.
echo O reconhecimento e totalmente local.
echo.
pause
endlocal
