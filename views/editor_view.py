"""
Vista: Interfaz gráfica del editor de código Python usando PySide6
"""
import sys
import os
import shutil
import keyword
import builtins
import ast
import re
import fnmatch
from pathlib import Path

# Importar el nuevo terminal
from new_terminal import IntegratedTerminalNew

from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                               QWidget, QPushButton, QLabel, QTextEdit, QMessageBox,
                               QSplitter, QFrame, QMenuBar, QFileDialog, QDialog, QPlainTextEdit,
                               QComboBox, QSpinBox, QColorDialog, QGridLayout, QGroupBox, QTabWidget,
                               QSystemTrayIcon, QMenu, QListWidget, QListWidgetItem, QTreeWidget,
                               QTreeWidgetItem, QInputDialog, QAbstractItemView, QTabBar, QToolTip,
                               QLineEdit, QCheckBox, QScrollArea)
from PySide6.QtCore import Qt, QTimer, QUrl, QRect, QSettings, QPoint, QThread, Signal, QProcess
from PySide6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter, QTextDocument, QAction, QPixmap, QDesktopServices, QPainter, QFontDatabase, QIcon, QKeyEvent, QTextCursor
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import NullFormatter
from pygments.token import Token
from config import AppConfig
from .documentation_dialog import DocumentationDialog


class CustomSyntaxError:
    """Clase para representar un error de sintaxis"""
    def __init__(self, line_number, column, message, error_type="error", suggestion=None):
        self.line_number = line_number
        self.column = column
        self.message = message
        self.error_type = error_type  # "error", "warning", "info"
        self.suggestion = suggestion


class SyntaxChecker(QThread):
    """Verificador de sintaxis que se ejecuta en un hilo separado"""
    
    errors_found = Signal(list)  # Señal que emite la lista de errores encontrados
    
    def __init__(self):
        super().__init__()
        self.code_to_check = ""
        self.should_check = False
        
    def set_code(self, code):
        """Establece el código a verificar"""
        self.code_to_check = code
        self.should_check = True
        
    def run(self):
        """Ejecuta la verificación de sintaxis"""
        if not self.should_check:
            return
            
        errors = []
        
        try:
            # Verificar sintaxis básica con AST
            ast.parse(self.code_to_check)
        except SyntaxError as e:
            errors.append(CustomSyntaxError(
                line_number=e.lineno or 1,
                column=e.offset or 0,
                message=f"Error de sintaxis: {e.msg}",
                error_type="error",
                suggestion=self._get_syntax_suggestion(e.msg)
            ))
        except Exception as e:
            errors.append(CustomSyntaxError(
                line_number=1,
                column=0,
                message=f"Error inesperado: {str(e)}",
                error_type="error"
            ))
        
        # Verificar variables no utilizadas
        unused_vars = self._find_unused_variables()
        for var_info in unused_vars:
            errors.append(CustomSyntaxError(
                line_number=var_info['line'],
                column=var_info['column'],
                message=f"Variable '{var_info['name']}' definida pero no utilizada",
                error_type="warning",
                suggestion=f"Considera eliminar la variable '{var_info['name']}' o usarla en tu código"
            ))
        
        # Verificar imports no utilizados
        unused_imports = self._find_unused_imports()
        for import_info in unused_imports:
            errors.append(CustomSyntaxError(
                line_number=import_info['line'],
                column=0,
                message=f"Import '{import_info['name']}' no utilizado",
                error_type="warning",
                suggestion=f"Considera eliminar 'import {import_info['name']}' si no lo necesitas"
            ))
        
        # Verificar problemas comunes
        common_issues = self._find_common_issues()
        errors.extend(common_issues)
        
        self.errors_found.emit(errors)
        self.should_check = False
    
    def _get_syntax_suggestion(self, error_msg):
        """Genera sugerencias para errores de sintaxis comunes"""
        suggestions = {
            "invalid syntax": "Verifica que todos los paréntesis, corchetes y llaves estén balanceados",
            "unexpected EOF": "Falta cerrar paréntesis, corchetes, llaves o comillas",
            "unmatched": "Verifica que todos los símbolos de apertura tengan su correspondiente cierre",
            "invalid character": "Hay un carácter no válido en el código",
            "unexpected indent": "Problema de indentación - verifica que uses 4 espacios consistentemente",
            "unindent does not match": "La indentación no coincide con niveles anteriores",
            "expected ':'": "Falta ':' al final de if, for, while, def, class, etc.",
            "invalid decimal literal": "Error en número decimal - usa punto (.) no coma (,)"
        }
        
        for key, suggestion in suggestions.items():
            if key in error_msg.lower():
                return suggestion
        
        return "Revisa la sintaxis en esta línea"
    
    def _find_unused_variables(self):
        """Encuentra variables definidas pero no utilizadas"""
        unused_vars = []
        
        try:
            tree = ast.parse(self.code_to_check)
            
            # Encontrar todas las asignaciones de variables
            assignments = {}
            usages = set()
            
            for node in ast.walk(tree):
                # Buscar asignaciones
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            assignments[target.id] = {
                                'line': node.lineno,
                                'column': node.col_offset,
                                'name': target.id
                            }
                elif isinstance(node, ast.AnnAssign) and node.target:
                    if isinstance(node.target, ast.Name):
                        assignments[node.target.id] = {
                            'line': node.lineno,
                            'column': node.col_offset,
                            'name': node.target.id
                        }
                
                # Buscar usos de variables
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    usages.add(node.id)
            
            # Encontrar variables no utilizadas (excluyendo algunas especiales)
            special_vars = {'_', '__name__', '__file__', '__doc__'}
            for var_name, var_info in assignments.items():
                if var_name not in usages and var_name not in special_vars:
                    unused_vars.append(var_info)
                    
        except:
            pass  # Si hay error en AST, no verificar variables no utilizadas
        
        return unused_vars
    
    def _find_unused_imports(self):
        """Encuentra imports no utilizados"""
        unused_imports = []
        
        try:
            tree = ast.parse(self.code_to_check)
            
            imports = {}
            usages = set()
            
            for node in ast.walk(tree):
                # Buscar imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports[name] = {
                            'line': node.lineno,
                            'name': alias.name
                        }
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports[name] = {
                            'line': node.lineno,
                            'name': alias.name
                        }
                
                # Buscar usos
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    usages.add(node.id)
                elif isinstance(node, ast.Attribute):
                    # Para casos como 'os.path'
                    if isinstance(node.value, ast.Name):
                        usages.add(node.value.id)
            
            # Encontrar imports no utilizados
            for import_name, import_info in imports.items():
                if import_name not in usages:
                    unused_imports.append(import_info)
                    
        except:
            pass
        
        return unused_imports
    
    def _find_common_issues(self):
        """Encuentra problemas comunes en el código"""
        issues = []
        lines = self.code_to_check.split('\n')
        
        for i, line in enumerate(lines):
            line_num = i + 1
            stripped_line = line.strip()
            
            # Verificar líneas muy largas (PEP 8)
            if len(line) > 120:
                issues.append(CustomSyntaxError(
                    line_number=line_num,
                    column=120,
                    message="Línea demasiado larga (>120 caracteres)",
                    error_type="info",
                    suggestion="Considera dividir esta línea para mejorar la legibilidad"
                ))
            
            # Verificar múltiples espacios consecutivos
            if '  ' in stripped_line and not stripped_line.startswith('#'):
                issues.append(CustomSyntaxError(
                    line_number=line_num,
                    column=line.find('  '),
                    message="Múltiples espacios consecutivos",
                    error_type="info",
                    suggestion="Usa un solo espacio entre elementos"
                ))
            
            # Verificar comparaciones con True/False/None
            if re.search(r'==\s*(True|False|None)', stripped_line):
                issues.append(CustomSyntaxError(
                    line_number=line_num,
                    column=0,
                    message="Comparación explícita con True/False/None",
                    error_type="info",
                    suggestion="Usa 'if variable:' en lugar de 'if variable == True:'"
                ))
            
            # Verificar funciones sin docstring
            if stripped_line.startswith('def ') and ':' in stripped_line:
                # Verificar si la siguiente línea no vacía es un docstring
                next_line_idx = i + 1
                while next_line_idx < len(lines) and not lines[next_line_idx].strip():
                    next_line_idx += 1
                
                if (next_line_idx < len(lines) and 
                    not lines[next_line_idx].strip().startswith('"""') and
                    not lines[next_line_idx].strip().startswith("'''")):
                    issues.append(CustomSyntaxError(
                        line_number=line_num,
                        column=0,
                        message="Función sin docstring",
                        error_type="info",
                        suggestion="Considera agregar un docstring para documentar esta función"
                    ))
        
        return issues


class AboutDialog(QDialog):
    """Ventana de información sobre la aplicación"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Acerca de - Ejecútalo! - Un editor básico de Python")
        self.setFixedSize(450, 600)  # Aumentado la altura para acomodar el scroll
        self.setModal(True)
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz de la ventana About"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Logo
        logo_label = QLabel()
        try:
            pixmap = QPixmap("img/logo.png")
            if pixmap.isNull():
                # Si no se puede cargar la imagen, usar texto
                logo_label.setText("🐍 PYTHON EDITOR")
                logo_label.setStyleSheet("""
                    QLabel {
                        font-size: 24px;
                        font-weight: bold;
                        color: #3498DB;
                        background-color: #2C3E50;
                        border-radius: 10px;
                        padding: 20px;
                        border: 2px solid #34495E;
                    }
                """)
            else:
                # Escalar la imagen manteniendo proporciones
                scaled_pixmap = pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
        except Exception:
            # Fallback si hay error cargando la imagen
            logo_label.setText("🐍 PYTHON EDITOR")
            logo_label.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    font-weight: bold;
                    color: #3498DB;
                    background-color: #2C3E50;
                    border-radius: 10px;
                    padding: 20px;
                    border: 2px solid #34495E;
                }
            """)
        
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        
        # Título
        title_label = QLabel("Editor de Código Python")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2C3E50;
                margin: 10px 0;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Versión
        version_label = QLabel("Versión 2.0 - MVC con PySide6")
        version_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7F8C8D;
                margin-bottom: 15px;
            }
        """)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        # Descripción con scroll
        description_scroll = QScrollArea()
        description_scroll.setWidgetResizable(True)
        description_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        description_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        description_scroll.setFixedHeight(250)  # Aumentado para mejor visualización
        description_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #BDC3C7;
                border-radius: 5px;
                background-color: #FAFAFA;
            }
        """)
        
        description = QLabel("""
<b>🎯 ¿Qué hace este programa?</b><br><br>
Este editor de código Python ofrece un entorno completo para escribir, 
editar y ejecutar código Python con las siguientes características:<br><br>

• <b>🎨 Resaltado de sintaxis avanzado</b> con Pygments<br>
• <b>🔧 Indentación automática inteligente</b> (4 espacios)<br>
• <b>📁 Gestión completa de archivos</b> (Abrir, Guardar, Guardar Como)<br>
• <b>⚡ Ejecución de código en tiempo real</b><br>
• <b>🏗️ Arquitectura MVC profesional</b><br>
• <b>⌨️ Atajos de teclado intuitivos</b><br>
• <b>🛡️ Manejo seguro de archivos</b> con confirmaciones<br>
• <b>🔍 Búsqueda y reemplazo avanzado</b> (Ctrl+F, Ctrl+H)<br>
• <b>🔎 Búsqueda en múltiples archivos</b> (Ctrl+Shift+F)<br>
• <b>🎯 Soporte para expresiones regulares</b><br>
• <b>🎨 Sistema de temas personalizable</b><br>
• <b>⚙️ Configuración de fuentes y colores</b><br>
• <b>📝 Numeración de líneas</b><br>
• <b>🔧 Formateo automático de código</b> (Ctrl+Alt+F)<br>
• <b>🚀 Ejecución de código</b> (Ctrl+Enter)<br>
• <b>💻 Ejecución en terminal integrado</b> (Ctrl+Shift+Enter)<br><br>

Ideal para aprender Python, desarrollar scripts, prototipar ideas 
y trabajar en proyectos pequeños y medianos.
        """)
        description.setWordWrap(True)
        description.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #34495E;
                background-color: transparent;
                padding: 15px;
                line-height: 1.4;
            }
        """)
        
        description_scroll.setWidget(description)
        layout.addWidget(description_scroll)
        
        # Espacio entre el scroll y los botones
        layout.addSpacing(15)
        
        # Layout horizontal para los botones
        buttons_layout = QHBoxLayout()
        
        # Botón para GitHub
        github_button = QPushButton("🌐 Visitar GitHub")
        github_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 10px 15px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5DADE2;
            }
            QPushButton:pressed {
                background-color: #2E86AB;
            }
        """)
        github_button.clicked.connect(self._open_github)
        buttons_layout.addWidget(github_button)
        
        # Botón Cerrar
        close_button = QPushButton("Cerrar")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #B2BABB;
            }
        """)
        close_button.clicked.connect(self.close)
        buttons_layout.addWidget(close_button)
        
        # Agregar el layout de botones al layout principal
        layout.addLayout(buttons_layout)
    
    def _open_github(self):
        """Abre el enlace de GitHub en el navegador predeterminado"""
        try:
            url = QUrl("https://github.com/sapoclay/ejecutate")
            QDesktopServices.openUrl(url)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo abrir el enlace:\n{str(e)}")
    
    def keyPressEvent(self, event):
        """Maneja eventos de teclado para cerrar con ESC"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()  # Cierra el diálogo
        else:
            super().keyPressEvent(event)


class SearchReplaceDialog(QDialog):
    """Diálogo para búsqueda y reemplazo avanzado"""
    
    def __init__(self, parent=None, search_mode="find"):
        super().__init__(parent)
        self.parent_editor = parent
        self.search_mode = search_mode  # "find" o "replace"
        self.current_matches = []
        self.current_match_index = -1
        
        self.setWindowTitle("Buscar y Reemplazar" if search_mode == "replace" else "Buscar")
        self.setFixedSize(600, 450 if search_mode == "replace" else 350)
        self.setModal(False)  # No modal para permitir editar mientras se busca
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Configurar la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        
        # Área de búsqueda
        search_group = QGroupBox("🔍 Buscar")
        search_group.setMinimumWidth(120)
        search_layout = QVBoxLayout(search_group)
        
        # Campo de búsqueda
        search_field_layout = QHBoxLayout()
        search_label = QLabel("Buscar:")
        search_label.setMinimumWidth(80)
        search_field_layout.addWidget(search_label)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ingresa el texto a buscar...")
        search_field_layout.addWidget(self.search_input)
        search_layout.addLayout(search_field_layout)
        
        # Área de reemplazo (solo si es modo replace)
        if self.search_mode == "replace":
            replace_field_layout = QHBoxLayout()
            replace_label = QLabel("Reemplazar:")
            replace_label.setMinimumWidth(80)
            replace_field_layout.addWidget(replace_label)
            self.replace_input = QLineEdit()
            self.replace_input.setPlaceholderText("Ingresa el texto de reemplazo...")
            replace_field_layout.addWidget(self.replace_input)
            search_layout.addLayout(replace_field_layout)
        
        layout.addWidget(search_group)
        
        # Opciones de búsqueda
        options_group = QGroupBox("⚙️ Opciones")
        options_group.setMinimumWidth(150)
        options_layout = QGridLayout(options_group)
        
        self.case_sensitive_cb = QCheckBox("Distinguir mayúsculas/minúsculas")
        self.whole_words_cb = QCheckBox("Solo palabras completas")
        self.regex_cb = QCheckBox("Expresiones regulares")
        self.wrap_around_cb = QCheckBox("Buscar desde el inicio al llegar al final")
        self.wrap_around_cb.setChecked(True)
        
        options_layout.addWidget(self.case_sensitive_cb, 0, 0)
        options_layout.addWidget(self.whole_words_cb, 0, 1)
        options_layout.addWidget(self.regex_cb, 1, 0)
        options_layout.addWidget(self.wrap_around_cb, 1, 1)
        
        layout.addWidget(options_group)
        
        # Área de resultados
        results_group = QGroupBox("📊 Resultados")
        results_group.setMinimumWidth(140)
        results_layout = QVBoxLayout(results_group)
        
        self.results_label = QLabel("Sin resultados")
        results_layout.addWidget(self.results_label)
        
        layout.addWidget(results_group)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.find_prev_btn = QPushButton("⬆️ Anterior")
        self.find_next_btn = QPushButton("⬇️ Siguiente")
        self.highlight_all_btn = QPushButton("🎯 Resaltar Todo")
        
        buttons_layout.addWidget(self.find_prev_btn)
        buttons_layout.addWidget(self.find_next_btn)
        buttons_layout.addWidget(self.highlight_all_btn)
        
        if self.search_mode == "replace":
            self.replace_btn = QPushButton("🔄 Reemplazar")
            self.replace_all_btn = QPushButton("🔄 Reemplazar Todo")
            buttons_layout.addWidget(self.replace_btn)
            buttons_layout.addWidget(self.replace_all_btn)
        
        self.close_btn = QPushButton("❌ Cerrar")
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
        
        # Configurar foco inicial
        self.search_input.setFocus()
        
    def _connect_signals(self):
        """Conectar señales de los controles"""
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.find_next_btn.clicked.connect(self._find_next)
        self.find_prev_btn.clicked.connect(self._find_previous)
        self.highlight_all_btn.clicked.connect(self._highlight_all)
        self.close_btn.clicked.connect(self.close)
        
        # Opciones
        self.case_sensitive_cb.toggled.connect(self._on_options_changed)
        self.whole_words_cb.toggled.connect(self._on_options_changed)
        self.regex_cb.toggled.connect(self._on_options_changed)
        self.wrap_around_cb.toggled.connect(self._on_options_changed)
        
        # Eventos de teclado
        self.search_input.returnPressed.connect(self._find_next)
        
        if self.search_mode == "replace":
            self.replace_input.returnPressed.connect(self._replace_current)
            self.replace_btn.clicked.connect(self._replace_current)
            self.replace_all_btn.clicked.connect(self._replace_all)
    
    def _on_search_text_changed(self):
        """Manejar cambios en el texto de búsqueda"""
        search_text = self.search_input.text()
        if search_text:
            self._perform_search()
        else:
            self._clear_search()
    
    def _on_options_changed(self):
        """Manejar cambios en las opciones de búsqueda"""
        if self.search_input.text():
            self._perform_search()
    
    def _perform_search(self):
        """Realizar la búsqueda"""
        if not self.parent_editor or not hasattr(self.parent_editor, 'input_text'):
            return
            
        search_text = self.search_input.text()
        if not search_text:
            return
            
        editor = self.parent_editor.input_text
        if not editor:
            return
            
        document_text = editor.toPlainText()
        self.current_matches = []
        
        try:
            # Configurar opciones de búsqueda
            flags = 0
            if not self.case_sensitive_cb.isChecked():
                flags |= re.IGNORECASE
                
            # Preparar patrón de búsqueda
            if self.regex_cb.isChecked():
                pattern = search_text
            else:
                pattern = re.escape(search_text)
                
            if self.whole_words_cb.isChecked():
                pattern = r'\b' + pattern + r'\b'
            
            # Buscar todas las coincidencias
            for match in re.finditer(pattern, document_text, flags):
                self.current_matches.append((match.start(), match.end()))
            
            # Actualizar resultados
            if self.current_matches:
                self.results_label.setText(f"Encontradas {len(self.current_matches)} coincidencias")
                self.current_match_index = 0
                self._highlight_current_match()
            else:
                self.results_label.setText("Sin coincidencias")
                self.current_match_index = -1
                
        except re.error as e:
            self.results_label.setText(f"Error en expresión regular: {str(e)}")
            self.current_matches = []
            self.current_match_index = -1
    
    def _find_next(self):
        """Buscar siguiente coincidencia"""
        if not self.current_matches:
            return
            
        self.current_match_index = (self.current_match_index + 1) % len(self.current_matches)
        self._highlight_current_match()
        self._update_results_label()
    
    def _find_previous(self):
        """Buscar coincidencia anterior"""
        if not self.current_matches:
            return
            
        self.current_match_index = (self.current_match_index - 1) % len(self.current_matches)
        self._highlight_current_match()
        self._update_results_label()
    
    def _highlight_current_match(self):
        """Resaltar la coincidencia actual"""
        if (not self.current_matches or 
            self.current_match_index < 0 or 
            self.current_match_index >= len(self.current_matches)):
            return
            
        editor = self.parent_editor.input_text
        if not editor:
            return
            
        start, end = self.current_matches[self.current_match_index]
        
        # Mover cursor a la coincidencia
        cursor = editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, cursor.KeepAnchor)
        editor.setTextCursor(cursor)
        
        # Asegurar que sea visible
        editor.ensureCursorVisible()
    
    def _highlight_all(self):
        """Resaltar todas las coincidencias"""
        # Esta funcionalidad se puede implementar usando QTextCharFormat
        # Por simplicidad, mostraremos un mensaje
        if self.current_matches:
            QMessageBox.information(self, "Resaltar Todo", 
                                  f"Se encontraron {len(self.current_matches)} coincidencias.\n"
                                  "Use 'Siguiente/Anterior' para navegar entre ellas.")
    
    def _replace_current(self):
        """Reemplazar la coincidencia actual"""
        if (not self.current_matches or 
            self.current_match_index < 0 or 
            self.current_match_index >= len(self.current_matches)):
            return
            
        editor = self.parent_editor.input_text
        if not editor:
            return
            
        replace_text = self.replace_input.text()
        start, end = self.current_matches[self.current_match_index]
        
        # Realizar reemplazo
        cursor = editor.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, cursor.KeepAnchor)
        cursor.insertText(replace_text)
        
        # Actualizar posiciones de las coincidencias
        diff = len(replace_text) - (end - start)
        for i in range(len(self.current_matches)):
            if i > self.current_match_index:
                old_start, old_end = self.current_matches[i]
                self.current_matches[i] = (old_start + diff, old_end + diff)
        
        # Remover la coincidencia reemplazada
        self.current_matches.pop(self.current_match_index)
        
        if self.current_matches:
            if self.current_match_index >= len(self.current_matches):
                self.current_match_index = 0
            self._highlight_current_match()
            self._update_results_label()
        else:
            self.results_label.setText("Todas las coincidencias han sido reemplazadas")
            self.current_match_index = -1
    
    def _replace_all(self):
        """Reemplazar todas las coincidencias"""
        if not self.current_matches:
            return
            
        editor = self.parent_editor.input_text
        if not editor:
            return
            
        replace_text = self.replace_input.text()
        count = len(self.current_matches)
        
        # Confirmar reemplazo múltiple
        reply = QMessageBox.question(self, "Reemplazar Todo",
                                   f"¿Está seguro de reemplazar {count} coincidencias?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        # Realizar reemplazos desde el final hacia el principio para mantener posiciones
        for start, end in reversed(self.current_matches):
            cursor = editor.textCursor()
            cursor.setPosition(start)
            cursor.setPosition(end, cursor.KeepAnchor)
            cursor.insertText(replace_text)
        
        self.current_matches = []
        self.current_match_index = -1
        self.results_label.setText(f"Se reemplazaron {count} coincidencias")
    
    def _update_results_label(self):
        """Actualizar etiqueta de resultados"""
        if self.current_matches:
            self.results_label.setText(
                f"Coincidencia {self.current_match_index + 1} de {len(self.current_matches)}"
            )
    
    def _clear_search(self):
        """Limpiar búsqueda actual"""
        self.current_matches = []
        self.current_match_index = -1
        self.results_label.setText("Sin resultados")
    
    def set_search_text(self, text):
        """Establecer texto de búsqueda desde el exterior"""
        self.search_input.setText(text)
        self.search_input.selectAll()
    
    def keyPressEvent(self, event):
        """Manejar eventos de teclado"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_F3:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._find_previous()
            else:
                self._find_next()
        else:
            super().keyPressEvent(event)


class MultiFileSearchDialog(QDialog):
    """Diálogo para búsqueda en múltiples archivos"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_editor = parent
        self.setWindowTitle("Buscar en Múltiples Archivos")
        self.setFixedSize(800, 600)
        self.setModal(False)
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Configurar la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        
        # Área de búsqueda
        search_group = QGroupBox("🔍 Búsqueda")
        search_group.setMinimumWidth(120)
        search_layout = QVBoxLayout(search_group)
        
        # Campo de búsqueda
        search_field_layout = QHBoxLayout()
        search_label = QLabel("Buscar:")
        search_label.setMinimumWidth(80)
        search_field_layout.addWidget(search_label)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ingresa el texto a buscar...")
        search_field_layout.addWidget(self.search_input)
        search_layout.addLayout(search_field_layout)
        
        # Directorio de búsqueda
        dir_layout = QHBoxLayout()
        dir_label = QLabel("Directorio:")
        dir_label.setMinimumWidth(80)
        dir_layout.addWidget(dir_label)
        self.dir_input = QLineEdit()
        self.dir_input.setText(os.getcwd())
        dir_layout.addWidget(self.dir_input)
        self.browse_btn = QPushButton("📁 Explorar")
        dir_layout.addWidget(self.browse_btn)
        search_layout.addLayout(dir_layout)
        
        # Patrones de archivo
        patterns_layout = QHBoxLayout()
        patterns_label = QLabel("Archivos:")
        patterns_label.setMinimumWidth(80)
        patterns_layout.addWidget(patterns_label)
        self.patterns_input = QLineEdit()
        self.patterns_input.setText("*.py;*.txt;*.md")
        self.patterns_input.setPlaceholderText("*.py;*.txt;*.md")
        patterns_layout.addWidget(self.patterns_input)
        search_layout.addLayout(patterns_layout)
        
        layout.addWidget(search_group)
        
        # Opciones
        options_group = QGroupBox("⚙️ Opciones")
        options_group.setMinimumWidth(150)
        options_layout = QGridLayout(options_group)
        
        self.case_sensitive_cb = QCheckBox("Distinguir mayúsculas/minúsculas")
        self.whole_words_cb = QCheckBox("Solo palabras completas")
        self.regex_cb = QCheckBox("Expresiones regulares")
        self.include_subdirs_cb = QCheckBox("Incluir subdirectorios")
        self.include_subdirs_cb.setChecked(True)
        
        options_layout.addWidget(self.case_sensitive_cb, 0, 0)
        options_layout.addWidget(self.whole_words_cb, 0, 1)
        options_layout.addWidget(self.regex_cb, 1, 0)
        options_layout.addWidget(self.include_subdirs_cb, 1, 1)
        
        layout.addWidget(options_group)
        
        # Resultados
        results_group = QGroupBox("📊 Resultados")
        results_group.setMinimumWidth(140)
        results_layout = QVBoxLayout(results_group)
        
        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["Archivo", "Línea", "Contenido"])
        self.results_tree.setColumnWidth(0, 200)
        self.results_tree.setColumnWidth(1, 60)
        results_layout.addWidget(self.results_tree)
        
        self.results_status = QLabel("Listo para buscar")
        results_layout.addWidget(self.results_status)
        
        layout.addWidget(results_group)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        self.search_btn = QPushButton("🔍 Buscar")
        self.clear_btn = QPushButton("🗑️ Limpiar")
        self.close_btn = QPushButton("❌ Cerrar")
        
        buttons_layout.addWidget(self.search_btn)
        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.close_btn)
        
        layout.addLayout(buttons_layout)
        
    def _connect_signals(self):
        """Conectar señales"""
        self.search_btn.clicked.connect(self._perform_search)
        self.clear_btn.clicked.connect(self._clear_results)
        self.close_btn.clicked.connect(self.close)
        self.browse_btn.clicked.connect(self._browse_directory)
        self.results_tree.itemDoubleClicked.connect(self._open_result)
        self.search_input.returnPressed.connect(self._perform_search)
        
    def _browse_directory(self):
        """Explorar directorio"""
        directory = QFileDialog.getExistingDirectory(
            self, "Seleccionar Directorio", self.dir_input.text()
        )
        if directory:
            self.dir_input.setText(directory)
    
    def _perform_search(self):
        """Realizar búsqueda en múltiples archivos"""
        search_text = self.search_input.text()
        if not search_text:
            QMessageBox.warning(self, "Advertencia", "Ingrese un texto para buscar")
            return
            
        search_dir = self.dir_input.text()
        if not os.path.exists(search_dir):
            QMessageBox.warning(self, "Advertencia", "El directorio no existe")
            return
        
        # Limpiar resultados anteriores
        self.results_tree.clear()
        self.results_status.setText("Buscando...")
        QApplication.processEvents()
        
        try:
            # Configurar opciones
            flags = 0
            if not self.case_sensitive_cb.isChecked():
                flags |= re.IGNORECASE
                
            # Preparar patrón
            if self.regex_cb.isChecked():
                pattern = search_text
            else:
                pattern = re.escape(search_text)
                
            if self.whole_words_cb.isChecked():
                pattern = r'\b' + pattern + r'\b'
            
            # Obtener patrones de archivo
            file_patterns = [p.strip() for p in self.patterns_input.text().split(';') if p.strip()]
            if not file_patterns:
                file_patterns = ['*']
            
            total_matches = 0
            files_searched = 0
            
            # Buscar archivos
            for root, dirs, files in os.walk(search_dir):
                if not self.include_subdirs_cb.isChecked() and root != search_dir:
                    break
                    
                for file in files:
                    # Verificar si el archivo coincide con los patrones
                    if not any(fnmatch.fnmatch(file, pattern) for pattern in file_patterns):
                        continue
                        
                    file_path = os.path.join(root, file)
                    files_searched += 1
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                matches = list(re.finditer(pattern, line, flags))
                                for match in matches:
                                    # Crear elemento en el árbol
                                    item = QTreeWidgetItem()
                                    item.setText(0, os.path.relpath(file_path, search_dir))
                                    item.setText(1, str(line_num))
                                    item.setText(2, line.strip()[:100] + "..." if len(line.strip()) > 100 else line.strip())
                                    item.setData(0, Qt.ItemDataRole.UserRole, file_path)
                                    item.setData(1, Qt.ItemDataRole.UserRole, line_num)
                                    self.results_tree.addTopLevelItem(item)
                                    total_matches += 1
                                    
                    except Exception as e:
                        continue  # Saltar archivos que no se pueden leer
            
            self.results_status.setText(
                f"Búsqueda completada: {total_matches} coincidencias en {files_searched} archivos"
            )
            
        except re.error as e:
            self.results_status.setText(f"Error en expresión regular: {str(e)}")
        except Exception as e:
            self.results_status.setText(f"Error durante la búsqueda: {str(e)}")
    
    def _clear_results(self):
        """Limpiar resultados"""
        self.results_tree.clear()
        self.results_status.setText("Listo para buscar")
    
    def _open_result(self, item):
        """Abrir archivo y navegar a la línea"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        line_num = item.data(1, Qt.ItemDataRole.UserRole)
        
        if file_path and self.parent_editor:
            # Abrir archivo en el editor
            self.parent_editor.open_file(file_path)
            
            # Navegar a la línea específica
            if hasattr(self.parent_editor, 'input_text') and self.parent_editor.input_text:
                editor = self.parent_editor.input_text
                cursor = editor.textCursor()
                cursor.movePosition(cursor.Start)
                for _ in range(line_num - 1):
                    cursor.movePosition(cursor.Down)
                editor.setTextCursor(cursor)
                editor.ensureCursorVisible()


class PreferencesDialog(QDialog):
    """Ventana de preferencias para personalizar el editor"""
    
    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.parent_editor = parent
        self.setWindowTitle("Preferencias - Editor de Código Python")
        self.setFixedSize(600, 750)  # Aumentado el ancho y altura para la pestaña del formatter
        self.setModal(True)
        
        # Configuraciones actuales
        self.current_settings = current_settings or self._get_default_settings()
        self.new_settings = self.current_settings.copy()
        
        self._setup_ui()
    
    def _get_default_settings(self):
        """Configuraciones por defecto"""
        from config import AppConfig
        
        # Obtener configuraciones del tema por defecto
        default_theme = AppConfig.DEFAULT_THEME
        theme_settings = AppConfig.THEMES[default_theme].copy()
        theme_settings['current_theme'] = default_theme
        
        # Añadir configuraciones del formatter por defecto
        theme_settings.update({
            'formatter_enabled': AppConfig.FORMATTER_ENABLED,
            'formatter_auto_save': AppConfig.FORMATTER_AUTO_FORMAT_ON_SAVE,
            'formatter_engine_index': 1,  # autopep8 por defecto
            'formatter_line_length': AppConfig.FORMATTER_MAX_LINE_LENGTH,
            'formatter_indent_size': AppConfig.FORMATTER_INDENT_SIZE,
            'formatter_use_tabs': AppConfig.FORMATTER_USE_TABS,
            'formatter_organize_imports': AppConfig.FORMATTER_ORGANIZE_IMPORTS,
            'formatter_remove_trailing': AppConfig.FORMATTER_REMOVE_TRAILING_WHITESPACE,
            'formatter_final_newline': AppConfig.FORMATTER_ADD_FINAL_NEWLINE,
            'formatter_auto_spacing': AppConfig.FORMATTER_AUTO_SPACING
        })
        
        return theme_settings
    
    def _create_themes_tab(self):
        """Crea el tab de selección de temas"""
        from config import AppConfig
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo de selección de tema
        theme_group = QGroupBox("🎭 Seleccionar Tema")
        theme_group.setMinimumWidth(400)
        theme_layout = QVBoxLayout(theme_group)
        
        # ComboBox para seleccionar tema
        self.theme_combo = QComboBox()
        
        # Agregar temas disponibles
        available_themes = list(AppConfig.THEMES.keys())
        for theme_name in available_themes:
            self.theme_combo.addItem(theme_name)
        
        # Establecer tema actual
        current_theme = self.current_settings.get('current_theme', AppConfig.DEFAULT_THEME)
        if current_theme in available_themes:
            self.theme_combo.setCurrentText(current_theme)
        
        # Conectar cambio de tema
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        
        theme_layout.addWidget(QLabel("Tema:"))
        theme_layout.addWidget(self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # Vista previa del tema
        preview_group = QGroupBox("👁️ Vista Previa del Tema")
        preview_group.setMinimumWidth(400)
        preview_layout = QVBoxLayout(preview_group)
        
        # Crear una vista previa visual
        self.theme_preview = QLabel()
        self.theme_preview.setFixedHeight(200)
        self.theme_preview.setStyleSheet("""
            QLabel {
                border: 2px solid #BDC3C7;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        preview_layout.addWidget(self.theme_preview)
        layout.addWidget(preview_group)
        
        # Información del tema
        info_group = QGroupBox("ℹ️ Información del Tema")
        info_group.setMinimumWidth(400)
        info_layout = QVBoxLayout(info_group)
        
        self.theme_info = QLabel()
        self.theme_info.setWordWrap(True)
        self.theme_info.setStyleSheet("""
            QLabel {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 3px;
                padding: 10px;
                font-size: 11px;
            }
        """)
        
        info_layout.addWidget(self.theme_info)
        layout.addWidget(info_group)
        
        # Actualizar vista previa inicial
        self._update_theme_preview()
        
        layout.addStretch()
        return widget
    
    def _on_theme_changed(self, theme_name):
        """Maneja el cambio de tema"""
        from config import AppConfig
        
        if theme_name in AppConfig.THEMES:
            # Actualizar configuraciones con el tema seleccionado
            theme_settings = AppConfig.THEMES[theme_name].copy()
            theme_settings['current_theme'] = theme_name
            
            # Actualizar new_settings
            for key, value in theme_settings.items():
                self.new_settings[key] = value
            
            # Actualizar otros controles del diálogo
            self._update_controls_from_theme(theme_settings)
            
            # Actualizar vista previa
            self._update_theme_preview()
            
            # Aplicar vista previa automáticamente
            self._apply_preview()
    
    def _update_controls_from_theme(self, theme_settings):
        """Actualiza los controles del diálogo con los valores del tema"""
        # Actualizar controles del tab Editor
        if hasattr(self, 'editor_font_combo'):
            self.editor_font_combo.setCurrentText(theme_settings['editor_font_family'])
        if hasattr(self, 'editor_font_size'):
            self.editor_font_size.setValue(theme_settings['editor_font_size'])
        
        # Actualizar controles del tab Salida
        if hasattr(self, 'output_font_combo'):
            self.output_font_combo.setCurrentText(theme_settings['output_font_family'])
        if hasattr(self, 'output_font_size'):
            self.output_font_size.setValue(theme_settings['output_font_size'])
        
        # Actualizar botones de color
        if hasattr(self, 'editor_bg_button'):
            self._update_color_button(self.editor_bg_button, theme_settings['editor_bg_color'])
        if hasattr(self, 'editor_text_button'):
            self._update_color_button(self.editor_text_button, theme_settings['editor_text_color'])
        if hasattr(self, 'editor_selection_button'):
            self._update_color_button(self.editor_selection_button, theme_settings['editor_selection_color'])
        if hasattr(self, 'line_bg_button'):
            self._update_color_button(self.line_bg_button, theme_settings['line_number_bg_color'])
        if hasattr(self, 'line_text_button'):
            self._update_color_button(self.line_text_button, theme_settings['line_number_text_color'])
        if hasattr(self, 'output_bg_button'):
            self._update_color_button(self.output_bg_button, theme_settings['output_bg_color'])
        if hasattr(self, 'output_text_button'):
            self._update_color_button(self.output_text_button, theme_settings['output_text_color'])
    
    def _update_theme_preview(self):
        """Actualiza la vista previa del tema"""
        from config import AppConfig
        
        current_theme = self.theme_combo.currentText()
        
        if current_theme in AppConfig.THEMES:
            theme = AppConfig.THEMES[current_theme]
            
            # Crear HTML de vista previa
            preview_html = f"""
            <div style="background-color: {theme['editor_bg_color']}; 
                        color: {theme['editor_text_color']}; 
                        padding: 15px; 
                        font-family: {theme['editor_font_family']}; 
                        font-size: {theme['editor_font_size']}px;
                        border-radius: 5px;">
                <div style="color: {theme['syntax_keyword_color']}; font-weight: bold;">def</div>
                <div style="color: {theme['syntax_function_color']};">example_function</div>
                <div style="color: {theme['syntax_string_color']};">"Texto de ejemplo"</div>
                <div style="color: {theme['syntax_comment_color']}; font-style: italic;"># Comentario</div>
                <div style="color: {theme['syntax_number_color']};">42</div>
            </div>
            """
            
            self.theme_preview.setText(preview_html)
            
            # Información del tema
            theme_descriptions = {
                "Oscuro": "Tema oscuro clásico con colores suaves para los ojos, ideal para sesiones largas de programación.",
                "Claro": "Tema claro tradicional con alto contraste, perfecto para ambientes bien iluminados.",
                "Solarized": "Tema diseñado científicamente para reducir la fatiga visual con una paleta de colores equilibrada.",
                "Monokai": "Tema popular inspirado en Sublime Text, con colores vibrantes sobre fondo oscuro.",
                "VS Code Dark": "Tema que replica los colores del popular editor Visual Studio Code en modo oscuro."
            }
            
            description = theme_descriptions.get(current_theme, "Tema personalizado.")
            
            self.theme_info.setText(f"""
<b>Tema: {current_theme}</b><br><br>
{description}<br><br>
<b>Características:</b><br>
• Color de fondo: {theme['editor_bg_color']}<br>
• Color de texto: {theme['editor_text_color']}<br>
• Fuente: {theme['editor_font_family']} ({theme['editor_font_size']}px)<br>
• Palabras clave: {theme['syntax_keyword_color']}<br>
• Strings: {theme['syntax_string_color']}<br>
• Comentarios: {theme['syntax_comment_color']}
            """)
    
    def _setup_ui(self):
        """Configura la interfaz de preferencias"""
        layout = QVBoxLayout(self)
        
        # Crear tabs
        tabs = QTabWidget()
        
        # Tab Temas (nuevo)
        themes_tab = self._create_themes_tab()
        tabs.addTab(themes_tab, "🎭 Temas")
        
        # Tab Formatter (nuevo)
        formatter_tab = self._create_formatter_tab()
        tabs.addTab(formatter_tab, "🔧 Formatter")
        
        # Tab Editor
        editor_tab = self._create_editor_tab()
        tabs.addTab(editor_tab, "🖥️ Editor")
        
        # Tab Salida
        output_tab = self._create_output_tab()
        tabs.addTab(output_tab, "📤 Salida")
        
        # Tab Colores
        colors_tab = self._create_colors_tab()
        tabs.addTab(colors_tab, "🎨 Colores")
        
        layout.addWidget(tabs)
        
        # Botones
        button_layout = QHBoxLayout()
        
        # Vista previa
        preview_button = QPushButton("👁️ Vista Previa")
        preview_button.clicked.connect(self._apply_preview)
        preview_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5DADE2; }
        """)
        
        # Restablecer
        reset_button = QPushButton("🔄 Restablecer")
        reset_button.clicked.connect(self._reset_to_defaults)
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #F39C12;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F8C471; }
        """)
        
        # Aceptar
        accept_button = QPushButton("✅ Aceptar")
        accept_button.clicked.connect(self._accept_changes)
        accept_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2ECC71; }
        """)
        
        # Cancelar
        cancel_button = QPushButton("❌ Cancelar")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #EC7063; }
        """)
        
        button_layout.addWidget(preview_button)
        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        button_layout.addWidget(accept_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def _create_editor_tab(self):
        """Crea el tab de configuración del editor"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo de fuente
        font_group = QGroupBox("🔤 Fuente del Editor")
        font_group.setMinimumWidth(400)
        font_layout = QGridLayout(font_group)
        
        # Familia de fuente
        font_layout.addWidget(QLabel("Familia:"), 0, 0)
        self.editor_font_combo = QComboBox()
        monospace_fonts = ['Consolas', 'Courier New', 'Monaco', 'Menlo', 'Liberation Mono', 'DejaVu Sans Mono']
        system_fonts = QFontDatabase.families()
        # Añadir fuentes monoespaciadas disponibles
        for font in monospace_fonts:
            if font in system_fonts:
                self.editor_font_combo.addItem(font)
        # Añadir algunas fuentes del sistema
        for font in system_fonts[:20]:  # Limitamos a 20 para no saturar
            if font not in monospace_fonts:
                self.editor_font_combo.addItem(font)
        
        self.editor_font_combo.setCurrentText(self.current_settings['editor_font_family'])
        font_layout.addWidget(self.editor_font_combo, 0, 1)
        
        # Tamaño de fuente
        font_layout.addWidget(QLabel("Tamaño:"), 1, 0)
        self.editor_font_size = QSpinBox()
        self.editor_font_size.setRange(8, 32)
        self.editor_font_size.setValue(self.current_settings['editor_font_size'])
        font_layout.addWidget(self.editor_font_size, 1, 1)
        
        layout.addWidget(font_group)
        
        # Grupo de numeración de líneas
        line_group = QGroupBox("🔢 Numeración de Líneas")
        line_group.setMinimumWidth(400)
        line_layout = QGridLayout(line_group)
        
        # Color de fondo de numeración
        line_layout.addWidget(QLabel("Fondo:"), 0, 0)
        self.line_bg_button = QPushButton()
        self.line_bg_button.setFixedHeight(30)
        self.line_bg_button.clicked.connect(lambda: self._choose_color('line_number_bg_color', self.line_bg_button))
        self._update_color_button(self.line_bg_button, self.current_settings['line_number_bg_color'])
        line_layout.addWidget(self.line_bg_button, 0, 1)
        
        # Color de texto de numeración
        line_layout.addWidget(QLabel("Texto:"), 1, 0)
        self.line_text_button = QPushButton()
        self.line_text_button.setFixedHeight(30)
        self.line_text_button.clicked.connect(lambda: self._choose_color('line_number_text_color', self.line_text_button))
        self._update_color_button(self.line_text_button, self.current_settings['line_number_text_color'])
        line_layout.addWidget(self.line_text_button, 1, 1)
        
        layout.addWidget(line_group)
        layout.addStretch()
        
        return widget
    
    def _create_output_tab(self):
        """Crea el tab de configuración de salida"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo de fuente de salida
        font_group = QGroupBox("🔤 Fuente del Área de Salida")
        font_group.setMinimumWidth(450)
        font_layout = QGridLayout(font_group)
        
        # Familia de fuente
        font_layout.addWidget(QLabel("Familia:"), 0, 0)
        self.output_font_combo = QComboBox()
        monospace_fonts = ['Consolas', 'Courier New', 'Monaco', 'Menlo', 'Liberation Mono', 'DejaVu Sans Mono']
        system_fonts = QFontDatabase.families()
        for font in monospace_fonts:
            if font in system_fonts:
                self.output_font_combo.addItem(font)
        for font in system_fonts[:20]:
            if font not in monospace_fonts:
                self.output_font_combo.addItem(font)
        
        self.output_font_combo.setCurrentText(self.current_settings['output_font_family'])
        font_layout.addWidget(self.output_font_combo, 0, 1)
        
        # Tamaño de fuente
        font_layout.addWidget(QLabel("Tamaño:"), 1, 0)
        self.output_font_size = QSpinBox()
        self.output_font_size.setRange(8, 32)
        self.output_font_size.setValue(self.current_settings['output_font_size'])
        font_layout.addWidget(self.output_font_size, 1, 1)
        
        layout.addWidget(font_group)
        
        # Grupo de colores de salida
        colors_group = QGroupBox("🎨 Colores del Área de Salida")
        colors_group.setMinimumWidth(450)
        colors_layout = QGridLayout(colors_group)
        
        # Color de fondo
        colors_layout.addWidget(QLabel("Fondo:"), 0, 0)
        self.output_bg_button = QPushButton()
        self.output_bg_button.setFixedHeight(30)
        self.output_bg_button.clicked.connect(lambda: self._choose_color('output_bg_color', self.output_bg_button))
        self._update_color_button(self.output_bg_button, self.current_settings['output_bg_color'])
        colors_layout.addWidget(self.output_bg_button, 0, 1)
        
        # Color de texto
        colors_layout.addWidget(QLabel("Texto:"), 1, 0)
        self.output_text_button = QPushButton()
        self.output_text_button.setFixedHeight(30)
        self.output_text_button.clicked.connect(lambda: self._choose_color('output_text_color', self.output_text_button))
        self._update_color_button(self.output_text_button, self.current_settings['output_text_color'])
        colors_layout.addWidget(self.output_text_button, 1, 1)
        
        layout.addWidget(colors_group)
        layout.addStretch()
        
        return widget
    
    def _create_colors_tab(self):
        """Crea el tab de configuración de colores del editor"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo de colores del editor
        colors_group = QGroupBox("🎨 Colores del Editor")
        colors_group.setMinimumWidth(400)
        colors_layout = QGridLayout(colors_group)
        
        # Color de fondo del editor
        colors_layout.addWidget(QLabel("Fondo del Editor:"), 0, 0)
        self.editor_bg_button = QPushButton()
        self.editor_bg_button.setFixedHeight(30)
        self.editor_bg_button.clicked.connect(lambda: self._choose_color('editor_bg_color', self.editor_bg_button))
        self._update_color_button(self.editor_bg_button, self.current_settings['editor_bg_color'])
        colors_layout.addWidget(self.editor_bg_button, 0, 1)
        
        # Color de texto del editor
        colors_layout.addWidget(QLabel("Texto del Editor:"), 1, 0)
        self.editor_text_button = QPushButton()
        self.editor_text_button.setFixedHeight(30)
        self.editor_text_button.clicked.connect(lambda: self._choose_color('editor_text_color', self.editor_text_button))
        self._update_color_button(self.editor_text_button, self.current_settings['editor_text_color'])
        colors_layout.addWidget(self.editor_text_button, 1, 1)
        
        # Color de selección
        colors_layout.addWidget(QLabel("Selección:"), 2, 0)
        self.editor_selection_button = QPushButton()
        self.editor_selection_button.setFixedHeight(30)
        self.editor_selection_button.clicked.connect(lambda: self._choose_color('editor_selection_color', self.editor_selection_button))
        self._update_color_button(self.editor_selection_button, self.current_settings['editor_selection_color'])
        colors_layout.addWidget(self.editor_selection_button, 2, 1)
        
        layout.addWidget(colors_group)
        
        # Nota informativa
        info_label = QLabel("""
💡 <b>Nota:</b> Los cambios en los colores se aplicarán inmediatamente 
al hacer clic en "Vista Previa" o "Aceptar". Puedes usar "Restablecer" 
para volver a los colores predeterminados.
        """)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #EBF5FB;
                border: 1px solid #3498DB;
                border-radius: 5px;
                padding: 10px;
                margin: 10px 0;
            }
        """)
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        return widget
    
    def _create_formatter_tab(self):
        """Crea el tab de configuración del formatter automático"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Grupo de configuración general del formatter
        general_group = QGroupBox("🔧 Configuración General del Formatter")
        general_group.setMinimumWidth(500)
        general_layout = QVBoxLayout(general_group)
        
        # Habilitar/deshabilitar formatter
        self.formatter_enabled_checkbox = QCheckBox("Habilitar formatter automático")
        self.formatter_enabled_checkbox.setChecked(self.current_settings.get('formatter_enabled', True))
        self.formatter_enabled_checkbox.stateChanged.connect(self._on_formatter_enabled_changed)
        general_layout.addWidget(self.formatter_enabled_checkbox)
        
        # Auto-formatear al guardar
        self.formatter_auto_save_checkbox = QCheckBox("Auto-formatear al guardar archivo (Ctrl+S)")
        self.formatter_auto_save_checkbox.setChecked(self.current_settings.get('formatter_auto_save', False))
        general_layout.addWidget(self.formatter_auto_save_checkbox)
        
        layout.addWidget(general_group)
        
        # Grupo de motor de formateo
        engine_group = QGroupBox("⚙️ Motor de Formateo")
        engine_group.setMinimumWidth(400)
        engine_layout = QVBoxLayout(engine_group)
        
        # Selector de motor
        engine_label = QLabel("Motor de formateo:")
        engine_layout.addWidget(engine_label)
        
        self.formatter_engine_combo = QComboBox()
        # Añadir motores disponibles
        self.formatter_engine_combo.addItem("Manual (Básico)")
        self.formatter_engine_combo.addItem("autopep8 (Recomendado)")
        self.formatter_engine_combo.addItem("black (Estricto)")
        
        # Establecer motor actual
        current_engine = self.current_settings.get('formatter_engine', 'autopep8')
        if current_engine == 'manual':
            self.formatter_engine_combo.setCurrentIndex(0)
        elif current_engine == 'autopep8':
            self.formatter_engine_combo.setCurrentIndex(1)
        elif current_engine == 'black':
            self.formatter_engine_combo.setCurrentIndex(2)
        
        engine_layout.addWidget(self.formatter_engine_combo)
        
        # Información del motor
        self.engine_info_label = QLabel()
        self.engine_info_label.setWordWrap(True)
        self.engine_info_label.setStyleSheet("""
            QLabel {
                background-color: #F8F9FA;
                border: 1px solid #DEE2E6;
                border-radius: 3px;
                padding: 8px;
                font-size: 11px;
            }
        """)
        self._update_engine_info()
        engine_layout.addWidget(self.engine_info_label)
        
        # Conectar cambio de motor
        self.formatter_engine_combo.currentIndexChanged.connect(self._update_engine_info)
        
        layout.addWidget(engine_group)
        
        # Grupo de configuración PEP 8
        pep8_group = QGroupBox("📏 Configuración PEP 8")
        pep8_group.setMinimumWidth(400)
        pep8_layout = QGridLayout(pep8_group)
        
        # Longitud máxima de línea
        pep8_layout.addWidget(QLabel("Longitud máxima de línea:"), 0, 0)
        self.formatter_line_length = QSpinBox()
        self.formatter_line_length.setRange(60, 120)
        self.formatter_line_length.setValue(self.current_settings.get('formatter_line_length', 88))
        pep8_layout.addWidget(self.formatter_line_length, 0, 1)
        
        # Tamaño de indentación
        pep8_layout.addWidget(QLabel("Tamaño de indentación:"), 1, 0)
        self.formatter_indent_size = QSpinBox()
        self.formatter_indent_size.setRange(2, 8)
        self.formatter_indent_size.setValue(self.current_settings.get('formatter_indent_size', 4))
        pep8_layout.addWidget(self.formatter_indent_size, 1, 1)
        
        # Usar tabs vs espacios
        self.formatter_use_tabs_checkbox = QCheckBox("Usar tabs en lugar de espacios")
        self.formatter_use_tabs_checkbox.setChecked(self.current_settings.get('formatter_use_tabs', False))
        pep8_layout.addWidget(self.formatter_use_tabs_checkbox, 2, 0, 1, 2)
        
        layout.addWidget(pep8_group)
        
        # Grupo de opciones adicionales
        options_group = QGroupBox("✨ Opciones Adicionales")
        options_group.setMinimumWidth(400)
        options_layout = QVBoxLayout(options_group)
        
        # Organizar imports
        self.formatter_organize_imports_checkbox = QCheckBox("Organizar imports automáticamente")
        self.formatter_organize_imports_checkbox.setChecked(self.current_settings.get('formatter_organize_imports', True))
        options_layout.addWidget(self.formatter_organize_imports_checkbox)
        
        # Eliminar espacios en blanco al final
        self.formatter_remove_trailing_checkbox = QCheckBox("Eliminar espacios en blanco al final de línea")
        self.formatter_remove_trailing_checkbox.setChecked(self.current_settings.get('formatter_remove_trailing', True))
        options_layout.addWidget(self.formatter_remove_trailing_checkbox)
        
        # Añadir nueva línea al final
        self.formatter_final_newline_checkbox = QCheckBox("Añadir nueva línea al final del archivo")
        self.formatter_final_newline_checkbox.setChecked(self.current_settings.get('formatter_final_newline', True))
        options_layout.addWidget(self.formatter_final_newline_checkbox)
        
        # Ajuste automático de espaciado
        self.formatter_auto_spacing_checkbox = QCheckBox("Ajuste automático de espaciado (operadores, comas, etc.)")
        self.formatter_auto_spacing_checkbox.setChecked(self.current_settings.get('formatter_auto_spacing', True))
        options_layout.addWidget(self.formatter_auto_spacing_checkbox)
        
        layout.addWidget(options_group)
        
        # Botón de prueba
        test_button = QPushButton("🧪 Probar Formatter")
        test_button.clicked.connect(self._test_formatter)
        layout.addWidget(test_button)
        
        # Información de instalación
        install_group = QGroupBox("📦 Instalación de Dependencias")
        install_group.setMinimumWidth(450)
        install_layout = QVBoxLayout(install_group)
        
        install_info = QLabel("""
💡 <b>Dependencias opcionales:</b> autopep8, black, isort
Instalar desde terminal: pip install autopep8 black isort
        """)
        install_info.setWordWrap(True)
        install_info.setStyleSheet("""
            QLabel {
                background-color: #EBF5FB;
                border: 1px solid #3498DB;
                border-radius: 5px;
                padding: 8px;
                font-size: 11px;
            }
        """)
        install_layout.addWidget(install_info)
        
        layout.addWidget(install_group)
        
        layout.addStretch()
        
        return widget
    
    def _on_formatter_enabled_changed(self, state):
        """Manejar cambio en habilitar/deshabilitar formatter"""
        enabled = state == 2  # 2 = checked
        
        # Habilitar/deshabilitar otros controles
        for widget in [self.formatter_auto_save_checkbox, self.formatter_engine_combo,
                      self.formatter_line_length, self.formatter_indent_size,
                      self.formatter_use_tabs_checkbox, self.formatter_organize_imports_checkbox,
                      self.formatter_remove_trailing_checkbox, self.formatter_final_newline_checkbox,
                      self.formatter_auto_spacing_checkbox]:
            widget.setEnabled(enabled)
    
    def _update_engine_info(self):
        """Actualiza la información del motor seleccionado"""
        engine_index = self.formatter_engine_combo.currentIndex()
        
        info_texts = [
            "<b>Manual (Básico):</b><br>• Formateo básico integrado<br>• Ajuste de indentación y espaciado<br>• Organización simple de imports<br>• No requiere dependencias externas",
            "<b>autopep8 (Recomendado):</b><br>• Formateo automático según PEP 8<br>• Corrección de errores de estilo<br>• Configuración flexible<br>• Requiere: pip install autopep8",
            "<b>black (Estricto):</b><br>• Formateo muy estricto y consistente<br>• Sin configuración (opinionated)<br>• Usado por muchos proyectos de Python<br>• Requiere: pip install black"
        ]
        
        self.engine_info_label.setText(info_texts[engine_index])
    
    def _test_formatter(self):
        """Prueba el formatter con código de ejemplo"""
        sample_code = '''import sys,os
from collections import defaultdict

def ejemplo_function( a,b,c ):
    if a > b:
        return a + b * c
    else:
        return b - a / c

class MiClase:
    def __init__(self,valor):
        self.valor = valor
    
    def metodo(self):
        lista = [1,2,3,4,5]
        return [x * 2 for x in lista if x > 2]

# Ejemplo con números decimales
def calcular(precio,descuento):
    precio_final = precio * (1 - descuento)
    return round(precio_final, 2)
'''
        
        # Crear diálogo para mostrar resultado
        dialog = QDialog(self)
        dialog.setWindowTitle("Prueba del Formatter")
        dialog.setFixedSize(700, 550)  # Aumentado un poco para mejor visibilidad
        
        layout = QVBoxLayout(dialog)
        
        # Código original
        layout.addWidget(QLabel("Código original:"))
        original_text = QTextEdit()
        original_text.setPlainText(sample_code)
        original_text.setMaximumHeight(170)  # Aumentado un poco
        layout.addWidget(original_text)
        
        # Código formateado
        layout.addWidget(QLabel("Código formateado:"))
        formatted_text = QTextEdit()
        formatted_text.setMaximumHeight(220)  # Aumentado para mejor visibilidad
        
        # Aplicar formateo de prueba
        try:
            # Simular configuración del formatter
            from utils.code_formatter import CodeFormatter
            
            formatter = CodeFormatter()
            
            # Obtener motor seleccionado
            engine_map = {0: 'manual', 1: 'autopep8', 2: 'black'}
            engine = engine_map[self.formatter_engine_combo.currentIndex()]
            
            # Aplicar formateo con supresión de warnings
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                formatted_code = formatter.format_code(sample_code, engine)
            
            formatted_text.setPlainText(formatted_code)
            layout.addWidget(formatted_text)
            
            # Información sobre el formateo
            info_text = f"✅ Formateo completado exitosamente con motor: {engine}"
            info_label = QLabel(info_text)
            info_label.setStyleSheet("color: green; font-weight: bold;")
            layout.addWidget(info_label)
            
        except Exception as e:
            import traceback
            error_details = str(e)
            formatted_text.setPlainText(f"Error al formatear:\n{error_details}")
            
            # Añadir información sobre motores disponibles
            try:
                from utils.code_formatter import FormatterPreferences
                available_engines = FormatterPreferences.get_available_engines()
                formatted_text.append(f"\n\nMotores disponibles: {', '.join(available_engines)}")
            except:
                pass
                
            error_label = QLabel("❌ Error en el formateo")
            error_label.setStyleSheet("color: red; font-weight: bold;")
            layout.addWidget(error_label)
        
        # Botón cerrar
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.exec()
    
    def _choose_color(self, setting_key, button):
        """Abre el selector de color"""
        current_color = QColor(self.new_settings[setting_key])
        color = QColorDialog.getColor(current_color, self, "Seleccionar Color")
        
        if color.isValid():
            self.new_settings[setting_key] = color.name()
            self._update_color_button(button, color.name())
    
    def _update_color_button(self, button, color):
        """Actualiza el botón con el color seleccionado"""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 2px solid #34495E;
                border-radius: 5px;
                color: {'white' if self._is_dark_color(color) else 'black'};
                font-weight: bold;
            }}
        """)
        button.setText(color.upper())
    
    def _is_dark_color(self, color_hex):
        """Determina si un color es oscuro"""
        color = QColor(color_hex)
        # Fórmula de luminancia
        luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
        return luminance < 0.5
    
    def _apply_preview(self):
        """Aplica una vista previa de los cambios"""
        self._update_new_settings()
        if hasattr(self.parent_editor, 'apply_preferences'):
            # Para vista previa, aplicar pero no guardar permanentemente
            self.parent_editor.apply_preferences(self.new_settings, preview=True)
    
    def _reset_to_defaults(self):
        """Restablece a configuraciones por defecto"""
        defaults = self._get_default_settings()
        self.new_settings = defaults.copy()
        
        # Actualizar controles
        self.editor_font_combo.setCurrentText(defaults['editor_font_family'])
        self.editor_font_size.setValue(defaults['editor_font_size'])
        self.output_font_combo.setCurrentText(defaults['output_font_family'])
        self.output_font_size.setValue(defaults['output_font_size'])
        
        # Actualizar botones de color
        self._update_color_button(self.editor_bg_button, defaults['editor_bg_color'])
        self._update_color_button(self.editor_text_button, defaults['editor_text_color'])
        self._update_color_button(self.editor_selection_button, defaults['editor_selection_color'])
        self._update_color_button(self.line_bg_button, defaults['line_number_bg_color'])
        self._update_color_button(self.line_text_button, defaults['line_number_text_color'])
        self._update_color_button(self.output_bg_button, defaults['output_bg_color'])
        self._update_color_button(self.output_text_button, defaults['output_text_color'])
        
        # Aplicar vista previa de los valores por defecto
        self._apply_preview()
    
    def _update_new_settings(self):
        """Actualiza las nuevas configuraciones con los valores de los controles"""
        self.new_settings['editor_font_family'] = self.editor_font_combo.currentText()
        self.new_settings['editor_font_size'] = self.editor_font_size.value()
        self.new_settings['output_font_family'] = self.output_font_combo.currentText()
        self.new_settings['output_font_size'] = self.output_font_size.value()
        
        # Configuraciones del formatter (si existen los controles)
        if hasattr(self, 'formatter_enabled_checkbox'):
            self.new_settings['formatter_enabled'] = self.formatter_enabled_checkbox.isChecked()
            self.new_settings['formatter_auto_save'] = self.formatter_auto_save_checkbox.isChecked()
            self.new_settings['formatter_engine_index'] = self.formatter_engine_combo.currentIndex()
            self.new_settings['formatter_line_length'] = self.formatter_line_length.value()
            self.new_settings['formatter_indent_size'] = self.formatter_indent_size.value()
            self.new_settings['formatter_use_tabs'] = self.formatter_use_tabs_checkbox.isChecked()
            self.new_settings['formatter_organize_imports'] = self.formatter_organize_imports_checkbox.isChecked()
            self.new_settings['formatter_remove_trailing'] = self.formatter_remove_trailing_checkbox.isChecked()
            self.new_settings['formatter_final_newline'] = self.formatter_final_newline_checkbox.isChecked()
            self.new_settings['formatter_auto_spacing'] = self.formatter_auto_spacing_checkbox.isChecked()
    
    def _accept_changes(self):
        """Acepta y aplica los cambios"""
        self._update_new_settings()
        if hasattr(self.parent_editor, 'apply_preferences'):
            # Aplicar y guardar permanentemente
            self.parent_editor.apply_preferences(self.new_settings, preview=False)
        self.accept()
    
    def get_new_settings(self):
        """Retorna las nuevas configuraciones"""
        return self.new_settings
    
    def keyPressEvent(self, event):
        """Maneja eventos de teclado para cerrar con ESC"""
        if event.key() == Qt.Key.Key_Escape:
            self.reject()  # Cierra el diálogo
        else:
            super().keyPressEvent(event)


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Resaltador de sintaxis para Python usando Pygments"""
    
    def __init__(self, document, theme_settings=None):
        super().__init__(document)
        self.lexer = PythonLexer()
        self.formatter = NullFormatter()
        self.theme_settings = theme_settings or self._get_default_theme()
        self._setup_formats()
    
    def _get_default_theme(self):
        """Obtiene el tema por defecto"""
        from config import AppConfig
        return AppConfig.THEMES[AppConfig.DEFAULT_THEME]
    
    def update_theme(self, theme_settings):
        """Actualiza el tema del resaltador"""
        self.theme_settings = theme_settings
        self._setup_formats()
        self.rehighlight()
    
    def _setup_formats(self):
        """Configura los formatos de colores para diferentes tipos de tokens"""
        self.formats = {}
        
        # Palabras clave (def, class, if, etc.)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(self.theme_settings.get('syntax_keyword_color', '#FF6B35')))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        self.formats[Token.Keyword] = keyword_format
        self.formats[Token.Keyword.Constant] = keyword_format
        self.formats[Token.Keyword.Declaration] = keyword_format
        self.formats[Token.Keyword.Namespace] = keyword_format
        self.formats[Token.Keyword.Reserved] = keyword_format
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(self.theme_settings.get('syntax_string_color', '#2ECC71')))
        self.formats[Token.Literal.String] = string_format
        self.formats[Token.Literal.String.Double] = string_format
        self.formats[Token.Literal.String.Single] = string_format
        self.formats[Token.Literal.String.Doc] = string_format
        
        # Comentarios
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(self.theme_settings.get('syntax_comment_color', '#95A5A6')))
        comment_format.setFontItalic(True)
        self.formats[Token.Comment] = comment_format
        self.formats[Token.Comment.Single] = comment_format
        self.formats[Token.Comment.Multiline] = comment_format
        
        # Números
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(self.theme_settings.get('syntax_number_color', '#E74C3C')))
        self.formats[Token.Literal.Number] = number_format
        self.formats[Token.Literal.Number.Integer] = number_format
        self.formats[Token.Literal.Number.Float] = number_format
        
        # Operadores
        operator_format = QTextCharFormat()
        operator_format.setForeground(QColor(self.theme_settings.get('syntax_operator_color', '#9B59B6')))
        operator_format.setFontWeight(QFont.Weight.Bold)
        self.formats[Token.Operator] = operator_format
        
        # Funciones built-in
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor(self.theme_settings.get('syntax_builtin_color', '#3498DB')))
        self.formats[Token.Name.Builtin] = builtin_format
        
        # Nombres de funciones
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(self.theme_settings.get('syntax_function_color', '#F39C12')))
        self.formats[Token.Name.Function] = function_format
        
        # Nombres de clases
        class_format = QTextCharFormat()
        class_format.setForeground(QColor(self.theme_settings.get('syntax_class_color', '#E67E22')))
        class_format.setFontWeight(QFont.Weight.Bold)
        self.formats[Token.Name.Class] = class_format
    
    def highlightBlock(self, text):
        """Resalta un bloque de texto"""
        try:
            tokens = list(self.lexer.get_tokens(text))
            index = 0
            
            for token_type, token_text in tokens:
                length = len(token_text)
                format_obj = self.formats.get(token_type)
                
                if format_obj:
                    self.setFormat(index, length, format_obj)
                
                index += length
                
        except Exception:
            # Si hay error en el resaltado, simplemente no resaltamos
            pass


class SyntaxHighlighterWithErrors(PythonSyntaxHighlighter):
    """Resaltador de sintaxis que también muestra errores"""
    
    def __init__(self, document, theme_settings=None):
        super().__init__(document, theme_settings)
        self.syntax_errors = []
        self._setup_error_formats()
    
    def _setup_error_formats(self):
        """Configura formatos para diferentes tipos de errores"""
        # Formato para errores
        self.error_format = QTextCharFormat()
        self.error_format.setUnderlineColor(QColor("#E74C3C"))
        self.error_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
        
        # Formato para advertencias
        self.warning_format = QTextCharFormat()
        self.warning_format.setUnderlineColor(QColor("#F39C12"))
        self.warning_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.WaveUnderline)
        
        # Formato para información
        self.info_format = QTextCharFormat()
        self.info_format.setUnderlineColor(QColor("#3498DB"))
        self.info_format.setUnderlineStyle(QTextCharFormat.UnderlineStyle.DotLine)
    
    def set_syntax_errors(self, errors):
        """Establece los errores de sintaxis a mostrar"""
        self.syntax_errors = errors
        self.rehighlight()
    
    def highlightBlock(self, text):
        """Resalta un bloque de texto incluyendo errores"""
        # Aplicar resaltado de sintaxis normal
        super().highlightBlock(text)
        
        # Aplicar subrayado de errores
        current_block = self.currentBlock()
        block_number = current_block.blockNumber() + 1  # Las líneas empiezan en 1
        
        for error in self.syntax_errors:
            if error.line_number == block_number:
                # Determinar formato según tipo de error
                if error.error_type == "error":
                    format_to_use = self.error_format
                elif error.error_type == "warning":
                    format_to_use = self.warning_format
                else:  # info
                    format_to_use = self.info_format
                
                # Aplicar formato a toda la línea o desde la columna específica
                start_index = max(0, error.column)
                length = len(text) - start_index
                if length > 0:
                    self.setFormat(start_index, length, format_to_use)
    
    def update_theme(self, theme_settings):
        """Actualiza el tema del resaltador de sintaxis"""
        self.theme_settings = theme_settings
        # Reconfigurar formatos con nuevos colores de tema
        self._setup_formats()
        # Volver a resaltar todo el documento
        self.rehighlight()


class FileExplorerWidget(QTreeWidget):
    """Widget explorador de archivos lateral con gestión completa de proyectos"""
    
    def __init__(self, parent_editor=None):
        super().__init__()  # No pasar parent_editor como parent de QTreeWidget
        self.parent_editor = parent_editor
        
        # Configuración del widget
        self.setHeaderLabel("📁 Explorador de Archivos")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.itemDoubleClicked.connect(self.open_file)
        self.itemExpanded.connect(self.on_item_expanded)  # Manejar expansión
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)  # Selección única
        self.setIndentation(20)  # Indentación más visible
        
        # Variables de estado
        self.current_root_path = os.path.expanduser("~")  # Comenzar en directorio home
        
        # Configurar estilo
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #2C3E50;
                color: #ECF0F1;
                border: 1px solid #34495E;
                border-radius: 5px;
                padding: 5px;
                selection-background-color: #3498DB;
                selection-color: white;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
            QTreeWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #34495E;
                height: 24px;
            }
            QTreeWidget::item:hover {
                background-color: #34495E;
            }
            QTreeWidget::item:selected {
                background-color: #3498DB;
                color: white;
            }
            QTreeWidget::branch:has-siblings {
                border-image: url(none);
                border: none;
            }
            QTreeWidget::branch:has-children {
                border-image: url(none);
                border: none;
            }
            QTreeWidget::branch:closed:has-children {
                border-image: url(none);
                border: none;
                image: url(none);
            }
            QTreeWidget::branch:open:has-children {
                border-image: url(none);
                border: none;
                image: url(none);
            }
        """)
        
        # Crear barra de herramientas de navegación
        self.create_navigation_toolbar()
        
        # Cargar el directorio inicial
        self.load_directory(self.current_root_path)
    
    def create_navigation_toolbar(self):
        """Crea la barra de herramientas de navegación"""
        # Como QTreeWidget no soporta toolbar directamente, 
        # vamos a usar el header personalizado del parent si existe
        if self.parent_editor and hasattr(self.parent_editor, 'file_explorer_layout'):
            # Crear widget contenedor para la barra de herramientas
            self.toolbar_widget = QWidget()
            toolbar_layout = QHBoxLayout(self.toolbar_widget)
            toolbar_layout.setContentsMargins(5, 5, 5, 5)
            
            # Botón para subir directorio
            self.up_button = QPushButton("⬆️")
            self.up_button.setFixedSize(30, 30)
            self.up_button.setToolTip("Subir al directorio padre")
            self.up_button.clicked.connect(self.navigate_up)
            self.up_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    border-radius: 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
                QPushButton:disabled {
                    background-color: #7F8C8D;
                }
            """)
            
            # Etiqueta de ruta actual
            self.path_label = QLabel("📁 Inicio")
            self.path_label.setStyleSheet("""
                QLabel {
                    color: #ECF0F1;
                    font-weight: bold;
                    padding: 5px;
                }
            """)
            
            # Botón para cambiar directorio raíz
            change_root_button = QPushButton("📂")
            change_root_button.setFixedSize(30, 30)
            change_root_button.setToolTip("Cambiar directorio raíz")
            change_root_button.clicked.connect(self.change_root_directory)
            change_root_button.setStyleSheet("""
                QPushButton {
                    background-color: #27AE60;
                    color: white;
                    border: none;
                    border-radius: 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
            
            toolbar_layout.addWidget(self.up_button)
            toolbar_layout.addWidget(self.path_label)
            toolbar_layout.addStretch()
            toolbar_layout.addWidget(change_root_button)
    
    def load_directory(self, path):
        """Carga un directorio en el explorador"""
        self.clear()
        self.current_root_path = path
        self.current_directory = path  # Añadir para tracking de directorio actual
        
        try:
            # Verificar que el directorio existe
            if not os.path.isdir(path):
                error_item = QTreeWidgetItem(self)
                error_item.setText(0, f"❌ Directorio no encontrado: {path}")
                error_item.setDisabled(True)
                return
            
            # Crear item raíz
            root_item = QTreeWidgetItem(self)
            root_name = os.path.basename(path) or path
            root_item.setText(0, f"📂 {root_name}")
            root_item.setData(0, Qt.ItemDataRole.UserRole, path)
            root_item.setExpanded(True)
            
            # Cargar contenido del directorio
            self._load_directory_contents(root_item, path)
            
            # Seleccionar el item raíz
            self.setCurrentItem(root_item)
            
            # Actualizar la barra de herramientas de navegación
            self.update_navigation_toolbar()
            
        except PermissionError:
            error_item = QTreeWidgetItem(self)
            error_item.setText(0, "❌ Sin permisos de acceso")
            error_item.setDisabled(True)
        except Exception as e:
            error_item = QTreeWidgetItem(self)
            error_item.setText(0, f"❌ Error: {str(e)}")
            error_item.setDisabled(True)
    
    def _load_directory_contents(self, parent_item, directory_path):
        """Carga el contenido de un directorio"""
        try:
            items = []
            # Obtener archivos y directorios
            for item_name in os.listdir(directory_path):
                if item_name.startswith('.') and not self._should_show_hidden():
                    continue
                
                item_path = os.path.join(directory_path, item_name)
                items.append((item_name, item_path))
            
            # Ordenar: directorios primero, luego archivos
            items.sort(key=lambda x: (not os.path.isdir(x[1]), x[0].lower()))
            
            for item_name, item_path in items:
                tree_item = QTreeWidgetItem(parent_item)
                
                if os.path.isdir(item_path):
                    tree_item.setText(0, f"📁 {item_name}")
                    tree_item.setData(0, Qt.ItemDataRole.UserRole, item_path)
                    # Agregar un item dummy para mostrar que tiene hijos
                    # Esto permite que aparezca el indicador de expansión
                    try:
                        sub_items = os.listdir(item_path)
                        if sub_items:  # Si tiene contenido, agregar dummy
                            dummy_item = QTreeWidgetItem(tree_item)
                            dummy_item.setText(0, "Cargando...")
                    except PermissionError:
                        pass
                else:
                    # Determinar icono por extensión
                    file_ext = os.path.splitext(item_name)[1].lower()
                    if file_ext in ['.py']:
                        icon = "🐍"
                    elif file_ext in ['.txt', '.md']:
                        icon = "📄"
                    elif file_ext in ['.json', '.yaml', '.yml']:
                        icon = "⚙️"
                    elif file_ext in ['.ini', '.cfg']:
                        icon = "🔧"
                    else:
                        icon = "📄"
                    
                    tree_item.setText(0, f"{icon} {item_name}")
                    tree_item.setData(0, Qt.ItemDataRole.UserRole, item_path)
                    
                    # Resaltar archivos soportados
                    if self._is_supported_file(item_path):
                        tree_item.setForeground(0, QColor("#3498DB"))
        
        except PermissionError:
            error_item = QTreeWidgetItem(parent_item)
            error_item.setText(0, "❌ Sin permisos")
            error_item.setDisabled(True)
    
    def _should_show_hidden(self):
        """Determina si mostrar archivos ocultos"""
        return getattr(self.parent_editor, 'show_hidden_files', False)
    
    def _should_auto_expand(self):
        """Determina si auto-expandir directorios"""
        return getattr(self.parent_editor, 'auto_expand_dirs', False)
    
    def _is_supported_file(self, file_path):
        """Verifica si un archivo es soportado"""
        from config import AppConfig
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in AppConfig.SUPPORTED_EXTENSIONS
    
    def open_file(self, item):
        """Abre un archivo al hacer doble clic o navega a directorio"""
        file_path = item.data(0, Qt.ItemDataRole.UserRole)
        print(f"🔍 open_file llamado con: {file_path}")  # Debug
        
        if os.path.isfile(file_path):
            print(f"✅ Es un archivo válido")  # Debug
            if self._is_supported_file(file_path):
                print(f"✅ Archivo soportado")  # Debug
                # Abrir archivo en el editor
                print(f"🔍 Intentando abrir archivo: {file_path}")  # Debug
                if hasattr(self.parent_editor, 'load_file_content'):
                    print("✅ Método load_file_content encontrado")  # Debug
                    result = self.parent_editor.load_file_content(file_path)
                    if result:
                        print("✅ Archivo cargado exitosamente")  # Debug
                    else:
                        print("❌ Error al cargar archivo")  # Debug
                else:
                    print("❌ Método load_file_content no encontrado")  # Debug
                    # Fallback: intentar abrir con el sistema
                    try:
                        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"No se pudo abrir el archivo:\n{str(e)}")
            else:
                print(f"❌ Archivo no soportado: {file_path}")  # Debug
        elif os.path.isdir(file_path):
            print(f"📁 Es un directorio, navegando...")  # Debug
            # Para directorios, navegar dentro de la carpeta (cambiar directorio raíz)
            self.navigate_to_directory(file_path)
        else:
            print(f"❌ Ruta no válida: {file_path}")  # Debug
    
    def on_item_expanded(self, item):
        """Maneja la expansión de items para carga bajo demanda"""
        # Verificar si el primer hijo es un item dummy
        if item.childCount() == 1:
            first_child = item.child(0)
            if first_child.text(0) == "Cargando...":
                # Remover el item dummy
                item.removeChild(first_child)
                # Cargar el contenido real
                file_path = item.data(0, Qt.ItemDataRole.UserRole)
                if os.path.isdir(file_path):
                    self._load_directory_contents(item, file_path)
    
    def keyPressEvent(self, event):
        """Maneja eventos de teclado para navegación mejorada"""
        current_item = self.currentItem()
        
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Enter para abrir archivo o expandir carpeta
            if current_item:
                self.open_file(current_item)
        elif event.key() == Qt.Key.Key_Right:
            # Flecha derecha para expandir carpeta
            if current_item and current_item.data(0, Qt.ItemDataRole.UserRole):
                file_path = current_item.data(0, Qt.ItemDataRole.UserRole)
                if os.path.isdir(file_path) and not current_item.isExpanded():
                    if current_item.childCount() == 0:
                        self._load_directory_contents(current_item, file_path)
                    current_item.setExpanded(True)
        elif event.key() == Qt.Key.Key_Left:
            # Flecha izquierda para contraer carpeta
            if current_item and current_item.isExpanded():
                current_item.setExpanded(False)
        elif event.key() == Qt.Key.Key_F5:
            # F5 para actualizar
            if current_item:
                file_path = current_item.data(0, Qt.ItemDataRole.UserRole)
                if os.path.isdir(file_path):
                    # Limpiar hijos y recargar
                    current_item.takeChildren()
                    self._load_directory_contents(current_item, file_path)
        else:
            # Para otras teclas, usar comportamiento por defecto
            super().keyPressEvent(event)
    
    def show_context_menu(self, position):
        """Muestra el menú contextual"""
        item = self.itemAt(position)
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2C3E50;
                color: #ECF0F1;
                border: 2px solid #3498DB;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #3498DB;
                color: white;
            }
        """)
        
        if item:
            file_path = item.data(0, Qt.ItemDataRole.UserRole)
            
            if os.path.isfile(file_path):
                # Menú para archivos
                open_action = menu.addAction("📖 Abrir archivo")
                open_action.triggered.connect(lambda: self.open_file(item))
                
                menu.addSeparator()
                delete_action = menu.addAction("🗑️ Eliminar archivo")
                delete_action.triggered.connect(lambda: self.delete_file(file_path))
                
            elif os.path.isdir(file_path):
                # Menú para directorios
                new_file_action = menu.addAction("📄 Nuevo archivo...")
                new_file_action.triggered.connect(lambda: self.create_new_file(file_path))
                
                new_folder_action = menu.addAction("📁 Nueva carpeta...")
                new_folder_action.triggered.connect(lambda: self.create_new_folder(file_path))
                
                menu.addSeparator()
                refresh_action = menu.addAction("🔄 Actualizar")
                refresh_action.triggered.connect(lambda: self.refresh_directory(item, file_path))
                
                menu.addSeparator()
                delete_action = menu.addAction("🗑️ Eliminar carpeta")
                delete_action.triggered.connect(lambda: self.delete_folder(file_path))
        else:
            # Menú para área vacía
            new_file_action = menu.addAction("📄 Nuevo archivo...")
            new_file_action.triggered.connect(lambda: self.create_new_file(self.current_root_path))
            
            new_folder_action = menu.addAction("📁 Nueva carpeta...")
            new_folder_action.triggered.connect(lambda: self.create_new_folder(self.current_root_path))
            
            menu.addSeparator()
            change_root_action = menu.addAction("📂 Cambiar directorio raíz...")
            change_root_action.triggered.connect(self.change_root_directory)
        
        menu.exec(self.mapToGlobal(position))
    
    def create_new_file(self, directory_path):
        """Crea un nuevo archivo"""
        file_name, ok = QInputDialog.getText(
            self, 
            "Nuevo Archivo", 
            "Nombre del archivo (con extensión):",
            text="nuevo_archivo.py"
        )
        
        if ok and file_name:
            file_path = os.path.join(directory_path, file_name)
            try:
                # Crear archivo vacío
                with open(file_path, 'w', encoding='utf-8') as f:
                    if file_name.endswith('.py'):
                        f.write('# Nuevo archivo Python\n\n')
                    else:
                        f.write('')
                
                # Actualizar explorador
                self.load_directory(self.current_root_path)
                
                # Abrir el archivo en el editor
                if hasattr(self.parent_editor, 'load_file_content'):
                    self.parent_editor.load_file_content(file_path)
                
                QMessageBox.information(self, "Éxito", f"Archivo '{file_name}' creado correctamente.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el archivo:\n{str(e)}")
    
    def create_new_folder(self, directory_path):
        """Crea una nueva carpeta"""
        folder_name, ok = QInputDialog.getText(
            self, 
            "Nueva Carpeta", 
            "Nombre de la carpeta:"
        )
        
        if ok and folder_name:
            folder_path = os.path.join(directory_path, folder_name)
            try:
                os.makedirs(folder_path, exist_ok=True)
                self.load_directory(self.current_root_path)
                QMessageBox.information(self, "Éxito", f"Carpeta '{folder_name}' creada correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear la carpeta:\n{str(e)}")
    
    def delete_file(self, file_path):
        """Elimina un archivo"""
        reply = QMessageBox.question(
            self, 
            "Confirmar Eliminación", 
            f"¿Estás seguro de que quieres eliminar el archivo?\n\n{os.path.basename(file_path)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(file_path)
                self.load_directory(self.current_root_path)
                QMessageBox.information(self, "Éxito", "Archivo eliminado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el archivo:\n{str(e)}")
    
    def delete_folder(self, folder_path):
        """Elimina una carpeta"""
        reply = QMessageBox.question(
            self, 
            "Confirmar Eliminación", 
            f"¿Estás seguro de que quieres eliminar la carpeta y todo su contenido?\n\n{os.path.basename(folder_path)}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import shutil
                shutil.rmtree(folder_path)
                self.load_directory(self.current_root_path)
                QMessageBox.information(self, "Éxito", "Carpeta eliminada correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar la carpeta:\n{str(e)}")
    
    def refresh_directory(self, item, directory_path):
        """Actualiza un directorio específico"""
        # Limpiar hijos del item
        item.takeChildren()
        # Recargar contenido
        self._load_directory_contents(item, directory_path)
    
    def change_root_directory(self):
        """Cambia el directorio raíz del explorador"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Directorio",
            self.current_root_path
        )
        
        if directory:
            self.load_directory(directory)
    
    def navigate_to_directory(self, directory_path):
        """Navega a un directorio específico y lo hace el nuevo directorio raíz"""
        if os.path.isdir(directory_path):
            self.current_directory = directory_path
            self.current_root_path = directory_path
            self.load_directory(directory_path)
            
            # Actualizar la barra de herramientas si existe
            if hasattr(self, 'toolbar_widget'):
                self.update_navigation_toolbar()
            return True
        return False
    
    def navigate_up(self):
        """Navega al directorio padre"""
        if hasattr(self, 'current_directory') and self.current_directory:
            parent_dir = os.path.dirname(self.current_directory)
            if parent_dir != self.current_directory:  # Evitar bucle en raíz del sistema
                self.navigate_to_directory(parent_dir)
    
    def update_navigation_toolbar(self):
        """Actualiza la barra de herramientas de navegación"""
        if hasattr(self, 'path_label') and hasattr(self, 'current_directory'):
            # Mostrar solo el nombre del directorio actual
            display_path = os.path.basename(self.current_directory) or self.current_directory
            self.path_label.setText(f"📁 {display_path}")
            
            # Habilitar/deshabilitar botón de subir según si estamos en la raíz
            if hasattr(self, 'up_button'):
                parent_dir = os.path.dirname(self.current_directory)
                self.up_button.setEnabled(parent_dir != self.current_directory)


class AutoCompleteWidget(QListWidget):
    """Widget de autocompletado que aparece mientras el usuario escribe"""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
        self.setWindowFlags(Qt.WindowType.Popup)
        self.setMaximumHeight(200)
        self.setMaximumWidth(400)
        self.hide()
        
        # Conectar señales
        self.itemClicked.connect(self.insert_completion)
        
        # Configurar estilo
        self.setStyleSheet("""
            QListWidget {
                background-color: #2C3E50;
                color: #ECF0F1;
                border: 2px solid #3498DB;
                border-radius: 5px;
                padding: 2px;
                selection-background-color: #3498DB;
                selection-color: white;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #34495E;
            }
            QListWidget::item:hover {
                background-color: #34495E;
            }
            QListWidget::item:selected {
                background-color: #3498DB;
                color: white;
            }
        """)
    
    def show_completions(self, completions, position):
        """Muestra las sugerencias de autocompletado"""
        if not completions:
            self.hide()
            return
        
        self.clear()
        for completion in completions:
            item = QListWidgetItem()
            
            if isinstance(completion, dict):
                # Completion con información adicional
                display_text = completion['text']
                if completion.get('type'):
                    display_text += f"  [{completion['type']}]"
                if completion.get('description'):
                    display_text += f" - {completion['description']}"
                item.setText(display_text)
                item.setData(Qt.ItemDataRole.UserRole, completion['text'])
            else:
                # Completion simple
                item.setText(completion)
                item.setData(Qt.ItemDataRole.UserRole, completion)
            
            self.addItem(item)
        
        # Posicionar el widget
        self.move(position)
        self.show()
        self.setCurrentRow(0)
    
    def insert_completion(self, item):
        """Inserta la completion seleccionada en el editor"""
        completion_text = item.data(Qt.ItemDataRole.UserRole)
        self.editor.insert_completion(completion_text)
        self.hide()
    
    def keyPressEvent(self, event):
        """Maneja eventos de teclado en el widget de autocompletado"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.editor.setFocus()
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.currentItem():
                self.insert_completion(self.currentItem())
        elif event.key() == Qt.Key.Key_Tab:
            if self.currentItem():
                self.insert_completion(self.currentItem())
        else:
            # Pasar otros eventos al editor
            self.editor.keyPressEvent(event)


class AutoCompleteManager:
    """Gestor de autocompletado con sugerencias inteligentes"""
    
    def __init__(self):
        # Palabras clave de Python
        self.keywords = list(keyword.kwlist)
        
        # Funciones built-in
        self.builtins = [name for name in dir(builtins) if not name.startswith('_')]
        
        # Snippets de código común
        self.snippets = {
            'def': {
                'text': 'def function_name():',
                'type': 'snippet',
                'description': 'Define una función',
                'template': 'def ${1:function_name}(${2:parameters}):\n    ${3:pass}'
            },
            'class': {
                'text': 'class ClassName:',
                'type': 'snippet', 
                'description': 'Define una clase',
                'template': 'class ${1:ClassName}:\n    def __init__(self${2:, parameters}):\n        ${3:pass}'
            },
            'if': {
                'text': 'if condition:',
                'type': 'snippet',
                'description': 'Estructura condicional if',
                'template': 'if ${1:condition}:\n    ${2:pass}'
            },
            'for': {
                'text': 'for item in iterable:',
                'type': 'snippet',
                'description': 'Bucle for',
                'template': 'for ${1:item} in ${2:iterable}:\n    ${3:pass}'
            },
            'while': {
                'text': 'while condition:',
                'type': 'snippet',
                'description': 'Bucle while',
                'template': 'while ${1:condition}:\n    ${2:pass}'
            },
            'try': {
                'text': 'try-except block',
                'type': 'snippet',
                'description': 'Manejo de excepciones',
                'template': 'try:\n    ${1:pass}\nexcept ${2:Exception} as e:\n    ${3:pass}'
            },
            'with': {
                'text': 'with statement',
                'type': 'snippet',
                'description': 'Context manager',
                'template': 'with ${1:expression} as ${2:variable}:\n    ${3:pass}'
            },
            'main': {
                'text': 'if __name__ == "__main__":',
                'type': 'snippet',
                'description': 'Punto de entrada principal',
                'template': 'if __name__ == "__main__":\n    ${1:main()}'
            }
        }
        
        # Documentación de funciones comunes
        self.function_docs = {
            'print': 'print(*values, sep=" ", end="\\n") - Imprime valores en la consola',
            'len': 'len(obj) - Retorna la longitud de un objeto',
            'range': 'range(start, stop, step) - Genera una secuencia de números',
            'input': 'input(prompt="") - Lee entrada del usuario',
            'int': 'int(x) - Convierte a entero',
            'str': 'str(x) - Convierte a string',
            'float': 'float(x) - Convierte a decimal',
            'list': 'list(iterable) - Crea una lista',
            'dict': 'dict(**kwargs) - Crea un diccionario',
            'set': 'set(iterable) - Crea un conjunto',
            'tuple': 'tuple(iterable) - Crea una tupla',
            'open': 'open(file, mode="r") - Abre un archivo',
            'enumerate': 'enumerate(iterable, start=0) - Enumera elementos con índices',
            'zip': 'zip(*iterables) - Combina múltiples iterables',
            'sorted': 'sorted(iterable, key=None, reverse=False) - Ordena elementos',
            'max': 'max(iterable) - Retorna el valor máximo',
            'min': 'min(iterable) - Retorna el valor mínimo',
            'sum': 'sum(iterable, start=0) - Suma elementos numéricos',
            'abs': 'abs(x) - Valor absoluto de un número',
            'round': 'round(number, ndigits=0) - Redondea un número'
        }
    
    def get_completions(self, text, cursor_position):
        """Obtiene las sugerencias de autocompletado para el texto actual"""
        # Validar que cursor_position esté dentro del rango del texto
        if not text or cursor_position < 0 or cursor_position > len(text):
            return []
        
        # Obtener la palabra actual
        word_start = cursor_position
        while word_start > 0 and word_start <= len(text) and (text[word_start - 1].isalnum() or text[word_start - 1] == '_'):
            word_start -= 1
        
        current_word = text[word_start:cursor_position].lower()
        
        if len(current_word) < 1:  # Mínimo 1 carácter para activar autocompletado
            return []
        
        completions = []
        
        # Snippets (prioridad alta)
        for snippet_key, snippet_info in self.snippets.items():
            if snippet_key.startswith(current_word):
                completions.append({
                    'text': snippet_key,
                    'type': 'snippet',
                    'description': snippet_info['description'],
                    'template': snippet_info.get('template', snippet_key)
                })
        
        # Palabras clave
        for kw in self.keywords:
            if kw.startswith(current_word):
                completions.append({
                    'text': kw,
                    'type': 'keyword',
                    'description': 'Palabra clave de Python'
                })
        
        # Funciones built-in
        for builtin in self.builtins:
            if builtin.startswith(current_word):
                doc = self.function_docs.get(builtin, 'Función built-in de Python')
                completions.append({
                    'text': builtin,
                    'type': 'builtin',
                    'description': doc
                })
        
        # Ordenar por relevancia (snippets primero, luego por longitud)
        completions.sort(key=lambda x: (
            0 if x['type'] == 'snippet' else 1,
            len(x['text'])
        ))
        
        return completions[:10]  # Limitar a 10 sugerencias


class LineNumberArea(QWidget):
    """Widget para mostrar la numeración de líneas"""
    
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor
    
    def sizeHint(self):
        """Tamaño recomendado para el área de numeración"""
        return self.codeEditor.lineNumberAreaWidth()
    
    def paintEvent(self, event):
        """Dibuja los números de línea"""
        self.codeEditor.lineNumberAreaPaintEvent(event)


class PythonCodeEditor(QPlainTextEdit):
    """Editor de código especializado para Python con indentación automática y numeración de líneas"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuración básica
        self.setFont(QFont("Consolas", 12))
        self.setTabStopDistance(40)  # 4 espacios de ancho
        
        # Área de numeración de líneas
        self.lineNumberArea = LineNumberArea(self)
        
        # Sistema de autocompletado
        self.autocomplete_widget = AutoCompleteWidget(self)
        self.autocomplete_manager = AutoCompleteManager()
        
        # Conectar señales para actualizar la numeración
        self.document().blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.verticalScrollBar().valueChanged.connect(self.updateLineNumberArea)
        self.textChanged.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.updateLineNumberArea)
        
        # Conectar señal para autocompletado
        self.textChanged.connect(self.on_text_changed)
        
        # Sistema de verificación de sintaxis en tiempo real
        self.syntax_checker = SyntaxChecker()
        self.syntax_checker.errors_found.connect(self.update_syntax_errors)
        
        # Timer para verificación de sintaxis con debounce
        self.syntax_check_timer = QTimer()
        self.syntax_check_timer.setSingleShot(True)
        self.syntax_check_timer.timeout.connect(self.check_syntax)
        self.syntax_check_timer.setInterval(1000)  # 1 segundo de delay
        
        # Conectar textChanged para verificación de sintaxis
        self.textChanged.connect(self.on_text_changed_syntax)
        
        # Lista de errores de sintaxis actuales
        self.current_syntax_errors = []
        
        # Configurar ancho inicial del área de numeración
        self.updateLineNumberAreaWidth(0)
        
        # Palabras clave que requieren indentación
        self.indent_keywords = {
            'if', 'elif', 'else', 'for', 'while', 'with', 'try', 'except', 
            'finally', 'def', 'class', 'async def', 'match', 'case'
        }
        
        # Configurar estilo
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #2C3E50;
                color: #ECF0F1;
                border: 2px solid #34495E;
                border-radius: 5px;
                padding: 10px;
                line-height: 1.2;
                selection-background-color: #3498DB;
            }
        """)
    
    def lineNumberAreaWidth(self):
        """Calcula el ancho necesario para el área de numeración"""
        digits = 1
        count = max(1, self.document().blockCount())
        while count >= 10:
            count /= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
    
    def updateLineNumberAreaWidth(self, newBlockCount):
        """Actualiza el ancho del área de numeración"""
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)
    
    def updateLineNumberArea(self, rect=None, dy=0):
        """Actualiza el área de numeración cuando cambia el contenido"""
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y() if rect else 0, 
                                     self.lineNumberArea.width(), 
                                     rect.height() if rect else self.lineNumberArea.height())
        
        if rect and rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)
    
    def resizeEvent(self, event):
        """Maneja el redimensionamiento del editor"""
        super().resizeEvent(event)
        
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), 
                                            self.lineNumberAreaWidth(), cr.height()))
    
    def lineNumberAreaPaintEvent(self, event):
        """Dibuja los números de línea"""
        painter = QPainter(self.lineNumberArea)
        
        # Obtener colores de las preferencias o usar defaults
        if hasattr(self, 'preferences_settings'):
            bg_color = self.preferences_settings['line_number_bg_color']
            text_color = self.preferences_settings['line_number_text_color']
        else:
            bg_color = "#34495E"
            text_color = "#BDC3C7"
        
        # Fondo del área de numeración
        painter.fillRect(event.rect(), QColor(bg_color))
        
        # Configuración del texto
        painter.setPen(QColor(text_color))
        painter.setFont(self.font())
        
        # Obtener el primer bloque visible y su posición
        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        # Altura de línea
        height = self.fontMetrics().height()
        
        # Dibujar números de línea
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1)
                painter.drawText(0, int(top), self.lineNumberArea.width() - 3, height,
                               Qt.AlignmentFlag.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1
    
    def keyPressEvent(self, event):
        """Maneja eventos de teclado incluyendo autocompletado e indentación automática"""
        # Si el widget de autocompletado está visible, manejar navegación
        if self.autocomplete_widget.isVisible():
            if event.key() == Qt.Key.Key_Escape:
                self.autocomplete_widget.hide()
                return
            elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                if self.autocomplete_widget.currentItem():
                    self.autocomplete_widget.insert_completion(self.autocomplete_widget.currentItem())
                return
            elif event.key() == Qt.Key.Key_Tab:
                if self.autocomplete_widget.currentItem():
                    self.autocomplete_widget.insert_completion(self.autocomplete_widget.currentItem())
                return
            elif event.key() == Qt.Key.Key_Down:
                current_row = self.autocomplete_widget.currentRow()
                if current_row < self.autocomplete_widget.count() - 1:
                    self.autocomplete_widget.setCurrentRow(current_row + 1)
                return
            elif event.key() == Qt.Key.Key_Up:
                current_row = self.autocomplete_widget.currentRow()
                if current_row > 0:
                    self.autocomplete_widget.setCurrentRow(current_row - 1)
                return
        
        # Manejar indentación automática
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.autocomplete_widget.hide()
            self._handle_enter_key()
        elif event.key() == Qt.Key.Key_Tab:
            if not self.autocomplete_widget.isVisible():
                self._handle_tab_key()
        elif event.key() == Qt.Key.Key_Backtab:  # Shift+Tab
            self.autocomplete_widget.hide()
            self._handle_shift_tab_key()
        else:
            # Para otras teclas, ocultar autocompletado si no es una letra/número
            if not (event.text().isalnum() or event.text() == '_'):
                self.autocomplete_widget.hide()
            super().keyPressEvent(event)
    
    def _handle_enter_key(self):
        """Maneja la tecla Enter para indentación automática"""
        cursor = self.textCursor()
        current_line = cursor.block().text()
        
        # Insertar nueva línea
        cursor.insertText('\n')
        
        # Calcular indentación actual
        current_indent = self._get_line_indent(current_line)
        
        # Verificar si la línea anterior requiere indentación adicional
        stripped_line = current_line.strip()
        needs_extra_indent = False
        
        if stripped_line.endswith(':'):
            # Verificar si es una palabra clave que requiere indentación
            for keyword in self.indent_keywords:
                if stripped_line.startswith(keyword + ' ') or stripped_line.startswith(keyword + ':'):
                    needs_extra_indent = True
                    break
            
            # También indentar para otras estructuras que terminen en ':'
            if not needs_extra_indent:
                # Buscar patrones comunes como "variable:" o "function():"
                if ('=' in stripped_line and stripped_line.endswith(':')) or \
                   ('(' in stripped_line and ')' in stripped_line and stripped_line.endswith(':')):
                    needs_extra_indent = True
        
        # Aplicar indentación
        if needs_extra_indent:
            cursor.insertText(current_indent + '    ')  # 4 espacios adicionales
        else:
            cursor.insertText(current_indent)
        
        self.setTextCursor(cursor)
    
    def _handle_tab_key(self):
        """Maneja la tecla Tab para indentar"""
        cursor = self.textCursor()
        
        if cursor.hasSelection():
            # Si hay selección, indentar todas las líneas seleccionadas
            self._indent_selection(cursor, indent=True)
        else:
            # Si no hay selección, insertar 4 espacios
            cursor.insertText('    ')
    
    def _handle_shift_tab_key(self):
        """Maneja Shift+Tab para des-indentar"""
        cursor = self.textCursor()
        
        if cursor.hasSelection():
            # Si hay selección, des-indentar todas las líneas seleccionadas
            self._indent_selection(cursor, indent=False)
        else:
            # Si no hay selección, des-indentar la línea actual
            self._unindent_current_line(cursor)
    
    def _indent_selection(self, cursor, indent=True):
        """Indenta o des-indenta las líneas seleccionadas"""
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        
        # Ir al inicio de la primera línea seleccionada
        cursor.setPosition(start)
        cursor.movePosition(cursor.MoveOperation.StartOfLine)
        start_block = cursor.blockNumber()
        
        # Ir al final de la última línea seleccionada
        cursor.setPosition(end)
        end_block = cursor.blockNumber()
        
        # Procesar cada línea
        cursor.beginEditBlock()
        for block_num in range(start_block, end_block + 1):
            cursor.movePosition(cursor.MoveOperation.Start)
            for _ in range(block_num):
                cursor.movePosition(cursor.MoveOperation.NextBlock)
            
            cursor.movePosition(cursor.MoveOperation.StartOfLine)
            
            if indent:
                cursor.insertText('    ')
            else:
                # Des-indentar: eliminar hasta 4 espacios del inicio
                line_text = cursor.block().text()
                spaces_to_remove = 0
                for char in line_text[:4]:
                    if char == ' ':
                        spaces_to_remove += 1
                    else:
                        break
                
                if spaces_to_remove > 0:
                    cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, spaces_to_remove)
                    cursor.removeSelectedText()
        
        cursor.endEditBlock()
        self.setTextCursor(cursor)
    
    def _unindent_current_line(self, cursor):
        """Des-indenta la línea actual"""
        cursor.movePosition(cursor.MoveOperation.StartOfLine)
        line_text = cursor.block().text()
        
        # Contar espacios al inicio de la línea
        spaces_to_remove = 0
        for char in line_text[:4]:
            if char == ' ':
                spaces_to_remove += 1
            else:
                break
        
        if spaces_to_remove > 0:
            cursor.movePosition(cursor.MoveOperation.Right, cursor.MoveMode.KeepAnchor, spaces_to_remove)
            cursor.removeSelectedText()
        
        self.setTextCursor(cursor)
    
    def _get_line_indent(self, line):
        """Obtiene la indentación de una línea"""
        indent = ''
        for char in line:
            if char == ' ':
                indent += char
            elif char == '\t':
                indent += '    '  # Convertir tabs a 4 espacios
            else:
                break
        return indent
    
    def on_text_changed(self):
        """Maneja cambios en el texto para mostrar autocompletado"""
        try:
            cursor = self.textCursor()
            text = self.toPlainText()
            cursor_position = cursor.position()
            
            # Validar posición del cursor
            if cursor_position < 0 or cursor_position > len(text):
                return
            
            # Obtener completions
            completions = self.autocomplete_manager.get_completions(text, cursor_position)
            
            if completions:
                # Calcular posición del widget de autocompletado
                cursor_rect = self.cursorRect()
                position = self.mapToGlobal(QPoint(
                    cursor_rect.left() + self.lineNumberArea.width(),
                    cursor_rect.bottom()
                ))
                
                # Mostrar autocompletado
                self.autocomplete_widget.show_completions(completions, position)
            else:
                self.autocomplete_widget.hide()
                
        except (IndexError, AttributeError) as e:
            # Manejar errores de índice o atributo en autocompletado
            if hasattr(self, 'autocomplete_widget'):
                self.autocomplete_widget.hide()
    
    def insert_completion(self, completion_text):
        """Inserta una completion en el editor"""
        cursor = self.textCursor()
        text = self.toPlainText()
        cursor_position = cursor.position()
        
        # Encontrar el inicio de la palabra actual
        word_start = cursor_position
        while word_start > 0 and (text[word_start - 1].isalnum() or text[word_start - 1] == '_'):
            word_start -= 1
        
        # Seleccionar la palabra actual para reemplazarla
        cursor.setPosition(word_start)
        cursor.setPosition(cursor_position, QTextCursor.MoveMode.KeepAnchor)
        
        # Verificar si es un snippet con template
        if hasattr(self.autocomplete_manager, 'snippets'):
            snippet_info = self.autocomplete_manager.snippets.get(completion_text)
            if snippet_info and 'template' in snippet_info:
                # Insertar template del snippet
                template = snippet_info['template']
                # Simplificar template eliminando placeholders por ahora
                simplified_template = template.replace('${1:', '').replace('${2:', '').replace('${3:', '')
                simplified_template = simplified_template.replace('}', '')
                cursor.insertText(simplified_template)
            else:
                cursor.insertText(completion_text)
        else:
            cursor.insertText(completion_text)
        
        self.setTextCursor(cursor)
    
    def on_text_changed_syntax(self):
        """Maneja cambios en el texto para verificación de sintaxis"""
        # Reiniciar el timer para verificación
        self.syntax_check_timer.stop()
        self.syntax_check_timer.start()
    
    def check_syntax(self):
        """Inicia la verificación de sintaxis en el hilo separado"""
        code = self.toPlainText()
        if code.strip():  # Solo verificar si hay código
            self.syntax_checker.set_code(code)
            if not self.syntax_checker.isRunning():
                self.syntax_checker.start()
    
    def update_syntax_errors(self, errors):
        """Actualiza los errores de sintaxis encontrados"""
        self.current_syntax_errors = errors
        
        # Si el editor tiene un resaltador de sintaxis con errores, actualizarlo
        if hasattr(self, 'syntax_highlighter') and isinstance(self.syntax_highlighter, SyntaxHighlighterWithErrors):
            self.syntax_highlighter.set_syntax_errors(errors)
    
    def mouseMoveEvent(self, event):
        """Maneja eventos de movimiento del mouse para mostrar tooltips de errores"""
        super().mouseMoveEvent(event)
        
        # Obtener posición del cursor en el texto
        cursor = self.cursorForPosition(event.pos())
        line_number = cursor.blockNumber() + 1
        
        # Buscar errores en esta línea
        errors_in_line = [error for error in self.current_syntax_errors if error.line_number == line_number]
        
        if errors_in_line:
            # Mostrar tooltip con los errores
            error_messages = []
            for error in errors_in_line:
                message = f"[{error.error_type.upper()}] {error.message}"
                if error.suggestion:
                    message += f"\nSugerencia: {error.suggestion}"
                error_messages.append(message)
            
            tooltip_text = "\n\n".join(error_messages)
            QToolTip.showText(event.globalPos(), tooltip_text, self)
        else:
            QToolTip.hideText()


class TabData:
    """Clase para almacenar información de cada pestaña"""
    def __init__(self, file_path=None, content="", is_modified=False):
        self.file_path = file_path
        self.content = content
        self.is_modified = is_modified
        self.original_content = content  # Para detectar cambios


class TabbedCodeEditor(QTabWidget):
    """Widget de pestañas que contiene múltiples editores de código"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_editor = parent
        self.tab_data = {}  # Diccionario para almacenar datos de cada pestaña
        
        # Configurar el widget de pestañas
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setUsesScrollButtons(True)
        
        # Permitir que Qt use el estilo del sistema para el botón de cierre
        # que automáticamente mostrará una X
        
        # Conectar señales
        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.on_tab_changed)
        
        # Configurar estilo
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #34495E;
                background-color: #2C3E50;
            }
            QTabWidget::tab-bar {
                left: 5px;
            }
            QTabBar::tab {
                background-color: #34495E;
                color: #ECF0F1;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background-color: #3498DB;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #5DADE2;
            }
        """)
        
        # Crear la primera pestaña
        self.new_tab()
    
    def new_tab(self, file_path=None, content=""):
        """Crea una nueva pestaña con un editor"""
        # Crear el editor
        editor = PythonCodeEditor()
        
        # Obtener configuraciones de tema actuales
        from config import AppConfig
        default_theme = AppConfig.DEFAULT_THEME
        settings = AppConfig.THEMES[default_theme].copy()
        
        theme_settings = {
            'syntax_colors': settings.get('syntax_colors', {}),
            'editor_colors': settings.get('editor_colors', {}),
            'font_settings': settings.get('font_settings', {})
        }
        
        # Configurar resaltado de sintaxis con soporte para errores y temas
        syntax_highlighter = SyntaxHighlighterWithErrors(editor.document(), theme_settings)
        editor.syntax_highlighter = syntax_highlighter  # Guardar referencia en el editor
        
        # Aplicar contenido si se proporciona
        if content:
            editor.setPlainText(content)
        
        # Configurar la pestaña
        if file_path:
            tab_name = os.path.basename(file_path)
            tooltip = file_path
        else:
            tab_count = self.count() + 1
            tab_name = f"Nuevo {tab_count}"
            tooltip = "Archivo sin guardar"
        
        # Agregar la pestaña
        tab_index = self.addTab(editor, tab_name)
        self.setTabToolTip(tab_index, tooltip)
        
        # Almacenar datos de la pestaña
        tab_data = TabData(file_path, content, False)
        self.tab_data[tab_index] = tab_data
        
        # Conectar señal de modificación del contenido
        editor.textChanged.connect(lambda: self.on_content_changed(tab_index))
        
        # Hacer activa la nueva pestaña
        self.setCurrentIndex(tab_index)
        
        return tab_index, editor
    
    def close_tab(self, index):
        """Cierra una pestaña con confirmación si hay cambios sin guardar"""
        if index in self.tab_data and self.tab_data[index].is_modified:
            # Hay cambios sin guardar, pedir confirmación
            reply = QMessageBox.question(
                self,
                "Archivo Modificado",
                f"El archivo '{self.tabText(index)}' tiene cambios sin guardar.\n\n¿Desea guardar antes de cerrar?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                # Guardar archivo
                if self.save_current_tab():
                    self._close_tab(index)
            elif reply == QMessageBox.StandardButton.Discard:
                # Descartar cambios
                self._close_tab(index)
            # Si es Cancel, no hacer nada
        else:
            # No hay cambios, cerrar directamente
            self._close_tab(index)
    
    def _close_tab(self, index):
        """Cierra la pestaña sin confirmación"""
        # Eliminar datos de la pestaña
        if index in self.tab_data:
            del self.tab_data[index]
        
        # Actualizar índices de tabs restantes
        new_tab_data = {}
        for i, data in self.tab_data.items():
            if i > index:
                new_tab_data[i - 1] = data
            elif i < index:
                new_tab_data[i] = data
        self.tab_data = new_tab_data
        
        # Eliminar la pestaña
        self.removeTab(index)
        
        # Si no quedan pestañas, crear una nueva
        if self.count() == 0:
            self.new_tab()
    
    def on_content_changed(self, tab_index):
        """Maneja cambios en el contenido de una pestaña"""
        if tab_index not in self.tab_data:
            return
        
        editor = self.widget(tab_index)
        current_content = editor.toPlainText()
        tab_data = self.tab_data[tab_index]
        
        # Verificar si el contenido ha cambiado
        is_modified = current_content != tab_data.original_content
        
        if is_modified != tab_data.is_modified:
            tab_data.is_modified = is_modified
            self.update_tab_title(tab_index)
    
    def update_tab_title(self, tab_index):
        """Actualiza el título de la pestaña con indicador de modificación"""
        if tab_index not in self.tab_data:
            return
        
        tab_data = self.tab_data[tab_index]
        
        if tab_data.file_path:
            tab_name = os.path.basename(tab_data.file_path)
        else:
            tab_name = f"Nuevo {tab_index + 1}"
        
        # Agregar asterisco si está modificado
        if tab_data.is_modified:
            tab_name = f"• {tab_name}"
        
        self.setTabText(tab_index, tab_name)
    
    def on_tab_changed(self, index):
        """Maneja el cambio de pestaña activa"""
        if index >= 0 and self.parent_editor:
            # Actualizar la información en el editor principal
            tab_data = self.tab_data.get(index)
            if tab_data and hasattr(self.parent_editor, 'current_file_path'):
                self.parent_editor.current_file_path = tab_data.file_path
    
    def get_current_editor(self):
        """Obtiene el editor de la pestaña activa"""
        current_index = self.currentIndex()
        if current_index >= 0:
            return self.widget(current_index)
        return None
    
    def get_current_file_path(self):
        """Obtiene la ruta del archivo de la pestaña activa"""
        current_index = self.currentIndex()
        if current_index in self.tab_data:
            return self.tab_data[current_index].file_path
        return None
    
    def load_file_in_tab(self, file_path):
        """Carga un archivo en una nueva pestaña o activa si ya está abierto"""
        # Verificar si el archivo ya está abierto
        for index, tab_data in self.tab_data.items():
            if tab_data.file_path == file_path:
                self.setCurrentIndex(index)
                return index
        
        # Cargar archivo en nueva pestaña
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            tab_index, editor = self.new_tab(file_path, content)
            
            # Marcar como contenido original para detectar cambios
            self.tab_data[tab_index].original_content = content
            
            return tab_index
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo cargar el archivo:\n{str(e)}"
            )
            return None
    
    def save_current_tab(self):
        """Guarda el contenido de la pestaña actual"""
        current_index = self.currentIndex()
        if current_index < 0:
            return False
        
        editor = self.widget(current_index)
        tab_data = self.tab_data[current_index]
        
        if not tab_data.file_path:
            # Archivo nuevo, pedir nombre
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar archivo",
                "",
                "Archivos Python (*.py);;Todos los archivos (*)"
            )
            if not file_path:
                return False
            tab_data.file_path = file_path
        
        # Guardar archivo
        try:
            content = editor.toPlainText()
            
            # Aplicar formateo automático si está habilitado
            if hasattr(self, 'parent_editor') and self.parent_editor:
                content = self.parent_editor._apply_auto_formatting(content)
            
            with open(tab_data.file_path, 'w', encoding='utf-8') as file:
                file.write(content)
            
            # Actualizar contenido del editor si se formateó
            if content != editor.toPlainText():
                cursor = editor.textCursor()
                position = cursor.position()
                editor.setPlainText(content)
                cursor.setPosition(min(position, len(content)))
                editor.setTextCursor(cursor)
            
            # Actualizar estado
            tab_data.original_content = content
            tab_data.is_modified = False
            self.update_tab_title(current_index)
            
            # Actualizar tooltip
            self.setTabToolTip(current_index, tab_data.file_path)
            
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo guardar el archivo:\n{str(e)}"
            )
            return False


class SessionManager:
    """Gestor de sesiones para recordar archivos abiertos y estado del editor"""
    
    def __init__(self, editor_instance=None):
        self.editor = editor_instance
        self.session_file = None
        self._setup_session_file()
    
    def _setup_session_file(self):
        """Configura la ruta del archivo de sesión"""
        from config import AppConfig
        import os
        
        # Usar directorio del proyecto para guardar sesión
        project_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(project_dir)  # Subir un nivel desde views/
        self.session_file = os.path.join(project_dir, AppConfig.SESSION_FILE_PATH)
    
    def save_session(self):
        """Guarda el estado actual de la sesión"""
        try:
            from config import AppConfig
            import json
            
            if not AppConfig.SESSION_MANAGEMENT_ENABLED:
                return
            
            session_data = {
                'version': '1.0',
                'timestamp': self._get_timestamp(),
                'open_files': [],
                'active_tab_index': 0,
                'window_state': {},
                'theme': AppConfig.DEFAULT_THEME,
                'preferences': {}
            }
            
            # Guardar archivos abiertos y su estado
            if hasattr(self.editor, 'tab_widget'):
                tab_widget = self.editor.tab_widget
                session_data['active_tab_index'] = tab_widget.currentIndex()
                
                for i in range(tab_widget.count()):
                    editor_widget = tab_widget.widget(i)
                    tab_text = tab_widget.tabText(i)
                    
                    file_info = {
                        'index': i,
                        'title': tab_text,
                        'file_path': None,
                        'content': '',
                        'cursor_position': 0,
                        'scroll_position': 0,
                        'is_modified': False
                    }
                    
                    # Obtener información del archivo si existe
                    if hasattr(tab_widget, 'tab_data') and i in tab_widget.tab_data:
                        tab_data = tab_widget.tab_data[i]
                        file_info['file_path'] = tab_data.file_path
                        file_info['is_modified'] = tab_data.is_modified
                    
                    # Obtener contenido y posición del cursor
                    if hasattr(editor_widget, 'toPlainText'):
                        file_info['content'] = editor_widget.toPlainText()
                        
                        if hasattr(editor_widget, 'textCursor'):
                            cursor = editor_widget.textCursor()
                            file_info['cursor_position'] = cursor.position()
                        
                        if hasattr(editor_widget, 'verticalScrollBar'):
                            scroll_bar = editor_widget.verticalScrollBar()
                            file_info['scroll_position'] = scroll_bar.value()
                    
                    session_data['open_files'].append(file_info)
            
            # Guardar estado de la ventana
            if hasattr(self.editor, 'window'):
                window = self.editor.window
                session_data['window_state'] = {
                    'geometry': {
                        'x': window.x(),
                        'y': window.y(),
                        'width': window.width(),
                        'height': window.height()
                    },
                    'maximized': window.isMaximized(),
                    'minimized': window.isMinimized()
                }
            
            # Guardar tema actual
            if hasattr(self.editor, 'current_preferences'):
                session_data['theme'] = self.editor.current_preferences.get('current_theme', AppConfig.DEFAULT_THEME)
                session_data['preferences'] = self.editor.current_preferences.copy()
            
            # Escribir archivo de sesión
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Sesión guardada: {len(session_data['open_files'])} archivos")
            
        except Exception as e:
            print(f"❌ Error guardando sesión: {e}")
    
    def restore_session(self):
        """Restaura la sesión guardada"""
        try:
            from config import AppConfig
            import json
            import os
            
            if not AppConfig.SESSION_MANAGEMENT_ENABLED or not AppConfig.SESSION_RESTORE_ON_STARTUP:
                return False
            
            if not os.path.exists(self.session_file):
                print("📝 No hay sesión previa para restaurar")
                return False
            
            # Leer archivo de sesión
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            print(f"🔄 Restaurando sesión: {len(session_data.get('open_files', []))} archivos")
            
            # Restaurar archivos abiertos
            open_files = session_data.get('open_files', [])
            if open_files and hasattr(self.editor, 'tab_widget'):
                # Limpiar pestañas existentes (excepto la primera vacía)
                tab_widget = self.editor.tab_widget
                while tab_widget.count() > 1:
                    tab_widget.removeTab(1)
                
                # Si hay archivos para restaurar, quitar la pestaña vacía inicial
                if open_files:
                    if tab_widget.count() > 0:
                        tab_widget.removeTab(0)
                
                # Restaurar cada archivo
                for file_info in open_files:
                    file_path = file_info.get('file_path')
                    content = file_info.get('content', '')
                    cursor_pos = file_info.get('cursor_position', 0)
                    scroll_pos = file_info.get('scroll_position', 0)
                    
                    # Crear nueva pestaña
                    if file_path and os.path.exists(file_path):
                        # Archivo existe, abrirlo
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            tab_index, editor = tab_widget.new_tab(file_path, file_content)
                        except Exception as e:
                            print(f"⚠️ Error leyendo archivo {file_path}: {e}")
                            # Usar contenido de la sesión como fallback
                            tab_index, editor = tab_widget.new_tab(file_path, content)
                    else:
                        # Archivo no existe o es nuevo, usar contenido de sesión
                        tab_index, editor = tab_widget.new_tab(file_path, content)
                    
                    # Restaurar posición del cursor y scroll
                    if hasattr(editor, 'textCursor'):
                        cursor = editor.textCursor()
                        cursor.setPosition(min(cursor_pos, len(editor.toPlainText())))
                        editor.setTextCursor(cursor)
                    
                    if hasattr(editor, 'verticalScrollBar'):
                        scroll_bar = editor.verticalScrollBar()
                        QTimer.singleShot(100, lambda pos=scroll_pos: scroll_bar.setValue(pos))
                
                # Restaurar pestaña activa
                active_index = session_data.get('active_tab_index', 0)
                if 0 <= active_index < tab_widget.count():
                    tab_widget.setCurrentIndex(active_index)
            
            # Restaurar estado de ventana
            if AppConfig.SESSION_REMEMBER_WINDOW_STATE and hasattr(self.editor, 'window'):
                window_state = session_data.get('window_state', {})
                if window_state:
                    self._restore_window_state(window_state)
            
            # Restaurar tema y preferencias
            if AppConfig.SESSION_REMEMBER_THEME:
                theme = session_data.get('theme', AppConfig.DEFAULT_THEME)
                preferences = session_data.get('preferences', {})
                
                if preferences and hasattr(self.editor, 'apply_preferences'):
                    # Aplicar preferencias restauradas
                    QTimer.singleShot(500, lambda: self.editor.apply_preferences(preferences, preview=True))
            
            print("✅ Sesión restaurada exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error restaurando sesión: {e}")
            return False
    
    def _restore_window_state(self, window_state):
        """Restaura el estado de la ventana"""
        try:
            if not hasattr(self.editor, 'window'):
                return
            
            window = self.editor.window
            geometry = window_state.get('geometry', {})
            
            if geometry:
                # Restaurar posición y tamaño
                window.setGeometry(
                    geometry.get('x', 100),
                    geometry.get('y', 100),
                    geometry.get('width', 1000),
                    geometry.get('height', 700)
                )
            
            # Restaurar estado maximizado/minimizado
            if window_state.get('maximized', False):
                window.showMaximized()
            elif window_state.get('minimized', False):
                window.showMinimized()
            else:
                window.showNormal()
                
        except Exception as e:
            print(f"⚠️ Error restaurando estado de ventana: {e}")
    
    def clear_session(self):
        """Limpia la sesión guardada"""
        try:
            import os
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
                print("🗑️ Sesión limpiada")
        except Exception as e:
            print(f"❌ Error limpiando sesión: {e}")
    
    def get_recent_files(self):
        """Obtiene la lista de archivos recientes"""
        try:
            from config import AppConfig
            import json
            import os
            
            if not os.path.exists(self.session_file):
                return []
            
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            recent_files = []
            for file_info in session_data.get('open_files', []):
                file_path = file_info.get('file_path')
                if file_path and os.path.exists(file_path):
                    recent_files.append({
                        'path': file_path,
                        'name': os.path.basename(file_path),
                        'timestamp': session_data.get('timestamp', '')
                    })
            
            # Limitar número de archivos recientes
            return recent_files[:AppConfig.SESSION_MAX_RECENT_FILES]
            
        except Exception as e:
            print(f"❌ Error obteniendo archivos recientes: {e}")
            return []
    
    def _get_timestamp(self):
        """Obtiene timestamp actual"""
        from datetime import datetime
        return datetime.now().isoformat()


class IntegratedTerminal(QWidget):
    """Terminal integrado con REPL de Python y comandos del sistema"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_editor = parent
        self.history = []
        self.history_index = -1
        self.current_process = None
        self.python_repl_active = False
        self.python_process = None
        
        self._setup_ui()
        self._setup_styles()
        
    def _setup_ui(self):
        """Configura la interfaz del terminal"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Barra de herramientas del terminal
        toolbar_layout = QHBoxLayout()
        
        # Selector de modo
        mode_label = QLabel("Modo:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["🖥️ Sistema", "🐍 Python REPL", "📦 Pip"])
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        
        # Botones de acción
        self.clear_btn = QPushButton("🗑️ Limpiar")
        self.clear_btn.clicked.connect(self.clear_terminal)
        
        self.stop_btn = QPushButton("⏹️ Detener")
        self.stop_btn.clicked.connect(self.stop_current_process)
        self.stop_btn.setEnabled(False)
        
        toolbar_layout.addWidget(mode_label)
        toolbar_layout.addWidget(self.mode_combo)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.clear_btn)
        toolbar_layout.addWidget(self.stop_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Área de salida del terminal
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(QFont("Consolas", 11))
        layout.addWidget(self.terminal_output)
        
        # Entrada de comandos
        input_layout = QHBoxLayout()
        
        self.prompt_label = QLabel("$")
        self.command_input = QLineEdit()
        self.command_input.returnPressed.connect(self.execute_command)
        
        # Configurar autocompletado básico
        self.command_input.installEventFilter(self)
        
        input_layout.addWidget(self.prompt_label)
        input_layout.addWidget(self.command_input)
        
        layout.addLayout(input_layout)
        
        # Agregar mensaje de bienvenida
        self._show_welcome_message()
    
    def _setup_styles(self):
        """Configura los estilos del terminal"""
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                color: #D4D4D4;
            }
            QTextEdit {
                background-color: #0C0C0C;
                color: #00FF00;
                border: 1px solid #333;
                border-radius: 3px;
                font-family: 'Consolas', 'Courier New', monospace;
                selection-background-color: #264F78;
            }
            QLineEdit {
                background-color: #2D2D30;
                color: #CCCCCC;
                border: 1px solid #3F3F46;
                border-radius: 3px;
                padding: 5px;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QLineEdit:focus {
                border-color: #007ACC;
            }
            QComboBox {
                background-color: #2D2D30;
                color: #CCCCCC;
                border: 1px solid #3F3F46;
                border-radius: 3px;
                padding: 3px;
                min-width: 120px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-style: solid;
                border-width: 3px;
                border-color: #CCCCCC transparent transparent transparent;
                margin-left: 5px;
            }
            QPushButton {
                background-color: #0E639C;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
            QLabel {
                color: #CCCCCC;
                font-weight: bold;
            }
        """)
    
    def _show_welcome_message(self):
        """Muestra el mensaje de bienvenida del terminal"""
        welcome_text = """
💻 Terminal Integrado - Editor de Código Python
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 Modos disponibles:
  🖥️ Sistema   : Comandos del sistema (ls, cd, mkdir, etc.)
  🐍 Python REPL : Intérprete interactivo de Python
  📦 Pip       : Instalación y gestión de paquetes

⌨️ Atajos:
  ↑/↓        : Navegar historial de comandos
  Ctrl+C     : Interrumpir proceso actual
  Ctrl+L     : Limpiar terminal

💡 Ejemplos:
  ls -la                    # Listar archivos
  cd /ruta/directorio      # Cambiar directorio
  python --version         # Versión de Python
  pip install requests     # Instalar paquete
  
¡Comienza escribiendo un comando!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        self.terminal_output.setTextColor(QColor("#00FFFF"))
        self.terminal_output.append(welcome_text)
        self.terminal_output.setTextColor(QColor("#00FF00"))
        
    def _on_mode_changed(self, mode_text):
        """Maneja el cambio de modo del terminal"""
        if "Python REPL" in mode_text:
            self._start_python_repl()
            self.prompt_label.setText(">>>")
        elif "Pip" in mode_text:
            self._setup_pip_mode()
            self.prompt_label.setText("pip")
        else:
            self._setup_system_mode()
            self.prompt_label.setText("$")
            
        # Limpiar entrada actual
        self.command_input.clear()
    
    def _start_python_repl(self):
        """Inicia el REPL de Python"""
        try:
            import subprocess
            import sys
            
            self.python_repl_active = True
            self.terminal_output.setTextColor(QColor("#FFFF00"))
            self.terminal_output.append("\n🐍 Modo Python REPL activado")
            self.terminal_output.append("Python " + sys.version.split()[0])
            self.terminal_output.append("Escribe 'exit()' para salir del REPL")
            self.terminal_output.setTextColor(QColor("#00FF00"))
            
        except Exception as e:
            self.terminal_output.setTextColor(QColor("#FF0000"))
            self.terminal_output.append(f"❌ Error al iniciar Python REPL: {e}")
            self.terminal_output.setTextColor(QColor("#00FF00"))
    
    def _setup_pip_mode(self):
        """Configura el modo pip"""
        self.python_repl_active = False
            
        self.terminal_output.setTextColor(QColor("#FFFF00"))
        self.terminal_output.append("\n📦 Modo Pip activado")
        self.terminal_output.append("Ejemplos: install requests, list, show requests, uninstall requests")
        self.terminal_output.setTextColor(QColor("#00FF00"))
    
    def _setup_system_mode(self):
        """Configura el modo sistema"""
        self.python_repl_active = False
            
        self.terminal_output.setTextColor(QColor("#FFFF00"))
        self.terminal_output.append("\n🖥️ Modo Sistema activado")
        self.terminal_output.setTextColor(QColor("#00FF00"))
    
    def execute_command(self):
        """Ejecuta el comando ingresado"""
        command = self.command_input.text().strip()
        if not command:
            return
            
        # Agregar al historial
        self.history.append(command)
        self.history_index = len(self.history)
        
        # Mostrar comando en terminal
        current_mode = self.mode_combo.currentText()
        prompt = self.prompt_label.text()
        
        self.terminal_output.setTextColor(QColor("#FFFFFF"))
        self.terminal_output.append(f"{prompt} {command}")
        self.terminal_output.setTextColor(QColor("#00FF00"))
        
        # Ejecutar según el modo
        if "Python REPL" in current_mode:
            self._execute_python_command(command)
        elif "Pip" in current_mode:
            self._execute_pip_command(command)
        else:
            self._execute_system_command(command)
            
        # Limpiar entrada
        self.command_input.clear()
        
        # Auto-scroll al final
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.terminal_output.setTextCursor(cursor)
    
    def _execute_python_command(self, command):
        """Ejecuta comando en Python REPL de forma segura"""
        try:
            if command.lower() in ['exit()', 'quit()', 'exit', 'quit']:
                self.terminal_output.setTextColor(QColor("#FFFF00"))
                self.terminal_output.append("🔄 Saliendo del Python REPL...")
                self.mode_combo.setCurrentText("🖥️ Sistema")
                return
            
            # Mostrar comando ejecutándose
            self.terminal_output.setTextColor(QColor("#CCCCCC"))
            self.terminal_output.append(f">>> {command[:100]}{'...' if len(command) > 100 else ''}")
            self.terminal_output.setTextColor(QColor("#00FF00"))
            
            # Ejecutar código Python de forma segura y síncrona (para evitar problemas de hilos)
            import io
            import sys
            from contextlib import redirect_stdout, redirect_stderr
            
            # Variables para capturar salida
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            
            try:
                # Capturar salida
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    # Suprimir warnings durante la evaluación
                    import warnings
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        
                        # Dividir código en líneas para mejor manejo
                        lines = command.strip().split('\n')
                        
                        # Intentar como expresión simple primero
                        if len(lines) == 1 and not any(keyword in command for keyword in ['=', 'import', 'def', 'class', 'if', 'for', 'while', 'with', 'try']):
                            try:
                                result = eval(command)
                                if result is not None:
                                    print(result)
                            except:
                                # Si falla como expresión, ejecutar como código
                                exec(command)
                        else:
                            # Ejecutar como código completo
                            exec(command)
                
                # Mostrar resultado
                stdout_output = stdout_capture.getvalue()
                stderr_output = stderr_capture.getvalue()
                
                if stdout_output:
                    self.terminal_output.append(stdout_output.strip())
                    
                if stderr_output:
                    self.terminal_output.setTextColor(QColor("#FF8800"))
                    self.terminal_output.append(stderr_output.strip())
                    self.terminal_output.setTextColor(QColor("#00FF00"))
                    
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
            # Auto-scroll al final
            cursor = self.terminal_output.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.terminal_output.setTextCursor(cursor)
                            
        except Exception as e:
            self.terminal_output.setTextColor(QColor("#FF0000"))
            self.terminal_output.append(f"❌ Error en Python REPL: {e}")
            self.terminal_output.setTextColor(QColor("#00FF00"))
    
    def _execute_pip_command(self, command):
        """Ejecuta comando pip"""
        try:
            import subprocess
            import sys
            
            # Construir comando pip completo
            pip_cmd = [sys.executable, "-m", "pip"] + command.split()
            
            self.stop_btn.setEnabled(True)
            self.terminal_output.setTextColor(QColor("#FFFF00"))
            self.terminal_output.append(f"⚡ Ejecutando: pip {command}")
            self.terminal_output.setTextColor(QColor("#00FF00"))
            
            # Ejecutar comando pip
            process = subprocess.run(
                pip_cmd,
                capture_output=True,
                text=True,
                timeout=60  # Timeout de 60 segundos
            )
            
            # Mostrar salida
            if process.stdout:
                self.terminal_output.append(process.stdout.strip())
                
            if process.stderr:
                self.terminal_output.setTextColor(QColor("#FF8800"))
                self.terminal_output.append(process.stderr.strip())
                self.terminal_output.setTextColor(QColor("#00FF00"))
            
            if process.returncode == 0:
                self.terminal_output.setTextColor(QColor("#00FF00"))
                self.terminal_output.append("✅ Comando completado exitosamente")
                self.terminal_output.setTextColor(QColor("#00FF00"))
            else:
                self.terminal_output.setTextColor(QColor("#FF0000"))
                self.terminal_output.append(f"❌ Comando falló con código: {process.returncode}")
                self.terminal_output.setTextColor(QColor("#00FF00"))
                
        except subprocess.TimeoutExpired:
            self.terminal_output.setTextColor(QColor("#FF8800"))
            self.terminal_output.append("⏰ Comando pip excedió el tiempo límite")
            self.terminal_output.setTextColor(QColor("#00FF00"))
        except Exception as e:
            self.terminal_output.setTextColor(QColor("#FF0000"))
            self.terminal_output.append(f"❌ Error ejecutando pip: {e}")
            self.terminal_output.setTextColor(QColor("#00FF00"))
        finally:
            self.stop_btn.setEnabled(False)
    
    def _execute_system_command(self, command):
        """Ejecuta comando del sistema"""
        try:
            import subprocess
            import os
            
            self.stop_btn.setEnabled(True)
            self.terminal_output.setTextColor(QColor("#FFFF00"))
            self.terminal_output.append(f"⚡ Ejecutando: {command}")
            self.terminal_output.setTextColor(QColor("#00FF00"))
            
            # Ejecutar comando del sistema
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                timeout=30  # Timeout de 30 segundos
            )
            
            # Mostrar salida
            if process.stdout:
                self.terminal_output.append(process.stdout.strip())
                
            if process.stderr:
                self.terminal_output.setTextColor(QColor("#FF8800"))
                self.terminal_output.append(process.stderr.strip())
                self.terminal_output.setTextColor(QColor("#00FF00"))
                
        except subprocess.TimeoutExpired:
            self.terminal_output.setTextColor(QColor("#FF8800"))
            self.terminal_output.append("⏰ Comando excedió el tiempo límite")
            self.terminal_output.setTextColor(QColor("#00FF00"))
        except Exception as e:
            self.terminal_output.setTextColor(QColor("#FF0000"))
            self.terminal_output.append(f"❌ Error ejecutando comando: {e}")
            self.terminal_output.setTextColor(QColor("#00FF00"))
        finally:
            self.stop_btn.setEnabled(False)
    
    def clear_terminal(self):
        """Limpia el contenido del terminal"""
        self.terminal_output.clear()
        self._show_welcome_message()
    
    def stop_current_process(self):
        """Detiene el proceso actual"""
        if self.current_process:
            self.current_process.terminate()
            self.current_process = None
            self.terminal_output.setTextColor(QColor("#FFFF00"))
            self.terminal_output.append("⏹️ Proceso detenido")
            self.terminal_output.setTextColor(QColor("#00FF00"))
            self.stop_btn.setEnabled(False)
    
    def eventFilter(self, obj, event):
        """Filtro de eventos para el historial de comandos"""
        if obj == self.command_input and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Up:
                self._navigate_history(-1)
                return True
            elif event.key() == Qt.Key.Key_Down:
                self._navigate_history(1)
                return True
            elif event.key() == Qt.Key.Key_L and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.clear_terminal()
                return True
                
        return super().eventFilter(obj, event)
    
    def _navigate_history(self, direction):
        """Navega por el historial de comandos"""
        if not self.history:
            return
            
        self.history_index += direction
        
        if self.history_index < 0:
            self.history_index = 0
        elif self.history_index >= len(self.history):
            self.history_index = len(self.history)
            self.command_input.clear()
            return
            
        if 0 <= self.history_index < len(self.history):
            self.command_input.setText(self.history[self.history_index])

    def execute_code_from_editor(self, code):
        """Ejecuta código Python enviado desde el editor"""
        # Cambiar al modo Python REPL si no está activado
        if "Python REPL" not in self.mode_combo.currentText():
            self.mode_combo.setCurrentText("🐍 Python REPL")
        
        # Mostrar el código que se va a ejecutar
        self.terminal_output.setTextColor(QColor("#FFFF00"))
        self.terminal_output.append("📝 Ejecutando código desde el editor:")
        self.terminal_output.setTextColor(QColor("#CCCCCC"))
        
        # Mostrar el código con numeración de líneas
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            self.terminal_output.append(f"{i:3d}: {line}")
        
        self.terminal_output.setTextColor(QColor("#FFFF00"))
        self.terminal_output.append("━━━ Salida del código ━━━")
        self.terminal_output.setTextColor(QColor("#00FF00"))
        
        # Ejecutar el código
        self._execute_python_command(code)
        
        # Auto-scroll al final
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.terminal_output.setTextCursor(cursor)


class CodeEditorViewPySide:
    """Vista principal del editor de código usando PySide6"""
    
    def __init__(self):
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)
        
        self.window = None
        self.input_text = None
        self.output_text = None
        self.clear_button = None
        self.save_button = None
        self.load_button = None
        self.syntax_highlighter = None
        self.current_file_path = None  # Para rastrear el archivo actual
        self.current_preferences = None  # Para mantener las preferencias actuales
        
        # Configuración de la bandeja del sistema
        self.tray_icon = None
        self.tray_menu = None
        self.is_minimized_to_tray = False
        
        # Inicializar gestor de sesiones
        self.session_manager = SessionManager(self)
        
        self._setup_ui()
        self._setup_system_tray()
        
        # Cargar preferencias guardadas
        self.load_saved_preferences()
        
        # Restaurar sesión después de configurar UI
        QTimer.singleShot(1000, self._restore_session_delayed)
    
    def _restore_session_delayed(self):
        """Restaura la sesión con un pequeño retraso para asegurar que la UI esté completamente cargada"""
        try:
            if hasattr(self, 'session_manager'):
                self.session_manager.restore_session()
        except Exception as e:
            print(f"⚠️ Error en restauración de sesión: {e}")
    
    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        self.window = QMainWindow()
        self.window.setWindowTitle(AppConfig.WINDOW_TITLE + " - PySide6")
        self.window.setGeometry(100, 100, 1000, 700)
        
        # Configurar el evento de cierre de ventana
        self.window.closeEvent = self._handle_close_event
        
        # Configurar menú
        self._create_menu()
        
        # Widget central
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)  # Márgenes más pequeños
        
        # Título con tamaño fijo
        title_label = QLabel("🐍 Editor de Código Python con Resaltado de Sintaxis")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2C3E50;
                padding: 8px;
                background-color: #ECF0F1;
                border-radius: 5px;
                margin-bottom: 5px;
                min-height: 35px;
                max-height: 35px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Splitter horizontal principal (explorador + editor) que ocupa el resto del espacio
        main_horizontal_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_horizontal_splitter, 1)  # stretch factor 1 para que ocupe todo el espacio restante
        
        # Crear widget contenedor para el explorador con su barra de herramientas
        self.explorer_container = QWidget()
        self.file_explorer_layout = QVBoxLayout(self.explorer_container)
        self.file_explorer_layout.setContentsMargins(0, 0, 0, 0)
        self.file_explorer_layout.setSpacing(0)
        
        # Explorador de archivos lateral
        self.file_explorer = FileExplorerWidget(self)
        
        # Agregar barra de herramientas si existe
        if hasattr(self.file_explorer, 'toolbar_widget'):
            self.file_explorer_layout.addWidget(self.file_explorer.toolbar_widget)
        
        # Agregar el explorador
        self.file_explorer_layout.addWidget(self.file_explorer)
        
        # Configurar el contenedor del explorador
        self.explorer_container.setMaximumWidth(AppConfig.FILE_EXPLORER_WIDTH)
        self.explorer_container.setMinimumWidth(200)
        main_horizontal_splitter.addWidget(self.explorer_container)
        
        # Widget derecho que contiene el editor y la salida
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        main_horizontal_splitter.addWidget(right_widget)
        
        # Splitter vertical para dividir entrada y salida
        splitter = QSplitter(Qt.Orientation.Vertical)
        right_layout.addWidget(splitter)
        
        # Frame para el área de entrada
        input_frame = QFrame()
        input_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        input_layout = QVBoxLayout(input_frame)
        
        # Label para área de entrada
        input_label = QLabel("📝 Código Python:")
        input_label.setStyleSheet("font-weight: bold; color: #34495E; font-size: 14px;")
        input_layout.addWidget(input_label)
        
        # Editor con pestañas
        self.tabbed_editor = TabbedCodeEditor(None)  # No pasar parent para evitar conflictos
        self.tabbed_editor.parent_editor = self  # Asignar referencia después
        input_layout.addWidget(self.tabbed_editor)
        
        # Mantener referencia al editor actual para compatibilidad
        self.input_text = self.tabbed_editor.get_current_editor()
        
        # Configurar resaltado de sintaxis para el editor inicial
        if self.input_text:
            self.syntax_highlighter = SyntaxHighlighterWithErrors(self.input_text.document())
            self.input_text.syntax_highlighter = self.syntax_highlighter  # Guardar referencia
        
        splitter.addWidget(input_frame)
        
        # Frame para botones
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        
        # Botón para ejecutar en terminal (ahora es el principal)
        self.execute_terminal_button = QPushButton("🚀 Ejecutar Código (Ctrl+Enter)")
        self.execute_terminal_button.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2ECC71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
        """)
        
        self.clear_button = QPushButton("🗑️ Limpiar (Ctrl+L)")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #EC7063;
            }
            QPushButton:pressed {
                background-color: #C0392B;
            }
        """)
        
        button_layout.addWidget(self.execute_terminal_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        input_layout.addWidget(button_frame)
        
        # Frame para el área de salida
        output_frame = QFrame()
        output_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        output_layout = QVBoxLayout(output_frame)
        
        # Label para área de características y terminal
        output_label = QLabel("🌟 Características y Terminal:")
        output_label.setStyleSheet("font-weight: bold; color: #34495E; font-size: 14px;")
        output_layout.addWidget(output_label)
        
        # Widget con pestañas para salida y terminal
        self.output_tabs = QTabWidget()
        self.output_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #BDC3C7;
                border-radius: 5px;
                background-color: #FAFAFA;
            }
            QTabBar::tab {
                background-color: #ECF0F1;
                color: #2C3E50;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                border: 1px solid #BDC3C7;
            }
            QTabBar::tab:selected {
                background-color: #3498DB;
                color: white;
                border-bottom: none;
            }
            QTabBar::tab:hover {
                background-color: #D5DBDB;
            }
        """)
        
        # Pestaña de salida/características
        self.output_text = QTextEdit()
        self.output_text.setFont(QFont("Consolas", 11))
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #FAFAFA;
                color: #2C3E50;
                border: none;
                padding: 10px;
            }
        """)
        
        # Contenido inicial con características del programa
        initial_content = """🌟 CARACTERÍSTICAS PRINCIPALES DEL EDITOR

📝 EDITOR DE CÓDIGO
• Pestañas múltiples: Trabaja con varios archivos simultáneamente
• Resaltado de sintaxis: Código Python con colores para mejor legibilidad
• Numeración de líneas: Referencia visual para debugging
• Formateo automático: Código limpio según estándares PEP 8

💻 TERMINAL INTEGRADO
• Python interactivo: Ejecuta código línea por línea
• Bash/Shell: Comandos del sistema operativo
• Input() interactivo: Soporte completo para entrada de usuario
• Aplicaciones gráficas: Ejecuta programas con interfaz gráfica

🔍 BÚSQUEDA AVANZADA
• Búsqueda simple: Encuentra texto en el archivo actual
• Buscar y reemplazar: Modifica texto de forma masiva
• Múltiples archivos: Busca en todo el proyecto

⚙️ PERSONALIZACIÓN
• Temas y colores: Personaliza la apariencia
• Fuentes: Cambia tipografía y tamaños
• Formatter: Configura herramientas de formateo

⌨️ ATAJOS DE TECLADO PRINCIPALES

🚀 EJECUCIÓN:
Ctrl + Enter → Ejecutar código en terminal
Ctrl + L → Limpiar salida del terminal

📁 ARCHIVOS:
Ctrl + O → Abrir archivo
Ctrl + S → Guardar archivo
Ctrl + T → Nueva pestaña
Ctrl + W → Cerrar pestaña

🔍 BÚSQUEDA:
Ctrl + F → Buscar en archivo actual
Ctrl + H → Buscar y reemplazar
Ctrl + Shift + F → Buscar en múltiples archivos

🔧 HERRAMIENTAS:
Ctrl + Alt + F → Formatear código
Ctrl + Alt + T → Abrir terminal del sistema
F2 → Mostrar documentación completa
F3 → Mostrar/ocultar explorador de archivos

💡 Consejo: Presiona F2 para acceder a la documentación completa con guías detalladas y tutoriales paso a paso.

────────────────────────────────────────────────────
La salida de ejecución de código aparecerá aquí."""
        
        self.output_text.setText(initial_content)
        self.output_tabs.addTab(self.output_text, "🌟 Características")
        
        # Pestaña del terminal integrado REAL
        self.integrated_terminal = IntegratedTerminalNew()
        self.output_tabs.addTab(self.integrated_terminal, "💻 Terminal")
        
        output_layout.addWidget(self.output_tabs)
        splitter.addWidget(output_frame)
        
        # Configurar proporciones del splitter
        splitter.setSizes([400, 200])
    
    def _handle_close_event(self, event, force_quit=False):
        """Maneja el evento de cierre de ventana"""
        try:
            # Si tenemos bandeja del sistema y no es un cierre forzado, minimizar a bandeja
            if (not force_quit and self.tray_icon and self.tray_icon.isVisible() and 
                QSystemTrayIcon.isSystemTrayAvailable()):
                
                if event:
                    event.ignore()  # Ignorar el evento de cierre
                
                self._minimize_to_tray()
                return
            
            # Si es un cierre forzado o no hay bandeja, cerrar completamente
            # Guardar configuraciones antes de cerrar
            if hasattr(self, 'input_text') and hasattr(self.input_text, 'preferences_settings'):
                self._save_settings(self.input_text.preferences_settings)
            
            # Guardar sesión antes de cerrar
            if hasattr(self, 'session_manager'):
                self.session_manager.save_session()
            
            # Limpiar terminal integrado y procesos
            if hasattr(self, 'integrated_terminal'):
                try:
                    # Terminar procesos activos del terminal
                    if hasattr(self.integrated_terminal, 'current_process') and self.integrated_terminal.current_process:
                        self.integrated_terminal.current_process.kill()
                        self.integrated_terminal.current_process.waitForFinished(1000)
                except:
                    pass
            
            # Ocultar el icono de la bandeja si existe
            if self.tray_icon:
                self.tray_icon.hide()
            
            # Aceptar el evento de cierre si existe
            if event:
                event.accept()
            
            # Limpiar hilos y recursos
            import threading
            
            # Esperar a que terminen los hilos no daemon
            for thread in threading.enumerate():
                if thread != threading.current_thread() and not thread.daemon:
                    try:
                        thread.join(timeout=1.0)  # Esperar máximo 1 segundo
                    except:
                        pass
            
            # Cerrar la aplicación de forma segura
            if self.app:
                self.app.quit()
                
        except Exception as e:
            print(f"Error en evento de cierre: {e}")
            if event:
                event.accept()  # Aceptar el cierre de todas formas
            if self.app:
                self.app.quit()
    
    def _cleanup_resources(self):
        """Limpia recursos antes del cierre"""
        try:
            # Limpiar terminal integrado
            if hasattr(self, 'integrated_terminal'):
                if hasattr(self.integrated_terminal, 'current_process') and self.integrated_terminal.current_process:
                    self.integrated_terminal.current_process.kill()
                    self.integrated_terminal.current_process.waitForFinished(1000)
            
            # Limpiar hilos activos (evitando daemon threads que causan el error)
            import threading
            for thread in threading.enumerate():
                if thread != threading.current_thread() and not thread.daemon and thread.is_alive():
                    try:
                        # No usar join() con daemon threads
                        thread.join(timeout=0.5)
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error en limpieza de recursos: {e}")
    
    def _create_menu(self):
        """Crea el menú superior de la aplicación"""
        menubar = self.window.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu("📁 Archivo")
        
        # Acción Abrir
        open_action = QAction("🔗 Abrir...", self.window)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Abrir archivo Python")
        file_menu.addAction(open_action)
        
        # Separador
        file_menu.addSeparator()
        
        # Acción Nueva Pestaña
        new_tab_action = QAction("📄 Nueva Pestaña", self.window)
        new_tab_action.setShortcut("Ctrl+T")
        new_tab_action.setStatusTip("Crear nueva pestaña")
        new_tab_action.triggered.connect(self.new_tab)
        file_menu.addAction(new_tab_action)
        
        # Acción Cerrar Pestaña
        close_tab_action = QAction("❌ Cerrar Pestaña", self.window)
        close_tab_action.setShortcut("Ctrl+W")
        close_tab_action.setStatusTip("Cerrar pestaña actual")
        close_tab_action.triggered.connect(self.close_current_tab)
        file_menu.addAction(close_tab_action)
        
        # Separador
        file_menu.addSeparator()
        
        # Acción Guardar
        save_action = QAction("💾 Guardar", self.window)
        save_action.setShortcut("Ctrl+S")
        save_action.setStatusTip("Guardar archivo actual")
        file_menu.addAction(save_action)
        
        # Acción Guardar Como
        save_as_action = QAction("📋 Guardar Como...", self.window)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.setStatusTip("Guardar archivo con nuevo nombre")
        file_menu.addAction(save_as_action)
        
        # Separador
        file_menu.addSeparator()
        
        # Acción Salir
        exit_action = QAction("🚪 Salir", self.window)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Salir del programa")
        file_menu.addAction(exit_action)
        
        # Menú Editar
        edit_menu = menubar.addMenu("⚙️ Editar")
        
        # Acción Formatear Código
        format_action = QAction("🔧 Formatear Código", self.window)
        format_action.setShortcut("Ctrl+Alt+F")
        format_action.setStatusTip("Formatear código actual según PEP 8")
        format_action.triggered.connect(self.format_current_code)
        edit_menu.addAction(format_action)
        
        edit_menu.addSeparator()
        
        # Acciones de Búsqueda
        find_action = QAction("🔍 Buscar...", self.window)
        find_action.setShortcut("Ctrl+F")
        find_action.setStatusTip("Buscar texto en el archivo actual")
        find_action.triggered.connect(self.show_find_dialog)
        edit_menu.addAction(find_action)
        
        find_replace_action = QAction("🔄 Buscar y Reemplazar...", self.window)
        find_replace_action.setShortcut("Ctrl+H")
        find_replace_action.setStatusTip("Buscar y reemplazar texto en el archivo actual")
        find_replace_action.triggered.connect(self.show_find_replace_dialog)
        edit_menu.addAction(find_replace_action)
        
        find_in_files_action = QAction("🗂️ Buscar en Archivos...", self.window)
        find_in_files_action.setShortcut("Ctrl+Shift+F")
        find_in_files_action.setStatusTip("Buscar texto en múltiples archivos")
        find_in_files_action.triggered.connect(self.show_multi_file_search_dialog)
        edit_menu.addAction(find_in_files_action)
        
        edit_menu.addSeparator()
        
        # Acción Preferencias
        preferences_action = QAction("🎨 Preferencias...", self.window)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.setStatusTip("Configurar preferencias del editor")
        edit_menu.addAction(preferences_action)
        
        # Menú Sesión
        session_menu = menubar.addMenu("💾 Sesión")
        
        # Acción Guardar Sesión
        save_session_action = QAction("💾 Guardar Sesión", self.window)
        save_session_action.setShortcut("Ctrl+Shift+S")
        save_session_action.setStatusTip("Guardar estado actual de la sesión")
        save_session_action.triggered.connect(self._save_session_manual)
        session_menu.addAction(save_session_action)
        
        # Acción Restaurar Sesión
        restore_session_action = QAction("🔄 Restaurar Sesión", self.window)
        restore_session_action.setShortcut("Ctrl+Shift+R")
        restore_session_action.setStatusTip("Restaurar última sesión guardada")
        restore_session_action.triggered.connect(self._restore_session_manual)
        session_menu.addAction(restore_session_action)
        
        session_menu.addSeparator()
        
        # Acción Archivos Recientes
        recent_files_action = QAction("📋 Archivos Recientes", self.window)
        recent_files_action.setStatusTip("Ver archivos abiertos recientemente")
        recent_files_action.triggered.connect(self._show_recent_files)
        session_menu.addAction(recent_files_action)
        
        session_menu.addSeparator()
        
        # Acción Limpiar Sesión
        clear_session_action = QAction("🗑️ Limpiar Sesión", self.window)
        clear_session_action.setStatusTip("Eliminar datos de sesión guardados")
        clear_session_action.triggered.connect(self._clear_session_manual)
        session_menu.addAction(clear_session_action)
        
        # Menú Vista
        view_menu = menubar.addMenu("👁️ Vista")
        
        # Acción Toggle Explorador de Archivos
        toggle_explorer_action = QAction("📁 Explorador de Archivos", self.window)
        toggle_explorer_action.setShortcut("F3")
        toggle_explorer_action.setStatusTip("Mostrar/Ocultar explorador de archivos")
        toggle_explorer_action.setCheckable(True)
        toggle_explorer_action.setChecked(True)  # Por defecto visible
        view_menu.addAction(toggle_explorer_action)
        
        # Separador
        view_menu.addSeparator()
        
        # Acción Abrir Terminal del Sistema
        open_system_terminal_action = QAction("🖥️ Abrir Terminal del Sistema", self.window)
        open_system_terminal_action.setShortcut("Ctrl+Alt+T")
        open_system_terminal_action.setStatusTip("Abrir terminal/cmd nativo del sistema operativo")
        open_system_terminal_action.triggered.connect(self.open_system_terminal)
        view_menu.addAction(open_system_terminal_action)
        
        # Menú Ayuda
        help_menu = menubar.addMenu("❓ Ayuda")
        
        # Acción Documentación
        documentation_action = QAction("📚 Documentación", self.window)
        documentation_action.setShortcut("F2")
        documentation_action.setStatusTip("Mostrar documentación de la aplicación")
        documentation_action.triggered.connect(self.show_documentation_dialog)
        help_menu.addAction(documentation_action)
        
        # Separador
        help_menu.addSeparator()
        
        # Acción About
        about_action = QAction("ℹ️ About", self.window)
        about_action.setShortcut("F1")
        about_action.setStatusTip("Información sobre la aplicación")
        help_menu.addAction(about_action)
        
        # Guardar referencias a las acciones para conectarlas después
        self.open_action = open_action
        self.save_action = save_action
        self.save_as_action = save_as_action
        self.exit_action = exit_action
        self.preferences_action = preferences_action
        self.toggle_explorer_action = toggle_explorer_action
        self.open_system_terminal_action = open_system_terminal_action
        self.documentation_action = documentation_action
        self.about_action = about_action
    
    def _setup_system_tray(self):
        """Configura la bandeja del sistema"""
        # Verificar si el sistema soporta bandeja del sistema
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.show_message("Bandeja del Sistema", 
                            "La bandeja del sistema no está disponible en este sistema.", 
                            "warning")
            return
        
        # Crear el icono de la bandeja
        try:
            # Intentar cargar el icono desde img/logo.png
            icon_path = "img/logo.png"
            icon = QIcon(icon_path)
            
            # Si no se puede cargar, usar un icono por defecto
            if icon.isNull():
                # Crear un icono simple usando texto
                pixmap = QPixmap(32, 32)
                pixmap.fill(QColor("#3498DB"))
                painter = QPainter(pixmap)
                painter.setPen(QColor("white"))
                painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
                painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Py")
                painter.end()
                icon = QIcon(pixmap)
            
            self.tray_icon = QSystemTrayIcon(icon, self.window)
            
        except Exception as e:
            print(f"Error cargando icono: {e}")
            # Crear icono por defecto
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor("#3498DB"))
            painter = QPainter(pixmap)
            painter.setPen(QColor("white"))
            painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "Py")
            painter.end()
            icon = QIcon(pixmap)
            self.tray_icon = QSystemTrayIcon(icon, self.window)
        
        # Crear el menú contextual de la bandeja
        self.tray_menu = QMenu()
        
        # Acción Restaurar
        restore_action = QAction("🔄 Restaurar", self.window)
        restore_action.triggered.connect(self._restore_from_tray)
        self.tray_menu.addAction(restore_action)
        
        # Separador
        self.tray_menu.addSeparator()
        
        # Acción Mostrar/Ocultar
        toggle_action = QAction("👁️ Mostrar/Ocultar", self.window)
        toggle_action.triggered.connect(self._toggle_window_visibility)
        self.tray_menu.addAction(toggle_action)
        
        # Separador
        self.tray_menu.addSeparator()
        
        # Acción Preferencias
        tray_preferences_action = QAction("🎨 Preferencias", self.window)
        tray_preferences_action.triggered.connect(self.show_preferences_dialog)
        self.tray_menu.addAction(tray_preferences_action)
        
        # Separador
        self.tray_menu.addSeparator()
        
        # Acción Salir
        quit_action = QAction("🚪 Salir", self.window)
        quit_action.triggered.connect(self._quit_application)
        self.tray_menu.addAction(quit_action)
        
        # Establecer el menú contextual
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # Configurar el tooltip
        self.tray_icon.setToolTip("Editor de Código Python")
        
        # Conectar el doble clic para restaurar la ventana
        self.tray_icon.activated.connect(self._tray_icon_activated)
        
        # Mostrar el icono en la bandeja
        self.tray_icon.show()
        
        # Mostrar mensaje de información
        self.tray_icon.showMessage(
            "Editor de Código Python",
            "La aplicación se ha iniciado en la bandeja del sistema.\nHaz doble clic en el icono para restaurar la ventana.",
            QSystemTrayIcon.MessageIcon.Information,
            3000  # 3 segundos
        )
    
    def _tray_icon_activated(self, reason):
        """Maneja los clics en el icono de la bandeja"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._restore_from_tray()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # En algunos sistemas, un solo clic también puede restaurar
            self._toggle_window_visibility()
    
    def _restore_from_tray(self):
        """Restaura la ventana desde la bandeja del sistema"""
        if self.window:
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()
            self.is_minimized_to_tray = False
    
    def _toggle_window_visibility(self):
        """Alterna la visibilidad de la ventana"""
        if self.window:
            if self.window.isVisible() and not self.window.isMinimized():
                self._minimize_to_tray()
            else:
                self._restore_from_tray()
    
    def _minimize_to_tray(self):
        """Minimiza la aplicación a la bandeja del sistema"""
        if self.window and self.tray_icon and self.tray_icon.isVisible():
            self.window.hide()
            self.is_minimized_to_tray = True
            
            # Mostrar mensaje solo la primera vez
            if not hasattr(self, '_first_minimize_shown'):
                self.tray_icon.showMessage(
                    "Editor de Código Python",
                    "La aplicación se ha minimizado a la bandeja del sistema.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
                self._first_minimize_shown = True
    
    def _quit_application(self):
        """Cierra completamente la aplicación"""
        # Ocultar el icono de la bandeja
        if self.tray_icon:
            self.tray_icon.hide()
        
        # Cerrar la aplicación
        self._handle_close_event(None, force_quit=True)
    
    def get_input_code(self):
        """Obtiene el código de entrada del editor activo"""
        current_editor = self.tabbed_editor.get_current_editor()
        if current_editor:
            return current_editor.toPlainText().strip()
        return ""
    
    def set_output(self, output_text, is_error=False):
        """Establece el texto en el área de salida"""
        self.output_text.clear()
        if is_error:
            self.output_text.setStyleSheet("""
                QTextEdit {
                    background-color: #FADBD8;
                    color: #C0392B;
                    border: 2px solid #E74C3C;
                    border-radius: 5px;
                    padding: 10px;
                    font-weight: bold;
                }
            """)
        else:
            # Aplicar configuraciones guardadas o defaults para salida normal
            self._apply_output_styles()
        self.output_text.setText(output_text)
    
    def append_output(self, text, is_error=False):
        """Añade texto al área de salida"""
        if is_error:
            # Para errores, cambiar estilo temporalmente
            current_text = self.output_text.toPlainText()
            self.set_output(current_text + text, is_error=True)
        else:
            # Asegurar que se mantengan los estilos guardados
            self._apply_output_styles()
            self.output_text.append(text)
    
    def clear_input(self):
        """Limpia el área de entrada del editor activo"""
        current_editor = self.tabbed_editor.get_current_editor()
        if current_editor:
            current_editor.clear()
    
    def clear_output(self):
        """Limpia el área de salida"""
        self.output_text.clear()
        # Aplicar configuraciones guardadas
        self._apply_output_styles()
    
    def show_message(self, title, message, message_type="info"):
        """Muestra un mensaje emergente"""
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if message_type == "error":
            msg_box.setIcon(QMessageBox.Icon.Critical)
        elif message_type == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        else:
            msg_box.setIcon(QMessageBox.Icon.Information)
        
        msg_box.exec()
    
    def show_confirmation(self, title, message):
        """Muestra un diálogo de confirmación"""
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        result = msg_box.exec()
        return result == QMessageBox.StandardButton.Yes
    
    def set_button_command(self, button_name, command):
        """Establece el comando para un botón específico"""
        if button_name == "execute" or button_name == "execute_terminal":
            # Ambos nombres mapean al mismo botón ahora
            self.execute_terminal_button.clicked.connect(command)
        elif button_name == "clear":
            self.clear_button.clicked.connect(command)
    
    def set_menu_commands(self, open_callback, save_callback, save_as_callback, exit_callback, preferences_callback, about_callback):
        """Establece los comandos para las acciones del menú"""
        self.open_action.triggered.connect(open_callback)
        self.save_action.triggered.connect(save_callback)
        self.save_as_action.triggered.connect(save_as_callback)
        self.exit_action.triggered.connect(exit_callback)
        self.preferences_action.triggered.connect(preferences_callback)
        self.toggle_explorer_action.triggered.connect(self.toggle_file_explorer)
        self.about_action.triggered.connect(about_callback)
    
    def open_file_dialog(self):
        """Abre un diálogo para seleccionar archivo Python"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self.window,
            "Abrir archivo Python",
            "",
            "Archivos Python (*.py);;Todos los archivos (*)"
        )
        return file_path
    
    def save_file_dialog(self):
        """Abre un diálogo para guardar archivo Python"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self.window,
            "Guardar archivo Python",
            "",
            "Archivos Python (*.py);;Todos los archivos (*)"
        )
        return file_path
    
    def load_file_content(self, file_path):
        """Carga el contenido de un archivo en una nueva pestaña"""
        try:
            # Verificar que el archivo existe
            if not os.path.isfile(file_path):
                self.show_message("Error", f"El archivo no existe:\n{file_path}", "error")
                return False
            
            # Cargar archivo en el sistema de pestañas
            tab_index = self.tabbed_editor.load_file_in_tab(file_path)
            if tab_index is not None:
                # Actualizar referencia al editor actual
                self.input_text = self.tabbed_editor.get_current_editor()
                self.current_file_path = file_path
                
                # Actualizar título de ventana
                filename = os.path.basename(file_path)
                self.window.setWindowTitle(f"{AppConfig.WINDOW_TITLE} - {filename}")
                
                # Mostrar mensaje de confirmación
                self.show_message("Archivo Cargado", f"Archivo '{filename}' cargado correctamente.", "info")
                return True
            
            return False
                
        except Exception as e:
            self.show_message("Error", f"No se pudo abrir el archivo:\n{str(e)}", "error")
            return False
    
    def save_file_content(self, file_path=None):
        """Guarda el contenido del editor en un archivo usando el sistema de pestañas"""
        result = self.tabbed_editor.save_current_tab()
        if result:
            # Actualizar referencia al archivo actual
            self.current_file_path = self.tabbed_editor.get_current_file_path()
            # Actualizar el título de la ventana
            if self.current_file_path:
                filename = os.path.basename(self.current_file_path)
                self.window.setWindowTitle(f"{AppConfig.WINDOW_TITLE} - {filename}")
        return result
    
    def get_current_file_path(self):
        """Obtiene la ruta del archivo actual"""
        return self.current_file_path
    
    def has_unsaved_changes(self):
        """Verifica si hay cambios sin guardar usando el sistema de pestañas"""
        # Verificar si alguna pestaña tiene cambios sin guardar
        for tab_data in self.tabbed_editor.tab_data.values():
            if tab_data.is_modified:
                return True
        return False
    
    def show_about_dialog(self):
        """Muestra la ventana About"""
        about_dialog = AboutDialog(self.window)
        about_dialog.exec()
    
    def show_documentation_dialog(self):
        """Muestra la ventana de documentación"""
        doc_dialog = DocumentationDialog(self.window)
        doc_dialog.exec()
    
    def show_preferences_dialog(self):
        """Muestra la ventana de preferencias"""
        current_settings = self._get_current_settings()
        preferences_dialog = PreferencesDialog(self.window, current_settings)
        preferences_dialog.parent_editor = self  # Establecer referencia al editor
        if preferences_dialog.exec() == QDialog.DialogCode.Accepted:
            new_settings = preferences_dialog.get_new_settings()
            self.apply_preferences(new_settings)  # Ya no pasamos False, que guardará automáticamente
    
    def _get_current_settings(self):
        """Obtiene las configuraciones actuales del editor"""
        # Obtener configuraciones guardadas o usar defaults
        settings = QSettings("PythonEditor", "Preferences")
        
        # Valores por defecto
        defaults = {
            'editor_font_family': 'Consolas',
            'editor_font_size': 12,
            'editor_bg_color': '#2C3E50',
            'editor_text_color': '#ECF0F1',
            'editor_selection_color': '#3498DB',
            'line_number_bg_color': '#34495E',
            'line_number_text_color': '#BDC3C7',
            'output_font_family': 'Consolas',
            'output_font_size': 11,
            'output_bg_color': '#FAFAFA',
            'output_text_color': '#2C3E50'
        }
        
        # Cargar valores guardados o usar defaults
        current_settings = {}
        for key, default_value in defaults.items():
            stored_value = settings.value(key, default_value)
            
            # Asegurar tipo correcto para tamaños de fuente
            if 'font_size' in key:
                try:
                    current_settings[key] = int(stored_value)
                except (ValueError, TypeError):
                    current_settings[key] = default_value
            else:
                current_settings[key] = stored_value
        
        return current_settings
    
    def _save_settings(self, settings_dict):
        """Guarda las configuraciones"""
        settings = QSettings("PythonEditor", "Preferences")
        
        # Guardar cada configuración
        for key, value in settings_dict.items():
            settings.setValue(key, value)
        
        # Asegurar que se escriban los datos al disco
        settings.sync()
        
        return True
    
    def _apply_output_styles(self):
        """Aplica los estilos guardados al área de salida"""
        # Usar configuraciones cacheadas o cargar desde QSettings
        if self.current_preferences:
            settings = self.current_preferences
        else:
            settings = self._get_current_settings()
            self.current_preferences = settings
        
        # Aplicar fuente del área de salida
        output_font = QFont(settings['output_font_family'], settings['output_font_size'])
        self.output_text.setFont(output_font)
        
        # Aplicar colores del área de salida
        output_style = f"""
            QTextEdit {{
                background-color: {settings['output_bg_color']};
                color: {settings['output_text_color']};
                border: 2px solid #BDC3C7;
                border-radius: 5px;
                padding: 10px;
            }}
        """
        self.output_text.setStyleSheet(output_style)
        
        # Aplicar configuraciones al terminal integrado si existe
        if hasattr(self, 'integrated_terminal'):
            # Aplicar fuente al terminal
            terminal_font = QFont(
                settings.get('editor_font_family', 'Consolas'), 
                settings.get('editor_font_size', 11)
            )
            self.integrated_terminal.terminal_output.setFont(terminal_font)
            self.integrated_terminal.command_input.setFont(terminal_font)
            
            # Aplicar colores basados en el tema del editor
            terminal_bg_color = settings.get('editor_bg_color', '#1E1E1E')
            terminal_text_color = settings.get('editor_text_color', '#D4D4D4')
            
            terminal_style = f"""
                QTextEdit {{
                    background-color: {terminal_bg_color};
                    color: #00FF00;
                    border: 1px solid #333;
                    border-radius: 3px;
                    font-family: 'Consolas', 'Courier New', monospace;
                    selection-background-color: #264F78;
                }}
                QLineEdit {{
                    background-color: {terminal_bg_color};
                    color: {terminal_text_color};
                    border: 1px solid #3F3F46;
                    border-radius: 3px;
                    padding: 5px;
                    font-family: 'Consolas', 'Courier New', monospace;
                }}
                QLineEdit:focus {{
                    border-color: #007ACC;
                }}
            """
            self.integrated_terminal.terminal_output.setStyleSheet(terminal_style)
            self.integrated_terminal.command_input.setStyleSheet(terminal_style)
    
    def _clear_settings(self):
        """Limpia todas las configuraciones guardadas (para debugging)"""
        settings = QSettings("PythonEditor", "Preferences")
        settings.clear()
        settings.sync()
        print("🗑️ Configuraciones limpiadas")
    
    def _debug_settings(self):
        """Muestra todas las configuraciones guardadas (para debugging)"""
        settings = QSettings("PythonEditor", "Preferences")
        print("🔍 Configuraciones actuales:")
        for key in settings.allKeys():
            value = settings.value(key)
            print(f"   {key}: {value} (tipo: {type(value)})")
        print(f"📁 Archivo de configuración: {settings.fileName()}")
    
    def apply_preferences(self, settings_dict, preview=False):
        """Aplica las preferencias al editor"""
        # Actualizar preferencias cacheadas
        self.current_preferences = settings_dict.copy()
        
        # Aplicar fuente del editor
        editor_font = QFont(settings_dict['editor_font_family'], settings_dict['editor_font_size'])
        self.input_text.setFont(editor_font)
        
        # Aplicar estilos del editor
        editor_style = f"""
            QPlainTextEdit {{
                background-color: {settings_dict['editor_bg_color']};
                color: {settings_dict['editor_text_color']};
                border: 2px solid #34495E;
                border-radius: 5px;
                padding: 10px;
                line-height: 1.2;
                selection-background-color: {settings_dict['editor_selection_color']};
            }}
        """
        self.input_text.setStyleSheet(editor_style)
        
        # Aplicar tema a todos los editores de pestañas si existe el widget de pestañas
        if hasattr(self, 'tab_widget'):
            for i in range(self.tab_widget.count()):
                editor = self.tab_widget.widget(i)
                if hasattr(editor, 'syntax_highlighter'):
                    # Preparar configuraciones de tema
                    theme_settings = {
                        'syntax_colors': settings_dict.get('syntax_colors', {}),
                        'editor_colors': settings_dict.get('editor_colors', {}),
                        'font_settings': settings_dict.get('font_settings', {})
                    }
                    
                    # Actualizar resaltador de sintaxis con nuevo tema
                    editor.syntax_highlighter.update_theme(theme_settings)
                    
                    # Aplicar estilos del editor a la pestaña
                    tab_editor_style = f"""
                        QPlainTextEdit {{
                            background-color: {settings_dict.get('editor_bg_color', '#2C3E50')};
                            color: {settings_dict.get('editor_text_color', '#ECF0F1')};
                            border: 1px solid #34495E;
                            border-radius: 3px;
                            selection-background-color: {settings_dict.get('editor_selection_color', '#3498DB')};
                        }}
                    """
                    editor.setStyleSheet(tab_editor_style)
                    
                    # Aplicar fuente
                    tab_font = QFont(
                        settings_dict.get('editor_font_family', 'Consolas'), 
                        settings_dict.get('editor_font_size', 12)
                    )
                    editor.setFont(tab_font)
        
        # Actualizar colores de numeración de líneas
        if hasattr(self.input_text, 'preferences_settings'):
            self.input_text.preferences_settings = settings_dict
        else:
            # Agregar las configuraciones al editor para que las use en el pintado
            self.input_text.preferences_settings = settings_dict
        
        # Forzar repintado del área de numeración
        if hasattr(self.input_text, 'lineNumberArea'):
            self.input_text.lineNumberArea.update()
        
        # Aplicar fuente y estilos del área de salida
        output_font = QFont(settings_dict['output_font_family'], settings_dict['output_font_size'])
        self.output_text.setFont(output_font)
        
        output_style = f"""
            QTextEdit {{
                background-color: {settings_dict['output_bg_color']};
                color: {settings_dict['output_text_color']};
                border: 2px solid #BDC3C7;
                border-radius: 5px;
                padding: 10px;
            }}
        """
        self.output_text.setStyleSheet(output_style)
        
        # Guardar las configuraciones si no es solo una vista previa
        if not preview:
            self._save_settings(settings_dict)
            self.show_message("Preferencias", "✅ Preferencias aplicadas y guardadas correctamente", "info")
    
    def _apply_auto_formatting(self, code):
        """Aplica formateo automático al código si está habilitado"""
        try:
            # Verificar si el formatter está habilitado
            settings = self._get_current_settings()
            if not settings.get('formatter_enabled', True):
                return code
            
            # Solo formatear si auto-format al guardar está habilitado
            if not settings.get('formatter_auto_save', False):
                return code
            
            # Importar y usar el formatter
            from utils.code_formatter import code_formatter
            
            # Configurar el formatter según las preferencias
            formatter = code_formatter
            formatter.config.FORMATTER_MAX_LINE_LENGTH = settings.get('formatter_line_length', 88)
            formatter.config.FORMATTER_INDENT_SIZE = settings.get('formatter_indent_size', 4)
            formatter.config.FORMATTER_USE_TABS = settings.get('formatter_use_tabs', False)
            formatter.config.FORMATTER_ORGANIZE_IMPORTS = settings.get('formatter_organize_imports', True)
            formatter.config.FORMATTER_REMOVE_TRAILING_WHITESPACE = settings.get('formatter_remove_trailing', True)
            formatter.config.FORMATTER_ADD_FINAL_NEWLINE = settings.get('formatter_final_newline', True)
            formatter.config.FORMATTER_AUTO_SPACING = settings.get('formatter_auto_spacing', True)
            
            # Determinar motor de formateo
            engine_map = {0: 'manual', 1: 'autopep8', 2: 'black'}
            engine_index = settings.get('formatter_engine_index', 1)
            engine = engine_map.get(engine_index, 'autopep8')
            
            # Aplicar formateo
            formatted_code = formatter.format_code(code, engine)
            
            return formatted_code
            
        except Exception as e:
            print(f"Error en formateo automático: {e}")
            return code  # Devolver código original si hay error
    
    def format_current_code(self):
        """Formatea el código actual manualmente (desde menú o atajo)"""
        try:
            current_editor = None
            
            # Obtener editor actual
            if hasattr(self, 'tab_widget') and self.tab_widget.count() > 0:
                current_editor = self.tab_widget.currentWidget()
            elif hasattr(self, 'input_text'):
                current_editor = self.input_text
            
            if not current_editor:
                self.show_message("Error", "❌ No hay código para formatear", "error")
                return
            
            # Obtener código actual
            original_code = current_editor.toPlainText()
            if not original_code.strip():
                self.show_message("Información", "📝 No hay código para formatear", "info")
                return
            
            # Aplicar formateo forzado (ignorar configuración auto-save)
            settings = self._get_current_settings()
            
            from utils.code_formatter import code_formatter
            
            # Configurar el formatter
            formatter = code_formatter
            formatter.config.FORMATTER_MAX_LINE_LENGTH = settings.get('formatter_line_length', 88)
            formatter.config.FORMATTER_INDENT_SIZE = settings.get('formatter_indent_size', 4)
            formatter.config.FORMATTER_USE_TABS = settings.get('formatter_use_tabs', False)
            formatter.config.FORMATTER_ORGANIZE_IMPORTS = settings.get('formatter_organize_imports', True)
            formatter.config.FORMATTER_REMOVE_TRAILING_WHITESPACE = settings.get('formatter_remove_trailing', True)
            formatter.config.FORMATTER_ADD_FINAL_NEWLINE = settings.get('formatter_final_newline', True)
            formatter.config.FORMATTER_AUTO_SPACING = settings.get('formatter_auto_spacing', True)
            
            # Determinar motor de formateo
            engine_map = {0: 'manual', 1: 'autopep8', 2: 'black'}
            engine_index = settings.get('formatter_engine_index', 1)
            engine = engine_map.get(engine_index, 'autopep8')
            
            # Aplicar formateo
            formatted_code = formatter.format_code(original_code, engine)
            
            # Verificar si hubo cambios
            if formatted_code == original_code:
                self.show_message("Formatter", "✅ El código ya está correctamente formateado", "info")
                return
            
            # Aplicar código formateado
            cursor = current_editor.textCursor()
            position = cursor.position()
            
            current_editor.setPlainText(formatted_code)
            
            # Restaurar posición del cursor (aproximadamente)
            cursor.setPosition(min(position, len(formatted_code)))
            current_editor.setTextCursor(cursor)
            
            # Marcar como modificado si es pestaña
            if hasattr(self, 'tab_widget'):
                current_index = self.tab_widget.currentIndex()
                if hasattr(self, 'tabbed_editor') and current_index >= 0:
                    if current_index in self.tabbed_editor.tab_data:
                        self.tabbed_editor.tab_data[current_index].is_modified = True
                        self.tabbed_editor.update_tab_title(current_index)
            
            self.show_message("Formatter", "✅ Código formateado exitosamente", "info")
            
        except Exception as e:
            self.show_message("Error", f"❌ Error formateando código: {e}", "error")
    
    def execute_code_in_terminal(self):
        """Ejecuta el código actual en el terminal integrado"""
        try:
            # Obtener el código del editor actual
            current_editor = None
            
            # Obtener editor actual
            if hasattr(self, 'tab_widget') and self.tab_widget.count() > 0:
                current_editor = self.tab_widget.currentWidget()
            elif hasattr(self, 'input_text'):
                current_editor = self.input_text
            
            if not current_editor:
                self.show_message("Error", "❌ No hay código para ejecutar", "error")
                return
            
            # Obtener código actual
            code = current_editor.toPlainText()
            if not code.strip():
                self.show_message("Información", "📝 No hay código para ejecutar", "info")
                return
            
            # Cambiar a la pestaña del terminal
            if hasattr(self, 'output_tabs'):
                # Buscar la pestaña del terminal
                for i in range(self.output_tabs.count()):
                    if "Terminal" in self.output_tabs.tabText(i):
                        self.output_tabs.setCurrentIndex(i)
                        break
            
            # Ejecutar código en el terminal integrado
            if hasattr(self, 'integrated_terminal'):
                self.integrated_terminal.execute_code_from_editor(code)
            else:
                self.show_message("Error", "❌ Terminal no disponible", "error")
                
        except Exception as e:
            self.show_message("Error", f"❌ Error ejecutando código en terminal: {e}", "error")
    
    def load_saved_preferences(self):
        """Carga las preferencias guardadas al iniciar"""
        settings = self._get_current_settings()
        
        # Aplicar todas las configuraciones sin mostrar mensaje
        self.apply_preferences(settings, preview=True)
        
        # Asegurar que los estilos se apliquen correctamente al área de salida
        self._apply_output_styles()
        
        # Forzar actualización del área de numeración de líneas
        if hasattr(self.input_text, 'lineNumberArea'):
            self.input_text.lineNumberArea.update()
    
    def set_key_bindings(self, execute_callback, clear_callback):
        """Configura los atajos de teclado"""
        from PySide6.QtGui import QShortcut, QKeySequence
        
        # Ctrl+Enter para ejecutar en terminal (comportamiento unificado)
        execute_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self.window)
        execute_shortcut.activated.connect(self.execute_code_in_terminal)
        
        # Ctrl+L para limpiar
        clear_shortcut = QShortcut(QKeySequence("Ctrl+L"), self.window)
        clear_shortcut.activated.connect(clear_callback)
        
        # Ctrl+Alt+F para formatear código
        format_shortcut = QShortcut(QKeySequence("Ctrl+Alt+F"), self.window)
        format_shortcut.activated.connect(self.format_current_code)
        
        # Ctrl+` para alternar terminal
        terminal_shortcut = QShortcut(QKeySequence("Ctrl+`"), self.window)
        terminal_shortcut.activated.connect(self.toggle_terminal)
        
        # Ctrl+Alt+T para abrir terminal del sistema
        system_terminal_shortcut = QShortcut(QKeySequence("Ctrl+Alt+T"), self.window)
        system_terminal_shortcut.activated.connect(self.open_system_terminal)
        
        # F3 para buscar siguiente (cuando hay diálogo de búsqueda abierto)
        find_next_shortcut = QShortcut(QKeySequence("F3"), self.window)
        find_next_shortcut.activated.connect(self._find_next_global)
        
        # Shift+F3 para buscar anterior
        find_prev_shortcut = QShortcut(QKeySequence("Shift+F3"), self.window)
        find_prev_shortcut.activated.connect(self._find_prev_global)
    
    def toggle_terminal(self):
        """Alterna entre la pestaña de salida y terminal"""
        try:
            if hasattr(self, 'output_tabs'):
                current_index = self.output_tabs.currentIndex()
                # Alternar entre pestaña 0 (Salida) y pestaña 1 (Terminal)
                new_index = 1 if current_index == 0 else 0
                self.output_tabs.setCurrentIndex(new_index)
                
                # Enfocar el terminal si se cambia a él
                if new_index == 1 and hasattr(self, 'integrated_terminal'):
                    self.integrated_terminal.command_input.setFocus()
        except Exception as e:
            print(f"Error alternando terminal: {e}")
    
    def _save_session_manual(self):
        """Guarda la sesión manualmente desde el menú"""
        try:
            if hasattr(self, 'session_manager'):
                self.session_manager.save_session()
                self.show_message("Sesión", "💾 Sesión guardada exitosamente", "info")
            else:
                self.show_message("Error", "❌ Gestor de sesiones no disponible", "error")
        except Exception as e:
            self.show_message("Error", f"❌ Error guardando sesión: {e}", "error")
    
    def _restore_session_manual(self):
        """Restaura la sesión manualmente desde el menú"""
        try:
            if hasattr(self, 'session_manager'):
                # Preguntar confirmación si hay archivos abiertos
                if hasattr(self, 'tab_widget') and self.tab_widget.count() > 0:
                    reply = QMessageBox.question(
                        self.window,
                        "Restaurar Sesión",
                        "¿Desea cerrar los archivos actuales y restaurar la sesión guardada?\n\n"
                        "Los cambios no guardados se perderán.",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.No:
                        return
                
                success = self.session_manager.restore_session()
                if success:
                    self.show_message("Sesión", "🔄 Sesión restaurada exitosamente", "info")
                else:
                    self.show_message("Información", "📝 No hay sesión previa para restaurar", "info")
            else:
                self.show_message("Error", "❌ Gestor de sesiones no disponible", "error")
        except Exception as e:
            self.show_message("Error", f"❌ Error restaurando sesión: {e}", "error")
    
    def _show_recent_files(self):
        """Muestra un diálogo con archivos recientes"""
        try:
            if not hasattr(self, 'session_manager'):
                self.show_message("Error", "❌ Gestor de sesiones no disponible", "error")
                return
            
            recent_files = self.session_manager.get_recent_files()
            
            if not recent_files:
                self.show_message("Información", "📝 No hay archivos recientes", "info")
                return
            
            # Crear diálogo de archivos recientes
            dialog = QDialog(self.window)
            dialog.setWindowTitle("📋 Archivos Recientes")
            dialog.setModal(True)
            dialog.resize(500, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Etiqueta
            label = QLabel("Selecciona un archivo para abrir:")
            label.setStyleSheet("font-weight: bold; margin: 10px;")
            layout.addWidget(label)
            
            # Lista de archivos
            files_list = QListWidget()
            files_list.setStyleSheet("""
                QListWidget {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    padding: 5px;
                }
                QListWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #eee;
                }
                QListWidget::item:selected {
                    background-color: #3498DB;
                    color: white;
                }
                QListWidget::item:hover {
                    background-color: #ecf0f1;
                }
            """)
            
            for file_info in recent_files:
                item = QListWidgetItem(f"📄 {file_info['name']}")
                item.setData(Qt.ItemDataRole.UserRole, file_info['path'])
                item.setToolTip(f"Ruta: {file_info['path']}\nÚltima sesión: {file_info['timestamp']}")
                files_list.addItem(item)
            
            layout.addWidget(files_list)
            
            # Botones
            buttons_layout = QHBoxLayout()
            
            open_button = QPushButton("📂 Abrir")
            open_button.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
            """)
            
            cancel_button = QPushButton("❌ Cancelar")
            cancel_button.setStyleSheet("""
                QPushButton {
                    background-color: #95A5A6;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #7F8C8D;
                }
            """)
            
            def open_selected_file():
                current_item = files_list.currentItem()
                if current_item:
                    file_path = current_item.data(Qt.ItemDataRole.UserRole)
                    if file_path and os.path.exists(file_path):
                        self._open_file_in_new_tab(file_path)
                        dialog.accept()
                    else:
                        self.show_message("Error", "❌ El archivo ya no existe", "error")
            
            def on_double_click(item):
                file_path = item.data(Qt.ItemDataRole.UserRole)
                if file_path and os.path.exists(file_path):
                    self._open_file_in_new_tab(file_path)
                    dialog.accept()
            
            open_button.clicked.connect(open_selected_file)
            cancel_button.clicked.connect(dialog.reject)
            files_list.itemDoubleClicked.connect(on_double_click)
            
            buttons_layout.addWidget(open_button)
            buttons_layout.addWidget(cancel_button)
            layout.addLayout(buttons_layout)
            
            dialog.exec()
            
        except Exception as e:
            self.show_message("Error", f"❌ Error mostrando archivos recientes: {e}", "error")
    
    def _clear_session_manual(self):
        """Limpia la sesión manualmente desde el menú"""
        try:
            reply = QMessageBox.question(
                self.window,
                "Limpiar Sesión",
                "¿Está seguro de que desea eliminar todos los datos de sesión guardados?\n\n"
                "Esta acción no se puede deshacer.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                if hasattr(self, 'session_manager'):
                    self.session_manager.clear_session()
                    self.show_message("Sesión", "🗑️ Datos de sesión eliminados", "info")
                else:
                    self.show_message("Error", "❌ Gestor de sesiones no disponible", "error")
        except Exception as e:
            self.show_message("Error", f"❌ Error limpiando sesión: {e}", "error")
    
    def _open_file_in_new_tab(self, file_path):
        """Abre un archivo en una nueva pestaña"""
        try:
            if not os.path.exists(file_path):
                self.show_message("Error", f"❌ El archivo no existe: {file_path}", "error")
                return
            
            # Leer contenido del archivo
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Crear nueva pestaña
            if hasattr(self, 'tab_widget'):
                self.tab_widget.new_tab(file_path, content)
                self.show_message("Archivo", f"📂 Archivo abierto: {os.path.basename(file_path)}", "info")
            
        except Exception as e:
            self.show_message("Error", f"❌ Error abriendo archivo: {e}", "error")
    
    def run(self):
        """Inicia el bucle principal de la aplicación"""
        try:
            self.window.show()
            return self.app.exec()
        except Exception as e:
            print(f"Error en bucle principal: {e}")
            return 1
        finally:
            # Asegurar limpieza al salir
            try:
                if self.app:
                    self.app.quit()
            except:
                pass
    
    def destroy(self):
        """Cierra la ventana y la aplicación de forma segura"""
        try:
            # Guardar configuraciones antes de cerrar
            if hasattr(self, 'input_text') and hasattr(self.input_text, 'preferences_settings'):
                self._save_settings(self.input_text.preferences_settings)
            
            # Ocultar el icono de la bandeja
            if self.tray_icon:
                self.tray_icon.hide()
            
            # Cerrar la ventana principal
            if self.window:
                self.window.close()
            
            # Salir de la aplicación
            if self.app:
                self.app.quit()
                
        except Exception as e:
            print(f"Error al cerrar aplicación: {e}")
            # Fallback: forzar salida
            if self.app:
                self.app.exit(0)
    
    def toggle_file_explorer(self):
        """Alterna la visibilidad del explorador de archivos"""
        if self.explorer_container.isVisible():
            self.explorer_container.hide()
            self.toggle_explorer_action.setChecked(False)
        else:
            self.explorer_container.show()
            self.toggle_explorer_action.setChecked(True)
    
    def show_find_dialog(self):
        """Mostrar diálogo de búsqueda"""
        if not hasattr(self, 'find_dialog') or not self.find_dialog:
            self.find_dialog = SearchReplaceDialog(self.window, "find")
            # Establecer referencia al editor principal
            self.find_dialog.parent_editor = self
        
        # Si hay texto seleccionado, usarlo como búsqueda inicial
        if self.input_text and self.input_text.textCursor().hasSelection():
            selected_text = self.input_text.textCursor().selectedText()
            self.find_dialog.set_search_text(selected_text)
        
        self.find_dialog.show()
        self.find_dialog.raise_()
        self.find_dialog.activateWindow()
    
    def show_find_replace_dialog(self):
        """Mostrar diálogo de búsqueda y reemplazo"""
        if not hasattr(self, 'replace_dialog') or not self.replace_dialog:
            self.replace_dialog = SearchReplaceDialog(self.window, "replace")
            # Establecer referencia al editor principal
            self.replace_dialog.parent_editor = self
        
        # Si hay texto seleccionado, usarlo como búsqueda inicial
        if self.input_text and self.input_text.textCursor().hasSelection():
            selected_text = self.input_text.textCursor().selectedText()
            self.replace_dialog.set_search_text(selected_text)
        
        self.replace_dialog.show()
        self.replace_dialog.raise_()
        self.replace_dialog.activateWindow()
    
    def show_multi_file_search_dialog(self):
        """Mostrar diálogo de búsqueda en múltiples archivos"""
        if not hasattr(self, 'multi_search_dialog') or not self.multi_search_dialog:
            self.multi_search_dialog = MultiFileSearchDialog(self.window)
            # Establecer referencia al editor principal
            self.multi_search_dialog.parent_editor = self
        
        # Si hay texto seleccionado, usarlo como búsqueda inicial
        if self.input_text and self.input_text.textCursor().hasSelection():
            selected_text = self.input_text.textCursor().selectedText()
            self.multi_search_dialog.search_input.setText(selected_text)
        
        self.multi_search_dialog.show()
        self.multi_search_dialog.raise_()
        self.multi_search_dialog.activateWindow()
    
    def _find_next_global(self):
        """Buscar siguiente con F3 (global)"""
        if hasattr(self, 'find_dialog') and self.find_dialog and self.find_dialog.isVisible():
            self.find_dialog._find_next()
        elif hasattr(self, 'replace_dialog') and self.replace_dialog and self.replace_dialog.isVisible():
            self.replace_dialog._find_next()
    
    def _find_prev_global(self):
        """Buscar anterior con Shift+F3 (global)"""
        if hasattr(self, 'find_dialog') and self.find_dialog and self.find_dialog.isVisible():
            self.find_dialog._find_previous()
        elif hasattr(self, 'replace_dialog') and self.replace_dialog and self.replace_dialog.isVisible():
            self.replace_dialog._find_previous()
    
    def new_tab(self):
        """Crea una nueva pestaña"""
        self.tabbed_editor.new_tab()
        # Actualizar referencia al editor actual
        self.input_text = self.tabbed_editor.get_current_editor()
    
    def close_current_tab(self):
        """Cierra la pestaña actual"""
        current_index = self.tabbed_editor.currentIndex()
        if current_index >= 0:
            self.tabbed_editor.close_tab(current_index)
            # Actualizar referencia al editor actual
            self.input_text = self.tabbed_editor.get_current_editor()
    
    def open_system_terminal(self):
        """Abre la terminal/cmd nativa del sistema operativo"""
        import platform
        import subprocess
        import os
        import shutil
        
        try:
            system = platform.system().lower()
            current_dir = os.getcwd()
            terminal_opened = False
            terminal_used = None
            
            if system == "windows":
                # Windows: Abrir CMD o PowerShell
                try:
                    # Intentar abrir Windows Terminal si está disponible
                    subprocess.Popen(['wt', '-d', current_dir], shell=True)
                    terminal_opened = True
                    terminal_used = "Windows Terminal"
                except (FileNotFoundError, subprocess.SubprocessError):
                    try:
                        # Si no, intentar PowerShell
                        subprocess.Popen(['powershell', '-NoExit', '-Command', f'cd "{current_dir}"'], shell=True)
                        terminal_opened = True
                        terminal_used = "PowerShell"
                    except (FileNotFoundError, subprocess.SubprocessError):
                        try:
                            # Como último recurso, abrir CMD
                            subprocess.Popen(['cmd', '/k', f'cd /d "{current_dir}"'], shell=True)
                            terminal_opened = True
                            terminal_used = "CMD"
                        except (FileNotFoundError, subprocess.SubprocessError):
                            pass
                        
            elif system == "darwin":  # macOS
                # macOS: Abrir Terminal.app
                try:
                    script = f'''
                    tell application "Terminal"
                        activate
                        do script "cd '{current_dir}'"
                    end tell
                    '''
                    subprocess.Popen(['osascript', '-e', script])
                    terminal_opened = True
                    terminal_used = "Terminal.app"
                except (FileNotFoundError, subprocess.SubprocessError):
                    pass
                
            else:  # Linux y otros sistemas Unix
                # Lista de terminales ordenada por preferencia
                terminals_config = [
                    ('gnome-terminal', ['--working-directory', current_dir]),
                    ('konsole', ['--workdir', current_dir]),
                    ('xfce4-terminal', ['--working-directory', current_dir]),
                    ('mate-terminal', ['--working-directory', current_dir]),
                    ('terminator', ['--working-directory', current_dir]),
                    ('alacritty', ['--working-directory', current_dir]),
                    ('kitty', ['--directory', current_dir]),
                    ('lxterminal', ['--working-directory', current_dir]),
                    ('xterm', ['-e', f'cd "{current_dir}"; exec bash'])
                ]
                
                # Intentar cada terminal disponible
                for terminal, args in terminals_config:
                    if shutil.which(terminal):  # Verificar si el terminal existe
                        try:
                            # Para gnome-terminal, usar método especial debido a problemas con snaps
                            if terminal == 'gnome-terminal':
                                process = subprocess.Popen([terminal] + args, 
                                                         stderr=subprocess.DEVNULL,
                                                         stdout=subprocess.DEVNULL)
                                # Esperar un momento para ver si el proceso se inicia
                                import time
                                time.sleep(0.5)
                                if process.poll() is None:  # Proceso aún ejecutándose
                                    terminal_opened = True
                                    terminal_used = "GNOME Terminal"
                                    break
                            else:
                                subprocess.Popen([terminal] + args)
                                terminal_opened = True
                                terminal_used = terminal.replace('-', ' ').title()
                                break
                                
                        except (FileNotFoundError, subprocess.SubprocessError) as e:
                            print(f"Error con {terminal}: {e}")  # Debug
                            continue
                
                # Fallback final: intentar con x-terminal-emulator
                if not terminal_opened and shutil.which('x-terminal-emulator'):
                    try:
                        subprocess.Popen(['x-terminal-emulator', '-e', f'cd "{current_dir}"; exec bash'])
                        terminal_opened = True
                        terminal_used = "X Terminal Emulator"
                    except (FileNotFoundError, subprocess.SubprocessError):
                        pass
            
            # Solo mostrar mensaje si la terminal se abrió exitosamente
            if terminal_opened and terminal_used:
                # No mostrar mensaje de confirmación para evitar ventanas innecesarias
                # La terminal se abrió correctamente y eso es suficiente
                pass
            elif not terminal_opened:
                # Solo mostrar error si realmente no se pudo abrir ninguna terminal
                available_terminals = []
                if system == 'linux':
                    for terminal, _ in terminals_config:
                        if shutil.which(terminal):
                            available_terminals.append(terminal)
                
                error_msg = "❌ No se pudo abrir una terminal del sistema.\n\n"
                if available_terminals:
                    error_msg += f"Terminales detectadas: {', '.join(available_terminals)}\n\n"
                    error_msg += "Es posible que haya un problema de permisos o configuración."
                else:
                    error_msg += "No se encontraron terminales compatibles instaladas.\n\n"
                    error_msg += "💡 Considera instalar una terminal:\n"
                    error_msg += "• sudo apt install gnome-terminal\n"
                    error_msg += "• sudo apt install konsole\n"
                    error_msg += "• sudo apt install xfce4-terminal\n"
                    error_msg += "• sudo apt install terminator"
                
                self.show_message("Error", error_msg, "error")
                            
        except Exception as e:
            self.show_message("Error", 
                            f"❌ Error abriendo terminal del sistema:\n{str(e)}", 
                            "error")
