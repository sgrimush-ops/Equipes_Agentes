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
arquivo_entrada = Path(r'c:\Users\Alessandro.soares.BAKLIZI\Downloads\Equipes_Agentes\Aplicativos\import_querys\query.parquet')

def compute_metrics(df_subset, loja_nome):
    """Computa as métricas de ruptura para um subconjunto de dados (Loja ou Geral)."""
    if df_subset.empty:
        return pd.DataFrame()
        
    c_cd = df_subset['CODIGO_EMPRESA'] == 15
    c_loja = df_subset['CODIGO_EMPRESA'] != 15
    c_rup_loja = df_subset['QUANTIDADE_DISPONIVEL'] <= 0
    # Ruptura CD considera estoque 0 ou abaixo da embalagem de transferência
    c_rup_cd = (df_subset['QUANTIDADE_DISPONIVEL'] <= 0) | (df_subset['QUANTIDADE_DISPONIVEL'] < df_subset['EMBL_TRANSFERENCIA'])
    c_neg = df_subset['QUANTIDADE_DISPONIVEL'] < 0
    c_pend = df_subset['QTD_PEND_PEDCOMPRA'] > 0
    c_est = df_subset['QUANTIDADE_DISPONIVEL'] > 0

    df_temp = pd.DataFrame({'COMPRADOR': df_subset['COMPRADOR']})
    df_temp['Base_CD'] = df_subset['CODIGO_PRODUTO'].where(c_cd)
    df_temp['Ruptura_CD'] = df_subset['CODIGO_PRODUTO'].where(c_cd & c_rup_cd)
    df_temp['Base_Loja'] = df_subset['CODIGO_PRODUTO'].where(c_loja)
    df_temp['Ruptura_Loja'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_rup_loja)
    df_temp['Rup_Loja_Neg'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_neg)
    df_temp['Rup_Loja_Pend'] = df_subset['CODIGO_PRODUTO'].where(c_loja & c_rup_loja & c_pend)
    df_temp['Est_Pend'] = df_subset['CODIGO_PRODUTO'].where(c_est & c_pend)

    resumo = df_temp.groupby('COMPRADOR').nunique().reset_index()

    # Total Geral do subset
    total_cd = df_subset.loc[c_cd, 'CODIGO_PRODUTO'].nunique()
    total_loja = df_subset.loc[c_loja, 'CODIGO_PRODUTO'].nunique()

    total_dict = {
        'COMPRADOR': 'TOTAL GERAL',
        'Base_CD': total_cd,
        'Ruptura_CD': resumo['Ruptura_CD'].sum(), 
        'Base_Loja': total_loja,
        'Ruptura_Loja': resumo['Ruptura_Loja'].sum(),
        'Rup_Loja_Neg': resumo['Rup_Loja_Neg'].sum(),
        'Rup_Loja_Pend': resumo['Rup_Loja_Pend'].sum(),
        'Est_Pend': resumo['Est_Pend'].sum(),
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
                       'QTD_PEND_PEDCOMPRA', 'QUANTIDADE_ESTOQUE_MINIMO', 'QUANTIDADE_ESTOQUE_MAXIMO']
    
    for col in cols_saneamento:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.replace(',', '.', regex=False)
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
    
    # Cálculos Percentuais
    final_df['% Ruptura CD'] = (final_df['Ruptura_CD'] / final_df['Base_CD'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Ruptura Loja'] = (final_df['Ruptura_Loja'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Loja Neg.'] = (final_df['Rup_Loja_Neg'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Loja Pend.'] = (final_df['Rup_Loja_Pend'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Est. c/ Ped.'] = (final_df['Est_Pend'] / (final_df['Base_CD'] + final_df['Base_Loja']).replace(0, np.nan) * 100).fillna(0)

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
        MIX_CD15=('CODIGO_PRODUTO', lambda x: x[df.loc[x.index, 'CODIGO_EMPRESA'] == 15].nunique())
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
            .table td { text-align: center; vertical-align: middle; }
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
                <div id="chart-container" style="width: 100%; height: 500px;"></div>
            </div>
            
            <div class="card table-container">
                <table class="table table-striped table-hover align-middle">
                    <thead>
                        <tr>
                            <th>COMPRADOR</th>
                            <th>Base CD</th>
                            <th>Ruptura CD</th>
                            <th>% Ruptura CD</th>
                            <th>Base Loja</th>
                            <th>Ruptura Loja</th>
                            <th>% Ruptura Loja</th>
                            <th>Est. Neg. Loja</th>
                            <th>% Est. Neg. Loja</th>
                            <th>Rup. Loja Pend.</th>
                            <th>% Rup. Loja Pend.</th>
                            <th>Est. com Ped.</th>
                            <th>% Est. com Ped.</th>
                        </tr>
                    </thead>
                    <tbody id="tabela-body">
                    </tbody>
                </table>
            </div>

            <div class="card mt-2">
                <div class="card-body">
                    <h5 class="card-title">📖 Entenda as Métricas</h5>
                    <div class="row mt-3">
                        <div class="col-md-6" style="font-size: 0.95rem;">
                            <ul class="list-unstyled">
                                <li class="mb-2"><strong>Base CD:</strong> Número total de produtos únicos que fazem parte do mix comercial do comprador no Centro de Distribuição (Empresa 15).</li>
                                <li class="mb-2"><span class="badge" style="background-color: #FF0000;">Ruptura CD</span> <strong>(%)</strong>: Produtos da Base CD que estão sistemicamente zerados ou com saldo inferior a 1 Embalagem de Transferência.</li>
                                <li class="mb-2"><strong>Base Loja:</strong> Número total de produtos únicos que o comprador atende e que deveriam estar ativos nas filiais.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #FFA500; color: white;">Ruptura Loja</span> <strong>(%)</strong>: Produtos da Base Loja que estão com estoque zerado na gôndola/filial.</li>
                            </ul>
                        </div>
                        <div class="col-md-6" style="font-size: 0.95rem;">
                            <ul class="list-unstyled">
                                <li class="mb-2"><span class="badge" style="background-color: #800080;">Estoque Neg. Loja</span> <strong>(%)</strong>: Produtos da Base Loja com saldo sistêmico menor que zero.</li>
                                <li class="mb-2"><span class="badge text-dark" style="background-color: #FFFF00;">Rup. Loja Pend.</span> <strong>(%)</strong>: Produtos da Base Loja zerados, mas com Pedidos de Compra emitidos.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #008000;">Est. com Pedido</span> <strong>(%)</strong>: Produtos com saldo positivo que possuem trânsito de compras ativo.</li>
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
                
                html += `<tr style="${fw}">
                    <td style="text-align: left; padding-left: 15px; ${isTotal ? 'background-color:#f1f3f5;' : ''}">${row.COMPRADOR}</td>
                    <td>${fmt(row.Base_CD)}</td>
                    <td>${fmt(row.Ruptura_CD)}</td>
                    <td style="color:#FF0000;font-weight:bold;">${fmt(row['% Ruptura CD'], true)}</td>
                    <td>${fmt(row.Base_Loja)}</td>
                    <td>${fmt(row.Ruptura_Loja)}</td>
                    <td style="color:#FFA500;font-weight:bold;">${fmt(row['% Ruptura Loja'], true)}</td>
                    <td>${fmt(row.Rup_Loja_Neg)}</td>
                    <td style="color:#800080;font-weight:bold;">${fmt(row['% Rup. Loja Neg.'], true)}</td>
                    <td>${fmt(row.Rup_Loja_Pend)}</td>
                    <td style="color:#d4a017;font-weight:bold;">${fmt(row['% Rup. Loja Pend.'], true)}</td>
                    <td>${fmt(row.Est_Pend)}</td>
                    <td style="color:#008000;font-weight:bold;">${fmt(row['% Est. c/ Ped.'], true)}</td>
                </tr>`;
            });
            document.getElementById("tabela-body").innerHTML = html;
        }

        function renderChart(data, tituloExtensao) {
            let ts = (arr, c) => arr.map(d => fmt(d[c]));
            let tsp = (arr, c) => arr.map(d => Math.round(d[c] * 10) / 10 + '%');

            let plotData = [
                {name: 'Base CD', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d.Base_CD), marker: {color: '#00008B'}, type: 'bar', text: ts(data,'Base_CD'), textposition: 'auto', offsetgroup: '1', yaxis: 'y2'},
                {name: 'Ruptura CD', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Ruptura CD']), marker: {color: '#FF0000'}, type: 'bar', text: tsp(data,'% Ruptura CD'), textposition: 'auto', offsetgroup: '2', yaxis: 'y'},
                {name: 'Base Loja', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d.Base_Loja), marker: {color: '#ADD8E6'}, type: 'bar', text: ts(data,'Base_Loja'), textposition: 'auto', offsetgroup: '3', yaxis: 'y2'},
                {name: 'Ruptura Loja', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Ruptura Loja']), marker: {color: '#FFA500'}, type: 'bar', text: tsp(data,'% Ruptura Loja'), textposition: 'auto', offsetgroup: '4', yaxis: 'y'},
                {name: 'Estoque Neg. Loja', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. Loja Neg.']), marker: {color: '#800080'}, type: 'bar', text: tsp(data,'% Rup. Loja Neg.'), textposition: 'auto', offsetgroup: '5', yaxis: 'y'},
                {name: 'Rup. Loja Pend.', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Rup. Loja Pend.']), marker: {color: '#FFFF00'}, type: 'bar', text: tsp(data,'% Rup. Loja Pend.'), textposition: 'auto', offsetgroup: '6', yaxis: 'y'},
                {name: 'Est. com Ped.', x: data.map(d=>d.COMPRADOR), y: data.map(d=>d['% Est. c/ Ped.']), marker: {color: '#008000'}, type: 'bar', text: tsp(data,'% Est. c/ Ped.'), textposition: 'auto', offsetgroup: '7', yaxis: 'y'}
            ];

            let layout = {
                title: "Ruptura por Comprador - " + tituloExtensao,
                barmode: 'group',
                xaxis: {title: "Comprador"},
                legend: {title: {text: "Métricas"}},
                template: "plotly_white",
                height: 500,
                margin: {l: 20, r: 20, t: 50, b: 20},
                yaxis: {title: "Percentual (%)", side: 'left', range: [0, 100]},
                yaxis2: {title: "Quantidade Mix", side: 'right', overlaying: 'y', showgrid: false}
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