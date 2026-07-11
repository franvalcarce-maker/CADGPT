#!/usr/bin/env python3
"""
CadGPT - Lanzador Principal
Interfaz de usuario simplificada para interactuar con los agentes CAD.
"""

import os
import sys
import time
from pathlib import Path

# Asegurar que el directorio raíz esté en el path
ROOT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(ROOT_DIR))

from core.orchestration.agent_orchestrator import AgentOrchestrator
from cad_engines import create_engine

def print_banner():
    print("\n" + "="*60)
    print("   CADGPT - Sistema de Diseño Asistido por IA")
    print("   Fase 2: OpenSCAD | Blender | FreeCAD")
    print("="*60 + "\n")

def get_user_choice():
    print("Selecciona el motor CAD:")
    print("1. OpenSCAD (Recomendado para MVP)")
    print("2. Blender (Python API)")
    print("3. FreeCAD (Part Workbench)")
    print("4. Salir")
    
    while True:
        choice = input("\nOpción [1-4]: ").strip()
        if choice in ['1', '2', '3', '4']:
            return choice
        print("Por favor, elige una opción válida (1-4).")

def main():
    print_banner()
    
    # Inicializar orquestador
    try:
        orchestrator = AgentOrchestrator()
        print("✓ Sistema inicializado correctamente.")
    except Exception as e:
        print(f"⚠ Error al inicializar el sistema: {e}")
        print("Continuando en modo limitado...")
        orchestrator = None

    while True:
        choice = get_user_choice()
        
        if choice == '4':
            print("\n👋 Saliendo de CadGPT. ¡Hasta luego!")
            break
        
        engine_map = {
            '1': 'openscad',
            '2': 'blender',
            '3': 'freecad'
        }
        
        engine_name = engine_map[choice]
        print(f"\n🔧 Iniciando motor: {engine_name.upper()}...")
        
        try:
            engine = create_engine(engine_name)
            print(f"✓ Motor {engine_name} listo.")
        except Exception as e:
            print(f"❌ Error cargando el motor: {e}")
            continue

        # Solicitar instrucción al usuario
        print("\n💡 Ejemplos de instrucciones:")
        if engine_name == 'openscad':
            print("   - 'Genera un cubo de 50 mm'")
            print("   - 'Crea una esfera hueca de 10 cm de diámetro'")
        elif engine_name == 'blender':
            print("   - 'Crea un cilindro metálico de 2 metros'")
            print("   - 'Genera una mesa con patas de madera'")
        else:  # freecad
            print("   - 'Diseña una caja de 100x50x30 mm'")
            print("   - 'Crea un tubo de 20 mm de diámetro'")
        
        prompt = input("\n📝 Tu instrucción: ").strip()
        
        if not prompt:
            print("⚠ Instrucción vacía. Inténtalo de nuevo.")
            continue
            
        print("\n⏳ Procesando solicitud...")
        
        try:
            # Simular proceso de generación (en fase futura se conectará al LLM real)
            # Por ahora usamos el parser interno del motor para demo
            result = engine.generate_code(prompt)
            
            if result and 'code' in result:
                print("\n✅ ¡Código generado exitosamente!")
                print("-" * 40)
                print(result['code'])
                print("-" * 40)
                
                # Validar
                if 'validation' in result:
                    status = "✅ VÁLIDO" if result['validation']['is_valid'] else "❌ INVÁLIDO"
                    print(f"\n🛡️ Validación: {status}")
                    if not result['validation']['is_valid']:
                        print(f"   Errores: {result['validation'].get('errors', 'Desconocido')}")
                
                # Preguntar si quiere exportar
                save_choice = input("\n💾 ¿Guardar archivo? (s/n): ").strip().lower()
                if save_choice == 's':
                    filename = input("Nombre del archivo (sin extensión): ").strip() or "modelo_cadgpt"
                    
                    # Determinar extensión por defecto
                    ext_map = {'openscad': '.scad', 'blender': '.py', 'freecad': '.py'}
                    full_path = ROOT_DIR / "output" / f"{filename}{ext_map[engine_name]}"
                    
                    # Guardar código
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write(result['code'])
                    print(f"💾 Archivo guardado en: {full_path}")
                    
                    # Intentar exportar a STL si el motor lo soporta y está configurado
                    if hasattr(engine, 'export_to_stl'):
                        stl_path = ROOT_DIR / "output" / f"{filename}.stl"
                        print(f"⏳ Exportando a STL...")
                        try:
                            # Nota: Esto requiere tener el software instalado (OpenSCAD/Blender/FreeCAD)
                            # En esta demo solo mostramos el mensaje si no está instalado
                            print("⚠ Para exportar a STL real, asegúrate de tener el software instalado y configurado.")
                        except Exception as exp_err:
                            print(f"⚠ Error exportando STL: {exp_err}")
                else:
                    print("⏭️ Archivo no guardado.")
            else:
                print("❌ No se pudo generar el código. Verifica la instrucción.")
                
        except Exception as e:
            print(f"❌ Error durante el procesamiento: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "-"*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Interrumpido por el usuario.")
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        input("Presiona Enter para salir...")
