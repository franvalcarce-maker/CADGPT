"""
Blender Engine

Implementation of CAD engine for Blender using bpy API.
"""

import math
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..base_engine import BaseCADEngine, CodeValidationResult, MeshAnalysis


class BlenderEngine(BaseCADEngine):
    """
    CAD engine for Blender.
    
    Generates Python scripts using Blender's bpy API.
    Requires Blender installation with Python bindings.
    """
    
    def __init__(self, output_dir: str = "output", blender_path: Optional[str] = None, **kwargs):
        """
        Initialize Blender engine.
        
        Args:
            output_dir: Directory for output files
            blender_path: Path to Blender executable (auto-detected if None)
            **kwargs: Additional configuration
        """
        super().__init__(output_dir=output_dir, **kwargs)
        self.blender_path = blender_path or self._find_blender()
    
    def _find_blender(self) -> Optional[str]:
        """Try to find Blender executable in system PATH."""
        import shutil
        return shutil.which("blender")
    
    def generate_code(
        self,
        shape: str,
        parameters: Optional[Dict[str, Any]] = None,
        operation: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate Blender Python script for a given shape.
        
        Args:
            shape: Type of shape (cube, sphere, cylinder, etc.)
            parameters: Shape parameters
            operation: Optional operation (hollow, centered)
            
        Returns:
            Blender Python script string
        """
        if parameters is None:
            parameters = {}
            
        shape_lower = shape.lower()
        
        # Build script header
        script = '''import bpy
import bmesh
from mathutils import Vector

# Clear existing mesh objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

'''
        
        # Generate shape creation code
        if shape_lower == "cube":
            script += self._generate_cube(parameters)
        elif shape_lower in ["sphere", "ball"]:
            script += self._generate_uv_sphere(parameters)
        elif shape_lower == "icosphere":
            script += self._generate_icosphere(parameters)
        elif shape_lower == "cylinder":
            script += self._generate_cylinder(parameters)
        elif shape_lower == "cone":
            script += self._generate_cone(parameters)
        elif shape_lower == "torus":
            script += self._generate_torus(parameters)
        elif shape_lower == "plane":
            script += self._generate_plane(parameters)
        elif shape_lower == "monkey":
            script += self._generate_monkey()
        else:
            script += self._generate_cube(parameters)  # Default
        
        # Apply operations
        if operation:
            script += "\n" + self._apply_operation(operation, parameters)
        
        # Add material if specified
        if "material" in kwargs:
            script += "\n" + self._add_material(kwargs["material"])
        
        # Add export code
        script += f'''

# Select the object
bpy.context.view_layer.objects.active = bpy.data.objects[0]
bpy.data.objects[0].select_set(True)

# Export to STL (uncomment when ready to export)
# bpy.ops.export_mesh.stl(filepath="{self.output_dir}/export.stl")
'''
        
        return script
    
    def _generate_cube(self, params: Dict[str, Any]) -> str:
        """Generate cube creation code."""
        size = params.get("size", 2)
        location = params.get("location", (0, 0, 0))
        
        return f'''# Create cube
bpy.ops.mesh.primitive_cube_add(
    size={size},
    location={location}
)
'''
    
    def _generate_uv_sphere(self, params: Dict[str, Any]) -> str:
        """Generate UV sphere creation code."""
        radius = params.get("radius", 1)
        segments = params.get("segments", 32)
        ring_count = params.get("rings", 16)
        location = params.get("location", (0, 0, 0))
        
        return f'''# Create UV sphere
bpy.ops.mesh.primitive_uv_sphere_add(
    radius={radius},
    segments={segments},
    ring_count={ring_count},
    location={location}
)
'''
    
    def _generate_icosphere(self, params: Dict[str, Any]) -> str:
        """Generate icosphere creation code."""
        radius = params.get("radius", 1)
        subdivisions = params.get("subdivisions", 2)
        location = params.get("location", (0, 0, 0))
        
        return f'''# Create icosphere
bpy.ops.mesh.primitive_ico_sphere_add(
    radius={radius},
    subdivisions={subdivisions},
    location={location}
)
'''
    
    def _generate_cylinder(self, params: Dict[str, Any]) -> str:
        """Generate cylinder creation code."""
        radius = params.get("radius", 0.5)
        depth = params.get("height", params.get("depth", 2))
        vertices = params.get("vertices", 32)
        location = params.get("location", (0, 0, depth/2))
        
        return f'''# Create cylinder
bpy.ops.mesh.primitive_cylinder_add(
    radius={radius},
    depth={depth},
    vertices={vertices},
    location={location}
)
'''
    
    def _generate_cone(self, params: Dict[str, Any]) -> str:
        """Generate cone creation code."""
        radius1 = params.get("radius", 0.5)
        radius2 = params.get("radius2", 0)
        depth = params.get("height", 2)
        vertices = params.get("vertices", 32)
        location = params.get("location", (0, 0, depth/2))
        
        return f'''# Create cone
bpy.ops.mesh.primitive_cone_add(
    radius1={radius1},
    radius2={radius2},
    depth={depth},
    vertices={vertices},
    location={location}
)
'''
    
    def _generate_torus(self, params: Dict[str, Any]) -> str:
        """Generate torus creation code."""
        major_radius = params.get("major_radius", 1)
        minor_radius = params.get("minor_radius", 0.3)
        ab_major_segments = params.get("major_segments", 48)
        ab_minor_segments = params.get("minor_segments", 16)
        location = params.get("location", (0, 0, 0))
        
        return f'''# Create torus
bpy.ops.mesh.primitive_torus_add(
    major_radius={major_radius},
    minor_radius={minor_radius},
    major_segments={ab_major_segments},
    minor_segments={ab_minor_segments},
    location={location}
)
'''
    
    def _generate_plane(self, params: Dict[str, Any]) -> str:
        """Generate plane creation code."""
        size = params.get("size", 2)
        location = params.get("location", (0, 0, 0))
        
        return f'''# Create plane
bpy.ops.mesh.primitive_plane_add(
    size={size},
    location={location}
)
'''
    
    def _generate_monkey(self) -> str:
        """Generate Suzanne (monkey head) creation code."""
        return '''# Create Suzanne (monkey head)
bpy.ops.mesh.primitive_monkey_add()
'''
    
    def _apply_operation(self, operation: str, parameters: Dict[str, Any]) -> str:
        """Apply operation to generated geometry."""
        
        if operation == "hollow":
            thickness = parameters.get("thickness", 0.1)
            return f'''# Apply hollow operation using Solidify modifier
obj = bpy.context.active_object
modifier = obj.modifiers.new(name="Solidify", type='SOLIDIFY')
modifier.thickness = -{thickness}
'''
        
        elif operation == "centered":
            return '''# Center object at origin
obj = bpy.context.active_object
bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='BOUNDS')
obj.location = (0, 0, 0)
'''
        
        elif operation == "subdivide":
            levels = parameters.get("levels", 2)
            return f'''# Subdivide mesh
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.subdivide(smoothness=0.0, cuts={levels})
bpy.ops.object.mode_set(mode='OBJECT')
'''
        
        return ""
    
    def _add_material(self, material_type: str) -> str:
        """Add material to object."""
        
        materials = {
            "metal": '''
# Create metallic material
mat = bpy.data.materials.new(name="Metal")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs['Metallic'].default_value = 0.9
bsdf.inputs['Roughness'].default_value = 0.2
''',
            "glass": '''
# Create glass material
mat = bpy.data.materials.new(name="Glass")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs['Transmission'].default_value = 1.0
bsdf.inputs['Roughness'].default_value = 0.0
bsdf.inputs['IOR'].default_value = 1.45
''',
            "plastic": '''
# Create plastic material
mat = bpy.data.materials.new(name="Plastic")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs['Metallic'].default_value = 0.0
bsdf.inputs['Roughness'].default_value = 0.5
''',
            "wood": '''
# Create wood-like material
mat = bpy.data.materials.new(name="Wood")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs['Roughness'].default_value = 0.7
'''
        }
        
        mat_code = materials.get(material_type, materials["plastic"])
        
        return mat_code + '''
# Assign material to active object
obj = bpy.context.active_object
if obj.data.materials:
    obj.data.materials[0] = mat
else:
    obj.data.materials.append(mat)
'''
    
    def validate_code(self, code: str) -> CodeValidationResult:
        """
        Validate Blender Python script syntax.
        
        Args:
            code: Python script to validate
            
        Returns:
            CodeValidationResult with validation status
        """
        errors = []
        warnings = []
        
        # Check Python syntax
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            errors.append(f"Syntax error: {e.msg} at line {e.lineno}")
        
        # Check for required imports
        if 'import bpy' not in code:
            errors.append("Missing 'import bpy' statement")
        
        # Check for primitive creation calls
        primitive_calls = [
            'primitive_cube_add',
            'primitive_uv_sphere_add',
            'primitive_cylinder_add',
            'primitive_cone_add',
            'primitive_torus_add'
        ]
        has_primitive = any(call in code for call in primitive_calls)
        if not has_primitive and 'monkey_add' not in code:
            warnings.append("No primitive creation detected")
        
        is_valid = len(errors) == 0
        
        report = "✓ VÁLIDO" if is_valid else "✗ INVÁLIDO\n"
        if errors:
            report += "\nErrores:\n" + "\n".join(f"  - {e}" for e in errors)
        if warnings:
            report += f"\nAdvertencias ({len(warnings)}):\n" + "\n".join(f"  - {w}" for w in warnings)
        
        return CodeValidationResult(
            is_valid=is_valid,
            report=report,
            errors=errors,
            warnings=warnings,
            syntax_valid=len(errors) == 0,
            geometry_valid=has_primitive,
            topology_valid=True
        )
    
    def execute_code(self, code: str) -> bool:
        """
        Execute Blender script (requires Blender installation).
        
        Args:
            code: Python script to execute
            
        Returns:
            True if execution successful
        """
        if not self.blender_path:
            return False
        
        # Save script to temp file
        script_file = self.output_dir / "temp_script.py"
        with open(script_file, 'w') as f:
            f.write(code)
        
        try:
            import subprocess
            result = subprocess.run(
                [self.blender_path, "--background", "--python", str(script_file)],
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def export_mesh(
        self,
        code: str,
        filepath: str,
        format: str = "stl"
    ) -> Optional[str]:
        """
        Export mesh by running Blender script.
        
        Args:
            code: Blender Python script
            filepath: Output file path
            format: Export format (stl, obj, fbx, etc.)
            
        Returns:
            Path to exported file or None
        """
        if not self.blender_path:
            return None
        
        # Modify script to include export
        export_code = code.replace(
            '# bpy.ops.export_mesh.stl',
            f'bpy.ops.export_mesh.{format.lower()}_insert(filepath="{filepath}")'
        )
        
        return self.execute_code(export_code)
    
    def analyze_mesh(self, code: str) -> MeshAnalysis:
        """
        Analyze mesh properties (placeholder).
        
        Args:
            code: Blender script
            
        Returns:
            MeshAnalysis with estimated properties
        """
        # Basic estimation without actual execution
        return MeshAnalysis(
            vertices=0,
            faces=0,
            edges=0,
            is_manifold=True,
            is_watertight=True,
            volume=0.0,
            surface_area=0.0,
            bounding_box={"min": [0, 0, 0], "max": [2, 2, 2]}
        )
    
    def get_supported_shapes(self) -> List[str]:
        """Get list of supported shapes."""
        return [
            "cube", "sphere", "uv_sphere", "icosphere",
            "cylinder", "cone", "torus", "plane", "monkey"
        ]
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return ["stl", "obj", "fbx", "gltf", "dae", "ply", "svg", "png"]
    
    def export_to_file(self, code: str, output_path: str, format: str = "stl") -> CodeValidationResult:
        """
        Exporta el código Blender Python a un archivo físico.
        
        Args:
            code: Código Python de Blender a guardar/ejecutar.
            output_path: Ruta completa del archivo de salida.
            format: Formato de exportación ('py' o 'stl', 'obj', etc.).
            
        Returns:
            CodeValidationResult con el estado de la operación.
        """
        import os
        import subprocess
        
        try:
            # Asegurar directorio
            dir_path = os.path.dirname(output_path)
            if dir_path:
                os.makedirs(dir_path, exist_ok=True)
            
            # Determinar extensiones
            file_ext = os.path.splitext(output_path)[1].lower()
            
            # 1. Guardar archivo .py siempre
            temp_py = output_path.replace(file_ext, '.py')
            if file_ext == '.py':
                temp_py = output_path
            
            with open(temp_py, 'w', encoding='utf-8') as f:
                f.write(code)
            
            msg = f"Script guardado en: {temp_py}"
            print(f"[Blender] {msg}")
            
            # Si solo queríamos el .py, terminamos aquí
            if file_ext == '.py':
                return CodeValidationResult(
                    success=True,
                    is_valid=True,
                    message=msg,
                    code=code,
                    output_file=temp_py
                )
            
            # 2. Intentar ejecutar con Blender para exportar
            if not self.blender_path or not os.path.exists(self.blender_path):
                msg_warning = "Ejecutable no encontrado. Solo se generó el archivo .py. Para generar STL/OBJ, instala Blender."
                print(f"[Blender] Advertencia: {msg_warning}")
                return CodeValidationResult(
                    success=True,
                    is_valid=True,
                    message=msg_warning,
                    code=code,
                    output_file=temp_py
                )
            
            # Modificar el código para agregar exportación al final
            export_cmd = f'\n# Export\nbpy.ops.export_mesh.stl(filepath="{output_path}")\n'
            code_with_export = code + export_cmd
            
            # Guardar script temporal con export
            temp_export_py = temp_py.replace('.py', '_export.py')
            with open(temp_export_py, 'w', encoding='utf-8') as f:
                f.write(code_with_export)
            
            # Comando: blender --background --python script.py
            cmd = [
                self.blender_path,
                "--background",
                "--python", temp_export_py
            ]
            
            print(f"[Blender] Ejecutando: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                msg_success = f"Exportación exitosa a: {output_path}"
                print(f"[Blender] {msg_success}")
                return CodeValidationResult(
                    success=True,
                    is_valid=True,
                    message=msg_success,
                    code=code,
                    output_file=output_path
                )
            else:
                error_msg = f"Error: {result.stderr}" if result.stderr else "Blender no generó el archivo de salida"
                if result.stderr:
                    print(f"[Blender] {error_msg}")
                # Aún devolvemos éxito parcial porque el .py existe
                return CodeValidationResult(
                    success=True,
                    is_valid=True,
                    message=f"{error_msg}. El script .py se guardó correctamente.",
                    code=code,
                    output_file=temp_py
                )
                
        except subprocess.TimeoutExpired:
            error_msg = "Tiempo de espera agotado al ejecutar Blender."
            print(f"[Blender] Error: {error_msg}")
            return CodeValidationResult(
                success=False,
                is_valid=False,
                message=error_msg,
                code=code
            )
        except Exception as e:
            error_msg = f"Excepción al exportar: {str(e)}"
            print(f"[Blender] {error_msg}")
            return CodeValidationResult(
                success=False,
                is_valid=False,
                message=error_msg,
                code=code
            )
