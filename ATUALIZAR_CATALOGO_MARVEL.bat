@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo   STAR V3.0 - ATUALIZAR CATALOGO MARVEL
echo ============================================================
echo.
echo Este processo:
echo - importa o PDF local;
echo - descobre o catalogo oficial Marvel;
echo - enriquece todos os perfis encontrados;
echo - salva imagens e dados no cache LOCAL;
echo - nao envia o PDF nem as imagens ao GitHub.
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente .venv nao encontrado.
    echo Execute a instalacao normal da STAR antes deste passo.
    pause
    exit /b 1
)

where tesseract >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Tesseract nao foi encontrado no PATH.
    echo O PDF Marvel enviado e escaneado; OCR e necessario para extrair suas fichas.
    echo Instale/configure o Tesseract e execute este arquivo novamente.
    pause
    exit /b 1
)

set "MARVEL_PDF=%~1"
if "%MARVEL_PDF%"=="" (
    set /p "MARVEL_PDF=Arraste o PDF Marvel para esta janela e pressione ENTER: "
)

set "MARVEL_PDF=%MARVEL_PDF:"=%"
if not exist "%MARVEL_PDF%" (
    echo [ERRO] PDF nao encontrado: %MARVEL_PDF%
    pause
    exit /b 1
)

echo.
echo [STAR] Construindo catalogo Marvel completo...
".venv\Scripts\python.exe" tools\build_heroes_island.py ^
  --marvel-pdf "%MARVEL_PDF%" ^
  --online ^
  --marvel-catalog-max-pages 120

if errorlevel 1 (
    echo.
    echo [ERRO] A atualizacao do catalogo falhou. Consulte os logs acima.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   CATALOGO MARVEL ATUALIZADO
echo ============================================================
echo Relatorio:
echo knowledge\local\reports\heroes_build_report.json
echo.
pause
