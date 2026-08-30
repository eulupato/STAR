@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
if not exist ".venv\Scripts\python.exe" (
  echo .venv nao encontrada. Execute CRIAR_AMBIENTE.bat.
  pause
  exit /b 1
)
if not exist ".voice_venv\Scripts\python.exe" (
  echo .voice_venv nao encontrada. Execute INSTALAR_VOZ.bat.
  pause
  exit /b 1
)
if not exist "voice\reference\star_reference.mp3" (
  echo Referencia de voz nao encontrada em voice\reference\star_reference.mp3.
  pause
  exit /b 1
)
echo ============================================
echo       STAR V1.9 - TESTE DE VOZ LOCAL
echo ============================================
echo.
".venv\Scripts\python.exe" voice\diagnostics.py
set "RC=%ERRORLEVEL%"
echo.
if not "%RC%"=="0" echo O teste falhou. Veja a mensagem acima.
if "%RC%"=="0" echo TESTE CONCLUIDO COM SUCESSO.
pause
exit /b %RC%
