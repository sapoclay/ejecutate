#!/usr/bin/env python3
"""
Gestor visual de paquetes Python para principiantes
Facilita la instalación y gestión de paquetes con pip
"""

import subprocess
import sys
import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
try:
    from importlib.metadata import distributions
    METADATA_AVAILABLE = True
except ImportError:
    try:
        from importlib_metadata import distributions
        METADATA_AVAILABLE = True
    except ImportError:
        METADATA_AVAILABLE = False
        distributions = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None
import threading
import time

@dataclass
class PackageInfo:
    """Información de un paquete Python"""
    name: str
    version: str = ""
    description: str = ""
    author: str = ""
    home_page: str = ""
    installed: bool = False
    latest_version: str = ""
    size: str = ""
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

class PackageManager:
    """Gestor de paquetes Python con interfaz amigable"""
    
    def __init__(self):
        self.popular_packages = self._get_popular_packages()
        self.installed_packages = {}
        self._update_installed_packages()
    
    def _get_popular_packages(self) -> Dict[str, PackageInfo]:
        """Retorna una lista de paquetes populares para principiantes"""
        return {
            'requests': PackageInfo(
                'requests',
                description='Librería para hacer peticiones HTTP de forma sencilla',
                home_page='https://requests.readthedocs.io/',
                author='Kenneth Reitz'
            ),
            'matplotlib': PackageInfo(
                'matplotlib',
                description='Librería para crear gráficos y visualizaciones',
                home_page='https://matplotlib.org/',
                author='John D. Hunter'
            ),
            'pandas': PackageInfo(
                'pandas',
                description='Análisis y manipulación de datos con estructuras potentes',
                home_page='https://pandas.pydata.org/',
                author='Wes McKinney'
            ),
            'numpy': PackageInfo(
                'numpy',
                description='Operaciones numéricas y arrays multidimensionales',
                home_page='https://numpy.org/',
                author='Travis Oliphant'
            ),
            'pillow': PackageInfo(
                'pillow',
                description='Manipulación de imágenes (PNG, JPEG, etc.)',
                home_page='https://pillow.readthedocs.io/',
                author='Alex Clark'
            ),
            'beautifulsoup4': PackageInfo(
                'beautifulsoup4',
                description='Análisis de documentos HTML y XML',
                home_page='https://www.crummy.com/software/BeautifulSoup/',
                author='Leonard Richardson'
            ),
            'flask': PackageInfo(
                'flask',
                description='Framework web minimalista y flexible',
                home_page='https://flask.palletsprojects.com/',
                author='Armin Ronacher'
            ),
            'django': PackageInfo(
                'django',
                description='Framework web completo y robusto',
                home_page='https://www.djangoproject.com/',
                author='Django Software Foundation'
            ),
            'pygame': PackageInfo(
                'pygame',
                description='Desarrollo de juegos 2D',
                home_page='https://www.pygame.org/',
                author='Pete Shinners'
            ),
            'tkinter': PackageInfo(
                'tkinter',
                description='Interfaz gráfica incluida con Python',
                installed=True,  # Viene con Python
                version='Built-in'
            ),
            'sqlite3': PackageInfo(
                'sqlite3',
                description='Base de datos ligera incluida con Python',
                installed=True,  # Viene con Python
                version='Built-in'
            ),
            'json': PackageInfo(
                'json',
                description='Trabajo con datos JSON incluido con Python',
                installed=True,  # Viene con Python
                version='Built-in'
            ),
            'random': PackageInfo(
                'random',
                description='Generación de números aleatorios incluido con Python',
                installed=True,  # Viene con Python
                version='Built-in'
            ),
            'datetime': PackageInfo(
                'datetime',
                description='Manejo de fechas y horas incluido con Python',
                installed=True,  # Viene con Python
                version='Built-in'
            ),
            'os': PackageInfo(
                'os',
                description='Interacción con el sistema operativo incluido con Python',
                installed=True,  # Viene con Python
                version='Built-in'
            )
        }
    
    def _update_installed_packages(self):
        """Actualiza la lista de paquetes instalados"""
        self.installed_packages = {}
        
        try:
            if METADATA_AVAILABLE and distributions:
                # Usar importlib.metadata para obtener paquetes instalados
                for dist in distributions():
                    package_name = dist.metadata['Name'].lower()
                    self.installed_packages[package_name] = PackageInfo(
                        name=package_name,
                        version=dist.version,
                        installed=True
                    )
                    
                    # Actualizar paquetes populares si están instalados
                    if package_name in self.popular_packages:
                        self.popular_packages[package_name].installed = True
                        self.popular_packages[package_name].version = dist.version
            else:
                # Método alternativo usando pip list
                try:
                    result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'], 
                                          capture_output=True, text=True, check=True)
                    installed_packages = json.loads(result.stdout)
                    
                    for package in installed_packages:
                        package_name = package['name'].lower()
                        self.installed_packages[package_name] = PackageInfo(
                            name=package_name,
                            version=package['version'],
                            installed=True
                        )
                        
                        # Actualizar paquetes populares si están instalados
                        if package_name in self.popular_packages:
                            self.popular_packages[package_name].installed = True
                            self.popular_packages[package_name].version = package['version']
                except subprocess.CalledProcessError:
                    print("No se pudo obtener la lista de paquetes instalados")
                    
        except Exception as e:
            print(f"Error al obtener paquetes instalados: {e}")
    
    def search_package(self, package_name: str) -> Optional[PackageInfo]:
        """Busca información de un paquete en PyPI"""
        try:
            if not REQUESTS_AVAILABLE or not requests:
                # Crear una respuesta básica sin usar requests
                is_installed = package_name.lower() in self.installed_packages
                current_version = ""
                if is_installed:
                    current_version = self.installed_packages[package_name.lower()].version
                
                return PackageInfo(
                    name=package_name,
                    version=current_version,
                    description=f"Paquete {package_name}",
                    installed=is_installed
                )
            
            # Buscar en PyPI usando requests
            response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=5)
            if response.status_code == 200:
                data = response.json()
                info = data.get('info', {})
                
                # Verificar si está instalado
                is_installed = package_name.lower() in self.installed_packages
                current_version = ""
                if is_installed:
                    current_version = self.installed_packages[package_name.lower()].version
                
                return PackageInfo(
                    name=info.get('name', package_name),
                    version=current_version,
                    description=info.get('summary', 'No hay descripción disponible'),
                    author=info.get('author', 'Desconocido'),
                    home_page=info.get('home_page', ''),
                    installed=is_installed,
                    latest_version=info.get('version', '')
                )
        except Exception as e:
            print(f"Error al buscar paquete {package_name}: {e}")
        
        return None
    
    def install_package(self, package_name: str, callback=None) -> Dict:
        """Instala un paquete usando pip"""
        try:
            if callback:
                callback(f"Instalando {package_name}...")
            
            # Comando pip install
            cmd = [sys.executable, '-m', 'pip', 'install', package_name]
            
            # Ejecutar comando
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )
            
            if result.returncode == 0:
                # Actualizar lista de paquetes instalados
                self._update_installed_packages()
                
                if callback:
                    callback(f"✅ {package_name} instalado correctamente")
                
                return {
                    'success': True,
                    'message': f'Paquete {package_name} instalado correctamente',
                    'output': result.stdout
                }
            else:
                error_msg = result.stderr or result.stdout or 'Error desconocido'
                if callback:
                    callback(f"❌ Error instalando {package_name}: {error_msg}")
                
                return {
                    'success': False,
                    'message': f'Error al instalar {package_name}',
                    'error': error_msg
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': 'La instalación tardó demasiado tiempo',
                'error': 'Timeout'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}',
                'error': str(e)
            }
    
    def uninstall_package(self, package_name: str, callback=None) -> Dict:
        """Desinstala un paquete usando pip"""
        try:
            if callback:
                callback(f"Desinstalando {package_name}...")
            
            # Comando pip uninstall
            cmd = [sys.executable, '-m', 'pip', 'uninstall', package_name, '-y']
            
            # Ejecutar comando
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Actualizar lista de paquetes instalados
                self._update_installed_packages()
                
                if callback:
                    callback(f"✅ {package_name} desinstalado correctamente")
                
                return {
                    'success': True,
                    'message': f'Paquete {package_name} desinstalado correctamente',
                    'output': result.stdout
                }
            else:
                error_msg = result.stderr or result.stdout or 'Error desconocido'
                if callback:
                    callback(f"❌ Error desinstalando {package_name}: {error_msg}")
                
                return {
                    'success': False,
                    'message': f'Error al desinstalar {package_name}',
                    'error': error_msg
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}',
                'error': str(e)
            }
    
    def upgrade_package(self, package_name: str, callback=None) -> Dict:
        """Actualiza un paquete a la última versión"""
        try:
            if callback:
                callback(f"Actualizando {package_name}...")
            
            # Comando pip install --upgrade
            cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade', package_name]
            
            # Ejecutar comando
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                # Actualizar lista de paquetes instalados
                self._update_installed_packages()
                
                if callback:
                    callback(f"✅ {package_name} actualizado correctamente")
                
                return {
                    'success': True,
                    'message': f'Paquete {package_name} actualizado correctamente',
                    'output': result.stdout
                }
            else:
                error_msg = result.stderr or result.stdout or 'Error desconocido'
                if callback:
                    callback(f"❌ Error actualizando {package_name}: {error_msg}")
                
                return {
                    'success': False,
                    'message': f'Error al actualizar {package_name}',
                    'error': error_msg
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error inesperado: {str(e)}',
                'error': str(e)
            }
    
    def get_popular_packages_list(self) -> List[Dict]:
        """Retorna lista de paquetes populares con su estado"""
        packages = []
        for name, package in self.popular_packages.items():
            packages.append({
                'name': package.name,
                'description': package.description,
                'version': package.version,
                'installed': package.installed,
                'author': package.author,
                'home_page': package.home_page,
                'category': self._get_package_category(name)
            })
        
        return sorted(packages, key=lambda x: (not x['installed'], x['name']))
    
    def get_installed_packages_list(self) -> List[Dict]:
        """Retorna lista de todos los paquetes instalados"""
        packages = []
        for name, package in self.installed_packages.items():
            packages.append({
                'name': package.name,
                'version': package.version,
                'description': package.description,
                'installed': True
            })
        
        return sorted(packages, key=lambda x: x['name'])
    
    def _get_package_category(self, package_name: str) -> str:
        """Retorna la categoría de un paquete"""
        categories = {
            'requests': '🌐 Web',
            'matplotlib': '📊 Visualización',
            'pandas': '📊 Datos',
            'numpy': '🔢 Matemáticas',
            'pillow': '🖼️ Imágenes',
            'beautifulsoup4': '🌐 Web',
            'flask': '🌐 Web Framework',
            'django': '🌐 Web Framework',
            'pygame': '🎮 Juegos',
            'tkinter': '🖥️ GUI (Incluido)',
            'sqlite3': '💾 Base de datos (Incluido)',
            'json': '📄 Datos (Incluido)',
            'random': '🎲 Utilidades (Incluido)',
            'datetime': '📅 Fechas (Incluido)',
            'os': '💻 Sistema (Incluido)'
        }
        return categories.get(package_name, '📦 General')
    
    def get_package_usage_examples(self, package_name: str) -> List[str]:
        """Retorna ejemplos de uso para paquetes populares"""
        examples = {
            'requests': [
                '# Hacer una petición GET\nimport requests\nresponse = requests.get("https://api.github.com")\nprint(response.json())',
                '# Descargar una imagen\nimport requests\nresponse = requests.get("https://ejemplo.com/imagen.jpg")\nwith open("imagen.jpg", "wb") as f:\n    f.write(response.content)'
            ],
            'matplotlib': [
                '# Gráfico simple\nimport matplotlib.pyplot as plt\nx = [1, 2, 3, 4]\ny = [1, 4, 2, 3]\nplt.plot(x, y)\nplt.show()',
                '# Gráfico de barras\nimport matplotlib.pyplot as plt\nnombres = ["Ana", "Luis", "María"]\nvalores = [23, 45, 56]\nplt.bar(nombres, valores)\nplt.show()'
            ],
            'pandas': [
                '# Crear DataFrame\nimport pandas as pd\ndata = {"nombre": ["Ana", "Luis"], "edad": [25, 30]}\ndf = pd.DataFrame(data)\nprint(df)',
                '# Leer archivo CSV\nimport pandas as pd\ndf = pd.read_csv("datos.csv")\nprint(df.head())'
            ],
            'pillow': [
                '# Abrir y redimensionar imagen\nfrom PIL import Image\nimg = Image.open("foto.jpg")\nimg_pequeña = img.resize((100, 100))\nimg_pequeña.save("foto_pequeña.jpg")'
            ],
            'flask': [
                '# Aplicación web básica\nfrom flask import Flask\napp = Flask(__name__)\n\n@app.route("/")\ndef hola():\n    return "¡Hola mundo!"\n\nif __name__ == "__main__":\n    app.run(debug=True)'
            ]
        }
        return examples.get(package_name, ['# No hay ejemplos disponibles para este paquete'])

class PackageManagerUI:
    """Interfaz para el gestor de paquetes"""
    
    def __init__(self):
        self.package_manager = PackageManager()
        self.current_operation = None
    
    def get_popular_packages(self) -> List[Dict]:
        """Obtiene paquetes populares para mostrar en la UI"""
        return self.package_manager.get_popular_packages_list()
    
    def get_installed_packages(self) -> List[Dict]:
        """Obtiene paquetes instalados para mostrar en la UI"""
        return self.package_manager.get_installed_packages_list()
    
    def install_package_async(self, package_name: str, progress_callback=None) -> Dict:
        """Instala un paquete de forma asíncrona"""
        def install_thread():
            return self.package_manager.install_package(package_name, progress_callback)
        
        # En una implementación real, esto se ejecutaría en un hilo separado
        return self.package_manager.install_package(package_name, progress_callback)
    
    def search_package_info(self, package_name: str) -> Optional[Dict]:
        """Busca información de un paquete"""
        package_info = self.package_manager.search_package(package_name)
        if package_info:
            return {
                'name': package_info.name,
                'version': package_info.version,
                'description': package_info.description,
                'author': package_info.author,
                'home_page': package_info.home_page,
                'installed': package_info.installed,
                'latest_version': package_info.latest_version,
                'examples': self.package_manager.get_package_usage_examples(package_info.name)
            }
        return None

# Función helper para la UI
def get_package_manager() -> PackageManagerUI:
    """Retorna una instancia del gestor de paquetes para la UI"""
    return PackageManagerUI()
