"""
Modelo: Maneja la lógica de ejecución de código Python
"""
import contextlib
import io
import sys


class CodeExecutor:
    """Modelo para ejecutar código Python y capturar su salida"""
    
    def __init__(self):
        self.last_output = ""
        self.last_errors = ""
    
    @contextlib.contextmanager
    def _capture_output(self):
        """Context manager para capturar stdout y stderr"""
        new_output = io.StringIO()
        new_error = io.StringIO()
        old_output, old_error = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = new_output, new_error
        try:
            yield new_output, new_error
        finally:
            sys.stdout, sys.stderr = old_output, old_error
    
    def execute_code(self, code):
        """
        Ejecuta el código Python y captura la salida
        
        Args:
            code (str): Código Python a ejecutar
            
        Returns:
            dict: Diccionario con 'output', 'errors' y 'success'
        """
        with self._capture_output() as (output, errors):
            try:
                exec(code)
                success = True
            except Exception as e:
                print(f"Error: {e}")
                success = False
        
        self.last_output = output.getvalue()
        self.last_errors = errors.getvalue()
        
        return {
            'output': self.last_output,
            'errors': self.last_errors,
            'success': success
        }
    
    def get_last_execution_result(self):
        """Retorna el resultado de la última ejecución"""
        return {
            'output': self.last_output,
            'errors': self.last_errors
        }
