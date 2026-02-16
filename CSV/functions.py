import pandas as pd
import os
from PySide6.QtWidgets import QFileDialog, QMessageBox, QInputDialog

def dividir_csv(parent_window):
    """Função para dividir um arquivo CSV em partes com número específico de linhas"""
    try:
        # Abrir diálogo para selecionar arquivo
        file_path, _ = QFileDialog.getOpenFileName(
            parent_window,
            "Selecione o arquivo CSV para dividir",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Ler o arquivo CSV
        df = pd.read_csv(file_path)
        total_linhas = len(df)
        
        # Perguntar o número de linhas por arquivo
        linhas_por_arquivo, ok = QInputDialog.getInt(
            parent_window,
            "Dividir CSV",
            f"O arquivo tem {total_linhas} linhas.\nEm quantas linhas por arquivo deseja dividir?",
            value=1000,
            minValue=1,
            maxValue=total_linhas
        )
        
        if not ok:
            return
        
        # Calcular número de arquivos necessários
        num_arquivos = (total_linhas + linhas_por_arquivo - 1) // linhas_por_arquivo
        
        # Confirmar operação
        reply = QMessageBox.question(
            parent_window,
            "Confirmar Divisão",
            f"O arquivo será dividido em {num_arquivos} arquivos com {linhas_por_arquivo} linhas cada.\nContinuar?"
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Obter nome base do arquivo original
        nome_base = os.path.splitext(os.path.basename(file_path))[0]
        pasta_destino = "CSV"
        
        # Dividir o DataFrame
        arquivos_criados = []
        for i in range(num_arquivos):
            inicio = i * linhas_por_arquivo
            fim = min((i + 1) * linhas_por_arquivo, total_linhas)
            
            # Extrair parte do DataFrame
            parte_df = df.iloc[inicio:fim]
            
            # Nome do arquivo
            nome_arquivo = f"{nome_base}_parte_{i+1:03d}.csv"
            caminho_completo = os.path.join(pasta_destino, nome_arquivo)
            
            # Salvar arquivo
            parte_df.to_csv(caminho_completo, index=False, encoding='utf-8')
            arquivos_criados.append(nome_arquivo)
        
        # Mostrar resultado
        QMessageBox.information(
            parent_window,
            "Divisão Concluída",
            f"Arquivo dividido com sucesso!\n"
            f"Total de arquivos criados: {num_arquivos}\n"
            f"Linhas por arquivo: {linhas_por_arquivo}\n"
            f"Arquivos salvos na pasta: {pasta_destino}/\n\n"
            f"Primeiros arquivos:\n" + "\n".join(arquivos_criados[:5]) + 
            (f"\n... e mais {len(arquivos_criados) - 5} arquivos" if len(arquivos_criados) > 5 else "")
        )
        
    except Exception as e:
        QMessageBox.critical(parent_window, "Erro", f"Erro ao dividir CSV: {str(e)}")

def formatar_csv(parent_window):
    """Função para formatar CSV e enviar para Google Sheets"""
    try:
        # Abrir diálogo para selecionar arquivo
        file_path, _ = QFileDialog.getOpenFileName(
            parent_window,
            "Selecione o arquivo CSV para formatar",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Perguntar se deseja salvar localmente ou no Google Sheets
        reply = QMessageBox.question(
            parent_window,
            "Destino do Arquivo",
            "Onde deseja salvar o arquivo formatado?\n\n"
            "Sim: Google Sheets\nNão: Salvar localmente",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Cancel:
            return
        elif reply == QMessageBox.Yes:
            # Salvar no Google Sheets
            salvar_no_google_sheets(file_path, parent_window)
        else:
            # Salvar localmente (função original)
            salvar_localmente(file_path, parent_window)
        
    except Exception as e:
        QMessageBox.critical(parent_window, "Erro", f"Erro ao formatar CSV: {str(e)}")

def salvar_localmente(file_path, parent_window):
    """Salva o arquivo formatado localmente"""
    try:
        # Definir colunas para manter
        COLUNAS_PARA_MANTER = [
            "navigation_id", 
            "titulo", 
            "descrição", 
            "ativo", 
            "tipo de produto", 
            "id da categoria pai", 
            "id da subcategoria", 
            "link do produto"
        ]
        
        # Ler o arquivo CSV
        df_completo = pd.read_csv(file_path)
        
        # Verificar se as colunas necessárias existem no arquivo
        colunas_existentes = df_completo.columns.tolist()
        colunas_faltantes = [coluna for coluna in COLUNAS_PARA_MANTER if coluna not in colunas_existentes]
        
        if colunas_faltantes:
            QMessageBox.critical(
                parent_window,
                "Erro", 
                f"Colunas não encontradas no arquivo:\n{', '.join(colunas_faltantes)}\n\n"
                f"Colunas disponíveis:\n{', '.join(colunas_existentes)}"
            )
            return
        
        # Manter apenas as colunas especificadas
        df_filtrado = df_completo[COLUNAS_PARA_MANTER].copy()
        
        # Criar nova coluna 'link_backoffice'
        link_base = 'https://enrichment-backoffice.magalu.com/product-enrichment/'
        df_filtrado['link_backoffice'] = [f'{link_base}{n}/edit' for n in df_filtrado['navigation_id']]
        
        # Preencher valores NaN com string vazia
        df_filtrado = df_filtrado.fillna("")
        
        # Salvar arquivo formatado
        nome_base = os.path.splitext(os.path.basename(file_path))[0]
        novo_path = f"CSV/{nome_base}_formatado.csv"
        df_filtrado.to_csv(novo_path, index=False, encoding='utf-8')
        
        # Mostrar estatísticas
        QMessageBox.information(
            parent_window,
            "Formatação Concluída", 
            f"Arquivo formatado salvo como: {novo_path}\n\n"
            f"Estatísticas:\n"
            f"- Colunas mantidas: {len(COLUNAS_PARA_MANTER)}\n"
            f"- Coluna adicionada: link_backoffice\n"
            f"- Total de linhas: {len(df_filtrado)}\n"
            f"- Total de colunas: {len(df_filtrado.columns)}"
        )
        
    except Exception as e:
        QMessageBox.critical(parent_window, "Erro", f"Erro ao salvar localmente: {str(e)}")

def salvar_no_google_sheets(file_path, parent_window):
    """Salva o arquivo formatado no Google Sheets"""
    try:
        # Importações necessárias para Google Sheets
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError:
            QMessageBox.critical(
                parent_window,
                "Bibliotecas Necessárias",
                "Para usar o Google Sheets, instale as bibliotecas:\n\n"
                "pip install gspread google-auth"
            )
            return
        
        # Definir escopos
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Definir colunas para manter
        COLUNAS_PARA_MANTER = [
            "navigation_id", 
            "titulo", 
            "descrição", 
            "ativo", 
            "tipo de produto", 
            "id da categoria pai", 
            "id da subcategoria", 
            "link do produto"
        ]
        
        # Pedir nome da planilha e aba
        nome_planilha, ok = QInputDialog.getText(
            parent_window,
            "Google Sheets - Nome da Planilha",
            "Digite o nome exato da planilha no Google Sheets:",
            text="Reprocessar Ofertas"
        )
        
        if not ok or not nome_planilha:
            return
        
        nome_aba, ok = QInputDialog.getText(
            parent_window,
            "Google Sheets - Nome da Aba",
            "Digite o nome da aba (deixe em branco para usar a primeira aba):",
            text=""
        )
        
        if not ok:
            return
        
        # Verificar se o arquivo de credenciais existe
        if not os.path.exists('credentials.json'):
            QMessageBox.critical(
                parent_window,
                "Arquivo de Credenciais",
                "Arquivo 'credentials.json' não encontrado.\n\n"
                "1. Acesse: https://console.cloud.google.com/\n"
                "2. Crie um projeto e ative Google Sheets API\n"
                "3. Crie uma Service Account\n"
                "4. Baixe o JSON e renomeie para 'credentials.json'\n"
                "5. Coloque na pasta do projeto"
            )
            return
        
        # Carregar credenciais
        try:
            creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
            client = gspread.authorize(creds)
        except Exception as e:
            QMessageBox.critical(
                parent_window,
                "Erro de Autenticação",
                f"Erro ao autenticar com Google Sheets:\n{str(e)}"
            )
            return
        
        # Abrir planilha
        try:
            spreadsheet = client.open(nome_planilha)
        except gspread.SpreadsheetNotFound:
            QMessageBox.critical(
                parent_window,
                "Planilha Não Encontrada",
                f"Planilha '{nome_planilha}' não encontrada.\n\n"
                "Verifique:\n"
                "1. O nome está exato\n"
                "2. A planilha foi compartilhada com o e-mail da service account"
            )
            return
        
        # Selecionar aba
        try:
            if nome_aba:
                sheet = spreadsheet.worksheet(nome_aba)
            else:
                sheet = spreadsheet.sheet1
        except gspread.WorksheetNotFound:
            QMessageBox.critical(
                parent_window,
                "Aba Não Encontrada",
                f"Aba '{nome_aba}' não encontrada na planilha."
            )
            return
        
        # Ler e processar o CSV
        try:
            df_completo = pd.read_csv(file_path)
            
            # Verificar se as colunas necessárias existem
            colunas_existentes = df_completo.columns.tolist()
            colunas_faltantes = [coluna for coluna in COLUNAS_PARA_MANTER if coluna not in colunas_existentes]
            
            if colunas_faltantes:
                QMessageBox.critical(
                    parent_window,
                    "Erro", 
                    f"Colunas não encontradas no arquivo:\n{', '.join(colunas_faltantes)}\n\n"
                    f"Colunas disponíveis:\n{', '.join(colunas_existentes)}"
                )
                return
            
            # Manter apenas as colunas especificadas
            df_filtrado = df_completo[COLUNAS_PARA_MANTER].copy()
            
            # Criar nova coluna 'link_backoffice'
            link_base = 'https://enrichment-backoffice.magalu.com/product-enrichment/'
            df_filtrado['link_backoffice'] = [f'{link_base}{n}/edit' for n in df_filtrado['navigation_id']]
            
            # Preencher valores NaN com string vazia
            df_filtrado = df_filtrado.fillna("")
            
        except Exception as e:
            QMessageBox.critical(
                parent_window,
                "Erro ao Processar CSV",
                f"Erro ao processar o arquivo CSV:\n{str(e)}"
            )
            return
        
        # Enviar para Google Sheets
        try:
            # Preparar dados para envio
            dados_para_enviar = [df_filtrado.columns.values.tolist()] + df_filtrado.values.tolist()
            
            # Calcular range dinamicamente
            num_colunas = len(df_filtrado.columns)
            num_linhas = len(dados_para_enviar)
            col_final = chr(64 + num_colunas)  # Converte número para letra (A, B, C...)
            
            # Limpar planilha existente (opcional)
            sheet.clear()
            
            # Enviar dados
            sheet.update(
                values=dados_para_enviar,
                range_name=f'A1:{col_final}{num_linhas}'
            )
            
            # Mostrar resultado
            QMessageBox.information(
                parent_window,
                "Upload Concluído",
                f"Dados enviados com sucesso para o Google Sheets!\n\n"
                f"Planilha: {nome_planilha}\n"
                f"Aba: {sheet.title}\n"
                f"Linhas enviadas: {len(df_filtrado)}\n"
                f"Colunas: {len(df_filtrado.columns)}\n\n"
                f"URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                parent_window,
                "Erro no Upload",
                f"Erro ao enviar dados para o Google Sheets:\n{str(e)}"
            )
        
    except Exception as e:
        QMessageBox.critical(parent_window, "Erro", f"Erro ao salvar no Google Sheets: {str(e)}")
