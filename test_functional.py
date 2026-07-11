import os
import struct
import subprocess
import unittest
from io import StringIO
from contextlib import redirect_stdout


def run_openscad(code, output_file):
    """Ejecuta OpenSCAD con el código proporcionado y guarda la salida en un archivo."""
    with open('temp.scad', 'w') as f:
        f.write(code)
    
    result = subprocess.run([
        'openscad', '-o', output_file, 'temp.scad'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Error ejecutando OpenSCAD: {result.stderr}")
    
    # Limpiar archivo temporal
    os.remove('temp.scad')


def validate_stl_syntax(file_path):
    """
    Valida la sintaxis básica de un archivo STL ASCII o binario.
    Retorna True si es válido, False en caso contrario.
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(80).decode('utf-8', errors='ignore').strip()
            
            # Detectar si es ASCII o binario basado en el encabezado
            is_ascii = header.startswith('solid ') or b'solid' in f.peek(10)
        
        if is_ascii:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            # Verificar estructura básica de STL ASCII
            if not content.startswith('solid ') or not content.endswith('endsolid'):
                return False
            
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            if len(lines) < 2:
                return False
            
            vertex_count = 0
            normal_found = False
            
            for line in lines[1:-1]:  # Excluir 'solid' y 'endsolid'
                if line.startswith('facet normal'):
                    normal_found = True
                elif line.startswith('vertex'):
                    vertex_count += 1
            
            # Cada triángulo debe tener 3 vértices
            if vertex_count % 3 != 0:
                return False
                
            return normal_found
        
        else:  # STL Binario
            return validate_stl_binary(file_path)
    
    except Exception:
        return False


def validate_stl_binary(file_path):
    """
    Valida un archivo STL binario verificando su estructura.
    """
    try:
        with open(file_path, 'rb') as f:
            # Leer encabezado (80 bytes)
            header = f.read(80)
            if len(header) < 80:
                return False
            
            # Leer número de triángulos (4 bytes)
            num_triangles_bytes = f.read(4)
            if len(num_triangles_bytes) < 4:
                return False
            
            num_triangles = struct.unpack('<I', num_triangles_bytes)[0]
            
            # Leer datos de los triángulos
            triangle_data_size = 50  # Tamaño fijo por triángulo en binario
            expected_size = 80 + 4 + (num_triangles * triangle_data_size)
            
            # Verificar tamaño total del archivo
            f.seek(0, 2)  # Ir al final
            actual_size = f.tell()
            
            return actual_size == expected_size
    
    except Exception:
        return False


def validate_stl_geometry(file_path):
    """
    Valida la geometría de un archivo STL binario.
    Lee los vértices y verifica la integridad geométrica.
    """
    vertices = set()
    triangles = []
    
    try:
        with open(file_path, 'rb') as f:
            # Saltar encabezado
            f.read(80)
            
            # Leer número de triángulos
            num_triangles_data = f.read(4)
            if len(num_triangles_data) < 4:
                return False
            
            num_triangles = struct.unpack('<I', num_triangles_data)[0]
            
            # Leer cada triángulo
            for _ in range(num_triangles):
                triangle_data = f.read(50)  # 50 bytes por triángulo
                if len(triangle_data) < 50:
                    return False
                
                # Extraer normales (12 bytes) y 3 vértices (36 bytes)
                # Formato: [nx, ny, nz] + [v1x, v1y, v1z] + [v2x, v2y, v2z] + [v3x, v3y, v3z] + [atributos (2 bytes)]
                floats = struct.unpack('<12fH', triangle_data)
                
                # Extraer vértices (índices 3-5, 6-8, 9-11 son x,y,z de cada vértice)
                v1 = tuple(floats[3:6])
                v2 = tuple(floats[6:9])
                v3 = tuple(floats[9:12])
                
                # Agregar vértices únicos al conjunto
                vertices.add(v1)
                vertices.add(v2)
                vertices.add(v3)
                
                triangles.append((v1, v2, v3))
        
        # Verificaciones geométricas básicas
        if len(triangles) != num_triangles:
            return False
            
        # Verificar que haya al menos 1 vértice por triángulo
        if len(vertices) < 3:
            return False
        
        # Retornar información sobre la geometría
        return {
            'valid': True,
            'num_triangles': len(triangles),
            'num_vertices': len(vertices),
            'triangles': triangles,
            'vertices': list(vertices)
        }
    
    except Exception as e:
        print(f"Error validando geometría STL: {e}")
        return {'valid': False}


class TestSTLValidation(unittest.TestCase):
    
    def test_openscad_stl_generation_and_validation(self):
        """Prueba generación de STL con OpenSCAD y validación."""
        scad_code = '''
        // Cubo hueco simple
        difference() {
            cube([10, 10, 10]);
            translate([2, 2, 2]) cube([6, 6, 6]);
        }
        '''
        
        output_file = 'output/test_cube_hollow.stl'
        
        # Asegurar directorio de salida
        os.makedirs('output', exist_ok=True)
        
        # Ejecutar OpenSCAD
        run_openscad(scad_code, output_file)
        
        # Validar archivo generado
        self.assertTrue(os.path.exists(output_file), "Archivo STL no generado")
        
        # Validar sintaxis
        self.assertTrue(validate_stl_syntax(output_file), "Sintaxis STL inválida")
        
        # Validar geometría
        geometry_result = validate_stl_geometry(output_file)
        self.assertTrue(geometry_result['valid'], "Geometría STL inválida")
        
        # Verificar propiedades geométricas
        self.assertEqual(geometry_result['num_triangles'], 12, "Número incorrecto de triángulos")
        self.assertEqual(geometry_result['num_vertices'], 8, "Número incorrecto de vértices")
        
        # Limpiar archivo generado
        os.remove(output_file)
    
    def test_blender_stl_validation(self):
        """Simula validación de archivo STL de Blender."""
        stl_content = '''solid blender_export
facet normal -1.000000 0.000000 0.000000
  outer loop
    vertex 0.000000 0.707107 0.707107
    vertex 0.000000 1.000000 0.000000
    vertex 0.000000 0.707107 -0.707107
  endloop
endfacet
facet normal -1.000000 0.000000 0.000000
  outer loop
    vertex 0.000000 0.707107 -0.707107
    vertex 0.000000 -0.707107 -0.707107
    vertex 0.000000 -1.000000 0.000000
  endloop
endfacet
endsolid blender_export
'''
        
        file_path = 'output/blender_test.stl'
        os.makedirs('output', exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write(stl_content)
        
        # Validar sintaxis
        self.assertTrue(validate_stl_syntax(file_path), "Validación de sintaxis fallida para archivo Blender")
        
        # Validar geometría
        geometry_result = validate_stl_geometry(file_path)
        self.assertTrue(geometry_result['valid'], "Validación de geometría fallida para archivo Blender")
        
        # Limpiar archivo
        os.remove(file_path)
    
    def test_freecad_stl_validation(self):
        """Simula validación de archivo STL de FreeCAD."""
        stl_content = '''solid FreeCAD_Model
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 1.0
      vertex 1.0 0.0 1.0
      vertex 1.0 1.0 1.0
    endloop
  endfacet
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 1.0
      vertex 1.0 1.0 1.0
      vertex 0.0 1.0 1.0
    endloop
  endfacet
endsolid FreeCAD_Model
'''
        
        file_path = 'output/freecad_test.stl'
        os.makedirs('output', exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write(stl_content)
        
        # Validar sintaxis
        self.assertTrue(validate_stl_syntax(file_path), "Validación de sintaxis fallida para archivo FreeCAD")
        
        # Validar geometría
        geometry_result = validate_stl_geometry(file_path)
        self.assertTrue(geometry_result['valid'], "Validación de geometría fallida para archivo FreeCAD")
        
        # Limpiar archivo
        os.remove(file_path)


if __name__ == '__main__':
    # Asegurar directorio de salida
    os.makedirs('output', exist_ok=True)
    
    # Ejecutar pruebas
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSTLValidation)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Imprimir resumen
    print("\n=== Resumen de Pruebas ===")
    print(f"Total pruebas: {result.testsRun}")
    print(f"Errores: {len(result.errors)}")
    print(f"Fallas: {len(result.failures)}")
    print("Estado:", "✅ ¡Todas las pruebas pasaron!" if result.wasSuccessful() else "❌ Algunas pruebas fallaron")