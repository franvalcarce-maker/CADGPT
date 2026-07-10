"""
LLM Interface Module

Provides abstract base classes and implementations for Language Model interfaces.
"""

from .base_llm import BaseLLM
from .local_llm import LocalLLM

__all__ = ["BaseLLM", "LocalLLM"]
