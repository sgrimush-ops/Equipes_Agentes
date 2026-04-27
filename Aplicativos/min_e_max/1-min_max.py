import pandas as pd
import math
import os
from pathlib import Path
from datetime import datetime

# --- TRAVA DE CONTEXTO ---
if __name__ == '__main__':
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass

def calcular_min_max(row, dias_relatorio):
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
        venda_periodo = float(row['QTD_VENDIDA_NUM'])
    except:
        venda_periodo = 0.0

    venda_media = venda_periodo / dias_relatorio

    # Regra 1: Mínimo = venda média de 4 dias em unidades inteiras.
    minimo_dias = 4 * venda_media

    if embalagem == 1:
        # Produto unitário mantém a regra mínima de 6 unidades.
        min_novo = max(math.ceil(minimo_dias), 6)
        regra_minimo = 'UNITARIO_PISO_6'
    else:
        # Para caixas fechadas, o mínimo não pode ficar abaixo de 60% da embalagem.
        piso_minimo = math.ceil(embalagem * 0.6)
        min_novo = max(math.ceil(minimo_dias), piso_minimo)
        if min_novo == piso_minimo:
            regra_minimo = 'PISO_60_EMBALAGEM'
        else:
            regra_minimo = 'VENDA_4_DIAS'

    # Cálculo do Máximo: baixo volume recebe 1 caixa acima do mínimo.
    # Alto volume recebe 35% acima do mínimo, com a diferença arredondada
    # para caixas fechadas.
    if embalagem == 1 and min_novo == 6 and minimo_dias <= 6:
        # Produto de emb=1 girando devagar. Fixo estrito de regra 3
        max_novo = 10
        regra_maximo = 'UNITARIO_LENTO_FIXO_10'
    else:
        embalagens_minimo = min_novo / embalagem

        if embalagem > 1 and embalagens_minimo >= 3:
            aumento_caixas = math.ceil((min_novo * 0.35) / embalagem)
            regra_maximo = 'ALTO_VOLUME_35'
        else:
            aumento_caixas = 1
            regra_maximo = 'UMA_CAIXA_ACIMA'

        aumento_caixas = max(aumento_caixas, 1)
        max_novo = min_novo + (aumento_caixas * embalagem)

    return pd.Series([
        round(venda_media, 2),
        int(min_novo),
        int(max_novo),
        regra_minimo,
        regra_maximo,
    ])

def converter_para_parquet(arquivo_csv='resultado.csv'):
    """
    Lê o resultado.csv e gera o resultado.parquet para o GAM.
    Incorporado de reajuste_digitar.py.
    """
    arquivo_csv = Path(arquivo_csv)
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


def solicitar_dias_relatorio():
    print("\n" + "=" * 50)
    print("          BASE DO RELATORIO DE VENDAS")
    print("=" * 50)
    print("Informe quantos dias de venda o relatorio traz.")
    print("Exemplos: 30 para venda de 30 dias, 60 para venda de 60 dias.")
    print("=" * 50)

    while True:
        entrada_dias = input("-> Digite a quantidade de dias do relatorio: ").strip()
        try:
            dias_relatorio = int(entrada_dias)
        except ValueError:
            print("x Valor invalido. Digite um numero inteiro maior que zero.")
            continue

        if dias_relatorio <= 0:
            print("x Valor invalido. Digite um numero inteiro maior que zero.")
            continue

        return dias_relatorio

def processar_calculos():
    dias_relatorio = solicitar_dias_relatorio()

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

    colunas_venda_possiveis = [
        'QTD_VENDIDA_PERIODO',
        'QTD_VENDIDA_30D',
        'QTD_VENDIDA',
    ]
    coluna_venda = next((c for c in colunas_venda_possiveis if c in df.columns), None)

    if not coluna_venda:
        print(
            'Erro: coluna de venda nao encontrada. '
            'Esperado uma entre: QTD_VENDIDA_PERIODO, QTD_VENDIDA_30D, QTD_VENDIDA.'
        )
        return

    if pd.api.types.is_numeric_dtype(df[coluna_venda]):
        df['QTD_VENDIDA_NUM'] = pd.to_numeric(
            df[coluna_venda],
            errors='coerce',
        ).fillna(0.0)
    else:
        venda_txt = (
            df[coluna_venda]
            .astype(str)
            .str.strip()
            .str.replace(',', '.', regex=False)
        )
        df['QTD_VENDIDA_NUM'] = pd.to_numeric(
            venda_txt,
            errors='coerce',
        ).fillna(0.0)

    print(
        f"Venda media sera calculada como {coluna_venda} / {dias_relatorio} dias."
    )
    df['DIAS_RELATORIO_VENDA'] = dias_relatorio
    
    # 2. Computar mínimos e máximos por linha
    print("Rodando cálculos matemáticos matriz...")
    df[
        [
            'VENDA_MEDIA',
            'NOVO_MINIMO',
            'NOVO_MAXIMO',
            'REGRA_MINIMO',
            'REGRA_MAXIMO',
        ]
    ] = df.apply(
        lambda row: calcular_min_max(row, dias_relatorio),
        axis=1,
    )
    
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
        'DIAS_RELATORIO_VENDA', 'VENDA_MEDIA', 'NOVO_MINIMO', 'NOVO_MAXIMO',
        'REGRA_MINIMO', 'REGRA_MAXIMO'
    ]
    
    cols_existentes = [c for c in colunas_finais if c in df_resultado.columns]
    df_export = df_resultado[cols_existentes]
    
    print("Exportando os resultados para 'resultado.csv' para conferência humana...")
    arquivo_saida = Path('resultado.csv')

    try:
        df_export.to_csv(
            arquivo_saida,
            sep=';',
            encoding='utf-8-sig',
            index=False,
            decimal=',',
        )
    except PermissionError:
        arquivo_saida = Path(
            f"resultado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        print(
            "Aviso: 'resultado.csv' está em uso. "
            f"Exportando em '{arquivo_saida.name}'."
        )
        df_export.to_csv(
            arquivo_saida,
            sep=';',
            encoding='utf-8-sig',
            index=False,
            decimal=',',
        )
    
    # 6. Chama a conversão direta (Antigo reajuste_digitar.py)
    print("\nInvocando pipeline de conversão para Parquet...")
    converter_para_parquet(arquivo_saida)
        
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

