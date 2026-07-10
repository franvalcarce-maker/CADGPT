@echo off
REM CadGPT - Lanzador para Windows
REM Este script inicia la aplicación CadGPT

cd /d "%~dp0"

echo ============================================
echo    CADGPT - Sistema de Diseño Asistido por IA
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

echo Iniciando CadGPT...
echo.

REM Ejecutar el programa principal
python run_cadgpt.py

if errorlevel 1 (
    echo.
    echo ERROR: Ocurrió un problema al ejecutar CadGPT.
    echo Asegúrate de tener instaladas las dependencias:
    echo pip install numpy trimesh pydantic
    pause
)
