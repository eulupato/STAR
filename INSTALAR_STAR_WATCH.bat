@echo off
setlocal
cd /d "%~dp0"

set "APK=clients\star_watch_android\app\build\outputs\apk\debug\app-debug.apk"

where adb >nul 2>nul
if errorlevel 1 (
    echo [ERRO] ADB nao encontrado no PATH. Instale Android Platform Tools.
    exit /b 1
)

if not exist "%APK%" (
    echo [ERRO] APK nao encontrado em:
    echo %APK%
    echo Gere o APK no Android Studio, Gradle ou GitHub Actions primeiro.
    exit /b 1
)

echo Dispositivos ADB detectados:
adb devices

echo.
echo Instalando STAR Watch...
adb install -r "%APK%"
if errorlevel 1 exit /b 1

echo.
echo STAR Watch instalado com sucesso.
endlocal
