import pandas as pd
from pathlib import Path
import os

if __name__ == '__main__':
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass

def consolidar():
    diretorio_historico = Path('historico_ruptura')
    if not diretorio_historico.exists():
        return
        
    arquivo_saida = diretorio_historico / 'ruptura_consolidada.parquet'
    arquivos = list(diretorio_historico.glob('ruptura_*.parquet'))
    arquivos = [f for f in arquivos if f.name != 'ruptura_consolidada.parquet']
    
    if not arquivos:
        print("Nenhum arquivo de histórico encontrado para consolidar.")
        return

    print(f"Consolidando {len(arquivos)} arquivos...")
    dfs = []
    for arq in arquivos:
        try:
            df_temp = pd.read_parquet(arq)
            for c in df_temp.select_dtypes(include=['object']).columns:
                df_temp[c] = df_temp[c].astype(str)
            dfs.append(df_temp)
        except Exception as e:
            print(f"Erro ao ler {arq}: {e}")

    if dfs:
        try:
            df_final = pd.concat(dfs, ignore_index=True)
            df_final.to_parquet(arquivo_saida, index=False)
            print(f"Consolidação concluída: {arquivo_saida}")
        except Exception as e:
            print(f"Aviso ao concatenar histórico: {e}")
    else:
        print("Nenhum dado válido lido.")

if __name__ == '__main__':
    consolidar()
