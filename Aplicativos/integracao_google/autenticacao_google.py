import os
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Escopos que permitiremos o nosso aplicativo usar.
# Se modificar esses escopos, delete o arquivo token.json.
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/script.deployments'
]

def get_google_credentials() -> Credentials:
    """
    Obtém as credenciais do Google API (via token.json ou pedindo login).
    
    Returns:
        Credentials: Objeto de credencial do Google para uso nos serviços.
    """
    base_dir = Path(__file__).parent
    token_path = base_dir / 'token.json'
    cred_path = base_dir / 'credentials.json'

    creds = None

    # O arquivo token.json armazena os tokens de acesso e de atualização do usuário
    # criados automaticamente na primeira vez que o fluxo de autorização for concluído.
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    # Se não existem credenciais (ou não são válidas), deixa o usuário fazer login.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Atualizando token de acesso do Google...")
            creds.refresh(Request())
        else:
            if not cred_path.exists():
                raise FileNotFoundError(
                    f"O arquivo {cred_path.name} não foi encontrado na pasta do projeto. "
                    "Baixe do Google Cloud Console e o coloque aqui."
                )
            print("Iniciando fluxo de login no navegador...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(cred_path), SCOPES
            )
            # Retorna as credenciais via redirecionamento de porta localhost
            creds = flow.run_local_server(port=0)
            
        # Salva a credencial para o próximo uso
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            print("Novo token salvo com sucesso!")

    return creds

if __name__ == "__main__":
    try:
        cred = get_google_credentials()
        print(f"Sucesso! Credencial carregada: {cred.valid}")
    except Exception as e:
        print(f"Erro ao obter credenciais Google: {e}")
