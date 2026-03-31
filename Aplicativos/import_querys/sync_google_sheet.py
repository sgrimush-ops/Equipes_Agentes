import sys
import os
import pandas as pd
import numpy as np

# Adiciona a pasta raiz ao sys.path para importar o modulo de autenticação do Google
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from integracao_google.autenticacao_google import get_google_credentials
from googleapiclient.discovery import build

def sync_ean_dun_to_sheets():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    arquivo_txt = os.path.join(current_dir, 'ean_dun.txt')
    arquivo_parquet = os.path.join(current_dir, 'query.parquet')
    
    SPREADSHEET_ID = '1_qgyE7V4Pd6Xw3FifWPMsApCYpA2_XHjAbemwlsedNw'
    RANGE_NAME = 'BaseDados!A:Z' 
    
    if not os.path.exists(arquivo_txt) or not os.path.exists(arquivo_parquet):
        print(f"[ERRO] Falta arquivo na pasta. Verifique ean_dun.txt e query.parquet.")
        return

    print("📊 Carregando bases de dados na memória. Opção 3: Filtrar apenas os ATIVOS...")
    
    # Lendo o TXT garantindo tipos como String para não perder zeros à esquerda no EAN
    df_txt = pd.read_csv(arquivo_txt, sep=';', encoding='iso-8859-1', dtype=str)
    
    # Tratando colunas inconsistentes (ex: coluna Unnamed vazia no final da linha)
    if df_txt.columns[-1].startswith('Unnamed'):
        df_txt = df_txt.drop(columns=[df_txt.columns[-1]])
        
    print(f"-> ean_dun.txt carregado com {len(df_txt)} linhas (Bruto).")

    # Lendo a Base do Consinco que tem os Status Oficiais (query.parquet)
    df_pq = pd.read_parquet(arquivo_parquet, columns=['CODIGO_EMPRESA', 'CODIGO_PRODUTO', 'STATUS_COMPRA'])
    
    # Harmonizando nomes de colunas para o JOIN
    df_pq['CODIGO_LOJA'] = df_pq['CODIGO_EMPRESA'].astype(str)
    df_pq['CODIGO_PRODUTO'] = df_pq['CODIGO_PRODUTO'].astype(str)
    
    # Criamos o Set de Chaves Ativas (STATUS_COMPRA == 'Ativo')
    df_ativos = df_pq[df_pq['STATUS_COMPRA'] == 'Ativo'].copy()
    chaves_ativas = set(zip(df_ativos['CODIGO_LOJA'], df_ativos['CODIGO_PRODUTO']))
    
    print(f"-> Encontradas {len(chaves_ativas)} combinações Loja+Produto ATIVAS no ERP hoje.")
    
    # ------------------
    # A MÁGICA DO FILTRO
    # ------------------
    # Só mantém a linha do TXT se a combinação (LOJA, PRODUTO) existir na lista dos ativos
    df_txt['LOJA_PRODUTO'] = list(zip(df_txt['CODIGO_LOJA'], df_txt['CODIGO_PRODUTO']))
    df_final = df_txt[df_txt['LOJA_PRODUTO'].isin(chaves_ativas)].drop(columns=['LOJA_PRODUTO'])
    
    # Saneamento (Limpeza de Colunas e Duplicatas a pedido do usuário)
    colunas_lixo = [
        'CODIGO_LOJA', 'GRUPO', 'SUBGRUPO', 'NIVEL_4', 
        'PRECO_VENDA', 'ESTOQUE_ATUAL', 'QTD_VENDIDA_90D'
    ]
    
    # Remove as colunas inúteis da lista do AppSheet se elas existirem no DataFrame final (evita quebra por nome errado)
    df_final = df_final.drop(columns=[c for c in colunas_lixo if c in df_final.columns], errors='ignore')
    
    # Substitui NaNs puros pela string vazia ou número zero para a API do Google aceitar
    df_final = df_final.fillna("")
    
    # Como removemos a Loja, agora cada Produto + EAN que se repete pela rede vira idêntico nas outras lojas
    # Vamos fundir todos juntos eliminando duplicados absolutos
    linhas_antes = len(df_final)
    df_final = df_final.drop_duplicates()
    
    print(f"-> 📉 Saneamento feito! Excluídas as colunas irrelevantes.")
    print(f"-> 🗑️ De {linhas_antes} registros espalhados pelas lojas, resumimos a {len(df_final)} produtos+EAN únicos Ativos na rede inteira!")

    # Transforma o DataFrame em matriz exigida pelo Google Sheets API (incluindo o cabeçalho)
    valores_matriz = [df_final.columns.tolist()] + df_final.values.tolist()

    print("🚀 Preparando comunicação com a Nuvem Google...")
    try:
        creds = get_google_credentials()
        servico_sheets = build('sheets', 'v4', credentials=creds)
        sheet = servico_sheets.spreadsheets()
    except Exception as e:
        print(f"[ERRO DE AUTENTICAÇÃO] Não foi possível logar: {e}")
        return

    try:
        print("Limpando aba antiga no Google Sheets (1 segundo)...")
        sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()

        print("Enviando os dados puros, já filtrados e reduzidos...")
        body = {'values': valores_matriz}
        resultado = sheet.values().update(
            spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
            valueInputOption='USER_ENTERED', body=body).execute()

        print(f"✅ [SUCESSO ABSOLUTO] Carga leve aceita pelo Google! {resultado.get('updatedCells')} células enxutas registradas.")
        print(f"👉 Acesse para conferir: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
        
    except Exception as e:
        print(f"❌ [ERRO DE API] Rejeitado pelo Google: {e}")

if __name__ == '__main__':
    sync_ean_dun_to_sheets()
