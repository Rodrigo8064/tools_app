import time
import re
from typing import List, Optional, Generator
from dataclasses import dataclass, asdict
import csv
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QLineEdit, QPushButton, QSpinBox, QTextEdit,
                              QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal

# --- Constantes ---
BASE_URL = "https://www.magazineluiza.com.br"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/115.0.0.0 Safari/537.36"
)
ID_PATTERN = re.compile(r'/p/([a-zA-Z0-9]+)/')

@dataclass(frozen=True)
class ProductRecord:
    """Modelo de dados imutável para exportação."""
    product_id: str

class ScrapingWorker(QThread):
    """Thread para execução do scraping em background"""
    progress_signal = Signal(int, int, str)  # (atual, total, mensagem)
    finished_signal = Signal(str)  # mensagem final
    error_signal = Signal(str)  # mensagem de erro
    
    def __init__(self, termo_busca: str, max_paginas: int):
        super().__init__()
        self.termo_busca = termo_busca
        self.max_paginas = max_paginas
        self.is_running = True
        
    def run(self):
        try:
            resultado = self.realizar_scraping()
            if resultado:
                self.finished_signal.emit(f"✅ Scraping concluído!\nArquivo salvo em: {resultado}")
            else:
                self.finished_signal.emit("❌ Nenhum produto encontrado.")
        except Exception as e:
            self.error_signal.emit(f"❌ Erro no scraping: {str(e)}")
    
    def realizar_scraping(self):
        """Executa o scraping e retorna o caminho do arquivo"""
        nome_arquivo = f"resultado_{self.termo_busca}_{int(time.time())}.csv"
        output_dir = Path("CSV")
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / nome_arquivo
        
        scraper = MagaluScraper()
        all_links = []
        
        # Etapa 1: Coleta de Links
        for pagina in range(1, self.max_paginas + 1):
            if not self.is_running:
                break
                
            self.progress_signal.emit(pagina, self.max_paginas * 2, f"Buscando página {pagina}...")
            
            links_pagina = scraper.get_search_links(query=self.termo_busca, page=pagina)
            
            if not links_pagina:
                break
                
            all_links.extend(links_pagina)
            time.sleep(1.5)
        
        # Etapa 2: Extração de Produtos
        if all_links and self.is_running:
            self.progress_signal.emit(self.max_paginas, self.max_paginas * 2, f"Extraindo {len(all_links)} produtos...")
            
            data_gen = scraper.deep_scrape_products(all_links)
            fieldnames = [field.name for field in ProductRecord.__dataclass_fields__.values()]
            
            try:
                with file_path.open(mode='w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    count = 0
                    for record in data_gen:
                        if not self.is_running:
                            break
                            
                        writer.writerow(asdict(record))
                        count += 1
                        
                        # Atualiza progresso a cada 10 produtos
                        if count % 10 == 0:
                            self.progress_signal.emit(
                                self.max_paginas + count, 
                                self.max_paginas * 2 + len(all_links), 
                                f"Extraídos {count} produtos..."
                            )
                    
                    return str(file_path)
                    
            except IOError as e:
                raise Exception(f"Erro ao salvar arquivo: {e}")
        
        return None
    
    def stop(self):
        """Para a execução do scraping"""
        self.is_running = False

class MagaluScraper:
    """Gerencia a sessão e a lógica de extração."""
    
    def __init__(self) -> None:
        self.session = self._setup_session()
    
    def _setup_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update({"User-Agent": USER_AGENT})
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
    
    def _extract_id_from_url(self, url: str) -> Optional[str]:
        match = ID_PATTERN.search(url)
        return match.group(1) if match else None
    
    def get_search_links(self, query: str, page: int = 1) -> List[str]:
        """Obtém links da página de busca."""
        search_url = f"{BASE_URL}/busca/{query}/"
        params = {"page": page, "sortOrientation": "asc", "sortType": "price", "bypass": "true"}
        
        try:
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = {a['href'] for a in soup.find_all('a', href=True) if '/p/' in a['href']}
            
            return list(links)
        except requests.exceptions.RequestException:
            return []
    
    def deep_scrape_products(self, product_links: List[str]) -> Generator[ProductRecord, None, None]:
        """Visita cada produto e gera um ProductRecord."""
        for partial_link in product_links:
            full_url = urljoin(BASE_URL, partial_link)
            time.sleep(1.0)  # Politeness
            
            try:
                response = self.session.get(full_url, timeout=10)
                if response.status_code != 200:
                    continue
                
                final_url = response.url
                product_id = self._extract_id_from_url(final_url)
                
                if product_id:
                    yield ProductRecord(product_id=product_id)
                    
            except requests.exceptions.RequestException:
                continue

class ScrapingDialog(QDialog):
    """Janela de diálogo para configuração do scraping"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scraping - Magazine Luiza")
        self.setFixedSize(500, 400)
        
        self.worker = None
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface do diálogo"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("📊 Scraping Magazine Luiza")
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Instruções
        info_label = QLabel("Extraia IDs de produtos da Magazine Luiza")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)
        
        # Campo de busca
        layout.addWidget(QLabel("Termo de busca:"))
        self.termo_input = QLineEdit()
        self.termo_input.setPlaceholderText("Ex: monitor, notebook, celular...")
        layout.addWidget(self.termo_input)
        
        # Número de páginas
        paginas_layout = QHBoxLayout()
        paginas_layout.addWidget(QLabel("Número de páginas:"))
        self.paginas_spin = QSpinBox()
        self.paginas_spin.setRange(1, 10)
        self.paginas_spin.setValue(3)
        paginas_layout.addWidget(self.paginas_spin)
        paginas_layout.addStretch()
        layout.addLayout(paginas_layout)
        
        # Barra de progresso
        layout.addWidget(QLabel("Progresso:"))
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Log de execução
        layout.addWidget(QLabel("Log:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)
        
        # Botões
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("▶️ Iniciar Scraping")
        self.start_button.clicked.connect(self.iniciar_scraping)
        button_layout.addWidget(self.start_button)
        
        self.cancel_button = QPushButton("⏹️ Cancelar")
        self.cancel_button.clicked.connect(self.cancelar_scraping)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)
        
        self.close_button = QPushButton("❌ Fechar")
        self.close_button.clicked.connect(self.close)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def log(self, mensagem: str):
        """Adiciona mensagem ao log"""
        self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {mensagem}")
    
    def iniciar_scraping(self):
        """Inicia o processo de scraping"""
        termo = self.termo_input.text().strip()
        
        if not termo:
            QMessageBox.warning(self, "Aviso", "Digite um termo de busca!")
            return
        
        # Desabilita controles durante a execução
        self.termo_input.setEnabled(False)
        self.paginas_spin.setEnabled(False)
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        
        # Limpa log anterior
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        self.log(f"Iniciando scraping para: '{termo}'")
        self.log(f"Páginas a serem buscadas: {self.paginas_spin.value()}")
        
        # Cria e inicia worker
        self.worker = ScrapingWorker(termo, self.paginas_spin.value())
        self.worker.progress_signal.connect(self.atualizar_progresso)
        self.worker.finished_signal.connect(self.scraping_concluido)
        self.worker.error_signal.connect(self.scraping_erro)
        self.worker.start()
    
    def atualizar_progresso(self, atual: int, total: int, mensagem: str):
        """Atualiza barra de progresso e log"""
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(atual)
        
        if mensagem:
            self.log(mensagem)
    
    def scraping_concluido(self, mensagem: str):
        """Processa conclusão do scraping"""
        self.log(mensagem)
        self.restaurar_controles()
        
        QMessageBox.information(self, "Concluído", mensagem)
    
    def scraping_erro(self, mensagem: str):
        """Processa erro no scraping"""
        self.log(mensagem)
        self.restaurar_controles()
        
        QMessageBox.critical(self, "Erro", mensagem)
    
    def cancelar_scraping(self):
        """Cancela o scraping em andamento"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            self.log("Scraping cancelado pelo usuário")
            self.restaurar_controles()
    
    def restaurar_controles(self):
        """Restaura controles para estado inicial"""
        self.termo_input.setEnabled(True)
        self.paginas_spin.setEnabled(True)
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.worker = None
    
    def closeEvent(self, event):
        """Trata o fechamento da janela"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "Scraping em andamento",
                "O scraping ainda está em execução. Deseja realmente cancelar?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.cancelar_scraping()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

# Função para ser chamada pelo botão na home
def abrir_scraping_magalu(parent=None):
    """Abre a janela de scraping - chamada pelo botão na home"""
    dialog = ScrapingDialog(parent)
    dialog.exec()
