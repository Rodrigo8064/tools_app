from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from CSV.functions import dividir_csv, formatar_csv

class CsvToolsWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Ferramentas para manipular CSV")
        self.setFixedSize(400, 400)

        # Layout principal
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        # Título
        title_label = QLabel("Ferramentas para manipular CSV")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Botão Dividir CSV
        dividir_button = QPushButton("Dividir CSV")
        dividir_button.setFixedHeight(40)
        dividir_button.clicked.connect(self.dividir_csv_action)
        layout.addWidget(dividir_button)

        # Botão Formatar CSV
        formatar_button = QPushButton("Formatar CSV")
        formatar_button.setFixedHeight(40)
        formatar_button.clicked.connect(self.formatar_csv_action)
        layout.addWidget(formatar_button)

        # Espaçamento
        layout.addStretch()

        # Botão Voltar
        voltar_button = QPushButton("Voltar")
        voltar_button.setFixedHeight(40)
        voltar_button.clicked.connect(self.voltar)
        layout.addWidget(voltar_button)

    def dividir_csv_action(self):
        """Ação para o botão Dividir CSV"""
        dividir_csv(self)

    def formatar_csv_action(self):
        """Ação para o botão Formatar CSV"""
        formatar_csv(self)

    def voltar(self):
        """Volta para a janela principal"""
        self.main_window.show()
        self.close()
