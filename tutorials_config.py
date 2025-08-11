#!/usr/bin/env python3
"""
Configuración de tutoriales independiente
Archivo para gestionar todos los tutoriales de manera sencilla
"""

from typing import List, Dict, Any

def get_tutorials_config() -> List[Dict[str, Any]]:
    """
    Configuración de todos los tutoriales disponibles
    
    Para añadir un nuevo tutorial:
    1. Añade un nuevo diccionario a la lista
    2. Define los pasos con su contenido
    3. Especifica la validación si es necesaria
    
    Returns:
        List[Dict]: Lista de configuraciones de tutoriales
    """
    return [
        # Tutorial 1: Primeros pasos con Python
        {
            'id': 'python_basics',
            'title': 'Primeros pasos con Python',
            'description': 'Aprende lo básico de Python: variables, tipos de datos y operaciones simples',
            'difficulty': 'Principiante',
            'steps': [
                {
                    'title': 'Bienvenido a Python',
                    'content': '''¡Hola! Bienvenido a tu primer tutorial de Python.
                    
Python es un lenguaje de programación muy popular y fácil de aprender. Es perfecto para principiantes porque:

• **Sintaxis simple**: Se lee casi como inglés
• **Muy potente**: Puedes hacer desde páginas web hasta inteligencia artificial
• **Gran comunidad**: Millones de programadores te pueden ayudar

¡Empecemos con tu primera línea de código!''',
                    'code_example': 'print("¡Hola, mundo!")',
                    'expected_output': '¡Hola, mundo!',
                    'validation_contains': ['print'],
                    'hints': [
                        'La función print() muestra texto en la pantalla',
                        'El texto debe ir entre comillas ("texto")',
                        'No olvides cerrar el paréntesis'
                    ]
                },
                {
                    'title': 'Variables y números',
                    'content': '''Excelente! Ahora aprenderás sobre **variables**.

Las variables son como cajas donde guardas información:

• **Números enteros**: `edad = 25`
• **Números decimales**: `altura = 1.75`
• **Texto**: `nombre = "Ana"`

Python es inteligente y detecta automáticamente qué tipo de dato estás guardando.''',
                    'code_example': '''edad = 25
nombre = "Ana"
print("Mi nombre es", nombre, "y tengo", edad, "años")''',
                    'expected_output': 'Mi nombre es Ana y tengo 25 años',
                    'validation_contains': ['=', 'print'],
                    'hints': [
                        'Usa = para asignar valores a variables',
                        'Los nombres van entre comillas',
                        'Los números van sin comillas',
                        'Puedes mostrar varias cosas con print separándolas por comas'
                    ]
                },
                {
                    'title': 'Operaciones matemáticas',
                    'content': '''¡Genial! Ahora aprenderás operaciones matemáticas básicas.

Python puede hacer matemáticas como una calculadora:

• **Suma**: `+`
• **Resta**: `-`
• **Multiplicación**: `*`
• **División**: `/`

También puedes usar paréntesis para cambiar el orden de las operaciones.''',
                    'code_example': '''numero1 = 10
numero2 = 5
suma = numero1 + numero2
print("La suma es:", suma)
print("La multiplicación es:", numero1 * numero2)''',
                    'expected_output': '''La suma es: 15
La multiplicación es: 50''',
                    'validation_contains': ['+', 'print'],
                    'hints': [
                        'Usa + para sumar números',
                        'Puedes guardar el resultado en una variable',
                        'Recuerda que * significa multiplicación',
                        'Puedes hacer varias operaciones en una línea'
                    ]
                },
                {
                    'title': 'Pidiendo información al usuario',
                    'content': '''¡Muy bien! Ahora aprenderás a pedir información al usuario.

La función `input()` te permite pedir al usuario que escriba algo:

• **input()**: Pide texto al usuario
• **int()**: Convierte texto a número entero
• **float()**: Convierte texto a número decimal

¡Esto hace que tus programas sean interactivos!''',
                    'code_example': '''nombre = input("¿Cómo te llamas? ")
edad = input("¿Cuántos años tienes? ")
print("Hola", nombre + ", tienes", edad, "años")''',
                    'expected_output': '''¿Cómo te llamas? Juan
¿Cuántos años tienes? 20
Hola Juan, tienes 20 años''',
                    'validation_contains': ['input', 'print'],
                    'hints': [
                        'input() siempre devuelve texto',
                        'Puedes poner una pregunta dentro de input()',
                        'Para unir texto usa el símbolo +'
                    ]
                }
            ]
        },
        
        # Tutorial 2: Estructuras de control
        {
            'id': 'control_structures',
            'title': 'Estructuras de control',
            'description': 'Aprende a usar if, else, for y while para controlar el flujo de tu programa',
            'difficulty': 'Principiante',
            'steps': [
                {
                    'title': 'Decisiones con if',
                    'content': '''Ahora aprenderás a tomar decisiones en tu programa.

La estructura `if` ejecuta código solo si una condición es verdadera:

• **if**: Si la condición es verdadera, ejecuta el código
• **else**: Si no, ejecuta este otro código
• **elif**: Si hay más opciones

¡Es como decir "si pasa esto, haz aquello"!''',
                    'code_example': '''edad = 18
if edad >= 18:
    print("Eres mayor de edad")
else:
    print("Eres menor de edad")''',
                    'expected_output': 'Eres mayor de edad',
                    'validation_contains': ['if', 'print'],
                    'hints': [
                        'Usa >= para "mayor o igual que"',
                        'No olvides los dos puntos : después del if',
                        'El código después del if debe estar indentado',
                        'else se ejecuta cuando if es falso'
                    ]
                },
                {
                    'title': 'Múltiples opciones con elif',
                    'content': '''¡Excelente! Ahora aprenderás a manejar múltiples opciones.

Con `elif` puedes verificar varias condiciones:

• **if**: Primera condición
• **elif**: Segunda condición (y más...)
• **else**: Si ninguna es verdadera

¡Es como tener un menú de opciones!''',
                    'code_example': '''nota = 85
if nota >= 90:
    print("Excelente")
elif nota >= 70:
    print("Bien")
else:
    print("Necesitas estudiar más")''',
                    'expected_output': 'Bien',
                    'validation_contains': ['if', 'elif', 'print'],
                    'hints': [
                        'elif significa "else if" (sino si)',
                        'Puedes tener varios elif',
                        'Solo se ejecuta el primer caso verdadero',
                        'Siempre indenta el código después de :'
                    ]
                },
                {
                    'title': 'Bucles con for',
                    'content': '''¡Genial! Ahora aprenderás a repetir código automáticamente.

El bucle `for` repite código un número específico de veces:

• **range(5)**: Números del 0 al 4
• **range(1, 6)**: Números del 1 al 5
• **for**: Repite para cada elemento

¡Es perfecto para tareas repetitivas!''',
                    'code_example': '''print("Contando del 1 al 5:")
for numero in range(1, 6):
    print("Número:", numero)
print("¡Terminé de contar!")''',
                    'expected_output': '''Contando del 1 al 5:
Número: 1
Número: 2
Número: 3
Número: 4
Número: 5
¡Terminé de contar!''',
                    'validation_contains': ['for', 'range', 'print'],
                    'hints': [
                        'range(1, 6) va del 1 al 5 (no incluye el 6)',
                        'La variable numero toma cada valor del rango',
                        'Indenta el código que quieres repetir',
                        'for in range() es muy común en Python'
                    ]
                },
                {
                    'title': 'Bucles con while',
                    'content': '''¡Muy bien! Ahora aprenderás otro tipo de bucle.

El bucle `while` repite mientras una condición sea verdadera:

• **while**: Mientras la condición sea verdadera
• **Cuidado**: Asegúrate de que la condición cambie
• **Infinito**: Si no cambia, el bucle nunca para

¡Es útil cuando no sabes cuántas veces repetir!''',
                    'code_example': '''contador = 1
while contador <= 3:
    print("Vuelta número:", contador)
    contador = contador + 1
print("Bucle terminado")''',
                    'expected_output': '''Vuelta número: 1
Vuelta número: 2
Vuelta número: 3
Bucle terminado''',
                    'validation_contains': ['while', 'print'],
                    'hints': [
                        'while continúa mientras la condición sea verdadera',
                        'Siempre modifica la variable del while',
                        'contador = contador + 1 se puede escribir como contador += 1',
                        'Si no cambias contador, el bucle será infinito'
                    ]
                }
            ]
        },
        
        # Tutorial 3: Listas y funciones
        {
            'id': 'lists_functions',
            'title': 'Listas y funciones',
            'description': 'Aprende a trabajar con listas y crear tus propias funciones',
            'difficulty': 'Intermedio',
            'steps': [
                {
                    'title': 'Trabajando con listas',
                    'content': '''¡Hola de nuevo! Ahora aprenderás sobre **listas**.

Las listas te permiten guardar varios elementos en una sola variable:

• **Crear lista**: `numeros = [1, 2, 3]`
• **Agregar**: `lista.append(elemento)`
• **Acceder**: `lista[0]` (primer elemento)
• **Longitud**: `len(lista)`

¡Es como tener una caja con compartimentos!''',
                    'code_example': '''frutas = ["manzana", "banana", "naranja"]
print("Mis frutas:", frutas)
print("Primera fruta:", frutas[0])
frutas.append("uva")
print("Ahora tengo", len(frutas), "frutas")''',
                    'expected_output': '''Mis frutas: ['manzana', 'banana', 'naranja']
Primera fruta: manzana
Ahora tengo 4 frutas''',
                    'validation_contains': ['[', ']', 'append', 'print'],
                    'hints': [
                        'Las listas van entre corchetes []',
                        'Los elementos se separan por comas',
                        'append() añade un elemento al final',
                        'len() te dice cuántos elementos hay'
                    ]
                },
                {
                    'title': 'Recorriendo listas',
                    'content': '''¡Excelente! Ahora aprenderás a recorrer listas.

Puedes usar `for` para procesar cada elemento de una lista:

• **for elemento in lista**: Recorre todos los elementos
• **for i in range(len(lista))**: Recorre por índices
• **enumerate()**: Te da posición y elemento

¡Es muy útil para procesar datos!''',
                    'code_example': '''colores = ["rojo", "verde", "azul"]
print("Mis colores favoritos:")
for color in colores:
    print("- Me gusta el", color)
    
print("\\nTotal de colores:", len(colores))''',
                    'expected_output': '''Mis colores favoritos:
- Me gusta el rojo
- Me gusta el verde
- Me gusta el azul

Total de colores: 3''',
                    'validation_contains': ['for', 'in', 'print'],
                    'hints': [
                        'for color in colores recorre cada elemento',
                        'La variable color toma el valor de cada elemento',
                        '\\n crea una línea nueva',
                        'Puedes usar cualquier nombre para la variable'
                    ]
                },
                {
                    'title': 'Creando funciones',
                    'content': '''¡Genial! Ahora aprenderás a crear tus propias funciones.

Las funciones son bloques de código reutilizable:

• **def**: Define una nueva función
• **Parámetros**: Información que recibe
• **return**: Valor que devuelve
• **Llamar**: Usar la función

¡Es como crear tus propias herramientas!''',
                    'code_example': '''def saludar(nombre):
    mensaje = "¡Hola, " + nombre + "!"
    return mensaje

# Usar la función
saludo = saludar("Ana")
print(saludo)
print(saludar("Luis"))''',
                    'expected_output': '''¡Hola, Ana!
¡Hola, Luis!''',
                    'validation_contains': ['def', 'return', 'print'],
                    'hints': [
                        'def nombre_funcion(parametros): define una función',
                        'Los parámetros van entre paréntesis',
                        'return devuelve un valor',
                        'Para usar la función, llámala con nombre_funcion()'
                    ]
                },
                {
                    'title': 'Funciones con múltiples parámetros',
                    'content': '''¡Muy bien! Ahora aprenderás funciones más avanzadas.

Las funciones pueden recibir varios parámetros y hacer cálculos:

• **Múltiples parámetros**: Separados por comas
• **Valores por defecto**: `parametro=valor`
• **Sin return**: La función solo ejecuta código
• **Con return**: Devuelve un resultado

¡Puedes crear funciones muy poderosas!''',
                    'code_example': '''def calcular_area(largo, ancho):
    area = largo * ancho
    return area

def presentar_resultado(largo, ancho, area):
    print(f"Un rectángulo de {largo}x{ancho} tiene área {area}")

# Usar las funciones
mi_area = calcular_area(5, 3)
presentar_resultado(5, 3, mi_area)''',
                    'expected_output': 'Un rectángulo de 5x3 tiene área 15',
                    'validation_contains': ['def', 'return', 'print'],
                    'hints': [
                        'Separa múltiples parámetros con comas',
                        'Puedes llamar una función desde otra',
                        'f"texto {variable}" es un f-string',
                        'Divide tareas complejas en funciones simples'
                    ]
                }
            ]
        }
    ]

# Función auxiliar para validación personalizada
def validate_tutorial_code(tutorial_id: str, step_index: int, code: str) -> dict:
    """
    Validación personalizada para códigos específicos de tutoriales
    
    Args:
        tutorial_id: ID del tutorial
        step_index: Índice del paso (0-based)
        code: Código a validar
    
    Returns:
        dict: Resultado de validación con 'valid' y 'message'
    """
    
    # Validaciones básicas para todos los tutoriales
    basic_validations = {
        'python_basics': {
            0: lambda c: 'print' in c,
            1: lambda c: '=' in c and 'print' in c,
            2: lambda c: '+' in c or '*' in c or '-' in c or '/' in c,
            3: lambda c: 'input' in c
        },
        'control_structures': {
            0: lambda c: 'if' in c,
            1: lambda c: 'if' in c and 'elif' in c,
            2: lambda c: 'for' in c and 'range' in c,
            3: lambda c: 'while' in c
        },
        'lists_functions': {
            0: lambda c: '[' in c and ']' in c,
            1: lambda c: 'for' in c and 'in' in c,
            2: lambda c: 'def' in c and 'return' in c,
            3: lambda c: 'def' in c and 'return' in c
        }
    }
    
    if tutorial_id in basic_validations and step_index in basic_validations[tutorial_id]:
        validation_func = basic_validations[tutorial_id][step_index]
        if validation_func(code.lower()):
            return {'valid': True, 'message': '¡Buen trabajo! Continúa al siguiente paso.'}
        else:
            # Mensajes específicos por tutorial y paso
            specific_messages = {
                'python_basics': {
                    0: 'Parece que falta la función print(). ¿La incluiste?',
                    1: 'Recuerda usar el símbolo = para asignar valores a variables.',
                    2: 'Intenta usar operadores matemáticos como +, -, * o /',
                    3: 'Necesitas usar input() para pedir información al usuario.'
                },
                'control_structures': {
                    0: 'No veo la palabra clave "if". ¿La incluiste?',
                    1: 'Necesitas usar tanto "if" como "elif" en tu código.',
                    2: 'Recuerda usar "for" y "range" para crear el bucle.',
                    3: 'Necesitas usar "while" para crear el bucle.'
                },
                'lists_functions': {
                    0: 'Recuerda que las listas van entre corchetes []',
                    1: 'Usa "for elemento in lista" para recorrer la lista.',
                    2: 'Define una función con "def" y devuelve un valor con "return".',
                    3: 'Crea una función con parámetros y usa "return".'
                }
            }
            
            message = specific_messages.get(tutorial_id, {}).get(step_index, 
                'Revisa tu código e intenta de nuevo.')
            return {'valid': False, 'message': message}
    
    return {'valid': True, 'message': 'Código aceptado.'}
