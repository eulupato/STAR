@echo off
setlocal
cd /d "%~dp0"

echo ================================================
echo      STAR Vision Portal V1 - inicializacao
echo ================================================

python -c "import cv2, mediapipe, numpy" >nul 2>&1
if errorlevel 1 (
  echo [STAR] Dependencias de visao ausentes.
  echo [STAR] Instalando requirements-vision.txt...
  python -m pip install -r requirements-vision.txt
  if errorlevel 1 (
    echo [ERRO] Nao foi possivel instalar o modulo de visao.
    pause
    exit /b 1
  )
)

python clients\star_vision_portal.py %*
if errorlevel 1 (
  echo.
  echo [STAR] O portal encerrou com erro. Verifique camera e permissoes.
  pause
)
endlocal
