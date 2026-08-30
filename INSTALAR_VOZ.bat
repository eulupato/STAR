@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

echo =====================================================
echo        STAR V1.9 FINAL - INSTALACAO DE VOZ
echo =====================================================
echo.
echo ENTRADA  : faster-whisper tiny (PT-BR, local)
echo OFICIAL  : Chatterbox + referencia local da STAR
echo FALLBACK : Piper PT-BR
echo FALLBACK2: Windows SAPI
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERRO: .venv nao encontrada.
    echo Execute CRIAR_AMBIENTE.bat primeiro.
    pause
    exit /b 1
)

echo [1/4] Instalando dependencias do ambiente principal...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERRO ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo [2/4] Preparando Piper PT-BR como fallback rapido...
".venv\Scripts\python.exe" voice\install_models.py
if errorlevel 1 (
    echo ERRO ao preparar o Piper.
    pause
    exit /b 1
)

echo.
echo [3/4] Preparando Whisper Tiny...
".venv\Scripts\python.exe" -c "from faster_whisper import WhisperModel; WhisperModel('tiny',device='cpu',compute_type='int8')"
if errorlevel 1 (
    echo AVISO: nao foi possivel preparar o Whisper agora.
)

echo.
echo [4/4] Preparando a voz oficial Chatterbox...
set STAR_SETUP_CHAIN=1
call INSTALAR_CHATTERBOX.bat
set STAR_SETUP_CHAIN=
if errorlevel 1 (
    echo.
    echo AVISO: Chatterbox nao ficou pronto.
    echo A STAR continuara falando pelo Piper ate a voz oficial ser configurada.
)

echo.
if exist "voice\reference\star_reference.mp3" (
    echo REFERENCIA OFICIAL: ENCONTRADA
) else (
    echo AVISO: referencia da voz oficial NAO encontrada.
    echo Coloque o arquivo autorizado em:
    echo voice\reference\star_reference.mp3
    echo Enquanto isso a STAR usara Piper como fallback.
)

echo.
echo =====================================================
echo        INSTALACAO DE VOZ V1.9 FINAL CONCLUIDA
echo =====================================================
echo Execute DIAGNOSTICO_VOZ.bat para validar.
echo.
pause
endlocal
