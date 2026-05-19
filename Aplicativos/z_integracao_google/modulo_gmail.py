from googleapiclient.discovery import build
from autenticacao_google import get_google_credentials

def listar_ultimos_emails(limite: int = 5):
    """
    Lista os últimos e-mails recebidos na caixa de entrada do Gmail.

    Args:
        limite (int): O número de e-mails para ler.
    """
    cred = get_google_credentials()
    service = build('gmail', 'v1', credentials=cred)

    print(f"Buscando os últimos {limite} e-mails na caixa de entrada...")
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=limite).execute()
    messages = results.get('messages', [])

    if not messages:
        print('Nenhum e-mail encontrado.')
    else:
        print('E-mails Encontrados:')
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id'], format='metadata').execute()
            headers = msg.get('payload', {}).get('headers', [])
            
            # Buscando o assunto do cabeçalho
            subject = "Sem Assunto"
            remetente = "Desconhecido"
            for header in headers:
                if header['name'].lower() == 'subject':
                    subject = header['value']
                if header['name'].lower() == 'from':
                    remetente = header['value']
                    
            print(f" - De: {remetente} | Assunto: {subject}")

    return messages

if __name__ == "__main__":
    listar_ultimos_emails()
