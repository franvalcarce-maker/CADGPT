#!/bin/bash
# CadGPT - Lanzador para Linux/Mac
# Este script inicia la interfaz gráfica de CadGPT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "   CADGPT - Sistema de Diseño Asistido por IA"
echo "   Interfaz Gráfica con Chat"
echo "============================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 no está instalado."
    echo "Por favor instala Python3 desde https://www.python.org/"
    exit 1
fi

echo "[OK] Python detectado: $(python3 --version)"
echo ""

# Verificar dependencias
echo "Verificando dependencias..."
if ! python3 -c "import customtkinter" 2>/dev/null; then
    echo "Instalando customtkinter..."
    pip3 install customtkinter packaging
fi

echo "[OK] Dependencias verificadas"
echo ""

# Ejecutar la interfaz gráfica
echo "Iniciando interfaz gráfica de CadGPT..."
echo ""
python3 frontend/gui_app.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Ocurrió un problema al ejecutar CadGPT."
    echo "Asegúrate de tener instaladas las dependencias:"
    echo "pip3 install customtkinter packaging numpy trimesh pydantic"
fi
