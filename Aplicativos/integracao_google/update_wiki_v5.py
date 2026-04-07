import os
from googleapiclient.discovery import build
from autenticacao_google import get_google_credentials

SPREADSHEET_ID = '1bGgibeiHfnX35Re7joK68Q6AqSif8uJwomuli_xrWGA'

def update_spreadsheet_v5():
    """
    Atualiza a planilha da Wiki:
    1. Adiciona cabeçalhos 'Reportado_por' e 'Responsavel' na aba Topicos (Colunas H e I).
    2. Cria uma nova aba 'Responsaveis' com nomes iniciais.
    """
    cred = get_google_credentials()
    service = build('sheets', 'v4', credentials=cred)
    
    # 1. Adicionar colunas H e I na aba Topicos
    print("Atualizando cabeçalhos da aba 'Topicos'...")
    headers = [['Reportado_por', 'Responsavel']]
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Topicos!H1',
        valueInputOption='RAW',
        body={'values': headers}
    ).execute()
    print("✅ Colunas 'Reportado_por' e 'Responsavel' adicionadas.")

    # 2. Criar aba Responsaveis usando batchUpdate
    print("Tentando criar nova aba 'Responsaveis'...")
    batch_update_request = {
        'requests': [
            {
                'addSheet': {
                    'properties': {
                        'title': 'Responsaveis'
                    }
                }
            }
        ]
    }
    
    try:
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=batch_update_request
        ).execute()
        print("✅ Aba 'Responsaveis' criada com sucesso.")
    except Exception as e:
        if "already exists" in str(e):
            print("ℹ️ A aba 'Responsaveis' já existe.")
        else:
            print(f"❌ Erro ao criar aba: {e}")

    # 3. Popular aba Responsaveis com valores iniciais
    print("Populando a lista de responsáveis...")
    responsaveis_data = [['Nome'], ['Walace'], ['Consultor Totvs']]
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Responsaveis!A1',
        valueInputOption='RAW',
        body={'values': responsaveis_data}
    ).execute()
    print("✅ Lista de responsáveis inicializada.")

if __name__ == "__main__":
    update_spreadsheet_v5()
