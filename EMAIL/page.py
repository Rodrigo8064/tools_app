from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from EMAIL.functions import enviar_email_seed, visualizar_responsaveis, configurar_email

class EmailToolsWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Automação de envio de e-mail")
        self.setFixedSize(450, 400)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        
        # Título
        title_label = QLabel("Automação de envio de e-mail")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Informação
        info_label = QLabel("Envio automatizado por categorias para responsáveis")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)
        
        # Espaçamento
        layout.addSpacing(20)
        
        # Botão Envio de e-mail por Categoria
        email_seed_button = QPushButton("Envio de e-mail por Categoria")
        email_seed_button.setFixedHeight(40)
        email_seed_button.clicked.connect(self.enviar_email_seed_action)
        layout.addWidget(email_seed_button)
        
        # Botão Configurar E-mail
        config_button = QPushButton("⚙️ Configurar E-mail")
        config_button.setFixedHeight(35)
        config_button.clicked.connect(self.configurar_email_action)
        layout.addWidget(config_button)
        
        # Botão Visualizar Responsáveis
        visualizar_button = QPushButton("👥 Visualizar Categorias e Responsáveis")
        visualizar_button.setFixedHeight(35)
        visualizar_button.clicked.connect(self.visualizar_responsaveis_action)
        layout.addWidget(visualizar_button)
        
        # Espaçamento
        layout.addStretch()
        
        # Botão Voltar
        voltar_button = QPushButton("↩️ Voltar")
        voltar_button.setFixedHeight(35)
        voltar_button.clicked.connect(self.voltar)
        layout.addWidget(voltar_button)
    
    def enviar_email_seed_action(self):
        """Ação para o botão Envio de e-mail por Categoria"""
        enviar_email_seed(self)
    
    def visualizar_responsaveis_action(self):
        """Ação para o botão Visualizar Responsáveis"""
        visualizar_responsaveis(self)
    
    def configurar_email_action(self):
        """Ação para o botão Configurar E-mail"""
        configurar_email(self)
    
    def voltar(self):
        """Volta para a janela principal"""
        self.main_window.show()
        self.close()
