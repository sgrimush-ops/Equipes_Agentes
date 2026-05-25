import os
from googleapiclient.discovery import build
from autenticacao_google import get_google_credentials

def criar_planilha_wiki():
    """
    Cria a planilha base para a Wikipedia Interna Colaborativa.
    """
    cred = get_google_credentials()
    service_sheets = build('sheets', 'v4', credentials=cred)
    
    # 1. Criar a planilha
    spreadsheet = {
        'properties': {
            'title': 'Wikipedia_Interna_Database'
        },
        'sheets': [
            {'properties': {'title': 'Topicos'}},
            {'properties': {'title': 'Interacoes'}}
        ]
    }
    
    print("Criando planilha no Google Sheets...")
    sheet = service_sheets.spreadsheets().create(body=spreadsheet, fields='spreadsheetId').execute()
    sheet_id = sheet.get('spreadsheetId')
    print(f"Planilha criada com sucesso! ID: {sheet_id}")
    
    # 2. Inserir Cabeçalhos
    headers_topicos = [['ID_Topico', 'Categoria', 'Titulo', 'Descricao_Demanda', 'Status', 'Data_Criacao']]
    headers_interacoes = [['ID_Interacao', 'ID_Topico', 'Usuario', 'Comentario', 'Data_Hora']]
    
    # Escrever cabeçalhos na aba Topicos
    service_sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range='Topicos!A1',
        valueInputOption='RAW',
        body={'values': headers_topicos}
    ).execute()
    
    # Escrever cabeçalhos na aba Interacoes
    service_sheets.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range='Interacoes!A1',
        valueInputOption='RAW',
        body={'values': headers_interacoes}
    ).execute()
    
    print("Cabeçalhos configurados com sucesso.")
    print(f"URL da Planilha: https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
    return sheet_id

if __name__ == "__main__":
    criar_planilha_wiki()
