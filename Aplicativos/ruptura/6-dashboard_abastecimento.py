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

def compute_metrics(df_subset, forma_nome, comp_nome):
    """Computa as métricas de ruptura para um subconjunto de dados."""
    if df_subset.empty:
        return pd.DataFrame()
        
    c_rup = df_subset['QUANTIDADE_DISPONIVEL'] <= 0

    df_temp = pd.DataFrame({'LOJA_RAW': df_subset['CODIGO_EMPRESA']})
    df_temp['Base_Loja'] = df_subset['CODIGO_PRODUTO']
    df_temp['Ruptura_Loja'] = df_subset['CODIGO_PRODUTO'].where(c_rup)

    resumo = df_temp.groupby('LOJA_RAW').nunique().reset_index()

    # Total Geral do subset
    total_dict = {
        'LOJA_RAW': 'TOTAL GERAL',
        'Base_Loja': df_subset['CODIGO_PRODUTO'].nunique(),
        'Ruptura_Loja': df_subset.loc[c_rup, 'CODIGO_PRODUTO'].nunique(),
    }
    
    total_df = pd.DataFrame([total_dict])
    resumo = pd.concat([resumo, total_df], ignore_index=True)
    resumo['FORMA_ABASTECIMENTO_FILTER'] = str(forma_nome)
    resumo['COMPRADOR_FILTER'] = str(comp_nome)
    
    # Arrumar os nomes da loja
    resumo['LOJA'] = resumo['LOJA_RAW'].apply(lambda x: f"Loja {int(x)}" if str(x).isdigit() or type(x) in [int, float] else x)
    return resumo

def principal():
    if not arquivo_entrada.exists():
        print(f"Erro: {arquivo_entrada} não encontrado.")
        return

    print("Carregando dados...")
    df = pd.read_parquet(arquivo_entrada)

    # Mapear Formas de Abastecimento
    mapa_formas = {
        'M': 'Centralizado/Matriz',
        'C': 'Central para Loja',
        'L': 'Loja Direto',
        'I': 'Inversa/Crossdoking'
    }
    if 'FORMA_ABASTECIMENTO' in df.columns:
        df['FORMA_ABASTECIMENTO'] = df['FORMA_ABASTECIMENTO'].map(mapa_formas).fillna(df['FORMA_ABASTECIMENTO'])

    # Filtrar CD 15 do Ranking de Lojas
    df = df[df['CODIGO_EMPRESA'] != 15].copy()

    if 'FORMA_ABASTECIMENTO' not in df.columns:
        print("Erro: A coluna 'FORMA_ABASTECIMENTO' não foi encontrada em query.parquet. Certifique-se de que a query atualizada já foi importada.")
        return
    
    if 'COMPRADOR' not in df.columns:
        print("Erro: A coluna 'COMPRADOR' não foi encontrada.")
        return

    # Saneamento (Regra 65)
    cols_saneamento = ['QUANTIDADE_DISPONIVEL']
    
    for col in cols_saneamento:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    print("Pré-computando métricas do Rank de Lojas...")
    master_frames = []
    
    compradores = sorted([str(x) for x in df['COMPRADOR'].dropna().unique()])
    formas = sorted([str(x) for x in df['FORMA_ABASTECIMENTO'].dropna().unique()])
    
    def run_and_append(subset, f_filter, c_filter):
        if not subset.empty:
            df_c = compute_metrics(subset, f_filter, c_filter)
            master_frames.append(df_c)

    print("Computando Global...")
    run_and_append(df, "TODOS", "TODOS")
    
    for f in formas:
        print(f"Computando Forma {f} (Todos os Compradores)...")
        run_and_append(df[df['FORMA_ABASTECIMENTO'] == f], f, "TODOS")
        
    for c in compradores:
        print(f"Computando Comprador {c} (Todas as Formas)...")
        run_and_append(df[df['COMPRADOR'] == c], "TODOS", c)
        
    for c in compradores:
        for f in formas:
            subset = df[(df['COMPRADOR'] == c) & (df['FORMA_ABASTECIMENTO'] == f)]
            if not subset.empty:
                run_and_append(subset, f, c)
                
    final_df = pd.concat(master_frames, ignore_index=True)
    
    # Cálculos Percentuais — linhas individuais (por loja)
    final_df['% Ruptura Loja'] = (final_df['Ruptura_Loja'] / final_df['Base_Loja'].replace(0, np.nan) * 100).fillna(0)

    # TOTAL GERAL: recalcular valores e percentuais como soma ponderada das lojas
    mask_total = final_df['LOJA'] == 'TOTAL GERAL'
    for forma_filter in final_df['FORMA_ABASTECIMENTO_FILTER'].unique():
        for comp_filter in final_df['COMPRADOR_FILTER'].unique():
            mask_combo = (final_df['FORMA_ABASTECIMENTO_FILTER'] == forma_filter) & (final_df['COMPRADOR_FILTER'] == comp_filter)
            mask_lojas = mask_combo & ~mask_total
            mask_total_combo = mask_combo & mask_total

            if not mask_total_combo.any():
                continue

            soma_base = final_df.loc[mask_lojas, 'Base_Loja'].sum()
            soma_rup = final_df.loc[mask_lojas, 'Ruptura_Loja'].sum()

            final_df.loc[mask_total_combo, 'Base_Loja'] = soma_base
            final_df.loc[mask_total_combo, 'Ruptura_Loja'] = soma_rup

            if soma_base > 0:
                final_df.loc[mask_total_combo, '% Ruptura Loja'] = soma_rup / soma_base * 100
            else:
                final_df.loc[mask_total_combo, '% Ruptura Loja'] = 0

    # Exportar para JSON (Estratégia No-Server < 10MB)
    dados_json = json.dumps(final_df.to_dict(orient='records'))

    # Preparar opções dos Dropdowns
    lojas = sorted([int(x) for x in df['CODIGO_EMPRESA'].dropna().unique()])
    
    options_formas = '<option value="TODOS">TODAS AS FORMAS DE ABASTECIMENTO</option>'
    for f in formas:
        options_formas += f'<option value="{f}">{f}</option>'
        
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
                <div class="col-md-3">
                    <h2>🏢 Ranking de Lojas</h2>
                    <p class="mb-0">Atualizado em: [DATA_HOJE]</p>
                </div>
                <div class="col-md-3">
                    <label class="form-label mb-1">Filtrar por Forma</label>
                    <select id="FiltroForma" class="form-select form-select-lg" onchange="atualizarDashboard()">
                        [OPTIONS_FORMA_ABASTECIMENTOES]
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label mb-1">Filtrar por Comprador</label>
                    <select id="FiltroComprador" class="form-select form-select-lg" onchange="atualizarDashboard()">
                        [OPTIONS_COMPRADORES]
                    </select>
                </div>
                <div class="col-md-3">
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
                        <div class="col-md-12" style="font-size: 0.95rem;">
                            <ul class="list-unstyled">
                                <li class="mb-2"><strong>Base Loja:</strong> Número total de produtos únicos que deveriam estar ativos na gôndola desta filial considerando os filtros ativos.</li>
                                <li class="mb-2"><span class="badge" style="background-color: #FFA500; color: white;">Ruptura Loja</span> <strong>(%)</strong>: Produtos da Base Loja que estão sistemicamente zerados.</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
        </div>

        <script>
        const masterData = [DADOS_JSON];

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

        function atualizarDashboard() {
            const forma = document.getElementById("FiltroForma").value;
            const comprador = document.getElementById("FiltroComprador").value;
            const loja = document.getElementById("FiltroLoja").value;

            // Render Table (Always shows the selected combination)
            let dadosCombo = masterData.filter(d => d.FORMA_ABASTECIMENTO_FILTER === forma && d.COMPRADOR_FILTER === comprador);
            let dadosTabela = [];

            if (loja === "TODAS") {
                dadosTabela = [...dadosCombo];
            } else {
                dadosTabela = dadosCombo.filter(d => d.LOJA === loja || d.LOJA === "TOTAL GERAL");
            }
            renderTable(dadosTabela);
            
            // Build PlotData for the Chart
            let plotData = [];
            let filterLojaFn = d => (loja === "TODAS" ? d.LOJA !== "TOTAL GERAL" : d.LOJA === loja);
            let tsp = (arr, c) => arr.map(d => Math.round(d[c] * 10) / 10 + '%');
            
            const coresFormas = {
                'Centralizado/Matriz': '#1f77b4',
                'Central para Loja': '#ff7f0e',
                'Loja Direto': '#2ca02c',
                'Inversa/Crossdoking': '#d62728',
                'TODOS': '#FFA500'
            };

            if (forma === "TODOS") {
                // Find all unique forms that are not "TODOS"
                let formasUnicas = [...new Set(masterData.filter(d => d.FORMA_ABASTECIMENTO_FILTER !== "TODOS").map(d => d.FORMA_ABASTECIMENTO_FILTER))];
                formasUnicas.sort();
                
                formasUnicas.forEach((f, idx) => {
                    let dadosF = masterData.filter(d => d.FORMA_ABASTECIMENTO_FILTER === f && d.COMPRADOR_FILTER === comprador && filterLojaFn(d));
                    if(dadosF.length > 0) {
                        plotData.push({
                            name: f,
                            x: dadosF.map(d=>d.LOJA),
                            y: dadosF.map(d=>d['% Ruptura Loja']),
                            marker: {color: coresFormas[f] || '#FFA500'},
                            type: 'bar',
                            text: tsp(dadosF,'% Ruptura Loja'),
                            textposition: 'auto',
                            offsetgroup: idx.toString(),
                            yaxis: 'y'
                        });
                    }
                });
            } else {
                let dadosGrafico = masterData.filter(d => d.FORMA_ABASTECIMENTO_FILTER === forma && d.COMPRADOR_FILTER === comprador && filterLojaFn(d));
                plotData.push({
                    name: 'Ruptura Loja - ' + forma,
                    x: dadosGrafico.map(d=>d.LOJA),
                    y: dadosGrafico.map(d=>d['% Ruptura Loja']),
                    marker: {color: coresFormas[forma] || '#FFA500'},
                    type: 'bar',
                    text: tsp(dadosGrafico,'% Ruptura Loja'),
                    textposition: 'auto',
                    offsetgroup: '1',
                    yaxis: 'y'
                });
            }

            let tituloStr = "Ranking";
            if (forma !== "TODOS") tituloStr += " | Forma: Todas as Formas";
            else tituloStr += " | Forma: Todas as Formas"; // Adjust this text depending on what looks best.
            if (comprador !== "TODOS") tituloStr += " | Comprador: " + comprador;
            tituloStr += " | Foco: " + (loja === "TODAS" ? "Rede Completa" : loja);
            
            renderChart(plotData, tituloStr);
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
                let pctRupturaLoja = getPctRupturaLoja(row);
                
                html += `<tr style="${fw}">
                    <td style="text-align: left; padding-left: 15px; ${isTotal ? 'background-color:#f1f3f5;' : ''}">${row.LOJA}</td>
                    <td>${fmt(row.Base_Loja)}</td>
                    <td>${fmt(row.Ruptura_Loja)}</td>
                    <td style="color:#FFA500;font-weight:bold;">${fmt(pctRupturaLoja, true)}</td>
                </tr>`;
            });
            document.getElementById("tabela-body").innerHTML = html;
        }

        function renderChart(plotData, tituloExtensao) {
            let layout = {
                title: "Desempenho por Filial - " + tituloExtensao,
                barmode: 'group',
                xaxis: {title: "Filial (Loja)", automargin: true, tickangle: -45},
                legend: {title: {text: "Métricas"}, orientation: 'h', y: 1.1},
                template: "plotly_white",
                height: 500,
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
    html_template = html_template.replace('[OPTIONS_FORMA_ABASTECIMENTOES]', options_formas)
    html_template = html_template.replace('[OPTIONS_COMPRADORES]', options_compradores)
    html_template = html_template.replace('[DADOS_JSON]', dados_json)

    output_path = base_dir / "dashboard_forma_abastecimento.html"
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(html_template)
    
    print(f"Dashboard de Formas de Abastecimento gerado com sucesso em: {output_path}")

if __name__ == '__main__':
    principal()
