import os
import subprocess
import tempfile
import re
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

# Importar la clase base desde la raíz del proyecto
try:
    from ..base_engine import BaseCADEngine, CodeValidationResult
except ImportError:
    # Fallback si hay problemas de ruta relativa
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from base_engine import BaseCADEngine, CodeValidationResult

class OpenSCADEngine(BaseCADEngine):
    """
    Motor CAD para OpenSCAD.
    Implementa todos los métodos abstractos requeridos por BaseCADEngine.
    """

    def __init__(self):
        super().__init__()
        self.engine_name = "OpenSCAD"
        self.supported_extensions = [".scad", ".stl", ".off", ".dxf"]
        
        # Detección robusta de la ruta de OpenSCAD
        self.openscad_path = self._find_openscad_executable()
        self.is_available = bool(self.openscad_path and os.path.exists(self.openscad_path))
        
        if self.is_available:
            print(f"[OK] OpenSCAD encontrado en: {self.openscad_path}")
        else:
            print("[ERROR] OpenSCAD no encontrado. Solo se generará código .scad, no STL.")

    def _find_openscad_executable(self) -> Optional[str]:
        """Busca el ejecutable de OpenSCAD en rutas comunes de Windows."""
        candidates = [
            r"C:\Program Files\OpenSCAD\openscad.exe",
            r"C:\Program Files (x86)\OpenSCAD\openscad.exe",
            os.path.join(os.environ.get("PROGRAMFILES", ""), "OpenSCAD", "openscad.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "OpenSCAD", "openscad.exe"),
        ]
        
        env_path = os.environ.get("OPENSCAD_PATH")
        if env_path:
            candidates.insert(0, env_path)

        for path in candidates:
            if os.path.isfile(path):
                return path
        
        return None

    # ------------------------------------------------------------------
    # IMPLEMENTACIÓN DE MÉTODOS ABSTRACTOS
    # ------------------------------------------------------------------

    def generate_code(self, shape_type: str, parameters: Dict[str, Any]) -> CodeValidationResult:
        """Genera código OpenSCAD básico basado en tipo y parámetros."""
        try:
            code = ""
            shape = shape_type.lower()
            
            if shape == "cube":
                size = parameters.get("size", 10)
                center = parameters.get("center", "false")
                code = f'cube([{size}, {size}, {size}], center={center});'
            elif shape == "sphere":
                radius = parameters.get("radius", 10)
                code = f'sphere(r={radius});'
            elif shape == "cylinder":
                h = parameters.get("height", 20)
                r = parameters.get("radius", 5)
                code = f'cylinder(h={h}, r={r});'
            else:
                code = f'// Forma {shape_type} no reconocida específicamente.\ncube([10,10,10]);'

            is_valid = self._validate_syntax(code)
            
            return CodeValidationResult(
                success=is_valid,
                message="Código generado exitosamente",
                code=code,
                is_valid=is_valid
            )
        except Exception as e:
            return CodeValidationResult(success=False, message=f"Error generando código: {str(e)}", code="")

    def validate_code(self, code: str) -> CodeValidationResult:
        """
        Valida la sintaxis del código OpenSCAD llamando al compilador.
        Implementación del método abstracto requerido.
        """
        if not self.is_available:
            # Validación estática básica si no hay ejecutable
            is_valid = self._validate_syntax(code)
            msg = "Validación estática (sintaxis básica)" if is_valid else "Sintaxis inválida detectada"
            return CodeValidationResult(success=is_valid, message=msg, code=code, is_valid=is_valid)

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
                f.write(code)
                temp_scad = f.name

            # Intentar compilar sin generar archivo final (o generando en NUL)
            cmd = [
                self.openscad_path,
                "-o", "NUL",
                temp_scad
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            os.unlink(temp_scad)

            if result.returncode == 0:
                return CodeValidationResult(success=True, message="Código válido y compilable", code=code, is_valid=True)
            else:
                error_msg = result.stderr.strip() or "Error de compilación desconocido"
                return CodeValidationResult(success=False, message=f"Error de validación: {error_msg}", code=code, is_valid=False)

        except subprocess.TimeoutExpired:
            return CodeValidationResult(success=False, message="Tiempo de espera agotado al validar", code=code, is_valid=False)
        except Exception as e:
            return CodeValidationResult(success=False, message=f"Excepción al validar: {str(e)}", code=code, is_valid=False)

    def execute_code(self, code: str) -> CodeValidationResult:
        """
        Ejecuta el código (alias para validate_code en este contexto, 
        pero puede extenderse para visualizar).
        """
        return self.validate_code(code)

    def export_mesh(self, code: str, output_path: str, format: str = "stl") -> CodeValidationResult:
        """
        Exporta el código a un archivo de malla (STL, OFF, etc.).
        """
        if not self.is_available:
            return CodeValidationResult(
                success=False, 
                message="Motor OpenSCAD no disponible. No se puede exportar a malla.",
                code=code,
                is_valid=False
            )

        try:
            if not output_path.lower().endswith(f".{format}"):
                output_path = f"{output_path}.{format}"
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.scad', delete=False) as f:
                f.write(code)
                temp_scad = f.name

            cmd = [
                self.openscad_path,
                "-o", output_path,
                "--export-format", format,
                temp_scad
            ]

            process = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            os.unlink(temp_scad)

            if process.returncode == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                if file_size > 0:
                    return CodeValidationResult(
                        success=True, 
                        message=f"Malla exportada exitosamente a {output_path}",
                        code=code,
                        is_valid=True,
                        output_file=output_path
                    )
                else:
                    return CodeValidationResult(success=False, message="Archivo generado vacío", code=code, is_valid=False)
            else:
                error_log = process.stderr.strip() or "Error silencioso"
                return CodeValidationResult(success=False, message=f"Fallo al exportar: {error_log}", code=code, is_valid=False)

        except subprocess.TimeoutExpired:
            return CodeValidationResult(success=False, message="Tiempo de espera agotado", code=code, is_valid=False)
        except Exception as e:
            return CodeValidationResult(success=False, message=f"Error crítico: {str(e)}", code=code, is_valid=False)

    def analyze_mesh(self, mesh_data: Any) -> Dict[str, Any]:
        """
        Analiza propiedades geométricas de una malla (requiere trimesh).
        """
        try:
            import trimesh
            
            if isinstance(mesh_data, str) and os.path.exists(mesh_data):
                mesh = trimesh.load(mesh_data)
            elif hasattr(mesh_data, 'vertices'):
                mesh = mesh_data
            else:
                return {"error": "Formato de datos no reconocido"}

            return {
                "volume": float(mesh.volume),
                "area": float(mesh.area),
                "vertices_count": len(mesh.vertices),
                "faces_count": len(mesh.faces),
                "is_watertight": mesh.is_watertight,
                "bounding_box": mesh.bounding_box.extents.tolist(),
                "is_manifold": mesh.is_volume
            }
        except ImportError:
            return {"error": "Librería 'trimesh' no instalada."}
        except Exception as e:
            return {"error": f"Fallo al analizar: {str(e)}"}

    # ------------------------------------------------------------------
    # MÉTODOS AUXILIARES
    # ------------------------------------------------------------------

    def _validate_syntax(self, code: str) -> bool:
        """Validación estática muy básica (llaves, paréntesis)."""
        if not code:
            return False
        if code.count('{') != code.count('}'):
            return False
        if code.count('(') != code.count(')'):
            return False
        if code.count('[') != code.count(']'):
            return False
        return True

    def export_to_file(self, code: str, output_folder: str, filename_base: str) -> Dict[str, Any]:
        """
        Helper completo: Guarda .scad y exporta a .stl
        """
        try:
            os.makedirs(output_folder, exist_ok=True)
            
            scad_path = os.path.join(output_folder, f"{filename_base}.scad")
            with open(scad_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            result_log = f"[OpenSCAD] Código guardado en: {scad_path}\n"
            
            stl_path = os.path.join(output_folder, f"{filename_base}.stl")
            
            if not self.is_available:
                result_log += "[OpenSCAD] Advertencia: Ejecutable no encontrado. Solo .scad generado."
                return {
                    "success": True,
                    "message": result_log,
                    "path": scad_path,
                    "stl_generated": False
                }
            
            export_result = self.export_mesh(code, stl_path, format="stl")
            
            if export_result.success:
                result_log += f"[OpenSCAD] Éxito: STL generado en {stl_path}"
                return {
                    "success": True,
                    "message": result_log,
                    "path": stl_path,
                    "scad_path": scad_path,
                    "stl_generated": True
                }
            else:
                result_log += f"\n[OpenSCAD] Error exportando STL: {export_result.message}"
                return {
                    "success": False,
                    "message": result_log,
                    "path": scad_path,
                    "stl_generated": False
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error crítico: {str(e)}",
                "path": None
            }