# 🐍 Editor de Código Python - Ejecútate!

<img width="1024" height="1024" alt="logo" src="https://github.com/user-attachments/assets/53caa94d-580f-45ce-af56-6e312500e30d" />

Este es un editor de código Python básico, pero con sus cosas, una arquitectura MVC y una interfaz creada con PySide6. Cuenta con **verificación de sintaxis en tiempo real**, **búsqueda y reemplazo avanzado**, **múltiples temas**, **terminal integrado**, **gestión de sesiones**, **formatter automático PEP 8**, **explorador de archivos** y **sistema educativo completo**.

## **Características principales**

### ✨ **Interfaz y Edición**
- **🎨 5 Temas predefinidos** (Oscuro, Claro, Solarized, Monokai, VS Code Dark)
- **📏 Resaltado de sintaxis avanzado** con Pygments
- **🔍 Verificación de sintaxis en tiempo real** con errores y sugerencias
- **🔍 Búsqueda y reemplazo avanzado** con regex y múltiples archivos
- **📁 Explorador de archivos lateral** con gestión de proyectos
- **🤖 Sistema de autocompletado** con snippets y funciones built-in

### 💻 **Herramientas de Desarrollo**
- **💻 Terminal integrado** con 3 modos (Sistema, Python REPL, Pip)
- **🎯 Formatter automático** con PEP 8, autopep8 y black
- **🗂️ Gestión de sesiones** con restauración automática
- **🔧 Ejecutor de código** seguro e integrado

### 🎓 **Sistema Educativo Completo** *(Nuevo)*
- **📚 Tutoriales interactivos** paso a paso para aprender Python
- **🐛 Debugger visual** con ejecución línea por línea
- **📦 Gestor de paquetes** visual para instalar/desinstalar librerías
- **🔍 Analizador de código** con recomendaciones en tiempo real
- **💡 Autocompletado inteligente** con explicaciones contextuales

## ⌨️ **Atajos de teclado principales**

### 🎓 **Funciones Educativas**
- `F4` - Tutoriales interactivos
- `F5` - Debugger visual
- `F6` - Gestor de paquetes
- `F7` - Análisis de código en tiempo real

### � **Temas y navegación**
- `F1/F2` - Cambiar tema (5 disponibles)
- `F3` - Toggle explorador de archivos

### 🔍 **Búsqueda y edición**
- `Ctrl+F` - Buscar en archivo
- `Ctrl+H` - Buscar y reemplazar
- `Ctrl+Shift+F` - Buscar en múltiples archivos
- `Ctrl+Enter` - Ejecutar código
- `Ctrl+Alt+F` - Formatear código

## 🏛️ **Arquitectura MVC**
```
📂 Estructura del proyecto
├── 🎯 main.py                    # Punto de entrada principal
├── 🚀 run_app.py                 # Script de ejecución optimizado
├── 📂 views/
│   └── editor_view.py           # Interfaz PySide6 + Sistema educativo integrado
├── 📂 controllers/
│   └── editor_controller.py     # Lógica de coordinación
├── 📂 models/
│   └── code_executor.py         # Ejecución segura de código
├── 📂 analyzers/                 # Sistema educativo modular
│   ├── code_analyzer.py         # Análisis de código en tiempo real
│   ├── smart_completer.py       # Autocompletado inteligente
│   ├── tutorial_system.py       # Gestión de tutoriales
│   ├── visual_debugger.py       # Debugger paso a paso
│   └── package_manager.py       # Gestor visual de paquetes
├── 📂 utils/
│   ├── code_formatter.py        # Formateo automático
│   └── new_terminal.py          # Terminal integrado mejorado
├── � tutorials_config.py        # Configuración modular de tutoriales
├── 📋 requirements.txt          # Dependencias completas
└── 📚 README.md                 # Documentación
```

## ️ **Instalación y uso**

### **Instalación rápida**
```bash
# Clonar repositorio
git clone https://github.com/sapoclay/ejecutate.git
cd ejecutate

# Instalar dependencias automáticamente  
python3 run_app.py --install-deps

# Ejecutar aplicación
python3 run_app.py
```

### **Dependencias principales**
- **PySide6** - Interfaz gráfica moderna
- **Pygments** - Resaltado de sintaxis  
- **autopep8/black** - Formateo automático
- **isort** - Organización de imports

## 🎓 **Sistema Educativo - Detalles**

### **� Tutoriales Interactivos (F4)**
- **Sistema modular** con configuración externa en `tutorials_config.py`
- **3 tutoriales incluidos**: Desde principiante hasta intermedio
- **Pasos progresivos** con ejemplos de código y validación
- **Fácil extensión**: Añadir nuevos tutoriales editando un solo archivo

### **� Debugger Visual (F5)**
- **Ejecución paso a paso** línea por línea
- **Visualización de variables** en tiempo real
- **Breakpoints interactivos** con control total
- **Análisis de flujo** para entender la lógica del programa

### **📦 Gestor de Paquetes (F6)**
- **Instalación visual** de librerías Python populares
- **Búsqueda en PyPI** con información detallada
- **Gestión completa**: Instalar, actualizar, desinstalar
- **Ejemplos de uso** para cada paquete

### **🔍 Analizador de Código (F7)**
- **Análisis en tiempo real** mientras escribes
- **Detección de errores** antes de ejecutar
- **Sugerencias PEP 8** para mejor estilo
- **Recomendaciones inteligentes** para optimización

## 🚀 **Inicio rápido**

1. **Instalar**: `python3 run_app.py --install-deps`
2. **Ejecutar**: `python3 run_app.py` 
3. **Crear archivo**: Explorador → Nuevo archivo Python
4. **Aprender**: Presiona `F4` para tutoriales interactivos
5. **Desarrollar**: Usa `F5-F7` para herramientas educativas avanzadas

---

🐍 **¡Editor de Python Ejecútate! - Básico pero coqueto con sistema educativo completo** 🐍

*Desarrollado con pocas horas de sueño para la comunidad Python por entreunosyceros* ❤️

### 📖 Documentación adicional:
- **Añadir tutoriales**: Ver `COMO_AÑADIR_TUTORIALES.md`
- **Configuración modular**: `tutorials_config.py`
- **Funciones educativas**: Presiona `F4-F7` para explorar
