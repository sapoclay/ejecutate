#!/usr/bin/env python3
"""
Sistema de autocompletado inteligente con explicaciones
Proporciona sugerencias contextales con documentación
"""

import keyword
import builtins
from typing import List, Dict, Tuple

class CompletionItem:
    """Representa un elemento de autocompletado"""
    def __init__(self, text: str, description: str, type_: str = "function", example: str = ""):
        self.text = text
        self.description = description
        self.type = type_  # "function", "keyword", "builtin", "snippet"
        self.example = example

class SmartAutoCompleter:
    """Sistema de autocompletado inteligente para principiantes"""
    
    def __init__(self):
        self.builtin_functions = self._get_builtin_functions()
        self.keywords = self._get_python_keywords()
        self.snippets = self._get_code_snippets()
    
    def _get_builtin_functions(self) -> Dict[str, CompletionItem]:
        """Retorna funciones built-in con explicaciones para principiantes"""
        return {
            'print': CompletionItem(
                'print()',
                'Muestra texto en la pantalla',
                'builtin',
                'print("Hola mundo")'
            ),
            'input': CompletionItem(
                'input()',
                'Pide al usuario que ingrese texto',
                'builtin',
                'nombre = input("¿Cómo te llamas? ")'
            ),
            'len': CompletionItem(
                'len()',
                'Devuelve la longitud de una lista, string, etc.',
                'builtin',
                'len("Python")  # Resultado: 6'
            ),
            'range': CompletionItem(
                'range()',
                'Genera una secuencia de números',
                'builtin',
                'for i in range(5):  # 0, 1, 2, 3, 4'
            ),
            'str': CompletionItem(
                'str()',
                'Convierte un valor a texto (string)',
                'builtin',
                'texto = str(123)  # "123"'
            ),
            'int': CompletionItem(
                'int()',
                'Convierte un valor a número entero',
                'builtin',
                'numero = int("42")  # 42'
            ),
            'float': CompletionItem(
                'float()',
                'Convierte un valor a número decimal',
                'builtin',
                'decimal = float("3.14")  # 3.14'
            ),
            'list': CompletionItem(
                'list()',
                'Crea una lista vacía o convierte a lista',
                'builtin',
                'mi_lista = list()  # []'
            ),
            'dict': CompletionItem(
                'dict()',
                'Crea un diccionario vacío',
                'builtin',
                'mi_dict = dict()  # {}'
            ),
            'type': CompletionItem(
                'type()',
                'Muestra el tipo de dato de una variable',
                'builtin',
                'type(42)  # <class "int">'
            ),
            'max': CompletionItem(
                'max()',
                'Encuentra el valor máximo',
                'builtin',
                'max([1, 5, 3])  # 5'
            ),
            'min': CompletionItem(
                'min()',
                'Encuentra el valor mínimo',
                'builtin',
                'min([1, 5, 3])  # 1'
            ),
            'sum': CompletionItem(
                'sum()',
                'Suma todos los valores de una lista',
                'builtin',
                'sum([1, 2, 3])  # 6'
            ),
            'sorted': CompletionItem(
                'sorted()',
                'Ordena una lista sin modificar la original',
                'builtin',
                'sorted([3, 1, 2])  # [1, 2, 3]'
            ),
            'enumerate': CompletionItem(
                'enumerate()',
                'Numera los elementos de una lista',
                'builtin',
                'for i, valor in enumerate(["a", "b"]):'
            ),
            'zip': CompletionItem(
                'zip()',
                'Combina múltiples listas elemento por elemento',
                'builtin',
                'list(zip([1, 2], ["a", "b"]))  # [(1, "a"), (2, "b")]'
            ),
            'open': CompletionItem(
                'open()',
                'Abre un archivo para leer o escribir',
                'builtin',
                'with open("archivo.txt", "r") as f:'
            )
        }
    
    def _get_python_keywords(self) -> Dict[str, CompletionItem]:
        """Retorna palabras clave de Python con explicaciones"""
        return {
            'if': CompletionItem(
                'if',
                'Ejecuta código solo si una condición es verdadera',
                'keyword',
                'if edad >= 18:\n    print("Eres mayor de edad")'
            ),
            'elif': CompletionItem(
                'elif',
                'Condición adicional si la anterior fue falsa',
                'keyword',
                'elif edad >= 13:\n    print("Eres adolescente")'
            ),
            'else': CompletionItem(
                'else',
                'Se ejecuta si ninguna condición anterior fue verdadera',
                'keyword',
                'else:\n    print("Eres menor de edad")'
            ),
            'for': CompletionItem(
                'for',
                'Repite código para cada elemento de una lista',
                'keyword',
                'for nombre in ["Ana", "Luis"]:\n    print(f"Hola {nombre}")'
            ),
            'while': CompletionItem(
                'while',
                'Repite código mientras una condición sea verdadera',
                'keyword',
                'while contador < 10:\n    print(contador)\n    contador += 1'
            ),
            'def': CompletionItem(
                'def',
                'Define una función que puedes usar después',
                'keyword',
                'def saludar(nombre):\n    return f"Hola {nombre}"'
            ),
            'class': CompletionItem(
                'class',
                'Define una clase (plantilla para objetos)',
                'keyword',
                'class Persona:\n    def __init__(self, nombre):\n        self.nombre = nombre'
            ),
            'return': CompletionItem(
                'return',
                'Devuelve un valor desde una función',
                'keyword',
                'def sumar(a, b):\n    return a + b'
            ),
            'import': CompletionItem(
                'import',
                'Importa un módulo para usar sus funciones',
                'keyword',
                'import math\nprint(math.pi)'
            ),
            'from': CompletionItem(
                'from',
                'Importa funciones específicas de un módulo',
                'keyword',
                'from math import pi, sqrt'
            ),
            'try': CompletionItem(
                'try',
                'Intenta ejecutar código que puede fallar',
                'keyword',
                'try:\n    numero = int(input("Número: "))\nexcept ValueError:\n    print("No es un número")'
            ),
            'except': CompletionItem(
                'except',
                'Maneja errores del bloque try',
                'keyword',
                'except ValueError:\n    print("Error: no es un número válido")'
            ),
            'finally': CompletionItem(
                'finally',
                'Se ejecuta siempre, haya error o no',
                'keyword',
                'finally:\n    print("Esto siempre se ejecuta")'
            ),
            'with': CompletionItem(
                'with',
                'Maneja recursos automáticamente (archivos, etc.)',
                'keyword',
                'with open("archivo.txt") as f:\n    contenido = f.read()'
            ),
            'break': CompletionItem(
                'break',
                'Sale inmediatamente de un bucle',
                'keyword',
                'for i in range(10):\n    if i == 5:\n        break'
            ),
            'continue': CompletionItem(
                'continue',
                'Salta a la siguiente iteración del bucle',
                'keyword',
                'for i in range(5):\n    if i == 2:\n        continue\n    print(i)'
            ),
            'and': CompletionItem(
                'and',
                'Operador lógico: ambas condiciones deben ser verdaderas',
                'keyword',
                'if edad >= 18 and tiene_licencia:\n    print("Puede conducir")'
            ),
            'or': CompletionItem(
                'or',
                'Operador lógico: al menos una condición debe ser verdadera',
                'keyword',
                'if es_admin or es_moderador:\n    print("Tiene permisos")'
            ),
            'not': CompletionItem(
                'not',
                'Operador lógico: invierte el valor de verdad',
                'keyword',
                'if not esta_ocupado:\n    print("Está libre")'
            ),
            'in': CompletionItem(
                'in',
                'Verifica si un elemento está en una lista/string',
                'keyword',
                'if "Python" in lenguajes:\n    print("Python está en la lista")'
            ),
            'is': CompletionItem(
                'is',
                'Verifica si dos variables son el mismo objeto',
                'keyword',
                'if variable is None:\n    print("La variable está vacía")'
            )
        }
    
    def _get_code_snippets(self) -> Dict[str, CompletionItem]:
        """Retorna snippets de código común para principiantes"""
        return {
            'main': CompletionItem(
                'if __name__ == "__main__":',
                'Punto de entrada principal del programa',
                'snippet',
                'if __name__ == "__main__":\n    main()'
            ),
            'forloop': CompletionItem(
                'for i in range():',
                'Bucle for básico con números',
                'snippet',
                'for i in range(10):\n    print(i)'
            ),
            'whileloop': CompletionItem(
                'while condition:',
                'Bucle while básico',
                'snippet',
                'while condicion:\n    # código aquí\n    pass'
            ),
            'ifelse': CompletionItem(
                'if condition: else:',
                'Estructura if-else completa',
                'snippet',
                'if condicion:\n    # si es verdadero\n    pass\nelse:\n    # si es falso\n    pass'
            ),
            'function': CompletionItem(
                'def function_name():',
                'Definición básica de función',
                'snippet',
                'def mi_funcion(parametro):\n    """Describe qué hace la función"""\n    return resultado'
            ),
            'class': CompletionItem(
                'class ClassName:',
                'Definición básica de clase',
                'snippet',
                'class MiClase:\n    def __init__(self):\n        pass'
            ),
            'tryexcept': CompletionItem(
                'try: except:',
                'Manejo básico de errores',
                'snippet',
                'try:\n    # código que puede fallar\n    pass\nexcept Exception as e:\n    print(f"Error: {e}")'
            ),
            'listcomp': CompletionItem(
                '[x for x in list]',
                'Lista por comprensión básica',
                'snippet',
                'numeros_pares = [x for x in range(10) if x % 2 == 0]'
            ),
            'readfile': CompletionItem(
                'with open() as f:',
                'Leer archivo de forma segura',
                'snippet',
                'with open("archivo.txt", "r") as f:\n    contenido = f.read()\n    print(contenido)'
            ),
            'writefile': CompletionItem(
                'with open() as f: write',
                'Escribir archivo de forma segura',
                'snippet',
                'with open("archivo.txt", "w") as f:\n    f.write("Hola mundo")'
            )
        }
    
    def get_completions(self, text: str, cursor_pos: int) -> List[CompletionItem]:
        """Retorna sugerencias de autocompletado basadas en el contexto"""
        # Obtener la palabra actual bajo el cursor
        lines = text[:cursor_pos].split('\n')
        current_line = lines[-1] if lines else ""
        
        # Buscar la palabra parcial actual
        words = current_line.split()
        partial_word = ""
        if words:
            # Si el cursor está al final de una palabra
            if cursor_pos > 0 and text[cursor_pos-1].isalnum():
                partial_word = words[-1]
            # Si el cursor está al inicio o hay espacios
            elif cursor_pos < len(text) and text[cursor_pos].isalnum():
                # Encontrar el inicio de la palabra
                start = cursor_pos
                while start > 0 and text[start-1].isalnum():
                    start -= 1
                end = cursor_pos
                while end < len(text) and text[end].isalnum():
                    end += 1
                partial_word = text[start:end]
        
        completions = []
        
        # Buscar en funciones built-in
        for name, item in self.builtin_functions.items():
            if name.startswith(partial_word.lower()):
                completions.append(item)
        
        # Buscar en palabras clave
        for name, item in self.keywords.items():
            if name.startswith(partial_word.lower()):
                completions.append(item)
        
        # Buscar en snippets si no hay palabra parcial o es muy corta
        if len(partial_word) <= 2:
            for name, item in self.snippets.items():
                if not partial_word or name.startswith(partial_word.lower()):
                    completions.append(item)
        
        # Ordenar por relevancia (exacto primero, luego alfabético)
        completions.sort(key=lambda x: (
            0 if x.text.lower().startswith(partial_word.lower()) else 1,
            x.text.lower()
        ))
        
        return completions[:10]  # Limitar a 10 sugerencias

# Función helper para la UI
def get_smart_completions(text: str, cursor_pos: int) -> List[Dict]:
    """Función helper que retorna completions en formato dict para la UI"""
    completer = SmartAutoCompleter()
    completions = completer.get_completions(text, cursor_pos)
    
    return [
        {
            'text': comp.text,
            'description': comp.description,
            'type': comp.type,
            'example': comp.example
        }
        for comp in completions
    ]
