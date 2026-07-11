"""
Session Memory

Manages conversation history and session state for multi-turn interactions.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import json


class SessionMemory:
    """
    Manages session state and conversation history.
    
    Provides persistent storage for multi-turn conversations
    and generation history.
    """
    
    def __init__(self, session_id: Optional[str] = None, max_history: int = 50):
        """
        Initialize session memory.
        
        Args:
            session_id: Unique session identifier (auto-generated if None)
            max_history: Maximum number of messages to keep in history
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.max_history = max_history
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        # Conversation history
        self.messages: List[Dict[str, Any]] = []
        
        # Generation results cache
        self.generations: Dict[str, Dict[str, Any]] = {}
        
        # Session metadata
        self.metadata: Dict[str, Any] = {
            "total_prompts": 0,
            "total_generations": 0,
            "engines_used": set(),
            "shapes_generated": set()
        }
    
    def add_message(self, role: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        Add a message to the conversation history.
        
        Args:
            role: Message role ('user', 'assistant', 'system')
            content: Message content
            **kwargs: Additional metadata
            
        Returns:
            The added message dictionary
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        # Trim history if exceeds max
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        
        if role == "user":
            self.metadata["total_prompts"] += 1
        
        return message
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Args:
            limit: Maximum number of messages to return (None for all)
            
        Returns:
            List of message dictionaries
        """
        if limit:
            return self.messages[-limit:]
        return self.messages.copy()
    
    def clear_history(self):
        """Clear conversation history while preserving metadata."""
        self.messages = []
        self.updated_at = datetime.now()
    
    def store_generation(
        self,
        generation_id: str,
        code: str,
        engine: str,
        shape: str,
        parameters: Dict[str, Any],
        validation_result: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Store a generation result.
        
        Args:
            generation_id: Unique identifier for this generation
            code: Generated CAD code
            engine: CAD engine used
            shape: Shape type generated
            parameters: Parameters used for generation
            validation_result: Validation results if available
            **kwargs: Additional metadata
        """
        self.generations[generation_id] = {
            "code": code,
            "engine": engine,
            "shape": shape,
            "parameters": parameters,
            "validation": validation_result,
            "created_at": datetime.now().isoformat(),
            **kwargs
        }
        
        self.metadata["total_generations"] += 1
        self.metadata["engines_used"].add(engine)
        self.metadata["shapes_generated"].add(shape)
        self.updated_at = datetime.now()
    
    def get_generation(self, generation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a stored generation by ID.
        
        Args:
            generation_id: ID of the generation to retrieve
            
        Returns:
            Generation data dictionary or None if not found
        """
        return self.generations.get(generation_id)
    
    def get_recent_generations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent generations.
        
        Args:
            limit: Maximum number of generations to return
            
        Returns:
            List of generation dictionaries
        """
        sorted_gens = sorted(
            self.generations.values(),
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        return sorted_gens[:limit]
    
    def export_session(self) -> Dict[str, Any]:
        """
        Export complete session data.
        
        Returns:
            Dictionary containing all session data
        """
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "messages": self.messages,
            "generations": self.generations,
            "metadata": {
                **self.metadata,
                "engines_used": list(self.metadata["engines_used"]),
                "shapes_generated": list(self.metadata["shapes_generated"])
            }
        }
    
    def import_session(self, data: Dict[str, Any]):
        """
        Import session data from a dictionary.
        
        Args:
            data: Session data dictionary
        """
        self.session_id = data.get("session_id", str(uuid.uuid4()))
        self.messages = data.get("messages", [])
        self.generations = data.get("generations", {})
        self.metadata = data.get("metadata", self.metadata)
        self.updated_at = datetime.now()
    
    def save_to_file(self, filepath: str):
        """
        Save session to a JSON file.
        
        Args:
            filepath: Path to save the file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.export_session(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> "SessionMemory":
        """
        Load session from a JSON file.
        
        Args:
            filepath: Path to the file to load
            
        Returns:
            SessionMemory instance with loaded data
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        session = cls()
        session.import_session(data)
        return session
    
    def get_context_for_prompt(self) -> str:
        """
        Build context string from recent conversation history.
        
        Returns:
            Formatted context string for LLM prompts
        """
        if not self.messages:
            return ""
        
        context_lines = []
        for msg in self.messages[-10:]:  # Last 10 messages
            context_lines.append(f"{msg['role']}: {msg['content']}")
        
        return "\n".join(context_lines)
    
    def __repr__(self) -> str:
        return (
            f"SessionMemory(id={self.session_id[:8]}, "
            f"messages={len(self.messages)}, "
            f"generations={len(self.generations)})"
        )
