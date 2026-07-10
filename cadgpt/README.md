# CadGPT - AI-Powered CAD Generation Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Phase](https://img.shields.io/badge/phase-2-green.svg)](docs/phase2_implementation.md)

**CadGPT** es una plataforma de inteligencia artificial especializada en modelado CAD, arquitectura e ingeniería capaz de transformar lenguaje natural en geometría, modelos tridimensionales, scripts paramétricos y documentación técnica.

## 🎯 Objetivo

Desarrollar un sistema modular capaz de interpretar instrucciones humanas y convertirlas en modelos y operaciones CAD mediante diferentes motores y plataformas de diseño.

## ✨ Características Principales

### Procesamiento de Lenguaje Natural
- Interpretación de instrucciones en español e inglés
- Detección automática de dimensiones y unidades (mm, cm, m, inches)
- Reconocimiento de formas geométricas básicas y complejas
- Soporte para operaciones booleanas (hueco, centrado, etc.)

### Motores CAD Soportados

| Motor | Estado | Formatos de Exportación |
|-------|--------|------------------------|
| **OpenSCAD** | ✅ Implementado | STL, OFF, DXF, SVG, PNG |
| **Blender** | ✅ Implementado | STL, OBJ, FBX, GLTF, DAE, PLY, SVG, PNG |
| **FreeCAD** | ✅ Implementado | STEP, STL, OBJ, DXF, SVG, IFC, FCSTD |

### Sistema de Validación
- Validación sintáctica de código generado
- Validación geométrica de mallas
- Detección de geometría inválida
- Análisis topológico (no-manifold, intersecciones)

## 🏗️ Arquitectura

```
cadgpt/
├── core/
│   ├── llm_interface/      # Interfaces para modelos de lenguaje
│   ├── memory/             # Gestión de sesiones y contexto
│   └── orchestration/      # Orquestador de agentes
├── cad_engines/
│   ├── base_engine.py      # Interfaz abstracta de motores
│   ├── openscad/           # Motor OpenSCAD
│   ├── blender/            # Motor Blender (bpy)
│   └── freecad/            # Motor FreeCAD (Part Workbench)
├── validators/
│   ├── geometry_validator/ # Validación geométrica
│   ├── syntax_validator/   # Validación sintáctica
│   └── topology_validator/ # Validación topológica
├── importers/              # Importación de modelos existentes
├── exporters/              # Exportación a múltiples formatos
├── api/                    # API REST (FastAPI)
├── frontend/               # Interfaz web (React + TypeScript)
├── tests/                  # Suite de tests unitarios e integración
├── docs/                   # Documentación técnica
└── output/                 # Archivos generados
```

## 🚀 Instalación

### Requisitos Previos

- Python 3.9+
- OpenSCAD (opcional, para renderizado)
- Blender con bpy (opcional)
- FreeCAD (opcional)

### Instalación del Proyecto

```bash
# Clonar el repositorio
git clone https://github.com/franvalcarce-maker/CADGPT.git
cd CADGPT

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Dependencias Principales

```txt
numpy>=1.24.0
trimesh>=4.0.0
open3d>=0.17.0
shapely>=2.0.0
cadquery>=2.3.0
pyvista>=0.42.0
networkx>=3.0.0
pydantic>=2.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
```

## 💡 Uso Básico

### Generar un Cubo con OpenSCAD

```python
from cad_engines import create_engine

# Crear motor OpenSCAD
engine = create_engine("openscad")

# Generar código para un cubo hueco
code = engine.generate_code(
    shape="cube",
    parameters={"size": 100.0, "thickness": 5.0},
    operation="hollow"
)

print(code)
# Validar y guardar
validation = engine.validate_code(code)
if validation.is_valid:
    engine.save_code(code, "output/cubo.scad")
```

### Usando el Orquestador de Agentes

```python
from core.orchestration.agent_orchestrator import AgentOrchestrator
from core.llm_interface.local_llm import LocalLLM

# Configurar orquestador con LLM local
llm = LocalLLM(base_url="http://localhost:1234/v1")
orchestrator = AgentOrchestrator(llm=llm)

# Procesar instrucción en lenguaje natural
result = orchestrator.process_prompt(
    "Genera un cubo hueco de 100 mm de lado y 5 mm de espesor"
)

print(f"Código generado:\n{result.code}")
print(f"Validación: {result.validation_report}")
```

### Ejemplos de Prompts Soportados

```
"Genera un cubo de 2 metros de lado."
"Diseña una mesa de 120x80 cm con patas metálicas."
"Genera una vivienda de 70 m² con dos dormitorios."
"Convierte este boceto en un modelo 3D."
"Crea una esfera de 50 mm de radio hueca con 3 mm de espesor"
"Genera un cilindro de 10 cm de altura y 5 cm de diámetro"
```

## 🧪 Testing

```bash
# Ejecutar tests unitarios
pytest tests/unit/ -v

# Ejecutar tests de integración
pytest tests/integration/ -v

# Coverage
pytest --cov=cadgpt tests/
```

## 📚 Documentación

- [Arquitectura del Sistema](docs/architecture.md)
- [Implementación Fase 1](docs/phase1_implementation.md)
- [Implementación Fase 2](docs/phase2_implementation.md)
- [API Reference](docs/api_reference.md)

## 🛣️ Roadmap

### ✅ Fase 1 Completada
- Generación de código OpenSCAD desde lenguaje natural
- Parser básico de instrucciones
- Validación sintáctica

### ✅ Fase 2 Completada
- Motor Blender con bpy API
- Motor FreeCAD con Part Workbench
- Tests unitarios completos

### 🔄 Fase 3 (En Desarrollo)
- Importación y análisis de modelos existentes
- Validadores geométricos avanzados
- API REST con FastAPI

### 📋 Fase 4 (Planificada)
- Generación automática de documentación técnica
- Planos constructivos automáticos

### 🔮 Fase 5 (Futuro)
- Agentes autónomos de revisión y optimización
- Integración BIM (IFC)
- Conversión video a malla 3D

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 👥 Autores

- **Fran Valcarce** - *Trabajo inicial* - [@franvalcarce-maker](https://github.com/franvalcarce-maker)

## 🙏 Agradecimientos

- Comunidad OpenSCAD
- Blender Foundation
- FreeCAD Community
- Contribuidores de cadquery y trimesh

---

**Nota:** Este proyecto está en desarrollo activo. Algunas características pueden cambiar en futuras versiones.
