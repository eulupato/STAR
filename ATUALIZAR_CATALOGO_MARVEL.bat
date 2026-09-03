@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo   STAR V3.0 - DADOS + IMAGENS DOS HEROIS
echo ============================================================
echo.
echo Este processo:
echo - sincroniza o catalogo mestre Marvel versionado;
echo - preenche dados estruturados das fichas via Wikidata/Wikipedia;
echo - depois procura imagens personagem por personagem;
echo - usa referencias Marvel ja associadas por ID;
echo - tenta Commons/Wikidata com licenca verificavel;
echo - nao consulta Marvel/DC live por padrao;
echo - salva checkpoints e pode continuar de onde parou.
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente .venv nao encontrado.
    pause
    exit /b 1
)

echo [STAR] Fase 1/2 - atualizando dados das fichas...
".venv\Scripts\python.exe" tools\build_heroes_island.py --scan-data
if errorlevel 1 (
    echo.
    echo [ERRO] A fase de dados foi interrompida.
    echo Execute novamente para continuar do checkpoint.
    pause
    exit /b 1
)

echo.
echo [STAR] Fase 2/2 - atualizando imagens...
".venv\Scripts\python.exe" tools\build_heroes_island.py --scan-images
if errorlevel 1 (
    echo.
    echo [ERRO] A fase de imagens foi interrompida.
    echo Execute novamente para continuar do checkpoint.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   ATUALIZACAO CONCLUIDA
echo ============================================================
echo Relatorios:
echo knowledge\local\reports\heroes_data_scan_report.json
echo knowledge\local\reports\heroes_image_scan_report.json
echo.
pause
