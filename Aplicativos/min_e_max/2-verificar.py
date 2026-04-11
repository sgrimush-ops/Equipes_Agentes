import os
import pandas as pd

def analisar_dados():
    # Caminhos baseados na raiz do projeto local
    pasta_base = r'c:\Users\Alessandro.soares.BAKLIZI\Downloads\Equipes_Agentes\Aplicativos'
    arquivo_resultado = os.path.join(pasta_base, 'min_e_max', 'resultado.parquet')
    arquivo_query = os.path.join(pasta_base, 'import_querys', 'query.parquet')
    arquivo_saida = os.path.join(pasta_base, 'min_e_max', 'verificado.csv')

    print("Carregando arquivos (resultado.parquet e query.parquet)...")
    try:
        df_resultado = pd.read_parquet(arquivo_resultado)
        df_query = pd.read_parquet(arquivo_query)
    except FileNotFoundError as e:
        print(f"Erro ao encontrar o arquivo: {e}")
        return

    # Garantir consistência dos tipos para o JOIN
    df_resultado['CODIGO_PRODUTO'] = df_resultado['CODIGO_PRODUTO'].astype(int)
    df_resultado['CODIGO_EMPRESA'] = df_resultado['CODIGO_EMPRESA'].astype(int)
    df_query['CODIGO_PRODUTO'] = df_query['CODIGO_PRODUTO'].astype(int)
    df_query['CODIGO_EMPRESA'] = df_query['CODIGO_EMPRESA'].astype(int)

    # Passo 1: Isolar dados do CD 15 a partir da query bruta
    print("Mapeando o estoque do CD 15...")
    df_cd15 = df_query[df_query['CODIGO_EMPRESA'] == 15][['CODIGO_PRODUTO', 'QUANTIDADE_DISPONIVEL']]
    # Caso possua múltiplas linhas de CD15 por algum motivo, agregamos ou pegamos o primeiro
    df_cd15 = df_cd15.groupby('CODIGO_PRODUTO', as_index=False).first()
    df_cd15 = df_cd15.rename(columns={'QUANTIDADE_DISPONIVEL': 'ESTOQUE_CD15'})

    # Passo 2: Buscar status de ativação da loja para cada linha no resultado
    print("Mapeando o Status do Produto de cada Loja...")
    df_status_lojas = df_query[['CODIGO_PRODUTO', 'CODIGO_EMPRESA', 'STATUS_COMPRA']]
    df_status_lojas = df_status_lojas.groupby(['CODIGO_PRODUTO', 'CODIGO_EMPRESA'], as_index=False).first()

    # Combinando os dados de base de analise com os status da loja
    df_analise = df_resultado.merge(df_status_lojas, on=['CODIGO_PRODUTO', 'CODIGO_EMPRESA'], how='left')

    # Combinando também com o estoque do CD15 para cruzamento
    df_analise = df_analise.merge(df_cd15, on='CODIGO_PRODUTO', how='left')
    
    # Padroniza dados da análise e do CD
    # Tratamento de vírgulas caso venha como string do parquet (comum em dumps do PL/SQL)
    if df_analise['ESTOQUE_CD15'].dtype == object:
        df_analise['ESTOQUE_CD15'] = df_analise['ESTOQUE_CD15'].str.replace(',', '.', regex=False)
    if df_analise['EMBL_TRANSFERENCIA'].dtype == object:
        df_analise['EMBL_TRANSFERENCIA'] = df_analise['EMBL_TRANSFERENCIA'].str.replace(',', '.', regex=False)

    df_analise['ESTOQUE_CD15'] = pd.to_numeric(df_analise['ESTOQUE_CD15'], errors='coerce').fillna(0)
    df_analise['EMBL_TRANSFERENCIA'] = pd.to_numeric(df_analise['EMBL_TRANSFERENCIA'], errors='coerce').fillna(1)
    df_analise['QUANTIDADE_ESTOQUE_MINIMO'] = pd.to_numeric(df_analise['QUANTIDADE_ESTOQUE_MINIMO'], errors='coerce').fillna(0)
    df_analise['QUANTIDADE_ESTOQUE_MAXIMO'] = pd.to_numeric(df_analise['QUANTIDADE_ESTOQUE_MAXIMO'], errors='coerce').fillna(0)

    # Passo 3: Filtros rigorosos
    print("Aplicando os filtros da análise...")
    
    # a) O status ativo (Ativo na Loja)
    filtro_ativo = (df_analise['STATUS_COMPRA'] == 'A')
    
    # b) Sem ponto de pedido anterior (MIN e MAX <= 0)
    filtro_sem_ponto = (df_analise['QUANTIDADE_ESTOQUE_MINIMO'] <= 0) & (df_analise['QUANTIDADE_ESTOQUE_MAXIMO'] <= 0)
    
    # c) Estoque no CD15 > embalagem de transferência (1 embalagem)
    filtro_cd15 = (df_analise['ESTOQUE_CD15'] > df_analise['EMBL_TRANSFERENCIA'])
    
    # Aplicando os filtros
    df_final = df_analise[filtro_ativo & filtro_sem_ponto & filtro_cd15].copy()

    # Passo 4: Limpar e Exportar
    # Organiza os dados para facilitar a analise visual
    df_final = df_final.sort_values(['CODIGO_PRODUTO', 'CODIGO_EMPRESA'])
    
    # Vamos manter as colunas que vieram do resultado.parquet como solicitado "mesmas informações", 
    # Mantenho STATUS_COMPRA e ESTOQUE_CD15 a titulo de prova do filtro para o relatorio.
    # Exclusão do que não precisa estar sujo
    colunas_finais = df_resultado.columns.tolist() + ['STATUS_COMPRA', 'ESTOQUE_CD15']
    
    print(f"Encontrados {len(df_final)} registros que necessitam de ajuste manual.")
    
    # Se existirem registros, exporta
    if not df_final.empty:
        df_final[colunas_finais].to_csv(arquivo_saida, sep=';', index=False, encoding='utf-8-sig', decimal=',')
        print(f"Arquivo CSV gravado em: {arquivo_saida}")
    else:
        print("Nenhum registro se enquadra nos filtros: Não há nada sem pedido original com mais de 1 CX no CD ativo!")

if __name__ == '__main__':
    analisar_dados()
# limpar tela com cls e depois msg de finalizado
os.system('cls')
print("[OK] Processo concluído!")