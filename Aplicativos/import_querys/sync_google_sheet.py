import sys
import os
import pandas as pd

# Adiciona a pasta raiz ao sys.path para importar o modulo de autenticação do Google
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from integracao_google.autenticacao_google import get_google_credentials
from googleapiclient.discovery import build

# ---------------------------------------------------------------------------
# Colunas esperadas no ean_dun.txt (versão reduzida)
# EAN_DUN | CODIGO_PRODUTO | DESCRICAO | DEPARTAMENTO
# ---------------------------------------------------------------------------
COLUNAS_ESPERADAS = {'EAN_DUN', 'CODIGO_PRODUTO', 'DESCRICAO', 'DEPARTAMENTO'}

def sync_ean_dun_to_sheets() -> None:
    """Filtra o ean_dun.txt pelos produtos ATIVOS do ERP e sobe ao Google Sheets."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    arquivo_txt     = os.path.join(current_dir, 'ean_dun.txt')
    arquivo_parquet = os.path.join(current_dir, 'query.parquet')

    SPREADSHEET_ID = '1Clil3OGwLSG31mkRjQ9rZxw3c63C9CAYzeEwuwnD_dg'
    RANGE_NAME     = 'dataframe!A:Z'

    # 1. Verificação de existência dos arquivos
    for arq in [arquivo_txt, arquivo_parquet]:
        if not os.path.exists(arq):
            print(f"[ERRO] Arquivo não encontrado: {arq}")
            return

    # 2. Carregar e VALIDAR o ean_dun.txt
    print("[INFO] Carregando ean_dun.txt...")
    df_txt = pd.read_csv(arquivo_txt, sep=';', encoding='cp1252', dtype=str)

    # Remove coluna Unnamed fantasma gerada por ';' extra no final da linha
    df_txt = df_txt.loc[:, ~df_txt.columns.str.startswith('Unnamed')]

    # Validação: checar se as colunas esperadas existem
    colunas_encontradas = set(df_txt.columns)
    colunas_faltando    = COLUNAS_ESPERADAS - colunas_encontradas
    colunas_extras      = colunas_encontradas - COLUNAS_ESPERADAS

    if colunas_faltando:
        print(f"[ERRO] Colunas ausentes no ean_dun.txt: {colunas_faltando}")
        print(f"       Colunas encontradas: {list(df_txt.columns)}")
        return

    if colunas_extras:
        print(f"[AVISO] Colunas extras ignoradas: {colunas_extras}")
        df_txt = df_txt[list(COLUNAS_ESPERADAS)]

    print(f"   [OK] Estrutura valida: {list(df_txt.columns)}")
    print(f"   -> {len(df_txt)} linhas brutas carregadas.")

    # Sanear CODIGO_PRODUTO: remover '.0' decimal e strip
    df_txt['CODIGO_PRODUTO'] = (
        df_txt['CODIGO_PRODUTO']
        .str.strip()
        .apply(lambda v: str(int(float(v))) if pd.notna(v) and v not in ('', 'nan') else '')
    )

    # 3. Carregar produtos ATIVOS do ERP (query.parquet)
    print("[INFO] Identificando produtos ATIVOS no ERP (query.parquet)...")
    df_pq = pd.read_parquet(arquivo_parquet, columns=['CODIGO_PRODUTO', 'STATUS_COMPRA'])
    df_pq['CODIGO_PRODUTO'] = df_pq['CODIGO_PRODUTO'].astype(str).str.strip()

    # Um produto é considerado ativo se ele for 'Ativo' em QUALQUER loja da rede
    produtos_ativos = set(
        df_pq[df_pq['STATUS_COMPRA'] == 'Ativo']['CODIGO_PRODUTO'].unique()
    )
    print(f"   -> {len(produtos_ativos)} produtos únicos ATIVOS na rede.")

    # 4. Filtrar o ean_dun apenas pelos produtos ativos
    df_final = df_txt[df_txt['CODIGO_PRODUTO'].isin(produtos_ativos)].copy()
    df_final = df_final.drop_duplicates()
    df_final = df_final.fillna("")

    print(f"   -> De {len(df_txt)} linhas brutas -> {len(df_final)} produtos ativos unicos.")

    # 5. Montar matriz para envio (cabecalho + dados)
    # NOTA: EAN_DUN nao recebe prefixo apostrofo pois e a coluna Key do AppSheet.
    # A conversao para Text deve ser feita manualmente na configuracao do AppSheet.
    valores_matriz = [df_final.columns.tolist()] + df_final.values.tolist()


    print("[INFO] Conectando ao Google Sheets...")
    try:
        creds = get_google_credentials()
        servico_sheets = build('sheets', 'v4', credentials=creds)
        sheet = servico_sheets.spreadsheets()
    except Exception as e:
        print(f"[ERRO DE AUTENTICAÇÃO] {e}")
        return

    try:
        print("   Limpando aba antiga...")
        sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()

        print("   Enviando dados filtrados...")
        body = {'values': valores_matriz}
        resultado = sheet.values().update(
            spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME,
            valueInputOption='USER_ENTERED', body=body
        ).execute()

        print(f"[SUCESSO] {resultado.get('updatedCells')} celulas enviadas.")
        print(f"Acesse: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")

    except Exception as e:
        print(f"[ERRO DE API] {e}")


if __name__ == '__main__':
    sync_ean_dun_to_sheets()
