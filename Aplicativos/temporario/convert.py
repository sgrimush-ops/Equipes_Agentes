import pandas as pd
from pathlib import Path

# Configuração de caminhos
base_dir = Path(__file__).parent
arquivo_txt = base_dir / "ean_dun.txt"
arquivo_excel = base_dir / "ean_dun.xlsx"

if not arquivo_txt.exists():
    print(f"Erro: Arquivo {arquivo_txt} não encontrado.")
else:
    print(f"Lendo {arquivo_txt.name} ({arquivo_txt.stat().st_size / 1024 / 1024:.2f} MB)...")
    
    # Tentativa de leitura com separador ; e encoding utf-8
    try:
        df = pd.read_csv(arquivo_txt, sep=';', encoding='utf-8', on_bad_lines='skip')
    except UnicodeDecodeError:
        df = pd.read_csv(arquivo_txt, sep=';', encoding='latin-1', on_bad_lines='skip')

    print(f"Salvando como {arquivo_excel.name}...")
    # Salvando com encoding utf-8-sig para compatibilidade com Excel
    df.to_excel(arquivo_excel, index=False)
    
    print("Conversão concluída com sucesso!")
