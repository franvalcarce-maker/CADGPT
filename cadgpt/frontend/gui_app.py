#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CadGPT - Interfaz Gráfica de Usuario
Interfaz moderna con chat, selección de motor CAD y carpeta de salida.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
import sys
from pathlib import Path
from datetime import datetime

# Agregar el path del proyecto (raíz de cadgpt)
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from cad_engines import create_engine
from core.orchestration.agent_orchestrator import AgentOrchestrator
from core.llm_interface.local_llm import LocalLLM
from core.memory.session_memory import SessionMemory


class CadGPTApp(ctk.CTk):
    """Aplicación principal de CadGPT con interfaz gráfica."""
    
    def __init__(self):
        super().__init__()
        
        # Configuración de la ventana principal
        self.title("CadGPT - IA para Modelado CAD")
        self.geometry("1200x800")
        self.minsize(900, 600)
        
        # Configurar tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Variables de estado
        self.selected_engine = "OpenSCAD"
        self.output_folder = str(Path(__file__).parent / "output")
        self.is_processing = False
        self.session_memory = SessionMemory()
        self.orchestrator = None
        
        # Inicializar componentes
        self._setup_ui()
        self._initialize_engines()
        
    def _setup_ui(self):
        """Configurar la interfaz de usuario."""
        
        # Grid configuration
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ===== PANEL LATERAL (IZQUIERDO) =====
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)
        
        # Logo/Título
        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="🏗️ CadGPT", 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.subtitle_label = ctk.CTkLabel(
            self.sidebar, 
            text="IA para Modelado CAD", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20))
        
        # Separador
        separator = ctk.CTkFrame(self.sidebar, height=2, fg_color="gray")
        separator.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        # ===== SELECCIÓN DE MOTOR CAD =====
        self.engine_label = ctk.CTkLabel(
            self.sidebar, 
            text="Motor CAD:", 
            font=ctk.CTkFont(weight="bold")
        )
        self.engine_label.grid(row=3, column=0, padx=20, pady=(10, 5), sticky="w")
        
        self.engine_var = ctk.StringVar(value="OpenSCAD")
        self.engine_menu = ctk.CTkOptionMenu(
            self.sidebar,
            variable=self.engine_var,
            values=["OpenSCAD", "Blender", "FreeCAD"],
            command=self._on_engine_change,
            font=ctk.CTkFont(size=14)
        )
        self.engine_menu.grid(row=4, column=0, padx=20, pady=5, sticky="ew")
        
        # Información del motor
        self.engine_info = ctk.CTkTextbox(
            self.sidebar,
            height=100,
            font=ctk.CTkFont(size=11)
        )
        self.engine_info.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        self.engine_info.insert("0.0", self._get_engine_description("OpenSCAD"))
        self.engine_info.configure(state="disabled")
        
        # ===== CARPETA DE SALIDA =====
        self.folder_label = ctk.CTkLabel(
            self.sidebar, 
            text="Carpeta de Salida:", 
            font=ctk.CTkFont(weight="bold")
        )
        self.folder_label.grid(row=6, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.folder_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.folder_frame.grid(row=7, column=0, padx=20, pady=5, sticky="ew")
        
        self.folder_entry = ctk.CTkEntry(
            self.folder_frame,
            placeholder_text="Seleccionar carpeta...",
            font=ctk.CTkFont(size=12)
        )
        self.folder_entry.grid(row=0, column=0, sticky="ew")
        self.folder_entry.insert(0, self.output_folder)
        
        self.folder_btn = ctk.CTkButton(
            self.folder_frame,
            text="📁",
            width=40,
            command=self._select_output_folder
        )
        self.folder_btn.grid(row=0, column=1, padx=(5, 0))
        
        # ===== FORMATOS DE EXPORTACIÓN =====
        self.format_label = ctk.CTkLabel(
            self.sidebar, 
            text="Formato de Exportación:", 
            font=ctk.CTkFont(weight="bold")
        )
        self.format_label.grid(row=8, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.format_var = ctk.StringVar(value="STL")
        self.format_menu = ctk.CTkOptionMenu(
            self.sidebar,
            variable=self.format_var,
            values=["STL", "OBJ", "STEP", "DXF"],
            font=ctk.CTkFont(size=12)
        )
        self.format_menu.grid(row=9, column=0, padx=20, pady=5, sticky="ew")
        
        # ===== BOTONES DE ACCIÓN =====
        self.btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.btn_frame.grid(row=10, column=0, padx=20, pady=20, sticky="ew")
        
        self.generate_btn = ctk.CTkButton(
            self.btn_frame,
            text="⚡ Generar Modelo",
            height=45,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._generate_model,
            fg_color="#2ecc71"
        )
        self.generate_btn.grid(row=0, column=0, pady=5, sticky="ew")
        
        self.clear_btn = ctk.CTkButton(
            self.btn_frame,
            text="🗑️ Limpiar Chat",
            height=35,
            command=self._clear_chat,
            fg_color="#e74c3c"
        )
        self.clear_btn.grid(row=1, column=0, pady=5, sticky="ew")
        
        self.open_folder_btn = ctk.CTkButton(
            self.btn_frame,
            text="📂 Abrir Carpeta",
            height=35,
            command=self._open_output_folder
        )
        self.open_folder_btn.grid(row=2, column=0, pady=5, sticky="ew")
        
        # ===== ESTADO =====
        self.status_label = ctk.CTkLabel(
            self.sidebar,
            text="● Listo",
            font=ctk.CTkFont(size=12),
            text_color="#2ecc71"
        )
        self.status_label.grid(row=11, column=0, padx=20, pady=(20, 10), sticky="w")
        
        # ===== ÁREA PRINCIPAL (DERECHA) =====
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        
        # ===== CHAT AREA =====
        self.chat_container = ctk.CTkFrame(self.main_area)
        self.chat_container.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.chat_container.grid_columnconfigure(0, weight=1)
        self.chat_container.grid_rowconfigure(0, weight=1)
        
        # Chat display (historial)
        self.chat_display = ctk.CTkTextbox(
            self.chat_container,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word",
            state="disabled"
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configurar tags para colores
        self.chat_display.tag_config("user", foreground="#3498db")
        self.chat_display.tag_config("assistant", foreground="#2ecc71")
        self.chat_display.tag_config("system", foreground="#f39c12")
        self.chat_display.tag_config("error", foreground="#e74c3c")
        self.chat_display.tag_config("code", foreground="#9b59b6")
        
        # ===== INPUT AREA =====
        self.input_frame = ctk.CTkFrame(self.main_area)
        self.input_frame.grid(row=1, column=0, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        self.chat_input = ctk.CTkTextbox(
            self.input_frame,
            height=80,
            font=ctk.CTkFont(family="Arial", size=13),
            wrap="word"
        )
        self.chat_input.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.chat_input.bind("<Return>", self._on_enter_key)
        self.chat_input.bind("<Shift-Return>", lambda e: None)  # Permitir Shift+Enter
        
        self.send_btn = ctk.CTkButton(
            self.input_frame,
            text="Enviar ➤",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._send_message
        )
        self.send_btn.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Mensaje de bienvenida
        self._add_welcome_message()
        
    def _initialize_engines(self):
        """Inicializar los motores CAD disponibles."""
        self.engines = {}
        try:
            for engine_name in ["OpenSCAD", "Blender", "FreeCAD"]:
                self.engines[engine_name] = create_engine(engine_name.lower())
        except Exception as e:
            messagebox.showerror("Error", f"Error al inicializar motores: {str(e)}")
            
    def _get_engine_description(self, engine_name):
        """Obtener descripción del motor seleccionado."""
        descriptions = {
            "OpenSCAD": "Motor de modelado paramétrico basado en código. Ideal para piezas técnicas y geometrías precisas. Exporta a STL, DXF.",
            "Blender": "Software de modelado 3D completo. Soporta mallas complejas, materiales y renderizado. Exporta a STL, OBJ, FBX, GLTF.",
            "FreeCAD": "CAD paramétrico de código abierto. Perfecto para diseño mecánico y arquitectura. Exporta a STEP, STL, IFC, DXF."
        }
        return descriptions.get(engine_name, "")
        
    def _on_engine_change(self, new_engine):
        """Manejar cambio de motor CAD."""
        self.selected_engine = new_engine
        self.engine_info.configure(state="normal")
        self.engine_info.delete("0.0", "end")
        self.engine_info.insert("0.0", self._get_engine_description(new_engine))
        self.engine_info.configure(state="disabled")
        
        # Actualizar formatos disponibles
        formats = {
            "OpenSCAD": ["STL", "DXF", "SVG"],
            "Blender": ["STL", "OBJ", "FBX", "GLTF"],
            "FreeCAD": ["STL", "STEP", "DXF", "IFC"]
        }
        current_format = self.format_var.get()
        available_formats = formats.get(new_engine, ["STL"])
        self.format_menu.configure(values=available_formats)
        if current_format not in available_formats:
            self.format_var.set(available_formats[0])
            
    def _select_output_folder(self):
        """Seleccionar carpeta de salida."""
        folder = filedialog.askdirectory(initialdir=self.output_folder)
        if folder:
            self.output_folder = folder
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            
    def _open_output_folder(self):
        """Abrir carpeta de salida en el explorador."""
        try:
            os.startfile(self.output_folder)  # Windows
        except AttributeError:
            os.system(f"xdg-open {self.output_folder}")  # Linux
        except Exception:
            os.system(f"open {self.output_folder}")  # Mac
            
    def _add_welcome_message(self):
        """Agregar mensaje de bienvenida al chat."""
        welcome_msg = """╔══════════════════════════════════════════════════╗
║     🎉 ¡Bienvenido a CadGPT!                      ║
║                                                    ║
║  Soy tu asistente de IA especializado en CAD.      ║
║  Puedo ayudarte a:                                 ║
║                                                    ║
║  • Generar modelos 3D desde lenguaje natural       ║
║  • Crear geometrías paramétricas                   ║
║  • Exportar a múltiples formatos (STL, STEP, etc.) ║
║                                                    ║
║  Ejemplos de comandos:                             ║
║  "Genera un cubo de 100mm de lado"                 ║
║  "Crea una esfera hueca de 5cm de diámetro"        ║
║  "Diseña un cilindro con agujero central"          ║
╚══════════════════════════════════════════════════╝"""
        self._add_message_to_chat(welcome_msg, "system")
        
    def _add_message_to_chat(self, message, sender):
        """Agregar mensaje al historial del chat."""
        self.chat_display.configure(state="normal")
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if sender == "user":
            prefix = f"\n[{timestamp}] Tú:\n"
            tag = "user"
        elif sender == "assistant":
            prefix = f"\n[{timestamp}] CadGPT:\n"
            tag = "assistant"
        elif sender == "system":
            prefix = "\n"
            tag = "system"
        else:
            prefix = "\n"
            tag = "error"
            
        self.chat_display.insert("end", prefix, tag)
        self.chat_display.insert("end", message + "\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")
        
    def _on_enter_key(self, event):
        """Manejar tecla Enter para enviar mensaje."""
        if not event.state & 0x1:  # Sin Shift
            self._send_message()
            return "break"
        return None
        
    def _send_message(self):
        """Enviar mensaje del usuario."""
        if self.is_processing:
            messagebox.showwarning("Procesando", "Por favor espera a que termine el proceso actual.")
            return
            
        message = self.chat_input.get("0.0", "end").strip()
        if not message:
            return
            
        # Agregar mensaje del usuario al chat
        self._add_message_to_chat(message, "user")
        self.chat_input.delete("0.0", "end")
        
        # Iniciar procesamiento en hilo separado
        self.is_processing = True
        self.status_label.configure(text="● Procesando...", text_color="#f39c12")
        self.generate_btn.configure(state="disabled")
        
        thread = threading.Thread(target=self._process_message, args=(message,))
        thread.daemon = True
        thread.start()
        
    def _process_message(self, message):
        """Procesar mensaje en segundo plano."""
        try:
            # Obtener configuración
            output_format = self.format_var.get()
            output_path = self.output_folder
            
            # Crear directorio si no existe
            os.makedirs(output_path, exist_ok=True)
            
            # Inicializar orquestador si es necesario
            if not self.orchestrator:
                # El orquestador crea su propia memoria interna
                self.orchestrator = AgentOrchestrator(default_engine=self.selected_engine.lower())
            
            # Seleccionar motor
            engine = self.engines.get(self.selected_engine)
            if not engine:
                raise ValueError(f"Motor {self.selected_engine} no disponible")
            
            # Generar código CAD
            self._add_message_to_chat(f"Generando código {self.selected_engine}...", "system")
            
            # Usar el parser del motor para interpretar el mensaje
            code_result = engine.generate_code(message)
            
            if not code_result.success:
                raise ValueError(f"Error al generar código: {code_result.error}")
            
            # Mostrar código generado
            code_preview = code_result.code[:500] + "..." if len(code_result.code) > 500 else code_result.code
            self._add_message_to_chat(f"Código generado:\n\n```{code_preview}```", "code")
            
            # Validar código
            self._add_message_to_chat("Validando geometría...", "system")
            validation = engine.validate_code(code_result.code)
            
            if not validation.is_valid:
                errors = "\n".join(validation.errors)
                self._add_message_to_chat(f"⚠️ Errores de validación:\n{errors}", "error")
            else:
                self._add_message_to_chat("✓ Validación exitosa", "assistant")
            
            # Exportar modelo
            filename = f"cadgpt_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            export_path = os.path.join(output_path, f"{filename}.{output_format.lower()}")
            
            self._add_message_to_chat(f"Exportando a {output_format}...", "system")
            export_result = engine.export_to_file(code_result.code, export_path, output_format)
            
            if export_result.success:
                self._add_message_to_chat(
                    f"✅ ¡Modelo generado exitosamente!\n\n"
                    f"📁 Archivo: {export_path}\n"
                    f"📊 Formato: {output_format}\n"
                    f"🔧 Motor: {self.selected_engine}",
                    "assistant"
                )
            else:
                self._add_message_to_chat(f"❌ Error al exportar: {export_result.error}", "error")
                
        except Exception as e:
            self._add_message_to_chat(f"❌ Error: {str(e)}", "error")
        finally:
            self.is_processing = False
            self.status_label.configure(text="● Listo", text_color="#2ecc71")
            self.generate_btn.configure(state="normal")
            
    def _generate_model(self):
        """Generar modelo desde el último mensaje del usuario."""
        # Obtener último mensaje del usuario del historial
        chat_content = self.chat_display.get("0.0", "end")
        lines = chat_content.split("\n")
        
        last_user_message = None
        for line in reversed(lines):
            if "Tú:" in line:
                idx = lines.index(line)
                if idx + 1 < len(lines):
                    last_user_message = lines[idx + 1].strip()
                    break
                    
        if last_user_message:
            self.chat_input.delete("0.0", "end")
            self.chat_input.insert("0.0", last_user_message)
            self._send_message()
        else:
            messagebox.showinfo("Información", "Primero escribe un comando en el chat.")
            
    def _clear_chat(self):
        """Limpiar el historial del chat."""
        if messagebox.askyesno("Confirmar", "¿Estás seguro de limpiar el chat?"):
            self.chat_display.configure(state="normal")
            self.chat_display.delete("0.0", "end")
            self.chat_display.configure(state="disabled")
            self._add_welcome_message()
            self.session_memory.clear()


def main():
    """Función principal de entrada."""
    app = CadGPTApp()
    app.mainloop()


if __name__ == "__main__":
    main()
