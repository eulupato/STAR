@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

echo ==========================================
echo STAR VOICE ENGINE - CHATTERBOX 0.1.7
echo ==========================================

if not exist ".voice_venv\Scripts\python.exe" (
    echo Criando ambiente Python 3.11...
    py -3.11 -m venv .voice_venv
    if errorlevel 1 (
        echo ERRO: Python 3.11 nao foi encontrado.
        echo Instale Python 3.11 para o motor Chatterbox.
        pause
        exit /b 1
    )
)

set "PY=.voice_venv\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install "chatterbox-tts==0.1.7"
if errorlevel 1 (
    echo ERRO na instalacao do Chatterbox 0.1.7.
    pause
    exit /b 1
)

echo.
echo INSTALACAO CONCLUIDA.
echo O motor Chatterbox sera carregado pela STAR somente quando a voz for usada.
echo.
pause
endlocal
