@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo ERROR: falta .venv. Ejecuta instalar.bat primero.
  exit /b 1
)
".venv\Scripts\python.exe" -m compileall -q main.py victor tests
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -c "from victor.config import ConfigManager; from victor.core import VictorCore; from victor.gui.app import GUIManager; from victor.voice.input import VoiceInput; from victor.integrations.local_remote import LocalRemote; print('OK: entorno, compilacion e imports esenciales. Servicios y dispositivos no comprobados.')"
if errorlevel 1 exit /b 1
if /i not "%~1"=="--sin-pausa" pause
exit /b 0
