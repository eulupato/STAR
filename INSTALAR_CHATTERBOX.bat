@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo STAR VOICE ENGINE - CHATTERBOX
echo ==========================================
if not exist ".voice_venv\Scripts\python.exe" (
  py -3.11 -m venv .voice_venv
  if errorlevel 1 (echo ERRO ao criar ambiente Python 3.11.& pause & exit /b 1)
)
set "PY=.voice_venv\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip
"%PY%" -m pip install chatterbox-tts
if errorlevel 1 (echo ERRO na instalacao do Chatterbox.& pause & exit /b 1)
echo.
echo INSTALACAO CONCLUIDA.
echo Execute TESTAR_VOZ_LOCAL.bat
pause
