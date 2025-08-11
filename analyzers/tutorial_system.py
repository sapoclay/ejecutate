#!/usr/bin/env python3
"""
Sistema de tutoriales interactivos mejorado
Ahora usa configuración externa para fácil mantenimiento
"""

from typing import List, Dict, Any, Optional
from tutorials_config import get_tutorials_config, validate_tutorial_code


class TutorialManager:
    """Gestor principal de tutoriales interactivos"""
    
    def __init__(self):
        """Inicializa el gestor de tutoriales"""
        self.tutorials = {}
        self.current_tutorial = None
        self.current_step = 0
        self._load_tutorials()
    
    def _load_tutorials(self):
        """Carga los tutoriales desde la configuración externa"""
        tutorials_config = get_tutorials_config()
        
        for tutorial_config in tutorials_config:
            tutorial_id = tutorial_config['id']
            self.tutorials[tutorial_id] = {
                'id': tutorial_id,
                'title': tutorial_config['title'],
                'description': tutorial_config['description'],
                'difficulty': tutorial_config['difficulty'],
                'steps': tutorial_config['steps'],
                'steps_count': len(tutorial_config['steps'])
            }
    
    def get_tutorial_list(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de tutoriales disponibles
        
        Returns:
            List[Dict]: Lista de tutoriales con información básica
        """
        return [
            {
                'id': tutorial['id'],
                'title': tutorial['title'],
                'description': tutorial['description'],
                'difficulty': tutorial['difficulty'],
                'steps_count': tutorial['steps_count']
            }
            for tutorial in self.tutorials.values()
        ]
    
    def start_tutorial(self, tutorial_id: str) -> bool:
        """
        Inicia un tutorial específico
        
        Args:
            tutorial_id: ID del tutorial a iniciar
            
        Returns:
            bool: True si se inició correctamente
        """
        if tutorial_id in self.tutorials:
            self.current_tutorial = tutorial_id
            self.current_step = 0
            return True
        return False
    
    def get_current_tutorial_info(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del paso actual del tutorial
        
        Returns:
            Dict con información del paso actual o None
        """
        if not self.current_tutorial or self.current_tutorial not in self.tutorials:
            return None
        
        tutorial = self.tutorials[self.current_tutorial]
        if self.current_step >= len(tutorial['steps']):
            return None
        
        current_step_data = tutorial['steps'][self.current_step]
        
        return {
            'tutorial_id': self.current_tutorial,
            'tutorial_title': tutorial['title'],
            'step_number': self.current_step + 1,
            'total_steps': len(tutorial['steps']),
            'step_title': current_step_data['title'],
            'step_content': current_step_data['content'],
            'code_example': current_step_data.get('code_example'),
            'expected_output': current_step_data.get('expected_output'),
            'hints': current_step_data.get('hints', []),
            'progress': (self.current_step + 1) / len(tutorial['steps'])
        }
    
    def next_tutorial_step(self) -> bool:
        """
        Avanza al siguiente paso del tutorial
        
        Returns:
            bool: True si hay siguiente paso, False si terminó
        """
        if not self.current_tutorial:
            return False
        
        tutorial = self.tutorials[self.current_tutorial]
        if self.current_step < len(tutorial['steps']) - 1:
            self.current_step += 1
            return True
        return False
    
    def previous_tutorial_step(self) -> bool:
        """
        Retrocede al paso anterior del tutorial
        
        Returns:
            bool: True si hay paso anterior, False si está en el primero
        """
        if not self.current_tutorial:
            return False
        
        if self.current_step > 0:
            self.current_step -= 1
            return True
        return False
    
    def validate_step_code(self, code: str) -> Dict[str, Any]:
        """
        Valida el código del usuario para el paso actual
        
        Args:
            code: Código escrito por el usuario
            
        Returns:
            Dict con resultado de validación
        """
        if not self.current_tutorial:
            return {'valid': False, 'message': 'No hay tutorial activo'}
        
        # Usar validación personalizada desde la configuración
        return validate_tutorial_code(self.current_tutorial, self.current_step, code)
    
    def get_tutorial_progress(self) -> Dict[str, Any]:
        """
        Obtiene el progreso actual del tutorial
        
        Returns:
            Dict con información de progreso
        """
        if not self.current_tutorial:
            return {'active': False}
        
        tutorial = self.tutorials[self.current_tutorial]
        return {
            'active': True,
            'tutorial_id': self.current_tutorial,
            'tutorial_title': tutorial['title'],
            'current_step': self.current_step + 1,
            'total_steps': len(tutorial['steps']),
            'progress_percent': int(((self.current_step + 1) / len(tutorial['steps'])) * 100),
            'completed': self.current_step >= len(tutorial['steps']) - 1
        }


# Instancia global del gestor
_tutorial_manager = None

def get_tutorial_manager() -> TutorialManager:
    """
    Obtiene la instancia global del gestor de tutoriales
    
    Returns:
        TutorialManager: Instancia del gestor
    """
    global _tutorial_manager
    if _tutorial_manager is None:
        _tutorial_manager = TutorialManager()
    return _tutorial_manager
