"""
Base LLM Interface

Abstract base class for all Language Model providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Standardized response from LLM."""
    
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseLLM(ABC):
    """
    Abstract base class for Language Model interfaces.
    
    Provides a unified interface for different LLM providers
    (OpenAI, LM Studio, Ollama, etc.)
    """
    
    def __init__(self, model_name: str = "default", **kwargs):
        """
        Initialize the LLM interface.
        
        Args:
            model_name: Name of the model to use
            **kwargs: Additional provider-specific arguments
        """
        self.model_name = model_name
        self.config = kwargs
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Generate a response from the language model.
        
        Args:
            prompt: Input prompt text
            **kwargs: Additional generation parameters
            
        Returns:
            LLMResponse object with generated content
        """
        pass
    
    @abstractmethod
    def generate_streaming(self, prompt: str, **kwargs):
        """
        Generate a streaming response from the language model.
        
        Args:
            prompt: Input prompt text
            **kwargs: Additional generation parameters
            
        Yields:
            Chunks of generated content
        """
        pass
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        Send a chat conversation to the model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            **kwargs: Additional generation parameters
            
        Returns:
            LLMResponse object with generated content
        """
        # Default implementation converts chat to prompt
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        return self.generate(prompt, **kwargs)
    
    def extract_json(self, response: LLMResponse) -> Optional[Dict[str, Any]]:
        """
        Extract JSON data from LLM response.
        
        Args:
            response: LLMResponse object
            
        Returns:
            Parsed JSON dictionary or None if parsing fails
        """
        import json
        import re
        
        content = response.content
        
        # Try to find JSON in the content
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Try to parse entire content as JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return None
    
    def validate_response(self, response: LLMResponse) -> bool:
        """
        Validate that the response meets basic requirements.
        
        Args:
            response: LLMResponse object
            
        Returns:
            True if response is valid, False otherwise
        """
        if not response.content:
            return False
        if response.finish_reason == "length":
            return False  # Response was truncated
        return True
