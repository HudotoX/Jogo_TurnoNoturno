@echo off
setlocal EnableExtensions
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 goto :try_python
set "PY_CMD=py -3"
goto :python_found

:try_python
where python >nul 2>nul
if errorlevel 1 goto :no_python
set "PY_CMD=python"

:python_found
echo Python encontrado:
%PY_CMD% --version

set "VENV_DIR=.build-venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo Criando ambiente isolado de build...
    %PY_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 goto :venv_error
)

echo Atualizando as ferramentas de instalacao...
"%VENV_PY%" -m pip install --disable-pip-version-check --upgrade pip setuptools wheel
if errorlevel 1 goto :dependency_error

rem Evita conflito se uma tentativa antiga instalou o pygame original.
"%VENV_PY%" -m pip uninstall --disable-pip-version-check -y pygame >nul 2>nul

echo Instalando dependencias binarias compativeis...
"%VENV_PY%" -m pip install --disable-pip-version-check --upgrade --only-binary=:all: -r requirements.txt -r requirements-build.txt
if errorlevel 1 goto :dependency_error

echo Conferindo Pygame...
"%VENV_PY%" -c "import pygame; print('Pygame', pygame.version.ver); assert pygame.IS_CE"
if errorlevel 1 goto :dependency_error

echo Gerando executavel...
"%VENV_PY%" -m PyInstaller --clean --noconfirm turno_noturno.spec
if errorlevel 1 goto :build_error

echo.
echo Build concluida em dist\TurnoNoturno\TurnoNoturno.exe
echo Copie a pasta TurnoNoturno inteira para o computador da feira.
pause
exit /b 0

:no_python
echo.
echo Python 3 nao foi encontrado. Instale pelo site python.org e tente novamente.
pause
exit /b 1

:venv_error
echo.
echo Nao foi possivel criar o ambiente isolado em %VENV_DIR%.
echo Feche programas que estejam usando essa pasta e tente novamente.
pause
exit /b 1

:dependency_error
echo.
echo Falha ao instalar as dependencias binarias.
echo Verifique a conexao com a internet e tente novamente.
echo Se a pasta %VENV_DIR% veio de outra maquina, apague-a e rode este arquivo outra vez.
pause
exit /b 1

:build_error
echo.
echo As dependencias foram instaladas, mas o PyInstaller nao concluiu a build.
echo Envie as ultimas linhas exibidas acima para diagnostico.
pause
exit /b 1
