import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date

# Configuração de diretório de trabalho (Regra 30)
if __name__ == '__main__':
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass

base_dir = Path(__file__).parent
arquivo_entrada = Path(r'C:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\import_querys\query.parquet')

# Compradores autorizados para abastecimento/compra no CD 16
COMPRADORES_CD16 = ['SANDRO', 'LAURINDO']

def is_comprador_cd16(nome):
    if not nome or not isinstance(nome, str):
        return False
    nome_up = nome.upper()
    return any(c in nome_up for c in COMPRADORES_CD16)

def compute_metrics(df_subset, loja_nome):
    """Computa as métricas de ruptura para um subconjunto de dados (Loja ou Geral) para CD 15, CD 16 e Lojas."""
    if df_subset.empty:
        return pd.DataFrame()
        
    c_cd15 = (df_subset['CODIGO_EMPRESA'] == 15) & (df_subset['FORMA_ABASTECIMENTO'].isin(['M', 'C']))
    
    # Apenas SANDRO e LAURINDO compram para o CD 16; para outros compradores o cadastro é virtual
    c_comp_cd16 = df_subset['COMPRADOR'].astype(str).str.upper().apply(lambda x: any(c in x for c in COMPRADORES_CD16))
    c_cd16 = (df_subset['CODIGO_EMPRESA'] == 16) & (df_subset['FORMA_ABASTECIMENTO'].isin(['M', 'C'])) & c_comp_cd16
    
    c_loja = ~df_subset['CODIGO_EMPRESA'].isin([15, 16])
    c_rup_loja = df_subset['QUANTIDADE_DISPONIVEL'] <= 0
    
    # Ruptura CD considera estoque 0 ou abaixo da embalagem de transferência apenas para formas M e C
    c_rup_cd15 = c_cd15 & ((df_subset['QUANTIDADE_DISPONIVEL'] <= 0) | (df_subset['QUANTIDADE_DISPONIVEL'] < df_subset['EMBL_TRANSFERENCIA']))
    c_rup_cd16 = c_cd16 & ((df_subset['QUANTIDADE_DISPONIVEL'] <= 0) | (df_subset['QUANTIDADE_DISPONIVEL'] < df_subset['EMBL_TRANSFERENCIA']))
    c_neg = df_subset['QUANTIDADE_DISPONIVEL'] < 0
    
    # Segmentação de Ruptura de Loja por Forma de Abastecimento
    c_rup_loja_cd = c_rup_loja & (df_subset['FORMA_ABASTECIMENTO'].isin(['M', 'C']))
    c_rup_loja_forn = c_rup_loja & (df_subset['FORMA_ABASTECIMENTO'] == 'L')
    c_rup_loja_cross = c_rup_loja & (df_subset['FORMA_ABASTECIMENTO'] == 'I')
    
    c_pend_forn = df_subset['QTD_PEND_PEDCOMPRA'] > 0
    if 'QTD_PEND_PEDTRANSF' in df_subset.columns:
        c_pend_transf = df_subset['QTD_PEND_PEDTRANSF'] > 0
    else:
        c_pend_transf = pd.Series(False, index=df_subset.index)

    df_temp = pd.DataFrame({'COMPRADOR': df_subset['COMPRADOR']})
    df_temp['Base_CD15'] = df_subset['CODIGO_PRODUTO'].where(c_cd15)
    df_temp['Ruptura_CD15'] = df_subset['CODIGO_PRODUTO'].where(c_rup_cd15)
    df_temp['Rup_CD15_Pend_Forn'] = df_subset['CODIGO_PRODUTO'].where(c_rup_cd15 & c_pend_forn)

    df_temp['Base_CD16'] = df_subset['CODIGO_PRODUTO'].where(c_cd16)
    df_temp['Ruptura_CD16'] = df_subset['CODIGO_PRODUTO'].where(c_rup_cd16)
    df_temp['Rup_CD16_Pend_Forn'] = df_subset['CODIGO_PRODUTO'].where(c_rup_cd16 & c_pend_forn)
    
    df_temp['Base_Loja'] = df_subset['CODIGO_PRODUTO'].where(c_loja)
    df_temp['Ruptura_Loja'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_rup_loja)
    df_temp['Rup_Loja_CD'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_rup_loja_cd)
    df_temp['Rup_Loja_Forn'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_rup_loja_forn)
    df_temp['Rup_Loja_Crossdocking'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_rup_loja_cross)
    
    df_temp['Rup_Loja_Neg'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_neg)
    df_temp['Rup_Loja_Pend_Transf'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_rup_loja & c_pend_transf)
    df_temp['Rup_Loja_Pend_Forn'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_rup_loja & c_pend_forn)

    resumo = df_temp.groupby('COMPRADOR').nunique().reset_index()

    # Total Geral do subset
    total_cd15 = df_subset.loc[c_cd15, 'CODIGO_PRODUTO'].nunique()
    total_cd16 = df_subset.loc[c_cd16, 'CODIGO_PRODUTO'].nunique()
    total_loja = df_subset.loc[c_loja, 'CODIGO_PRODUTO'].nunique()

    total_dict = {
        'COMPRADOR': 'TOTAL GERAL',
        'Base_CD15': total_cd15,
        'Ruptura_CD15': resumo['Ruptura_CD15'].sum(), 
        'Rup_CD15_Pend_Forn': resumo['Rup_CD15_Pend_Forn'].sum(),
        'Base_CD16': total_cd16,
        'Ruptura_CD16': resumo['Ruptura_CD16'].sum(), 
        'Rup_CD16_Pend_Forn': resumo['Rup_CD16_Pend_Forn'].sum(),
        'Base_Loja': total_loja,
        'Ruptura_Loja': resumo['Ruptura_Loja'].sum(),
        'Rup_Loja_CD': resumo['Rup_Loja_CD'].sum(),
        'Rup_Loja_Forn': resumo['Rup_Loja_Forn'].sum(),
        'Rup_Loja_Crossdocking': resumo['Rup_Loja_Crossdocking'].sum(),
        'Rup_Loja_Neg': resumo['Rup_Loja_Neg'].sum(),
        'Rup_Loja_Pend_Transf': resumo['Rup_Loja_Pend_Transf'].sum(),
        'Rup_Loja_Pend_Forn': resumo['Rup_Loja_Pend_Forn'].sum(),
    }
    
    total_df = pd.DataFrame([total_dict])
    resumo = pd.concat([resumo, total_df], ignore_index=True)
    resumo['LOJA'] = str(loja_nome)
    
    return resumo

def principal():
    if not arquivo_entrada.exists():
        print(f"Erro: {arquivo_entrada} não encontrado.")
        return

    print("Carregando dados...")
    df = pd.read_parquet(arquivo_entrada)

    # Saneamento (Regra 65)
    cols_saneamento = ['QUANTIDADE_DISPONIVEL', 'EMBL_COMPRA', 'EMBL_TRANSFERENCIA', 
                       'QTD_PEND_PEDCOMPRA', 'QTD_PEND_PEDTRANSF', 'QUANTIDADE_ESTOQUE_MINIMO', 'QUANTIDADE_ESTOQUE_MAXIMO']
    
    for col in cols_saneamento:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    print("Pré-computando métricas...")
    master_frames = []
    
    # 1. Visão Global (TODAS as Lojas)
    df_todas = compute_metrics(df, "TODAS")
    master_frames.append(df_todas)
    
    # 2. Visão por Filial
    lojas = sorted([int(x) for x in df['CODIGO_EMPRESA'].dropna().unique()])
    for loja in lojas:
        print(f"Computando Loja {loja}...")
        df_loja = compute_metrics(df[df['CODIGO_EMPRESA'] == loja], str(loja))
        master_frames.append(df_loja)
        
    final_df = pd.concat(master_frames, ignore_index=True)
    
    # Cálculos Percentuais — linhas individuais (por comprador dentro de cada loja)
    final_df['% Ruptura CD 15'] = (final_df['Ruptura_CD15'] / final_df['Base_CD15'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. CD 15 Pend. Forn'] = (final_df['Rup_CD15_Pend_Forn'] / final_df['Base_CD15'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Ruptura CD 16'] = (final_df['Ruptura_CD16'] / final_df['Base_CD16'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. CD 16 Pend. Forn'] = (final_df['Rup_CD16_Pend_Forn'] / final_df['Base_CD16'].replace(0, np.nan) * 100).fillna(0)
    
    final_df['% Ruptura Loja'] = (final_df['Ruptura_Loja'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Loja (CD)'] = (final_df['Rup_Loja_CD'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Forn. Loja (L)'] = (final_df['Rup_Loja_Forn'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Crossdocking (I)'] = (final_df['Rup_Loja_Crossdocking'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Loja Neg.'] = (final_df['Rup_Loja_Neg'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    
    # CDs individuais utilizam sua respectiva Base_CD como denominador para estoque negativo
    mask_cd15 = final_df['LOJA'] == '15'
    if mask_cd15.any():
        final_df.loc[mask_cd15, '% Rup. Loja Neg.'] = (final_df.loc[mask_cd15, 'Rup_Loja_Neg'] / final_df.loc[mask_cd15, 'Base_CD15'].replace(0, np.nan) * 100).fillna(0)
    mask_cd16 = final_df['LOJA'] == '16'
    if mask_cd16.any():
        final_df.loc[mask_cd16, '% Rup. Loja Neg.'] = (final_df.loc[mask_cd16, 'Rup_Loja_Neg'] / final_df.loc[mask_cd16, 'Base_CD16'].replace(0, np.nan) * 100).fillna(0)

    final_df['% Rup. Loja Pend. Transf'] = (final_df['Rup_Loja_Pend_Transf'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Loja Pend. Forn'] = (final_df['Rup_Loja_Pend_Forn'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)

    # Visão "TODAS": nunique() deduplica entre lojas, gerando % inflados.
    # Recalcular linhas de compradores e TOTAL GERAL como soma das lojas individuais.
    mask_todas = final_df['LOJA'] == 'TODAS'
    mask_total = final_df['COMPRADOR'] == 'TOTAL GERAL'
    lojas_str = [str(l) for l in lojas]
    mask_lojas_individuais = final_df['LOJA'].isin(lojas_str)

    # Para cada comprador na visão TODAS, somar valores das lojas individuais
    compradores_unicos = final_df.loc[mask_todas & ~mask_total, 'COMPRADOR'].unique()
    for comp in compradores_unicos:
        mask_comp_lojas = mask_lojas_individuais & (final_df['COMPRADOR'] == comp)
        mask_comp_todas = mask_todas & (final_df['COMPRADOR'] == comp)

        if not mask_comp_todas.any() or not mask_comp_lojas.any():
            continue

        soma_base_loja = final_df.loc[mask_comp_lojas, 'Base_Loja'].sum()
        soma_rup_loja = final_df.loc[mask_comp_lojas, 'Ruptura_Loja'].sum()
        soma_rup_loja_cd = final_df.loc[mask_comp_lojas, 'Rup_Loja_CD'].sum()
        soma_rup_loja_forn = final_df.loc[mask_comp_lojas, 'Rup_Loja_Forn'].sum()
        soma_rup_loja_cross = final_df.loc[mask_comp_lojas, 'Rup_Loja_Crossdocking'].sum()
        soma_neg = final_df.loc[mask_comp_lojas & (~final_df['LOJA'].isin(['15', '16'])), 'Rup_Loja_Neg'].sum()
        soma_pend_transf = final_df.loc[mask_comp_lojas, 'Rup_Loja_Pend_Transf'].sum()
        soma_pend_forn = final_df.loc[mask_comp_lojas, 'Rup_Loja_Pend_Forn'].sum()
        soma_pend_cd15_forn = final_df.loc[mask_comp_lojas, 'Rup_CD15_Pend_Forn'].sum()
        soma_pend_cd16_forn = final_df.loc[mask_comp_lojas, 'Rup_CD16_Pend_Forn'].sum()
        soma_base_cd15 = final_df.loc[mask_comp_lojas, 'Base_CD15'].sum()
        soma_base_cd16 = final_df.loc[mask_comp_lojas, 'Base_CD16'].sum()

        final_df.loc[mask_comp_todas, 'Base_Loja'] = soma_base_loja
        final_df.loc[mask_comp_todas, 'Ruptura_Loja'] = soma_rup_loja
        final_df.loc[mask_comp_todas, 'Rup_Loja_CD'] = soma_rup_loja_cd
        final_df.loc[mask_comp_todas, 'Rup_Loja_Forn'] = soma_rup_loja_forn
        final_df.loc[mask_comp_todas, 'Rup_Loja_Crossdocking'] = soma_rup_loja_cross
        final_df.loc[mask_comp_todas, 'Rup_Loja_Neg'] = soma_neg
        final_df.loc[mask_comp_todas, 'Rup_Loja_Pend_Transf'] = soma_pend_transf
        final_df.loc[mask_comp_todas, 'Rup_Loja_Pend_Forn'] = soma_pend_forn
        final_df.loc[mask_comp_todas, 'Rup_CD15_Pend_Forn'] = soma_pend_cd15_forn
        final_df.loc[mask_comp_todas, 'Rup_CD16_Pend_Forn'] = soma_pend_cd16_forn

        if soma_base_loja > 0:
            final_df.loc[mask_comp_todas, '% Ruptura Loja'] = soma_rup_loja / soma_base_loja * 100
            final_df.loc[mask_comp_todas, '% Rup. Loja (CD)'] = soma_rup_loja_cd / soma_base_loja * 100
            final_df.loc[mask_comp_todas, '% Rup. Forn. Loja (L)'] = soma_rup_loja_forn / soma_base_loja * 100
            final_df.loc[mask_comp_todas, '% Rup. Crossdocking (I)'] = soma_rup_loja_cross / soma_base_loja * 100
            final_df.loc[mask_comp_todas, '% Rup. Loja Neg.'] = soma_neg / soma_base_loja * 100
            final_df.loc[mask_comp_todas, '% Rup. Loja Pend. Transf'] = soma_pend_transf / soma_base_loja * 100
            final_df.loc[mask_comp_todas, '% Rup. Loja Pend. Forn'] = soma_pend_forn / soma_base_loja * 100
        if soma_base_cd15 > 0:
            final_df.loc[mask_comp_todas, '% Rup. CD 15 Pend. Forn'] = soma_pend_cd15_forn / soma_base_cd15 * 100
        if soma_base_cd16 > 0:
            final_df.loc[mask_comp_todas, '% Rup. CD 16 Pend. Forn'] = soma_pend_cd16_forn / soma_base_cd16 * 100

    # TOTAL GERAL na visão TODAS: soma ponderada de todos os compradores
    mask_total_todas = mask_todas & mask_total
    mask_comp_todas_nontotal = mask_todas & ~mask_total
    if mask_total_todas.any():
        soma_base = final_df.loc[mask_comp_todas_nontotal, 'Base_Loja'].sum()
        soma_rup = final_df.loc[mask_comp_todas_nontotal, 'Ruptura_Loja'].sum()
        soma_rup_cd_loja = final_df.loc[mask_comp_todas_nontotal, 'Rup_Loja_CD'].sum()
        soma_rup_forn = final_df.loc[mask_comp_todas_nontotal, 'Rup_Loja_Forn'].sum()
        soma_rup_cross = final_df.loc[mask_comp_todas_nontotal, 'Rup_Loja_Crossdocking'].sum()
        soma_neg = final_df.loc[mask_comp_todas_nontotal, 'Rup_Loja_Neg'].sum()
        soma_pend_transf = final_df.loc[mask_comp_todas_nontotal, 'Rup_Loja_Pend_Transf'].sum()
        soma_pend_forn = final_df.loc[mask_comp_todas_nontotal, 'Rup_Loja_Pend_Forn'].sum()
        
        soma_base_cd15 = final_df.loc[mask_comp_todas_nontotal, 'Base_CD15'].sum()
        soma_rup_cd15 = final_df.loc[mask_comp_todas_nontotal, 'Ruptura_CD15'].sum()
        soma_pend_cd15_forn = final_df.loc[mask_comp_todas_nontotal, 'Rup_CD15_Pend_Forn'].sum()

        soma_base_cd16 = final_df.loc[mask_comp_todas_nontotal, 'Base_CD16'].sum()
        soma_rup_cd16 = final_df.loc[mask_comp_todas_nontotal, 'Ruptura_CD16'].sum()
        soma_pend_cd16_forn = final_df.loc[mask_comp_todas_nontotal, 'Rup_CD16_Pend_Forn'].sum()

        final_df.loc[mask_total_todas, 'Base_Loja'] = soma_base
        final_df.loc[mask_total_todas, 'Ruptura_Loja'] = soma_rup
        final_df.loc[mask_total_todas, 'Rup_Loja_CD'] = soma_rup_cd_loja
        final_df.loc[mask_total_todas, 'Rup_Loja_Forn'] = soma_rup_forn
        final_df.loc[mask_total_todas, 'Rup_Loja_Crossdocking'] = soma_rup_cross
        final_df.loc[mask_total_todas, 'Rup_Loja_Neg'] = soma_neg
        final_df.loc[mask_total_todas, 'Rup_Loja_Pend_Transf'] = soma_pend_transf
        final_df.loc[mask_total_todas, 'Rup_Loja_Pend_Forn'] = soma_pend_forn
        
        final_df.loc[mask_total_todas, 'Base_CD15'] = soma_base_cd15
        final_df.loc[mask_total_todas, 'Ruptura_CD15'] = soma_rup_cd15
        final_df.loc[mask_total_todas, 'Rup_CD15_Pend_Forn'] = soma_pend_cd15_forn

        final_df.loc[mask_total_todas, 'Base_CD16'] = soma_base_cd16
        final_df.loc[mask_total_todas, 'Ruptura_CD16'] = soma_rup_cd16
        final_df.loc[mask_total_todas, 'Rup_CD16_Pend_Forn'] = soma_pend_cd16_forn

        if soma_base > 0:
            final_df.loc[mask_total_todas, '% Ruptura Loja'] = soma_rup / soma_base * 100
            final_df.loc[mask_total_todas, '% Rup. Loja (CD)'] = soma_rup_cd_loja / soma_base * 100
            final_df.loc[mask_total_todas, '% Rup. Forn. Loja (L)'] = soma_rup_forn / soma_base * 100
            final_df.loc[mask_total_todas, '% Rup. Crossdocking (I)'] = soma_rup_cross / soma_base * 100
            final_df.loc[mask_total_todas, '% Rup. Loja Neg.'] = soma_neg / soma_base * 100
            final_df.loc[mask_total_todas, '% Rup. Loja Pend. Transf'] = soma_pend_transf / soma_base * 100
            final_df.loc[mask_total_todas, '% Rup. Loja Pend. Forn'] = soma_pend_forn / soma_base * 100
            
        if soma_base_cd15 > 0:
            final_df.loc[mask_total_todas, '% Ruptura CD 15'] = soma_rup_cd15 / soma_base_cd15 * 100
            final_df.loc[mask_total_todas, '% Rup. CD 15 Pend. Forn'] = soma_pend_cd15_forn / soma_base_cd15 * 100
            
        if soma_base_cd16 > 0:
            final_df.loc[mask_total_todas, '% Ruptura CD 16'] = soma_rup_cd16 / soma_base_cd16 * 100
            final_df.loc[mask_total_todas, '% Rup. CD 16 Pend. Forn'] = soma_pend_cd16_forn / soma_base_cd16 * 100

    # Exportar para JSON (Estratégia No-Server < 10MB)
    dados_json = json.dumps(final_df.to_dict(orient='records'))

    # Preparar opções dos Dropdowns
    compradores = sorted([c for c in df['COMPRADOR'].dropna().unique()])
    
    options_compradores = '<option value="TODOS">TODOS OS COMPRADORES</option>'
    for c in compradores:
        options_compradores += f'<option value="{c}">{c}</option>'
        
    options_lojas = '<option value="TODAS">TODAS AS LOJAS</option>'
    for l in lojas:
        if l == 15:
            options_lojas += f'<option value="{l}">Loja 15 (CD 15)</option>'
        elif l == 16:
            options_lojas += f'<option value="{l}">Loja 16 (CD 16)</option>'
        else:
            options_lojas += f'<option value="{l}">Loja {l}</option>'

    # Gerar Snapshot Histórico
    print("Gerando snapshot histórico...")
    df_resumo_global = df.groupby('COMPRADOR').agg(
        MIX_CD15=('CODIGO_PRODUTO', lambda x: x[(df.loc[x.index, 'CODIGO_EMPRESA'] == 15) & (df.loc[x.index, 'FORMA_ABASTECIMENTO'].isin(['M', 'C']))].nunique()),
        MIX_CD16=('CODIGO_PRODUTO', lambda x: x[(df.loc[x.index, 'CODIGO_EMPRESA'] == 16) & (df.loc[x.index, 'FORMA_ABASTECIMENTO'].isin(['M', 'C'])) & (df.loc[x.index, 'COMPRADOR'].astype(str).str.upper().apply(lambda c: any(k in c for k in COMPRADORES_CD16)))].nunique())
    ).reset_index()
    df_resumo_global['TIPO'] = 'COMPRADOR'
    df_resumo_global = df_resumo_global.rename(columns={'COMPRADOR': 'IDENTIFICADOR'})
    df_resumo_global = df_resumo_global[['TIPO', 'IDENTIFICADOR', 'MIX_CD15', 'MIX_CD16']]
    
    dir_historico = base_dir / "historico_ruptura"
    dir_historico.mkdir(exist_ok=True)
    arquivo_snapshot = dir_historico / f"ruptura_snapshot_{date.today().strftime('%Y-%m-%d')}.parquet"
    df_resumo_global.to_parquet(arquivo_snapshot)
    print(f"Snapshot salvo: {arquivo_snapshot}")

    # No-Server HTML Javascript Template (Premium Design)
    html_template = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Ruptura - Varejo Insight</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
        <style>
            body { background-color: #f8f9fa; padding: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .card { border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 12px; margin-bottom: 20px; padding: 20px; }
            .header-info { background: #2c3e50; color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
            .table-container { overflow-x: auto; max-height: 800px; }
            .table th { text-align: center !important; font-weight: bold; background-color: #f1f3f5 !important; border-bottom: 2px solid #dee2e6; position: sticky; top: 0; z-index: 2; }
            .table td { text-align: center; vertical-align: middle; white-space: nowrap; }
            .table th:first-child, .table td:first-child { text-align: left; padding-left: 15px; position: sticky; left: 0; background: white; z-index: 1; }
            .table th:first-child { z-index: 3; }
            select.form-select { border-radius: 8px; border: 2px solid #dee2e6; }
            .badge { font-size: 0.85rem; padding: 0.5em 0.8em; }
            .th-cd15 { background-color: #ffebee !important; color: #b71c1c !important; }
            .th-cd16 { background-color: #fbe9e7 !important; color: #bf360c !important; }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="header-info row align-items-center">
                <div class="col-md-4">
                    <h2>📊 Painel de Ruptura Multi-CD</h2>
                    <p class="mb-0">Atualizado em: [DATA_HOJE]</p>
                </div>
                <div class="col-md-4">
                    <label class="form-label mb-1">Visão por Loja</label>
                    <select id="FiltroLoja" class="form-select form-select-lg" onchange="atualizarDashboard()">
                        [OPTIONS_LOJAS]
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label mb-1">Filtro Comprador</label>
                    <select id="FiltroComprador" class="form-select form-select-lg" onchange="atualizarDashboard()">
                        [OPTIONS_COMPRADORES]
                    </select>
                </div>
            </div>

            <div class="card">
                <div id="chart-container" style="width: 100%; height: 530px;"></div>
            </div>
            
            <div class="card table-container">
                <table class="table table-striped table-hover align-middle">
                    <thead>
                        <tr>
                            <th>COMPRADOR</th>
                            <th class="th-cd15">Base CD 15</th>
                            <th class="th-cd15">Rup. CD 15</th>
                            <th class="th-cd15">% Rup. CD 15</th>
                            <th class="th-cd15">Pend. Forn CD 15</th>
                            <th class="th-cd15">% Pend. CD 15</th>
                            
                            <th class="th-cd16">Base CD 16</th>
                            <th class="th-cd16">Rup. CD 16</th>
                            <th class="th-cd16">% Rup. CD 16</th>
                            <th class="th-cd16">Pend. Forn CD 16</th>
                            <th class="th-cd16">% Pend. CD 16</th>

                            <th>Base Loja</th>
                            <th>Ruptura Loja</th>
                            <th>% Ruptura Loja</th>
                            <th>Rup. Loja (CD)</th>
                            <th>% Rup. Loja (CD)</th>
                            <th>Rup. Forn. Loja (L)</th>
                            <th>% Rup. Forn. Loja (L)</th>
                            <th>Rup. Crossdocking (I)</th>
                            <th>% Rup. Crossdocking (I)</th>
                            <th>Est. Neg. Loja</th>
                            <th>% Est. Neg. Loja</th>
                            <th>Rup. Loja Pend. Transf</th>
                            <th>% Rup. Loja Pend. Transf</th>
                            <th>Rup. Loja Pend. Forn</th>
                            <th>% Rup. Loja Pend. Forn</th>
                        </tr>
                    </thead>
                    <tbody id="tabela-body">
                    </tbody>
                </table>
            </div>

            <div class="card mt-2">
                <div class="card-body">
                    <h5 class="card-title">📖 Entenda as Métricas de Ruptura e Abastecimento Multi-CD</h5>
                    <div class="row mt-3">
                        <div class="col-md-6" style="font-size: 0.95rem;">
                            <ul class="list-unstyled">
                                <li class="mb-2"><span class="badge" style="background-color: #FF0000; color: white;">Ruptura CD 15</span> <strong>(%)</strong>: Produtos do CD 15 (M/C) zerados ou abaixo da embalagem de transferência.</li>
                                <li class="mb-2"><span class="badge text-dark" style="background-color: #FF7F50;">Rup. CD 15 Pend. Forn</span> <strong>(%)</strong>: Ruptura CD 15 com pedido de compra pendente.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #C62828; color: white;">Ruptura CD 16</span> <strong>(%)</strong>: Produtos do CD 16 (M/C) zerados ou abaixo da embalagem de transferência (calculado exclusivamente para SANDRO e LAURINDO).</li>
                                <li class="mb-2"><span class="badge text-dark" style="background-color: #FF8A65;">Rup. CD 16 Pend. Forn</span> <strong>(%)</strong>: Ruptura CD 16 com pedido de compra pendente.</li>
                                <li class="mb-2"><strong>Base Loja:</strong> Total de produtos ativos nas filiais (fluxos M, C, L, I).</li>
                            </ul>
                        </div>
                        <div class="col-md-6" style="font-size: 0.95rem;">
                            <ul class="list-unstyled">
                                <li class="mb-2"><span class="badge" style="background-color: #FFA500; color: white;">Ruptura Loja (Total)</span> <strong>(%)</strong>: Produtos zerados nas lojas.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #E65100; color: white;">Rup. Loja (CD - M/C)</span> <strong>(%)</strong>: Ruptura em filial de itens cujo fluxo de abastecimento é via CD.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #0288D1; color: white;">Rup. Forn. -> Loja (L)</span> <strong>(%)</strong>: Ruptura de entrega direta da indústria na loja.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #8E24AA; color: white;">Rup. Crossdocking (I)</span> <strong>(%)</strong>: Ruptura Crossdocking.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #800080;">Estoque Neg. Loja</span> <strong>(%)</strong>: Produtos com saldo sistêmico negativo (< 0).</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
        </div>

        <script>
        const masterData = [DADOS_JSON];

        function atualizarDashboard() {
            const loja = document.getElementById("FiltroLoja").value;
            const comprador = document.getElementById("FiltroComprador").value;
            let dadosLoja = masterData.filter(d => d.LOJA === loja);
            
            let dadosTabela = [];
            let dadosGrafico = [];

            if (comprador === "TODOS") {
                dadosTabela = [...dadosLoja];
                dadosGrafico = dadosLoja.filter(d => d.COMPRADOR === "TOTAL GERAL");
            } else {
                dadosTabela = dadosLoja.filter(d => d.COMPRADOR === comprador || d.COMPRADOR === "TOTAL GERAL");
                dadosGrafico = dadosLoja.filter(d => d.COMPRADOR === comprador);
            }

            renderTable(dadosTabela);
            renderChart(dadosGrafico, (comprador === "TODOS" ? "Visão Total" : comprador) + " | " + (loja === "TODAS" ? "Rede Geral" : (loja === "15" ? "CD 15" : (loja === "16" ? "CD 16" : "Loja " + loja))));
        }

        function getPctRupturaLoja(row) {
            if (!row) return 0;
            return row['% Ruptura Loja'] || 0;
        }

        function fmt(val, perc=false) {
            if (val == null) return "0";
            if (typeof val === 'number') {
                if (val % 1 !== 0) {
                    return val.toFixed(2).replace('.', ',') + (perc ? '%' : '');
                } else {
                    return val.toLocaleString('pt-BR') + (perc ? '%' : '');
                }
            }
            return val;
        }

        function renderTable(data) {
            let rows = data.filter(d => d.COMPRADOR !== "TOTAL GERAL");
            let totalRow = data.find(d => d.COMPRADOR === "TOTAL GERAL");

            rows.sort((a, b) => ((b['% Ruptura CD 15'] || 0) + (b['% Ruptura CD 16'] || 0)) - ((a['% Ruptura CD 15'] || 0) + (a['% Ruptura CD 16'] || 0)));

            if (totalRow) rows.push(totalRow);

            let html = '';
            rows.forEach(row => {
                let isTotal = row.COMPRADOR === "TOTAL GERAL";
                let fw = isTotal ? "font-weight: bold; background-color: #f1f3f5 !important;" : "";
                let pctRupturaLoja = getPctRupturaLoja(row);
                
                let isCompCD16 = isTotal || (row.COMPRADOR && (row.COMPRADOR.includes('SANDRO') || row.COMPRADOR.includes('LAURINDO')));
                let baseCd16Cell = isCompCD16 ? fmt(row.Base_CD16) : '<span class="text-muted" title="Comprador não compra para CD 16 (Itens na filial 16 são virtuais)">-</span>';
                let rupCd16Cell = isCompCD16 ? fmt(row.Ruptura_CD16) : '<span class="text-muted">-</span>';
                let pctCd16Cell = isCompCD16 ? fmt(row['% Ruptura CD 16'], true) : '<span class="text-muted">-</span>';
                let pendCd16Cell = isCompCD16 ? fmt(row.Rup_CD16_Pend_Forn) : '<span class="text-muted">-</span>';
                let pctPendCd16Cell = isCompCD16 ? fmt(row['% Rup. CD 16 Pend. Forn'], true) : '<span class="text-muted">-</span>';

                html += `<tr style="${fw}">
                    <td style="text-align: left; padding-left: 15px; ${isTotal ? 'background-color:#f1f3f5;' : ''}">${row.COMPRADOR}</td>
                    
                    <td>${fmt(row.Base_CD15)}</td>
                    <td>${fmt(row.Ruptura_CD15)}</td>
                    <td style="color:#FF0000;font-weight:bold;">${fmt(row['% Ruptura CD 15'], true)}</td>
                    <td>${fmt(row.Rup_CD15_Pend_Forn)}</td>
                    <td style="color:#FF7F50;font-weight:bold;">${fmt(row['% Rup. CD 15 Pend. Forn'], true)}</td>

                    <td>${baseCd16Cell}</td>
                    <td>${rupCd16Cell}</td>
                    <td style="${isCompCD16 ? 'color:#C62828;font-weight:bold;' : ''}">${pctCd16Cell}</td>
                    <td>${pendCd16Cell}</td>
                    <td style="${isCompCD16 ? 'color:#FF8A65;font-weight:bold;' : ''}">${pctPendCd16Cell}</td>

                    <td>${fmt(row.Base_Loja)}</td>
                    <td>${fmt(row.Ruptura_Loja)}</td>
                    <td style="color:#FFA500;font-weight:bold;">${fmt(pctRupturaLoja, true)}</td>
                    <td>${fmt(row.Rup_Loja_CD)}</td>
                    <td style="color:#E65100;font-weight:bold;">${fmt(row['% Rup. Loja (CD)'], true)}</td>
                    <td>${fmt(row.Rup_Loja_Forn)}</td>
                    <td style="color:#0288D1;font-weight:bold;">${fmt(row['% Rup. Forn. Loja (L)'], true)}</td>
                    <td>${fmt(row.Rup_Loja_Crossdocking)}</td>
                    <td style="color:#8E24AA;font-weight:bold;">${fmt(row['% Rup. Crossdocking (I)'], true)}</td>
                    <td>${fmt(row.Rup_Loja_Neg)}</td>
                    <td style="color:#800080;font-weight:bold;">${fmt(row['% Rup. Loja Neg.'], true)}</td>
                    <td>${fmt(row.Rup_Loja_Pend_Transf)}</td>
                    <td style="color:#d4a017;font-weight:bold;">${fmt(row['% Rup. Loja Pend. Transf'], true)}</td>
                    <td>${fmt(row.Rup_Loja_Pend_Forn)}</td>
                    <td style="color:#d4a017;font-weight:bold;">${fmt(row['% Rup. Loja Pend. Forn'], true)}</td>
                </tr>`;
            });
            document.getElementById("tabela-body").innerHTML = html;
        }

        function renderChart(data, tituloExtensao) {
            let tsp = (arr, c) => arr.map(d => Math.round((d[c] || 0) * 10) / 10 + '%');

            let plotData = [
                {name: 'Ruptura CD 15 (M/C)', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Ruptura CD 15']), marker: {color: '#FF0000'}, type: 'bar', text: tsp(data,'% Ruptura CD 15'), textposition: 'auto', offsetgroup: '1', yaxis: 'y'},
                {name: 'Rup. CD 15 Pend. Forn', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. CD 15 Pend. Forn']), marker: {color: '#FF7F50'}, type: 'bar', text: tsp(data,'% Rup. CD 15 Pend. Forn'), textposition: 'auto', offsetgroup: '2', yaxis: 'y'},
                
                {name: 'Ruptura CD 16 (M/C)', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Ruptura CD 16']), marker: {color: '#C62828'}, type: 'bar', text: tsp(data,'% Ruptura CD 16'), textposition: 'auto', offsetgroup: '3', yaxis: 'y'},
                {name: 'Rup. CD 16 Pend. Forn', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. CD 16 Pend. Forn']), marker: {color: '#FF8A65'}, type: 'bar', text: tsp(data,'% Rup. CD 16 Pend. Forn'), textposition: 'auto', offsetgroup: '4', yaxis: 'y'},
                
                {name: 'Ruptura Loja Total', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Ruptura Loja']), marker: {color: '#FFA500'}, type: 'bar', text: tsp(data,'% Ruptura Loja'), textposition: 'auto', offsetgroup: '5', yaxis: 'y'},
                {name: 'Rup. Loja - CD (M/C)', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. Loja (CD)']), marker: {color: '#E65100'}, type: 'bar', text: tsp(data,'% Rup. Loja (CD)'), textposition: 'auto', offsetgroup: '6', yaxis: 'y'},
                {name: 'Rup. Fornecedor -> Loja (L)', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. Forn. Loja (L)']), marker: {color: '#0288D1'}, type: 'bar', text: tsp(data,'% Rup. Forn. Loja (L)'), textposition: 'auto', offsetgroup: '7', yaxis: 'y'},
                {name: 'Rup. Crossdocking (I)', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. Crossdocking (I)']), marker: {color: '#8E24AA'}, type: 'bar', text: tsp(data,'% Rup. Crossdocking (I)'), textposition: 'auto', offsetgroup: '8', yaxis: 'y'},
                {name: 'Estoque Neg. Loja', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. Loja Neg.']), marker: {color: '#800080'}, type: 'bar', text: tsp(data,'% Rup. Loja Neg.'), textposition: 'auto', offsetgroup: '9', yaxis: 'y'},
                {name: 'Rup. Loja Pend. Transf', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. Loja Pend. Transf']), marker: {color: '#FFFF00'}, type: 'bar', text: tsp(data,'% Rup. Loja Pend. Transf'), textposition: 'auto', offsetgroup: '10', yaxis: 'y'},
                {name: 'Rup. Loja Pend. Forn', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. Loja Pend. Forn']), marker: {color: '#FFD700'}, type: 'bar', text: tsp(data,'% Rup. Loja Pend. Forn'), textposition: 'auto', offsetgroup: '11', yaxis: 'y'}
            ];

            let layout = {
                title: "Ruptura Multi-CD e Lojas por Comprador - " + tituloExtensao,
                barmode: 'group',
                xaxis: {title: "Comprador"},
                legend: {title: {text: "Métricas"}},
                template: "plotly_white",
                height: 530,
                margin: {l: 20, r: 20, t: 50, b: 20},
                yaxis: {title: "Percentual (%)", side: 'left'}
            };

            Plotly.react('chart-container', plotData, layout, {displayModeBar: false, responsive: true});
        }

        window.onload = atualizarDashboard;
        </script>
    </body>
    </html>
    """
    
    # Substituições no Template
    html_template = html_template.replace('[DATA_HOJE]', date.today().strftime('%d/%m/%Y'))
    html_template = html_template.replace('[OPTIONS_LOJAS]', options_lojas)
    html_template = html_template.replace('[OPTIONS_COMPRADORES]', options_compradores)
    html_template = html_template.replace('[DADOS_JSON]', dados_json)

    output_path = base_dir / "dashboard_comprador.html"
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(html_template)
    
    print(f"Dashboard gerado com sucesso em: {output_path}")

if __name__ == '__main__':
    principal()