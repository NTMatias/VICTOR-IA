@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Primero ejecuta instalar.bat.
    pause
    exit /b 1
)
rem Usar este entorno directamente: activate.bat puede conservar una ruta antigua.
"%~dp0.venv\Scripts\python.exe" "%~dp0main.py" %*
if errorlevel 1 (
    echo.
    echo VICTOR.IA no pudo arrancar. Revisa el mensaje anterior y data\victor.log.
    pause
    exit /b 1
)
endlocal
