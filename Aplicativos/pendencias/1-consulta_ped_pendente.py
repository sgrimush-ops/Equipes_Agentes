import pandas as pd
from pathlib import Path
import os
import subprocess
import sys
from datetime import datetime


def _first_non_empty(series):
    values = series.fillna('').astype(str).str.strip()
    values = values[values != '']
    return values.iloc[0] if len(values) else ''


def _to_numeric(series):
    return pd.to_numeric(
        series.fillna('').astype(str).str.replace(',', '.', regex=False),
        errors='coerce',
    )


def _fmt_number(value):
    if pd.isna(value):
        return ''
    if float(value).is_integer():
        return str(int(value))
    return str(round(float(value), 3)).replace('.', ',')


def consolidar_chave_negocio(df):
    chave = ['CODIGO_EMPRESA', 'CODIGO_PRODUTO', 'NRO_PEDIDO', 'DATA']
    if not all(col in df.columns for col in chave):
        return df

    qtd_chaves_duplicadas = (
        df.groupby(chave, dropna=False).size().reset_index(name='QTD')
    )
    qtd_chaves_duplicadas = int((qtd_chaves_duplicadas['QTD'] > 1).sum())

    if qtd_chaves_duplicadas == 0:
        return df

    registros = []
    for _, g in df.groupby(chave, dropna=False, sort=False):
        row = {col: g.iloc[0][col] for col in chave}

        for col in g.columns:
            if col in chave:
                continue

            if col == 'QUANTIDADE_A_EXPEDIR':
                vals = _to_numeric(g[col]).dropna()
                positivos = vals[vals > 0]
                escolhido = positivos.min() if len(positivos) else vals.min()
                row[col] = _fmt_number(escolhido)
                continue

            if col in ('QTD_SEPARADA', 'QTD_CONFERIDA'):
                vals = _to_numeric(g[col]).dropna()
                row[col] = _fmt_number(vals.max()) if len(vals) else ''
                continue

            if col in (
                'NRO_PED_EXPEDICAO',
                'CARGA',
                'DATA_CONFERENCIA',
                'USUARIO_CONFERENCIA',
            ):
                row[col] = _first_non_empty(g[col])
                continue

            row[col] = _first_non_empty(g[col])

        registros.append(row)

    out = pd.DataFrame(registros)
    out = out[df.columns.tolist()]

    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] "
        "Consolidacao defensiva aplicada em "
        f"{qtd_chaves_duplicadas} chave(s) duplicada(s)."
    )
    return out


def processar_pedidos_pendentes():
    # Descobre o diretório real da pasta base 'Aplicativos'.
    base_dir = Path(__file__).resolve().parent.parent

    # Caminho do arquivo de origem (a query recém criada)
    arquivo_origem = base_dir / 'import_querys' / 'ped_pendentes.txt'

    # Pasta de destino e arquivo
    pasta_destino = base_dir / 'pendencias' / 'bd_saida'
    pasta_destino.mkdir(parents=True, exist_ok=True)

    data_hoje = datetime.now().strftime('%d_%m_%Y')
    arquivo_csv_saida = (
        pasta_destino / f'ped_pendentes_formatado_{data_hoje}.csv'
    )

    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] "
        f"Iniciando leitura de: {arquivo_origem.name}"
    )

    try:
        # Lê o TXT bruto delimitado por ponto-e-vírgula (Padrão Consinco),
        # forçando object puro para evitar interpretação errada de floats.
        df = pd.read_csv(arquivo_origem, sep=';', dtype=str, encoding='utf-8')

        # Limpeza genérica em colunas textuais.
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.strip()

        # Limpa timestamps do Consinco para manter apenas AAAA-MM-DD.
        if 'DATA' in df.columns:
            df['DATA'] = df['DATA'].astype(str).str[:10]

        # Garante 1 linha por loja+item+pedido+data
        # quando a fonte vier duplicada.
        df = consolidar_chave_negocio(df)

        # Gera CSV compatível com Excel (UTF-8 com BOM).
        df.to_csv(
            arquivo_csv_saida,
            index=False,
            sep=';',
            encoding='utf-8-sig',
        )

        print("✅ SUCESSO! Arquivo processado e formatado isolado com sucesso.")
        print(f"Salvo em: {arquivo_csv_saida}")
        print(f"Total de Linhas Processadas: {len(df)}")
        return True

    except FileNotFoundError:
        print(
            "❌ ERRO: O arquivo central nao foi encontrado em "
            f"\n{arquivo_origem}"
        )
        print(
            "💡 Verifique se a query SQL foi devidamente "
            "extraida/puxada com o nome 'ped_pendentes.txt'."
        )
        return False
    except Exception as e:
        print(f"❌ ERRO CRÍTICO no processamento: {str(e)}")
        return False


if __name__ == '__main__':
    # Garante execução a partir da pasta local do script.
    os.chdir(Path(__file__).parent.resolve())
    sucesso = processar_pedidos_pendentes()
    if sucesso:
        script_dashboard = Path(__file__).parent / '2-dashboard_pendencias.py'
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"Executando dashboard: {script_dashboard.name}"
        )
        subprocess.run([sys.executable, str(script_dashboard)], check=True)
