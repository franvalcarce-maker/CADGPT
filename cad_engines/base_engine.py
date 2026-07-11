"""
Base CAD Engine

Abstract base class for all CAD engine implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CodeValidationResult:
    """Result of code validation."""
    
    is_valid: bool
    report: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    syntax_valid: bool = True
    geometry_valid: bool = True
    topology_valid: bool = True
    code: str = ""  # Added to store generated code
    success: bool = True  # Alias for is_valid for compatibility
    output_file: Optional[str] = None  # Path to generated file
    message: str = ""  # Human-readable message


@dataclass
class MeshAnalysis:
    """Analysis results for a mesh."""
    
    vertices: int
    faces: int
    edges: int
    is_manifold: bool
    is_watertight: bool
    volume: float
    surface_area: float
    bounding_box: Dict[str, Any]


class BaseCADEngine(ABC):
    """
    Abstract base class for CAD engines.
    
    All CAD engine implementations must inherit from this class
    and implement the required methods.
    """
    
    def __init__(self, output_dir: str = "output", **kwargs):
        """
        Initialize the CAD engine.
        
        Args:
            output_dir: Directory for output files
            **kwargs: Engine-specific configuration
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = kwargs
    
    def generate_from_text(self, text: str) -> Any:
        """
        Generate CAD code from natural language text.
        
        This is a convenience method that parses natural language
        and calls generate_code with appropriate parameters.
        
        Args:
            text: Natural language description
            
        Returns:
            CodeValidationResult or similar result object
        """
        # Parse the text to extract shape and parameters
        shape, params, operation = self._parse_natural_language(text)
        
        # Generate code
        code = self.generate_code(shape, params, operation)
        
        # Return result object
        return CodeValidationResult(
            is_valid=True,
            report="Code generated successfully",
            code=code
        )
    
    def _parse_natural_language(self, text: str) -> tuple:
        """
        Parse natural language text to extract shape, parameters and operations.
        
        Args:
            text: Natural language description
            
        Returns:
            Tuple of (shape, parameters_dict, operation)
        """
        import re
        
        text_lower = text.lower()
        params = {}
        operation = None
        
        # Detect shape
        shape = "cube"  # default
        if any(word in text_lower for word in ["cubo", "cube"]):
            shape = "cube"
        elif any(word in text_lower for word in ["esfera", "sphere", "bola", "ball"]):
            shape = "sphere"
        elif any(word in text_lower for word in ["cilindro", "cylinder"]):
            shape = "cylinder"
        elif any(word in text_lower for word in ["cono", "cone"]):
            shape = "cone"
        elif any(word in text_lower for word in ["toro", "torus", "dona", "donut"]):
            shape = "torus"
        elif any(word in text_lower for word in ["piramide", "pyramid"]):
            shape = "pyramid"
        
        # Extract dimensions using regex
        # Pattern for numbers with optional units
        number_pattern = r'(\d+(?:\.\d+)?)\s*(mm|cm|m|inch|in)?'
        
        # Look for size/length/width/height
        size_match = re.search(r'(?:lado|size|longitud|length|ancho|width|alto|height)\s*(?:de\s*)?' + number_pattern, text_lower)
        if size_match:
            value = float(size_match.group(1))
            unit = size_match.group(2) or 'mm'
            params['size'] = self._convert_to_mm(value, unit)
        
        # Look for radius/diameter
        radius_match = re.search(r'(?:radio|radius|diametro|diameter)\s*(?:de\s*)?' + number_pattern, text_lower)
        if radius_match:
            value = float(radius_match.group(1))
            unit = radius_match.group(2) or 'mm'
            mm_value = self._convert_to_mm(value, unit)
            if 'diametro' in text_lower or 'diameter' in text_lower:
                params['radius'] = mm_value / 2
            else:
                params['radius'] = mm_value
        
        # Look for height
        height_match = re.search(r'(?:alto|altura|height|h)\s*(?:de\s*)?' + number_pattern, text_lower)
        if height_match:
            value = float(height_match.group(1))
            unit = height_match.group(2) or 'mm'
            params['height'] = self._convert_to_mm(value, unit)
        
        # Look for thickness (for hollow objects)
        thickness_match = re.search(r'(?:espesor|thickness|pared|wall)\s*(?:de\s*)?' + number_pattern, text_lower)
        if thickness_match:
            value = float(thickness_match.group(1))
            unit = thickness_match.group(2) or 'mm'
            params['thickness'] = self._convert_to_mm(value, unit)
        
        # Detect hollow operation
        if any(word in text_lower for word in ["hueco", "hollow", "vacío", "empty"]):
            operation = "hollow"
        
        # Detect centered operation
        if any(word in text_lower for word in ["centrado", "centered", "centro", "center"]):
            params['centered'] = True
        
        # Set defaults based on shape
        if shape == "cube" and 'size' not in params:
            params['size'] = 100  # default 100mm
        elif shape == "sphere" and 'radius' not in params:
            params['radius'] = 50  # default 50mm
        elif shape == "cylinder":
            if 'radius' not in params:
                params['radius'] = 25
            if 'height' not in params:
                params['height'] = 100
        
        return shape, params, operation
    
    def _convert_to_mm(self, value: float, unit: str) -> float:
        """Convert value to millimeters."""
        unit = unit.lower() if unit else 'mm'
        conversions = {
            'mm': 1.0,
            'cm': 10.0,
            'm': 1000.0,
            'inch': 25.4,
            'in': 25.4
        }
        return value * conversions.get(unit, 1.0)
    
    @abstractmethod
    def generate_code(
        self,
        shape: str,
        parameters: Dict[str, Any],
        operation: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate CAD code for a given shape.
        
        Args:
            shape: Type of shape to generate
            parameters: Shape parameters (dimensions, etc.)
            operation: Optional operation (hollow, centered, etc.)
            **kwargs: Additional engine-specific parameters
            
        Returns:
            Generated CAD code as string
        """
        pass
    
    @abstractmethod
    def validate_code(self, code: str) -> CodeValidationResult:
        """
        Validate generated CAD code.
        
        Args:
            code: CAD code to validate
            
        Returns:
            CodeValidationResult with validation status
        """
        pass
    
    @abstractmethod
    def execute_code(self, code: str) -> bool:
        """
        Execute CAD code to generate geometry.
        
        Args:
            code: CAD code to execute
            
        Returns:
            True if execution successful, False otherwise
        """
        pass
    
    @abstractmethod
    def export_mesh(
        self,
        code: str,
        filepath: str,
        format: str = "stl"
    ) -> Optional[str]:
        """
        Export generated geometry to mesh file.
        
        Args:
            code: CAD code
            filepath: Output file path
            format: Export format (stl, obj, etc.)
            
        Returns:
            Path to exported file or None if failed
        """
        pass
    
    @abstractmethod
    def analyze_mesh(self, code: str) -> MeshAnalysis:
        """
        Analyze generated mesh properties.
        
        Args:
            code: CAD code
            
        Returns:
            MeshAnalysis with mesh properties
        """
        pass
    
    def save_code(self, code: str, filename: str) -> str:
        """
        Save code to file.
        
        Args:
            code: CAD code to save
            filename: Output filename
            
        Returns:
            Full path to saved file
        """
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        return str(filepath)
    
    def load_code(self, filename: str) -> str:
        """
        Load code from file.
        
        Args:
            filename: File to load
            
        Returns:
            CAD code content
        """
        filepath = self.output_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def get_supported_shapes(self) -> List[str]:
        """
        Get list of supported shape types.
        
        Returns:
            List of shape names
        """
        return [
            "cube", "sphere", "cylinder", "cone", 
            "torus", "pyramid", "box", "wedge"
        ]
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported export formats.
        
        Returns:
            List of format extensions
        """
        return ["stl", "obj", "off", "dxf", "svg"]
    
    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about this engine.
        
        Returns:
            Dictionary with engine metadata
        """
        return {
            "name": self.__class__.__name__,
            "output_dir": str(self.output_dir),
            "supported_shapes": self.get_supported_shapes(),
            "supported_formats": self.get_supported_formats(),
            "config": self.config
        }
