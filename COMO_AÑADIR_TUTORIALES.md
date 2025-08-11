# 📚 Guía para Añadir Nuevos Tutoriales

## 🎯 **Cómo funciona el sistema modular**

Los tutoriales ahora están completamente separados del código principal en el archivo `tutorials_config.py`. Esto permite:

- ✅ **Fácil mantenimiento**: Edita solo un archivo
- ✅ **Añadir tutoriales rápidamente**: Sin tocar código complejo
- ✅ **Validación personalizada**: Control total sobre la verificación
- ✅ **Estructura clara**: Organización lógica del contenido

---

## 🔧 **Estructura de un tutorial**

Cada tutorial en `tutorials_config.py` tiene esta estructura:

```python
{
    'id': 'identificador_unico',              # ID único del tutorial
    'title': 'Título del Tutorial',           # Nombre que ve el usuario
    'description': 'Descripción breve...',    # Qué aprenderá el usuario
    'difficulty': 'Principiante',             # Principiante/Intermedio/Avanzado
    'steps': [                                # Lista de pasos
        {
            'title': 'Nombre del paso',
            'content': '''Contenido explicativo...''',
            'code_example': 'print("ejemplo")',
            'expected_output': 'ejemplo',
            'validation_contains': ['print'],
            'hints': ['Pista 1', 'Pista 2']
        },
        # Más pasos...
    ]
}
```

---

## ➕ **Cómo añadir un nuevo tutorial**

### **Paso 1: Abrir el archivo de configuración**
```bash
nano tutorials_config.py
```

### **Paso 2: Añadir el tutorial a la lista**
Busca la función `get_tutorials_config()` y añade tu tutorial al final de la lista:

```python
def get_tutorials_config() -> List[Dict[str, Any]]:
    return [
        # Tutoriales existentes...
        
        # TU NUEVO TUTORIAL AQUÍ
        {
            'id': 'mi_nuevo_tutorial',
            'title': 'Mi Nuevo Tutorial',
            'description': 'Aprende conceptos nuevos paso a paso',
            'difficulty': 'Intermedio',
            'steps': [
                {
                    'title': 'Primer paso',
                    'content': '''Explicación del concepto...
                    
Puntos importantes:
• Punto 1
• Punto 2
• Punto 3''',
                    'code_example': 'codigo_ejemplo = "hola"',
                    'expected_output': 'Resultado esperado',
                    'validation_contains': ['codigo_ejemplo'],
                    'hints': [
                        'Pista útil 1',
                        'Pista útil 2'
                    ]
                },
                # Más pasos...
            ]
        }
    ]
```

### **Paso 3: Añadir validación personalizada (opcional)**
Si necesitas validación especial, edita la función `validate_tutorial_code()`:

```python
def validate_tutorial_code(tutorial_id: str, step_index: int, code: str) -> dict:
    # Validaciones básicas existentes...
    
    # TU VALIDACIÓN PERSONALIZADA
    if tutorial_id == 'mi_nuevo_tutorial':
        if step_index == 0:
            if 'concepto_importante' not in code.lower():
                return {'valid': False, 'message': 'Incluye el concepto importante'}
    
    # Resto del código...
```

---

## 📝 **Campos explicados**

### **Campos obligatorios:**
- **`id`**: Identificador único (solo letras, números y guiones bajos)
- **`title`**: Título visible para el usuario
- **`description`**: Breve descripción de qué aprenderá
- **`difficulty`**: `'Principiante'`, `'Intermedio'` o `'Avanzado'`
- **`steps`**: Lista de pasos (mínimo 1)

### **Campos de cada paso:**
- **`title`**: Nombre del paso
- **`content`**: Explicación (puede usar Markdown)
- **`code_example`** (opcional): Código de ejemplo
- **`expected_output`** (opcional): Salida esperada
- **`validation_contains`** (opcional): Palabras que debe contener el código
- **`hints`** (opcional): Lista de pistas

---

## 🎨 **Consejos para crear buen contenido**

### **📖 Contenido explicativo:**
```python
'content': '''¡Hola! Ahora aprenderás sobre **variables**.

Las variables son como cajas donde guardas información:

• **Tipo 1**: Descripción
• **Tipo 2**: Descripción  
• **Tipo 3**: Descripción

¡Empecemos con un ejemplo!'''
```

### **💻 Ejemplos de código:**
```python
'code_example': '''variable = "valor"
print("El valor es:", variable)
resultado = variable + " modificado"'''
```

### **💡 Pistas útiles:**
```python
'hints': [
    'Recuerda usar comillas para texto',
    'La función print() muestra información',
    'Las variables se crean con el símbolo ='
]
```

---

## 🧪 **Probar tu tutorial**

### **1. Verificar sintaxis:**
```bash
python3 -c "from tutorials_config import get_tutorials_config; print('✅ Sintaxis correcta')"
```

### **2. Ver tutoriales disponibles:**
```bash
python3 -c "from tutorials_config import get_tutorials_config; [print(f'📚 {t[\"title\"]} ({t[\"difficulty\"]}) - {len(t[\"steps\"])} pasos') for t in get_tutorials_config()]"
```

### **3. Probar en la aplicación:**
1. Ejecuta la aplicación: `python3 main.py`
2. Presiona `F4` para abrir tutoriales
3. Busca tu nuevo tutorial en la lista
4. Prueba todos los pasos

---

## ✅ **Checklist de calidad**

Antes de finalizar tu tutorial, verifica:

- [ ] **ID único**: No existe otro tutorial con el mismo ID
- [ ] **Título claro**: Describe bien qué se aprenderá
- [ ] **Dificultad apropiada**: Coherente con el contenido
- [ ] **Pasos progresivos**: Cada paso construye sobre el anterior
- [ ] **Ejemplos funcionales**: Todo el código funciona correctamente
- [ ] **Pistas útiles**: Ayudan sin dar la respuesta completa
- [ ] **Validación adecuada**: Detecta errores comunes
- [ ] **Contenido completo**: Explicaciones claras y suficientes

---

## 🚀 **Ejemplos de temas para nuevos tutoriales**

### **Principiante:**
- Trabajando con archivos
- Manejo de errores básico
- Módulos e import
- Diccionarios básicos

### **Intermedio:**
- Programación orientada a objetos
- Manejo de excepciones
- Comprensiones de lista
- Decoradores básicos

### **Avanzado:**
- Generators y iteradores
- Context managers
- Programación asíncrona
- Metaprogramación

---
