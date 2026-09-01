@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

set "STAR_LABEL=STAR"
if exist ".venv\Scripts\python.exe" (
  for /f "delims=" %%V in ('".venv\Scripts\python.exe" -c "from core.release import RELEASE; print(RELEASE.label)"') do set "STAR_LABEL=%%V"
)

echo =====================================================
echo        %STAR_LABEL% - INSTALACAO DE VOZ
echo =====================================================
echo.
echo ENTRADA : faster-whisper tiny (PT-BR, local)
echo OFICIAL : Chatterbox + referencia local da STAR
echo RAPIDA  : Piper PT-BR (somente se escolhido)
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
echo [2/4] Preparando Piper PT-BR para o modo rapido...
".venv\Scripts\python.exe" voice\install_models.py
if errorlevel 1 (
    echo AVISO: Piper nao ficou pronto. Isso nao impede a voz oficial.
)

echo.
echo [3/4] Preparando Whisper Tiny...
".venv\Scripts\python.exe" -c "from faster_whisper import WhisperModel; WhisperModel('tiny',device='cpu',compute_type='int8')"
if errorlevel 1 (
    echo AVISO: nao foi possivel preparar o Whisper agora.
)

echo.
echo [4/4] Preparando Chatterbox...
set STAR_SETUP_CHAIN=1
call INSTALAR_CHATTERBOX.bat
set STAR_SETUP_CHAIN=
if errorlevel 1 (
    echo ERRO: Chatterbox nao ficou pronto.
    echo Execute novamente INSTALAR_CHATTERBOX.bat e veja o erro.
)

echo.
".venv\Scripts\python.exe" -c "from voice.manager import ChatterboxOfficialTTS; e=ChatterboxOfficialTTS(); print('REFERENCIA OFICIAL:', e.reference_path if e.reference_path.exists() else 'AUSENTE')"

echo.
echo Se a referencia aparecer como AUSENTE:
echo coloque um MP3/WAV/FLAC/OGG/M4A/AAC autorizado em:
echo voice\reference\
echo e execute DIAGNOSTICO_VOZ.bat.
echo O arquivo sera mantido apenas na sua maquina.
echo.
echo =====================================================
echo        INSTALACAO DE VOZ CONCLUIDA
echo =====================================================
echo Depois execute DIAGNOSTICO_VOZ.bat.
echo.
pause
endlocal
