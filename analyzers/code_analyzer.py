#!/usr/bin/env python3
"""
Analizador de código Python en tiempo real
Detecta errores comunes y sugiere mejoras para principiantes
"""

import ast
import re
from typing import List, Dict, Tuple

class CodeIssue:
    """Representa un problema encontrado en el código"""
    def __init__(self, line: int, message: str, severity: str = "warning", suggestion: str = ""):
        self.line = line
        self.message = message
        self.severity = severity  # "error", "warning", "info"
        self.suggestion = suggestion

class PythonCodeAnalyzer:
    """Analizador de código Python para principiantes"""
    
    def __init__(self):
        self.issues: List[CodeIssue] = []
    
    def analyze(self, code: str) -> List[CodeIssue]:
        """Analiza el código y retorna una lista de problemas encontrados"""
        self.issues = []
        
        if not code.strip():
            return self.issues
        
        lines = code.split('\n')
        
        # Análisis línea por línea
        for i, line in enumerate(lines, 1):
            self._check_line_issues(line, i)
        
        # Análisis de sintaxis con AST
        self._check_syntax_issues(code)
        
        # Análisis de estructura general
        self._check_structure_issues(code)
        
        return self.issues
    
    def _check_line_issues(self, line: str, line_num: int):
        """Verifica problemas específicos de cada línea"""
        stripped = line.strip()
        
        if not stripped:
            return
        
        # Problema: print sin paréntesis (Python 2 style)
        if re.match(r'^\s*print\s+[^(]', line):
            self.issues.append(CodeIssue(
                line_num, 
                "Usa paréntesis con print()", 
                "error",
                f'Cambia "print {stripped.split("print")[1].strip()}" por "print({stripped.split("print")[1].strip()})"'
            ))
        
        # Problema: Variables con nombres no descriptivos
        single_char_vars = re.findall(r'\b([a-z])\s*=', line.lower())
        for var in single_char_vars:
            if var not in ['x', 'y', 'i', 'j', 'n']:  # Excepciones comunes
                self.issues.append(CodeIssue(
                    line_num,
                    f"Variable '{var}' tiene nombre poco descriptivo",
                    "warning",
                    f"Considera usar un nombre más descriptivo que '{var}'"
                ))
        
        # Problema: Comparación con == True/False
        if '== True' in line or '== False' in line:
            self.issues.append(CodeIssue(
                line_num,
                "No uses '== True' o '== False'",
                "warning",
                "Usa directamente la variable o 'not variable'"
            ))
        
        # Problema: input() sin mensaje
        if re.search(r'input\(\s*\)', line):
            self.issues.append(CodeIssue(
                line_num,
                "input() sin mensaje para el usuario",
                "info",
                'Agrega un mensaje: input("Ingresa un valor: ")'
            ))
        
        # Problema: Líneas muy largas
        if len(line) > 79:
            self.issues.append(CodeIssue(
                line_num,
                f"Línea muy larga ({len(line)} caracteres)",
                "warning",
                "Considera dividir la línea en múltiples líneas"
            ))
        
        # Sugerencia: Uso de f-strings
        if '".format(' in line or '" %' in line:
            self.issues.append(CodeIssue(
                line_num,
                "Considera usar f-strings para formateo",
                "info",
                'Ejemplo: f"Hola {nombre}" en lugar de "Hola {}".format(nombre)'
            ))
    
    def _check_syntax_issues(self, code: str):
        """Verifica problemas de sintaxis usando AST"""
        try:
            tree = ast.parse(code)
            self._check_ast_patterns(tree)
        except SyntaxError as e:
            self.issues.append(CodeIssue(
                e.lineno or 1,
                f"Error de sintaxis: {e.msg}",
                "error",
                "Revisa la sintaxis de esta línea"
            ))
        except Exception:
            # Si no se puede parsear, no es un problema crítico
            pass
    
    def _check_ast_patterns(self, tree):
        """Analiza patrones en el AST"""
        for node in ast.walk(tree):
            # Detectar bucles infinitos potenciales
            if isinstance(node, ast.While):
                if isinstance(node.test, ast.Constant) and node.test.value is True:
                    self.issues.append(CodeIssue(
                        node.lineno,
                        "Posible bucle infinito: while True",
                        "warning",
                        "Asegúrate de tener una condición de salida (break)"
                    ))
            
            # Detectar imports no utilizados (básico)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Análisis muy básico - mejorable
                    if alias.name not in ['os', 'sys', 'time', 'math']:
                        self.issues.append(CodeIssue(
                            node.lineno,
                            f"Verifica si usas el módulo '{alias.name}'",
                            "info",
                            "Elimina imports innecesarios para código más limpio"
                        ))
    
    def _check_structure_issues(self, code: str):
        """Verifica problemas de estructura general"""
        lines = code.split('\n')
        
        # Verificar indentación inconsistente
        indentations = []
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                if indent > 0:
                    indentations.append(indent)
        
        if indentations:
            # Verificar si se mezclan tabs y espacios (básico)
            if len(set(indentations)) > 3:  # Más de 3 niveles diferentes puede ser problemático
                self.issues.append(CodeIssue(
                    1,
                    "Indentación inconsistente detectada",
                    "warning",
                    "Usa siempre 4 espacios para indentar"
                ))
        
        # Verificar funciones muy largas
        function_lines = 0
        in_function = False
        function_start = 0
        
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*def\s+', line):
                if in_function and function_lines > 20:
                    self.issues.append(CodeIssue(
                        function_start,
                        f"Función muy larga ({function_lines} líneas)",
                        "info",
                        "Considera dividir en funciones más pequeñas"
                    ))
                in_function = True
                function_start = i
                function_lines = 0
            elif in_function:
                if line.strip():
                    function_lines += 1
                if not line.startswith(' ') and not line.startswith('\t') and line.strip():
                    in_function = False

# Función de utilidad para usar desde el editor
def analyze_code(code: str) -> List[Dict]:
    """Función helper que retorna issues en formato dict para la UI"""
    analyzer = PythonCodeAnalyzer()
    issues = analyzer.analyze(code)
    
    return [
        {
            'line': issue.line,
            'message': issue.message,
            'type': issue.severity,  # Mapear severity a type para compatibilidad
            'suggestion': issue.suggestion
        }
        for issue in issues
    ]
