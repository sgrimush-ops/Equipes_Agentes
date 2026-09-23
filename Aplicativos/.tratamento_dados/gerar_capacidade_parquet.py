import os
import sys
from pathlib import Path
import pandas as pd

def encontrar_query_parquet(base_dir: Path) -> Path:
    candidatos = [
        base_dir / "import_querys" / "query.parquet",
        base_dir.parent / "import_querys" / "query.parquet",
        base_dir / "query.parquet",
    ]
    for c in candidatos:
        if c.exists():
            return c
    encontrados = list(base_dir.parent.glob("**/query.parquet"))
    if encontrados:
        return max(encontrados, key=os.path.getmtime)
    raise FileNotFoundError("Arquivo query.parquet não encontrado.")

def gerar_tabela_capacidade():
    dir_atual = Path(__file__).parent.resolve()
    saida_excel = dir_atual / "capacidade.xlsx"
    
    # 1. Localizar fontes de dados
    query_path = encontrar_query_parquet(dir_atual.parent)
    info_path = dir_atual / "info.xlsx"
    cap_antiga_path = dir_atual / "capacidade.xlsx"
    cap_minmax_path = dir_atual.parent / "min_e_max" / "capacidade.xlsx"
    
    print(f"Lendo base de dados Parquet: {query_path}")
    df_query = pd.read_parquet(query_path)
    
    # 2. Construir mapa consolidado de capacidades de gôndola por (CODIGO_PRODUTO, EMPRESA)
    cap_map = {}
    
    # Carregar do min_e_max/capacidade.xlsx se existir
    if cap_minmax_path.exists():
        try:
            df_mm = pd.read_excel(cap_minmax_path)
            for _, r in df_mm.iterrows():
                try:
                    p = int(float(str(r.get('CODIGO_PRODUTO', -1))))
                    e = int(float(str(r.get('EMPRESA', r.get('CODIGO_EMPRESA', -1)))))
                    c = float(str(r.get('CAPACIDADE_GONDOLA', 0)))
                    if p > 0 and e > 0 and c > 0:
                        cap_map[(p, e)] = int(c) if c.is_integer() else c
                except:
                    pass
        except Exception as e:
            print(f"Aviso ao ler {cap_minmax_path.name}: {e}")
            
    # Carregar do capacidade.xlsx anterior da pasta atual se existir
    if cap_antiga_path.exists():
        try:
            df_ant = pd.read_excel(cap_antiga_path)
            for _, r in df_ant.iterrows():
                try:
                    p = int(float(str(r.get('CODIGO_PRODUTO', -1))))
                    e = int(float(str(r.get('EMPRESA', r.get('CODIGO_EMPRESA', -1)))))
                    c = float(str(r.get('CAPACIDADE_GONDOLA', 0)))
                    if p > 0 and e > 0 and c > 0:
                        cap_map[(p, e)] = int(c) if c.is_integer() else c
                except:
                    pass
        except Exception as e:
            print(f"Aviso ao ler capacidade antiga: {e}")
            
    # Carregar de info.xlsx (base atualizada e prioritária)
    if info_path.exists():
        try:
            df_inf = pd.read_excel(info_path)
            for _, r in df_inf.iterrows():
                try:
                    p = int(float(str(r.get('CODIGO_PRODUTO', -1))))
                    e = int(float(str(r.get('EMPRESA', r.get('CODIGO_EMPRESA', -1)))))
                    c = float(str(r.get('CAPACIDADE_GONDOLA', 0)))
                    if p > 0 and e > 0 and c > 0:
                        cap_map[(p, e)] = int(c) if c.is_integer() else c
                except:
                    pass
        except Exception as e:
            print(f"Aviso ao ler info.xlsx: {e}")
            
    print(f"Total de regras de capacidade mapeadas: {len(cap_map)}")
    
    # 3. Montar DataFrame final com todos os itens do query.parquet
    df_result = df_query.copy()
    
    # Normalizar códigos para inteiros
    df_result['CODIGO_PRODUTO_INT'] = pd.to_numeric(df_result['CODIGO_PRODUTO'], errors='coerce').fillna(-1).astype(int)
    df_result['CODIGO_EMPRESA_INT'] = pd.to_numeric(df_result['CODIGO_EMPRESA'], errors='coerce').fillna(-1).astype(int)
    
    # Preencher capacidade de gôndola na última coluna
    df_result['CAPACIDADE_GONDOLA'] = [
        cap_map.get((p, e), None)
        for p, e in zip(df_result['CODIGO_PRODUTO_INT'], df_result['CODIGO_EMPRESA_INT'])
    ]
    
    # Remover colunas auxiliares temporárias
    df_result = df_result.drop(columns=['CODIGO_PRODUTO_INT', 'CODIGO_EMPRESA_INT'])
    
    # Ordenar por código do produto e código da empresa
    col_prod = 'CODIGO_PRODUTO'
    col_emp = 'CODIGO_EMPRESA'
    if col_prod in df_result.columns and col_emp in df_result.columns:
        df_result = df_result.sort_values(by=[col_prod, col_emp]).reset_index(drop=True)
        
    print(f"Gravando planilha de capacidade: {saida_excel}...")
    df_result.to_excel(saida_excel, index=False)
    
    total = len(df_result)
    preenchidos = df_result['CAPACIDADE_GONDOLA'].notna().sum()
    vazios = df_result['CAPACIDADE_GONDOLA'].isna().sum()
    
    print("\n[OK] Planilha capacidade.xlsx gerada com sucesso!")
    print(f"Arquivo: {saida_excel}")
    print(f"Total de registros do query.parquet: {total}")
    print(f"Itens com Capacidade de Gondola: {preenchidos} ({preenchidos/total*100:.1f}%)")
    print(f"Itens sem Capacidade de Gondola: {vazios} ({vazios/total*100:.1f}%)")
    print(f"Total de colunas: {len(df_result.columns)}")
    print(f"Ultima coluna: {df_result.columns[-1]}")

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    gerar_tabela_capacidade()
