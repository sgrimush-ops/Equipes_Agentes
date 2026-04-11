import pandas as pd
import math
import os
from pathlib import Path

# --- TRAVA DE CONTEXTO ---
if __name__ == '__main__':
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass

def calcular_min_max(row):
    """
    Função dedicada a calcular as novas propriedades de Estoque Mínimo e Máximo.
    """
    try:
        embalagem = int(row['EMBL_TRANSFERENCIA_NUM'])
    except:
        embalagem = 1
    if embalagem <= 0:
        embalagem = 1
        
    try:
        venda_30d = float(row['QTD_VENDIDA_NUM'])
    except:
        venda_30d = 0.0
        
    venda_media = venda_30d / 30.0
    
    # Regra 1: Mínimo = Venda média de 4 dias arredondado p/ múltiplo da embalagem
    minimo_dias = 4 * venda_media
    minimo_calc = math.ceil(minimo_dias / embalagem) * embalagem
    minimo_calc = max(minimo_calc, embalagem)  # Pelo menos obrigatório 1 caixa de transfer
    
    # Regra 2 e Regra 3 (limites base de 6 unidades)
    if minimo_calc < 6:
        min_novo = math.ceil(6 / embalagem) * embalagem
    else:
        min_novo = minimo_calc
        
    # Calculo do Máximo (Regra 3 para lentos vs Regra 1 Geral)
    if embalagem == 1 and min_novo == 6 and minimo_dias <= 6:
        # Produto de emb=1 girando devagar. Fixo estrito de regra 3
        max_novo = 10
    else:
        # Regra 1: Maximo é Mínimo + 30% ou 40% (sempre encerra na embalagem exata, mínimo +1 caixa)
        aumento_caixas = math.ceil((min_novo * 0.3) / embalagem)
        aumento_caixas = max(aumento_caixas, 1) # Sempre soma ao menos 1 caixa limpa
        max_novo = min_novo + (aumento_caixas * embalagem)
        
    return pd.Series([round(venda_media, 2), int(min_novo), int(max_novo)])

def converter_para_parquet():
    """
    Lê o resultado.csv e gera o resultado.parquet para o GAM.
    Incorporado de reajuste_digitar.py.
    """
    arquivo_csv = Path('resultado.csv')
    if not arquivo_csv.exists():
        print(f"ERRO: O arquivo '{arquivo_csv.name}' não foi encontrado.")
        return
        
    print(f"Lendo dados de '{arquivo_csv.name}'...")
    try:
        df = pd.read_csv(arquivo_csv, sep=';', encoding='utf-8-sig', decimal=',')
    except Exception as e:
        print(f"Erro ao ler CSV: {e}")
        return
        
    arquivo_parquet = Path('resultado.parquet')
    print(f"Convertendo e salvando em '{arquivo_parquet.name}'...")
    
    try:
        # Tenta com pyarrow (padrão Rules)
        df.to_parquet(arquivo_parquet, engine='pyarrow', index=False)
        print("Sucesso! O arquivo 'resultado.parquet' foi gerado corretamente e já pode ser lido pelo GAM.")
    except Exception as e:
        print(f"Aviso: Erro com pyarrow ({e})\nTentando fallback com fastparquet...")
        try:
            df.to_parquet(arquivo_parquet, engine='fastparquet', index=False)
            print("Sucesso usando fastparquet!")
        except Exception as err:
            print(f"Erro catastrófico ao gerar parquet: {err}")

def processar_calculos():
    # Caminho corporativo centralizado
    arquivo_query = Path(__file__).parent.parent / 'import_querys' / 'query.parquet'
    
    if not arquivo_query.exists():
        print(f"Erro fatal: Não foi encontrado o arquivo fonte de dados no caminho corporativo: {arquivo_query}")
        return
        
    print(f"Carregando base volumosa corporativa '{arquivo_query.name}'...")
    df = pd.read_parquet(arquivo_query)
    
    # 0. Filtro de Ativos (Garante que só produtos em linha na loja recebam sugestão)
    if 'ATIVO_COMPRA' in df.columns:
        print("Filtrando apenas produtos ATIVOS para as lojas...")
        df = df[df['ATIVO_COMPRA'] == 'A'].copy()
    
    # 1. Aplicando Regra Global nº 6 (Saneamento de Inteiros)
    print("Saneando extração de embalagens e ajustando preenchimentos...")
    df['EMBL_TRANSFERENCIA_NUM'] = df['EMBL_TRANSFERENCIA'].astype(str).str.extract(r'(\d+)')[0].fillna(1).astype(int)
    df['QTD_VENDIDA_NUM'] = pd.to_numeric(df['QTD_VENDIDA_30D'], errors='coerce').fillna(0.0)
    
    # 2. Computar mínimos e máximos por linha
    print("Rodando cálculos matemáticos matriz...")
    df[['VENDA_MEDIA', 'NOVO_MINIMO', 'NOVO_MAXIMO']] = df.apply(calcular_min_max, axis=1)
    
    # 3. Regra de Negócio que preserva Loja 15 recebe a soma das outras filiais do CD
    print("Projetando equivalências para o Centro de Distribuição (Loja 15)...")
    df_outras = df[df['CODIGO_EMPRESA'] != 15]
    somas_produto = df_outras.groupby('CODIGO_PRODUTO')[['NOVO_MINIMO', 'NOVO_MAXIMO']].sum()
    
    mapa_soma_min = somas_produto['NOVO_MINIMO'].to_dict()
    mapa_soma_max = somas_produto['NOVO_MAXIMO'].to_dict()
    
    mask_15 = df['CODIGO_EMPRESA'] == 15
    df.loc[mask_15, 'NOVO_MINIMO'] = df.loc[mask_15, 'CODIGO_PRODUTO'].map(mapa_soma_min).fillna(0).astype(int)
    df.loc[mask_15, 'NOVO_MAXIMO'] = df.loc[mask_15, 'CODIGO_PRODUTO'].map(mapa_soma_max).fillna(0).astype(int)
    
    df['NOVO_MINIMO'] = df['NOVO_MINIMO'].astype(int)
    df['NOVO_MAXIMO'] = df['NOVO_MAXIMO'].astype(int)
    
    df['QUANTIDADE_ESTOQUE_MINIMO'] = pd.to_numeric(df.get('QUANTIDADE_ESTOQUE_MINIMO', 0), errors='coerce').fillna(0).astype(int)
    df['QUANTIDADE_ESTOQUE_MAXIMO'] = pd.to_numeric(df.get('QUANTIDADE_ESTOQUE_MAXIMO', 0), errors='coerce').fillna(0).astype(int)
    
    # 4. Input Terminal
    print("\n" + "="*50)
    print("           OPÇÕES DE RELATÓRIO / EXPORTAÇÃO")
    print("="*50)
    print("[1] - Gerar APENAS sugestões para AUMENTAR")
    print("      (Filtra os casos onde o Novo Mínimo Calculado é maior que o Atual (origem))")
    print("\n[2] - Gerar TOTAL")
    print("      (Exporta a base total indiscriminada, englobando altas, baixas e manutenção equivalentes)")
    print("="*50)
    
    while True:
        opcao = input("-> Digite a opção escolhida (1 ou 2): ").strip()
        if opcao in ['1', '2']:
            break
        print("x Opção inválida. Digite 1 ou 2.")
        
    if opcao == '1':
        print("\n=> Filtrando exclusivamente os produtos apontando para AUMENTO (Diferença > 5 unidades)...")
        df_resultado = df[df['NOVO_MINIMO'] > (df['QUANTIDADE_ESTOQUE_MINIMO'] + 5)].copy()
    else:
        print("\n=> Exportando a totalidade dos produtos analisados...")
        df_resultado = df.copy()
        
    print(f"Total de linhas prontas para exportação: {len(df_resultado)}")
    
    # 5. Organiza as colunas limpas
    colunas_finais = [
        'DESCRICAO_PRODUTO', 'CODIGO_PRODUTO', 'CODIGO_EMPRESA',
        'EMBL_TRANSFERENCIA', 'QUANTIDADE_ESTOQUE_MINIMO', 'QUANTIDADE_ESTOQUE_MAXIMO',
        'VENDA_MEDIA', 'NOVO_MINIMO', 'NOVO_MAXIMO'
    ]
    
    cols_existentes = [c for c in colunas_finais if c in df_resultado.columns]
    df_export = df_resultado[cols_existentes]
    
    print("Exportando os resultados para 'resultado.csv' para conferência humana...")
    df_export.to_csv('resultado.csv', sep=';', encoding='utf-8-sig', index=False, decimal=',')
    
    # 6. Chama a conversão direta (Antigo reajuste_digitar.py)
    print("\nInvocando pipeline de conversão para Parquet...")
    converter_para_parquet()
        
    print("\n[✓] Trabalho finalizado de ponta a ponta com sucesso!")

if __name__ == "__main__":
    os.system('cls')
    print("\n" + "="*50)
    print("       GERENCIADOR DE ESTOQUE MÍNIMO E MÁXIMO")
    print("="*50)
    print("[1] - Executar Script Completo (Cálculos + Conversão)")
    print("[2] - Apenas Converter 'resultado.csv' para Parquet")
    print("="*50)
    
    while True:
        modo = input("-> Escolha o modo de operação (1 ou 2): ").strip()
        if modo in ['1', '2']:
            break
        print("x Opção inválida. Digite 1 ou 2.")
        
    if modo == '1':
        processar_calculos()
    else:
        converter_para_parquet()

# limpar tela com cls e depois msg de finalizado
os.system('cls')
print("[OK] Processo concluído!")

