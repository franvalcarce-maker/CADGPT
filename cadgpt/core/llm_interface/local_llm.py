"""
Local LLM Interface

Implementation for local LLM providers (LM Studio, Ollama, etc.)
"""

import requests
from typing import Optional, Dict, Any, List, Generator
from .base_llm import BaseLLM, LLMResponse


class LocalLLM(BaseLLM):
    """
    Local LLM interface compatible with LM Studio and Ollama APIs.

    Supports OpenAI-compatible API endpoints running locally.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        model_name: str = "local-model",
        api_key: str = "not-needed",
        timeout: int = 120,
        **kwargs
    ):
        """
        Initialize the Local LLM interface.

        Args:
            base_url: Base URL of the local LLM server
            model_name: Name of the model to use
            api_key: API key (usually not needed for local servers)
            timeout: Request timeout in seconds
            **kwargs: Additional configuration options
        """
        super().__init__(model_name=model_name, **kwargs)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}" if api_key else ""
        }

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.95,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a response from the local LLM.

        Args:
            prompt: Input prompt text
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            **kwargs: Additional OpenAI-compatible parameters

        Returns:
            LLMResponse object with generated content
        """
        endpoint = f"{self.base_url}/chat/completions"

        # Instrucciones de formato para la IA generadora de código 3D
        system_instructions = (
            "Instrucciones de formato: solo entrega el código fuente, "
            "sin explicaciones, sin razonamiento paso a paso, "
            "sin introducciones ni conclusiones. "
            "Formato de salida: bloque de código puro."
        )

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            **kwargs
        }

        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            choice = data["choices"][0]

            return LLMResponse(
                content=choice["message"]["content"],
                model=data.get("model", self.model_name),
                usage=data.get("usage"),
                finish_reason=choice.get("finish_reason"),
                metadata={"raw_response": data}
            )

        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to LLM server at {self.base_url}. "
                "Ensure LM Studio or Ollama is running."
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out after {self.timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {str(e)}")

    def generate_streaming(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Generate a streaming response from the local LLM.

        Args:
            prompt: Input prompt text
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Yields:
            Chunks of generated content
        """
        endpoint = f"{self.base_url}/chat/completions"

        # Instrucciones de formato para la IA generadora de código 3D
        system_instructions = (
            "Instrucciones de formato: solo entrega el código fuente, "
            "sin explicaciones, sin razonamiento paso a paso, "
            "sin introducciones ni conclusiones. "
            "Formato de salida: bloque de código puro."
        )

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs
        }

        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            import json
                            data = json.loads(data_str)
                            if data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to LLM server at {self.base_url}"
            )
        except Exception as e:
            raise RuntimeError(f"Streaming request failed: {str(e)}")

    def health_check(self) -> bool:
        """
        Check if the LLM server is available.

        Returns:
            True if server is reachable, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> List[str]:
        """
        List available models on the server.

        Returns:
            List of model names
        """
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return [model["id"] for model in data.get("data", [])]
        except:
            return []
