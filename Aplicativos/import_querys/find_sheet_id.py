import os
import sys
from pathlib import Path
import importlib.util

def load_google_credentials():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    auth_script_path = os.path.abspath(os.path.join(current_dir, '..', '..', '.integracao_google', 'autenticacao_google.py'))
    
    spec = importlib.util.spec_from_file_location("autenticacao_google", auth_script_path)
    autenticacao_google = importlib.util.module_from_spec(spec)
    sys.modules["autenticacao_google"] = autenticacao_google
    spec.loader.exec_module(autenticacao_google)
    
    return autenticacao_google.get_google_credentials()

def find_sheet():
    from googleapiclient.discovery import build
    creds = load_google_credentials()
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Busca por planilhas chamadas DataFrame_Baklizi
    query = "name contains 'DataFrame_Baklizi' and mimeType='application/vnd.google-apps.spreadsheet'"
    results = drive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    items = results.get('files', [])
    
    if not items:
        print("Nenhuma planilha encontrada com esse nome.")
    else:
        for item in items:
            print(f"ENCONTRADO: {item['name']} - ID: {item['id']}")
            try:
                sheet = build('sheets', 'v4', credentials=creds).spreadsheets()
                result = sheet.get(spreadsheetId=item['id']).execute()
                print("ABAS:")
                for s in result.get('sheets', []):
                    print(f" - {s.get('properties', {}).get('title')}")
            except Exception as e:
                print(f"Erro ao ler abas: {e}")

if __name__ == '__main__':
    find_sheet()
