"""
Agent Orchestrator

Coordinates multiple specialized agents for CAD generation workflows.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import re
import json

from ..llm_interface.base_llm import BaseLLM, LLMResponse
from ..memory.session_memory import SessionMemory


@dataclass
class GenerationResult:
    """Result of a CAD generation operation."""
    
    code: str
    engine: str
    shape: str
    parameters: Dict[str, Any]
    is_valid: bool
    validation_report: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedCommand:
    """Parsed command from natural language."""
    
    action: str
    shape: str
    parameters: Dict[str, Any]
    operation: Optional[str] = None
    units: str = "mm"
    confidence: float = 1.0


class AgentOrchestrator:
    """
    Orchestrates multiple specialized agents for CAD generation.
    
    Coordinates:
    - Language interpretation agent
    - Geometry generation agent
    - Validation agent
    - Optimization agent
    - Export agent
    """
    
    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        default_engine: str = "openscad",
        auto_validate: bool = True
    ):
        """
        Initialize the orchestrator.
        
        Args:
            llm: Language model interface (optional for rule-based parsing)
            default_engine: Default CAD engine to use
            auto_validate: Whether to automatically validate generated code
        """
        self.llm = llm
        self.default_engine = default_engine
        self.auto_validate = auto_validate
        self.session = SessionMemory()
        
        # Supported shapes and their parameter parsers
        self.shape_parsers = {
            "cube": self._parse_cube_params,
            "box": self._parse_cube_params,
            "cuboid": self._parse_cuboid_params,
            "sphere": self._parse_sphere_params,
            "cylinder": self._parse_cylinder_params,
            "cone": self._parse_cone_params,
            "torus": self._parse_torus_params,
            "pyramid": self._parse_pyramid_params,
        }
        
        # Unit conversions to mm
        self.unit_conversions = {
            "mm": 1.0,
            "milimetros": 1.0,
            "milímetros": 1.0,
            "cm": 10.0,
            "centimetros": 10.0,
            "centímetros": 10.0,
            "m": 1000.0,
            "metros": 1000.0,
            "inch": 25.4,
            "inches": 25.4,
            "pulgada": 25.4,
            "pulgadas": 25.4,
        }
    
    def process_prompt(self, prompt: str, engine: Optional[str] = None) -> GenerationResult:
        """
        Process a natural language prompt and generate CAD code.
        
        Args:
            prompt: Natural language instruction
            engine: CAD engine to use (defaults to instance default)
            
        Returns:
            GenerationResult with code and validation status
        """
        engine = engine or self.default_engine
        
        # Store user prompt
        self.session.add_message("user", prompt)
        
        # Parse the command
        parsed = self._parse_command(prompt)
        
        # Generate code using appropriate engine
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from cad_engines import create_engine
        cad_engine = create_engine(engine)
        
        # Generate code
        code = cad_engine.generate_code(
            shape=parsed.shape,
            parameters=parsed.parameters,
            operation=parsed.operation
        )
        
        # Validate if enabled
        validation_result = None
        is_valid = True
        validation_report = "Validation skipped"
        errors = []
        warnings = []
        
        if self.auto_validate:
            validation_result = cad_engine.validate_code(code)
            is_valid = validation_result.is_valid
            validation_report = validation_result.report
            errors = validation_result.errors
            warnings = validation_result.warnings
        
        # Store generation
        gen_id = f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session.store_generation(
            generation_id=gen_id,
            code=code,
            engine=engine,
            shape=parsed.shape,
            parameters=parsed.parameters,
            validation_result={
                "is_valid": is_valid,
                "report": validation_report,
                "errors": errors,
                "warnings": warnings
            } if validation_result else None
        )
        
        # Store assistant response
        response_summary = f"Generated {parsed.shape} with {parsed.parameters}"
        self.session.add_message("assistant", response_summary)
        
        return GenerationResult(
            code=code,
            engine=engine,
            shape=parsed.shape,
            parameters=parsed.parameters,
            is_valid=is_valid,
            validation_report=validation_report,
            errors=errors,
            warnings=warnings,
            metadata={
                "generation_id": gen_id,
                "parsed_command": {
                    "action": parsed.action,
                    "operation": parsed.operation,
                    "units": parsed.units,
                    "confidence": parsed.confidence
                },
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def _parse_command(self, prompt: str) -> ParsedCommand:
        """
        Parse natural language command into structured format.
        
        Uses rule-based parsing with regex patterns.
        Can be enhanced with LLM for complex commands.
        
        Args:
            prompt: Natural language instruction
            
        Returns:
            ParsedCommand with extracted information
        """
        prompt_lower = prompt.lower()
        
        # Detect action
        action = "generate"
        if any(word in prompt_lower for word in ["crear", "genera", "haz", "diseña", "diseña", "construye"]):
            action = "generate"
        elif any(word in prompt_lower for word in ["modifica", "edita", "cambia"]):
            action = "modify"
        elif any(word in prompt_lower for word in ["elimina", "borra"]):
            action = "delete"
        
        # Detect shape - check for specific shapes first before defaulting to cube
        shape = "cube"  # default
        # Priority order: check more specific shapes first
        priority_shapes = ["torus", "cylinder", "sphere", "cone", "pyramid", "cuboid", "cube", "box"]
        for shape_name in priority_shapes:
            if shape_name in prompt_lower:
                shape = shape_name
                break
        
        # Also check Spanish aliases
        if "esfera" in prompt_lower or "ball" in prompt_lower:
            shape = "sphere"
        elif "cilindro" in prompt_lower:
            shape = "cylinder"
        elif "cono" in prompt_lower:
            shape = "cone"
        elif "piramide" in prompt_lower or "pirámide" in prompt_lower:
            shape = "pyramid"
        elif "toroide" in prompt_lower or "dona" in prompt_lower or "doughnut" in prompt_lower:
            shape = "torus"
        
        # Detect operation
        operation = None
        if "huec" in prompt_lower or "hollow" in prompt_lower:
            operation = "hollow"
        elif "centr" in prompt_lower or "center" in prompt_lower:
            operation = "centered"
        elif "union" in prompt_lower or "unir" in prompt_lower:
            operation = "union"
        elif "diferencia" in prompt_lower or "difference" in prompt_lower:
            operation = "difference"
        
        # Detect units
        units = "mm"
        for unit in self.unit_conversions.keys():
            if unit in prompt_lower:
                units = unit
                break
        
        # Extract dimensions using regex
        parameters = self._extract_dimensions(prompt, units)
        
        # Use shape-specific parser
        if shape in self.shape_parsers:
            parameters = self.shape_parsers[shape](parameters, prompt_lower)
        
        return ParsedCommand(
            action=action,
            shape=shape,
            parameters=parameters,
            operation=operation,
            units=units,
            confidence=0.9  # Could be improved with LLM confidence scoring
        )
    
    def _extract_dimensions(self, prompt: str, units: str) -> Dict[str, float]:
        """
        Extract numerical dimensions from prompt.
        
        Args:
            prompt: Natural language instruction
            units: Detected unit type
            
        Returns:
            Dictionary of dimension names to values in mm
        """
        params = {}
        conversion = self.unit_conversions.get(units, 1.0)
        
        # Pattern: number followed by optional unit
        pattern = r'(\d+(?:\.\d+)?)\s*(?:mm|cm|m|inch|inches|milimetros|centimetros|metros)?'
        matches = re.findall(pattern, prompt.lower())
        
        if matches:
            values = [float(m) * conversion for m in matches]
            
            # Assign based on context
            if len(values) == 1:
                params["size"] = values[0]
            elif len(values) == 2:
                params["width"] = values[0]
                params["depth"] = values[1]
            elif len(values) >= 3:
                params["width"] = values[0]
                params["depth"] = values[1]
                params["height"] = values[2]
        
        # Look for specific dimension keywords
        radius_match = re.search(r'radio\s+de\s+(\d+(?:\.\d+)?)', prompt.lower())
        if radius_match:
            params["radius"] = float(radius_match.group(1)) * conversion
        
        diameter_match = re.search(r'diametro\s+de\s+(\d+(?:\.\d+)?)|diámetro\s+de\s+(\d+(?:\.\d+)?)', prompt.lower())
        if diameter_match:
            diam = float(diameter_match.group(1) or diameter_match.group(2))
            params["diameter"] = diam * conversion
            if "radius" not in params:
                params["radius"] = diam * conversion / 2
        
        thickness_match = re.search(r'espesor\s+(?:de\s+)?(\d+(?:\.\d+)?)', prompt.lower())
        if thickness_match:
            params["thickness"] = float(thickness_match.group(1)) * conversion
        
        height_match = re.search(r'altura\s+(?:de\s+)?(\d+(?:\.\d+)?)', prompt.lower())
        if height_match:
            params["height"] = float(height_match.group(1)) * conversion
        
        return params
    
    def _parse_cube_params(self, params: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Parse parameters for cube shape."""
        if "size" not in params and "width" not in params:
            params["size"] = 100.0  # default
        
        # Normalize to size if width/depth/height are equal
        if all(k in params for k in ["width", "depth", "height"]):
            if params["width"] == params["depth"] == params["height"]:
                params["size"] = params["width"]
                del params["width"]
                del params["depth"]
                del params["height"]
        
        return params
    
    def _parse_cuboid_params(self, params: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Parse parameters for cuboid shape."""
        if "width" not in params:
            params["width"] = 100.0
        if "depth" not in params:
            params["depth"] = params.get("width", 100.0)
        if "height" not in params:
            params["height"] = params.get("width", 100.0)
        return params
    
    def _parse_sphere_params(self, params: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Parse parameters for sphere shape."""
        if "radius" not in params and "diameter" not in params:
            if "size" in params:
                params["radius"] = params["size"] / 2
                del params["size"]
            else:
                params["radius"] = 50.0
        elif "diameter" in params and "radius" not in params:
            params["radius"] = params["diameter"] / 2
        return params
    
    def _parse_cylinder_params(self, params: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Parse parameters for cylinder shape."""
        if "radius" not in params and "diameter" not in params:
            params["radius"] = 25.0
        if "height" not in params:
            params["height"] = 100.0
        return params
    
    def _parse_cone_params(self, params: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Parse parameters for cone shape."""
        if "radius" not in params:
            params["radius"] = 25.0
        if "height" not in params:
            params["height"] = 100.0
        return params
    
    def _parse_torus_params(self, params: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Parse parameters for torus shape."""
        if "outer_radius" not in params and "radius" not in params:
            params["outer_radius"] = 50.0
        if "inner_radius" not in params and "tube_radius" not in params:
            params["inner_radius"] = 10.0
        return params
    
    def _parse_pyramid_params(self, params: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Parse parameters for pyramid shape."""
        if "base_size" not in params and "size" not in params:
            params["base_size"] = 100.0
        if "height" not in params:
            params["height"] = 100.0
        return params
    
    def get_session_history(self) -> List[Dict[str, Any]]:
        """Get current session history."""
        return self.session.get_history()
    
    def clear_session(self):
        """Clear current session."""
        self.session = SessionMemory()
    
    def export_session(self, filepath: str):
        """Export session to file."""
        self.session.save_to_file(filepath)
