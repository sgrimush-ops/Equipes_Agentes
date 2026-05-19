from googleapiclient.discovery import build
from autenticacao_google import get_google_credentials

def check_wiki_sheet():
    cred = get_google_credentials()
    service = build('sheets', 'v4', credentials=cred)
    id_planilha = '1bGgibeiHfnX35Re7joK68Q6AqSif8uJwomuli_xrWGA'
    
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=id_planilha).execute()
        print(f"Planilha: {spreadsheet['properties']['title']}")
        for s in spreadsheet.get('sheets', []):
            name = s['properties']['title']
            rows = s['properties'].get('gridProperties', {}).get('rowCount', 0)
            print(f" - Aba: {name} ({rows} linhas)")
            
            # Ler dados da aba Topicos
            if name == "Topicos":
                res = service.spreadsheets().values().get(spreadsheetId=id_planilha, range='Topicos!A1:E10').execute()
                print(f"   Dados em Topicos: {len(res.get('values', []))} linhas encontradas.")
    except Exception as e:
        print(f"ERRO AO ACESSAR: {e}")

if __name__ == "__main__":
    check_wiki_sheet()
