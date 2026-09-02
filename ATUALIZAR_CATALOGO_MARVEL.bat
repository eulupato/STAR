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
echo - tenta enriquecer cada perfil pela fonte oficial Marvel primeiro;
echo - usa Commons/Wikidata licenciado como referencia visual preferida;
echo - aceita referencias oficiais Marvel/DC como fallback documentado;
echo - registra o motivo de cada imagem recusada;
echo - preenche campos estruturados quando a fonte confiavel os fornece;
echo - preserva fontes primarias, proveniencia, autoria e direitos da imagem;
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
".venv\Scripts\python.exe" tools\build_heroes_island.py --online --live-marvel-enrichment --cache-marvel-images --wikidata-fallback

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
echo Consulte "image_rejection_reasons" no JSON para ver por que
echo imagens especificas nao foram aceitas.
echo.
pause
