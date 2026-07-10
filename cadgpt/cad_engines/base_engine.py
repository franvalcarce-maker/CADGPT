"""
Base CAD Engine

Abstract base class for all CAD engine implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CodeValidationResult:
    """Result of code validation."""
    
    is_valid: bool
    report: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    syntax_valid: bool = True
    geometry_valid: bool = True
    topology_valid: bool = True


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
