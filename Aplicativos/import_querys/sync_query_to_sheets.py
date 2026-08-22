import os
import sys
import pandas as pd
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import importlib.util

def load_google_credentials():
    # Caminho absoluto para o arquivo de autenticação do Google
    current_dir = os.path.dirname(os.path.abspath(__file__))
    auth_script_path = os.path.abspath(os.path.join(current_dir, '..', '..', '.integracao_google', 'autenticacao_google.py'))
    
    if not os.path.exists(auth_script_path):
        raise FileNotFoundError(f"Script de autenticação não encontrado: {auth_script_path}")
        
    spec = importlib.util.spec_from_file_location("autenticacao_google", auth_script_path)
    autenticacao_google = importlib.util.module_from_spec(spec)
    sys.modules["autenticacao_google"] = autenticacao_google
    spec.loader.exec_module(autenticacao_google)
    
    return autenticacao_google.get_google_credentials()

def upload_parquet_to_sheet(sheet, spreadsheet_id, parquet_path, sheet_tab):
    """Lê um arquivo parquet e envia para a aba correspondente no Google Sheets."""
    if not os.path.exists(parquet_path):
        print(f"[ERRO] Arquivo {parquet_path} não encontrado! Abortando envio desta aba.")
        return

    range_name = f"{sheet_tab}!A:Z"
    
    print(f"\n[INFO] ----------------------------------------------------")
    print(f"[INFO] Processando: {os.path.basename(parquet_path)} -> Aba: {sheet_tab}")
    print(f"[INFO] Carregando {parquet_path} com Pandas...")
    try:
        df = pd.read_parquet(parquet_path)
        # Substitui NaN para string vazia
        df = df.fillna("")
        # Converte para string para garantir que a API do Google aceite todos os tipos de dados sem erro
        df = df.astype(str)
        
        # Montar a matriz: cabeçalho na primeira linha, seguido dos dados
        valores_matriz = [df.columns.tolist()] + df.values.tolist()
        print(f"[INFO] Lidos {len(valores_matriz) - 1} registros (linhas).")
    except Exception as e:
        print(f"[ERRO] Falha ao ler o Parquet: {e}")
        return

    try:
        # Primeiro, obtemos as planilhas existentes
        spreadsheet = sheet.get(spreadsheetId=spreadsheet_id).execute()
        existing_sheets = [s.get('properties', {}).get('title') for s in spreadsheet.get('sheets', [])]
        
        if sheet_tab not in existing_sheets:
            print(f"[INFO] Aba '{sheet_tab}' não existe. Criando automaticamente...")
            requests = [{'addSheet': {'properties': {'title': sheet_tab}}}]
            sheet.batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': requests}).execute()
        
        print(f"[INFO] Limpando aba '{sheet_tab}' (isso previne dados fantasmas de envios anteriores)...")
        sheet.values().clear(spreadsheetId=spreadsheet_id, range=range_name).execute()

        print("[INFO] Enviando pacote de dados (Batch Update)... isso leva apenas alguns segundos.")
        body = {'values': valores_matriz}
        resultado = sheet.values().update(
            spreadsheetId=spreadsheet_id, 
            range=range_name,
            valueInputOption='USER_ENTERED', 
            body=body
        ).execute()

        print(f"[SUCESSO] {resultado.get('updatedCells')} células foram atualizadas na aba {sheet_tab}.")
    except Exception as e:
        print(f"[ERRO] Falha durante a transmissão pro Sheets na aba {sheet_tab}: {e}")
        print(f"Nota: Certifique-se de que a aba '{sheet_tab}' existe na planilha e o Spreadsheet ID está correto.")
        sys.exit(1)


def sync_all_to_sheets() -> None:
    """Roda a conversão do EAN e envia os Parquets diretamente para o Google Sheets."""
    from googleapiclient.discovery import build
    
    # 1. Carregar variáveis de ambiente
    load_dotenv()
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Executar script de conversão de EAN/DUN antes de enviar
    convert_script = os.path.join(current_dir, 'convert_ean_dun.py')
    print(f"[INFO] Executando o script {convert_script} para garantir que ean_dun.parquet está atualizado...")
    try:
        subprocess.run([sys.executable, convert_script], check=True, cwd=current_dir)
        print("[INFO] Conversão do EAN/DUN concluída com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"[ERRO] Falha ao executar o convert_ean_dun.py: {e}")
        return
    except FileNotFoundError:
         print(f"[ERRO] Arquivo {convert_script} não encontrado!")
         return

    # ID da planilha e o nome das abas alvos
    SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID_COMPRAS', '1Clil3OGwLSG31mkRjQ9rZxw3c63C9CAYzeEwuwnD_dg') 
    SHEET_TAB_QUERY = os.getenv('APPSHEET_TABLE_COMPRAS', 'GestaoCompras')
    SHEET_TAB_EANDUN = os.getenv('APPSHEET_TABLE_EAN_DUN', 'EAN_DUN') # Default para EAN_DUN
    
    # Arquivos parquet
    parquet_query = os.path.join(current_dir, 'query.parquet')
    parquet_ean_dun = os.path.join(current_dir, 'ean_dun.parquet')

    # 3. Conectar ao Google Sheets
    print("\n[INFO] Conectando ao Google Sheets API...")
    try:
        creds = load_google_credentials()
        servico_sheets = build('sheets', 'v4', credentials=creds)
        sheet = servico_sheets.spreadsheets()
    except Exception as e:
        print(f"[ERRO] Não foi possível autenticar no Google Sheets: {e}")
        sys.exit(1)

    # 4. Fazer upload dos dois arquivos nas abas respectivas
    upload_parquet_to_sheet(sheet, SPREADSHEET_ID, parquet_query, SHEET_TAB_QUERY)
    upload_parquet_to_sheet(sheet, SPREADSHEET_ID, parquet_ean_dun, SHEET_TAB_EANDUN)
    
    print("\n=======================================================")
    print("[INFO] Sincronização finalizada com o Google Sheets!")
    print(f"[INFO] Link da Planilha: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print("[INFO] O AppSheet fará a leitura nativa destas duas abas.")

if __name__ == '__main__':
    # Trava obrigatória de WD para terminal
    os.chdir(Path(__file__).parent.resolve())
    sync_all_to_sheets()
