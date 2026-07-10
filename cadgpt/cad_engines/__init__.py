"""
CAD Engines Package

Provides abstract base class and implementations for different CAD engines.
"""

from .base_engine import BaseCADEngine, CodeValidationResult
from .openscad.openscad_engine import OpenSCADEngine

__all__ = ["BaseCADEngine", "CodeValidationResult", "OpenSCADEngine"]


def create_engine(engine_name: str, **kwargs) -> BaseCADEngine:
    """
    Factory function to create CAD engine instances.
    
    Args:
        engine_name: Name of the engine ('openscad', 'blender', 'freecad')
        **kwargs: Engine-specific configuration
        
    Returns:
        CAD engine instance
        
    Raises:
        ValueError: If engine name is not recognized
    """
    engines = {
        "openscad": OpenSCADEngine,
    }
    
    # Try to import optional engines
    try:
        from .blender.blender_engine import BlenderEngine
        engines["blender"] = BlenderEngine
    except ImportError:
        pass
    
    try:
        from .freecad.freecad_engine import FreeCADEngine
        engines["freecad"] = FreeCADEngine
    except ImportError:
        pass
    
    if engine_name.lower() not in engines:
        available = ", ".join(engines.keys())
        raise ValueError(
            f"Unknown engine: {engine_name}. Available engines: {available}"
        )
    
    return engines[engine_name.lower()](**kwargs)
