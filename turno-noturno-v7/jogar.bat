@echo off
setlocal
cd /d "%~dp0"

if exist "dist\TurnoNoturno\TurnoNoturno.exe" (
    "dist\TurnoNoturno\TurnoNoturno.exe"
    exit /b %errorlevel%
)

if exist ".build-venv\Scripts\python.exe" (
    ".build-venv\Scripts\python.exe" main.py
    if not errorlevel 1 exit /b 0
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3 main.py
    if not errorlevel 1 exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
    python main.py
    if not errorlevel 1 exit /b 0
)

echo Nao encontrei a build nem uma instalacao funcional do Python.
echo Rode build_windows.bat antes de levar o jogo para a feira.
pause
exit /b 1
