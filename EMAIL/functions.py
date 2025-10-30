import pandas as pd
import smtplib
from PySide6.QtWidgets import (QFileDialog, QMessageBox, QInputDialog, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit)
from PySide6.QtCore import Qt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from EMAIL.especialistas import dicionario, obter_responsavel_por_categoria
from EMAIL.config import CONFIG_EMAIL

def enviar_email_seed(parent_window):
    """Função para enviar e-mails separados por categoria para os responsáveis"""
    try:
        # Abrir diálogo para selecionar arquivo CSV
        file_path, _ = QFileDialog.getOpenFileName(
            parent_window,
            "Selecione a planilha de categorias (CSV)",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Ler o arquivo CSV
        df = pd.read_csv(file_path)
        
        # Verificar se as colunas obrigatórias existem
        colunas_necessarias = ['Categoria', 'Tarefa']
        for coluna in colunas_necessarias:
            if coluna not in df.columns:
                QMessageBox.critical(
                    parent_window, 
                    "Erro", 
                    f"Coluna '{coluna}' não encontrada no arquivo CSV"
                )
                return
        
        # Mostrar colunas detectadas
        colunas_detectadas = list(df.columns)
        QMessageBox.information(
            parent_window,
            "Colunas Detectadas", 
            f"Colunas no arquivo: {', '.join(colunas_detectadas)}"
        )
        
        # Obter configurações de e-mail
        config = obter_configuracao_email(parent_window)
        if not config:
            return
        
        # Processar as categorias e enviar e-mails
        resultado = processar_categorias_e_enviar_emails(df, config, parent_window)
        
        # Mostrar resultado
        mostrar_resultado_envio(resultado, parent_window)
        
    except Exception as e:
        QMessageBox.critical(parent_window, "Erro", f"Erro ao processar e enviar e-mails: {str(e)}")

def processar_categorias_e_enviar_emails(df, config, parent_window):
    """
    Processa o DataFrame por categorias e envia e-mails para os responsáveis
    """
    resultado = {
        'enviados': 0,
        'falhas': [],
        'categorias_sem_responsavel': [],
        'categorias_processadas': []
    }
    
    # Agrupar por categoria
    categorias = df['Categoria'].unique()
    
    for categoria in categorias:
        try:
            # Obter e-mail do responsável
            email_responsavel = obter_responsavel_por_categoria(categoria)
            
            if not email_responsavel:
                resultado['categorias_sem_responsavel'].append(categoria)
                continue
            
            # Filtrar tarefas da categoria
            tarefas_categoria = df[df['Categoria'] == categoria]
            
            # Criar corpo do e-mail com TODAS as colunas
            corpo_email = criar_corpo_email_completo(categoria, tarefas_categoria)
            
            # Assunto do e-mail
            assunto = f"Tarefas - Categoria {categoria}"
            
            # Enviar e-mail
            enviar_email_unico(
                config['email'],
                config['senha'],
                config['smtp_server'],
                config['smtp_port'],
                email_responsavel,
                assunto,
                corpo_email
            )
            
            resultado['enviados'] += 1
            resultado['categorias_processadas'].append(categoria)
            
        except Exception as e:
            resultado['falhas'].append(f"{categoria}: {str(e)}")
    
    return resultado

def criar_corpo_email_completo(categoria, tarefas_df):
    """
    Cria o corpo do e-mail com TODAS as colunas do DataFrame
    """
    # Obter todas as colunas (exceto Categoria se quiser)
    colunas = [col for col in tarefas_df.columns if col != 'Categoria']
    
    corpo = f"""Prezado Responsável pela Categoria {categoria},

Segue a lista detalhada de tarefas para sua área:

"""
    
    # Para cada tarefa, mostrar todas as colunas
    for index, row in tarefas_df.iterrows():
        corpo += f"📋 Tarefa {index + 1}:\n"
        
        for coluna in colunas:
            valor = row[coluna]
            # Formatar valores NaN ou vazios
            if pd.isna(valor) or valor == "":
                valor = "Não informado"
            corpo += f"   • {coluna}: {valor}\n"
        
        corpo += "\n"  # Espaço entre tarefas
    
    corpo += f"""
Total de tarefas: {len(tarefas_df)}

Atenciosamente,
Sistema de Automação
"""
    
    return corpo

def obter_configuracao_email(parent_window):
    """Obtém as configurações de e-mail - usa salvas ou pergunta ao usuário"""
    # Verificar se as configurações estão preenchidas no config.py
    if (CONFIG_EMAIL['email'] and CONFIG_EMAIL['email'] != 'seu_email@gmail.com' and
        CONFIG_EMAIL['senha'] and CONFIG_EMAIL['senha'] != 'sua_senha_app'):
        
        reply = QMessageBox.question(
            parent_window,
            "Configuração de E-mail",
            f"Usar configuração salva?\nE-mail: {CONFIG_EMAIL['email']}\n\n"
            "Clique 'Não' para usar outro e-mail.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            return CONFIG_EMAIL
    
    # Se não quiser usar o salvo ou não estiver configurado, pedir ao usuário
    return obter_configuracao_email_interativo(parent_window)

def obter_configuracao_email_interativo(parent_window):
    """Obtém as configurações de e-mail interativamente"""
    email, ok = QInputDialog.getText(
        parent_window,
        "Configuração de E-mail",
        "Digite seu e-mail:"
    )
    
    if not ok or not email:
        return None
    
    senha, ok = QInputDialog.getText(
        parent_window,
        "Configuração de E-mail",
        "Digite sua senha do e-mail:",
        echo=QLineEdit.Password
    )
    
    if not ok or not senha:
        return None
    
    smtp_server, ok = QInputDialog.getText(
        parent_window,
        "Servidor SMTP",
        "Digite o servidor SMTP (ex: smtp.gmail.com):",
        text="smtp.gmail.com"
    )
    
    if not ok or not smtp_server:
        return None
    
    smtp_port, ok = QInputDialog.getInt(
        parent_window,
        "Porta SMTP",
        "Digite a porta SMTP (ex: 587):",
        value=587,
        minValue=1,
        maxValue=65535
    )
    
    if not ok:
        return None
    
    return {
        'email': email,
        'senha': senha,
        'smtp_server': smtp_server,
        'smtp_port': smtp_port
    }

def enviar_email_unico(remetente, senha, smtp_server, smtp_port, destinatario, assunto, corpo):
    """Envia um único e-mail"""
    # Criar mensagem
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = assunto
    
    # Adicionar corpo do e-mail
    msg.attach(MIMEText(corpo, 'plain'))
    
    # Conectar e enviar e-mail
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(remetente, senha)
    text = msg.as_string()
    server.sendmail(remetente, destinatario, text)
    server.quit()

def mostrar_resultado_envio(resultado, parent_window):
    """Mostra o resultado do envio de e-mails"""
    mensagem = f"""
RESULTADO DO ENVIO:

✅ E-mails enviados com sucesso: {resultado['enviados']}
📋 Categorias processadas: {', '.join(resultado['categorias_processadas']) if resultado['categorias_processadas'] else 'Nenhuma'}

"""
    
    if resultado['categorias_sem_responsavel']:
        mensagem += f"""
⚠️ Categorias sem responsável definido:
{', '.join(resultado['categorias_sem_responsavel'])}
"""
    
    if resultado['falhas']:
        mensagem += f"""
❌ Falhas no envio:
{' | '.join(resultado['falhas'][:3])}
"""
        if len(resultado['falhas']) > 3:
            mensagem += f"... e mais {len(resultado['falhas']) - 3} falhas"
    
    QMessageBox.information(parent_window, "Resultado do Envio", mensagem)

def visualizar_responsaveis(parent_window):
    """Mostra uma janela com todas as categorias e seus responsáveis"""
    responsaveis = dicionario()
    
    # Criar janela de visualização
    dialog = QDialog(parent_window)
    dialog.setWindowTitle("Categorias e Responsáveis")
    dialog.setFixedSize(400, 500)
    
    # Layout
    layout = QVBoxLayout(dialog)
    
    # Título
    title_label = QLabel("Categorias e Responsáveis")
    title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
    title_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(title_label)
    
    # Texto com as categorias
    text_edit = QTextEdit()
    text_edit.setReadOnly(True)
    
    # Adicionar categorias ao texto
    for categoria, email in responsaveis.items():
        text_edit.append(f"📋 {categoria}")
        text_edit.append(f"   👤 {email}")
        text_edit.append("")
    
    layout.addWidget(text_edit)
    
    # Botão fechar
    fechar_btn = QPushButton("Fechar")
    fechar_btn.clicked.connect(dialog.close)
    layout.addWidget(fechar_btn)

    dialog.exec()

def configurar_email(parent_window):
    """Janela para configurar e-mail e senha"""
    dialog = QDialog(parent_window)
    dialog.setWindowTitle("Configuração de E-mail")
    dialog.setFixedSize(400, 350)
    
    # Layout
    layout = QVBoxLayout(dialog)
    layout.setSpacing(10)
    
    # Título
    title_label = QLabel("Configuração de E-mail")
    title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
    title_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(title_label)
    
    # E-mail
    layout.addWidget(QLabel("Seu E-mail:"))
    email_edit = QLineEdit()
    email_edit.setText(CONFIG_EMAIL['email'])
    layout.addWidget(email_edit)
    
    # Senha
    layout.addWidget(QLabel("Senha:"))
    senha_edit = QLineEdit()
    senha_edit.setText(CONFIG_EMAIL['senha'])
    senha_edit.setEchoMode(QLineEdit.Password)
    layout.addWidget(senha_edit)
    
    # Servidor SMTP
    layout.addWidget(QLabel("Servidor SMTP:"))
    smtp_edit = QLineEdit()
    smtp_edit.setText(CONFIG_EMAIL['smtp_server'])
    layout.addWidget(smtp_edit)
    
    # Porta SMTP
    layout.addWidget(QLabel("Porta SMTP:"))
    porta_edit = QLineEdit()
    porta_edit.setText(str(CONFIG_EMAIL['smtp_port']))
    layout.addWidget(porta_edit)
    
    # Botões
    button_layout = QVBoxLayout()
    
    def salvar_configuracao():
        """Salva a configuração no arquivo config.py"""
        try:
            novo_config = f'''# Configurações de E-mail
CONFIG_EMAIL = {{
    'email': '{email_edit.text()}',
    'senha': '{senha_edit.text()}',
    'smtp_server': '{smtp_edit.text()}',
    'smtp_port': {porta_edit.text()}
}}
'''
            with open('EMAIL/config.py', 'w', encoding='utf-8') as f:
                f.write(novo_config)
            
            QMessageBox.information(dialog, "Sucesso", "Configuração salva com sucesso!")
            dialog.close()
            
        except Exception as e:
            QMessageBox.critical(dialog, "Erro", f"Erro ao salvar configuração: {str(e)}")
    
    salvar_btn = QPushButton("Salvar")
    salvar_btn.clicked.connect(salvar_configuracao)
    button_layout.addWidget(salvar_btn)
    
    cancelar_btn = QPushButton("Cancelar")
    cancelar_btn.clicked.connect(dialog.close)
    button_layout.addWidget(cancelar_btn)
    
    layout.addLayout(button_layout)
    
    dialog.exec()
