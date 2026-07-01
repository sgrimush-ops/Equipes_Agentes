from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
ARQ_1 = BASE_DIR / 'aa1.txt'
ARQ_2 = BASE_DIR / 'aa2.txt'
SAIDA = BASE_DIR / 'comparativo_aa1_aa2.xlsx'

COLUNAS_CHAVE = [
    'ORIGEM',
    'EMPRESA',
    'TITULO',
    'PEDIDO',
    'COD_FORNECEDOR',
    'FORNECEDOR',
    'DATA_EMISSAO',
    'DATA_PREV_ENTREGA',
    'PRAZO_PAGAMENTO_DIAS',
    'PARCELA',
    'DATA_VENCIMENTO',
    'STATUS_PEDIDO',
]

COLUNAS_COMPARADAS = [
    'COMPRADOR',
    'VALOR_PROJETADO',
]


def carregar_txt(caminho: Path) -> pd.DataFrame:
    ultimo_erro = None
    for encoding in ('utf-8-sig', 'cp1252', 'latin1'):
        try:
            df = pd.read_csv(caminho, sep=';', dtype=str, keep_default_na=False, encoding=encoding)
            break
        except UnicodeDecodeError as erro:
            ultimo_erro = erro
    else:
        raise ultimo_erro
    df.columns = [col.strip() for col in df.columns]
    for coluna in df.columns:
        df[coluna] = df[coluna].astype(str).str.strip()
    return df


def preparar_comparacao(df: pd.DataFrame, origem: str) -> pd.DataFrame:
    base = df.copy()
    base['ARQUIVO_ORIGEM'] = origem
    base['ORDEM_ORIGINAL'] = range(1, len(base) + 1)
    base['OCORRENCIA_CHAVE'] = base.groupby(COLUNAS_CHAVE).cumcount() + 1
    return base


def gerar_resumo(df1: pd.DataFrame, df2: pd.DataFrame, so_1: pd.DataFrame, so_2: pd.DataFrame, dif: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {'INDICADOR': 'Linhas aa1', 'VALOR': len(df1)},
            {'INDICADOR': 'Linhas aa2', 'VALOR': len(df2)},
            {'INDICADOR': 'Somente no aa1', 'VALOR': len(so_1)},
            {'INDICADOR': 'Somente no aa2', 'VALOR': len(so_2)},
            {'INDICADOR': 'Linhas com diferenca de comprador', 'VALOR': int(dif['DIF_COMPRADOR'].sum()) if not dif.empty else 0},
            {'INDICADOR': 'Linhas com diferenca de valor', 'VALOR': int(dif['DIF_VALOR_PROJETADO'].sum()) if not dif.empty else 0},
            {'INDICADOR': 'Total de linhas com alguma diferenca', 'VALOR': len(dif)},
        ]
    )


def main() -> None:
    df1 = preparar_comparacao(carregar_txt(ARQ_1), 'aa1')
    df2 = preparar_comparacao(carregar_txt(ARQ_2), 'aa2')

    merge_cols = COLUNAS_CHAVE + ['OCORRENCIA_CHAVE']
    comp = df1.merge(
        df2,
        on=merge_cols,
        how='outer',
        suffixes=('_aa1', '_aa2'),
        indicator=True,
    )

    somente_aa1 = comp.loc[comp['_merge'] == 'left_only', [f'{col}_aa1' for col in df1.columns if col not in merge_cols]].copy()
    somente_aa1.columns = [col.replace('_aa1', '') for col in somente_aa1.columns]
    somente_aa1.insert(0, 'OCORRENCIA_CHAVE', comp.loc[comp['_merge'] == 'left_only', 'OCORRENCIA_CHAVE'].values)
    for coluna in COLUNAS_CHAVE:
        somente_aa1.insert(len(somente_aa1.columns), coluna, comp.loc[comp['_merge'] == 'left_only', coluna].values)
    somente_aa1 = somente_aa1[COLUNAS_CHAVE + ['OCORRENCIA_CHAVE'] + [c for c in somente_aa1.columns if c not in COLUNAS_CHAVE + ['OCORRENCIA_CHAVE']]]

    somente_aa2 = comp.loc[comp['_merge'] == 'right_only', [f'{col}_aa2' for col in df2.columns if col not in merge_cols]].copy()
    somente_aa2.columns = [col.replace('_aa2', '') for col in somente_aa2.columns]
    somente_aa2.insert(0, 'OCORRENCIA_CHAVE', comp.loc[comp['_merge'] == 'right_only', 'OCORRENCIA_CHAVE'].values)
    for coluna in COLUNAS_CHAVE:
        somente_aa2.insert(len(somente_aa2.columns), coluna, comp.loc[comp['_merge'] == 'right_only', coluna].values)
    somente_aa2 = somente_aa2[COLUNAS_CHAVE + ['OCORRENCIA_CHAVE'] + [c for c in somente_aa2.columns if c not in COLUNAS_CHAVE + ['OCORRENCIA_CHAVE']]]

    em_ambos = comp.loc[comp['_merge'] == 'both'].copy()
    em_ambos['DIF_COMPRADOR'] = em_ambos['COMPRADOR_aa1'] != em_ambos['COMPRADOR_aa2']
    em_ambos['DIF_VALOR_PROJETADO'] = em_ambos['VALOR_PROJETADO_aa1'] != em_ambos['VALOR_PROJETADO_aa2']
    diferencas = em_ambos.loc[em_ambos['DIF_COMPRADOR'] | em_ambos['DIF_VALOR_PROJETADO']].copy()

    colunas_diferencas = merge_cols + [
        'COMPRADOR_aa1',
        'COMPRADOR_aa2',
        'VALOR_PROJETADO_aa1',
        'VALOR_PROJETADO_aa2',
        'DIF_COMPRADOR',
        'DIF_VALOR_PROJETADO',
        'ORDEM_ORIGINAL_aa1',
        'ORDEM_ORIGINAL_aa2',
    ]
    diferencas = diferencas[colunas_diferencas].sort_values(merge_cols).reset_index(drop=True)

    resumo = gerar_resumo(df1, df2, somente_aa1, somente_aa2, diferencas)

    with pd.ExcelWriter(SAIDA, engine='openpyxl') as writer:
        resumo.to_excel(writer, sheet_name='Resumo', index=False)
        diferencas.to_excel(writer, sheet_name='Diferencas', index=False)
        somente_aa1.to_excel(writer, sheet_name='Somente_aa1', index=False)
        somente_aa2.to_excel(writer, sheet_name='Somente_aa2', index=False)

    print(f'Arquivo gerado: {SAIDA}')
    print(resumo.to_string(index=False))


if __name__ == '__main__':
    main()