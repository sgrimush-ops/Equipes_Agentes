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
# Caminho absoluto conforme ambiente local (Regra 26)
arquivo_entrada = Path(r'C:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\import_querys\query.parquet')

def compute_metrics(df_subset, loja_nome):
    """Computa as métricas de ruptura para um subconjunto de dados (Loja ou Geral)."""
    if df_subset.empty:
        return pd.DataFrame()
        
    c_cd = (df_subset['CODIGO_EMPRESA'] == 15) & (df_subset['FORMA_ABASTECIMENTO'].isin(['M', 'C']))
    c_loja = df_subset['CODIGO_EMPRESA'] != 15
    c_rup_loja = df_subset['QUANTIDADE_DISPONIVEL'] <= 0
    # Ruptura CD considera estoque 0 ou abaixo da embalagem de transferência apenas para formas M e C
    c_rup_cd = (df_subset['QUANTIDADE_DISPONIVEL'] <= 0) | (df_subset['QUANTIDADE_DISPONIVEL'] < df_subset['EMBL_TRANSFERENCIA'])
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
    df_temp['Base_CD'] = df_subset['CODIGO_PRODUTO'].where(c_cd)
    df_temp['Ruptura_CD'] = df_subset['CODIGO_PRODUTO'].where(c_cd & c_rup_cd)
    df_temp['Rup_CD_Pend_Forn'] = df_subset['CODIGO_PRODUTO'].where(c_cd & c_rup_cd & c_pend_forn)
    
    df_temp['Base_Loja'] = df_subset['CODIGO_PRODUTO'].where(c_loja)
    df_temp['Ruptura_Loja'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_rup_loja)
    df_temp['Rup_Loja_CD'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_rup_loja_cd)
    df_temp['Rup_Loja_Forn'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_rup_loja_forn)
    df_temp['Rup_Loja_Crossdocking'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_rup_loja_cross)
    
    df_temp['Rup_Loja_Neg'] = df_subset['CODIGO_PRODUTO'].where(c_neg)
    df_temp['Rup_Loja_Pend_Transf'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_rup_loja & c_pend_transf)
    df_temp['Rup_Loja_Pend_Forn'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_rup_loja & c_pend_forn)

    resumo = df_temp.groupby('COMPRADOR').nunique().reset_index()

    # Total Geral do subset
    total_cd = df_subset.loc[c_cd, 'CODIGO_PRODUTO'].nunique()
    total_loja = df_subset.loc[c_loja, 'CODIGO_PRODUTO'].nunique()

    total_dict = {
        'COMPRADOR': 'TOTAL GERAL',
        'Base_CD': total_cd,
        'Ruptura_CD': resumo['Ruptura_CD'].sum(), 
        'Rup_CD_Pend_Forn': resumo['Rup_CD_Pend_Forn'].sum(),
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
    final_df['% Ruptura CD'] = (final_df['Ruptura_CD'] / final_df['Base_CD'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. CD Pend. Forn'] = (final_df['Rup_CD_Pend_Forn'] / final_df['Base_CD'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Ruptura Loja'] = (final_df['Ruptura_Loja'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Loja (CD)'] = (final_df['Rup_Loja_CD'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Forn. Loja (L)'] = (final_df['Rup_Loja_Forn'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Crossdocking (I)'] = (final_df['Rup_Loja_Crossdocking'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Loja Neg.'] = (final_df['Rup_Loja_Neg'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    
    # CD 15 (LOJA == '15') utiliza Base_CD como denominador para estoque negativo
    mask_cd15 = final_df['LOJA'] == '15'
    if mask_cd15.any():
        final_df.loc[mask_cd15, '% Rup. Loja Neg.'] = (final_df.loc[mask_cd15, 'Rup_Loja_Neg'] / final_df.loc[mask_cd15, 'Base_CD'].replace(0, np.nan) * 100).fillna(0)

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
        soma_neg = final_df.loc[mask_comp_lojas & (final_df['LOJA'] != '15'), 'Rup_Loja_Neg'].sum()
        soma_pend_transf = final_df.loc[mask_comp_lojas, 'Rup_Loja_Pend_Transf'].sum()
        soma_pend_forn = final_df.loc[mask_comp_lojas, 'Rup_Loja_Pend_Forn'].sum()
        soma_pend_cd_forn = final_df.loc[mask_comp_lojas, 'Rup_CD_Pend_Forn'].sum()
        soma_base_cd = final_df.loc[mask_comp_lojas, 'Base_CD'].sum()

        final_df.loc[mask_comp_todas, 'Base_Loja'] = soma_base_loja
        final_df.loc[mask_comp_todas, 'Ruptura_Loja'] = soma_rup_loja
        final_df.loc[mask_comp_todas, 'Rup_Loja_CD'] = soma_rup_loja_cd
        final_df.loc[mask_comp_todas, 'Rup_Loja_Forn'] = soma_rup_loja_forn
        final_df.loc[mask_comp_todas, 'Rup_Loja_Crossdocking'] = soma_rup_loja_cross
        final_df.loc[mask_comp_todas, 'Rup_Loja_Neg'] = soma_neg
        final_df.loc[mask_comp_todas, 'Rup_Loja_Pend_Transf'] = soma_pend_transf
        final_df.loc[mask_comp_todas, 'Rup_Loja_Pend_Forn'] = soma_pend_forn
        final_df.loc[mask_comp_todas, 'Rup_CD_Pend_Forn'] = soma_pend_cd_forn

        if soma_base_loja > 0:
            final_df.loc[mask_comp_todas, '% Ruptura Loja'] = soma_rup_loja / soma_base_loja * 100
            final_df.loc[mask_comp_todas, '% Rup. Loja (CD)'] = soma_rup_loja_cd / soma_base_loja * 100
            final_df.loc[mask_comp_todas, '% Rup. Forn. Loja (L)'] = soma_rup_loja_forn / soma_base_loja * 100
            final_df.loc[mask_comp_todas, '% Rup. Crossdocking (I)'] = soma_rup_loja_cross / soma_base_loja * 100
            final_df.loc[mask_comp_todas, '% Rup. Loja Neg.'] = soma_neg / soma_base_loja * 100
            final_df.loc[mask_comp_todas, '% Rup. Loja Pend. Transf'] = soma_pend_transf / soma_base_loja * 100
            final_df.loc[mask_comp_todas, '% Rup. Loja Pend. Forn'] = soma_pend_forn / soma_base_loja * 100
        if soma_base_cd > 0:
            final_df.loc[mask_comp_todas, '% Rup. CD Pend. Forn'] = soma_pend_cd_forn / soma_base_cd * 100

    # TOTAL GERAL na visão TODAS: soma ponderada de todos os compradores (já corrigidos)
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
        soma_base_cd = final_df.loc[mask_comp_todas_nontotal, 'Base_CD'].sum()
        soma_rup_cd = final_df.loc[mask_comp_todas_nontotal, 'Ruptura_CD'].sum()
        soma_pend_cd_forn = final_df.loc[mask_comp_todas_nontotal, 'Rup_CD_Pend_Forn'].sum()

        final_df.loc[mask_total_todas, 'Base_Loja'] = soma_base
        final_df.loc[mask_total_todas, 'Ruptura_Loja'] = soma_rup
        final_df.loc[mask_total_todas, 'Rup_Loja_CD'] = soma_rup_cd_loja
        final_df.loc[mask_total_todas, 'Rup_Loja_Forn'] = soma_rup_forn
        final_df.loc[mask_total_todas, 'Rup_Loja_Crossdocking'] = soma_rup_cross
        final_df.loc[mask_total_todas, 'Rup_Loja_Neg'] = soma_neg
        final_df.loc[mask_total_todas, 'Rup_Loja_Pend_Transf'] = soma_pend_transf
        final_df.loc[mask_total_todas, 'Rup_Loja_Pend_Forn'] = soma_pend_forn
        final_df.loc[mask_total_todas, 'Base_CD'] = soma_base_cd
        final_df.loc[mask_total_todas, 'Ruptura_CD'] = soma_rup_cd
        final_df.loc[mask_total_todas, 'Rup_CD_Pend_Forn'] = soma_pend_cd_forn

        if soma_base > 0:
            final_df.loc[mask_total_todas, '% Ruptura Loja'] = soma_rup / soma_base * 100
            final_df.loc[mask_total_todas, '% Rup. Loja (CD)'] = soma_rup_cd_loja / soma_base * 100
            final_df.loc[mask_total_todas, '% Rup. Forn. Loja (L)'] = soma_rup_forn / soma_base * 100
            final_df.loc[mask_total_todas, '% Rup. Crossdocking (I)'] = soma_rup_cross / soma_base * 100
            final_df.loc[mask_total_todas, '% Rup. Loja Neg.'] = soma_neg / soma_base * 100
            final_df.loc[mask_total_todas, '% Rup. Loja Pend. Transf'] = soma_pend_transf / soma_base * 100
            final_df.loc[mask_total_todas, '% Rup. Loja Pend. Forn'] = soma_pend_forn / soma_base * 100
        if soma_base_cd > 0:
            final_df.loc[mask_total_todas, '% Ruptura CD'] = soma_rup_cd / soma_base_cd * 100
            final_df.loc[mask_total_todas, '% Rup. CD Pend. Forn'] = soma_pend_cd_forn / soma_base_cd * 100

    # Exportar para JSON (Estratégia No-Server < 10MB)
    dados_json = json.dumps(final_df.to_dict(orient='records'))

    # Preparar opções dos Dropdowns
    compradores = sorted([c for c in df['COMPRADOR'].dropna().unique()])
    
    options_compradores = '<option value="TODOS">TODOS OS COMPRADORES</option>'
    for c in compradores:
        options_compradores += f'<option value="{c}">{c}</option>'
        
    options_lojas = '<option value="TODAS">TODAS AS LOJAS</option>'
    for l in lojas:
        options_lojas += f'<option value="{l}">Loja {l}</option>'

    # Gerar Snapshot Histórico (Funcionalidade integrada da versão remota)
    print("Gerando snapshot histórico...")
    df_resumo_global = df.groupby('COMPRADOR').agg(
        MIX_CD15=('CODIGO_PRODUTO', lambda x: x[(df.loc[x.index, 'CODIGO_EMPRESA'] == 15) & (df.loc[x.index, 'FORMA_ABASTECIMENTO'].isin(['M', 'C']))].nunique())
    ).reset_index()
    df_resumo_global['TIPO'] = 'COMPRADOR'
    df_resumo_global = df_resumo_global.rename(columns={'COMPRADOR': 'IDENTIFICADOR'})
    df_resumo_global = df_resumo_global[['TIPO', 'IDENTIFICADOR', 'MIX_CD15']]
    
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
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="header-info row align-items-center">
                <div class="col-md-4">
                    <h2>📊 Painel de Ruptura</h2>
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
                <div id="chart-container" style="width: 100%; height: 520px;"></div>
            </div>
            
            <div class="card table-container">
                <table class="table table-striped table-hover align-middle">
                    <thead>
                        <tr>
                            <th>COMPRADOR</th>
                            <th>Base CD (M/C)</th>
                            <th>Ruptura CD</th>
                            <th>% Ruptura CD</th>
                            <th>Rup. CD Pend. Forn</th>
                            <th>% Rup. CD Pend. Forn</th>
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
                    <h5 class="card-title">📖 Entenda as Métricas de Ruptura e Abastecimento</h5>
                    <div class="row mt-3">
                        <div class="col-md-6" style="font-size: 0.95rem;">
                            <ul class="list-unstyled">
                                <li class="mb-2"><strong>Base CD (M/C):</strong> Mix de produtos únicos cadastrados no CD (Empresa 15) com abastecimento Centralizado/Matriz (M) ou Central para Loja (C). Tipos "I" (Crossdocking) e "L" (Direto Loja) são excluídos do CD por não formarem estoque de armazenagem.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #FF0000;">Ruptura CD</span> <strong>(%)</strong>: Produtos da Base CD zerados ou com saldo inferior a 1 Embalagem de Transferência.</li>
                                <li class="mb-2"><span class="badge text-dark" style="background-color: #FF7F50;">Rup. CD Pend. Forn</span> <strong>(%)</strong>: Produtos da Base CD em ruptura com Pedido de Fornecedor ativo.</li>
                                <li class="mb-2"><strong>Base Loja:</strong> Total de produtos únicos que deveriam estar ativos nas filiais (computa todos os tipos: M, C, L, I).</li>
                                <li class="mb-2"><span class="badge" style="background-color: #FFA500; color: white;">Ruptura Loja (Total)</span> <strong>(%)</strong>: Produtos da Base Loja com estoque zerado na gôndola/filial.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #E65100; color: white;">Rup. Loja (CD - M/C)</span> <strong>(%)</strong>: Ruptura em filial de itens cujo fluxo de abastecimento é via CD.</li>
                            </ul>
                        </div>
                        <div class="col-md-6" style="font-size: 0.95rem;">
                            <ul class="list-unstyled">
                                <li class="mb-2"><span class="badge" style="background-color: #0288D1; color: white;">Rup. Forn. -> Loja (L)</span> <strong>(%)</strong>: Ruptura de produtos comprados para entrega direta da indústria/fornecedor na loja.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #8E24AA; color: white;">Rup. Crossdocking (I)</span> <strong>(%)</strong>: Ruptura de produtos com fluxo Crossdocking (tipo I).</li>
                                <li class="mb-2"><span class="badge" style="background-color: #800080;">Estoque Neg. Loja</span> <strong>(%)</strong>: Produtos com saldo sistêmico negativo (< 0).</li>
                                <li class="mb-2"><span class="badge text-dark" style="background-color: #FFFF00;">Rup. Loja Pend. Transf / Forn</span> <strong>(%)</strong>: Produtos da loja zerados com Pedido de Transferência ou de Compra.</li>
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
            renderChart(dadosGrafico, (comprador === "TODOS" ? "Visão Total" : comprador) + " | Loja " + (loja === "TODAS" ? "Geral" : loja));
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

            rows.sort((a, b) => b['% Ruptura CD'] - a['% Ruptura CD']);

            if (totalRow) rows.push(totalRow);

            let html = '';
            rows.forEach(row => {
                let isTotal = row.COMPRADOR === "TOTAL GERAL";
                let fw = isTotal ? "font-weight: bold; background-color: #f1f3f5 !important;" : "";
                let pctRupturaLoja = getPctRupturaLoja(row);
                
                html += `<tr style="${fw}">
                    <td style="text-align: left; padding-left: 15px; ${isTotal ? 'background-color:#f1f3f5;' : ''}">${row.COMPRADOR}</td>
                    <td>${fmt(row.Base_CD)}</td>
                    <td>${fmt(row.Ruptura_CD)}</td>
                    <td style="color:#FF0000;font-weight:bold;">${fmt(row['% Ruptura CD'], true)}</td>
                    <td>${fmt(row.Rup_CD_Pend_Forn)}</td>
                    <td style="color:#FF7F50;font-weight:bold;">${fmt(row['% Rup. CD Pend. Forn'], true)}</td>
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
            let ts = (arr, c) => arr.map(d => fmt(d[c]));
            let tsp = (arr, c) => arr.map(d => Math.round(d[c] * 10) / 10 + '%');

            let plotData = [
                {name: 'Ruptura CD (M/C)', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Ruptura CD']), marker: {color: '#FF0000'}, type: 'bar', text: tsp(data,'% Ruptura CD'), textposition: 'auto', offsetgroup: '1', yaxis: 'y'},
                {name: 'Rup. CD Pend. Forn', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. CD Pend. Forn']), marker: {color: '#FF7F50'}, type: 'bar', text: tsp(data,'% Rup. CD Pend. Forn'), textposition: 'auto', offsetgroup: '2', yaxis: 'y'},
                {name: 'Ruptura Loja Total', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Ruptura Loja']), marker: {color: '#FFA500'}, type: 'bar', text: tsp(data,'% Ruptura Loja'), textposition: 'auto', offsetgroup: '3', yaxis: 'y'},
                {name: 'Rup. Loja - CD (M/C)', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. Loja (CD)']), marker: {color: '#E65100'}, type: 'bar', text: tsp(data,'% Rup. Loja (CD)'), textposition: 'auto', offsetgroup: '4', yaxis: 'y'},
                {name: 'Rup. Fornecedor -> Loja (L)', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. Forn. Loja (L)']), marker: {color: '#0288D1'}, type: 'bar', text: tsp(data,'% Rup. Forn. Loja (L)'), textposition: 'auto', offsetgroup: '5', yaxis: 'y'},
                {name: 'Rup. Crossdocking (I)', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. Crossdocking (I)']), marker: {color: '#8E24AA'}, type: 'bar', text: tsp(data,'% Rup. Crossdocking (I)'), textposition: 'auto', offsetgroup: '6', yaxis: 'y'},
                {name: 'Estoque Neg. Loja', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. Loja Neg.']), marker: {color: '#800080'}, type: 'bar', text: tsp(data,'% Rup. Loja Neg.'), textposition: 'auto', offsetgroup: '7', yaxis: 'y'},
                {name: 'Rup. Loja Pend. Transf', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. Loja Pend. Transf']), marker: {color: '#FFFF00'}, type: 'bar', text: tsp(data,'% Rup. Loja Pend. Transf'), textposition: 'auto', offsetgroup: '8', yaxis: 'y'},
                {name: 'Rup. Loja Pend. Forn', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. Loja Pend. Forn']), marker: {color: '#FFD700'}, type: 'bar', text: tsp(data,'% Rup. Loja Pend. Forn'), textposition: 'auto', offsetgroup: '9', yaxis: 'y'}
            ];

            let layout = {
                title: "Ruptura por Comprador - " + tituloExtensao,
                barmode: 'group',
                xaxis: {title: "Comprador"},
                legend: {title: {text: "Métricas"}},
                template: "plotly_white",
                height: 520,
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

