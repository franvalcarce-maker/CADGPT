"""
Unit Tests for CadGPT

Test suite for core functionality and CAD engines.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCADEngines:
    """Tests for CAD engine implementations."""
    
    def test_create_openscad_engine(self):
        """Test OpenSCAD engine creation via factory."""
        from cadgpt.cad_engines import create_engine
        
        engine = create_engine("openscad")
        assert engine is not None
        assert engine.__class__.__name__ == "OpenSCADEngine"
    
    def test_create_blender_engine(self):
        """Test Blender engine creation via factory."""
        from cadgpt.cad_engines import create_engine
        
        try:
            engine = create_engine("blender")
            assert engine is not None
            assert engine.__class__.__name__ == "BlenderEngine"
        except ValueError as e:
            # May fail if bpy not available
            assert "bpy" in str(e).lower() or "not recognized" in str(e).lower()
    
    def test_create_freecad_engine(self):
        """Test FreeCAD engine creation via factory."""
        from cadgpt.cad_engines import create_engine
        
        try:
            engine = create_engine("freecad")
            assert engine is not None
            assert engine.__class__.__name__ == "FreeCADEngine"
        except ValueError as e:
            # May fail if FreeCAD not available
            assert "not recognized" in str(e).lower()
    
    def test_openscad_generate_cube(self):
        """Test OpenSCAD cube generation."""
        from cadgpt.cad_engines.openscad import OpenSCADEngine
        
        engine = OpenSCADEngine()
        code = engine.generate_code(
            shape="cube",
            parameters={"size": 100}
        )
        
        assert "cube" in code
        assert "[100, 100, 100]" in code
    
    def test_openscad_generate_sphere(self):
        """Test OpenSCAD sphere generation."""
        from cadgpt.cad_engines.openscad import OpenSCADEngine
        
        engine = OpenSCADEngine()
        code = engine.generate_code(
            shape="sphere",
            parameters={"radius": 50}
        )
        
        assert "sphere" in code
        assert "r=50" in code
    
    def test_openscad_generate_cylinder(self):
        """Test OpenSCAD cylinder generation."""
        from cadgpt.cad_engines.openscad import OpenSCADEngine
        
        engine = OpenSCADEngine()
        code = engine.generate_code(
            shape="cylinder",
            parameters={"radius": 25, "height": 100}
        )
        
        assert "cylinder" in code
        assert "h=100" in code
        assert "r=25" in code
    
    def test_openscad_hollow_operation(self):
        """Test OpenSCAD hollow operation."""
        from cadgpt.cad_engines.openscad import OpenSCADEngine
        
        engine = OpenSCADEngine()
        code = engine.generate_code(
            shape="cube",
            parameters={"size": 100, "thickness": 5},
            operation="hollow"
        )
        
        assert "difference()" in code
        assert "cube" in code
    
    def test_openscad_validate_valid_code(self):
        """Test OpenSCAD validation with valid code."""
        from cadgpt.cad_engines.openscad import OpenSCADEngine
        
        engine = OpenSCADEngine()
        code = "cube([10, 10, 10]);"
        result = engine.validate_code(code)
        
        assert result.is_valid
        assert result.syntax_valid
    
    def test_openscad_validate_invalid_code(self):
        """Test OpenSCAD validation with invalid code."""
        from cadgpt.cad_engines.openscad import OpenSCADEngine
        
        engine = OpenSCADEngine()
        code = "cube([10, 10, 10"  # Missing closing bracket and semicolon
        result = engine.validate_code(code)
        
        assert not result.is_valid or len(result.errors) > 0
    
    def test_blender_generate_cube(self):
        """Test Blender cube generation."""
        from cadgpt.cad_engines.blender import BlenderEngine
        
        engine = BlenderEngine()
        code = engine.generate_code(
            shape="cube",
            parameters={"size": 2}
        )
        
        assert "import bpy" in code
        assert "primitive_cube_add" in code
        assert "size=2" in code
    
    def test_blender_generate_sphere(self):
        """Test Blender sphere generation."""
        from cadgpt.cad_engines.blender import BlenderEngine
        
        engine = BlenderEngine()
        code = engine.generate_code(
            shape="sphere",
            parameters={"radius": 1}
        )
        
        assert "primitive_uv_sphere_add" in code
        assert "radius=1" in code
    
    def test_blender_validate_code(self):
        """Test Blender code validation."""
        from cadgpt.cad_engines.blender import BlenderEngine
        
        engine = BlenderEngine()
        code = """import bpy
bpy.ops.mesh.primitive_cube_add(size=2)
"""
        result = engine.validate_code(code)
        
        assert result.is_valid
        assert result.syntax_valid
    
    def test_freecad_generate_box(self):
        """Test FreeCAD box generation."""
        from cadgpt.cad_engines.freecad import FreeCADEngine
        
        engine = FreeCADEngine()
        code = engine.generate_code(
            shape="box",
            parameters={"length": 100, "width": 50, "height": 25}
        )
        
        assert "import FreeCAD" in code
        assert "import Part" in code
        assert "makeBox" in code
        assert "100" in code
        assert "50" in code
        assert "25" in code
    
    def test_freecad_generate_sphere(self):
        """Test FreeCAD sphere generation."""
        from cadgpt.cad_engines.freecad import FreeCADEngine
        
        engine = FreeCADEngine()
        code = engine.generate_code(
            shape="sphere",
            parameters={"radius": 50}
        )
        
        assert "makeSphere" in code
        assert "50" in code
    
    def test_freecad_validate_code(self):
        """Test FreeCAD code validation."""
        from cadgpt.cad_engines.freecad import FreeCADEngine
        
        engine = FreeCADEngine()
        code = """import FreeCAD
import Part
doc = FreeCAD.newDocument("Test")
obj = Part.makeBox(10, 10, 10)
"""
        result = engine.validate_code(code)
        
        assert result.is_valid
        assert result.syntax_valid
    
    def test_freecad_validate_missing_import(self):
        """Test FreeCAD validation detects missing imports."""
        from cadgpt.cad_engines.freecad import FreeCADEngine
        
        engine = FreeCADEngine()
        code = """doc = FreeCAD.newDocument("Test")
obj = Part.makeBox(10, 10, 10)
"""
        result = engine.validate_code(code)
        
        assert not result.is_valid
        assert any("import" in err.lower() for err in result.errors)


class TestCoreComponents:
    """Tests for core components."""
    
    def test_session_memory_creation(self):
        """Test SessionMemory initialization."""
        from cadgpt.core.memory import SessionMemory
        
        memory = SessionMemory()
        assert memory.session_id is not None
        assert len(memory.messages) == 0
    
    def test_session_memory_add_message(self):
        """Test adding messages to session."""
        from cadgpt.core.memory import SessionMemory
        
        memory = SessionMemory()
        msg = memory.add_message("user", "Test message")
        
        assert msg["role"] == "user"
        assert msg["content"] == "Test message"
        assert len(memory.messages) == 1
    
    def test_session_memory_export(self):
        """Test session export."""
        from cadgpt.core.memory import SessionMemory
        
        memory = SessionMemory()
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi there")
        
        exported = memory.export_session()
        
        assert "session_id" in exported
        assert len(exported["messages"]) == 2
    
    def test_llm_response_model(self):
        """Test LLMResponse pydantic model."""
        from cadgpt.core.llm_interface.base_llm import LLMResponse
        
        response = LLMResponse(
            content="Test response",
            model="test-model"
        )
        
        assert response.content == "Test response"
        assert response.model == "test-model"


class TestAgentOrchestrator:
    """Tests for agent orchestrator."""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        from cadgpt.core.orchestration import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        assert orchestrator.default_engine == "openscad"
        assert orchestrator.auto_validate
    
    def test_orchestrator_parse_simple_prompt(self):
        """Test parsing simple prompt."""
        from cadgpt.core.orchestration import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        parsed = orchestrator._parse_command("Genera un cubo de 100 mm")
        
        assert parsed.shape == "cube"
        assert parsed.action == "generate"
    
    def test_orchestrator_parse_hollow_prompt(self):
        """Test parsing hollow operation prompt."""
        from cadgpt.core.orchestration import AgentOrchestrator
        
        orchestrator = AgentOrchestrator()
        parsed = orchestrator._parse_command("Crea una esfera hueca de 50 mm con 5 mm de espesor")
        
        assert parsed.shape == "sphere"
        assert parsed.operation == "hollow"
        assert "thickness" in parsed.parameters
    
    def test_orchestrator_process_prompt(self):
        """Test full prompt processing."""
        from cadgpt.core.orchestration import AgentOrchestrator
        
        orchestrator = AgentOrchestrator(auto_validate=True)
        result = orchestrator.process_prompt(
            "Genera un cubo de 100 mm de lado"
        )
        
        assert result.code is not None
        assert result.engine == "openscad"
        assert result.shape == "cube"
        assert result.is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
