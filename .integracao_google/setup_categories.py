import json
import os
from googleapiclient.discovery import build
from autenticacao_google import get_google_credentials

def setup_categories_sheet():
    creds = get_google_credentials()
    service = build('sheets', 'v4', credentials=creds)
    spreadsheet_id = '1bGgibeiHfnX35Re7joK68Q6AqSif8uJwomuli_xrWGA'
    
    # 1. Verificar se a aba 'Categorias' existe
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = spreadsheet.get('sheets', [])
    sheet_names = [s['properties']['title'] for s in sheets]
    
    if 'Categorias' not in sheet_names:
        print("Criando aba 'Categorias'...")
        batch_update_request = {
            'requests': [
                {
                    'addSheet': {
                        'properties': {
                            'title': 'Categorias'
                        }
                    }
                }
            ]
        }
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=batch_update_request).execute()
        
        # 2. Adicionar cabeçalho e categorias iniciais
        values = [
            ["Categoria"],
            ["Supply"],
            ["Comercial"],
            ["Financeiro"],
            ["Logistica"],
            ["Sistemas"],
            ["Outros"]
        ]
        body = {'values': values}
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range='Categorias!A1',
            valueInputOption='RAW', body=body).execute()
        print("Aba 'Categorias' configurada com sucesso!")
    else:
        print("Aba 'Categorias' já existe.")

if __name__ == "__main__":
    setup_categories_sheet()
