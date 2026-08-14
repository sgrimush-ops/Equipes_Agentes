import pandas as pd
from pathlib import Path

ARQUIVO_ENTRADA = Path(__file__).resolve().parents[1] / 'import_querys' / 'query_bz.parquet'
ARQUIVO_SAIDA   = Path(__file__).parent / 'inativar_nao_alimentos.xlsx'

DEPARTAMENTOS_ALVO = {
    'NAO ALIMENTO',
}

EMPRESA_CD = 15   # Centro de distribuição — recebe "A" quando produto não cobre todas as lojas

# ---------------------------------------------------------------------------
print(f'Lendo {ARQUIVO_ENTRADA.name}...')
df = pd.read_parquet(ARQUIVO_ENTRADA)
df['CODIGO_EMPRESA'] = df['CODIGO_EMPRESA'].astype(int)

# Filtra apenas os departamentos desejados
df = df[df['DEPARTAMENTO'].str.upper().isin(DEPARTAMENTOS_ALVO)].copy()

# Saneamento das colunas usadas no cálculo de sem venda
df['QUANTIDADE_DISPONIVEL'] = pd.to_numeric(df['QUANTIDADE_DISPONIVEL'], errors='coerce').fillna(0)
df['QTD_VENDIDA_PERIODO'] = pd.to_numeric(df['QTD_VENDIDA_PERIODO'], errors='coerce').fillna(0)

# Estoque do CD calculado sobre a base completa, antes do filtro de sem venda
estoque_cd = (
    df[df['CODIGO_EMPRESA'] == EMPRESA_CD]
    .groupby('CODIGO_PRODUTO')['QUANTIDADE_DISPONIVEL']
    .sum()
    .rename('ESTOQUE_CD')
)

# Filtra Sem Venda: não teve vendas no período mas tem estoque físico disponível
df = df[(df['QTD_VENDIDA_PERIODO'] <= 0) & (df['QUANTIDADE_DISPONIVEL'] > 0)].copy()

# Renomeia para manter o padrão utilizado no restante do pipeline
df = df.rename(columns={'CODIGO_EMPRESA': 'EMPRESA', 'QUANTIDADE_DISPONIVEL': 'ESTOQUE'})

# Mantém apenas as colunas necessárias
df = df[['CODIGO_PRODUTO', 'DESCRICAO_PRODUTO', 'DEPARTAMENTO', 'EMPRESA', 'ESTOQUE']].copy()

# Com estoque no CD (empresa 15) acima de 1 unidade, o CD ainda pode abastecer a loja: não inativar
df = df.merge(estoque_cd, on='CODIGO_PRODUTO', how='left')
df['ESTOQUE_CD'] = df['ESTOQUE_CD'].fillna(0)
df = df[df['ESTOQUE_CD'] <= 1].copy()


# ---------------------------------------------------------------------------
# Identifica o conjunto de lojas (todas as empresas exceto o CD)
todas_lojas = sorted(e for e in df['EMPRESA'].unique() if e != EMPRESA_CD)
total_lojas = len(todas_lojas)

print(f'Lojas encontradas ({total_lojas}): {todas_lojas}')
print(f'CD identificado como empresa {EMPRESA_CD}')

# ---------------------------------------------------------------------------
# Para cada produto, conta em quantas lojas ele aparece
lojas_df = df[df['EMPRESA'] != EMPRESA_CD]

cobertura = (
    lojas_df.groupby('CODIGO_PRODUTO')['EMPRESA']
    .nunique()
    .rename('QTD_LOJAS')
)

# Produtos que aparecem em TODAS as lojas → TI (total inativação)
produtos_ti = set(cobertura[cobertura == total_lojas].index)

# ---------------------------------------------------------------------------
# Aplica a coluna ACAO
def calcular_acao(row):
    produto  = row['CODIGO_PRODUTO']
    empresa  = row['EMPRESA']

    if produto in produtos_ti:
        return 'TI'                   # cobre todas as lojas → inativar em tudo

    # Produto não cobre todas as lojas
    if empresa == EMPRESA_CD:
        return 'A'                    # CD fica ativo para abastecer lojas restantes
    return 'I'                        # lojas com sem-venda → inativar

df['ACAO'] = df.apply(calcular_acao, axis=1)

# ---------------------------------------------------------------------------
# Ordenação para facilitar revisão
df = df.sort_values(['ACAO', 'DEPARTAMENTO', 'CODIGO_PRODUTO', 'EMPRESA'] if 'DEPARTAMENTO' in df.columns
                    else ['ACAO', 'CODIGO_PRODUTO', 'EMPRESA']).reset_index(drop=True)

colunas_finais = ['CODIGO_PRODUTO', 'DESCRICAO_PRODUTO', 'DEPARTAMENTO', 'EMPRESA', 'ESTOQUE', 'ESTOQUE_CD', 'ACAO']
df = df[colunas_finais]

# ---------------------------------------------------------------------------
print(f'\nResumo da coluna ACAO:')
print(df['ACAO'].value_counts().to_string())
print(f'\nTotal de linhas: {len(df):,}')

df.to_excel(ARQUIVO_SAIDA, index=False)
print(f'\n✅ Arquivo gerado: {ARQUIVO_SAIDA.name}')
