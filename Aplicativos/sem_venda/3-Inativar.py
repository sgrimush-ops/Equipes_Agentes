import pandas as pd
from pathlib import Path

ARQUIVO_ENTRADA = Path(__file__).parent / 'sem_venda.xlsx'
ARQUIVO_SAIDA   = Path(__file__).parent / 'inativar.xlsx'

DEPARTAMENTOS_ALVO = {
    'BEBIDAS',
    'MERCEARIA',
    'PERFUMARIA E LIMPEZA',
    'PRODUTOS PET',
}

EMPRESA_CD = 15   # Centro de distribuição — recebe "A" quando produto não cobre todas as lojas

# ---------------------------------------------------------------------------
print(f'Lendo {ARQUIVO_ENTRADA.name}...')
df = pd.read_excel(ARQUIVO_ENTRADA, dtype={'EMPRESA': int})

# Filtra apenas os departamentos desejados
df = df[df['DEPARTAMENTO'].str.upper().isin(DEPARTAMENTOS_ALVO)].copy()

# Mantém apenas as colunas necessárias
df = df[['CODIGO_PRODUTO', 'DESCRICAO_PRODUTO', 'EMPRESA']].copy()

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

# ---------------------------------------------------------------------------
print(f'\nResumo da coluna ACAO:')
print(df['ACAO'].value_counts().to_string())
print(f'\nTotal de linhas: {len(df):,}')

df.to_excel(ARQUIVO_SAIDA, index=False)
print(f'\n✅ Arquivo gerado: {ARQUIVO_SAIDA.name}')
