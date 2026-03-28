import pandas as pd
from pathlib import Path

# Configuração de caminhos
base_dir = Path(__file__).parent
arquivo_txt = base_dir / "ean_dun.txt"
arquivo_excel = base_dir / "ean_dun_tratado.xlsx"

if not arquivo_txt.exists():
    print(f"Erro: Arquivo {arquivo_txt} não encontrado.")
else:
    print(f"Lendo {arquivo_txt.name}...")
    
    # Leitura com separador ; 
    try:
        df = pd.read_csv(arquivo_txt, sep=';', encoding='utf-8', on_bad_lines='skip')
    except UnicodeDecodeError:
        df = pd.read_csv(arquivo_txt, sep=';', encoding='latin-1', on_bad_lines='skip')
#filtrar caracteres especiais na descrição do produto, mater apenas codigo do produto e descrição do produto   

    # 1. Identificação de produtos com caracteres especiais
    # Usamos regex para encontrar qualquer coisa que NÃO seja Letra (A-Z), Número (0-9) ou Espaço (\s)
    # Incluímos caracteres acentuados comuns (À-ÿ) como "normais"
    if 'DESCRICAO' in df.columns:
        print("Buscando caracteres especiais nas descrições...")
        # Regex: identifica se contém algo fora do padrão alfanumérico + espaço + acentos
        padrao_normal = r'^[a-zA-Z0-9\sÀ-ÿ]*$'
        # df_com_problema = df[~df['DESCRICAO'].astype(str).str.match(padrao_normal, na=False)]
        # Alternativa mais direta: encontrar onde tem algo fora do padrão
        regex_especial = r'[^a-zA-Z0-9\sÀ-ÿ]'
        df_ajustar = df[df['DESCRICAO'].astype(str).str.contains(regex_especial, regex=True, na=False)].copy()
        
        # 2. Selecionar colunas e remover duplicatas
        colunas_finais = ['CODIGO_PRODUTO', 'DESCRICAO']
        df_final = df_ajustar[[c for c in colunas_finais if c in df_ajustar.columns]].drop_duplicates(subset=['CODIGO_PRODUTO'])
        
        print(f"Total de itens com caracteres especiais encontrados: {len(df_final)}")
        
        arquivo_ajuste = base_dir / "produtos_para_ajustar.xlsx"
        print(f"Salvando lista para ajuste em {arquivo_ajuste.name}...")
        df_final.to_excel(arquivo_ajuste, index=False)
        print("Relatório de ajustes gerado com sucesso!")
    else:
        print("Erro: Coluna 'DESCRICAO' não encontrada no arquivo.")

if __name__ == '__main__':
    import os
    os.chdir(Path(__file__).parent.resolve())
