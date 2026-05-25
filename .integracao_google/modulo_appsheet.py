import os
import requests
from dotenv import load_dotenv

# Carrega variáveis do .env se existirem
load_dotenv()

APPSHEET_APP_ID = os.getenv("APPSHEET_APP_ID")
APPSHEET_ACCESS_KEY = os.getenv("APPSHEET_ACCESS_KEY")
APPSHEET_BASE_URL = "https://api.appsheet.com/api/v2"

def consultar_tabela_appsheet(nome_tabela: str) -> dict:
    """
    Consulta os dados de uma tabela específica no AppSheet.

    Args:
        nome_tabela (str): Nome da tabela exatamente como está no AppSheet.
    
    Returns:
        dict: Resposta completa da API do AppSheet (em formato dicionário).
    """
    if not APPSHEET_APP_ID or not APPSHEET_ACCESS_KEY:
        print("Erro: As credenciais do AppSheet (APPSHEET_APP_ID e APPSHEET_ACCESS_KEY) não estão no arquivo .env.")
        print("Crie um arquivo .env na base do projeto e defina essas variáveis.")
        return {}

    url = f"{APPSHEET_BASE_URL}/apps/{APPSHEET_APP_ID}/tables/{nome_tabela}/Action"

    headers = {
        "ApplicationAccessKey": APPSHEET_ACCESS_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "Action": "Find",
        "Properties": {
            "Locale": "pt-BR",
            "Timezone": "E. South America Standard Time"
        },
        "Rows": [] # Vazio significa ler tudo ou usando limit.
    }

    print(f"Fazendo requisição ao AppSheet na tabela: '{nome_tabela}'...")

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() # Dispara exceção se não for 2XX
        data = response.json()
        print(f"Sucesso! Retornados {len(data)} registros (ou ação completada).")
        return data

    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição para o AppSheet: {e}")
        if response is not None:
             print(f"Detalhes do Erro na API: {response.text}")
        return {}

if __name__ == "__main__":
    tabela_teste = input("Digite o nome da tabela do AppSheet para testar (ex: 'Clientes'): ")
    resultado = consultar_tabela_appsheet(tabela_teste)
    
    if type(resultado) == list and len(resultado) > 0:
        print("\nPrimeiro registro da tabela:")
        print(resultado[0])
