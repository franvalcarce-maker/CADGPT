"""
Session Manager - Maintains state across modeling commands.

This module provides a centralized session object that preserves geometry
state between commands, enabling incremental modeling workflows.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelingSession:
    """
    Session container for 3D modeling operations.
    
    Maintains a persistent collection of geometry objects and commands
    across multiple parse-calculate-print cycles.
    """
    
    # Geometry collections (indexed by name for retrieval)
    lines: dict[str, Any] = field(default_factory=dict)
    planes: dict[str, Any] = field(default_factory=dict)
    points: dict[str, Any] = field(default_factory=dict)
    
    # Command history (for undo/redo and audit trails)
    command_history: list[tuple[str, dict]] = field(default_factory=list)
    
    @property
    def all_geometry(self) -> dict[str, Any]:
        """Return all geometry objects in a unified collection."""
        return {**self.lines, **self.planes, **self.points}
    
    @property
    def geometry_count(self) -> int:
        """Total number of geometry objects in session."""
        return len(self.lines) + len(self.planes) + len(self.points)
    
    def clear_command_history(self) -> None:
        """Clear the command history (useful for fresh sessions)."""
        self.command_history.clear()


def create_session() -> ModelingSession:
    """Factory function to create a fresh modeling session."""
    return ModelingSession()


def SessionManager():
    """
    Compatibility wrapper to match expected import signature in main.py.
    Creates and returns a new ModelingSession instance.
    """
    return ModelingSession()
