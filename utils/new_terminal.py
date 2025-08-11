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
        
        self.setup_ui()
        self.start_terminal()
        
        # Variables para manejar el estado del comando actual
        self.current_command = ""
        self.command_finished = True
        
    def setup_ui(self):
        """Configura la interfaz del terminal"""
        layout = QVBoxLayout()
        
        # Barra de herramientas del terminal
        toolbar = QHBoxLayout()
        
        # Selector de intérprete
        self.shell_combo = QComboBox()
        self.shell_combo.addItem("🐍 Python", "python3")
        self.shell_combo.addItem("🐧 Bash", "/bin/bash")
        self.shell_combo.addItem("🐚 Zsh", "/bin/zsh")
        self.shell_combo.addItem("🐟 Fish", "/usr/bin/fish")
        self.shell_combo.addItem("📱 Sh", "/bin/sh")
        self.shell_combo.currentTextChanged.connect(self.change_shell)
        
        # Botón para limpiar terminal
        self.clear_btn = QPushButton("🗑️ Limpiar")
        self.clear_btn.setMaximumWidth(80)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_terminal)
        
        # Botón para reiniciar terminal
        self.restart_btn = QPushButton("🔄 Reiniciar")
        self.restart_btn.setMaximumWidth(90)
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        self.restart_btn.clicked.connect(self.restart_terminal)
        
        toolbar.addWidget(QLabel("🖥️ Intérprete:"))
        toolbar.addWidget(self.shell_combo)
        toolbar.addStretch()
        toolbar.addWidget(self.clear_btn)
        toolbar.addWidget(self.restart_btn)
        
        # Área de salida del terminal
        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setFont(QFont("Consolas", 11))
        self.terminal_output.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #444444;
                selection-background-color: #4A4A4A;
            }
        """)
        
        # Campo de entrada de comandos
        self.command_input = QLineEdit()
        self.command_input.setFont(QFont("Consolas", 11))
        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #444444;
                padding: 8px;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 2px solid #3498DB;
            }
        """)
        self.command_input.setPlaceholderText("Escribe tu comando aquí y presiona Enter...")
        self.command_input.returnPressed.connect(self.execute_command)
        
        # Conectar eventos del teclado para historial
        self.command_input.keyPressEvent = self.handle_key_press
        
        # Botón para ejecutar comando
        self.execute_btn = QPushButton("▶️ Ejecutar")
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ECC71;
            }
        """)
        self.execute_btn.clicked.connect(self.execute_command)
        
        # Layout para entrada de comandos
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.command_input)
        input_layout.addWidget(self.execute_btn)
        
        # Etiqueta de estado del terminal
        self.status_label = QLabel("🔴 Terminal detenido")
        self.status_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
        
        # Agregar todos los widgets al layout principal
        layout.addLayout(toolbar)
        layout.addWidget(self.terminal_output)
        layout.addLayout(input_layout)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)

    def start_terminal(self):
        """Inicia el proceso del terminal"""
        try:
            self.process = QProcess(self)
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(self.handle_finished)
            self.process.started.connect(self.handle_started)
            
            self.change_shell()
            
        except Exception as e:
            self.terminal_output.append(f"❌ Error al inicializar terminal: {str(e)}")

    def change_shell(self):
        """Cambia el shell del terminal"""
        try:
            if self.process and self.process.state() == QProcess.Running:
                self.process.kill()
                self.process.waitForFinished(3000)
            
            shell_data = self.shell_combo.currentData()
            
            if shell_data == "python3":
                self.process.start("python3", ["-i", "-u"])
            else:
                self.process.start(shell_data, ["-i"])
            
            # Configurar el entorno del proceso
            env = QProcessEnvironment.systemEnvironment()
            env.insert("PYTHONUNBUFFERED", "1")
            env.insert("PYTHONIOENCODING", "utf-8")
            
            # Variables específicas para diferentes shells
            if shell_data == "/bin/bash":
                env.insert("PS1", "\\u@\\h:\\w$ ")
            elif shell_data == "/bin/zsh":
                env.insert("PS1", "%n@%m:%~ %# ")
            
            # Configurar variables básicas de terminal
            env.insert("TERM", "xterm-256color")
            env.insert("COLUMNS", "80")
            env.insert("LINES", "24")
            
            self.process.setProcessEnvironment(env)
            
            # Limpiar salida y mostrar información inicial
            self.terminal_output.clear()
            shell_name = self.shell_combo.currentText()
            self.terminal_output.append(f"🚀 Iniciando {shell_name}...")
            self.terminal_output.append("=" * 50)
            
        except Exception as e:
            self.terminal_output.append(f"❌ Error al cambiar shell: {str(e)}")
    
    def execute_command(self):
        """Ejecuta un comando en el terminal"""
        try:
            command = self.command_input.text().strip()
            if not command:
                return
            
            # Agregar comando al historial
            if command not in self.command_history:
                self.command_history.append(command)
            self.history_index = len(self.command_history)
            
            # Mostrar comando en salida
            current_shell = self.shell_combo.currentText()
            self.terminal_output.append(f"\n📝 {current_shell} > {command}")
            
            # Verificar si el proceso está ejecutándose
            if not self.process or self.process.state() != QProcess.Running:
                self.terminal_output.append("❌ Terminal no está ejecutándose. Reiniciando...")
                self.start_terminal()
                return
            
            # Escribir comando al proceso
            command_bytes = (command + "\n").encode('utf-8')
            self.process.write(command_bytes)
            
            # Limpiar campo de entrada
            self.command_input.clear()
            
            # Marcar que hay un comando en ejecución
            self.current_command = command
            self.command_finished = False
            
            # Actualizar estado
            self.status_label.setText("⚡ Ejecutando comando...")
            self.status_label.setStyleSheet("color: #F39C12; font-weight: bold;")
            
        except Exception as e:
            self.terminal_output.append(f"❌ Error ejecutando comando: {str(e)}")
    
    def handle_stdout(self):
        """Maneja la salida estándar del proceso"""
        try:
            data = self.process.readAllStandardOutput()
            text = data.data().decode('utf-8', errors='replace')
            
            if text.strip():
                # Configurar color verde para salida normal
                self.terminal_output.setTextColor(QColor("#00FF00"))
                self.terminal_output.insertPlainText(text)
                self.terminal_output.setTextColor(QColor("#FFFFFF"))  # Resetear color
                
                # Auto-scroll hacia abajo
                scrollbar = self.terminal_output.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
                
        except Exception as e:
            self.terminal_output.append(f"❌ Error procesando salida: {str(e)}")
    
    def handle_stderr(self):
        """Maneja la salida de error del proceso"""
        try:
            data = self.process.readAllStandardError()
            text = data.data().decode('utf-8', errors='replace')
            
            if text.strip():
                # Configurar color rojo para errores
                self.terminal_output.setTextColor(QColor("#FF4444"))
                self.terminal_output.insertPlainText(text)
                self.terminal_output.setTextColor(QColor("#FFFFFF"))  # Resetear color
                
                # Auto-scroll hacia abajo
                scrollbar = self.terminal_output.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
                
        except Exception as e:
            self.terminal_output.append(f"❌ Error procesando error: {str(e)}")
    
    def handle_started(self):
        """Maneja cuando el proceso se inicia exitosamente"""
        self.status_label.setText("🟢 Terminal ejecutándose")
        self.status_label.setStyleSheet("color: #27AE60; font-weight: bold;")
        
        # Enviar comando inicial dependiendo del shell
        shell_data = self.shell_combo.currentData()
        if shell_data == "python3":
            # Configurar Python para mejor experiencia
            init_commands = [
                "import sys",
                "sys.ps1 = '🐍 >>> '",
                "sys.ps2 = '🐍 ... '",
                "print('🐍 Python interactivo listo!')"
            ]
            
            for cmd in init_commands:
                self.process.write((cmd + "\n").encode('utf-8'))
        else:
            # Para shells de sistema
            self.process.write("echo '🐧 Terminal listo!'\n".encode('utf-8'))
    
    def handle_finished(self, exit_code):
        """Maneja cuando el proceso termina"""
        self.status_label.setText(f"🔴 Terminal terminado (código: {exit_code})")
        self.status_label.setStyleSheet("color: #E74C3C; font-weight: bold;")
        
        if exit_code != 0:
            self.terminal_output.append(f"\n❌ Proceso terminado con código de error: {exit_code}")
        else:
            self.terminal_output.append(f"\n✅ Proceso terminado exitosamente")
    
    def clear_terminal(self):
        """Limpia la salida del terminal"""
        self.terminal_output.clear()
        self.terminal_output.append("🗑️ Terminal limpiado")
        self.terminal_output.append("=" * 30)
    
    def restart_terminal(self):
        """Reinicia el terminal"""
        try:
            if self.process and self.process.state() == QProcess.Running:
                self.process.kill()
                self.process.waitForFinished(3000)
            
            self.terminal_output.append("\n🔄 Reiniciando terminal...")
            self.terminal_output.append("=" * 40)
            
            # Pequeño delay para asegurar limpieza
            QTimer.singleShot(500, self.start_terminal)
            
        except Exception as e:
            self.terminal_output.append(f"❌ Error reiniciando terminal: {str(e)}")
    
    def handle_key_press(self, event):
        """Maneja las teclas presionadas en el campo de entrada"""
        # Llamar al método original primero
        QLineEdit.keyPressEvent(self.command_input, event)
        
        # Manejar historial con flechas arriba/abajo
        if event.key() == Qt.Key_Up:
            if self.command_history and self.history_index > 0:
                self.history_index -= 1
                self.command_input.setText(self.command_history[self.history_index])
        elif event.key() == Qt.Key_Down:
            if self.command_history and self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_input.setText(self.command_history[self.history_index])
            elif self.history_index >= len(self.command_history) - 1:
                self.history_index = len(self.command_history)
                self.command_input.clear()
    
    def send_to_terminal(self, text):
        """Método público para enviar texto al terminal desde el editor"""
        try:
            if not self.process or self.process.state() != QProcess.Running:
                self.terminal_output.append("❌ Terminal no está ejecutándose. Iniciando...")
                self.start_terminal()
                return False
            
            # Mostrar el texto que se va a ejecutar
            self.terminal_output.append(f"\n📤 Enviando código al terminal:")
            self.terminal_output.append("─" * 40)
            self.terminal_output.setTextColor(QColor("#87CEEB"))
            self.terminal_output.insertPlainText(text)
            self.terminal_output.setTextColor(QColor("#FFFFFF"))
            self.terminal_output.append("─" * 40)
            
            # Verificar si necesitamos cambiar a Python
            if self.shell_combo.currentData() != "python3":
                self.shell_combo.setCurrentText("🐍 Python")
                self.change_shell()
                # Esperar un poco para que se inicie Python
                QTimer.singleShot(1000, lambda: self._send_text_to_process(text))
            else:
                self._send_text_to_process(text)
            
            return True
            
        except Exception as e:
            self.terminal_output.append(f"❌ Error enviando al terminal: {str(e)}")
            return False
    
    def _send_text_to_process(self, text):
        """Envía texto al proceso del terminal"""
        try:
            # Dividir en líneas y enviar una por una
            lines = text.split('\n')
            for line in lines:
                if line.strip():  # Solo enviar líneas no vacías
                    self.process.write((line + "\n").encode('utf-8'))
            
            # Enviar línea vacía al final para asegurar ejecución
            self.process.write("\n".encode('utf-8'))
            
        except Exception as e:
            self.terminal_output.append(f"❌ Error en envío: {str(e)}")
    
    def get_terminal_text(self):
        """Retorna todo el texto del terminal"""
        return self.terminal_output.toPlainText()
    
    def is_running(self):
        """Verifica si el terminal está ejecutándose"""
        return self.process and self.process.state() == QProcess.Running
