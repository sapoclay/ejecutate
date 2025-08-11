#!/usr/bin/env python3
"""
Terminal integrado real usando QProcess
Este archivo contiene la nueva implementación del terminal
"""

import time
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                               QLineEdit, QPushButton, QLabel, QComboBox, QInputDialog)
from PySide6.QtCore import Qt, QProcess, QProcessEnvironment, QTimer
from PySide6.QtGui import QFont, QColor

class IntegratedTerminalNew(QWidget):
    """Terminal integrado real del sistema usando QProcess"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_editor = parent
        self.process = None
        self.command_history = []
        self.history_index = -1
        self.waiting_for_input = False
        self.input_prompt = ""
        self.init_ui()
        self.start_terminal()
        
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Barra de herramientas del terminal
        toolbar = QHBoxLayout()
        
        # Selector de shell
        shell_label = QLabel("Shell:")
        shell_label.setStyleSheet("color: #FFFFFF; font-weight: bold;")
        self.shell_combo = QComboBox()
        self.shell_combo.addItems([
            "� Python3 Interactivo",  # Poner Python como primera opción
            "�️ Bash", 
            "� Python3"
        ])
        self.shell_combo.setStyleSheet("""
            QComboBox {
                background-color: #2C3E50;
                color: white;
                border: 1px solid #34495E;
                padding: 5px;
                min-width: 150px;
            }
        """)
        self.shell_combo.currentTextChanged.connect(self.change_shell)
        
        toolbar.addWidget(shell_label)
        toolbar.addWidget(self.shell_combo)
        toolbar.addStretch()
        
        # Botones de control
        self.clear_btn = QPushButton("🗑️ Limpiar")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #C0392B; }
        """)
        self.clear_btn.clicked.connect(self.clear_terminal)
        
        self.restart_btn = QPushButton("🔄 Reiniciar")
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980B9; }
        """)
        self.restart_btn.clicked.connect(self.restart_terminal)
        
        toolbar.addWidget(self.clear_btn)
        toolbar.addWidget(self.restart_btn)
        layout.addLayout(toolbar)
        
        # Área de salida del terminal
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(QFont("Consolas", 11))
        self.terminal_output.setStyleSheet("""
            QTextEdit {
                background-color: #0C0C0C;
                color: #00FF00;
                border: 1px solid #333333;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                line-height: 1.2;
            }
        """)
        layout.addWidget(self.terminal_output)
        
        # Línea de comandos
        input_layout = QHBoxLayout()
        
        self.prompt_label = QLabel("$ ")
        self.prompt_label.setStyleSheet("""
            QLabel {
                color: #00FFFF;
                font-weight: bold;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                min-width: 20px;
            }
        """)
        
        self.command_input = QLineEdit()
        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: #1A1A1A;
                color: #FFFFFF;
                border: 1px solid #333333;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #4A90E2;
            }
        """)
        self.command_input.returnPressed.connect(self.execute_command)
        self.command_input.keyPressEvent = self.handle_key_press
        
        send_btn = QPushButton("▶️")
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2ECC71; }
        """)
        send_btn.clicked.connect(self.execute_command)
        
        input_layout.addWidget(self.prompt_label)
        input_layout.addWidget(self.command_input)
        input_layout.addWidget(send_btn)
        layout.addLayout(input_layout)
        
        # Estado del terminal
        self.status_label = QLabel("🔴 Terminal detenido")
        self.status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")
        layout.addWidget(self.status_label)
        
    def start_terminal(self):
        """Inicia el proceso del terminal"""
        self.process = QProcess(self)
        
        # Conectar señales
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.finished.connect(self.process_finished)
        self.process.started.connect(self.process_started)
        
        # Iniciar con shell por defecto (será configurado en change_shell)
        self.change_shell()
        
    def change_shell(self):
        """Cambia el shell del terminal"""
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.process.waitForFinished(2000)
            
        shell_text = self.shell_combo.currentText()
        
        try:
            # Configurar variables de entorno preservando las necesarias para aplicaciones gráficas
            env = QProcessEnvironment.systemEnvironment()
            
            # Preservar variables importantes para aplicaciones gráficas
            important_vars = [
                "DISPLAY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE", "XDG_RUNTIME_DIR",
                "XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "XDG_DATA_DIRS",
                "XDG_CONFIG_DIRS", "DESKTOP_SESSION", "SESSION_MANAGER",
                "GNOME_DESKTOP_SESSION_ID", "GDMSESSION", "PATH", "HOME",
                "USER", "LANG", "LANGUAGE", "LC_ALL", "LC_CTYPE",
                "DBUS_SESSION_BUS_ADDRESS", "QT_QPA_PLATFORM", "GDK_BACKEND"
            ]
            
            # Guardar variables importantes antes de limpiar
            saved_vars = {}
            for var in important_vars:
                if env.contains(var):
                    saved_vars[var] = env.value(var)
            
            # Configurar variables básicas de terminal
            env.insert("TERM", "xterm")
            env.insert("PS1", "$ ")  # Prompt simple
            env.insert("PS2", "> ")  # Prompt de continuación
            
            # Remover solo configuraciones problemáticas específicas de shells
            custom_vars = [
                "STARSHIP_CONFIG", "STARSHIP_CACHE", "STARSHIP_SESSION_KEY",
                "OH_MY_ZSH", "ZSH_THEME", "ZSH", "ZSH_CUSTOM",
                "PROMPT", "RPROMPT", "POWERLEVEL9K_MODE", "POWERLEVEL10K_MODE",
                "CONDA_PROMPT_MODIFIER", "VIRTUAL_ENV_PROMPT",
                "BASH_IT", "BASH_IT_THEME"
            ]
            
            for var in custom_vars:
                env.remove(var)
            
            # Restaurar variables importantes
            for var, value in saved_vars.items():
                env.insert(var, value)
                
            # Configurar entorno específico según el shell
            if "Bash" in shell_text:
                # Bash limpio
                self.process.setProcessEnvironment(env)
                self.process.start("/bin/bash", ["--norc", "--noprofile", "-i"])
                self.prompt_label.setText("$ ")
                
            elif "Python" in shell_text:
                # Python con configuración específica
                env.insert("PYTHONUNBUFFERED", "1")
                env.insert("PYTHONIOENCODING", "utf-8")
                env.insert("PYTHONDONTWRITEBYTECODE", "1")  # No crear archivos .pyc
                env.insert("PYTHONINTERACTIVE", "1")  # Forzar modo interactivo
                
                self.process.setProcessEnvironment(env)
                
                if "Interactivo" in shell_text:
                    self.process.start("python3", ["-i", "-u", "-B"])
                else:
                    self.process.start("python3", ["-u", "-B"])
                    
                self.prompt_label.setText(">>> ")
                
            # Esperar a que inicie y verificar
            if self.process.waitForStarted(5000):
                self.terminal_output.setTextColor(QColor("#00FF00"))
                self.terminal_output.append(f"🚀 {shell_text} iniciado correctamente")
                self.terminal_output.setTextColor(QColor("#CCCCCC"))
            else:
                self.terminal_output.setTextColor(QColor("#FF0000"))
                self.terminal_output.append(f"❌ Error iniciando {shell_text}")
                self.status_label.setText("🔴 Error al iniciar")
                
        except Exception as e:
            self.terminal_output.setTextColor(QColor("#FF0000"))
            self.terminal_output.append(f"❌ Error: {str(e)}")
            self.status_label.setText("🔴 Error")
            
    def restart_terminal(self):
        """Reinicia el terminal"""
        self.clear_terminal()
        self.start_terminal()
        
    def clear_terminal(self):
        """Limpia la salida del terminal"""
        self.terminal_output.clear()
        
    def execute_command(self):
        """Ejecuta un comando en el terminal"""
        command = self.command_input.text()
        if not command.strip():
            return
            
        # Agregar al historial
        if command not in self.command_history:
            self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Mostrar comando ejecutándose
        self.terminal_output.setTextColor(QColor("#FFFF00"))
        self.terminal_output.append(f"{self.prompt_label.text()}{command}")
        self.terminal_output.setTextColor(QColor("#00FF00"))
        
        # Limpiar entrada
        self.command_input.clear()
        
        # Enviar al proceso
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            try:
                # Enviar comando con salto de línea
                self.process.write(f"{command}\n".encode('utf-8'))
            except Exception as e:
                self.terminal_output.setTextColor(QColor("#FF0000"))
                self.terminal_output.append(f"❌ Error enviando comando: {str(e)}")
                self.terminal_output.setTextColor(QColor("#00FF00"))
        else:
            self.terminal_output.setTextColor(QColor("#FF0000"))
            self.terminal_output.append("❌ Terminal no está ejecutándose")
            self.terminal_output.setTextColor(QColor("#00FF00"))
            
        # Auto-scroll
        self.scroll_to_bottom()
        
    def execute_code_from_editor(self, code):
        """Ejecuta código Python enviado desde el editor"""
        # SIEMPRE forzar Python para ejecución de código del editor
        current_shell = self.shell_combo.currentText()
        
        # Verificar si el proceso actual es Python
        is_python_running = (self.process and 
                           self.process.state() == QProcess.ProcessState.Running and
                           "python" in self.process.program().lower())
        
        if not is_python_running:
            self.terminal_output.setTextColor(QColor("#FFFF00"))
            self.terminal_output.append("🔄 Iniciando Python...")
            self.terminal_output.setTextColor(QColor("#00FF00"))
            
            # Matar proceso actual si existe
            if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
                self.process.kill()
                self.process.waitForFinished(3000)
            
            # Configurar variables de entorno específicas para Python preservando las gráficas
            env = QProcessEnvironment.systemEnvironment()
            
            # Preservar variables importantes para aplicaciones gráficas
            important_vars = [
                "DISPLAY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE", "XDG_RUNTIME_DIR",
                "XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "XDG_DATA_DIRS",
                "XDG_CONFIG_DIRS", "DESKTOP_SESSION", "SESSION_MANAGER",
                "GNOME_DESKTOP_SESSION_ID", "GDMSESSION", "PATH", "HOME",
                "USER", "LANG", "LANGUAGE", "LC_ALL", "LC_CTYPE",
                "DBUS_SESSION_BUS_ADDRESS", "QT_QPA_PLATFORM", "GDK_BACKEND"
            ]
            
            # Guardar variables importantes antes de limpiar
            saved_vars = {}
            for var in important_vars:
                if env.contains(var):
                    saved_vars[var] = env.value(var)
            
            # Configurar variables específicas de Python
            env.insert("PYTHONUNBUFFERED", "1")
            env.insert("PYTHONIOENCODING", "utf-8")
            env.insert("PYTHONDONTWRITEBYTECODE", "1")
            env.insert("TERM", "xterm")
            env.insert("PYTHONINTERACTIVE", "1")  # Forzar modo interactivo
            
            # Limpiar solo variables problemáticas específicas de shells
            custom_vars = [
                "STARSHIP_CONFIG", "STARSHIP_CACHE", "STARSHIP_SESSION_KEY",
                "OH_MY_ZSH", "ZSH_THEME", "ZSH", "ZSH_CUSTOM",
                "PROMPT", "RPROMPT", "POWERLEVEL9K_MODE", "POWERLEVEL10K_MODE",
                "CONDA_PROMPT_MODIFIER", "VIRTUAL_ENV_PROMPT",
                "BASH_IT", "BASH_IT_THEME"
            ]
            
            for var in custom_vars:
                env.remove(var)
            
            # Restaurar variables importantes
            for var, value in saved_vars.items():
                env.insert(var, value)
            
            # Configurar proceso para Python
            self.process.setProcessEnvironment(env)
            
            # Iniciar Python interactivo
            self.process.start("python3", ["-i", "-u", "-B"])
            
            if not self.process.waitForStarted(5000):
                self.terminal_output.setTextColor(QColor("#FF0000"))
                self.terminal_output.append("❌ Error: No se pudo iniciar Python")
                self.terminal_output.setTextColor(QColor("#00FF00"))
                return
            
            # Cambiar el ComboBox para reflejar el estado
            self.shell_combo.setCurrentText("🐍 Python3 Interactivo")
            self.prompt_label.setText(">>> ")
            
            # Esperar a que Python esté completamente listo
            import time as time_module
            time_module.sleep(2)
        
        # Verificar estado final
        if (not self.process or 
            self.process.state() != QProcess.ProcessState.Running):
            self.terminal_output.setTextColor(QColor("#FF0000"))
            self.terminal_output.append("❌ Error: Python no está ejecutándose")
            self.terminal_output.setTextColor(QColor("#00FF00"))
            return
            
        # Enviar código al proceso Python (con manejo especial para input)
        try:
            # Filtrar y preparar el código
            lines = code.split('\n')
            filtered_lines = []
            
            for line in lines:
                stripped = line.strip()
                if stripped:  # Incluir todas las líneas no vacías
                    filtered_lines.append(line)
            
            if filtered_lines:
                # Verificar si hay input() en el código
                has_input = any('input(' in line for line in filtered_lines)
                
                if has_input:
                    # Para código con input(), crear una versión modificada
                    modified_code = self._process_code_with_input(filtered_lines)
                    self.process.write(modified_code.encode('utf-8'))
                    self.process.write(b"\n")
                else:
                    # Para código sin input(), usar exec() normal
                    full_code = '\n'.join(filtered_lines)
                    exec_command = f'exec("""{full_code}""")'
                    self.process.write(exec_command.encode('utf-8'))
                    self.process.write(b"\n")
                
                # Forzar flush del buffer
                if hasattr(self.process, 'waitForBytesWritten'):
                    self.process.waitForBytesWritten(1000)
                
        except Exception as e:
            self.terminal_output.setTextColor(QColor("#FF0000"))
            self.terminal_output.append(f"❌ Error enviando código: {str(e)}")
            self.terminal_output.setTextColor(QColor("#00FF00"))
            
        self.scroll_to_bottom()
        
    def _process_code_with_input(self, lines):
        """Procesa código con input() para manejarlo de forma interactiva"""
        import re
        
        # Crear código modificado que reemplace input() con nuestro sistema
        modified_lines = []
        for line in lines:
            # Buscar patrones de input()
            input_pattern = r'(\w+)\s*=\s*input\s*\(\s*["\']([^"\']*)["\']?\s*\)'
            match = re.search(input_pattern, line)
            
            if match:
                var_name = match.group(1)
                prompt_text = match.group(2) if match.group(2) else "Entrada"
                
                # Reemplazar con nuestro sistema de input
                new_line = f'{var_name} = __get_user_input__("{prompt_text}")'
                modified_lines.append(new_line)
            else:
                modified_lines.append(line)
        
        # Crear función helper para obtener input del usuario
        helper_code = '''
def __get_user_input__(prompt):
    print(f"{prompt}", end="", flush=True)
    import sys
    return sys.stdin.readline().strip()
'''
        
        full_code = helper_code + '\n' + '\n'.join(modified_lines)
        return f'exec("""{full_code}""")'
        
    def read_output(self):
        """Lee la salida estándar del proceso"""
        if not self.process:
            return
            
        try:
            data = self.process.readAllStandardOutput()
            if data:
                output = data.data().decode('utf-8', errors='replace')
                
                # Limpiar secuencias de escape ANSI y caracteres de control
                import re
                
                # Remover secuencias de escape ANSI (colores, posicionamiento del cursor, etc.)
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                output = ansi_escape.sub('', output)
                
                # Limpiar otros caracteres problemáticos
                output = output.replace('\r\n', '\n').replace('\r', '')
                
                # Remover caracteres de control adicionales
                control_chars = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')
                output = control_chars.sub('', output)
                
                # Detectar si Python está esperando entrada (termina sin >>> y sin newline)
                if output and not output.endswith('\n') and not output.endswith('>>> '):
                    # Probablemente es un prompt de input
                    self.terminal_output.setTextColor(QColor("#FFFF00"))
                    self.terminal_output.insertPlainText(output)
                    
                    # Mostrar diálogo para obtener entrada del usuario
                    QTimer.singleShot(100, lambda: self._handle_input_request(output))
                    
                elif output.strip():  # Solo mostrar si hay contenido real
                    self.terminal_output.setTextColor(QColor("#CCCCCC"))
                    self.terminal_output.insertPlainText(output)
                    self.scroll_to_bottom()
                    
        except Exception as e:
            self.terminal_output.setTextColor(QColor("#FF8800"))
            self.terminal_output.append(f"⚠️ Error leyendo salida: {str(e)}")
            self.terminal_output.setTextColor(QColor("#00FF00"))
            
    def _handle_input_request(self, prompt_text):
        """Maneja solicitudes de input del usuario"""
        try:
            # Mostrar diálogo para obtener entrada del usuario
            text, ok = QInputDialog.getText(
                self, 
                "Entrada requerida", 
                prompt_text.strip(),
                QLineEdit.EchoMode.Normal
            )
            
            if ok:
                # Enviar la respuesta al proceso Python
                if self.process and self.process.state() == QProcess.ProcessState.Running:
                    self.process.write(f"{text}\n".encode('utf-8'))
                    
                    # Mostrar la entrada en el terminal
                    self.terminal_output.setTextColor(QColor("#00FFFF"))
                    self.terminal_output.insertPlainText(f"{text}\n")
                    self.terminal_output.setTextColor(QColor("#CCCCCC"))
                    self.scroll_to_bottom()
            else:
                # Usuario canceló - enviar línea vacía
                if self.process and self.process.state() == QProcess.ProcessState.Running:
                    self.process.write(b"\n")
                    
        except Exception as e:
            self.terminal_output.setTextColor(QColor("#FF0000"))
            self.terminal_output.append(f"❌ Error manejando entrada: {str(e)}")
            self.terminal_output.setTextColor(QColor("#00FF00"))
            
    def read_error(self):
        """Lee la salida de error del proceso"""
        if not self.process:
            return
            
        try:
            data = self.process.readAllStandardError()
            if data:
                output = data.data().decode('utf-8', errors='replace')
                
                # Limpiar secuencias de escape ANSI
                import re
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                output = ansi_escape.sub('', output)
                
                # Limpiar caracteres de control
                output = output.replace('\r\n', '\n').replace('\r', '')
                control_chars = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')
                output = control_chars.sub('', output)
                
                if output.strip():
                    self.terminal_output.setTextColor(QColor("#FF8800"))
                    self.terminal_output.insertPlainText(output)
                    self.terminal_output.setTextColor(QColor("#00FF00"))
                    self.scroll_to_bottom()
                    
        except Exception as e:
            self.terminal_output.setTextColor(QColor("#FF0000"))
            self.terminal_output.append(f"❌ Error leyendo stderr: {str(e)}")
            self.terminal_output.setTextColor(QColor("#00FF00"))
            
    def process_started(self):
        """Se ejecuta cuando el proceso inicia"""
        self.status_label.setText("🟢 Terminal activo")
        self.status_label.setStyleSheet("color: #00FF00; font-weight: bold; padding: 5px;")
        
    def process_finished(self, exit_code):
        """Se ejecuta cuando el proceso termina"""
        self.terminal_output.setTextColor(QColor("#FFFF00"))
        self.terminal_output.append(f"\n🔚 Proceso terminado (código: {exit_code})")
        self.terminal_output.setTextColor(QColor("#00FF00"))
        self.status_label.setText("🔴 Terminal detenido")
        self.status_label.setStyleSheet("color: #FF0000; font-weight: bold; padding: 5px;")
        
    def handle_key_press(self, event):
        """Maneja eventos de teclado especiales"""
        if event.key() == Qt.Key.Key_Up:
            # Historial hacia atrás
            if self.command_history and self.history_index > 0:
                self.history_index -= 1
                self.command_input.setText(self.command_history[self.history_index])
        elif event.key() == Qt.Key.Key_Down:
            # Historial hacia adelante
            if self.command_history and self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_input.setText(self.command_history[self.history_index])
            else:
                self.history_index = len(self.command_history)
                self.command_input.clear()
        elif event.key() == Qt.Key.Key_Tab:
            # Auto-completado básico (podríamos expandir esto)
            current_text = self.command_input.text()
            # Por ahora, simplemente ignoramos tab
            return
        else:
            # Comportamiento normal para otras teclas
            QLineEdit.keyPressEvent(self.command_input, event)
            
    def scroll_to_bottom(self):
        """Hace scroll automático al final"""
        cursor = self.terminal_output.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.terminal_output.setTextCursor(cursor)
        
    def closeEvent(self, event):
        """Limpia recursos al cerrar"""
        if self.process:
            self.process.kill()
            self.process.waitForFinished(2000)
        event.accept()
