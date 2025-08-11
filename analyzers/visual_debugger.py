#!/usr/bin/env python3
"""
Sistema básico de debugging visual para principiantes
Permite ejecutar código paso a paso y inspeccionar variables
"""

import ast
import sys
import traceback
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import io
import contextlib

@dataclass
class BreakPoint:
    """Representa un punto de interrupción"""
    line_number: int
    condition: str = ""  # Condición opcional para el breakpoint
    enabled: bool = True

@dataclass
class Variable:
    """Representa una variable en el contexto actual"""
    name: str
    value: Any
    type_name: str
    line_defined: int = 0

@dataclass
class ExecutionState:
    """Estado actual de la ejecución"""
    current_line: int
    variables: Dict[str, Variable]
    output: List[str]
    error: Optional[str]
    finished: bool
    call_stack: List[str]

class SimpleDebugger:
    """Debugger básico para principiantes"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reinicia el estado del debugger"""
        self.code = ""
        self.lines = []
        self.breakpoints: Dict[int, BreakPoint] = {}
        self.current_line = 0
        self.variables: Dict[str, Any] = {}
        self.output = []
        self.error = None
        self.finished = False
        self.execution_context = {}
        self.step_mode = False
    
    def set_code(self, code: str):
        """Establece el código a debuggear"""
        self.code = code
        self.lines = code.split('\n')
        self.reset_execution()
    
    def reset_execution(self):
        """Reinicia la ejecución pero mantiene breakpoints"""
        self.current_line = 0
        self.variables = {}
        self.output = []
        self.error = None
        self.finished = False
        self.execution_context = {}
    
    def add_breakpoint(self, line_number: int, condition: str = "") -> bool:
        """Agrega un breakpoint en la línea especificada"""
        if 1 <= line_number <= len(self.lines):
            self.breakpoints[line_number] = BreakPoint(line_number, condition)
            return True
        return False
    
    def remove_breakpoint(self, line_number: int) -> bool:
        """Elimina un breakpoint"""
        if line_number in self.breakpoints:
            del self.breakpoints[line_number]
            return True
        return False
    
    def toggle_breakpoint(self, line_number: int) -> bool:
        """Activa/desactiva un breakpoint"""
        if line_number in self.breakpoints:
            self.breakpoints[line_number].enabled = not self.breakpoints[line_number].enabled
            return self.breakpoints[line_number].enabled
        else:
            return self.add_breakpoint(line_number)
    
    def get_breakpoints(self) -> List[int]:
        """Retorna lista de líneas con breakpoints activos"""
        return [bp.line_number for bp in self.breakpoints.values() if bp.enabled]
    
    def should_break_at_line(self, line_number: int) -> bool:
        """Verifica si debe parar en esta línea"""
        if line_number in self.breakpoints and self.breakpoints[line_number].enabled:
            bp = self.breakpoints[line_number]
            if not bp.condition:
                return True
            # Evaluar condición del breakpoint
            try:
                return eval(bp.condition, self.execution_context)
            except:
                return True  # Si hay error en la condición, parar anyway
        return False
    
    def execute_line(self, line_content: str, line_number: int) -> Tuple[bool, str]:
        """Ejecuta una línea de código y retorna (success, output)"""
        try:
            # Capturar output
            old_stdout = sys.stdout
            captured_output = io.StringIO()
            
            with contextlib.redirect_stdout(captured_output):
                # Intentar compilar y ejecutar la línea
                if line_content.strip():
                    # Compilar la línea
                    try:
                        # Primero intentar como statement
                        code_obj = compile(line_content, f'<line {line_number}>', 'exec')
                        exec(code_obj, self.execution_context)
                    except SyntaxError:
                        # Si falla, intentar como expression
                        try:
                            code_obj = compile(line_content, f'<line {line_number}>', 'eval')
                            result = eval(code_obj, self.execution_context)
                            if result is not None:
                                print(result)
                        except:
                            # Si ambos fallan, re-raise el error original
                            raise
            
            output = captured_output.getvalue()
            if output:
                self.output.append(output.strip())
            
            return True, output
            
        except Exception as e:
            error_msg = f"Error en línea {line_number}: {str(e)}"
            self.error = error_msg
            return False, error_msg
    
    def step_over(self) -> ExecutionState:
        """Ejecuta la siguiente línea de código"""
        if self.finished:
            return self.get_current_state()
        
        # Buscar la siguiente línea ejecutable
        while self.current_line < len(self.lines):
            line_content = self.lines[self.current_line].strip()
            line_number = self.current_line + 1
            
            # Saltar líneas vacías y comentarios
            if not line_content or line_content.startswith('#'):
                self.current_line += 1
                continue
            
            # Ejecutar la línea
            success, output = self.execute_line(line_content, line_number)
            
            # Actualizar variables desde el contexto
            self._update_variables()
            
            self.current_line += 1
            
            if not success:
                self.finished = True
                break
            
            # Si es modo step o hay breakpoint, parar aquí
            if self.step_mode or self.should_break_at_line(line_number):
                break
        
        # Verificar si terminó la ejecución
        if self.current_line >= len(self.lines):
            self.finished = True
        
        return self.get_current_state()
    
    def run_to_breakpoint(self) -> ExecutionState:
        """Ejecuta hasta el siguiente breakpoint"""
        self.step_mode = False
        
        while not self.finished and self.current_line < len(self.lines):
            line_number = self.current_line + 1
            
            # Si hay breakpoint en esta línea, parar antes de ejecutar
            if self.should_break_at_line(line_number):
                break
                
            self.step_over()
        
        return self.get_current_state()
    
    def run_all(self) -> ExecutionState:
        """Ejecuta todo el código de una vez"""
        self.step_mode = False
        
        try:
            # Capturar todo el output
            old_stdout = sys.stdout
            captured_output = io.StringIO()
            
            with contextlib.redirect_stdout(captured_output):
                exec(self.code, self.execution_context)
            
            self.output = captured_output.getvalue().split('\n') if captured_output.getvalue() else []
            self.finished = True
            self.current_line = len(self.lines)
            self._update_variables()
            
        except Exception as e:
            self.error = f"Error en la ejecución: {str(e)}"
            self.finished = True
        
        return self.get_current_state()
    
    def step_into(self) -> ExecutionState:
        """Paso a paso (igual que step_over para esta implementación básica)"""
        self.step_mode = True
        return self.step_over()
    
    def _update_variables(self):
        """Actualiza las variables desde el contexto de ejecución"""
        self.variables = {}
        for name, value in self.execution_context.items():
            if not name.startswith('__') and not callable(value):
                self.variables[name] = Variable(
                    name=name,
                    value=value,
                    type_name=type(value).__name__,
                    line_defined=self.current_line
                )
    
    def get_current_state(self) -> ExecutionState:
        """Retorna el estado actual de la ejecución"""
        return ExecutionState(
            current_line=self.current_line + 1 if self.current_line < len(self.lines) else len(self.lines),
            variables=self.variables.copy(),
            output=self.output.copy(),
            error=self.error,
            finished=self.finished,
            call_stack=[f"Línea {self.current_line + 1}"] if not self.finished else []
        )
    
    def get_variable_info(self, var_name: str) -> Optional[Dict]:
        """Retorna información detallada de una variable"""
        if var_name in self.variables:
            var = self.variables[var_name]
            return {
                'name': var.name,
                'value': str(var.value),
                'type': var.type_name,
                'repr': repr(var.value),
                'line_defined': var.line_defined
            }
        return None
    
    def evaluate_expression(self, expression: str) -> Dict:
        """Evalúa una expresión en el contexto actual"""
        try:
            result = eval(expression, self.execution_context)
            return {
                'success': True,
                'result': str(result),
                'type': type(result).__name__,
                'repr': repr(result)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

class DebuggerManager:
    """Gestor del sistema de debugging"""
    
    def __init__(self):
        self.debugger = SimpleDebugger()
        self.is_debugging = False
    
    def start_debugging(self, code: str) -> Dict:
        """Inicia una sesión de debugging"""
        self.debugger.set_code(code)
        self.is_debugging = True
        
        return {
            'status': 'started',
            'lines_count': len(self.debugger.lines),
            'state': self._state_to_dict(self.debugger.get_current_state())
        }
    
    def stop_debugging(self) -> Dict:
        """Detiene la sesión de debugging"""
        self.is_debugging = False
        self.debugger.reset()
        
        return {'status': 'stopped'}
    
    def step_over(self) -> Dict:
        """Ejecuta la siguiente línea"""
        if not self.is_debugging:
            return {'error': 'No hay sesión de debugging activa'}
        
        state = self.debugger.step_over()
        return self._state_to_dict(state)
    
    def run_to_breakpoint(self) -> Dict:
        """Ejecuta hasta el siguiente breakpoint"""
        if not self.is_debugging:
            return {'error': 'No hay sesión de debugging activa'}
        
        state = self.debugger.run_to_breakpoint()
        return self._state_to_dict(state)
    
    def toggle_breakpoint(self, line_number: int) -> Dict:
        """Activa/desactiva un breakpoint"""
        enabled = self.debugger.toggle_breakpoint(line_number)
        return {
            'line': line_number,
            'enabled': enabled,
            'breakpoints': self.debugger.get_breakpoints()
        }
    
    def get_variable_details(self, var_name: str) -> Dict:
        """Obtiene detalles de una variable"""
        info = self.debugger.get_variable_info(var_name)
        if info:
            return info
        return {'error': f'Variable "{var_name}" no encontrada'}
    
    def evaluate(self, expression: str) -> Dict:
        """Evalúa una expresión"""
        return self.debugger.evaluate_expression(expression)
    
    def _state_to_dict(self, state: ExecutionState) -> Dict:
        """Convierte ExecutionState a diccionario"""
        return {
            'current_line': state.current_line,
            'variables': {
                name: {
                    'value': str(var.value),
                    'type': var.type_name,
                    'line_defined': var.line_defined
                }
                for name, var in state.variables.items()
            },
            'output': state.output,
            'error': state.error,
            'finished': state.finished,
            'call_stack': state.call_stack,
            'breakpoints': self.debugger.get_breakpoints()
        }

# Función helper para la UI
def get_debugger_manager() -> DebuggerManager:
    """Retorna una instancia del gestor de debugging"""
    return DebuggerManager()
