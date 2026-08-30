@echo off
cd /d "%~dp0"
if not exist ".voice_venv\Scripts\python.exe" (echo Instale primeiro usando INSTALAR_CHATTERBOX.bat & pause & exit /b 1)
.voice_venv\Scripts\python.exe test_chatterbox_voice.py
pause
