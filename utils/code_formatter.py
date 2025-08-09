"""
Módulo de formateo automático de código Python
Incluye formateo PEP 8, organización de imports y ajuste de espaciado
"""

import re
import ast
import subprocess
import sys
from typing import Optional, Dict, List, Tuple
from config import AppConfig

class CodeFormatter:
    """
    Clase para formatear código Python automáticamente
    """
    
    def __init__(self):
        self.config = AppConfig()
        
    def format_code(self, code: str, engine: str = None) -> str:
        """
        Formatea el código usando el motor especificado
        
        Args:
            code: Código Python a formatear
            engine: Motor de formateo ('autopep8', 'black', 'manual')
            
        Returns:
            Código formateado
        """
        if not self.config.FORMATTER_ENABLED:
            return code
            
        if not code.strip():
            return code
            
        engine = engine or self.config.FORMATTER_ENGINE
        
        try:
            # Suprimir warnings durante el formateo
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                if engine == "autopep8":
                    return self._format_with_autopep8(code)
                elif engine == "black":
                    return self._format_with_black(code)
                else:
                    return self._format_manual(code)
        except Exception as e:
            print(f"Error al formatear código: {e}")
            return code
    
    def _format_with_autopep8(self, code: str) -> str:
        """Formatear con autopep8"""
        try:
            import autopep8
            import warnings
            
            # Suprimir warnings durante el formateo
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=SyntaxWarning)
                
                options = {
                    'max_line_length': self.config.FORMATTER_MAX_LINE_LENGTH,
                    'indent_size': self.config.FORMATTER_INDENT_SIZE,
                    'aggressive': 1,  # Nivel de agresividad más conservador
                }
                
                formatted = autopep8.fix_code(code, options=options)
                
                if self.config.FORMATTER_ORGANIZE_IMPORTS:
                    formatted = self._organize_imports(formatted)
                    
                return formatted
            
        except ImportError:
            print("autopep8 no está instalado. Usando formateo manual.")
            return self._format_manual(code)
    
    def _format_with_black(self, code: str) -> str:
        """Formatear con black"""
        try:
            import black
            import warnings
            
            # Suprimir warnings de black que pueden ser molestos
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=SyntaxWarning)
                
                mode = black.FileMode(
                    line_length=self.config.FORMATTER_MAX_LINE_LENGTH,
                    target_versions={black.TargetVersion.PY38}
                )
                
                formatted = black.format_str(code, mode=mode)
                
                if self.config.FORMATTER_ORGANIZE_IMPORTS:
                    formatted = self._organize_imports(formatted)
                    
                return formatted
            
        except ImportError:
            print("black no está instalado. Usando formateo manual.")
            return self._format_manual(code)
        except black.InvalidInput as e:
            print(f"Código inválido para black: {e}")
            return self._format_manual(code)
        except Exception as e:
            print(f"Error con black: {e}")
            return self._format_manual(code)
    
    def _format_manual(self, code: str) -> str:
        """Formateo manual básico"""
        lines = code.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Eliminar espacios en blanco al final
            if self.config.FORMATTER_REMOVE_TRAILING_WHITESPACE:
                line = line.rstrip()
            
            # Ajustar indentación
            if self.config.FORMATTER_AUTO_SPACING:
                line = self._fix_indentation(line)
                line = self._fix_spacing(line)
            
            formatted_lines.append(line)
        
        formatted_code = '\n'.join(formatted_lines)
        
        # Organizar imports si está habilitado
        if self.config.FORMATTER_ORGANIZE_IMPORTS:
            formatted_code = self._organize_imports(formatted_code)
        
        # Añadir nueva línea final
        if self.config.FORMATTER_ADD_FINAL_NEWLINE and not formatted_code.endswith('\n'):
            formatted_code += '\n'
        
        return formatted_code
    
    def _fix_indentation(self, line: str) -> str:
        """Corrige la indentación de una línea"""
        if not line.strip():
            return ""
        
        # Contar espacios al inicio
        leading_spaces = len(line) - len(line.lstrip())
        content = line.lstrip()
        
        if self.config.FORMATTER_USE_TABS:
            # Convertir a tabs
            indent_level = leading_spaces // self.config.FORMATTER_INDENT_SIZE
            return '\t' * indent_level + content
        else:
            # Normalizar espacios
            indent_level = leading_spaces // self.config.FORMATTER_INDENT_SIZE
            return ' ' * (indent_level * self.config.FORMATTER_INDENT_SIZE) + content
    
    def _fix_spacing(self, line: str) -> str:
        """Corrige el espaciado en una línea según PEP 8"""
        if not line.strip():
            return line
        
        # Evitar procesar líneas que son comentarios o strings
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            return line
        
        # Guardar posición de strings para no modificarlos
        string_positions = []
        in_string = False
        string_char = None
        
        for i, char in enumerate(line):
            if char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                if not in_string:
                    in_string = True
                    string_char = char
                    string_start = i
                elif char == string_char:
                    in_string = False
                    string_positions.append((string_start, i))
        
        def is_in_string(pos):
            return any(start <= pos <= end for start, end in string_positions)
        
        # Aplicar espaciado solo fuera de strings
        result = ""
        i = 0
        while i < len(line):
            char = line[i]
            
            if is_in_string(i):
                result += char
                i += 1
                continue
            
            # Espacios alrededor de operadores (evitando decimales)
            if char in '+-*/%=<>!&|^':
                # Verificar si es parte de un número decimal
                if char in '+-' and i > 0 and line[i-1].isdigit() and i+1 < len(line) and line[i+1].isdigit():
                    # Probablemente un signo en notación científica (e+, e-)
                    if i > 1 and line[i-2].lower() == 'e':
                        result += char
                        i += 1
                        continue
                
                # Verificar si no hay espacios adecuados
                need_space_before = i > 0 and line[i-1] not in ' \t'
                need_space_after = i+1 < len(line) and line[i+1] not in ' \t'
                
                if need_space_before and result and result[-1] != ' ':
                    result += ' '
                result += char
                if need_space_after:
                    result += ' '
                i += 1
            
            # Espacios después de comas
            elif char == ',':
                result += char
                if i+1 < len(line) and line[i+1] not in ' \t\n':
                    result += ' '
                i += 1
            
            # Espacios después de dos puntos (solo en contextos apropiados)
            elif char == ':':
                result += char
                # Solo añadir espacio si no es slicing (no hay números antes y después)
                if (i+1 < len(line) and line[i+1] not in ' \t\n' and 
                    not (i > 0 and line[i-1].isdigit() and i+1 < len(line) and line[i+1].isdigit())):
                    result += ' '
                i += 1
            
            else:
                result += char
                i += 1
        
        # Limpiar espacios múltiples (preservando indentación)
        leading_spaces = len(line) - len(line.lstrip())
        content = result[leading_spaces:].strip()
        content = re.sub(r' +', ' ', content)
        
        return line[:leading_spaces] + content
    
    def _organize_imports(self, code: str) -> str:
        """Organiza las declaraciones import según PEP 8"""
        try:
            import isort
            
            config = isort.Config(
                profile="black",
                line_length=self.config.FORMATTER_MAX_LINE_LENGTH,
                multi_line_output=3,
                include_trailing_comma=True,
                force_grid_wrap=0,
                use_parentheses=True,
                ensure_newline_before_comments=True,
                split_on_trailing_comma=True,
            )
            
            return isort.code(code, config=config)
            
        except ImportError:
            print("isort no está instalado. Organizando imports manualmente.")
            return self._organize_imports_manual(code)
        except Exception as e:
            print(f"Error con isort: {e}")
            return self._organize_imports_manual(code)
    
    def _organize_imports_manual(self, code: str) -> str:
        """Organización manual básica de imports"""
        lines = code.split('\n')
        
        imports_stdlib = []
        imports_third_party = []
        imports_local = []
        other_lines = []
        
        import_section = True
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                if import_section:
                    continue
                other_lines.append(line)
                continue
            
            if stripped.startswith('import ') or stripped.startswith('from '):
                if import_section:
                    module_name = self._extract_module_name(stripped)
                    if self._is_stdlib_module(module_name):
                        imports_stdlib.append(line)
                    elif self._is_local_module(module_name):
                        imports_local.append(line)
                    else:
                        imports_third_party.append(line)
                else:
                    other_lines.append(line)
            else:
                import_section = False
                other_lines.append(line)
        
        # Construir código reorganizado
        result = []
        
        if imports_stdlib:
            result.extend(sorted(imports_stdlib))
            result.append('')
        
        if imports_third_party:
            result.extend(sorted(imports_third_party))
            result.append('')
        
        if imports_local:
            result.extend(sorted(imports_local))
            result.append('')
        
        result.extend(other_lines)
        
        return '\n'.join(result)
    
    def _extract_module_name(self, import_line: str) -> str:
        """Extrae el nombre del módulo de una línea import"""
        if import_line.startswith('from '):
            parts = import_line.split()
            if len(parts) >= 2:
                return parts[1].split('.')[0]
        elif import_line.startswith('import '):
            parts = import_line.split()
            if len(parts) >= 2:
                return parts[1].split('.')[0]
        return ""
    
    def _is_stdlib_module(self, module_name: str) -> bool:
        """Verifica si un módulo es de la biblioteca estándar"""
        stdlib_modules = {
            'os', 'sys', 'datetime', 'json', 'urllib', 'http', 're', 'math',
            'random', 'collections', 'itertools', 'functools', 'operator',
            'pathlib', 'typing', 'abc', 'contextlib', 'dataclasses',
            'asyncio', 'threading', 'multiprocessing', 'subprocess',
            'sqlite3', 'csv', 'configparser', 'argparse', 'logging',
            'unittest', 'traceback', 'warnings', 'copy', 'pickle',
            'base64', 'hashlib', 'hmac', 'secrets', 'uuid', 'time'
        }
        return module_name in stdlib_modules
    
    def _is_local_module(self, module_name: str) -> bool:
        """Verifica si un módulo es local (relativo)"""
        return module_name.startswith('.') or module_name in ['config', 'utils', 'views', 'models']
    
    def format_on_save(self, code: str) -> str:
        """Formatea código al guardar si está habilitado"""
        if self.config.FORMATTER_AUTO_FORMAT_ON_SAVE:
            return self.format_code(code)
        return code
    
    def get_formatting_info(self, code: str) -> Dict:
        """Obtiene información sobre el estado del formateo"""
        lines = code.split('\n')
        
        info = {
            'total_lines': len(lines),
            'empty_lines': sum(1 for line in lines if not line.strip()),
            'max_line_length': max(len(line) for line in lines) if lines else 0,
            'trailing_whitespace_lines': sum(1 for line in lines if line.rstrip() != line),
            'indentation_issues': 0,
            'spacing_issues': 0,
            'import_issues': 0
        }
        
        # Analizar problemas de indentación
        for line in lines:
            if line.strip():
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces % self.config.FORMATTER_INDENT_SIZE != 0:
                    info['indentation_issues'] += 1
        
        # Analizar problemas de espaciado
        for line in lines:
            if re.search(r'[+\-*/%=<>!&|^]+\w|\w[+\-*/%=<>!&|^]+', line):
                info['spacing_issues'] += 1
        
        return info


class FormatterPreferences:
    """
    Clase para manejar las preferencias del formatter
    """
    
    @staticmethod
    def get_available_engines() -> List[str]:
        """Obtiene los motores de formateo disponibles"""
        engines = ['manual']
        
        try:
            import autopep8
            engines.append('autopep8')
        except ImportError:
            pass
        
        try:
            import black
            engines.append('black')
        except ImportError:
            pass
        
        return engines
    
    @staticmethod
    def install_formatter_engine(engine_name: str) -> bool:
        """Instala un motor de formateo"""
        try:
            if engine_name == 'autopep8':
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'autopep8'])
            elif engine_name == 'black':
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'black'])
            elif engine_name == 'isort':
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'isort'])
            return True
        except subprocess.CalledProcessError:
            return False


# Instancia global del formatter
code_formatter = CodeFormatter()
