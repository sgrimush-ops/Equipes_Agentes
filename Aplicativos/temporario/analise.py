import pandas as pd
import glob
import os

def encontrar_query_parquet():
    # Busca o arquivo query.parquet dentro da pasta Aplicativos
    base_dir = r"c:\Users\Alessandro.soares.BAKLIZI\Downloads\Equipes_Agentes\Aplicativos"
    arquivos = glob.glob(os.path.join(base_dir, "**", "query.parquet"), recursive=True)
    if not arquivos:
        print("Erro: query.parquet não encontrado.")
        return None
    
    # Se houver mais de um, pega o mais recém modificado
    mais_recente = max(arquivos, key=os.path.getmtime)
    print(f"Lendo base: {mais_recente}")
    return mais_recente

def rodar_analise():
    path_parquet = encontrar_query_parquet()
    if not path_parquet:
        return
        
    df = pd.read_parquet(path_parquet)
    
    # Identificar nome das colunas
    col_prod = next((c for c in df.columns if 'produto' in c.lower()), None)
    col_desc = next((c for c in df.columns if 'descri' in c.lower()), None)
    col_emp = next((c for c in df.columns if 'empresa' in c.lower() or 'loja' in c.lower()), None)
    col_estq = next((c for c in df.columns if 'estoque' in c.lower()), None) # Apenas como base adicional se precisar

    if not all([col_prod, col_emp]):
        print(f"Colunas não identificadas! Encontradas: {list(df.columns)}")
        return
        
    print(f"Colunas base -> Prod: {col_prod}, Desc: {col_desc}, Loja: {col_emp}")

    # Filtrar apenas os produtos que possuem algunna loja
    df_validos = df.dropna(subset=[col_prod, col_emp]).copy()
    
    # Lojas Ativas - Como o query.parquet (do Varejo) geralmente contém
    # os estoques/informações de produtos que ESTÃO na loja. 
    # Assumimos que existir na base = "ativo na loja", ou buscamos um status 'A'
    col_status = next((c for c in df.columns if 'status' in c.lower()), None)
    
    if col_status:
        df_ativos = df_validos[df_validos[col_status].astype(str).str.upper().isin(['A', 'ATIVO'])].copy()
    else:
        # Se não tem coluna status, assumimos que existir na base parquet já quer dizer ativo/mix
        df_ativos = df_validos.copy()
        
    df_ativos[col_emp] = df_ativos[col_emp].astype(str).str.replace('.0', '').str.zfill(3)
    lojas_pequenas = {'004', '005', '007', '008'}
    
    # Agrupar por produto e compilar a lista de lojas ativas
    grupo = df_ativos.groupby([col_prod, col_desc] if col_desc else [col_prod])[col_emp].apply(list).reset_index()
    grupo.columns = ['Produto', 'Descricao', 'Lojas_Ativas'] if col_desc else ['Produto', 'Lojas_Ativas']
    
    # Aplicar Filtros
    produtos_alvo = []
    
    for idx, row in grupo.iterrows():
        lojas = set(row['Lojas_Ativas'])
        qtd_total = len(lojas)
        
        subset_pequenas = lojas.intersection(lojas_pequenas)
        qtd_pequenas = len(subset_pequenas)
        
        # Filtro 1: Ativos em EXATAMENTE 3 lojas da rede
        cond1 = (qtd_total == 3)
        
        # Filtro 2: Ativos em lojas pequenas, mas não em todas (0 < qtd < 4)
        cond2 = (0 < qtd_pequenas < 4)
        
        if cond1 or cond2:
            produtos_alvo.append({
                'Codigo_Produto': row['Produto'],
                'Descricao': row['Descricao'] if col_desc else 'Sem Desc',
                'Qtd_Lojas_Rede': qtd_total,
                'Filtro_1_Apenas_3_Lojas': 'SIM' if cond1 else 'NAO',
                'Filtro_2_Pequenas_Incompletas': 'SIM' if cond2 else 'NAO',
                'Quais_Lojas_Ativas': ", ".join(sorted(lojas))
            })
            
    df_resultado = pd.DataFrame(produtos_alvo)
    
    path_saida = r"c:\Users\Alessandro.soares.BAKLIZI\Downloads\Equipes_Agentes\Aplicativos\temporario\resultado_analise.csv"
    
    if df_resultado.empty:
        print("\nNenhum produto atendeu aos critérios da sua busca.")
    else:
        df_resultado.to_csv(path_saida, sep=';', index=False, encoding='utf-8-sig')
        print(f"\n✅ Análise concluída! Foram encontrados {len(df_resultado)} produtos.")
        print(f"O resultado foi salvo em: {path_saida}")
        print("\nPrimeiras linhas do resultado:")
        print(df_resultado[['Codigo_Produto', 'Quais_Lojas_Ativas']].head(10))

if __name__ == "__main__":
    rodar_analise()
