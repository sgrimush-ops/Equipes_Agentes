import argparse
from pathlib import Path
import pandas as pd

def processar_sem_venda(
    origem_parquet: Path,
    destino_xlsx: Path | None = None,
) -> Path:
    if not origem_parquet.exists():
        raise FileNotFoundError(f"Arquivo de origem nao encontrado: {origem_parquet}")

    if destino_xlsx is None:
        destino_xlsx = origem_parquet.parent / "sem_venda.xlsx"

    destino_xlsx.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Lendo base mestra: {origem_parquet}")
    df = pd.read_parquet(origem_parquet)
    
    # Preencher vazios para evitar erros de comparacao
    if 'DATA_CADASTRO_PRODUTO' in df.columns:
        # Converter para data e calcular dias ate hoje
        df['DATA_CADASTRO_OBJ'] = pd.to_datetime(df['DATA_CADASTRO_PRODUTO'], format='%d/%m/%Y', errors='coerce')
        df['DIAS_CADASTRO'] = (pd.Timestamp.today().normalize() - df['DATA_CADASTRO_OBJ']).dt.days
        df['DIAS_CADASTRO'] = df['DIAS_CADASTRO'].fillna(0).astype(int)
    else:
        df['DIAS_CADASTRO'] = 0

    if 'QTD_VENDIDA_PERIODO' in df.columns:
        df['QTD_VENDIDA_PERIODO'] = pd.to_numeric(df['QTD_VENDIDA_PERIODO'], errors='coerce').fillna(0)
    else:
        df['QTD_VENDIDA_PERIODO'] = 0
        
    if 'QUANTIDADE_DISPONIVEL' in df.columns:
        df['QUANTIDADE_DISPONIVEL'] = pd.to_numeric(df['QUANTIDADE_DISPONIVEL'], errors='coerce').fillna(0)
    else:
        df['QUANTIDADE_DISPONIVEL'] = 0
    
    # Calcular estoque do CD (empresas 15, 16 e 50) agrupado por produto
    df_cd = df[df['CODIGO_EMPRESA'].isin([15, 16, 50])].copy()
    estoque_cd = df_cd.groupby('CODIGO_PRODUTO')['QUANTIDADE_DISPONIVEL'].sum().reset_index(name='ESTOQUE_CD')
    
    # Filtrar Sem Venda: Nao teve vendas mas TEM estoque fisico maior que zero na loja
    df_sem_venda = df[(df['QTD_VENDIDA_PERIODO'] <= 0) & (df['QUANTIDADE_DISPONIVEL'] > 0)].copy()
    
    # Adicionar o estoque do CD na base
    df_sem_venda = df_sem_venda.merge(estoque_cd, on='CODIGO_PRODUTO', how='left')
    df_sem_venda['ESTOQUE_CD'] = df_sem_venda['ESTOQUE_CD'].fillna(0)
    
    # Excluir as linhas referentes ao CD
    df_sem_venda = df_sem_venda[~df_sem_venda['CODIGO_EMPRESA'].isin([15, 16, 50])]
    
    # Somar Pedidos Pendentes
    qtd_compra = pd.to_numeric(df_sem_venda['QTD_PEND_PEDCOMPRA'], errors='coerce').fillna(0) if 'QTD_PEND_PEDCOMPRA' in df_sem_venda.columns else 0
    qtd_transf = pd.to_numeric(df_sem_venda['QTD_PEND_PEDTRANSF'], errors='coerce').fillna(0) if 'QTD_PEND_PEDTRANSF' in df_sem_venda.columns else 0
    df_sem_venda['PEDIDOS_PENDENTES'] = qtd_compra + qtd_transf
    
    # Renomear colunas para manter padrao antigo
    df_final = df_sem_venda.rename(columns={
        'CODIGO_EMPRESA': 'EMPRESA',
        'STATUS_COMPRA': 'STATUS',
        'QUANTIDADE_DISPONIVEL': 'ESTOQUE'
    })
    
    # Ordenar colunas (colunas faltantes como DATA_CADASTRO foram ignoradas conf. aprovado)
    colunas_finais = [
        'DEPARTAMENTO', 'COMPRADOR', 'CODIGO_PRODUTO', 'DESCRICAO_PRODUTO', 
        'DIAS_CADASTRO', 'EMPRESA', 'STATUS', 'ESTOQUE', 'PEDIDOS_PENDENTES', 
        'QTD_VENDIDA_PERIODO', 'ESTOQUE_CD'
    ]
    
    colunas_existentes = [c for c in colunas_finais if c in df_final.columns]
    df_final = df_final[colunas_existentes]
    
    # Exportar
    print("Gerando arquivo Excel...")
    df_final.to_excel(destino_xlsx, index=False)
    
    print("Processo concluido com sucesso!")
    print(f"Destino: {destino_xlsx}")
    print(f"Itens 'Sem Venda' gerados: {len(df_final)}")
    
    return destino_xlsx

def main() -> int:
    parser = argparse.ArgumentParser(description="Gera o relatorio Sem Venda a partir do master query.parquet.")
    parser.add_argument(
        "--origem",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "import_querys" / "query.parquet",
        help="Caminho do arquivo parquet de origem.",
    )
    parser.add_argument(
        "--destino",
        type=Path,
        default=Path(__file__).resolve().parent / "sem_venda.xlsx",
        help="Caminho do arquivo XLSX de destino.",
    )

    args = parser.parse_args()

    processar_sem_venda(
        origem_parquet=args.origem,
        destino_xlsx=args.destino,
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
