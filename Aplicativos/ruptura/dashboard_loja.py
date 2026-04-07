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
arquivo_entrada = Path(r'c:\Users\Alessandro.soares.BAKLIZI\Downloads\Equipes_Agentes\Aplicativos\import_querys\query.parquet')

def compute_metrics(df_subset, comprador_nome):
    """Computa as métricas de ruptura para um subconjunto de dados (Comprador ou Geral)."""
    if df_subset.empty:
        return pd.DataFrame()
        
    c_rup = df_subset['QUANTIDADE_DISPONIVEL'] <= 0
    c_neg = df_subset['QUANTIDADE_DISPONIVEL'] < 0
    c_pend = df_subset['QTD_PEND_PEDCOMPRA'] > 0
    c_est = df_subset['QUANTIDADE_DISPONIVEL'] > 0

    df_temp = pd.DataFrame({'LOJA_RAW': df_subset['CODIGO_EMPRESA']})
    df_temp['Base_Loja'] = df_subset['CODIGO_PRODUTO']
    df_temp['Ruptura_Loja'] = df_subset['CODIGO_PRODUTO'].where(c_rup)
    df_temp['Rup_Loja_Neg'] = df_subset['CODIGO_PRODUTO'].where(c_neg)
    df_temp['Rup_Loja_Pend'] = df_subset['CODIGO_PRODUTO'].where(c_rup & c_pend)
    df_temp['Est_Pend'] = df_subset['CODIGO_PRODUTO'].where(c_est & c_pend)

    resumo = df_temp.groupby('LOJA_RAW').nunique().reset_index()

    # Total Geral do subset
    total_dict = {
        'LOJA_RAW': 'TOTAL GERAL',
        'Base_Loja': df_subset['CODIGO_PRODUTO'].nunique(),
        'Ruptura_Loja': df_subset.loc[c_rup, 'CODIGO_PRODUTO'].nunique(),
        'Rup_Loja_Neg': df_subset.loc[c_neg, 'CODIGO_PRODUTO'].nunique(),
        'Rup_Loja_Pend': df_subset.loc[c_rup & c_pend, 'CODIGO_PRODUTO'].nunique(),
        'Est_Pend': df_subset.loc[c_est & c_pend, 'CODIGO_PRODUTO'].nunique(),
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

    # Filtrar CD 15 do Ranking de Lojas
    df = df[df['CODIGO_EMPRESA'] != 15].copy()

    # Saneamento (Regra 65)
    cols_saneamento = ['QUANTIDADE_DISPONIVEL', 'EMBL_COMPRA', 'EMBL_TRANSFERENCIA', 
                       'QTD_PEND_PEDCOMPRA', 'QUANTIDADE_ESTOQUE_MINIMO', 'QUANTIDADE_ESTOQUE_MAXIMO']
    
    for col in cols_saneamento:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    print("Pré-computando métricas do Rank de Lojas...")
    master_frames = []
    
    # 1. Visão Global (TODOS os Compradores)
    df_todas = compute_metrics(df, "TODOS")
    master_frames.append(df_todas)
    
    # 2. Visão por Comprador
    compradores = sorted([x for x in df['COMPRADOR'].dropna().unique()])
    for c in compradores:
        print(f"Computando Comprador {c}...")
        df_c = compute_metrics(df[df['COMPRADOR'] == c], str(c))
        master_frames.append(df_c)
        
    final_df = pd.concat(master_frames, ignore_index=True)
    
    # Cálculos Percentuais
    final_df['% Ruptura Loja'] = (final_df['Ruptura_Loja'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Loja Neg.'] = (final_df['Rup_Loja_Neg'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Rup. Loja Pend.'] = (final_df['Rup_Loja_Pend'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    final_df['% Est. c/ Ped.'] = (final_df['Est_Pend'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)

    # Exportar para JSON (Estratégia No-Server < 10MB)
    dados_json = json.dumps(final_df.to_dict(orient='records'))

    # Preparar opções dos Dropdowns
    lojas = sorted([int(x) for x in df['CODIGO_EMPRESA'].dropna().unique()])
    
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

            <div class="card">
                <div id="chart-container" style="width: 100%; height: 500px;"></div>
            </div>
            
            <div class="card table-container">
                <table class="table table-striped table-hover align-middle">
                    <thead>
                        <tr>
                            <th>LOJA</th>
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
                    <h5 class="card-title">📖 Entenda as Métricas do Ranking das Lojas</h5>
                    <div class="row mt-3">
                        <div class="col-md-6" style="font-size: 0.95rem;">
                            <ul class="list-unstyled">
                                <li class="mb-2"><strong>Base Loja:</strong> Número total de produtos únicos que deveriam estar ativos na gôndola desta filial (no cenário geral ou no mix do comprador selecionado).</li>
                                <li class="mb-2"><span class="badge" style="background-color: #FFA500; color: white;">Ruptura Loja</span> <strong>(%)</strong>: Produtos da Base Loja que estão sistemicamente zerados.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #800080;">Estoque Neg. Loja</span> <strong>(%)</strong>: Produtos com saldo negativo nesta filial, indicando furos de estoque ou devoluções não processadas.</li>
                            </ul>
                        </div>
                        <div class="col-md-6" style="font-size: 0.95rem;">
                            <ul class="list-unstyled">
                                <li class="mb-2"><span class="badge text-dark" style="background-color: #FFFF00;">Rup. Loja Pend.</span> <strong>(%)</strong>: Produtos da filial que estão sem estoque, porém possuem trânsito / pedido de compra pendente na rede.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #008000;">Est. com Pedido</span> <strong>(%)</strong>: Produtos com saldo positivo na filial que também possuem pedido pendente de reposição.</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
        </div>

        <script>
        const masterData = [DADOS_JSON];

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

            renderTable(dadosTabela);
            renderChart(dadosGrafico, "Ranking: " + (comprador === "TODOS" ? "Todos os Compradores" : comprador) + " | Foco: " + (loja === "TODAS" ? "Rede Completa" : loja));
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
            let rows = data.filter(d => d.LOJA !== "TOTAL GERAL");
            let totalRow = data.find(d => d.LOJA === "TOTAL GERAL");

            rows.sort((a, b) => b['% Ruptura Loja'] - a['% Ruptura Loja']);

            if (totalRow) rows.push(totalRow);

            let html = '';
            rows.forEach(row => {
                let isTotal = row.LOJA === "TOTAL GERAL";
                let fw = isTotal ? "font-weight: bold; background-color: #f1f3f5 !important;" : "";
                
                html += `<tr style="${fw}">
                    <td style="text-align: left; padding-left: 15px; ${isTotal ? 'background-color:#f1f3f5;' : ''}">${row.LOJA}</td>
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
                {name: 'Base Loja', x: data.map(d=>d.LOJA), y: data.map(d=>d.Base_Loja), marker: {color: '#ADD8E6'}, type: 'bar', text: ts(data,'Base_Loja'), textposition: 'auto', offsetgroup: '1', yaxis: 'y2'},
                {name: 'Ruptura Loja', x: data.map(d=>d.LOJA), y: data.map(d=>d['% Ruptura Loja']), marker: {color: '#FFA500'}, type: 'bar', text: tsp(data,'% Ruptura Loja'), textposition: 'auto', offsetgroup: '2', yaxis: 'y'},
                {name: 'Estoque Neg. Loja', x: data.map(d=>d.LOJA), y: data.map(d=>d['% Rup. Loja Neg.']), marker: {color: '#800080'}, type: 'bar', text: tsp(data,'% Rup. Loja Neg.'), textposition: 'auto', offsetgroup: '3', yaxis: 'y'},
                {name: 'Rup. Loja Pend.', x: data.map(d=>d.LOJA), y: data.map(d=>d['% Rup. Loja Pend.']), marker: {color: '#FFFF00'}, type: 'bar', text: tsp(data,'% Rup. Loja Pend.'), textposition: 'auto', offsetgroup: '4', yaxis: 'y'},
                {name: 'Est. com Ped.', x: data.map(d=>d.LOJA), y: data.map(d=>d['% Est. c/ Ped.']), marker: {color: '#008000'}, type: 'bar', text: tsp(data,'% Est. c/ Ped.'), textposition: 'auto', offsetgroup: '5', yaxis: 'y'}
            ];

            let layout = {
                title: "Desempenho por Filial - " + tituloExtensao,
                barmode: 'group',
                xaxis: {title: "Filial (Loja)", automargin: true, tickangle: -45},
                legend: {title: {text: "Métricas"}},
                template: "plotly_white",
                height: 500,
                margin: {l: 20, r: 20, t: 50, b: 60},
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

    output_path = base_dir / "dashboard_loja.html"
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(html_template)
    
    print(f"Dashboard de Lojas gerado com sucesso em: {output_path}")

if __name__ == '__main__':
    principal()
