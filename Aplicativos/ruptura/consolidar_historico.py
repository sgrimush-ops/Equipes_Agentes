import pandas as pd
from pathlib import Path
import os

# Configuração de diretório de trabalho
if __name__ == '__main__':
    os.chdir(Path(__file__).parent.resolve())

def consolidar():
    diretorio_historico = Path('historico_ruptura')
    arquivo_saida = diretorio_historico / 'ruptura_consolidada.parquet'
    
    arquivos = list(diretorio_historico.glob('ruptura_*.parquet'))
    # Ignorar o arquivo consolidado se ele já existir na lista
    arquivos = [f for f in arquivos if f.name != 'ruptura_consolidada.parquet']
    
    if not arquivos:
        print("Nenhum arquivo de histórico encontrado para consolidar.")
        return

    print(f"Consolidando {len(arquivos)} arquivos...")
    dfs = []
    for arq in arquivos:
        try:
            df_temp = pd.read_parquet(arq)
            dfs.append(df_temp)
        except Exception as e:
            print(f"Erro ao ler {arq}: {e}")

    if dfs:
        df_final = pd.concat(dfs, ignore_index=True)
        # Remover duplicatas se necessário (por exemplo, Produto x Loja x Data)
        # Mas por ora, apenas concatenamos conforme o fluxo esperado
        df_final.to_parquet(arquivo_saida)
        print(f"Consolidação concluída: {arquivo_saida}")
    else:
        print("Falha na consolidação: nenhum dado válido lido.")

if __name__ == '__main__':
    consolidar()
