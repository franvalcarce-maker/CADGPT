import streamlit as st
import os
import re
import requests

# Intentar importar CadQuery para la compilación real del archivo 3D
try:
    import cadquery as cq
except ImportError:
    cq = None

# Configuración de la página
st.set_page_config(page_title="CadGPT - 3D Studio", layout="wide", initial_sidebar_state="expanded")

# --- CONEXIÓN CON QWEN EN LM STUDIO ---
URL_API = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:1234/v1") + "/chat/completions"
MODELO = os.environ.get("QWEN_MODEL", "openai:qwen/qwen3.5-9b")

# --- INICIALIZACIÓN DEL ESTADO DE LA SESIÓN ---
if "historial" not in st.session_state:
    st.session_state.historial = [
        {"nombre": "Cubo_Base.stl", "prompt": "Un cubo simple de 20x20", "preview": "📦"}
    ]
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

def consultar_qwen_cadquery(prompt_usuario):
    system_instruction = (
        "You are a pure Python CadQuery code generator. "
        "DO NOT write any text, greetings, or explanations. "
        "ONLY output valid Python code."
    )

    payload = {
        "model": MODELO,
        "messages": [
            {"role": "system", "content": system_instruction},
            {
                "role": "user",
                "content": (
                    f"Generate a complete CadQuery python script for: '{prompt_usuario}'. Must start with 'import cadquery as cq' and end with 'result = ...'. Write the full script."
                )
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1000,
        "stop": []  # Esto es clave: vacío para que no se detenga por señales de fin estándar
    }
    try:
        response = requests.post(URL_API, json=payload, timeout=999)
        raw_text = response.json()['choices'][0]['message']['content']
        code_match = re.search(r"```python(.*?)```", raw_text, re.DOTALL)
        return code_match.group(1).strip() if code_match else raw_text.strip()
    except Exception as e:
        return f"# Error de conexión: {e}"

# --- RENDERIZADO VISUAL DE LA INTERFAZ ---
st.title("🤖 CadGPT — Generative AI 3D Studio")
st.caption("Escribe en lenguaje natural, genera topologías matemáticas con Qwen y descarga tu STL al instante.")

# Dibujar las 3 columnas principales
col_historial, col_visor, col_chat = st.columns([1.2, 2, 1.5])

# Panel 1: Historial de objetos
with col_historial:
    st.subheader("📁 Historial de Objetos")
    for item in st.session_state.historial:
        with st.container(border=True):
            col_icon, col_info = st.columns([1, 3])
            with col_icon:
                st.write(f"### {item['preview']}")
            with col_info:
                st.markdown(f"**{item['nombre']}**")
                st.caption(f"Prompt: {item['prompt']}")
            st.button("Visualizar", key=item['nombre'])

# Panel 2: Visor central 3D
with col_visor:
    st.subheader("👁️ Visor 3D Interactivo")
    with st.container(border=True):
        st.info("Renderizando espacio topológico... Listo para recibir datos de malla.")
        st.image("https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=600&auto=format&fit=crop",
                 caption="[Vista de Malla Tridimensional Activa]", use_container_width=True)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.button("📥 Descargar Archivo .STL", use_container_width=True)
        with col_btn2:
            st.button("🔄 Regenerar Geometría", use_container_width=True)

# Panel 3: El chat interactivo con el historial visible
with col_chat:
    st.subheader("💬 Asistente de Diseño")

    # Caja contenedora del chat con tamaño fijo y scroll automático
    with st.container(height=500, border=True):
        if not st.session_state.chat_history:
            st.write("El chat está limpio. Pídele algo a la IA para comenzar.")
        else:
            for chat in st.session_state.chat_history:
                with st.chat_message(chat["role"]):
                    st.write(chat["message"])
                    if "code" in chat:
                        st.code(chat["code"], language="python")

# --- CAPTURA DEL INPUT DEL USUARIO (PROCESAMIENTO INMEDIATO) ---
if prompt_usuario := st.chat_input("Ej: Haceme una silla con cuatro patas cilíndricas"):
    # 1. Registrar inmediatamente el mensaje del usuario
    st.session_state.chat_history.append({"role": "user", "message": prompt_usuario})

    # 2. Consultar al backend de Qwen
    codigo_generado = consultar_qwen_cadquery(prompt_usuario)

    # 3. Procesar la respuesta
    if codigo_generado and not codigo_generado.startswith("# Error"):
        # 1. Mostrar el código generado
        st.chat_message("assistant").code(codigo_generado, language="python")

        # 2. EL MOTOR DE CONSTRUCCIÓN: Esto ejecuta el código realmente
        st.write("⚙️ Construyendo el modelo 3D...")
        try:
            # Creamos un entorno seguro para ejecutar el código de la IA
            contexto_ejecucion = {"cq": cq}
            # Ejecutamos el código generado por la IA
            exec(codigo_generado, contexto_ejecucion)

            # Si la IA definió 'result', lo exportamos a STL
            if "result" in contexto_ejecucion:
                objeto_3d = contexto_ejecucion["result"]
                # Exportamos a un archivo físico
                cq.exporters.export(objeto_3d, "modelo_generado.stl")

                # 3. Mostrar botón de descarga
                with open("modelo_generado.stl", "rb") as f:
                    st.download_button(
                        label="📥 Descargar modelo generado (.stl)",
                        data=f,
                        file_name="modelo_generado.stl",
                        mime="application/octet-stream"
                    )
                st.success("¡Modelo listo para descargar!")
                
                # 4. Registrar la respuesta del asistente en el chat
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "message": "¡Topología calculada con éxito! Compilando archivo STL...",
                    "code": codigo_generado
                })

                # 5. Agregar el objeto creado de forma dinámica al panel izquierdo
                nuevo_indice = len(st.session_state.historial) + 1
                st.session_state.historial.append({
                    "nombre": f"Objeto_{nuevo_indice:02d}.stl",
                    "prompt": prompt_usuario,
                    "preview": "📐"
                })
            else:
                st.error("El código no definió la variable 'result'.")
        except Exception as e:
            st.error(f"Error al compilar el modelo 3D: {e}")
            st.session_state.chat_history.append({
                "role": "assistant",
                "message": f"Error al compilar: {e}",
                "code": codigo_generado
            })
    else:
        st.session_state.chat_history.append({
            "role": "assistant",
            "message": "Hubo un problema al conectar con el servidor de la IA. Asegúrate de que LM Studio esté encendido."
        })

    # 6. Forzar redibujado con los nuevos datos cargados
    st.rerun()
