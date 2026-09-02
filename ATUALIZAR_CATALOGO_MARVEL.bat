@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo   STAR V3.0 - CATALOGO + IMAGENS DOS HEROIS
echo ============================================================
echo.
echo Este processo:
echo - sincroniza o catalogo mestre Marvel versionado;
echo - procura imagens personagem por personagem;
echo - usa primeiro referencias Marvel ja associadas por ID;
echo - tenta Commons/Wikidata com licenca verificavel;
echo - usa perfil oficial apenas quando ainda nao existe imagem;
echo - registra fonte, credito, direitos e motivo de rejeicao;
echo - salva checkpoint e continua de onde parou;
echo - nao exige PDF nem Tesseract;
echo - nao envia imagens, banco ou dados locais ao GitHub.
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente .venv nao encontrado.
    echo Execute a instalacao normal da STAR antes deste passo.
    pause
    exit /b 1
)

echo [STAR] Atualizando catalogo e imagens...
".venv\Scripts\python.exe" tools\build_heroes_island.py --scan-images

if errorlevel 1 (
    echo.
    echo [ERRO] A atualizacao foi interrompida.
    echo O checkpoint foi preservado.
    echo Execute este arquivo novamente para continuar.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   ATUALIZACAO CONCLUIDA
echo ============================================================
echo Relatorios:
echo knowledge\local\reports\heroes_image_scan_report.json
echo knowledge\local\reports\heroes_image_scan_state.json
echo.
echo Para medir a cobertura atual:
echo .\.venv\Scripts\python.exe tools\build_heroes_island.py --audit-only
echo.
pause
