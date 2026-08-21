import pandas as pd
import json
import os
import sys

def parse_br_currency(x):
    if pd.isna(x):
        return 0.0
    x = str(x).strip()
    if ',' in x and '.' in x:
        x = x.replace('.', '').replace(',', '.')
    elif ',' in x:
        x = x.replace(',', '.')
    try:
        return float(x)
    except:
        return 0.0

def load_and_clean_data(input_file):
    print("Lendo o arquivo de dados (a_pagar_empresa.txt)...")
    encodings = ['cp850', 'cp1252', 'latin1', 'utf-8']
    separators = [';', '\t', ',']
    
    df = None
    for enc in encodings:
        for sep in separators:
            try:
                temp_df = pd.read_csv(input_file, sep=sep, encoding=enc, engine='python', on_bad_lines='skip')
                if len(temp_df.columns) > 5:
                    df = temp_df
                    break
            except Exception:
                continue
        if df is not None:
            break
            
    if df is None or len(df.columns) < 5:
        print("Erro ao ler o arquivo. Verifique se o formato está correto (separado por ponto-e-vírgula ou tabulado).")
        sys.exit(1)

    # Filtrar apenas linhas com EMPRESA válida (números inteiros)
    if 'EMPRESA' in df.columns:
        df = df[df['EMPRESA'].astype(str).str.strip().str.isdigit()].copy()
        df['EMPRESA'] = df['EMPRESA'].astype(str).str.strip()
    else:
        df['EMPRESA'] = '1'

    print(f"Total de registros válidos carregados: {len(df)}")
    print("Tratamento de dados e desduplicação por título único...")

    # Limpar colunas numéricas
    val_cols = ['VALOR_OPERACAO', 'VALOR_NOMINAL_TITULO', 'VALOR_PAGO_TITULO', 'SALDO_DEVEDOR_TITULO']
    for col in val_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_br_currency)
        else:
            df[col] = 0.0

    # Tratar datas
    if 'DATA_VENCIMENTO' in df.columns:
        df['DATA_VENCIMENTO_DT'] = pd.to_datetime(df['DATA_VENCIMENTO'], format='%d/%m/%Y', errors='coerce')
    else:
        print("Aviso: Coluna DATA_VENCIMENTO não encontrada.")
        df['DATA_VENCIMENTO_DT'] = pd.NaT

    # Preencher colunas essenciais
    if 'ESPECIE' in df.columns:
        df['ESPECIE'] = df['ESPECIE'].fillna('OUTROS').astype(str).str.strip()
    else:
        df['ESPECIE'] = 'GERAL'

    if 'TITULO' in df.columns:
        df['TITULO'] = df['TITULO'].fillna('-').astype(str).str.strip()
    else:
        df['TITULO'] = '-'

    if 'FORNECEDOR' in df.columns:
        df['FORNECEDOR'] = df['FORNECEDOR'].fillna('-').astype(str).str.strip()
    else:
        df['FORNECEDOR'] = '-'

    if 'SEQ_TITULO' not in df.columns:
        df['SEQ_TITULO'] = df.index

    # Desduplicar por título único para análise patrimonial sem repetição
    df_dedup = df.drop_duplicates('SEQ_TITULO').copy()

    # Remover registros sem data válida
    df_dedup = df_dedup.dropna(subset=['DATA_VENCIMENTO_DT']).copy()
    df_dedup['DATA_FORMATADA'] = df_dedup['DATA_VENCIMENTO_DT'].dt.strftime('%d/%m/%Y')
    df_dedup['DATA_ISO'] = df_dedup['DATA_VENCIMENTO_DT'].dt.strftime('%Y-%m-%d')
    df_dedup = df_dedup.sort_values(['DATA_VENCIMENTO_DT', 'EMPRESA']).reset_index(drop=True)

    return df_dedup

def generate_html_dashboard(df, output_file):
    print("Preparando dados para o Dashboard Interativo...")
    
    # Extrair listas únicas para os filtros
    empresas = sorted(df['EMPRESA'].unique().tolist(), key=lambda x: int(x) if x.isdigit() else 999999)
    especies = sorted(df['ESPECIE'].unique().tolist())

    opcoes_empresa_html = '<option value="todas">🏢 Todas as Empresas</option>\n'
    for emp in empresas:
        opcoes_empresa_html += f'<option value="{emp}">Empresa {emp}</option>\n'

    opcoes_especie_html = '<option value="todos">📑 Todos os Tipos de Título (Geral)</option>\n'
    for esp in especies:
        opcoes_especie_html += f'<option value="{esp}">Espécie: {esp}</option>\n'

    # Exportar registros limpos em JSON
    cols_json = ['EMPRESA', 'SEQ_TITULO', 'TITULO', 'ESPECIE', 'FORNECEDOR', 'DATA_FORMATADA', 'DATA_ISO', 'VALOR_NOMINAL_TITULO', 'VALOR_PAGO_TITULO', 'SALDO_DEVEDOR_TITULO']
    json_data = df[cols_json].to_json(orient='records', force_ascii=False)

    html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Dashboard Executivo - Contas a Pagar por Empresa e Espécie</title>
    <!-- Fonte Moderna -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <!-- Plotly via CDN -->
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <style>
        :root {{
            --bg-main: #0d0f12;
            --bg-card: #161a22;
            --bg-filter: #1c212c;
            --primary: #00f2fe;
            --secondary: #4facfe;
            --success: #00e676;
            --accent: #ff9800;
            --text: #e0e0e0;
            --text-muted: #8c95a6;
            --border: #2a3142;
        }}
        body {{ 
            background-color: var(--bg-main); 
            color: var(--text); 
            font-family: 'Inter', sans-serif; 
            margin: 0; 
            padding: 25px; 
            box-sizing: border-box;
        }}
        .header {{ 
            text-align: center; 
            padding: 35px 20px; 
            background: linear-gradient(135deg, #181d28 0%, #222b3c 100%); 
            border-radius: 16px; 
            margin-bottom: 25px; 
            border: 1px solid var(--border);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            position: relative;
            overflow: hidden;
        }}
        .header::after {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, var(--primary), var(--success), var(--accent));
        }}
        .header h1 {{ margin: 0; color: white; letter-spacing: 1px; font-weight: 800; font-size: 32px; }}
        .header p {{ color: var(--text-muted); margin-top: 10px; font-size: 16px; font-weight: 400; }}
        
        /* Cards de KPI */
        .kpi-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }}
        .kpi-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            transition: transform 0.3s ease, border-color 0.3s ease;
        }}
        .kpi-card:hover {{
            transform: translateY(-4px);
            border-color: var(--secondary);
        }}
        .kpi-title {{ font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
        .kpi-value {{ font-size: 26px; font-weight: 800; color: white; margin: 0; }}
        .kpi-value.destaque {{ color: var(--primary); text-shadow: 0 0 15px rgba(0,242,254,0.3); }}
        .kpi-value.pago {{ color: var(--success); text-shadow: 0 0 15px rgba(0,230,118,0.3); }}
        .kpi-value.saldo {{ color: var(--accent); text-shadow: 0 0 15px rgba(255,152,0,0.3); }}
        
        /* Barra de Filtros */
        .filtros-container {{ 
            display: flex; 
            justify-content: center; 
            gap: 20px; 
            align-items: center; 
            margin-bottom: 25px; 
            flex-wrap: wrap; 
            background: var(--bg-filter); 
            padding: 18px 25px; 
            border-radius: 14px; 
            border: 1px solid var(--border); 
            box-shadow: 0 4px 20px rgba(0,0,0,0.4); 
        }}
        
        .dropdown-select {{ 
            background: #11141a; 
            color: white; 
            padding: 12px 20px; 
            border: 1px solid var(--border); 
            border-radius: 30px; 
            font-size: 14px; 
            font-weight: 600;
            font-family: 'Inter', sans-serif; 
            cursor: pointer; 
            outline: none; 
            transition: all 0.3s;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            min-width: 220px;
        }}
        .dropdown-select:focus, .dropdown-select:hover {{ border-color: var(--primary); box-shadow: 0 0 12px rgba(0,242,254,0.3); }}
        
        .date-filter {{ display: flex; align-items: center; gap: 10px; background: #11141a; padding: 10px 20px; border-radius: 30px; border: 1px solid var(--border); box-shadow: 0 2px 8px rgba(0,0,0,0.2); }}
        .date-filter label {{ font-size: 13px; font-weight: 600; color: var(--secondary); text-transform: uppercase; }}
        .date-filter input {{ background: transparent; border: none; color: white; font-family: 'Inter', sans-serif; font-size: 14px; outline: none; cursor: pointer; }}
        .date-filter input::-webkit-calendar-picker-indicator {{ filter: invert(1); cursor: pointer; }}
        .btn-clear {{ background: transparent; border: 1px solid #666; color: #888; border-radius: 50%; width: 24px; height: 24px; display: flex; justify-content: center; align-items: center; cursor: pointer; transition: 0.3s; font-weight: bold; padding: 0; }}
        .btn-clear:hover {{ background: #ff4d4d; color: white; border-color: #ff4d4d; }}
        
        /* Gráfico */
        .chart-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.4);
        }}
        .btn-action {{
            background: #11141a;
            border: 1px solid var(--border);
            color: var(--text);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .btn-action:hover {{
            border-color: var(--primary);
            color: white;
            box-shadow: 0 0 10px rgba(0,242,254,0.3);
        }}
        
        /* Tabela */
        .table-container {{ 
            background: var(--bg-card); 
            border: 1px solid var(--border); 
            border-radius: 16px; 
            padding: 25px; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.4); 
        }}
        .table-container h3 {{ color: var(--primary); margin: 0 0 20px 0; font-size: 18px; font-weight: 800; border-bottom: 1px solid var(--border); padding-bottom: 12px; }}
        .table-responsive {{ overflow-x: auto; max-height: 600px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 5px; }}
        th, td {{ padding: 14px 16px; text-align: left; border-bottom: 1px solid var(--border); font-size: 13px; }}
        th {{ background-color: #11141a; color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.5px; position: sticky; top: 0; z-index: 10; }}
        tr:hover {{ background-color: rgba(0, 242, 254, 0.05); }}
        .tr-total {{ background-color: #11141a !important; font-weight: 800; color: var(--primary); font-size: 14px; border-top: 2px solid var(--primary); }}
        .tr-total td {{ border-bottom: none; }}
        .tag-especie {{ background: rgba(79, 172, 254, 0.15); color: var(--secondary); padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 11px; display: inline-block; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Dashboard Executivo - Contas a Pagar</h1>
        <p>Visão Analítica por Tipo de Título (Espécie), Empresa e Cronologia de Vencimentos</p>
    </div>

    <!-- KPIs Executivos Reestruturados -->
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">Valor Nominal Total</div>
            <div id="kpiValorNominal" class="kpi-value destaque">R$ 0,00</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Total Já Pago</div>
            <div id="kpiValorPago" class="kpi-value pago">R$ 0,00</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Total Saldo Devedor</div>
            <div id="kpiSaldoDevedor" class="kpi-value saldo">R$ 0,00</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Quantidade de Títulos Únicos</div>
            <div id="kpiQtd" class="kpi-value">0</div>
        </div>
    </div>

    <!-- Filtros -->
    <div class="filtros-container">
        <select id="filtroEmpresa" class="dropdown-select" onchange="renderAll()">
            {opcoes_empresa_html}
        </select>
        
        <select id="filtroEspecie" class="dropdown-select" onchange="renderAll()">
            {opcoes_especie_html}
        </select>
        
        <div class="date-filter">
            <label>Período:</label>
            <input type="date" id="filtroDataInicio" onchange="renderAll()" title="Data Inicial">
            <span style="color:var(--secondary); font-weight:600; font-size:13px;">até</span>
            <input type="date" id="filtroDataFim" onchange="renderAll()" title="Data Final">
            <button class="btn-clear" onclick="clearData()" title="Limpar Período">X</button>
        </div>
    </div>
    
    <!-- Gráfico -->
    <div class="chart-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-wrap: wrap; gap: 15px; border-bottom: 1px solid var(--border); padding-bottom: 12px;">
            <div id="chartHeaderTitle" style="font-weight: 800; font-size: 18px; color: white;">Evolução Diária de Vencimentos por Espécie (Valor Nominal)</div>
            <div id="chartLegendControls" style="display: flex; gap: 10px; align-items: center;">
                <span style="font-size: 12px; color: var(--text-muted); font-weight: 600;">LEGENDA:</span>
                <button class="btn-action" onclick="marcarTodos()">✅ Marcar Todos</button>
                <button class="btn-action" onclick="desmarcarTodos()">❌ Desmarcar Todos</button>
            </div>
        </div>
        <div id="plotlyChart" style="height: 480px; width: 100%;"></div>
    </div>

    <!-- Tabela Detalhada -->
    <div class="table-container">
        <h3 id="tableTitle">Detalhamento dos Títulos a Pagar</h3>
        <div class="table-responsive">
            <table id="tableRegistros">
                <thead>
                    <tr>
                        <th>Empresa</th>
                        <th>Vencimento</th>
                        <th>Espécie</th>
                        <th>Título</th>
                        <th>Fornecedor</th>
                        <th style="text-align: right;">Valor Nominal</th>
                        <th style="text-align: right;">Valor Pago</th>
                        <th style="text-align: right;">Saldo Devedor</th>
                    </tr>
                </thead>
                <tbody id="tableBody"></tbody>
            </table>
        </div>
    </div>

    <script>
    const allData = {json_data};
    const paletaCores = [
        '#00f2fe', '#4facfe', '#ff9800', '#00e676', '#e91e63', '#9c27b0', '#00bcd4', 
        '#ffeb3b', '#795548', '#607d8b', '#f44336', '#3f51b5', '#8bc34a', '#ff5722',
        '#009688', '#c2185b', '#512da8', '#1976d2', '#388e3c', '#fbc02d', '#e64a19'
    ];
    
    // Mapeamento de cor fixa por Espécie para consistência visual
    const mapCores = {{}};
    const especiesUnicas = [...new Set(allData.map(d => d.ESPECIE))].sort();
    especiesUnicas.forEach((esp, idx) => {{
        mapCores[esp] = paletaCores[idx % paletaCores.length];
    }});

    function clearData() {{
        document.getElementById('filtroDataInicio').value = '';
        document.getElementById('filtroDataFim').value = '';
        renderAll();
    }}

    function getFilteredData() {{
        const emp = document.getElementById('filtroEmpresa').value;
        const esp = document.getElementById('filtroEspecie').value;
        const dtIni = document.getElementById('filtroDataInicio').value;
        const dtFim = document.getElementById('filtroDataFim').value;

        return allData.filter(d => {{
            if (emp !== 'todas' && d.EMPRESA !== emp) return false;
            if (esp !== 'todos' && d.ESPECIE !== esp) return false;
            if (dtIni && d.DATA_ISO < dtIni) return false;
            if (dtFim && d.DATA_ISO > dtFim) return false;
            return true;
        }});
    }}

    function formatCurrency(val) {{
        return "R$ " + Number(val || 0).toFixed(2).replace('.', ',').replace(/(\\d)(?=(\\d{{3}})+(?!\\d))/g, '$1.');
    }}

    function renderKPIs(data) {{
        let totNominal = 0;
        let totPago = 0;
        let totSaldo = 0;
        let qtdTitulos = data.length;

        data.forEach(d => {{
            totNominal += (d.VALOR_NOMINAL_TITULO || 0);
            totPago += (d.VALOR_PAGO_TITULO || 0);
            totSaldo += (d.SALDO_DEVEDOR_TITULO || 0);
        }});

        document.getElementById('kpiValorNominal').innerText = formatCurrency(totNominal);
        document.getElementById('kpiValorPago').innerText = formatCurrency(totPago);
        document.getElementById('kpiSaldoDevedor').innerText = formatCurrency(totSaldo);
        document.getElementById('kpiQtd').innerText = qtdTitulos.toLocaleString('pt-BR');
    }}

    function renderChart(data) {{
        const esp = document.getElementById('filtroEspecie').value;
        const titleEl = document.getElementById('chartHeaderTitle');
        if (titleEl) {{
            titleEl.innerText = (esp === 'todos') ? 'Evolução Diária de Vencimentos por Espécie (Valor Nominal)' : `Evolução Diária de Vencimentos - Espécie: ${{esp}}`;
        }}
        const controlsEl = document.getElementById('chartLegendControls');
        if (controlsEl) {{
            controlsEl.style.display = (esp === 'todos') ? 'flex' : 'none';
        }}
        
        if (data.length === 0) {{
            Plotly.newPlot('plotlyChart', [], {{
                title: 'Sem dados para os filtros selecionados',
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: {{ family: 'Inter', color: '#8c95a6' }}
            }});
            return;
        }}

        const datasUnicas = [...new Set(data.map(d => d.DATA_ISO))].sort();
        const dataFormattedMap = {{}};
        data.forEach(d => {{ dataFormattedMap[d.DATA_ISO] = d.DATA_FORMATADA; }});
        const xLabels = datasUnicas.map(iso => dataFormattedMap[iso]);

        const traces = [];
        const visibleEspecies = [...new Set(data.map(d => d.ESPECIE))].sort();

        visibleEspecies.forEach(espNome => {{
            const yValues = datasUnicas.map(isoDate => {{
                const items = data.filter(d => d.DATA_ISO === isoDate && d.ESPECIE === espNome);
                return items.reduce((sum, d) => sum + (d.VALOR_NOMINAL_TITULO || 0), 0);
            }});

            traces.push({{
                x: xLabels,
                y: yValues,
                name: espNome,
                type: 'bar',
                marker: {{
                    color: mapCores[espNome] || '#4facfe',
                    line: {{ color: 'rgba(255,255,255,0.1)', width: 1 }}
                }},
                hovertemplate: `<b>${{espNome}}</b><br>Data: %{{x}}<br>Valor Nominal: R$ %{{y:,.2f}}<extra></extra>`
            }});
        }});

        const layout = {{
            barmode: 'stack',
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {{ family: 'Inter', color: '#e0e0e0', size: 12 }},
            margin: {{ l: 80, r: 30, t: 20, b: 80 }},
            xaxis: {{
                tickangle: -45,
                gridcolor: '#2a3142',
                zerolinecolor: '#2a3142',
                tickfont: {{ size: 11 }}
            }},
            yaxis: {{
                gridcolor: '#2a3142',
                zerolinecolor: '#2a3142',
                tickprefix: 'R$ ',
                tickformat: ',.2f'
            }},
            legend: {{
                orientation: 'h',
                yanchor: 'bottom',
                y: -0.35,
                xanchor: 'center',
                x: 0.5,
                font: {{ size: 11, color: '#e0e0e0' }}
            }}
        }};

        const config = {{ responsive: true, displayModeBar: false }};
        Plotly.newPlot('plotlyChart', traces, layout, config).then(() => {{
            const chartDiv = document.getElementById('plotlyChart');
            // Sincronização em tempo real da legenda do gráfico com os KPIs e Tabela
            chartDiv.on('plotly_restyle', () => {{
                updateVisibleDataFromChart();
            }});
        }});
    }}

    function updateVisibleDataFromChart() {{
        const chartDiv = document.getElementById('plotlyChart');
        if (!chartDiv || !chartDiv.data) return;

        // Identifica quais espécies estão ativas/visíveis no gráfico
        const visibleEspecies = new Set();
        chartDiv.data.forEach(trace => {{
            if (trace.visible === true || trace.visible === undefined) {{
                visibleEspecies.add(trace.name);
            }}
        }});

        const baseFiltered = getFilteredData();
        const activeData = baseFiltered.filter(d => visibleEspecies.has(d.ESPECIE));

        // Atualiza os KPIs e a Tabela em tempo real com base no que está visível!
        renderKPIs(activeData);
        renderTable(activeData);
    }}

    function marcarTodos() {{
        Plotly.restyle('plotlyChart', {{ visible: true }}).then(() => {{
            updateVisibleDataFromChart();
        }});
    }}

    function desmarcarTodos() {{
        Plotly.restyle('plotlyChart', {{ visible: 'legendonly' }}).then(() => {{
            updateVisibleDataFromChart();
        }});
    }}

    function renderTable(data) {{
        const tbody = document.getElementById('tableBody');
        tbody.innerHTML = '';

        let totNominal = 0;
        let totPago = 0;
        let totSaldo = 0;

        // Limitar a exibição das primeiras 200 linhas para máxima performance fluida no navegador
        const maxRows = 200;
        const displayData = data.slice(0, maxRows);

        displayData.forEach(d => {{
            totNominal += (d.VALOR_NOMINAL_TITULO || 0);
            totPago += (d.VALOR_PAGO_TITULO || 0);
            totSaldo += (d.SALDO_DEVEDOR_TITULO || 0);

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><b>Loja ${{d.EMPRESA}}</b></td>
                <td>${{d.DATA_FORMATADA}}</td>
                <td><span class="tag-especie">${{d.ESPECIE}}</span></td>
                <td>${{d.TITULO}}</td>
                <td>${{d.FORNECEDOR}}</td>
                <td style="text-align: right; font-weight: 600;">${{formatCurrency(d.VALOR_NOMINAL_TITULO)}}</td>
                <td style="text-align: right; color: var(--success);">${{formatCurrency(d.VALOR_PAGO_TITULO)}}</td>
                <td style="text-align: right; font-weight: bold; color: var(--accent);">${{formatCurrency(d.SALDO_DEVEDOR_TITULO)}}</td>
            `;
            tbody.appendChild(tr);
        }});

        // Linha de Totalizador
        const totalNominalGeral = data.reduce((sum, d) => sum + (d.VALOR_NOMINAL_TITULO || 0), 0);
        const totalPagoGeral = data.reduce((sum, d) => sum + (d.VALOR_PAGO_TITULO || 0), 0);
        const totalSaldoGeral = data.reduce((sum, d) => sum + (d.SALDO_DEVEDOR_TITULO || 0), 0);

        const trTotal = document.createElement('tr');
        trTotal.className = 'tr-total';
        trTotal.innerHTML = `
            <td colspan="5">TOTAL GERAL (${{data.length.toLocaleString('pt-BR')}} Títulos)</td>
            <td style="text-align: right;">${{formatCurrency(totalNominalGeral)}}</td>
            <td style="text-align: right; color: var(--success);">${{formatCurrency(totalPagoGeral)}}</td>
            <td style="text-align: right; color: var(--accent);">${{formatCurrency(totalSaldoGeral)}}</td>
        `;
        tbody.appendChild(trTotal);
    }}

    function renderAll() {{
        const filtered = getFilteredData();
        renderKPIs(filtered);
        renderChart(filtered);
        renderTable(filtered);
    }}

    // Inicialização
    document.addEventListener('DOMContentLoaded', () => {{
        renderAll();
    }});
    </script>
</body>
</html>
"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)
    print(f"Dashboard interativo salvo com sucesso em: {output_file}")

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, 'a_pagar_empresa.txt')
    output_html = os.path.join(current_dir, 'dashboard_titulos_a_pagar.html')

    if not os.path.exists(input_file):
        print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
        sys.exit(1)

    df = load_and_clean_data(input_file)
    generate_html_dashboard(df, output_html)

if __name__ == '__main__':
    main()
