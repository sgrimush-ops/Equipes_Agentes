import pandas as pd
import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

def sync_parquet_to_appsheet() -> None:
    """Extrai os registros nativos do Parquet e invoca o endpoint REST da nuvem AppSheet."""
    
    # 1. Autenticação Fixa Invisível (Conforme SKILL de Integração Google)
    load_dotenv()
    app_id = os.getenv('APPSHEET_APP_ID')
    access_key = os.getenv('APPSHEET_ACCESS_KEY')
    
    # Definir o nome exato da aba/tabela alvo no AppSheet (padrão: GestaoCompras)
    table_name = os.getenv('APPSHEET_TABLE_COMPRAS', 'GestaoCompras')
    
    if not app_id or not access_key:
        print("❌ ALERTA DE SEGURANÇA: Chaves da API ('APPSHEET_APP_ID' e 'APPSHEET_ACCESS_KEY') não criadas no seu arquivo '.env'!")
        print("💡 Crie um arquivo '.env' na mesma pasta ou raiz do sistema para garantir a comunicação restrita.")
        return

    # 2. Carrega Dados do Parquet de Alta Velocidade
    parquet_path = Path('query.parquet')
    if not parquet_path.exists():
        print("❌ ERRO NATIVO: Arquivo query.parquet não enxergado na pasta atual. Rode o 'data.py' primeiro!")
        return
        
    print(f"📦 Descompactando Parquet e mapeando injeção em {table_name} na Nuvem...")
    
    try:
        df = pd.read_parquet(parquet_path)
        # Sanitiza campos nulos (NaN) para strings vazias, prevenindo 'NullPointerException' na leitura Web
        df = df.fillna("")
        records = df.to_dict(orient='records')
        print(f"📊 Volume extraído internamente: {len(records)} linhas massivas prontas para viagem.")
        
    except Exception as e:
        print(f"❌ Falha intrínseca de Dados: {e}")
        return

    # 3. Empacota a Carga em JSON e envia pro Gateway do AppSheet (Ação: ADD)
    url = f"https://api.appsheet.com/api/v2/apps/{app_id}/tables/{table_name}/Action"
    
    headers = {
        'ApplicationAccessKey': access_key,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "Action": "Add",
        "Properties": {
            "Locale": "pt-BR",
            "Timezone": "E. South America Standard Time"
        },
        "Rows": records
    }

    # 4. Transmissão REST API
    print("🚀 Acionando Gateway HTTP AppSheet Cloud...")
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print("✅ SUCESSO ABSOLUTO! Tabela alimentada pelo Python na nuvem remotamente!")
        else:
            print(f"❌ DEFEITO NA REQUISIÇÃO (HTTP {response.status_code}). AppSheet rejeitou o pacote. Resposta:")
            print(response.text)
            
    except requests.exceptions.RequestException as net_e:
        print(f"❌ INSTABILIDADE LOCAL: Rede com erro ou firewall impediu o POST: {net_e}")


if __name__ == '__main__':
    # Trava obrigatória de WD para terminal imposta pela Rule Mestra (Clean Code #3 Python)
    os.chdir(Path(__file__).parent.resolve())
    sync_parquet_to_appsheet()
