# 🖥️ CadGPT - Interfaz Gráfica de Usuario

## Descripción

Interfaz gráfica moderna para CadGPT que permite interactuar con el sistema mediante chat, seleccionar motores CAD y configurar carpetas de salida.

![CadGPT GUI](docs/images/gui_preview.png)

## ✨ Características

- **💬 Chat Interactivo**: Interfaz tipo chat para enviar instrucciones en lenguaje natural
- **🔧 Selección de Motor CAD**: Cambia entre OpenSCAD, Blender y FreeCAD fácilmente
- **📁 Selector de Carpeta**: Elige dónde guardar tus modelos generados
- **📦 Múltiples Formatos**: Exporta a STL, OBJ, STEP, DXF, FBX, GLTF, IFC
- **⚡ Procesamiento en Segundo Plano**: No bloquea la interfaz mientras genera modelos
- **🎨 Tema Oscuro**: Diseño moderno y cómodo para la vista

## 🚀 Instalación

### Requisitos Previos

- Python 3.8 o superior
- Tkinter (generalmente incluido con Python)
- customtkinter

### Instalación de Dependencias

```bash
# Windows
pip install customtkinter packaging

# Linux
pip3 install customtkinter packaging
# Si falta tkinter:
sudo apt-get install python3-tk tk

# macOS
pip3 install customtkinter packaging
# Si falta tkinter:
brew install python-tk
```

## 🎯 Cómo Usar

### Método 1: Doble clic en el lanzador

**Windows:**
1. Ve a la carpeta de CadGPT
2. Haz doble clic en `INICIAR_CADGPT.bat`

**Linux/Mac:**
1. Ve a la carpeta de CadGPT
2. Haz doble clic en `iniciar_cadgpt.sh` (o ejecútalo desde terminal)

### Método 2: Desde línea de comandos

```bash
cd cadgpt
python frontend/gui_app.py
```

### Método 3: Icono de escritorio (Linux)

```bash
# Copiar el archivo .desktop a aplicaciones
cp CadGPT.desktop ~/.local/share/applications/
chmod +x ~/.local/share/applications/CadGPT.desktop
```

## 📖 Uso de la Interfaz

### Panel Lateral (Izquierda)

1. **Motor CAD**: Selecciona el motor a usar (OpenSCAD, Blender, FreeCAD)
2. **Información del Motor**: Descripción de las capacidades del motor seleccionado
3. **Carpeta de Salida**: Ruta donde se guardarán los archivos generados
4. **Formato de Exportación**: Formato del archivo de salida (STL, OBJ, etc.)
5. **Botones de Acción**:
   - ⚡ Generar Modelo: Ejecuta el último comando del chat
   - 🗑️ Limpiar Chat: Borra el historial de conversación
   - 📂 Abrir Carpeta: Abre la carpeta de salida en el explorador

### Área Principal (Derecha)

1. **Historial del Chat**: Muestra la conversación con timestamps
2. **Campo de Entrada**: Escribe tus instrucciones aquí
3. **Botón Enviar**: Envía el mensaje para procesar

### Ejemplos de Comandos

```
"Genera un cubo de 100mm de lado"
"Crea una esfera hueca de 5cm de diámetro con 3mm de espesor"
"Diseña un cilindro de 50mm de altura y 30mm de diámetro"
"Genera un cono truncado de 100mm de base y 60mm de altura"
"Crea un toroide de 80mm de radio mayor y 20mm de radio menor"
```

## 🎨 Colores del Chat

- 🔵 **Azul**: Mensajes del usuario
- 🟢 **Verde**: Respuestas de CadGPT
- 🟠 **Naranja**: Mensajes del sistema
- 🟣 **Violeta**: Código generado
- 🔴 **Rojo**: Errores

## ⚙️ Configuración Avanzada

### Variables de Entorno

```bash
# Para usar LLM local (LM Studio)
export CADGPT_LLM_URL=http://localhost:1234/v1
export CADGPT_LLM_MODEL=local-model

# Para cambiar el tema
export CADGPT_THEME=dark  # o 'light'
```

### Personalización

Puedes modificar el archivo `frontend/gui_app.py` para:
- Cambiar colores y temas
- Agregar nuevos formatos de exportación
- Modificar el comportamiento del parser
- Integrar con otros servicios

## 🐛 Solución de Problemas

### Error: "No module named 'customtkinter'"
```bash
pip install customtkinter
```

### Error: "ImportError: libtk8.6.so"
**Linux:**
```bash
sudo apt-get install python3-tk tk
```

**macOS:**
```bash
brew install python-tk
```

**Windows:**
Reinstala Python asegurándote de marcar "tcl/tk and IDLE" durante la instalación.

### La ventana no aparece
Verifica que tengas un servidor X corriendo (Linux) o que Tkinter esté correctamente instalado.

### Los archivos no se generan
1. Verifica que la carpeta de salida exista
2. Comprueba los permisos de escritura
3. Revisa el historial del chat para mensajes de error

## 📁 Estructura de Archivos

```
cadgpt/
├── frontend/
│   ├── gui_app.py          # Aplicación principal de la GUI
│   └── ...                 # Otros componentes frontend
├── INICIAR_CADGPT.bat      # Lanzador Windows
├── iniciar_cadgpt.sh       # Lanzador Linux/Mac
├── CadGPT.desktop          # Icono de escritorio Linux
└── README_GUI.md           # Este archivo
```

## 🔮 Próximas Características

- [ ] Visualizador 3D integrado
- [ ] Historial de modelos generados
- [ ] Vista previa de código en tiempo real
- [ ] Temas personalizables
- [ ] Soporte para múltiples idiomas
- [ ] Exportación directa a impresora 3D
- [ ] Integración con nube para compartir modelos

## 📄 Licencia

Misma licencia que el proyecto principal CadGPT.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor abre un issue o PR en el repositorio principal.

---

**Desarrollado con ❤️ usando CustomTkinter**
