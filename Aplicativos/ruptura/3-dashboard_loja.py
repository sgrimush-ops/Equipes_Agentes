import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date

# Configuração de diretório de trabalho
if __name__ == '__main__':
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass

base_dir = Path(__file__).parent
arquivo_entrada = Path(r'C:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\import_querys\query.parquet')

# Compradores autorizados para abastecimento/compra no CD 16
COMPRADORES_CD16 = ['SANDRO', 'LAURINDO']

def compute_metrics(df_subset, comprador_nome, prods_cd15_mc, prods_cd16_mc):
    """Computa as métricas de ruptura para um subconjunto de dados (Comprador ou Geral) com separação de CD 15 e CD 16."""
    if df_subset.empty:
        return pd.DataFrame()
        
    c_rup = df_subset['QUANTIDADE_DISPONIVEL'] <= 0
    
    is_comp_cd16 = df_subset['COMPRADOR'].astype(str).str.upper().apply(lambda x: any(c in x for c in COMPRADORES_CD16))
    is_mc = df_subset['FORMA_ABASTECIMENTO'].isin(['M', 'C'])
    
    # Abastecimento via CD 16: apenas compradores CD 16 para itens CD 16
    c_cd16_supply = is_mc & is_comp_cd16 & (~df_subset['CODIGO_PRODUTO'].isin(prods_cd15_mc) | df_subset['CODIGO_PRODUTO'].isin(prods_cd16_mc))
    # Abastecimento via CD 15: demais itens M/C
    c_cd15_supply = is_mc & ~c_cd16_supply
    
    c_rup_cd15 = c_rup & c_cd15_supply
    c_rup_cd16 = c_rup & c_cd16_supply
    c_rup_forn = c_rup & (df_subset['FORMA_ABASTECIMENTO'] == 'L')
    c_rup_cross = c_rup & (df_subset['FORMA_ABASTECIMENTO'] == 'I')
    c_neg = df_subset['QUANTIDADE_DISPONIVEL'] < 0
    
    c_pend_forn = df_subset['QTD_PEND_PEDCOMPRA'] > 0
    if 'QTD_PEND_PEDTRANSF' in df_subset.columns:
        c_pend_transf = df_subset['QTD_PEND_PEDTRANSF'] > 0
    else:
        c_pend_transf = pd.Series(False, index=df_subset.index)

    df_temp = pd.DataFrame({'LOJA_RAW': df_subset['CODIGO_EMPRESA']})
    df_temp['Base_Loja'] = df_subset['CODIGO_PRODUTO']
    df_temp['Ruptura_Loja'] = df_subset['CODIGO_PRODUTO'].where(c_rup)
    df_temp['Rup_Loja_CD15'] = df_subset['CODIGO_PRODUTO'].where(c_rup_cd15)
    df_temp['Rup_Loja_CD16'] = df_subset['CODIGO_PRODUTO'].where(c_rup_cd16)
    df_temp['Rup_Loja_Forn'] = df_subset['CODIGO_PRODUTO'].where(c_rup_forn)
    df_temp['Rup_Loja_Crossdocking'] = df_subset['CODIGO_PRODUTO'].where(c_rup_cross)
    df_temp['Rup_Loja_Neg'] = df_subset['CODIGO_PRODUTO'].where(c_neg)
    df_temp['Rup_Loja_Pend_Transf'] = df_subset['CODIGO_PRODUTO'].where(c_rup & c_pend_transf)
    df_temp['Rup_Loja_Pend_Forn'] = df_subset['CODIGO_PRODUTO'].where(c_rup & c_pend_forn)

    resumo = df_temp.groupby('LOJA_RAW').nunique().reset_index()

    # Total Geral do subset
    total_dict = {
        'LOJA_RAW': 'TOTAL GERAL',
        'Base_Loja': df_subset['CODIGO_PRODUTO'].nunique(),
        'Ruptura_Loja': df_subset.loc[c_rup, 'CODIGO_PRODUTO'].nunique(),
        'Rup_Loja_CD15': df_subset.loc[c_rup_cd15, 'CODIGO_PRODUTO'].nunique(),
        'Rup_Loja_CD16': df_subset.loc[c_rup_cd16, 'CODIGO_PRODUTO'].nunique(),
        'Rup_Loja_Forn': df_subset.loc[c_rup_forn, 'CODIGO_PRODUTO'].nunique(),
        'Rup_Loja_Crossdocking': df_subset.loc[c_rup_cross, 'CODIGO_PRODUTO'].nunique(),
        'Rup_Loja_Neg': df_subset.loc[c_neg, 'CODIGO_PRODUTO'].nunique(),
        'Rup_Loja_Pend_Transf': df_subset.loc[c_rup & c_pend_transf, 'CODIGO_PRODUTO'].nunique(),
        'Rup_Loja_Pend_Forn': df_subset.loc[c_rup & c_pend_forn, 'CODIGO_PRODUTO'].nunique(),
    }
    
    total_df = pd.DataFrame([total_dict])
    resumo = pd.concat([resumo, total_df], ignore_index=True)
    resumo['COMPRADOR_FILTER'] = str(comprador_nome)
    
    # Arrumar os nomes da loja
    resumo['LOJA'] = resumo['LOJA_RAW'].apply(lambda x: f"Loja {int(x)}" if str(x).isdigit() or type(x) in [int, float] else x)
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

    # Mapear produtos ativos em CD 15 e CD 16 para abastecimento M/C
    c_cd15_all = (df['CODIGO_EMPRESA'] == 15) & (df['FORMA_ABASTECIMENTO'].isin(['M', 'C']))
    c_rup_cd15_all = c_cd15_all & ((df['QUANTIDADE_DISPONIVEL'] <= 0) | (df['QUANTIDADE_DISPONIVEL'] < df['EMBL_TRANSFERENCIA']))
    c_pend_cd15_all = c_rup_cd15_all & (df['QTD_PEND_PEDCOMPRA'] > 0)

    c_comp_cd16_all = df['COMPRADOR'].astype(str).str.upper().apply(lambda x: any(c in x for c in COMPRADORES_CD16))
    c_cd16_all = (df['CODIGO_EMPRESA'] == 16) & (df['FORMA_ABASTECIMENTO'].isin(['M', 'C'])) & c_comp_cd16_all
    c_rup_cd16_all = c_cd16_all & ((df['QUANTIDADE_DISPONIVEL'] <= 0) | (df['QUANTIDADE_DISPONIVEL'] < df['EMBL_TRANSFERENCIA']))
    c_pend_cd16_all = c_rup_cd16_all & (df['QTD_PEND_PEDCOMPRA'] > 0)

    prods_cd15_mc = set(df.loc[c_cd15_all, 'CODIGO_PRODUTO'])
    prods_cd16_mc = set(df.loc[c_cd16_all, 'CODIGO_PRODUTO'])

    # Calcular Métricas de Depósito (CD 15 e CD 16) por Comprador para os KPI Cards
    compradores = sorted([x for x in df['COMPRADOR'].dropna().unique()])
    cd_kpis = {}
    
    b15_tot = int(df.loc[c_cd15_all, 'CODIGO_PRODUTO'].nunique())
    r15_tot = int(df.loc[c_rup_cd15_all, 'CODIGO_PRODUTO'].nunique())
    p15_tot = int(df.loc[c_pend_cd15_all, 'CODIGO_PRODUTO'].nunique())
    
    b16_tot = int(df.loc[c_cd16_all, 'CODIGO_PRODUTO'].nunique())
    r16_tot = int(df.loc[c_rup_cd16_all, 'CODIGO_PRODUTO'].nunique())
    p16_tot = int(df.loc[c_pend_cd16_all, 'CODIGO_PRODUTO'].nunique())

    cd_kpis['TODOS'] = {
        'Base_CD15': b15_tot,
        'Ruptura_CD15': r15_tot,
        'Pct_CD15': round(r15_tot / b15_tot * 100, 2) if b15_tot > 0 else 0,
        'Pend_CD15': p15_tot,
        'Pct_Pend_CD15': round(p15_tot / b15_tot * 100, 2) if b15_tot > 0 else 0,
        'Base_CD16': b16_tot,
        'Ruptura_CD16': r16_tot,
        'Pct_CD16': round(r16_tot / b16_tot * 100, 2) if b16_tot > 0 else 0,
        'Pend_CD16': p16_tot,
        'Pct_Pend_CD16': round(p16_tot / b16_tot * 100, 2) if b16_tot > 0 else 0,
    }

    for c in compradores:
        df_c = df[df['COMPRADOR'] == c]
        c_15_c = (df_c['CODIGO_EMPRESA'] == 15) & (df_c['FORMA_ABASTECIMENTO'].isin(['M', 'C']))
        c_15_rup_c = c_15_c & ((df_c['QUANTIDADE_DISPONIVEL'] <= 0) | (df_c['QUANTIDADE_DISPONIVEL'] < df_c['EMBL_TRANSFERENCIA']))
        c_15_p_c = c_15_rup_c & (df_c['QTD_PEND_PEDCOMPRA'] > 0)
        
        is_c16 = any(k in str(c).upper() for k in COMPRADORES_CD16)
        c_16_c = (df_c['CODIGO_EMPRESA'] == 16) & (df_c['FORMA_ABASTECIMENTO'].isin(['M', 'C'])) if is_c16 else pd.Series(False, index=df_c.index)
        c_16_rup_c = c_16_c & ((df_c['QUANTIDADE_DISPONIVEL'] <= 0) | (df_c['QUANTIDADE_DISPONIVEL'] < df_c['EMBL_TRANSFERENCIA']))
        c_16_p_c = c_16_rup_c & (df_c['QTD_PEND_PEDCOMPRA'] > 0)
        
        b15 = int(df_c.loc[c_15_c, 'CODIGO_PRODUTO'].nunique())
        r15 = int(df_c.loc[c_15_rup_c, 'CODIGO_PRODUTO'].nunique())
        p15 = int(df_c.loc[c_15_p_c, 'CODIGO_PRODUTO'].nunique())
        
        b16 = int(df_c.loc[c_16_c, 'CODIGO_PRODUTO'].nunique()) if is_c16 else 0
        r16 = int(df_c.loc[c_16_rup_c, 'CODIGO_PRODUTO'].nunique()) if is_c16 else 0
        p16 = int(df_c.loc[c_16_p_c, 'CODIGO_PRODUTO'].nunique()) if is_c16 else 0
        
        cd_kpis[c] = {
            'Base_CD15': b15,
            'Ruptura_CD15': r15,
            'Pct_CD15': round(r15 / b15 * 100, 2) if b15 > 0 else 0,
            'Pend_CD15': p15,
            'Pct_Pend_CD15': round(p15 / b15 * 100, 2) if b15 > 0 else 0,
            'Base_CD16': b16,
            'Ruptura_CD16': r16,
            'Pct_CD16': round(r16 / b16 * 100, 2) if b16 > 0 else 0,
            'Pend_CD16': p16,
            'Pct_Pend_CD16': round(p16 / b16 * 100, 2) if b16 > 0 else 0,
        }

    # Filtrar CDs (15 e 16) do Ranking de Lojas
    df_lojas = df[~df['CODIGO_EMPRESA'].isin([15, 16])].copy()

    print("Pré-computando métricas do Rank de Lojas com separação CD 15 e CD 16...")
    master_frames = []
    
    # 1. Visão Global (TODOS os Compradores)
    df_todas = compute_metrics(df_lojas, "TODOS", prods_cd15_mc, prods_cd16_mc)
    master_frames.append(df_todas)
    
    # 2. Visão por Comprador
    for c in compradores:
        print(f"Computando Comprador {c}...")
        df_c = compute_metrics(df_lojas[df_lojas['COMPRADOR'] == c], str(c), prods_cd15_mc, prods_cd16_mc)
        master_frames.append(df_c)
        
    final_df = pd.concat(master_frames, ignore_index=True)
    
    # Cálculos Percentuais — linhas individuais (por loja)
    final_df['% Ruptura Loja'] = (final_df['Ruptura_Loja'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Loja (CD 15)'] = (final_df['Rup_Loja_CD15'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Loja (CD 16)'] = (final_df['Rup_Loja_CD16'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Forn. Loja (L)'] = (final_df['Rup_Loja_Forn'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Crossdocking (I)'] = (final_df['Rup_Loja_Crossdocking'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Loja Neg.'] = (final_df['Rup_Loja_Neg'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Loja Pend. Transf'] = (final_df['Rup_Loja_Pend_Transf'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Loja Pend. Forn'] = (final_df['Rup_Loja_Pend_Forn'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)

    # TOTAL GERAL: recalcular valores e percentuais como soma ponderada das lojas
    mask_total = final_df['LOJA'] == 'TOTAL GERAL'
    for comprador_filter in final_df['COMPRADOR_FILTER'].unique():
        mask_comp = final_df['COMPRADOR_FILTER'] == comprador_filter
        mask_lojas = mask_comp & ~mask_total
        mask_total_comp = mask_comp & mask_total

        if not mask_total_comp.any():
            continue

        soma_base = final_df.loc[mask_lojas, 'Base_Loja'].sum()
        soma_rup = final_df.loc[mask_lojas, 'Ruptura_Loja'].sum()
        soma_rup_cd15 = final_df.loc[mask_lojas, 'Rup_Loja_CD15'].sum()
        soma_rup_cd16 = final_df.loc[mask_lojas, 'Rup_Loja_CD16'].sum()
        soma_rup_forn = final_df.loc[mask_lojas, 'Rup_Loja_Forn'].sum()
        soma_rup_cross = final_df.loc[mask_lojas, 'Rup_Loja_Crossdocking'].sum()
        soma_neg = final_df.loc[mask_lojas, 'Rup_Loja_Neg'].sum()
        soma_pend_transf = final_df.loc[mask_lojas, 'Rup_Loja_Pend_Transf'].sum()
        soma_pend_forn = final_df.loc[mask_lojas, 'Rup_Loja_Pend_Forn'].sum()

        final_df.loc[mask_total_comp, 'Base_Loja'] = soma_base
        final_df.loc[mask_total_comp, 'Ruptura_Loja'] = soma_rup
        final_df.loc[mask_total_comp, 'Rup_Loja_CD15'] = soma_rup_cd15
        final_df.loc[mask_total_comp, 'Rup_Loja_CD16'] = soma_rup_cd16
        final_df.loc[mask_total_comp, 'Rup_Loja_Forn'] = soma_rup_forn
        final_df.loc[mask_total_comp, 'Rup_Loja_Crossdocking'] = soma_rup_cross
        final_df.loc[mask_total_comp, 'Rup_Loja_Neg'] = soma_neg
        final_df.loc[mask_total_comp, 'Rup_Loja_Pend_Transf'] = soma_pend_transf
        final_df.loc[mask_total_comp, 'Rup_Loja_Pend_Forn'] = soma_pend_forn

        if soma_base > 0:
            final_df.loc[mask_total_comp, '% Ruptura Loja'] = soma_rup / soma_base * 100
            final_df.loc[mask_total_comp, '% Rup. Loja (CD 15)'] = soma_rup_cd15 / soma_base * 100
            final_df.loc[mask_total_comp, '% Rup. Loja (CD 16)'] = soma_rup_cd16 / soma_base * 100
            final_df.loc[mask_total_comp, '% Rup. Forn. Loja (L)'] = soma_rup_forn / soma_base * 100
            final_df.loc[mask_total_comp, '% Rup. Crossdocking (I)'] = soma_rup_cross / soma_base * 100
            final_df.loc[mask_total_comp, '% Rup. Loja Neg.'] = soma_neg / soma_base * 100
            final_df.loc[mask_total_comp, '% Rup. Loja Pend. Transf'] = soma_pend_transf / soma_base * 100
            final_df.loc[mask_total_comp, '% Rup. Loja Pend. Forn'] = soma_pend_forn / soma_base * 100

    # Exportar para JSON (Estratégia No-Server < 10MB)
    dados_json = json.dumps(final_df.to_dict(orient='records'))
    cd_kpi_json = json.dumps(cd_kpis)

    # Preparar opções dos Dropdowns
    lojas = sorted([int(x) for x in df_lojas['CODIGO_EMPRESA'].dropna().unique()])
    
    options_compradores = '<option value="TODOS">TODOS OS COMPRADORES</option>'
    for c in compradores:
        options_compradores += f'<option value="{c}">{c}</option>'
        
    options_lojas = '<option value="TODAS">TODAS AS LOJAS</option>'
    for l in lojas:
        options_lojas += f'<option value="Loja {l}">Loja {l}</option>'

    # No-Server HTML Javascript Template (Premium Design)
    html_template = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ranking de Lojas - Varejo Insight</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
        <style>
            body { background-color: #f8f9fa; padding: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .card { border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 12px; margin-bottom: 20px; padding: 20px; }
            .header-info { background: #3b2c50; color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
            .table-container { overflow-x: auto; max-height: 800px; }
            .table th { text-align: center !important; font-weight: bold; background-color: #f1f3f5 !important; border-bottom: 2px solid #dee2e6; position: sticky; top: 0; z-index: 2; }
            .table td { text-align: center; vertical-align: middle; white-space: nowrap; }
            .table th:first-child, .table td:first-child { text-align: left; padding-left: 15px; position: sticky; left: 0; background: white; z-index: 1; }
            .table th:first-child { z-index: 3; }
            select.form-select { border-radius: 8px; border: 2px solid #dee2e6; }
            .badge { font-size: 0.85rem; padding: 0.5em 0.8em; }
            .th-cd15 { background-color: #ffebee !important; color: #b71c1c !important; }
            .th-cd16 { background-color: #fbe9e7 !important; color: #bf360c !important; }
            .kpi-card { border-radius: 10px; padding: 15px 20px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.06); }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="header-info row align-items-center">
                <div class="col-md-4">
                    <h2>🏢 Ranking de Lojas</h2>
                    <p class="mb-0">Atualizado em: [DATA_HOJE]</p>
                </div>
                <div class="col-md-4">
                    <label class="form-label mb-1">Filtrar por Comprador</label>
                    <select id="FiltroComprador" class="form-select form-select-lg" onchange="atualizarDashboard()">
                        [OPTIONS_COMPRADORES]
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label mb-1">Foco na Loja</label>
                    <select id="FiltroLoja" class="form-select form-select-lg" onchange="atualizarDashboard()">
                        [OPTIONS_LOJAS]
                    </select>
                </div>
            </div>

            <!-- KPI Cards no Topo -->
            <div class="row g-3 mb-3" id="kpi-cards-container">
                <div class="col-md-4">
                    <div class="kpi-card" style="border-left: 5px solid #FF0000;">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="text-muted fw-bold" style="font-size: 0.85rem;">📦 MIX CD 15 (DEPÓSITO)</span>
                            <span class="badge" style="background-color: #ffebee; color: #b71c1c;">Geral</span>
                        </div>
                        <div class="d-flex align-items-baseline mt-2">
                            <h3 class="mb-0 fw-bold" id="kpi-rup-cd15" style="color: #b71c1c;">-</h3>
                            <span class="ms-2 fw-bold" id="kpi-pct-cd15" style="color: #FF0000; font-size: 1.1rem;">-</span>
                        </div>
                        <div class="d-flex justify-content-between text-muted mt-2" style="font-size: 0.85rem;">
                            <span>Base: <strong id="kpi-base-cd15" class="text-dark">-</strong></span>
                            <span>Pend. Forn: <strong id="kpi-pend-cd15" class="text-dark">-</strong></span>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="kpi-card" style="border-left: 5px solid #C62828;">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="text-muted fw-bold" style="font-size: 0.85rem;">📦 MIX CD 16 (DEPÓSITO)</span>
                            <span class="badge" style="background-color: #fbe9e7; color: #bf360c;">Sandro & Laurindo</span>
                        </div>
                        <div class="d-flex align-items-baseline mt-2">
                            <h3 class="mb-0 fw-bold" id="kpi-rup-cd16" style="color: #bf360c;">-</h3>
                            <span class="ms-2 fw-bold" id="kpi-pct-cd16" style="color: #C62828; font-size: 1.1rem;">-</span>
                        </div>
                        <div class="d-flex justify-content-between text-muted mt-2" style="font-size: 0.85rem;">
                            <span>Base: <strong id="kpi-base-cd16" class="text-dark">-</strong></span>
                            <span>Pend. Forn: <strong id="kpi-pend-cd16" class="text-dark">-</strong></span>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="kpi-card" style="border-left: 5px solid #FFA500;">
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="text-muted fw-bold" style="font-size: 0.85rem;">🏢 RUPTURA NAS LOJAS</span>
                            <span class="badge" style="background-color: #fff3e0; color: #e65100;">Gôndola</span>
                        </div>
                        <div class="d-flex align-items-baseline mt-2">
                            <h3 class="mb-0 fw-bold" id="kpi-rup-loja" style="color: #e65100;">-</h3>
                            <span class="ms-2 fw-bold" id="kpi-pct-loja" style="color: #FFA500; font-size: 1.1rem;">-</span>
                        </div>
                        <div class="d-flex justify-content-between text-muted mt-2" style="font-size: 0.85rem;">
                            <span>Via CD 15: <strong id="kpi-loja-cd15" class="text-dark">-</strong></span>
                            <span>Via CD 16: <strong id="kpi-loja-cd16" class="text-dark">-</strong></span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div id="chart-container" style="width: 100%; height: 520px;"></div>
            </div>
            
            <div class="card table-container">
                <table class="table table-striped table-hover align-middle">
                    <thead>
                        <tr>
                            <th>LOJA</th>
                            <th>Base Loja</th>
                            <th>Ruptura Loja</th>
                            <th>% Ruptura Loja</th>
                            <th class="th-cd15">Rup. Loja (CD 15)</th>
                            <th class="th-cd15">% Rup. Loja (CD 15)</th>
                            <th class="th-cd16">Rup. Loja (CD 16)</th>
                            <th class="th-cd16">% Rup. Loja (CD 16)</th>
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
                    <h5 class="card-title">📖 Entenda as Métricas do Ranking das Lojas</h5>
                    <div class="row mt-3">
                        <div class="col-md-6" style="font-size: 0.95rem;">
                            <ul class="list-unstyled">
                                <li class="mb-2"><strong>Base Loja:</strong> Número total de produtos únicos que deveriam estar ativos na gôndola desta filial (no cenário geral ou no mix do comprador selecionado).</li>
                                <li class="mb-2"><span class="badge" style="background-color: #FFA500; color: white;">Ruptura Loja (Total)</span> <strong>(%)</strong>: Produtos da Base Loja que estão sistemicamente zerados.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #FF0000; color: white;">Rup. Loja (CD 15 - M/C)</span> <strong>(%)</strong>: Ruptura originada do abastecimento via CD 15.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #C62828; color: white;">Rup. Loja (CD 16 - M/C)</span> <strong>(%)</strong>: Ruptura originada do abastecimento via CD 16 (itens exclusivos SANDRO e LAURINDO).</li>
                                <li class="mb-2"><span class="badge" style="background-color: #0288D1; color: white;">Rup. Forn. -> Loja (L)</span> <strong>(%)</strong>: Ruptura de entrega direta de fornecedor.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #8E24AA; color: white;">Rup. Crossdocking (I)</span> <strong>(%)</strong>: Ruptura em produtos com fluxo Crossdocking (tipo I).</li>
                            </ul>
                        </div>
                        <div class="col-md-6" style="font-size: 0.95rem;">
                            <ul class="list-unstyled">
                                <li class="mb-2"><span class="badge" style="background-color: #800080;">Estoque Neg. Loja</span> <strong>(%)</strong>: Produtos com saldo negativo nesta filial.</li>
                                <li class="mb-2"><span class="badge text-dark" style="background-color: #FFFF00;">Rup. Loja Pend. Transf</span> <strong>(%)</strong>: Itens zerados na loja com Pedido de Transferência pendente.</li>
                                <li class="mb-2"><span class="badge text-dark" style="background-color: #FFD700;">Rup. Loja Pend. Forn</span> <strong>(%)</strong>: Itens zerados na loja com Pedido de Compra pendente.</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
        </div>

        <script>
        const masterData = [DADOS_JSON];
        const cdKpiData = [CD_KPI_JSON];

        function atualizarDashboard() {
            const comprador = document.getElementById("FiltroComprador").value;
            const loja = document.getElementById("FiltroLoja").value;

            let dadosComprador = masterData.filter(d => d.COMPRADOR_FILTER === comprador);
            
            let dadosTabela = [];
            let dadosGrafico = [];

            if (loja === "TODAS") {
                dadosTabela = [...dadosComprador];
                dadosGrafico = dadosComprador.filter(d => d.LOJA !== "TOTAL GERAL");
            } else {
                dadosTabela = dadosComprador.filter(d => d.LOJA === loja || d.LOJA === "TOTAL GERAL");
                dadosGrafico = dadosComprador.filter(d => d.LOJA === loja);
            }

            renderTable(dadosTabela, comprador);
            renderChart(dadosGrafico, "Ranking: " + (comprador === "TODOS" ? "Todos os Compradores" : comprador) + " | Foco: " + (loja === "TODAS" ? "Rede Completa" : loja), comprador);
            atualizarKpiCards(dadosComprador, comprador, loja);
        }

        function atualizarKpiCards(dadosComprador, comprador, loja) {
            const cdInfo = cdKpiData[comprador] || cdKpiData["TODOS"];
            const isCompCD16 = (comprador === "TODOS") || (comprador.includes("SANDRO") || comprador.includes("LAURINDO"));

            // CD 15 (Warehouse)
            document.getElementById("kpi-base-cd15").innerText = fmt(cdInfo.Base_CD15);
            document.getElementById("kpi-rup-cd15").innerText = fmt(cdInfo.Ruptura_CD15);
            document.getElementById("kpi-pct-cd15").innerText = fmt(cdInfo.Pct_CD15, true);
            document.getElementById("kpi-pend-cd15").innerText = fmt(cdInfo.Pend_CD15) + " (" + fmt(cdInfo.Pct_Pend_CD15, true) + ")";

            // CD 16 (Warehouse)
            if (isCompCD16) {
                document.getElementById("kpi-base-cd16").innerText = fmt(cdInfo.Base_CD16);
                document.getElementById("kpi-rup-cd16").innerText = fmt(cdInfo.Ruptura_CD16);
                document.getElementById("kpi-pct-cd16").innerText = fmt(cdInfo.Pct_CD16, true);
                document.getElementById("kpi-pend-cd16").innerText = fmt(cdInfo.Pend_CD16) + " (" + fmt(cdInfo.Pct_Pend_CD16, true) + ")";
            } else {
                document.getElementById("kpi-base-cd16").innerText = "-";
                document.getElementById("kpi-rup-cd16").innerText = "-";
                document.getElementById("kpi-pct-cd16").innerText = "(Não compra CD 16)";
                document.getElementById("kpi-pend-cd16").innerText = "-";
            }

            // Loja Foco / Rede
            let lojaRow = (loja === "TODAS") ? dadosComprador.find(d => d.LOJA === "TOTAL GERAL") : dadosComprador.find(d => d.LOJA === loja);
            if (!lojaRow) lojaRow = dadosComprador[0];
            if (lojaRow) {
                document.getElementById("kpi-rup-loja").innerText = fmt(lojaRow.Ruptura_Loja);
                document.getElementById("kpi-pct-loja").innerText = fmt(lojaRow['% Ruptura Loja'], true);
                document.getElementById("kpi-loja-cd15").innerText = fmt(lojaRow.Rup_Loja_CD15) + " (" + fmt(lojaRow['% Rup. Loja (CD 15)'], true) + ")";
                document.getElementById("kpi-loja-cd16").innerText = isCompCD16 ? (fmt(lojaRow.Rup_Loja_CD16) + " (" + fmt(lojaRow['% Rup. Loja (CD 16)'], true) + ")") : "-";
            }
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

        function renderTable(data, comprador) {
            let rows = data.filter(d => d.LOJA !== "TOTAL GERAL");
            let totalRow = data.find(d => d.LOJA === "TOTAL GERAL");

            rows.sort((a, b) => b['% Ruptura Loja'] - a['% Ruptura Loja']);

            if (totalRow) rows.push(totalRow);

            const isCompCD16 = (comprador === "TODOS") || comprador.includes("SANDRO") || comprador.includes("LAURINDO");

            let html = '';
            rows.forEach(row => {
                let isTotal = row.LOJA === "TOTAL GERAL";
                let fw = isTotal ? "font-weight: bold; background-color: #f1f3f5 !important;" : "";
                let pctRupturaLoja = getPctRupturaLoja(row);
                
                let rupCd16Cell = isCompCD16 ? fmt(row.Rup_Loja_CD16) : '<span class="text-muted" title="Comprador não compra para CD 16">-</span>';
                let pctCd16Cell = isCompCD16 ? fmt(row['% Rup. Loja (CD 16)'], true) : '<span class="text-muted">-</span>';

                html += `<tr style="${fw}">
                    <td style="text-align: left; padding-left: 15px; ${isTotal ? 'background-color:#f1f3f5;' : ''}">${row.LOJA}</td>
                    <td>${fmt(row.Base_Loja)}</td>
                    <td>${fmt(row.Ruptura_Loja)}</td>
                    <td style="color:#FFA500;font-weight:bold;">${fmt(pctRupturaLoja, true)}</td>
                    <td>${fmt(row.Rup_Loja_CD15)}</td>
                    <td style="color:#FF0000;font-weight:bold;">${fmt(row['% Rup. Loja (CD 15)'], true)}</td>
                    <td>${rupCd16Cell}</td>
                    <td style="${isCompCD16 ? 'color:#C62828;font-weight:bold;' : ''}">${pctCd16Cell}</td>
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

        function renderChart(data, tituloExtensao, comprador) {
            let tsp = (arr, c) => arr.map(d => Math.round((d[c] || 0) * 10) / 10 + '%');

            let plotData = [
                {name: 'Ruptura Loja Total', x: data.map(d=>d.LOJA), y: data.map(d=>d['% Ruptura Loja']), marker: {color: '#FFA500'}, type: 'bar', text: tsp(data,'% Ruptura Loja'), textposition: 'auto', offsetgroup: '1', yaxis: 'y'},
                {name: 'Rup. Loja - CD 15 (M/C)', x: data.map(d=>d.LOJA), y: data.map(d=>d['% Rup. Loja (CD 15)']), marker: {color: '#FF0000'}, type: 'bar', text: tsp(data,'% Rup. Loja (CD 15)'), textposition: 'auto', offsetgroup: '2', yaxis: 'y'},
                {name: 'Rup. Loja - CD 16 (M/C)', x: data.map(d=>d.LOJA), y: data.map(d=>d['% Rup. Loja (CD 16)']), marker: {color: '#C62828'}, type: 'bar', text: tsp(data,'% Rup. Loja (CD 16)'), textposition: 'auto', offsetgroup: '3', yaxis: 'y'},
                {name: 'Rup. Fornecedor -> Loja (L)', x: data.map(d=>d.LOJA), y: data.map(d=>d['% Rup. Forn. Loja (L)']), marker: {color: '#0288D1'}, type: 'bar', text: tsp(data,'% Rup. Forn. Loja (L)'), textposition: 'auto', offsetgroup: '4', yaxis: 'y'},
                {name: 'Rup. Crossdocking (I)', x: data.map(d=>d.LOJA), y: data.map(d=>d['% Rup. Crossdocking (I)']), marker: {color: '#8E24AA'}, type: 'bar', text: tsp(data,'% Rup. Crossdocking (I)'), textposition: 'auto', offsetgroup: '5', yaxis: 'y'},
                {name: 'Estoque Neg. Loja', x: data.map(d=>d.LOJA), y: data.map(d=>d['% Rup. Loja Neg.']), marker: {color: '#800080'}, type: 'bar', text: tsp(data,'% Rup. Loja Neg.'), textposition: 'auto', offsetgroup: '6', yaxis: 'y'},
                {name: 'Rup. Loja Pend. Transf', x: data.map(d=>d.LOJA), y: data.map(d=>d['% Rup. Loja Pend. Transf']), marker: {color: '#FFFF00'}, type: 'bar', text: tsp(data,'% Rup. Loja Pend. Transf'), textposition: 'auto', offsetgroup: '7', yaxis: 'y'},
                {name: 'Rup. Loja Pend. Forn', x: data.map(d=>d.LOJA), y: data.map(d=>d['% Rup. Loja Pend. Forn']), marker: {color: '#FFD700'}, type: 'bar', text: tsp(data,'% Rup. Loja Pend. Forn'), textposition: 'auto', offsetgroup: '8', yaxis: 'y'}
            ];

            let layout = {
                title: "Desempenho por Filial - " + tituloExtensao,
                barmode: 'group',
                xaxis: {title: "Filial (Loja)", automargin: true, tickangle: -45},
                legend: {title: {text: "Métricas"}},
                template: "plotly_white",
                height: 520,
                margin: {l: 20, r: 20, t: 50, b: 60},
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
    html_template = html_template.replace('[CD_KPI_JSON]', cd_kpi_json)

    output_path = base_dir / "dashboard_loja.html"
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(html_template)
    
    print(f"Dashboard de Lojas gerado com sucesso em: {output_path}")

if __name__ == '__main__':
    principal()
