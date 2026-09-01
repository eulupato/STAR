@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

if not exist ".venv\Scripts\python.exe" (
  echo ERRO: .venv nao encontrada. Execute CRIAR_AMBIENTE.bat.
  pause
  exit /b 1
)

set "STAR_LABEL=STAR"
for /f "delims=" %%V in ('".venv\Scripts\python.exe" -c "from core.release import RELEASE; print(RELEASE.label)"') do set "STAR_LABEL=%%V"

echo ============================================
echo       %STAR_LABEL% - TESTE DE VOZ LOCAL
echo ============================================
echo.
echo O diagnostico usa o mesmo resolvedor de referencia da interface.
echo Nao ha nome de arquivo de audio fixo neste launcher.
echo.

".venv\Scripts\python.exe" -m voice.diagnostics
set "RC=%ERRORLEVEL%"

echo.
if not "%RC%"=="0" echo O teste encontrou uma falha. Veja a etapa indicada acima.
if "%RC%"=="0" echo TESTE CONCLUIDO COM SUCESSO.
pause
exit /b %RC%
