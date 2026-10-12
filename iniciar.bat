@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Primero ejecuta instalar.bat.
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat
python main.py %*
if errorlevel 1 (
    echo.
    echo VICTOR.IA no pudo arrancar. Revisa el mensaje anterior y data\victor.log.
    pause
    exit /b 1
)
endlocal
