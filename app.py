import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from CSV.page import CsvToolsWindow
from EMAIL.page import EmailToolsWindow

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ferramentas Multimídia")
        self.setFixedSize(400, 300)
        
        # Criar widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Título
        title_label = QLabel("Ferramentas Multimídia")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Botão Manipular CSV
        csv_button = QPushButton("Manipular CSV")
        csv_button.setFixedHeight(40)
        csv_button.clicked.connect(self.open_csv_tool)
        layout.addWidget(csv_button)
        
        # Botão Enviar e-mail
        email_button = QPushButton("Enviar e-mail")
        email_button.setFixedHeight(40)
        email_button.clicked.connect(self.open_email_tool)
        layout.addWidget(email_button)
        
        # Espaçamento
        layout.addStretch()
    
    def open_csv_tool(self):
        """Abre a ferramenta de manipulação de CSV"""
        self.csv_window = CsvToolsWindow(self)
        self.csv_window.show()
        self.hide()
    
    def open_email_tool(self):
        """Abre a ferramenta de envio de e-mail"""
        self.email_window = EmailToolsWindow(self)
        self.email_window.show()
        self.hide()

def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
