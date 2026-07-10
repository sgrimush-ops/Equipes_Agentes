"""Conversor de cadastros novos (TXT → XLSX).

Lê o arquivo cadastro_novo.txt da pasta import_querys,
aplica saneamento básico e exporta diretamente como XLSX padronizado.
"""

import os
import sys
import shutil
import pandas as pd
from pathlib import Path


# ── Trava de contexto (execução via VSCode / terminal isolado) ──
if __name__ == '__main__':
    os.chdir(Path(__file__).parent.resolve())


def processar_cadastro_novo() -> None:
    """Lê cadastro_novo.txt, saneia e exporta como XLSX."""

    # Caminho dinâmico para a pasta import_querys
    base_dir = Path(__file__).resolve().parent.parent
    pasta_import = base_dir / 'import_querys'
    arquivo_entrada = pasta_import / 'cadastro_novo.txt'
    arquivo_saida = Path(__file__).parent / 'cadastro_novo.xlsx'

    # Validação de existência
    if not arquivo_entrada.exists():
        print(f'[ERRO] Arquivo não encontrado: {arquivo_entrada}')
        sys.exit(1)

    try:
        # Leitura com delimitador ; e encoding latin-1 (padrão Consinco/Pt-BR)
        df = pd.read_csv(
            arquivo_entrada,
            sep=';',
            encoding='latin-1',
        )

        print(f'[OK] {len(df)} linhas carregadas de {arquivo_entrada.name}')

        # Saneamento de códigos (produto/empresa) — remover decimais espúrios
        for col in ['CODIGO_PRODUTO', 'EMPRESA']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')

        # Exportação padronizada em formato Excel (.xlsx)
        df.to_excel(
            arquivo_saida,
            index=False,
            engine='openpyxl',
        )

        print(f'[OK] Arquivo salvo em: {arquivo_saida}')

        # Remover CSV antigo caso exista na pasta
        arquivo_csv_antigo = Path(__file__).parent / 'cadastro_novo.csv'
        if arquivo_csv_antigo.exists():
            arquivo_csv_antigo.unlink()

    except Exception as e:
        print(f'[ERRO] Falha no processamento: {e}')
        sys.exit(1)


def gerar_ajustepp() -> None:
    """Gera ajustepp.xlsx no formato do GAM com Min/Max baseados em EMBL_TRANSFERENCIA.

    Formato de saída (6 colunas):
        CODIGO_PRODUTO, DESCRICAO_PRODUTO, EMBL_TRANSFERENCIA, EMPRESA, MINIMO, MAXIMO

    Regra de negócio:
        - MINIMO = 1 × EMBL_TRANSFERENCIA (uma embalagem)
        - MAXIMO = 2 × EMBL_TRANSFERENCIA (mínimo + mais uma embalagem)
    """

    arquivo_xlsx = Path(__file__).parent / 'cadastro_novo.xlsx'
    pasta_saida = Path(__file__).parent
    arquivo_saida = pasta_saida / 'ajustepp.xlsx'

    # Validação de existência do arquivo XLSX gerado na etapa anterior
    if not arquivo_xlsx.exists():
        print(f'[ERRO] Arquivo não encontrado: {arquivo_xlsx}')
        print('       Execute processar_cadastro_novo() antes.')
        sys.exit(1)

    try:
        df = pd.read_excel(arquivo_xlsx, engine='openpyxl')
        print(f'[OK] {len(df)} linhas carregadas de {arquivo_xlsx.name}')

        # Saneamento de EMBL_TRANSFERENCIA (extrair numérico puro)
        df['EMBL_TRANSFERENCIA'] = (
            pd.to_numeric(
                df['EMBL_TRANSFERENCIA'].astype(str).str.extract(r'(\d+)')[0],
                errors='coerce',
            )
            .fillna(1)
            .astype(int)
        )

        # Cálculo de Min/Max conforme regra de negócio
        df['MINIMO'] = df['EMBL_TRANSFERENCIA'].astype(int)
        df['MAXIMO'] = (df['EMBL_TRANSFERENCIA'] * 2).astype(int)

        # Selecionar e ordenar colunas no formato do ajustepp.xlsx (GAM)
        colunas_saida = [
            'CODIGO_PRODUTO',
            'DESCRICAO_PRODUTO',
            'EMBL_TRANSFERENCIA',
            'EMPRESA',
            'MINIMO',
            'MAXIMO',
        ]
        df_saida = df[colunas_saida].copy()

        # Garantir tipos inteiros puros
        for col in ['CODIGO_PRODUTO', 'EMBL_TRANSFERENCIA', 'EMPRESA', 'MINIMO', 'MAXIMO']:
            df_saida[col] = pd.to_numeric(df_saida[col], errors='coerce').astype('Int64')

        # Criar pasta de saída se não existir
        pasta_saida.mkdir(parents=True, exist_ok=True)

        # Exportar como xlsx (padrão GAM)
        df_saida.to_excel(arquivo_saida, index=False, engine='openpyxl')

        print(f'[OK] ajustepp.xlsx gerado com {len(df_saida)} linhas em {arquivo_saida}')

        # Mover para pasta bd_entrada do GAM
        destino_dir = Path(__file__).resolve().parent.parent / 'GAM' / 'bd_entrada'
        destino_dir.mkdir(parents=True, exist_ok=True)
        destino = destino_dir / 'ajustepp.xlsx'
        shutil.move(str(arquivo_saida), str(destino))
        print(f'[OK] Movido para: {destino}')

    except Exception as e:
        print(f'[ERRO] Falha ao gerar ajustepp: {e}')
        sys.exit(1)


if __name__ == '__main__':
    processar_cadastro_novo()
    gerar_ajustepp()
    print('[OK] Processo concluído com sucesso!')