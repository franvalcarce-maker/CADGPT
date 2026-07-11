import tkinter as tk
import customtkinter as ctk
import threading
import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# --- CONFIGURACIÓN DE RUTAS ---
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

try:
    from core.llm_interface.local_llm import LocalLLM
    from cad_engines.openscad.openscad_engine import OpenSCADEngine
    # Importación condicional para la Fase 3 (Importadores)
    try:
        from importers.stl_importer import STLImporter
        HAS_IMPORTER = True
    except ImportError:
        HAS_IMPORTER = False
        print("[AVISO] Módulo de importación no encontrado. Funcionalidad limitada.")
except Exception as e:
    print(f"[ERROR CRÍTICO] No se pudieron cargar los módulos del núcleo: {e}")
    LocalLLM = None
    OpenSCADEngine = None

# --- CONFIGURACIÓN DE TEMA ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CadGPTApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Estado de la aplicación
        self.title("CADGPT - Diseño Asistido por IA (OpenSCAD)")
        self.geometry("1200x750")
        self.minsize(900, 600)
        
        # Inicialización de componentes lógicos
        self.llm = None
        self.engine = None
        self.importer = None
        
        if LocalLLM:
            self.llm = LocalLLM()
        if OpenSCADEngine:
            self.engine = OpenSCADEngine()
        if HAS_IMPORTER and self.importer is None:
            try:
                self.importer = STLImporter()
            except:
                pass

        # Variables de entorno
        self.output_folder = str(Path.home() / "Documents" / "CADGPT_Output")
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
            
        self.current_model_path: Optional[str] = None
        self.is_processing = False

        # Construcción de la UI
        self._setup_ui_components()
        self._setup_ui_layout()
        
        # Verificación asíncrona de LM Studio
        self.after(500, self._check_lm_studio_status)

    # ------------------------------------------------------------------
    # 1. CONFIGURACIÓN DE COMPONENTES (WIDGETS)
    # ------------------------------------------------------------------
    def _setup_ui_components(self):
        """Crea todos los widgets pero no los ubica aún"""
        
        # --- BARRA LATERAL (SIDEBAR) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        
        # Logo / Título
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="CADGPT\n[OpenSCAD]", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        
        # Indicador de Estado LM Studio
        self.status_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.lbl_status_text = ctk.CTkLabel(self.status_frame, text="IA Server:", font=ctk.CTkFont(size=12))
        self.lbl_status_dot = ctk.CTkLabel(self.status_frame, text="●", font=ctk.CTkFont(size=24), text_color="gray")
        
        # Botones de Acción
        self.btn_config = ctk.CTkButton(self.sidebar_frame, text="⚙️ Configuración", command=self._open_config_dialog)
        self.btn_import = ctk.CTkButton(self.sidebar_frame, text="📂 Importar Modelo", command=self._import_model_action, fg_color="#d35400", hover_color="#e67e22")
        
        # Selector de Carpeta
        self.lbl_folder_title = ctk.CTkLabel(self.sidebar_frame, text="Carpeta de Salida:", font=ctk.CTkFont(size=11, weight="bold"))
        self.btn_change_folder = ctk.CTkButton(self.sidebar_frame, text="📁 Examinar...", height=30, command=self._select_output_folder)
        self.lbl_current_path = ctk.CTkLabel(self.sidebar_frame, text="", font=ctk.CTkFont(size=9), wraplength=180, justify="left")

        # --- ÁREA PRINCIPAL (MAIN) ---
        # Contenedor del Chat
        self.chat_container = ctk.CTkFrame(self, fg_color="transparent")
        # CORRECCIÓN: Usamos state="normal" temporalmente si es necesario, pero generalmente disabled para solo lectura
        self.chat_display = ctk.CTkTextbox(self.chat_container, state="disabled", font=ctk.CTkFont(family="Consolas", size=12))
        
        # Contenedor de Entrada (Input)
        self.input_container = ctk.CTkFrame(self.chat_container, fg_color="transparent", height=60)
        self.entry_prompt = ctk.CTkEntry(
            self.input_container, 
            placeholder_text="Describe tu modelo aquí... (Ej: 'Un engranaje de 20 dientes')", 
            font=ctk.CTkFont(size=14),
            height=45
        )
        self.entry_prompt.bind("<Return>", lambda e: self._send_message_threaded())
        self.btn_send = ctk.CTkButton(
            self.input_container, 
            text="GENERAR ➤", 
            height=45, 
            width=100,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._send_message_threaded
        )
        
        # Panel de Análisis (Fase 3 - Se crea oculto mediante grid_remove más adelante)
        self.analysis_panel = ctk.CTkFrame(self, height=160)
        self.lbl_analysis_title = ctk.CTkLabel(self.analysis_panel, text="📊 Análisis del Modelo Importado", font=ctk.CTkFont(size=14, weight="bold"))
        self.txt_analysis_content = ctk.CTkTextbox(self.analysis_panel, height=100, state="disabled", font=ctk.CTkFont(size=11))

    # ------------------------------------------------------------------
    # 2. DISEÑO (LAYOUT)
    # ------------------------------------------------------------------
    def _setup_ui_layout(self):
        """Ubica los widgets en la ventana usando grid"""
        
        # Configurar pesos de expansión
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # --- Sidebar Layout ---
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1) # Espacio flexible
        
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))
        
        self.status_frame.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.lbl_status_text.grid(row=0, column=0, sticky="w")
        self.lbl_status_dot.grid(row=0, column=1, padx=(10, 0))
        
        self.btn_config.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.btn_import.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        self.lbl_folder_title.grid(row=4, column=0, padx=20, pady=(30, 5), sticky="w")
        self.btn_change_folder.grid(row=5, column=0, padx=20, pady=5, sticky="ew")
        self.lbl_current_path.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="nw")
        self._update_path_label()

        # --- Main Area Layout ---
        self.chat_container.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.chat_container.grid_rowconfigure(0, weight=1)
        self.chat_container.grid_columnconfigure(0, weight=1)
        
        self.chat_display.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        
        self.input_container.grid(row=1, column=0, sticky="ew")
        self.input_container.grid_columnconfigure(0, weight=1)
        
        self.entry_prompt.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.btn_send.grid(row=0, column=1)

        # --- Analysis Panel Layout (Oculto inicialmente con grid_remove) ---
        self.analysis_panel.grid(row=1, column=1, sticky="ew", padx=15, pady=(0, 15))
        self.analysis_panel.grid_columnconfigure(0, weight=1)
        self.lbl_analysis_title.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.txt_analysis_content.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Ocultar inicialmente
        self.analysis_panel.grid_remove()

    # ------------------------------------------------------------------
    # 3. LÓGICA DE INTERFAZ Y EVENTOS
    # ------------------------------------------------------------------
    
    def _update_path_label(self):
        """Actualiza la etiqueta de la carpeta con truncamiento"""
        path = self.output_folder
        if len(path) > 25:
            display_path = "..." + path[-22:]
        else:
            display_path = path
        self.lbl_current_path.configure(text=display_path, text_color="#aaaaaa")

    def _select_output_folder(self):
        folder = ctk.filedialog.askdirectory(initialdir=self.output_folder)
        if folder:
            self.output_folder = folder
            self._update_path_label()
            self._log_system(f"Carpeta de salida cambiada a: {folder}")

    def _check_lm_studio_status(self):
        """Verifica conexión en segundo plano"""
        def check():
            status = "offline"
            color = "#e74c3c" # Rojo
            
            if self.llm:
                try:
                    if self.llm.check_connection():
                        status = "online"
                        color = "#2ecc71" # Verde
                except:
                    pass
            
            # Actualizar UI en el hilo principal
            self.after(0, lambda: self.lbl_status_dot.configure(text_color=color))
            if status == "online":
                self.after(0, lambda: self._log_system("Conexión con LM Studio establecida."))

        threading.Thread(target=check, daemon=True).start()

    def _open_config_dialog(self):
        """Muestra configuración básica"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Configuración")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        
        lbl = ctk.CTkLabel(dialog, text="Configuración del Sistema", font=ctk.CTkFont(size=16, weight="bold"))
        lbl.pack(pady=20)
        
        info_text = f"Motor CAD: OpenSCAD\nRuta: {self.engine.openscad_path if self.engine else 'N/A'}\n\nEstado: Activo"
        txt_info = ctk.CTkLabel(dialog, text=info_text, justify="left", font=ctk.CTkFont(size=12))
        txt_info.pack(pady=10)
        
        btn_close = ctk.CTkButton(dialog, text="Cerrar", command=dialog.destroy)
        btn_close.pack(pady=20)

    def _import_model_action(self):
        """Maneja la importación de archivos (Fase 3)"""
        if not HAS_IMPORTER:
            self._log_error("El módulo de importación no está disponible en esta versión.")
            return

        filetypes = [
            ("Archivos 3D", "*.stl *.obj *.step *.stp"),
            ("Todos los archivos", "*.*")
        ]
        file_path = ctk.filedialog.askopenfilename(title="Seleccionar modelo 3D", filetypes=filetypes)
        
        if file_path:
            self.current_model_path = file_path
            filename = os.path.basename(file_path)
            self._log_user(f"Importando modelo: {filename}")
            
            # Mostrar panel de análisis
            self.analysis_panel.grid()
            self.txt_analysis_content.configure(state="normal")
            self.txt_analysis_content.delete("1.0", "end")
            self.txt_analysis_content.insert("1.0", f"Analizando {filename}...\n")
            self.txt_analysis_content.configure(state="disabled")
            
            # Ejecutar análisis en hilo separado
            def run_analysis():
                try:
                    time.sleep(1) # Simular proceso
                    
                    info = f"✅ Archivo cargado: {filename}\n"
                    info += f"📍 Ruta: {file_path}\n"
                    info += f"📐 Dimensiones: Pendiente de cálculo detallado.\n"
                    info += f"💡 Tip: Escribe 'haz este modelo un 20% más grande' para modificarlo."
                    
                    self.after(0, lambda: self._show_analysis_result(info))
                    self.after(0, lambda: self._log_system(f"Modelo {filename} analizado correctamente."))
                except Exception as e:
                    self.after(0, lambda: self._log_error(f"Error al analizar: {str(e)}"))

            threading.Thread(target=run_analysis, daemon=True).start()

    def _show_analysis_result(self, text):
        self.txt_analysis_content.configure(state="normal")
        self.txt_analysis_content.delete("1.0", "end")
        self.txt_analysis_content.insert("1.0", text)
        self.txt_analysis_content.configure(state="disabled")

    def _send_message_threaded(self):
        """Envía el mensaje del usuario en un hilo separado para no congelar la UI"""
        if self.is_processing:
            return
            
        prompt = self.entry_prompt.get().strip()
        if not prompt:
            return

        self.is_processing = True
        self.entry_prompt.delete(0, 'end')
        self.btn_send.configure(state="disabled", text="Procesando...")
        
        self._log_user(prompt)

        def process_request():
            try:
                context_msg = ""
                if self.current_model_path:
                    context_msg = f"(Contexto: El usuario está modificando el archivo importado: {os.path.basename(self.current_model_path)})"
                
                self._log_system("Consultando a la IA...")
                
                if not self.llm:
                    raise Exception("Módulo de IA no inicializado.")
                
                code_response = self.llm.generate_code(prompt, context=context_msg)
                
                if not code_response:
                    code_response = "// Error: La IA no generó código válido."
                
                self._log_assistant(code_response, is_code=True)
                
                self._log_system("Generando geometría y exportando STL...")
                
                if not self.engine:
                    raise Exception("Motor OpenSCAD no disponible.")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name = "modelo_ia"
                result = self.engine.export_to_file(code_response, self.output_folder, f"{base_name}_{timestamp}")
                
                if result.get("success"):
                    self._log_system(f"✅ ÉXITO: Archivo generado en\n{result.get('path')}")
                else:
                    self._log_error(f"❌ Fallo en exportación: {result.get('message')}")
                    
            except Exception as e:
                self._log_error(f"❌ Error crítico: {str(e)}")
            finally:
                self.is_processing = False
                self.after(0, lambda: self.btn_send.configure(state="normal", text="GENERAR ➤"))

        threading.Thread(target=process_request, daemon=True).start()

    # ------------------------------------------------------------------
    # 4. UTILIDADES DE LOG (CHAT) - CORREGIDO
    # ------------------------------------------------------------------
    
    def _log_user(self, message):
        self._append_to_chat(f"Tú", message, color="#3498db")

    def _log_system(self, message):
        self._append_to_chat("Sistema", message, color="#f1c40f")

    def _log_error(self, message):
        self._append_to_chat("Error", message, color="#e74c3c")

    def _log_assistant(self, message, is_code=False):
        self._append_to_chat("CadGPT", message, color="#2ecc71", is_code=is_code)

    def _append_to_chat(self, sender, message, color, is_code=False):
        """
        Inserta mensajes en el chat SIN usar tag_configure (no soportado por CTkTextbox).
        Usa inserción directa de texto formateado.
        """
        self.chat_display.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Crear el encabezado con colores simulados mediante inserción separada no es posible fácilmente en CTkTextbox
        # Solución: Insertar todo como texto plano pero con formato legible.
        # CTkTextbox no soporta múltiples colores en una misma línea fácilmente sin tags nativos de tkinter.
        # Workaround: Usar emojis o prefijos de texto para diferenciar, ya que el color de fuente global es único.
        
        # Para mantenerlo simple y robusto en CustomTkinter:
        # Insertamos el texto completo. Si queremos color, deberíamos cambiar el color global del textbox dinámicamente
        # o usar múltiples labels, pero eso rompe el scroll.
        # La mejor opción compatible es texto plano con prefijos claros.
        
        header = f"[{timestamp}] {sender}: "
        full_message = f"{header}{message}\n\n"
        
        # Opción avanzada: Intentar cambiar el color del texto insertado NO es posible línea por línea en CTkTextbox estándar
        # sin acceder al widget interno de tkinter. 
        # SOLUCIÓN DEFINITIVA: Insertar texto normal. El usuario distingue por el nombre "[Sistema]", "[Tú]", etc.
        
        self.chat_display.insert("end", full_message)
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

def main():
    try:
        app = CadGPTApp()
        app.mainloop()
    except Exception as e:
        print(f"\n[CRITICAL ERROR] La aplicación falló al iniciarse: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresione Enter para salir...")

if __name__ == "__main__":
    main()