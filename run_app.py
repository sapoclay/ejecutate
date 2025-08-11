#!/usr/bin/env python3
"""
Script para ejecutar el Editor de Código Python Ejecútate!
Maneja automáticamente el entorno virtual y dependencias
"""

import os
import sys
import subprocess
from pathlib import Path

def get_venv_python():
    """Obtiene la ruta del ejecutable Python del entorno virtual"""
    script_dir = Path(__file__).parent
    venv_python = script_dir / ".venv" / "bin" / "python"
    
    if venv_python.exists():
        return str(venv_python)
    return None

def create_venv_if_needed():
    """Crea el entorno virtual si no existe"""
    script_dir = Path(__file__).parent
    venv_dir = script_dir / ".venv"
    
    if not venv_dir.exists():
        print("🔧 Creando entorno virtual...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        return True
    return False

def install_dependencies():
    """Instala las dependencias en el entorno virtual"""
    venv_python = get_venv_python()
    if not venv_python:
        return False
    
    print("📦 Instalando dependencias PySide6 y Pygments...")
    try:
        subprocess.run([venv_python, "-m", "pip", "install", "PySide6", "Pygments"], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al instalar dependencias: {e}")
        return False

def run_app_with_venv():
    """Ejecuta la aplicación usando el entorno virtual de manera directa"""
    venv_python = get_venv_python()
    
    if not venv_python:
        print("❌ No se pudo encontrar el entorno virtual")
        return False
    
    # Activar el entorno virtual añadiendo sus rutas al path
    script_dir = Path(__file__).parent
    venv_site_packages = script_dir / ".venv" / "lib" / "python3.12" / "site-packages"
    
    if venv_site_packages.exists():
        sys.path.insert(0, str(venv_site_packages))
    
    # Agregar el directorio actual al path
    sys.path.insert(0, str(script_dir))
    
    print("🚀 Iniciando Editor de código Python Ejecútate! (modo directo)...")
    
    try:
        # Importar y ejecutar directamente
        from controllers.editor_controller import CodeEditorController
        app = CodeEditorController()
        return app.run()
    except Exception as e:
        print(f"❌ Error al ejecutar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    try:
        # Cambiar al directorio del script
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        
        # Crear entorno virtual si es necesario
        venv_created = create_venv_if_needed()
        
        # Instalar dependencias si el entorno virtual es nuevo o si se solicita
        if venv_created or "--install-deps" in sys.argv:
            if not install_dependencies():
                print("\n❌ No se pudieron instalar las dependencias.")
                print("💡 Sugerencias:")
                print("- Instalar manualmente: pip install PySide6 Pygments")
                print("- Verificar conexión a internet")
                sys.exit(1)
        
        # Ejecutar la aplicación
        if not run_app_with_venv():
            print("\n❌ No se pudo ejecutar la aplicación PySide6.")
            print("💡 Sugerencias:")
            print("- Verificar dependencias: python main.py --check-deps")
            print("- Reinstalar dependencias: python run_app.py --install-deps")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n¡Aplicación cerrada por el usuario!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Sugerencias:")
        print("- Verificar dependencias: python main.py --check-deps")
        print("- Reinstalar entorno: rm -rf .venv && python run_app.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
