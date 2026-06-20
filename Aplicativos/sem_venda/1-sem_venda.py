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
    if 'QTD_VENDIDA_PERIODO' in df.columns:
        df['QTD_VENDIDA_PERIODO'] = pd.to_numeric(df['QTD_VENDIDA_PERIODO'], errors='coerce').fillna(0)
    else:
        df['QTD_VENDIDA_PERIODO'] = 0
        
    if 'QUANTIDADE_DISPONIVEL' in df.columns:
        df['QUANTIDADE_DISPONIVEL'] = pd.to_numeric(df['QUANTIDADE_DISPONIVEL'], errors='coerce').fillna(0)
    else:
        df['QUANTIDADE_DISPONIVEL'] = 0
    
    # Filtrar Sem Venda: Nao teve vendas mas TEM estoque fisico maior que zero na loja
    df_sem_venda = df[(df['QTD_VENDIDA_PERIODO'] <= 0) & (df['QUANTIDADE_DISPONIVEL'] > 0)].copy()
    
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
        'DEPARTAMENTO', 'CODIGO_PRODUTO', 'DESCRICAO_PRODUTO', 
        'EMPRESA', 'STATUS', 'ESTOQUE', 'PEDIDOS_PENDENTES', 
        'QTD_VENDIDA_PERIODO'
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
