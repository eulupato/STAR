@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

echo ================================================
echo        STAR V1.9 - INSTALADOR DE VOZ LOCAL
echo ================================================
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
        echo Instale Python 3.11 e rode novamente.
        pause
        exit /b 1
    )
)

echo Instalando/atualizando dependencias da STAR...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERRO ao instalar dependencias da STAR.
    pause
    exit /b 1
)

echo Instalando/atualizando Chatterbox...
".voice_venv\Scripts\python.exe" -m pip install --upgrade pip
".voice_venv\Scripts\python.exe" -m pip install chatterbox-tts
if errorlevel 1 (
    echo ERRO ao instalar Chatterbox.
    pause
    exit /b 1
)

echo.
echo INSTALACAO DA VOZ LOCAL CONCLUIDA.
echo O primeiro teste pode baixar o modelo faster-whisper automaticamente.
echo.
pause
endlocal
