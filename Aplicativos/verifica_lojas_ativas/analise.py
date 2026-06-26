import pandas as pd
import glob
import os

BASE_DIR = r"c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def encontrar_query_parquet():
    # Busca o arquivo query.parquet dentro da pasta Aplicativos
    arquivos = glob.glob(os.path.join(BASE_DIR, "**", "query.parquet"), recursive=True)
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

    if not all([col_prod, col_emp]):
        print(f"Colunas não identificadas! Encontradas: {list(df.columns)}")
        return
        
    print(f"Colunas base -> Prod: {col_prod}, Desc: {col_desc}, Loja: {col_emp}")

    # Filtrar apenas os produtos que possuem alguma loja
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
        
    df_ativos[col_emp] = df_ativos[col_emp].astype(str).str.replace('.0', '', regex=False).str.zfill(3)
    lojas_pequenas = {'004', '005', '007'}
    
    # Agrupar por produto e compilar a lista de lojas ativas
    grupo = df_ativos.groupby([col_prod, col_desc] if col_desc else [col_prod])[col_emp].apply(list).reset_index()
    grupo.columns = ['Produto', 'Descricao', 'Lojas_Ativas'] if col_desc else ['Produto', 'Lojas_Ativas']
    
    # Calcular estoque do CD (empresa 15) e soma da venda das empresas
    col_estoque = next((c for c in df.columns if 'disponivel' in c.lower()), None)
    col_venda = next((c for c in df.columns if 'qtd_vendida' in c.lower()), None)
    col_cd = None
    # Procurar empresa 15 (CD)
    if col_emp is not None:
        cd_mask = df[col_emp].astype(str).str.zfill(3) == '015'
        if cd_mask.any():
            col_cd = '015'


    # Soma de vendas por produto (tratando como decimal)
    vendas_prod = None
    if col_prod and col_venda:
        # Converter para string, trocar vírgula por ponto e forçar float
        vendas_tratada = df[col_venda].astype(str).str.replace(',', '.').str.replace(' ', '').str.strip()
        vendas_tratada = pd.to_numeric(vendas_tratada, errors='coerce').fillna(0)
        vendas_prod = df.assign(_venda_num=vendas_tratada).groupby(col_prod)['_venda_num'].sum(min_count=1)

    # Soma de Pedidos ao Fornecedor
    col_ped_compra = next((c for c in df.columns if 'pedcompra' in c.lower()), None)
    ped_forn_prod = None
    if col_prod and col_ped_compra:
        ped_forn_tratada = df[col_ped_compra].astype(str).str.replace(',', '.').str.replace(' ', '').str.strip()
        ped_forn_tratada = pd.to_numeric(ped_forn_tratada, errors='coerce').fillna(0)
        ped_forn_prod = df.assign(_ped_forn_num=ped_forn_tratada).groupby(col_prod)['_ped_forn_num'].sum(min_count=1)

    # Soma de Pedidos ao CD (Transferência)
    col_ped_transf = next((c for c in df.columns if 'pedtransf' in c.lower()), None)
    ped_cd_prod = None
    if col_prod and col_ped_transf:
        ped_cd_tratada = df[col_ped_transf].astype(str).str.replace(',', '.').str.replace(' ', '').str.strip()
        ped_cd_tratada = pd.to_numeric(ped_cd_tratada, errors='coerce').fillna(0)
        ped_cd_prod = df.assign(_ped_cd_num=ped_cd_tratada).groupby(col_prod)['_ped_cd_num'].sum(min_count=1)

    # Estoque do CD por produto
    estoque_cd = None
    if col_prod and col_estoque and col_emp:
        estoque_cd = df[df[col_emp].astype(str).str.zfill(3) == '015'].groupby(col_prod)[col_estoque].sum(min_count=1)

    produtos_alvo = []
    for idx, row in grupo.iterrows():
        lojas = set(row['Lojas_Ativas'])
        qtd_total = len(lojas)
        subset_pequenas = lojas.intersection(lojas_pequenas)
        qtd_pequenas = len(subset_pequenas)
        cond1 = (qtd_total == 3)
        cond2 = (0 < qtd_pequenas < 3)
        if cond1 or cond2:
            cod_prod = row['Produto']
            # Estoque do CD
            estoque_val = estoque_cd[cod_prod] if estoque_cd is not None and cod_prod in estoque_cd else ''
            # Soma de vendas
            venda_val = vendas_prod[cod_prod] if vendas_prod is not None and cod_prod in vendas_prod else ''
            
            # Pedidos Pendentes
            ped_forn_val = ped_forn_prod[cod_prod] if ped_forn_prod is not None and cod_prod in ped_forn_prod else ''
            ped_cd_val = ped_cd_prod[cod_prod] if ped_cd_prod is not None and cod_prod in ped_cd_prod else ''
            
            produtos_alvo.append({
                'Codigo_Produto': cod_prod,
                'Descricao': row['Descricao'] if col_desc else 'Sem Desc',
                'Qtd_Lojas_Rede': qtd_total,
                'Filtro_1_Apenas_3_Lojas': 'SIM' if cond1 else 'NAO',
                'Filtro_2_Pequenas_Incompletas': 'SIM' if cond2 else 'NAO',
                'Quais_Lojas_Ativas': ", ".join(sorted(lojas)),
                'Estoque_CD': estoque_val,
                'Venda_Total': venda_val,
                'Pedidos_Fornecedor': ped_forn_val,
                'Pedidos_CD': ped_cd_val
            })

    df_resultado = pd.DataFrame(produtos_alvo)

    path_saida = os.path.join(SCRIPT_DIR, "resultado_analise.xlsx")
    os.makedirs(os.path.dirname(path_saida), exist_ok=True)

    if df_resultado.empty:
        print("\nNenhum produto atendeu aos critérios da sua busca.")
    else:
        df_resultado.to_excel(path_saida, index=False)
        print(f"\n✅ Análise concluída! Foram encontrados {len(df_resultado)} produtos.")
        print(f"O resultado foi salvo em: {path_saida}")
        print("\nPrimeiras linhas do resultado:")
        print(df_resultado[['Codigo_Produto', 'Quais_Lojas_Ativas', 'Estoque_CD', 'Venda_Total']].head(10))

if __name__ == "__main__":
    os.system('cls')
    rodar_analise()
    print("\n[OK] Processo concluido!")
