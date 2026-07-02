import os
import re
import requests

def generate_cadquery_code(user_prompt):
    """
    Conecta con el servidor local de LM Studio para traducir la petición
    en lenguaje natural del usuario a un script puro de CadQuery.
    """
    url = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1") + "/chat/completions"
    model = os.environ.get("QWEN_MODEL", "openai:qwen/qwen3.5-9b")
    
    system_instruction = (
        "You are an expert 3D modeling assistant specializing in CadQuery.\n"
        "Your task is to write ONLY valid Python code using the `cadquery` library based on the user's request.\n"
        "Requirements:\n"
        "1. Do not explain anything. Do not write markdown text outside the code block.\n"
        "2. The final shape MUST be assigned to a global variable named `result` (e.g., result = cq.Workplane(...)).\n"
        "3. Keep the geometry clean, parametric, and functional."
    )
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Create a 3D model for: '{user_prompt}'. Remember to assign the final object to the variable 'result'."}
        ],
        "temperature": 0.2
    }
    
    try:
        print("\n[AI] Pensando la estructura geométrica en 3D...")
        response = requests.post(url, json=payload, timeout=60)
        response_json = response.json()
        raw_text = response_json['choices'][0]['message']['content']
        
        # Extraer limpiamente el bloque de código de Python
        code_match = re.search(r"```python(.*?)```", raw_text, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        return raw_text.strip()
        
    except Exception as e:
        print(f"[Error] No se pudo conectar con LM Studio: {e}")
        return None