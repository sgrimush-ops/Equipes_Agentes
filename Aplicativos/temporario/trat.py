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

    print("Aplicando filtros...")
    
    # Filtro 1: Departamento 'NAO ALIMENTO'
    # Filtro 2: Grupo 'MATERIAL DE LIMPEZA'
    # Usamos o operador OR (|) pois eles estão em ramos diferentes da árvore mercadológica
    condicao = (df['DEPARTAMENTO'] == 'NAO ALIMENTO') | (df['GRUPO'] == 'MATERIAL DE LIMPEZA')
    
    df_filtrado = df[condicao].copy()
    
    initial_count = len(df_filtrado)
    print(f"Itens após filtros: {initial_count}")

    # Remover duplicatas de EAN ou DUN
    # Consideramos a coluna EAN_DUN conforme visto no arquivo
    if 'EAN_DUN' in df_filtrado.columns:
        df_filtrado = df_filtrado.drop_duplicates(subset=['EAN_DUN'], keep='first')
        final_count = len(df_filtrado)
        print(f"Duplicatas removidas: {initial_count - final_count}")
        print(f"Itens únicos finais: {final_count}")

    print(f"Salvando como {arquivo_excel.name}...")
    # Exportação para Excel
    df_filtrado.to_excel(arquivo_excel, index=False)
    
    print("Processamento concluído com sucesso!")
