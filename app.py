import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from CSV.page import CsvToolsWindow
from EMAIL.page import EmailToolsWindow
from scraping import abrir_scraping_magalu
from utils import iniciar_lembretes_agua, lembrete_agua

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ferramentas Multimídia")
        self.setFixedSize(400, 350)

        # Iniciar lembretes automáticos
        self.iniciar_lembretes_automaticos()

        # Criar widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

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

        # Botão de scraping
        scraping_button = QPushButton("🕷️ Scraping Magazine Luiza")
        scraping_button.setFixedHeight(40)
        scraping_button.clicked.connect(self.open_scraping_tool)  # Conecta a função
        layout.addWidget(scraping_button)


        # Botão Lembrete de Água
        agua_button = QPushButton("💧 Lembrete de Água")
        agua_button.setFixedHeight(40)
        agua_button.clicked.connect(self.lembrete_agua_manual)
        layout.addWidget(agua_button)

        # Status dos lembretes
        self.status_label = QLabel("Lembretes de água: ATIVOS ✅")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.status_label)

        # Espaçamento
        layout.addStretch()

    def iniciar_lembretes_automaticos(self):
        """Inicia os lembretes automáticos de água"""
        try:
            self.lembretes_thread = iniciar_lembretes_agua(intervalo_minutos=60)
            print("Lembretes de água iniciados (60 minutos)")
        except Exception as e:
            print(f"Erro ao iniciar lembretes: {e}")

    def lembrete_agua_manual(self):
        """Dispara um lembrete de água manualmente"""
        try:
            lembrete_agua()
        except Exception as e:
            print(f"Erro no lembrete manual: {e}")

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

    def open_scraping_tool(self):
        try:
            abrir_scraping_magalu()
        except Exception as e:
            print(F'Erro ao realizar scraping: {e}')

def main():
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
