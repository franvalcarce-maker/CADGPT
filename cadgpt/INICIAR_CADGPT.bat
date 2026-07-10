@echo off
REM CadGPT - Lanzador para Windows
REM Este script inicia la interfaz gráfica de CadGPT

cd /d "%~dp0"

echo ============================================
echo    CADGPT - Sistema de Diseño Asistido por IA
echo    Interfaz Gráfica con Chat
echo ============================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH.
    echo Por favor instala Python desde https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python detectado
echo.

REM Verificar e instalar dependencias
echo Verificando dependencias...
pip show customtkinter >nul 2>&1
if errorlevel 1 (
    echo Instalando customtkinter...
    pip install customtkinter packaging
)

echo [OK] Dependencias verificadas
echo.

REM Ejecutar la interfaz gráfica
echo Iniciando interfaz gráfica de CadGPT...
echo.
python frontend/gui_app.py

if errorlevel 1 (
    echo.
    echo ERROR: Ocurrió un problema al ejecutar CadGPT.
    echo Asegúrate de tener instaladas las dependencias:
    echo pip install customtkinter packaging numpy trimesh pydantic
    pause
)
