from googleapiclient.discovery import build
from autenticacao_google import get_google_credentials
from datetime import datetime

SPREADSHEET_ID = '1bGgibeiHfnX35Re7joK68Q6AqSif8uJwomuli_xrWGA'

def popular_topicos_iniciais():
    """
    Insere 3 tópicos iniciais na planilha para demonstração.
    """
    cred = get_google_credentials()
    service_sheets = build('sheets', 'v4', credentials=cred)
    
    agora = datetime.now().strftime("%d/%m/%Y")
    
    topicos = [
        # ID_Topico, Categoria, Titulo, Descricao, Status, Data
        ['T001', 'Sistemas', 'Melhorias de Pedidos', 'Sistema tem que ver estoque e venda de forma integrada para sugerir quantidades.', 'Aberta', agora],
        ['T002', 'Logística', 'Status de Entregas', 'Monitoramento de status em aberto das transportadoras locais.', 'Aberta', agora],
        ['T003', 'Bazar', 'Sincronização EAN/DUN', 'Padronização dos códigos de barras para novos fornecedores de Bazar.', 'Aberta', agora]
    ]
    
    print("Enviando tópicos iniciais para o Sheets...")
    service_sheets.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='Topicos!A2',
        valueInputOption='RAW',
        body={'values': topicos}
    ).execute()
    
    print("Tópicos inseridos com sucesso.")

if __name__ == "__main__":
    popular_topicos_iniciais()
