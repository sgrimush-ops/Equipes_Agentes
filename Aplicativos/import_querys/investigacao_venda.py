# investigacao_venda.py
import os
import pandas as pd
import numpy as np

# Descobre o diretório real onde o script está
base_dir = os.path.dirname(os.path.abspath(__file__))

# Caminhos dos arquivos
file_sistema = os.path.join(base_dir, 'venda_maio.csv')
file_query = os.path.join(base_dir, 'venda_maio_query.txt')

def clean_numeric(val):
    if pd.isna(val):
        return 0.0
    val_str = str(val).strip()
    if not val_str:
        return 0.0
    # Limpeza de formato brasileiro: 1.234,56 -> 1234.56
    if ',' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def principal():
    if not os.path.exists(file_sistema):
        print(f"Erro: Arquivo do sistema não encontrado em {file_sistema}")
        return
        
    if not os.path.exists(file_query):
        print(f"Erro: Arquivo da query não encontrado em {file_query}")
        return

    # 1. Carregar arquivos
    print("Carregando venda_maio.csv (Sistema)...")
    df_sis = pd.read_csv(file_sistema, sep=';', encoding='latin1')

    print("Carregando venda_maio_query.txt (Query)...")
    df_qry = pd.read_csv(file_query, sep=';', encoding='latin1')

    # 2. Padronizar nomes de colunas do sistema
    df_sis = df_sis.rename(columns={
        'Código Produto': 'CODIGO_PRODUTO',
        'Produto': 'PRODUTO',
        'CGO': 'CGO',
        'Quantidade': 'QUANTIDADE',
        'Valor Bruto': 'VALOR_BRUTO',
        'Valor Liquido': 'VALOR_LIQUIDO'
    })

    # Limpar linhas nulas de produto
    df_sis = df_sis.dropna(subset=['CODIGO_PRODUTO'])
    df_qry = df_qry.dropna(subset=['CODIGO_PRODUTO'])

    # 3. Formatar tipos de dados chaves
    df_sis['CODIGO_PRODUTO'] = pd.to_numeric(df_sis['CODIGO_PRODUTO'], errors='coerce').fillna(0).astype(int)
    df_sis['CGO'] = pd.to_numeric(df_sis['CGO'], errors='coerce').fillna(0).astype(int)
    df_qry['CODIGO_PRODUTO'] = pd.to_numeric(df_qry['CODIGO_PRODUTO'], errors='coerce').fillna(0).astype(int)
    df_qry['CGO'] = pd.to_numeric(df_qry['CGO'], errors='coerce').fillna(0).astype(int)

    # Aplicar conversão numérica para valores monetários e quantidades
    for col in ['QUANTIDADE', 'VALOR_BRUTO', 'VALOR_LIQUIDO']:
        df_sis[col] = df_sis[col].apply(clean_numeric)
        df_qry[col] = df_qry[col].apply(clean_numeric)

    # 4. Fazer o merge (full outer join) para cruzar todas as chaves (CODIGO_PRODUTO, CGO)
    df_merged = pd.merge(
        df_sis, 
        df_qry, 
        on=['CODIGO_PRODUTO', 'CGO'], 
        how='outer', 
        suffixes=('_SIS', '_QRY')
    )

    # 5. Identificar divergências
    divergencias = []

    for idx, row in df_merged.iterrows():
        cod = int(row['CODIGO_PRODUTO'])
        cgo = int(row['CGO'])
        
        prod_sis = row['PRODUTO_SIS']
        prod_qry = row['PRODUTO_QRY']
        
        qtd_sis = row['QUANTIDADE_SIS'] if not pd.isna(row['QUANTIDADE_SIS']) else 0.0
        qtd_qry = row['QUANTIDADE_QRY'] if not pd.isna(row['QUANTIDADE_QRY']) else 0.0
        
        vlr_sis = row['VALOR_BRUTO_SIS'] if not pd.isna(row['VALOR_BRUTO_SIS']) else 0.0
        vlr_qry = row['VALOR_BRUTO_QRY'] if not pd.isna(row['VALOR_BRUTO_QRY']) else 0.0
        
        # Caso 1: Faltando no Sistema (Existe na Query mas não no CSV do Sistema)
        if pd.isna(row['PRODUTO_SIS']) and pd.isna(row['QUANTIDADE_SIS']) and pd.isna(row['VALOR_BRUTO_SIS']):
            status = 'Faltando no Sistema (venda_maio.csv)'
            diff = vlr_qry
            divergencias.append({
                'CODIGO_PRODUTO': cod,
                'PRODUTO_SISTEMA': None,
                'PRODUTO_QUERY': prod_qry,
                'CGO': cgo,
                'QTD_SISTEMA': 0.0,
                'QTD_QUERY': qtd_qry,
                'VALOR_BRUTO_SISTEMA': 0.0,
                'VALOR_BRUTO_QUERY': vlr_qry,
                'DIFERENCA_VALOR': diff,
                'STATUS': status
            })
        # Caso 2: Faltando na Query (Existe no CSV do Sistema mas não no txt da Query)
        elif pd.isna(row['PRODUTO_QRY']) and pd.isna(row['QUANTIDADE_QRY']) and pd.isna(row['VALOR_BRUTO_QRY']):
            status = 'Faltando na Query (venda_maio_query.txt)'
            diff = -vlr_sis
            divergencias.append({
                'CODIGO_PRODUTO': cod,
                'PRODUTO_SISTEMA': prod_sis,
                'PRODUTO_QUERY': None,
                'CGO': cgo,
                'QTD_SISTEMA': qtd_sis,
                'QTD_QUERY': 0.0,
                'VALOR_BRUTO_SISTEMA': vlr_sis,
                'VALOR_BRUTO_QUERY': 0.0,
                'DIFERENCA_VALOR': diff,
                'STATUS': status
            })
        # Caso 3: Presente em ambos, mas com divergência de valor de venda bruta (tolerância de 1 centavo)
        else:
            diff = vlr_qry - vlr_sis
            if abs(diff) > 0.01:
                status = 'Divergencia de Valor'
                divergencias.append({
                    'CODIGO_PRODUTO': cod,
                    'PRODUTO_SISTEMA': prod_sis,
                    'PRODUTO_QUERY': prod_qry,
                    'CGO': cgo,
                    'QTD_SISTEMA': qtd_sis,
                    'QTD_QUERY': qtd_qry,
                    'VALOR_BRUTO_SISTEMA': vlr_sis,
                    'VALOR_BRUTO_QUERY': vlr_qry,
                    'DIFERENCA_VALOR': diff,
                    'STATUS': status
                })

    df_div = pd.DataFrame(divergencias)

    # 6. Salvar e apresentar resultados
    output_excel = os.path.join(base_dir, 'divergencias_venda_maio.xlsx')

    if not df_div.empty:
        # Adicionar coluna temporária para ordenar de forma decrescente pela diferença absoluta
        df_div['DIFERENCA_ABS'] = df_div['DIFERENCA_VALOR'].abs()
        df_div = df_div.sort_values(by='DIFERENCA_ABS', ascending=False)
        df_div = df_div.drop(columns=['DIFERENCA_ABS'])
        
        # Salvar a planilha com os itens divergentes
        df_div.to_excel(output_excel, index=False)
        print(f"\nDivergencias encontradas! Total: {len(df_div)} registros divergentes.")
        print(f"Planilha gerada com sucesso em: {output_excel}")
        
        # Resumo quantitativo por tipo de divergência
        print("\nResumo por tipo de divergencia:")
        print(df_div['STATUS'].value_counts())
        
        # Mostrar as maiores divergências encontradas
        print("\nAs 10 maiores divergencias em valor:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(df_div.head(10)[['CODIGO_PRODUTO', 'CGO', 'VALOR_BRUTO_SISTEMA', 'VALOR_BRUTO_QUERY', 'DIFERENCA_VALOR', 'STATUS']])
    else:
        print("\nNenhuma divergencia de itens ou valores encontrada! A venda bate perfeitamente entre os arquivos.")

if __name__ == '__main__':
    principal()
