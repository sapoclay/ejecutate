# 🐍 Editor de Código Python - Ejecútate!

Este es un editor de código Python básico, pero con sus cosas, una arquitectura MVC y una interfaz creada con PySide6. Cuenta con un **sistema de verificación de sintaxis en tiempo real**, **búsqueda y reemplazo avanzado**, **múltiples temas**, **terminal integrado**, **gestión de sesiones**, **formatter automático PEP 8** y **explorador de archivos lateral**.

## **Características principales**

### ✨ **Interfaz sencilla pero funcional**
- **🎨 5 Temas predefinidos** (Oscuro, Claro, Solarized, Monokai, VS Code Dark)
- **📏 Resaltado de sintaxis avanzado** con Pygments (12 tipos de tokens diferentes)
- **🔍 Verificación de sintaxis en tiempo real** con errores, advertencias y sugerencias
- **� Búsqueda y reemplazo avanzado** con regex y búsqueda en múltiples archivos
- **�📁 Explorador de archivos lateral** con gestión completa de proyectos
- **💻 Terminal integrado** con 3 modos (Sistema, Python REPL, Pip)
- **🗂️ Gestión de sesiones** con restauración automática
- **🎯 Formatter automático** con PEP 8, autopep8 y black
- **🤖 Sistema de autocompletado avanzado** con snippets y funciones built-in

### 🎭 **Sistema de temas múltiples**
5 temas con colores optimizados:

#### 🌙 **Tema Oscuro** (Por defecto)
#### ☀️ **Tema Claro**
#### 🌅 **Tema Solarized**
#### 🔥 **Tema Monokai**
#### 💙 **Tema VS Code Dark**

### 🔍 **Verificación de sintaxis en tiempo real**
Sistema avanzado de análisis de código mientras escribes:

#### **Tipos de verificación:**
- **🔴 Errores de sintaxis**: Detección inmediata con `ast.parse()`
- **🟠 Advertencias**: Variables/imports no utilizados
- **🔵 Sugerencias**: Mejores prácticas PEP 8

#### **Características:**
- **Subrayado visual**: Rojo ondulado (errores), naranja ondulado (advertencias), azul punteado (sugerencias)
- **Tooltips informativos**: Hover para ver detalles y sugerencias
- **Verificación no intrusiva**: Procesamiento en background con debounce
- **Análisis inteligente**: AST parsing, rastreo de variables, análisis de imports

### 💻 **Terminal integrado**
Terminal completo con 3 modos especializados:

#### **🖥️ Modo sistema**
- Ejecuta comandos del sistema operativo
- Navegación de directorios y operaciones de archivos
- Gestión de procesos y herramientas del sistema

#### **🐍 Modo Python REPL**
- Intérprete interactivo de Python
- Prueba rápida de código y expresiones
- Importación y testing de módulos

#### **📦 Modo Pip**
- Gestión especializada de paquetes Python
- Comandos pip con autocompletado
- Instalación, actualización y desinstalación de librerías

### 🗂️ **Gestión de sesiones avanzada**
Sistema automático de persistencia y restauración:

#### **Funcionalidades:**
- **Guardado automático**: Estado de la aplicación al cerrar
- **Restauración completa**: Archivos abiertos, posición del cursor, configuraciones
- **Gestión inteligente**: Solo guarda cambios importantes
- **Respaldo seguro**: Archivo JSON con validación de integridad

#### **Qué se guarda:**
- Lista de archivos abiertos con rutas completas
- Posición del cursor en cada archivo
- Configuraciones de ventana (tamaño, posición)
- Tema seleccionado y preferencias personalizadas

### 🎯 **Formatter automático**
Sistema completo de formateo de código Python:

#### **3 Motores de Formateo:**
- **Manual**: Espaciado básico y organización simple
- **autopep8**: Formateo automático según PEP 8
- **black**: Formatter opinionado y consistente

#### **Características:**
- **Cumplimiento PEP 8**: Líneas máximo 79/88 caracteres
- **Organización de imports**: Automática con `isort`
- **Espaciado inteligente**: Operadores, funciones, clases
- **Preferencias configurables**: Longitud de línea, estilo de comillas
- **Vista previa**: Prueba el formatter antes de aplicar

### 📁 **Explorador da archivos lateral**
Gestión completa de proyectos integrada:

#### **Navegación:**
- **Árbol jerárquico** con iconos diferenciados
- **Apertura rápida** con doble clic
- **Toggle completo**: F3 oculta/muestra toda la columna
- **Cambio de directorio raíz** para diferentes proyectos

#### **Gestión de Aachivos:**
- **Crear/eliminar** archivos y carpetas
- **Menú contextual** con todas las opciones
- **Plantillas automáticas** para archivos Python
- **Filtrado inteligente** por extensiones

### 🔍 **Sistema de búsqueda y reemplazo**
Funcionalidad completa de búsqueda con soporte para expresiones regulares:

#### **🔍 Búsqueda simple (Ctrl+F)**
- **Búsqueda en tiempo real** mientras escribes
- **Navegación entre resultados** con F3/Shift+F3
- **Resaltado de coincidencias** en el editor
- **Opciones avanzadas**: Distinguir mayúsculas, palabras completas
- **Búsqueda circular**: Continúa desde el inicio al llegar al final

#### **🔄 Búsqueda y reemplazo (Ctrl+H)**
- **Reemplazo individual** de coincidencias seleccionadas
- **Reemplazo masivo** con confirmación de seguridad
- **Vista previa** de cambios antes de aplicar
- **Soporte para expresiones regulares** con grupos de captura
- **Historial de búsqueda** y reemplazo

#### **🗂️ Búsqueda en múltiples archivos (Ctrl+Shift+F)**
- **Búsqueda recursiva** en directorios completos
- **Filtros de archivo** configurables (*.py, *.txt, etc.)
- **Expresiones regulares** para patrones complejos
- **Resultados en árbol** con navegación directa
- **Exclusión de directorios** (.git, __pycache__, etc.)

#### **⚙️ Opciones avanzadas**
- **Expresiones regulares**: Soporte completo para regex Python
- **Búsqueda sensible**: Mayúsculas/minúsculas configurable
- **Palabras completas**: Evita coincidencias parciales
- **Búsqueda en selección**: Limita el ámbito de búsqueda
- **Navegación rápida**: F3 (siguiente), Shift+F3 (anterior)

## 🏛️ **Arquitectura MVC**
```
📂 Estructura del proyecto
├── 🎯 main.py                    # Punto de entrada principal
├── 🚀 run_app.py                 # Script de ejecución optimizado
├── 📂 views/
│   └── editor_view.py           # Interfaz PySide6 + Temas + Terminal + Sessions
├── 📂 controllers/
│   └── editor_controller.py     # Lógica de coordinación
├── 📂 models/
│   └── code_executor.py         # Ejecución segura de código
├── 📂 utils/
│   ├── __init__.py              # Módulo utils
│   └── code_formatter.py       # Sistema de formateo automático
├── 📂 img/
│   └── logo.png                 # Icono de la aplicación
├── 🔧 config.py                 # Configuraciones centralizadas con todos los sistemas
├── 📋 requirements.txt          # Dependencias completas (PySide6, Pygments, autopep8, black, isort)
└── 📚 README.md                 # Documentación completa
```

## ⌨️ **Atajos de teclado**

### 🎨 **Temas y visualización**
- `F1` - Cambiar tema siguiente
- `F2` - Cambiar tema anterior
- `F3` - Toggle explorador de archivos

### � **Búsqueda y reemplazo**
- `Ctrl+F` - Buscar en archivo actual
- `Ctrl+H` - Buscar y reemplazar
- `Ctrl+Shift+F` - Buscar en múltiples archivos
- `F3` - Buscar siguiente (en diálogo abierto)
- `Shift+F3` - Buscar anterior (en diálogo abierto)

### �💻 **Terminal**
- `F4` - Toggle terminal integrado
- `Ctrl+Shift+S` - Modo Sistema
- `Ctrl+Shift+P` - Modo Python REPL
- `Ctrl+Shift+I` - Modo Pip

### 🎯 **Formatter**
- `Ctrl+Alt+F` - Formatear código y preferencias

### 🔧 **Edición**
- `Ctrl+Enter` - Ejecutar código
- `Ctrl+L` - Limpiar todo
- `Tab` - Indentar
- `Shift+Tab` - Des-indentar

### 📁 **Archivos y sesiones**
- `Ctrl+O` - Abrir archivo
- `Ctrl+S` - Guardar
- `Ctrl+Shift+S` - Guardar como
- `Ctrl+Shift+N` - Guardar sesión manual
- `Ctrl+Shift+R` - Restaurar sesión

### ⚙️ **Configuración**
- `Ctrl+,` - Abrir preferencias
- `F12` - Ventana About

## 🛠️ **Instalación y uso**

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

### **Instalación manual**
```bash
# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python3 main.py
```

### **Dependencias requeridas**
```text
PySide6>=6.7.0      # Interfaz gráfica moderna
Pygments>=2.18.0    # Resaltado de sintaxis
autopep8>=2.0.4     # Formatter PEP 8
black>=24.0.0       # Formatter opinionado
isort>=5.13.0       # Organización de imports
```

## 📝 **Funcionalidades destacadas**

### **🔍 35+ Funcionalidades verificadas**
Por el momento este editor incluye un sistema completo con todas estas características:

#### **✅ Edición avanzada:**
- Resaltado de sintaxis Python básico, pero funcional
- Numeración de líneas
- Indentación automática (que funciona un poco cuando quiere!!)
- Autocompletado con snippets
- Verificación de sintaxis en tiempo real
- Búsqueda y reemplazo con expresiones regulares
- Búsqueda en múltiples archivos

#### **✅ Gestión de archivos:**
- Abrir, guardar, crear, eliminar archivos
- Explorador lateral con navegación
- Gestión de proyectos y directorios
- Filtros inteligentes de archivos

#### **✅ Personalización:**
- 5 temas profesionales predefinidos
- Configuración de fuentes y colores
- Preferencias persistentes
- Interface adaptable

#### **✅ Herramientas de desarrollo:**
- Terminal integrado con 3 modos
- Formatter automático con 3 motores
- Ejecutor de código seguro
- Gestión de sesiones

#### **✅ Interface:**
- Arquitectura MVC robusta
- Componentes modulares reutilizables
- Manejo de errores bastante completo
- Una experiencia de usuario sencilla

## 🎯 **Ejemplos de uso**

### **🚀 Desarrollo básico**
1. **Abrir el editor**: `python3 run_app.py`
2. **Crear archivo**: Explorador → Clic derecho → Nuevo archivo
3. **Escribir código**: Verificación automática de sintaxis
4. **Buscar texto**: `Ctrl+F` para búsqueda rápida, `Ctrl+H` para reemplazar
5. **Formatear**: `Ctrl+Alt+F` para PEP 8 automático
6. **Ejecutar**: `Ctrl+Enter` para ver resultados

### **⚙️ Personalización avanzada**
1. **Cambiar tema**: `F1` para navegar entre los 5 temas
2. **Configurar formatter**: `Ctrl+Alt+F` → Elegir autopep8 o black
3. **Ajustar terminal**: `F4` → Cambiar entre modos con `Ctrl+Shift+S/P/I`
4. **Gestionar sesión**: Se guarda automáticamente al cerrar

## 🔧 **Configuración avanzada**

### **Archivos de configuración**
- **Preferencias**: `~/.config/PythonEditor/Preferences.conf`
- **Sesiones**: `.editor_session.json` (directorio del proyecto)
- **Temas**: Integrados en `config.py`

### **Personalización de formatter**
```python
# Configuraciones disponibles en Preferencias
FORMATTER_ENGINE = "autopep8"  # "manual", "autopep8", "black"
MAX_LINE_LENGTH = 79           # 79 (PEP 8) o 88 (black)
QUOTE_STYLE = "single"         # "single" o "double"
ORGANIZE_IMPORTS = True        # Usar isort automáticamente
```

## 🔍 **Solución de problemas**

### **Error: "python comando no encontrado"**
```bash
# Usar python3 en lugar de python
python3 run_app.py
```

### **Error: "ModuleNotFoundError"**
```bash
# Instalar dependencias específicas
pip install PySide6 Pygments autopep8 black isort
```

### **Terminal no responde**
- Cambiar modo del terminal: `Ctrl+Shift+S` (Sistema)
- Reiniciar terminal: Cerrar y abrir con `F4`

### **Formatter no funciona**
- Verificar instalación: `pip list | grep autopep8`
- Cambiar motor en Preferencias → Formatter
- Usar modo manual como fallback

### **Sesión no se restaura**
- Verificar permisos en directorio del proyecto
- Revisar archivo `.editor_session.json`
- Restaurar manualmente: `Ctrl+Shift+R`

## 🚀 **Arquitectura y extensibilidad**

### **Patrones de diseño implementados**
- **MVC (Model-View-Controller)**: Separación clara de responsabilidades
- **Observer**: Sistema de eventos para comunicación entre componentes
- **Strategy**: Múltiples motores de formateo intercambiables
- **Factory**: Creación de componentes de interface según configuración

### **Puntos de extensión**
1. **Nuevos temas**: Agregar en `config.py` → `THEMES`
2. **Motores de formatter**: Extender `utils/code_formatter.py`
3. **Modos de terminal**: Agregar en `IntegratedTerminal`
4. **Verificadores**: Extender sistema de sintaxis en tiempo real

## 🤝 **Contribuir al Proyecto**

### **Estructura para nuevas características**
1. **Modelo** (`models/`) - Lógica
2. **Vista** (`views/`) - Interfaz y componentes UI  
3. **Controlador** (`controllers/`) - Coordinación y eventos
4. **Utilidades** (`utils/`) - Herramientas auxiliares
5. **Configuración** (`config.py`) - Parámetros centralizados

### **Líneas de Desarrollo**
- Seguir arquitectura MVC existente
- Usar type hints en Python
- Documentar funciones públicas
- Mantener compatibilidad con temas
- Agregar tests para nuevas funcionalidades

---

🐍 **¡Editor de Python Ejecútate! - Básico pero coqueto** 🐍

*Desarrollado con pocas horas de sueño para la comunidad Python por entreunosyceros* ❤️
