@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

echo ================================================
echo        STAR V1.9 - VOZ 100%% LOCAL
 echo ================================================
echo.
echo A STAR nao usa ElevenLabs neste ciclo.
echo Entrada : faster-whisper local
 echo Saida   : Chatterbox local
 echo Audio   : sounddevice
 echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERRO: .venv da STAR nao foi encontrada.
    echo Execute CRIAR_AMBIENTE.bat primeiro.
    pause
    exit /b 1
)

if not exist ".voice_venv\Scripts\python.exe" (
    echo Criando ambiente dedicado do Chatterbox com Python 3.11...
    py -3.11 -m venv .voice_venv
    if errorlevel 1 (
        echo ERRO: Python 3.11 nao foi encontrado.
        echo O Chatterbox recomenda Python 3.11.
        pause
        exit /b 1
    )
)

echo Instalando dependencias de audio e STT local...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERRO ao instalar dependencias da STAR.
    pause
    exit /b 1
)

echo Instalando Chatterbox no ambiente dedicado...
".voice_venv\Scripts\python.exe" -m pip install --upgrade pip
".voice_venv\Scripts\python.exe" -m pip install chatterbox-tts
if errorlevel 1 (
    echo ERRO ao instalar Chatterbox.
    pause
    exit /b 1
)

echo.
echo ================================================
echo       VOZ LOCAL INSTALADA
 echo ================================================
echo.
echo STT : faster-whisper (modelo base, portugues)
echo TTS : Chatterbox Multilingual
 echo.
echo O modelo do faster-whisper sera baixado na primeira transcricao.
echo O modelo do Chatterbox sera baixado na primeira fala.
echo.
pause
endlocal
