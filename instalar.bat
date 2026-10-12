@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
set "PIP_CACHE_DIR=%~dp0.venv\pip-cache"
echo ===================================================
echo    VICTOR.IA - Instalacion para Windows 10/11
echo ===================================================
echo Se requiere Python 3.11+ de 64 bits e Internet.
echo No ejecutes este instalador como administrador.
if exist ".venv\Scripts\python.exe" goto entorno
set "VICTOR_PY=py -3"
%VICTOR_PY% -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
if not errorlevel 1 goto crear
set "VICTOR_PY=python"
%VICTOR_PY% -c "import sys; assert sys.version_info >= (3,11)" >nul 2>&1
if errorlevel 1 goto falta_python
:crear
%VICTOR_PY% -m venv .venv
if errorlevel 1 goto fallo
:entorno
.venv\Scripts\python.exe -c "import sys; assert sys.version_info >= (3,11)"
if errorlevel 1 goto fallo
.venv\Scripts\python.exe -m pip install --upgrade pip --timeout 30 --retries 2
if errorlevel 1 goto fallo
.venv\Scripts\python.exe -m pip install -r requirements.txt --timeout 30 --retries 2
if errorlevel 1 goto fallo
echo.
echo Instalando funciones opcionales. Si alguna falla, el chat seguira funcionando.
set "VICTOR_OPTIONAL_FAILED=0"
for %%P in ("mss>=9,<11" "pyautogui>=0.9.54,<1" "pygetwindow>=0.0.9,<1" "pyttsx3>=2.98,<3" "SpeechRecognition>=3.14,<4" "sounddevice>=0.5,<1" "numpy>=1.26,<3" "pycaw>=20240210" "pywin32>=306") do (
    .venv\Scripts\python.exe -m pip install %%P --timeout 20 --retries 1
    if errorlevel 1 (
        echo AVISO: No se pudo instalar %%P
        set "VICTOR_OPTIONAL_FAILED=1"
    )
)
if not exist ".env" copy ".env.example" ".env" >nul
.venv\Scripts\python.exe -m compileall -q main.py victor
if errorlevel 1 goto fallo
.venv\Scripts\python.exe -c "from victor.gui.app import GUIManager; from victor.config import ConfigManager; print('Imports principales correctos.')"
if errorlevel 1 goto fallo
echo.
echo Instalacion finalizada. Ejecuta iniciar.bat.
echo Para IA online edita .env y agrega tu clave. Para IA local configura Ollama.
if "%VICTOR_OPTIONAL_FAILED%"=="1" echo Algunas funciones opcionales no se instalaron. Consulta los avisos anteriores.
pause
exit /b 0
:falta_python
echo.
echo No se encontro Python 3.11 o posterior.
echo Instala Python 3.12 de 64 bits desde https://www.python.org/downloads/windows/
echo Marca "Add python.exe to PATH", vuelve a abrir esta carpeta y ejecuta instalar.bat.
pause
exit /b 1
:fallo
echo.
echo La instalacion no termino correctamente. Revisa el error anterior, Internet y Python.
echo Puedes ejecutar instalar.bat de nuevo: reutiliza el entorno y no borra tus datos.
pause
exit /b 1
