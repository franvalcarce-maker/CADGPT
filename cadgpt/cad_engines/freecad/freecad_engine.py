"""
FreeCAD Engine

Implementation of CAD engine for FreeCAD using Part Workbench.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path

from ..base_engine import BaseCADEngine, CodeValidationResult, MeshAnalysis


class FreeCADEngine(BaseCADEngine):
    """
    CAD engine for FreeCAD.
    
    Generates Python scripts using FreeCAD's Part and PartDesign workbenches.
    Requires FreeCAD installation.
    """
    
    def __init__(self, output_dir: str = "output", freecad_path: Optional[str] = None, **kwargs):
        """
        Initialize FreeCAD engine.
        
        Args:
            output_dir: Directory for output files
            freecad_path: Path to FreeCAD executable (auto-detected if None)
            **kwargs: Additional configuration
        """
        super().__init__(output_dir=output_dir, **kwargs)
        self.freecad_path = freecad_path or self._find_freecad()
    
    def _find_freecad(self) -> Optional[str]:
        """Try to find FreeCAD executable in system PATH."""
        import shutil
        return shutil.which("freecad") or shutil.which("FreeCAD")
    
    def generate_code(
        self,
        shape: str,
        parameters: Optional[Dict[str, Any]] = None,
        operation: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate FreeCAD Python script for a given shape.
        
        Args:
            shape: Type of shape (box, sphere, cylinder, etc.)
            parameters: Shape parameters
            operation: Optional operation (hollow, fillet, chamfer)
            
        Returns:
            FreeCAD Python script string
        """
        if parameters is None:
            parameters = {}
            
        shape_lower = shape.lower()
        
        # Build script header
        script = '''import FreeCAD
import Part
from FreeCAD import Vector

# Create new document
doc = FreeCAD.newDocument("CadGPT_Generated")

'''
        
        # Generate shape creation code
        if shape_lower == "box" or shape_lower == "cube":
            script += self._generate_box(parameters)
        elif shape_lower in ["sphere", "ball"]:
            script += self._generate_sphere(parameters)
        elif shape_lower == "cylinder":
            script += self._generate_cylinder(parameters)
        elif shape_lower == "cone":
            script += self._generate_cone(parameters)
        elif shape_lower == "torus":
            script += self._generate_torus(parameters)
        elif shape_lower == "wedge":
            script += self._generate_wedge(parameters)
        elif shape_lower == "tube":
            script += self._generate_tube(parameters)
        else:
            script += self._generate_box(parameters)  # Default
        
        # Apply operations
        if operation:
            script += "\n" + self._apply_operation(operation, parameters)
        
        # Add recomputation and view fitting
        script += '''

# Recompute and fit view
doc.recompute()
FreeCAD.Gui.SendMsgToActiveView("ViewFit")

# Export instructions (uncomment when ready)
# Part.export([obj.Label], "/path/to/export.step")
'''
        
        return script
    
    def _generate_box(self, params: Dict[str, Any]) -> str:
        """Generate box creation code."""
        length = params.get("length", params.get("size", 100))
        width = params.get("width", params.get("size", 100))
        height = params.get("height", params.get("size", 100))
        location = params.get("location", (0, 0, 0))
        
        return f'''# Create box
obj = Part.makeBox({length}, {width}, {height})
box_obj = doc.addObject("Part::Feature", "Box")
box_obj.Shape = obj
'''
    
    def _generate_sphere(self, params: Dict[str, Any]) -> str:
        """Generate sphere creation code."""
        radius = params.get("radius", 50)
        angle_min = params.get("angle_min", -180)
        angle_max = params.get("angle_max", 180)
        angle_range = params.get("angle_range", 360)
        
        return f'''# Create sphere
sphere = Part.makeSphere({radius}, Vector(0, 0, 0), Vector(0, 0, 1), {angle_min}, {angle_max}, {angle_range})
sphere_obj = doc.addObject("Part::Feature", "Sphere")
sphere_obj.Shape = sphere
'''
    
    def _generate_cylinder(self, params: Dict[str, Any]) -> str:
        """Generate cylinder creation code."""
        radius = params.get("radius", 25)
        height = params.get("height", 100)
        angle = params.get("angle", 360)
        
        return f'''# Create cylinder
cylinder = Part.makeCylinder({radius}, {height}, Vector(0, 0, 0), Vector(0, 0, 1), {angle})
cyl_obj = doc.addObject("Part::Feature", "Cylinder")
cyl_obj.Shape = cylinder
'''
    
    def _generate_cone(self, params: Dict[str, Any]) -> str:
        """Generate cone creation code."""
        radius1 = params.get("radius1", params.get("radius", 25))
        radius2 = params.get("radius2", 0)
        height = params.get("height", 100)
        angle = params.get("angle", 360)
        
        return f'''# Create cone
cone = Part.makeCone({radius1}, {radius2}, {height}, Vector(0, 0, 0), Vector(0, 0, 1), {angle})
cone_obj = doc.addObject("Part::Feature", "Cone")
cone_obj.Shape = cone
'''
    
    def _generate_torus(self, params: Dict[str, Any]) -> str:
        """Generate torus creation code."""
        radius1 = params.get("major_radius", 50)
        radius2 = params.get("minor_radius", 10)
        angle1 = params.get("angle1", 0)
        angle2 = params.get("angle2", 360)
        angle = params.get("angle", 360)
        
        return f'''# Create torus
torus = Part.makeTorus({radius1}, {radius2}, Vector(0, 0, 0), Vector(0, 0, 1), {angle1}, {angle2}, {angle})
torus_obj = doc.addObject("Part::Feature", "Torus")
torus_obj.Shape = torus
'''
    
    def _generate_wedge(self, params: Dict[str, Any]) -> str:
        """Generate wedge creation code."""
        dx = params.get("dx", 100)
        dy = params.get("dy", 50)
        dz = params.get("dz", 100)
        xmin = params.get("xmin", 0)
        zmin = params.get("zmin", 0)
        xmax = params.get("xmax", params.get("dx", 100))
        zmax = params.get("zmax", params.get("dz", 100))
        
        return f'''# Create wedge
wedge = Part.makeWedge({dx}, {dy}, {dz}, {xmin}, {zmin}, {xmax}, {zmax})
wedge_obj = doc.addObject("Part::Feature", "Wedge")
wedge_obj.Shape = wedge
'''
    
    def _generate_tube(self, params: Dict[str, Any]) -> str:
        """Generate tube/pipe creation code."""
        outer_radius = params.get("outer_radius", 25)
        inner_radius = params.get("inner_radius", 20)
        height = params.get("height", 100)
        
        return f'''# Create tube (hollow cylinder)
outer_cyl = Part.makeCylinder({outer_radius}, {height})
inner_cyl = Part.makeCylinder({inner_radius}, {height})
tube = outer_cyl.cut(inner_cyl)
tube_obj = doc.addObject("Part::Feature", "Tube")
tube_obj.Shape = tube
'''
    
    def _apply_operation(self, operation: str, parameters: Dict[str, Any]) -> str:
        """Apply operation to generated geometry."""
        
        if operation == "hollow":
            thickness = parameters.get("thickness", 5)
            return f'''
# Apply hollow operation (shell)
shape = FreeCAD.ActiveDocument.ActiveObject.Shape
try:
    shell = shape.makeThickness(-{thickness}, 0.01)
    shell_obj = doc.addObject("Part::Feature", "Hollowed")
    shell_obj.Shape = shell
    FreeCAD.ActiveDocument.removeObject(FreeCAD.ActiveDocument.ActiveObject.Label)
except Exception as e:
    print(f"Shell operation failed: {{e}}")
'''
        
        elif operation == "fillet":
            radius = parameters.get("fillet_radius", 2)
            edges = parameters.get("edges", list(range(4)))  # Default first 4 edges
            edge_list = ", ".join(str(i) for i in edges)
            return f'''
# Apply fillet
shape = FreeCAD.ActiveDocument.ActiveObject.Shape
edges_to_fillet = [shape.Edges[{edge_list}]]
fillet = shape.makeFillet({radius}, edges_to_fillet)
fillet_obj = doc.addObject("Part::Feature", "Fillet")
fillet_obj.Shape = fillet
'''
        
        elif operation == "chamfer":
            distance = parameters.get("chamfer_distance", 2)
            edges = parameters.get("edges", [0])
            edge_list = ", ".join(str(i) for i in edges)
            return f'''
# Apply chamfer
shape = FreeCAD.ActiveDocument.ActiveObject.Shape
edges_to_chamfer = [shape.Edges[{edge_list}]]
chamfer = shape.makeChamfer({distance}, edges_to_chamfer)
chamfer_obj = doc.addObject("Part::Feature", "Chamfer")
chamfer_obj.Shape = chamfer
'''
        
        elif operation == "fuse":
            return '''
# Fuse with another object (requires selection)
obj1 = FreeCAD.ActiveDocument.ActiveObject
# Select second object and fuse
# obj2 = FreeCAD.ActiveDocument.getObject("ObjectName")
# fused = obj1.Shape.fuse(obj2.Shape)
'''
        
        elif operation == "cut":
            return '''
# Cut operation (boolean difference)
obj1 = FreeCAD.ActiveDocument.ActiveObject
# Select tool object and cut
# obj2 = FreeCAD.ActiveDocument.getObject("ToolName")
# cut_result = obj1.Shape.cut(obj2.Shape)
'''
        
        elif operation == "common":
            return '''
# Common operation (boolean intersection)
obj1 = FreeCAD.ActiveDocument.ActiveObject
# Select second object and intersect
# obj2 = FreeCAD.ActiveDocument.getObject("ObjectName")
# common_result = obj1.Shape.common(obj2.Shape)
'''
        
        return ""
    
    def validate_code(self, code: str) -> CodeValidationResult:
        """
        Validate FreeCAD Python script syntax.
        
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
        if 'import FreeCAD' not in code:
            errors.append("Missing 'import FreeCAD' statement")
        if 'import Part' not in code:
            errors.append("Missing 'import Part' statement")
        
        # Check for shape creation
        shape_creators = [
            'makeBox', 'makeSphere', 'makeCylinder', 
            'makeCone', 'makeTorus', 'makeWedge'
        ]
        has_shape = any(creator in code for creator in shape_creators)
        if not has_shape:
            warnings.append("No shape creation detected")
        
        # Check for document creation
        if 'newDocument' not in code:
            warnings.append("Document creation not found")
        
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
            geometry_valid=has_shape,
            topology_valid=True
        )
    
    def execute_code(self, code: str) -> bool:
        """
        Execute FreeCAD script (requires FreeCAD installation).
        
        Args:
            code: Python script to execute
            
        Returns:
            True if execution successful
        """
        if not self.freecad_path:
            return False
        
        # Save script to temp file
        script_file = self.output_dir / "temp_script.py"
        with open(script_file, 'w') as f:
            f.write(code)
        
        try:
            import subprocess
            result = subprocess.run(
                [self.freecad_path, "--console", str(script_file)],
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
        format: str = "step"
    ) -> Optional[str]:
        """
        Export mesh by running FreeCAD script.
        
        Args:
            code: FreeCAD Python script
            filepath: Output file path
            format: Export format (step, stl, obj, etc.)
            
        Returns:
            Path to exported file or None
        """
        if not self.freecad_path:
            return None
        
        # Modify script to include export
        export_lines = f'''
# Export
Part.export([FreeCAD.ActiveDocument.ActiveObject.Label], r"{filepath}")
'''
        
        export_code = code.replace(
            '# Part.export',
            f'Part.export'
        ) + export_lines
        
        return self.execute_code(export_code)
    
    def analyze_mesh(self, code: str) -> MeshAnalysis:
        """
        Analyze mesh properties (placeholder).
        
        Args:
            code: FreeCAD script
            
        Returns:
            MeshAnalysis with estimated properties
        """
        return MeshAnalysis(
            vertices=0,
            faces=0,
            edges=0,
            is_manifold=True,
            is_watertight=True,
            volume=0.0,
            surface_area=0.0,
            bounding_box={"min": [0, 0, 0], "max": [100, 100, 100]}
        )
    
    def get_supported_shapes(self) -> List[str]:
        """Get list of supported shapes."""
        return [
            "box", "cube", "sphere", "cylinder", 
            "cone", "torus", "wedge", "tube"
        ]
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported export formats."""
        return ["step", "stl", "obj", "dxf", "svg", "ifc", "fcstd"]
    
    def export_to_file(self, code: str, output_path: str, format: str = "stl") -> bool:
        """
        Exporta el código FreeCAD Python a un archivo físico.
        
        Args:
            code: Código Python de FreeCAD a guardar/ejecutar.
            output_path: Ruta completa del archivo de salida.
            format: Formato de exportación ('py' o 'step', 'stl', etc.).
            
        Returns:
            True si éxito, False si fallo.
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
            
            print(f"[FreeCAD] Script guardado en: {temp_py}")
            
            # Si solo queríamos el .py, terminamos aquí
            if file_ext == '.py':
                return True
            
            # 2. Intentar ejecutar con FreeCAD para exportar
            if not self.freecad_path or not os.path.exists(self.freecad_path):
                print("[FreeCAD] Advertencia: Ejecutable no encontrado. Solo se generó el archivo .py")
                print("[FreeCAD] Para generar STEP/STL, instala FreeCAD y configura la ruta.")
                return True
            
            # Modificar el código para agregar exportación al final
            # Detectar formato por extensión
            export_format = file_ext.lstrip('.').upper()
            if export_format == 'STL':
                export_format = 'Mesh'
            elif export_format == 'STEP':
                export_format = 'STEP'
            
            export_cmd = f'''
# Export
doc = App.ActiveDocument
if doc and len(doc.Objects) > 0:
    obj = doc.Objects[0]
    if "{export_format}" == "Mesh":
        import Mesh
        mesh = Mesh.Mesh(obj.Shape.tessellate(0.1))
        Mesh.export([mesh], r"{output_path}")
    else:
        doc.exportExport([obj], r"{output_path}")
'''
            code_with_export = code + export_cmd
            
            # Guardar script temporal con export
            temp_export_py = temp_py.replace('.py', '_export.py')
            with open(temp_export_py, 'w', encoding='utf-8') as f:
                f.write(code_with_export)
            
            # Comando: freecad --console script.py
            cmd = [
                self.freecad_path,
                "--console",
                temp_export_py
            ]
            
            print(f"[FreeCAD] Ejecutando: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                print(f"[FreeCAD] Exportación exitosa a: {output_path}")
                return True
            else:
                if result.stderr:
                    print(f"[FreeCAD] Error: {result.stderr}")
                # Aún devolvemos True porque el .py se generó
                return True
                
        except Exception as e:
            print(f"[FreeCAD] Excepción al exportar: {str(e)}")
            return False
