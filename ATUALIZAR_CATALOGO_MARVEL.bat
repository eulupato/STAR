@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo   STAR V3.0 - SINCRONIZAR CATALOGO MARVEL
echo ============================================================
echo.
echo Este processo:
echo - importa o catalogo mestre Marvel versionado no GitHub;
echo - remove somente residuos Marvel criados pelo antigo OCR sem fonte confiavel;
echo - baixa referencias visuais Marvel para o cache LOCAL;
echo - tenta preencher descricoes/imagens ausentes via Wikidata/Commons;
echo - preserva fontes primarias e registra proveniencia/atribuicao;
echo - nao exige PDF nem Tesseract;
echo - nao envia imagens, banco ou dados locais ao GitHub.
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente .venv nao encontrado.
    echo Execute a instalacao normal da STAR antes deste passo.
    pause
    exit /b 1
)

echo [STAR] Sincronizando identidades e imagens Marvel...
".venv\Scripts\python.exe" tools\build_heroes_island.py --cache-marvel-images --wikidata-fallback

if errorlevel 1 (
    echo.
    echo [ERRO] A sincronizacao do catalogo falhou. Consulte os logs acima.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   CATALOGO MARVEL SINCRONIZADO
echo ============================================================
echo Relatorio:
echo knowledge\local\reports\heroes_build_report.json
echo.
pause
