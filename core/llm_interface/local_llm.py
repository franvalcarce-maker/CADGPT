import requests
import json
import re
import os
from typing import Optional, Dict, Any, List
from pathlib import Path

class LocalLLM:
    """
    Interfaz para conectar con modelos de lenguaje locales (LM Studio, Ollama, etc.)
    mediante la API compatible con OpenAI.
    """

    def __init__(self, base_url: str = "http://localhost:1234/v1", model_name: str = "auto"):
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.session = requests.Session()
        
        # Intentar cargar configuración desde archivo si existe
        self._load_config()

    def _load_config(self):
        """Carga configuración desde config.json si está disponible"""
        config_path = Path(__file__).parent.parent.parent / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'lm_studio_url' in config:
                        self.base_url = config['lm_studio_url']
                    if 'lm_studio_model' in config and config['lm_studio_model'] != "auto":
                        self.model_name = config['lm_studio_model']
                print(f"[INFO] Configuración LLM cargada: {self.base_url}")
            except Exception as e:
                print(f"[AVISO] No se pudo leer config.json: {e}")

    def check_connection(self) -> bool:
        """
        Verifica si el servidor LM Studio está accesible.
        Retorna True si responde correctamente, False en caso contrario.
        """
        try:
            # Endpoint estándar para listar modelos (funciona en LM Studio)
            response = self.session.get(f"{self.base_url}/models", timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                if models:
                    print(f"[OK] LM Studio conectado. Modelos disponibles: {len(models)}")
                    # Si el modelo es "auto", usamos el primero disponible
                    if self.model_name == "auto" and models:
                        self.model_name = models[0].get("id", "unknown")
                        print(f"[INFO] Usando modelo detectado: {self.model_name}")
                    return True
                else:
                    print("[WARN] LM Studio responde pero no hay modelos cargados.")
                    return False
            else:
                print(f"[ERROR] LM Studio respondió con estado {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            print("[ERROR] No se pudo conectar a LM Studio. ¿Está el servidor encendido?")
            return False
        except requests.exceptions.Timeout:
            print("[ERROR] Tiempo de espera agotado al conectar con LM Studio.")
            return False
        except Exception as e:
            print(f"[ERROR] Error inesperado verificando conexión: {e}")
            return False

    def generate_code(self, prompt: str, context: str = "", temperature: float = 0.7) -> str:
        """
        Envía un prompt a la IA para generar código OpenSCAD.
        Limpia la respuesta para devolver solo el código útil.
        """
        if not self.check_connection():
            return "// Error: No hay conexión con el servidor de IA (LM Studio)."

        # Construcción del prompt de sistema para forzar comportamiento de experto CAD
        system_prompt = (
            "Eres un experto ingeniero de software especializado en OpenSCAD y diseño paramétrico. "
            "Tu tarea es convertir instrucciones de lenguaje natural en código OpenSCAD válido y completo. "
            "REGLAS ESTRICTAS:\n"
            "1. Responde ÚNICAMENTE con el código OpenSCAD. Sin explicaciones, sin markdown (```), sin texto antes o después.\n"
            "2. El código debe ser funcional y estar listo para copiar y pegar en un archivo .scad.\n"
            "3. Si se piden formas complejas (engranajes, roscas), usa bucles 'for' y matemáticas precisas.\n"
            "4. Si el usuario pide modificar un modelo existente, asume que el contexto es la base y genera el código completo resultante.\n"
            "5. No incluyas comentarios explicativos largos, solo los necesarios para parámetros."
        )

        user_message = f"{context}\nInstrucción de diseño: {prompt}"

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": temperature,
            "max_tokens": 4096, # Permitir respuestas largas para geometrías complejas
            "stream": False
        }

        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=300 # Timeout de 300 segundos para generación compleja
            )
            
            if response.status_code == 200:
                data = response.json()
                raw_content = data["choices"][0]["message"]["content"]
                
                # Limpieza robusta del código generado
                clean_code = self._clean_code_response(raw_content)
                
                if not clean_code:
                    return "// Error: La IA generó una respuesta vacía o inválida."
                
                return clean_code
            else:
                error_msg = response.text
                return f"// Error del servidor IA ({response.status_code}): {error_msg}"

        except requests.exceptions.Timeout:
            return "// Error: La IA tardó demasiado en responder. Intenta simplificar la solicitud."
        except Exception as e:
            return f"// Error crítico al comunicarse con la IA: {str(e)}"

    def _clean_code_response(self, text: str) -> str:
        """
        Elimina bloques de markdown (```), explicaciones y texto basura,
        dejando solo el código OpenSCAD puro.
        """
        if not text:
            return ""

        # 1. Eliminar bloques de código markdown ```openscad ... ``` o ``` ... ```
        code_block_pattern = r"```(?:openscad)?\s*(.*?)\s*```"
        matches = re.findall(code_block_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            # Si hay bloques de código, tomamos el primero (o podríamos unirlos si son múltiples)
            code = matches[0].strip()
        else:
            # Si no hay bloques markdown, asumimos que todo el texto es código o hay que limpiarlo
            # Eliminamos líneas que parecen explicaciones comunes (empiezan con "Aquí tienes...", "Claro...", etc.)
            lines = text.split('\n')
            clean_lines = []
            for line in lines:
                stripped = line.strip()
                # Filtrar frases típicas de IA
                if any(phrase in stripped.lower() for phrase in ["aquí tienes", "here is", "claro", "sure", "espero que te sirva", "hope this helps"]):
                    continue
                clean_lines.append(line)
            code = '\n'.join(clean_lines).strip()

        # 2. Limpieza final de espacios y saltos de línea excesivos
        code = re.sub(r'\n\s*\n\s*\n', '\n\n', code)
        
        return code