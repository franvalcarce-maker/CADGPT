import sys
import os
from parser_engine import generate_cadquery_code

# Intentar importar CadQuery para procesar el modelado tridimensional
try:
    import cadquery as cq
except ImportError:
    cq = None

def run_cadgpt():
    print("="*55)
    print("  CadGPT v2.0 - Motor de Modelado 3D Inteligente (CadQuery)")
    print("  Escribí lo que quieras diseñar (ej: 'Haceme una silla')")
    print("="*55)

    while True:
        try:
            user_input = input("\nCadGPT > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("Cerrando CadGPT. ¡Adiós!")
                break

            # 1. Obtener el script matemático generado por la IA
            script_code = generate_cadquery_code(user_input)

            if not script_code:
                print("[Error] No se pudo generar la lógica CAD.")
                continue

            print("\n[Engine] Código CadQuery Generado:")
            print("-" * 50)
            print(script_code)
            print("-" * 50)

            # 2. Verificar el entorno de ejecución matemático
            if cq is None:
                print("\n[Advertencia] La librería 'cadquery' no está instalada en este entorno Python.")
                print("Guardando el script generado de respaldo en 'output_script.py'.")
                with open("output_script.py", "w", encoding="utf-8") as f:
                    f.write(script_code)
                continue

            print("[Engine] Compilando topología espacial y ejecutando operaciones...")

            # Entorno aislado para inyectar y ejecutar el código de la IA en caliente
            local_vars = {"cq": cq}
            exec(script_code, globals(), local_vars)

            if "result" in local_vars:
                final_shape = local_vars["result"]
                filename = "cadgpt_output.stl"

                print(f"[Engine] Exportando malla tridimensional a '{filename}'...")
                cq.exporters.export(final_shape, filename)
                print("¡Éxito! El archivo 3D ha sido guardado en la carpeta del proyecto.")
            else:
                print("[Error] El script se ejecutó pero no definió la variable global 'result'.")

        except KeyboardInterrupt:
            print("\nSaliendo de CadGPT.")
            break
        except Exception as e:
            print(f"[Error de Ejecución]: {e}")

if __name__ == "__main__":
    run_cadgpt()
