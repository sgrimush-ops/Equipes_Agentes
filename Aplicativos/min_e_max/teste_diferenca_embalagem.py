from pathlib import Path

import pandas as pd


def _resolver_coluna(df, candidatos, nome_logico):
    for coluna in candidatos:
        if coluna in df.columns:
            return coluna
    raise KeyError(
        f"Nao encontrei a coluna de {nome_logico}. "
        f"Candidatas testadas: {candidatos}"
    )


def _to_numeric(series):
    return pd.to_numeric(
        series.astype(str).str.replace(',', '.', regex=False),
        errors='coerce',
    )


def gerar_relatorio_diferenca_embalagem():
    base_dir = Path(__file__).resolve().parent.parent
    arquivo_origem = base_dir / 'import_querys' / 'query.parquet'
    arquivo_saida = (
        Path(__file__).resolve().parent
        / 'itens_diferenca_menor_que_embalagem.xlsx'
    )

    if not arquivo_origem.exists():
        print(f"Erro: arquivo nao encontrado: {arquivo_origem}")
        return

    print(f"Lendo base: {arquivo_origem}")
    df = pd.read_parquet(arquivo_origem)

    col_produto = _resolver_coluna(
        df,
        ['CODIGO_PRODUTO', 'SEQPRODUTO'],
        'codigo do produto',
    )
    col_descricao = _resolver_coluna(
        df,
        ['DESCRICAO_PRODUTO', 'DESCCOMPLETA'],
        'descricao do produto',
    )
    col_emb = _resolver_coluna(
        df,
        ['EMBL_TRANSFERENCIA', 'EMBALAGEM_TRANSFERENCIA', 'EMBALAGEM'],
        'embalagem de transferencia',
    )
    col_empresa = _resolver_coluna(
        df,
        ['CODIGO_EMPRESA', 'NROEMPRESA'],
        'empresa',
    )
    col_min = _resolver_coluna(
        df,
        [
            'QUANTIDADE_ESTOQUE_MINIMO',
            'ESTOQUE_MINIMO',
            'MINIMO',
            'NOVO_MINIMO',
        ],
        'minimo',
    )
    col_max = _resolver_coluna(
        df,
        [
            'QUANTIDADE_ESTOQUE_MAXIMO',
            'ESTOQUE_MAXIMO',
            'MAXIMO',
            'NOVO_MAXIMO',
        ],
        'maximo',
    )

    work = df[
        [
            col_produto,
            col_descricao,
            col_emb,
            col_empresa,
            col_min,
            col_max,
        ]
    ].copy()
    work.columns = [
        'CODIGO_PRODUTO',
        'DESCRICAO_PRODUTO',
        'EMBL_TRANSFERENCIA',
        'EMPRESA',
        'MINIMO',
        'MAXIMO',
    ]

    work['EMBL_TRANSFERENCIA'] = _to_numeric(
        work['EMBL_TRANSFERENCIA']
        .astype(str)
        .str.extract(r'(\d+[\.,]?\d*)')[0]
    ).fillna(0)
    work['MINIMO'] = _to_numeric(work['MINIMO']).fillna(0)
    work['MAXIMO'] = _to_numeric(work['MAXIMO']).fillna(0)

    work['DIFERENCA_MIN_MAX'] = work['MAXIMO'] - work['MINIMO']

    resultado = work[
        (work['EMBL_TRANSFERENCIA'] > 0)
        & (work['DIFERENCA_MIN_MAX'] >= 0)
        & (work['DIFERENCA_MIN_MAX'] < work['EMBL_TRANSFERENCIA'])
    ].copy()

    resultado = resultado.sort_values(['EMPRESA', 'CODIGO_PRODUTO'])
    resultado.to_excel(arquivo_saida, index=False)

    print(f"Excel gerado com sucesso: {arquivo_saida}")
    print(f"Total de linhas no resultado: {len(resultado)}")


if __name__ == '__main__':
    gerar_relatorio_diferenca_embalagem()

