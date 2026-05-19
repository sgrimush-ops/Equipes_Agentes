from googleapiclient.discovery import build
from autenticacao_google import get_google_credentials

def listar_arquivos_drive(limite: int = 10):
    """
    Lista os últimos arquivos modificados no Google Drive do usuário.

    Args:
        limite (int): O número máximo de arquivos para exibir.
    """
    cred = get_google_credentials()
    service = build('drive', 'v3', credentials=cred)

    print(f"Buscando os últimos {limite} arquivos no Google Drive...")
    # Executa a busca. Ordena por última modificação e não considera pastas vazias se quiser.
    results = service.files().list(
        pageSize=limite, 
        fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
        orderBy="modifiedTime desc"
    ).execute()
    
    items = results.get('files', [])

    if not items:
        print('Nenhum arquivo encontrado.')
    else:
        print('Arquivos Encontrados:')
        for item in items:
            print(f" - {item['name']} (ID: {item['id']}) [Tipo: {item['mimeType']}]")

    return items

if __name__ == "__main__":
    listar_arquivos_drive()
