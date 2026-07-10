#!/bin/bash
# CadGPT - Lanzador para Linux/Mac
# Este script inicia la aplicación CadGPT

cd "$(dirname "$0")"

echo "============================================"
echo "   CADGPT - Sistema de Diseño Asistido por IA"
echo "============================================"
echo ""

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 no está instalado."
    echo "Por favor instala Python3 desde tu gestor de paquetes."
    exit 1
fi

echo "Iniciando CadGPT..."
echo ""

# Ejecutar el programa principal
python3 run_cadgpt.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Ocurrió un problema al ejecutar CadGPT."
    echo "Asegúrate de tener instaladas las dependencias:"
    echo "pip install numpy trimesh pydantic"
fi
