import pandas as pd
import plotly.express as px
import os
import sys
import re

def parse_br_currency(x):
    x = str(x).strip()
    if ',' in x and '.' in x:
        x = x.replace('.', '').replace(',', '.')
    elif ',' in x:
        x = x.replace(',', '.')
    try:
        return float(x)
    except:
        return 0.0

def expand_installments(df):
    if 'DATA_PREV_ENTREGA' in df.columns and 'DATA_EMISSAO' in df.columns:
        dt_prev = pd.to_datetime(df['DATA_PREV_ENTREGA'], format='%d/%m/%Y', errors='coerce')
        dt_emi = pd.to_datetime(df['DATA_EMISSAO'], format='%d/%m/%Y', errors='coerce')
        base_dates = dt_prev.fillna(dt_emi)
    else:
        base_dates = pd.Series(pd.NaT, index=df.index)

    new_rows = []
    df = df.reset_index(drop=True)
    base_dates = base_dates.reset_index(drop=True)
    
    for i, row in df.iterrows():
        is_projecao = str(row.get('ORIGEM', '')).startswith('2')
        prazo_str = str(row.get('PRAZO_PAGAMENTO_DIAS', '')).strip()
        
        if is_projecao and ('/' in prazo_str or ',' in prazo_str or '-' in prazo_str):
            prazos = re.findall(r'\d+', prazo_str)
            if len(prazos) > 1:
                n = len(prazos)
                val_parcela = row.get('VALOR_PROJETADO', 0) / n
                base_dt = base_dates.iloc[i]
                
                for idx, prazo in enumerate(prazos):
                    new_row = row.copy()
                    new_row['VALOR_PROJETADO'] = val_parcela
                    if 'VALOR_NOMINAL' in new_row:
                        new_row['VALOR_NOMINAL'] = row.get('VALOR_NOMINAL', 0) / n
                    if 'VALOR_PAGO' in new_row:
                        new_row['VALOR_PAGO'] = row.get('VALOR_PAGO', 0) / n
                    new_row['PARCELA'] = f"{idx + 1}/{n}"
                    
                    if pd.notnull(base_dt):
                        new_dt = base_dt + pd.Timedelta(days=int(prazo))
                        new_row['DATA_VENCIMENTO_DT'] = new_dt
                        new_row['DATA_VENCIMENTO'] = new_dt.strftime('%d/%m/%Y')
                        
                    new_rows.append(new_row)
                continue
                
        new_rows.append(row)
        
    return pd.DataFrame(new_rows)

def load_data(input_file):
    print("Lendo o arquivo de dados...")
    encodings = ['utf-8', 'latin1', 'cp1252', 'utf-16']
    separators = [';', '\t', ',']
    
    df = None
    for enc in encodings:
        for sep in separators:
            try:
                temp_df = pd.read_csv(input_file, sep=sep, encoding=enc)
                if len(temp_df.columns) > 5:
                    df = temp_df
                    break
            except Exception:
                continue
        if df is not None:
            break
            
    if df is None or len(df.columns) < 5:
        print("Erro ao ler o arquivo. Verifique se o formato está correto (tabulado ou ponto-e-vírgula).")
        sys.exit(1)

    print("Processando valores e datas...")
    if 'VALOR_PROJETADO' in df.columns:
        df['VALOR_PROJETADO'] = df['VALOR_PROJETADO'].apply(parse_br_currency)
    if 'VALOR_NOMINAL' in df.columns:
        df['VALOR_NOMINAL'] = df['VALOR_NOMINAL'].apply(parse_br_currency)
    else:
        df['VALOR_NOMINAL'] = df['VALOR_PROJETADO']
    if 'VALOR_PAGO' in df.columns:
        df['VALOR_PAGO'] = df['VALOR_PAGO'].apply(parse_br_currency)
    else:
        df['VALOR_PAGO'] = 0.0

    if 'DATA_VENCIMENTO' in df.columns:
        df['DATA_VENCIMENTO_DT'] = pd.to_datetime(df['DATA_VENCIMENTO'], format='%d/%m/%Y', errors='coerce')
    else:
        df['DATA_VENCIMENTO_DT'] = pd.NaT

    df = expand_installments(df)

    # Preencher comprador vazio
    if 'COMPRADOR' in df.columns:
        df['COMPRADOR'] = df['COMPRADOR'].fillna('SEM COMPRADOR')
    else:
        df['COMPRADOR'] = 'GERAL'

    return df

def compilar_visao(nome_visao, curr_df, id_visao, is_single_comprador=False, is_todos_compradores=False):
    if curr_df.empty:
        return f"<div style='text-align:center; padding: 50px; color: #888;'><h3>Não há dados para este filtro.</h3></div>", "", "Resumo"

    dias_semana = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']

    # Agrega por Data e Origem
    df_chart = curr_df.groupby(['DATA_VENCIMENTO_DT', 'ORIGEM'], as_index=False)[['VALOR_PROJETADO', 'VALOR_NOMINAL']].sum()
    df_chart = df_chart.sort_values('DATA_VENCIMENTO_DT')
    
    # Calcula Total do Dia e Formatação para Tooltip
    df_totais = df_chart.groupby('DATA_VENCIMENTO_DT', as_index=False)[['VALOR_PROJETADO', 'VALOR_NOMINAL']].sum()
    df_totais = df_totais.rename(columns={'VALOR_PROJETADO': 'TOTAL_DIA', 'VALOR_NOMINAL': 'TOTAL_DIA_NOMINAL'})
    df_chart = pd.merge(df_chart, df_totais, on='DATA_VENCIMENTO_DT')
    
    df_chart['Data Formatada'] = df_chart['DATA_VENCIMENTO_DT'].apply(lambda x: f"{x.strftime('%d/%m/%Y')} ({dias_semana[x.weekday()]})" if pd.notnull(x) else "Sem Data")
    df_chart['Valor Formatado'] = df_chart['VALOR_PROJETADO'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    df_chart['Valor Nominal Formatado'] = df_chart['VALOR_NOMINAL'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    df_chart['Total Formatado'] = df_chart['TOTAL_DIA'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    df_chart['Total Nominal Formatado'] = df_chart['TOTAL_DIA_NOMINAL'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    # Mapeia os nomes limpos para a legenda
    df_chart['Origem_Nome'] = df_chart['ORIGEM'].map({'1-TITULO_REAL': 'Real', '2-PROJECAO_PEDIDO': 'Projetado'})
    df_chart['Origem_Nome'] = df_chart['Origem_Nome'].fillna('Outros')

    fig = px.bar(
        df_chart, 
        x='DATA_VENCIMENTO_DT', 
        y='VALOR_PROJETADO', 
        color='Origem_Nome',
        color_discrete_map={'Real': '#4facfe', 'Projetado': '#ff9800'},
        custom_data=['Data Formatada', 'Valor Formatado', 'Valor Nominal Formatado', 'Total Formatado', 'Total Nominal Formatado'],
        title=f"Evolução Diária - {nome_visao}",
        template='plotly_dark',
        barmode='stack'
    )
    
    fig.update_traces(
        hovertemplate="<b>Data:</b> %{customdata[0]}<br>" +
                      "<b>Tipo:</b> %{data.name}<br>" +
                      "<b>Valor a Pagar:</b> %{customdata[1]}<br>" +
                      "<b>Valor Nominal:</b> %{customdata[2]}<br>" +
                      "<b>TOTAL DO DIA (a Pagar):</b> %{customdata[3]}<br>" +
                      "<b>TOTAL DO DIA (Nominal):</b> %{customdata[4]}<extra></extra>",
        marker_line_width=0
    )
    
    fig.update_layout(
        xaxis_title="Data de Vencimento",
        yaxis_title="Valor a Pagar (R$)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter", size=14, color="#e0e0e0"),
        margin=dict(l=40, r=40, t=60, b=40),
        legend_title_text='',
        showlegend=True
    )
    # Configurar eixo X para datas verticais sob cada coluna (intervalo de 2 dias)
    fig.update_xaxes(
        tickformat="%d/%m/%Y",
        tickangle=-90,
        dtick=172800000, # 172800000 ms = 2 dias (intercala dia sim, dia não)
        showgrid=False
    )
    
    grafico_html = fig.to_html(full_html=False, include_plotlyjs=False)
    
    return grafico_html

def clean_id(x):
    return re.sub(r'[^a-zA-Z0-9]', '', str(x)).lower()

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, 'a_pagar.txt')
    output_html = os.path.join(current_dir, 'Dashboard_Compras.html')

    if not os.path.exists(input_file):
        print(f"Erro: O arquivo '{input_file}' não foi encontrado.")
        sys.exit(1)
    
    df = load_data(input_file)
    
    print("Compilando visualizações (isso pode levar alguns segundos)...")
    
    origens = [
        {"id": "todos", "nome": "Todos (Real + Projetado)", "df": df},
        {"id": "real", "nome": "Somente Real (Faturado)", "df": df[df['ORIGEM'] == '1-TITULO_REAL']},
        {"id": "projetado", "nome": "Somente Projetado (Pedidos)", "df": df[df['ORIGEM'] == '2-PROJECAO_PEDIDO']}
    ]
    
    compradores = sorted(df['COMPRADOR'].unique().tolist())
    
    opcoes_comprador_html = '<option value="todos">Filtro: Todos os Compradores</option>\n'
    for comp in compradores:
        opcoes_comprador_html += f'<option value="{clean_id(comp)}">Comprador: {comp}</option>\n'
    
    # Preparar JSON com os detalhes linha a linha
    if 'EMPRESA' not in df.columns: df['EMPRESA'] = '-'
    if 'STATUS_PEDIDO' not in df.columns: df['STATUS_PEDIDO'] = '-'
    if 'VALOR_NOMINAL' not in df.columns: df['VALOR_NOMINAL'] = df['VALOR_PROJETADO']
    
    df_details = df[['ORIGEM', 'TITULO', 'FORNECEDOR', 'COMPRADOR', 'DATA_VENCIMENTO_DT', 'PARCELA', 'VALOR_PROJETADO', 'VALOR_NOMINAL', 'EMPRESA', 'STATUS_PEDIDO']].copy()
    df_details['TITULO'] = df_details['TITULO'].fillna('-')
    df_details['FORNECEDOR'] = df_details['FORNECEDOR'].fillna('-')
    df_details['COMPRADOR_ID'] = df_details['COMPRADOR'].apply(clean_id)
    df_details['PARCELA'] = df_details['PARCELA'].fillna('-')
    df_details['EMPRESA'] = df_details['EMPRESA'].fillna('-')
    df_details['STATUS_PEDIDO'] = df_details['STATUS_PEDIDO'].fillna('-')
    df_valid = df_details.dropna(subset=['DATA_VENCIMENTO_DT']).copy()
    df_valid['DATA_FORMATADA'] = df_valid['DATA_VENCIMENTO_DT'].dt.strftime('%d/%m/%Y')
    df_valid['DATA_ISO'] = df_valid['DATA_VENCIMENTO_DT'].dt.strftime('%Y-%m-%d')
    df_valid['VALOR_FORMATADO'] = df_valid['VALOR_PROJETADO'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    df_valid['VALOR_NOMINAL_FORMATADO'] = df_valid['VALOR_NOMINAL'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    json_data = df_valid[['ORIGEM', 'TITULO', 'FORNECEDOR', 'COMPRADOR', 'COMPRADOR_ID', 'DATA_FORMATADA', 'DATA_ISO', 'PARCELA', 'VALOR_PROJETADO', 'VALOR_FORMATADO', 'VALOR_NOMINAL', 'VALOR_NOMINAL_FORMATADO', 'EMPRESA', 'STATUS_PEDIDO']].to_json(orient='records', force_ascii=False)
    
    visoes_html = ""
    botoes_html = ""
    
    for i, orig in enumerate(origens):
        active_btn = "active" if i == 0 else ""
        botoes_html += f'<button class="btn {active_btn}" onclick="changeOrigem(\'{orig["id"]}\', this)">{orig["nome"]}</button>\n'
        
        # Visão: Todos os Compradores (para esta Origem)
        gf = compilar_visao(orig["nome"], orig["df"], f'{orig["id"]}_todos', is_todos_compradores=True)
        display_css = "block" if i == 0 else "none"
        visoes_html += f'<div id="view_{orig["id"]}_todos" class="sub-view" style="display:{display_css};">\n{gf}\n</div>\n'
        
        # Visões Específicas: Um por um dos Compradores (para esta Origem)
        for comp in compradores:
            df_comp = orig["df"][orig["df"]['COMPRADOR'] == comp]
            cid = clean_id(comp)
            gf = compilar_visao(f"{orig['nome']} - {comp}", df_comp, f'{orig["id"]}_{cid}', is_single_comprador=True)
            visoes_html += f'<div id="view_{orig["id"]}_{cid}" class="sub-view" style="display:none;">\n{gf}\n</div>\n'
        
    html_template = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Dashboard - Compras a Pagar</title>
    <!-- Fonte Moderna -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <!-- Importação Mestra do Plotly -->
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <style>
        body {{ background-color: #121212; color: #e0e0e0; font-family: 'Inter', sans-serif; margin: 0; padding: 20px; }}
        .header {{ text-align: center; padding: 30px; background: linear-gradient(135deg, #1f1c2c 0%, #928DAB 100%); border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
        .header h1 {{ margin: 0; color: white; letter-spacing: 1px; font-weight: 800; }}
        .header p {{ color: #ddd; margin-top: 10px; font-size: 16px; }}
        
        .filtros-container {{ display: flex; justify-content: center; gap: 20px; align-items: center; margin-bottom: 25px; flex-wrap: wrap; background: #1a1a1a; padding: 15px; border-radius: 12px; border: 1px solid #333; box-shadow: inset 0 2px 10px rgba(0,0,0,0.5); }}
        
        .btn-group {{ display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; }}
        .btn {{ 
            background: rgba(255, 255, 255, 0.05); 
            border: 1px solid rgba(255, 255, 255, 0.1); 
            color: white; 
            padding: 12px 25px; 
            border-radius: 30px; 
            cursor: pointer; 
            font-size: 15px; 
            font-weight: 600; 
            transition: all 0.3s ease; 
        }}
        .btn:hover, .btn.active {{ 
            background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%); 
            border-color: transparent; 
            box-shadow: 0 0 15px rgba(79, 172, 254, 0.4); 
            transform: translateY(-2px); 
        }}
        
        .dropdown-comprador {{ 
            background: #2c2c2c; 
            color: white; 
            padding: 12px 20px; 
            border: 1px solid #4facfe; 
            border-radius: 30px; 
            font-size: 15px; 
            font-weight: 600;
            font-family: 'Inter', sans-serif; 
            cursor: pointer; 
            outline: none; 
            transition: all 0.3s;
            box-shadow: 0 0 10px rgba(79, 172, 254, 0.2);
        }}
        .dropdown-comprador:focus {{ box-shadow: 0 0 15px rgba(79, 172, 254, 0.6); }}
        
        .sub-view {{ 
            background: #1e1e1e; 
            padding: 25px; 
            border-radius: 12px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.2); 
            animation: fadeIn 0.4s ease-in-out; 
        }}
        
        .table-container {{ margin-top: 40px; padding: 0 20px; }}
        .table-container h3 {{ color: #4facfe; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 5px; border-radius: 8px; overflow: hidden; }}
        th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #333; }}
        th {{ background-color: #2c2c2c; color: #fff; font-weight: 600; text-transform: uppercase; font-size: 14px; letter-spacing: 0.5px; }}
        tr:hover {{ background-color: #2a2a2a; }}
        tr:last-child td {{ border-bottom: none; font-weight: 800; color: #00f2fe; font-size: 16px; background-color: #1a1a1a; }}
        .date-filter {{ display: flex; align-items: center; gap: 10px; background: #2c2c2c; padding: 10px 20px; border-radius: 30px; border: 1px solid #4facfe; box-shadow: 0 0 10px rgba(79, 172, 254, 0.2); }}
        .date-filter label {{ font-size: 14px; font-weight: 600; color: #4facfe; }}
        .date-filter input {{ background: transparent; border: none; color: white; font-family: 'Inter', sans-serif; font-size: 15px; outline: none; cursor: pointer; }}
        .date-filter input::-webkit-calendar-picker-indicator {{ filter: invert(1); cursor: pointer; }}
        .btn-clear {{ background: transparent; border: 1px solid #888; color: #888; border-radius: 50%; width: 24px; height: 24px; display: flex; justify-content: center; align-items: center; cursor: pointer; transition: 0.3s; font-weight: bold; padding: 0; }}
        .btn-clear:hover {{ background: #ff4d4d; color: white; border-color: #ff4d4d; }}
        
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Fluxo de Caixa de Compras</h1>
        <p>Visão Executiva Interativa por Comprador e Fornecedor</p>
    </div>

    <div class="filtros-container">
        <div class="btn-group">
            {botoes_html}
        </div>
        
        <select id="filtroComprador" class="dropdown-comprador" onchange="changeComprador(this)">
            {opcoes_comprador_html}
        </select>
        
        <div class="date-filter">
            <label>Detalhar Período:</label>
            <input type="date" id="filtroDataInicio" onchange="changeData()" title="Data Inicial (Opcional)">
            <span style="color:#4facfe; font-weight:600; font-size:14px;">até</span>
            <input type="date" id="filtroDataFim" onchange="changeData()" title="Data Final (Opcional)">
            <button class="btn-clear" onclick="clearData()" title="Limpar Período">X</button>
        </div>
    </div>
    
    {visoes_html}

    <div id="resumoDinamicoContainer" class="table-container"></div>
    <div id="detalhesDataContainer" style="display:none; margin-top:20px;"></div>

    <script>
    const contas_detalhes = {json_data};
    let current_origem = 'todos';
    let current_comprador = 'todos';

    function changeOrigem(origem, btnElement) {{
        current_origem = origem;
        var botoes = document.getElementsByClassName("btn");
        for(var i=0; i < botoes.length; i++) {{
            botoes[i].classList.remove("active");
        }}
        btnElement.classList.add("active");
        updateView();
        renderResumo();
        renderDetalhes();
    }}

    function changeComprador(selectObj) {{
        current_comprador = selectObj.value;
        updateView();
        renderResumo();
        renderDetalhes();
    }}

    function updateView() {{
        var target_id = "view_" + current_origem + "_" + current_comprador;
        var abas = document.getElementsByClassName("sub-view");
        for(var i=0; i < abas.length; i++) {{
            abas[i].style.display = (abas[i].id === target_id) ? "block" : "none";
        }}
        
        // TRUQUE DE MESTRE: Força renderização para o Plotly não bugar ao sair do display:none
        window.dispatchEvent(new Event('resize')); 
    }}
    
    function changeData() {{
        renderResumo();
        renderDetalhes();
    }}
    
    function clearData() {{
        document.getElementById('filtroDataInicio').value = '';
        document.getElementById('filtroDataFim').value = '';
        renderResumo();
        renderDetalhes();
    }}

    function renderResumo() {{
        const inicio = document.getElementById('filtroDataInicio').value;
        const fim = document.getElementById('filtroDataFim').value;
        const container = document.getElementById('resumoDinamicoContainer');
        
        let filtrados = contas_detalhes;
        
        if (inicio && fim) {{
            filtrados = filtrados.filter(item => item.DATA_ISO >= inicio && item.DATA_ISO <= fim);
        }} else if (inicio) {{
            filtrados = filtrados.filter(item => item.DATA_ISO === inicio);
        }} else if (fim) {{
            filtrados = filtrados.filter(item => item.DATA_ISO === fim);
        }}
        
        if (current_comprador !== 'todos') {{
            filtrados = filtrados.filter(item => item.COMPRADOR_ID === current_comprador);
        }}
        
        if (current_origem === 'real') {{
            filtrados = filtrados.filter(item => item.ORIGEM === '1-TITULO_REAL');
        }} else if (current_origem === 'projetado') {{
            filtrados = filtrados.filter(item => item.ORIGEM === '2-PROJECAO_PEDIDO');
        }}
        
        let is_single = current_comprador !== 'todos';
        let agrupamento = {{}};
        
        filtrados.forEach(item => {{
            let key = is_single ? item.FORNECEDOR : item.COMPRADOR;
            if (!agrupamento[key]) {{
                agrupamento[key] = {{ real_nom: 0, real_proj: 0, proj_nom: 0, proj_proj: 0, total_nom: 0, total_proj: 0 }};
            }}
            let nom = item.VALOR_NOMINAL || 0;
            let proj = item.VALOR_PROJETADO || 0;
            if (item.ORIGEM === '1-TITULO_REAL') {{
                agrupamento[key].real_nom += nom;
                agrupamento[key].real_proj += proj;
            }} else {{
                agrupamento[key].proj_nom += nom;
                agrupamento[key].proj_proj += proj;
            }}
            agrupamento[key].total_nom += nom;
            agrupamento[key].total_proj += proj;
        }});
        
        let lista = Object.keys(agrupamento).map(k => {{
            return {{
                nome: k,
                real_nom: agrupamento[k].real_nom,
                real_proj: agrupamento[k].real_proj,
                proj_nom: agrupamento[k].proj_nom,
                proj_proj: agrupamento[k].proj_proj,
                total_nom: agrupamento[k].total_nom,
                total_proj: agrupamento[k].total_proj
            }};
        }});
        lista.sort((a, b) => b.total_proj - a.total_proj);
        
        let nomeCompradorText = '';
        if (is_single) {{
            let selectObj = document.getElementById('filtroComprador');
            nomeCompradorText = selectObj.options[selectObj.selectedIndex].text.replace('Comprador: ', '');
        }}
        let titulo = is_single ? `Detalhamento por Fornecedor (Comprador: ${{nomeCompradorText}})` : 'Resumo Geral por Comprador';
        
        let html = `<h3>${{titulo}}</h3>`;
        html += `<table style="width:100%; border-collapse:collapse;">
            <tr>
                <th>${{is_single ? 'Fornecedor' : 'Comprador'}}</th>
                <th style="text-align:right;">Real (Nominal)</th>
                <th style="text-align:right;">Real (a Pagar)</th>
                <th style="text-align:right;">Projetado (Nominal)</th>
                <th style="text-align:right;">Projetado (a Pagar)</th>
                <th style="text-align:right;">Total Nominal</th>
                <th style="text-align:right;">Total a Pagar</th>
            </tr>`;
            
        let totRealNom = 0, totRealProj = 0, totProjNom = 0, totProjProj = 0, totGeralNom = 0, totGeralProj = 0;
        let fmt = val => "R$ " + val.toFixed(2).replace('.', ',').replace(/(\\d)(?=(\\d{{3}})+(?!\\d))/g, '$1.');
        
        lista.forEach(item => {{
            html += `<tr>
                <td>${{item.nome}}</td>
                <td style="text-align:right; color:#bbb;">${{fmt(item.real_nom)}}</td>
                <td style="text-align:right;">${{fmt(item.real_proj)}}</td>
                <td style="text-align:right; color:#bbb;">${{fmt(item.proj_nom)}}</td>
                <td style="text-align:right;">${{fmt(item.proj_proj)}}</td>
                <td style="text-align:right; color:#bbb; font-weight:600;">${{fmt(item.total_nom)}}</td>
                <td style="text-align:right; font-weight:bold; color:#00f2fe;">${{fmt(item.total_proj)}}</td>
            </tr>`;
            totRealNom += item.real_nom;
            totRealProj += item.real_proj;
            totProjNom += item.proj_nom;
            totProjProj += item.proj_proj;
            totGeralNom += item.total_nom;
            totGeralProj += item.total_proj;
        }});
        
        html += `<tr style="background-color: #1a1a1a; font-weight:800; color:#00f2fe; font-size:15px;">
            <td>TOTAL GERAL</td>
            <td style="text-align:right; color:#ddd;">${{fmt(totRealNom)}}</td>
            <td style="text-align:right;">${{fmt(totRealProj)}}</td>
            <td style="text-align:right; color:#ddd;">${{fmt(totProjNom)}}</td>
            <td style="text-align:right;">${{fmt(totProjProj)}}</td>
            <td style="text-align:right; color:#ddd;">${{fmt(totGeralNom)}}</td>
            <td style="text-align:right;">${{fmt(totGeralProj)}}</td>
        </tr></table>`;
        
        container.innerHTML = html;
    }}

    function renderDetalhes() {{
        const inicio = document.getElementById('filtroDataInicio').value;
        const fim = document.getElementById('filtroDataFim').value;
        const container = document.getElementById('detalhesDataContainer');
        
        if (!inicio && !fim) {{
            container.style.display = 'none';
            return;
        }}
        
        let filtrados = contas_detalhes.filter(item => {{
            if (inicio && item.DATA_ISO < inicio) return false;
            if (fim && item.DATA_ISO > fim) return false;
            return true;
        }});
        
        if (current_comprador !== 'todos') {{
            filtrados = filtrados.filter(item => item.COMPRADOR_ID === current_comprador);
        }}
        
        if (current_origem === 'real') {{
            filtrados = filtrados.filter(item => item.ORIGEM === '1-TITULO_REAL');
        }} else if (current_origem === 'projetado') {{
            filtrados = filtrados.filter(item => item.ORIGEM === '2-PROJECAO_PEDIDO');
        }}
        
        if (filtrados.length === 0) {{
            container.innerHTML = `<div class="sub-view"><h3 style="color:#4facfe; margin-top:0;">Detalhes do Período</h3><p>Nenhuma conta a pagar encontrada para este intervalo e filtros selecionados.</p></div>`;
            container.style.display = 'block';
            return;
        }}
        
        let html = `<div class="sub-view">
            <h3 style="color:#4facfe; margin-top:0; border-bottom: 1px solid #333; padding-bottom: 10px;">
                Detalhes do Período
            </h3>
            <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; margin-top:10px;">
                <tr>
                    <th>Data</th>
                    <th>Loja</th>
                    <th>Fornecedor</th>
                    <th>Título/Pedido</th>
                    <th>Comprador</th>
                    <th>Origem</th>
                    <th>Status</th>
                    <th>Parcela</th>
                    <th style="text-align:right;">Valor Nominal</th>
                    <th style="text-align:right;">Valor a Pagar</th>
                </tr>`;
                
        let totalProj = 0;
        let totalNom = 0;
        
        filtrados.forEach(item => {{
            html += `<tr>
                <td style="font-weight:600;">${{item.DATA_FORMATADA}}</td>
                <td>${{item.EMPRESA}}</td>
                <td>${{item.FORNECEDOR}}</td>
                <td>${{item.TITULO}}</td>
                <td>${{item.COMPRADOR}}</td>
                <td>${{item.ORIGEM === '1-TITULO_REAL' ? '<span style="color:#2ecc71;">Faturado</span>' : '<span style="color:#f39c12;">Projetado</span>'}}</td>
                <td>${{item.STATUS_PEDIDO}}</td>
                <td>${{item.PARCELA}}</td>
                <td style="text-align:right; color:#bbb;">${{item.VALOR_NOMINAL_FORMATADO || '-'}}</td>
                <td style="text-align:right; font-weight:bold;">${{item.VALOR_FORMATADO}}</td>
            </tr>`;
            totalProj += (item.VALOR_PROJETADO || 0);
            totalNom += (item.VALOR_NOMINAL || 0);
        }});
        
        let totalProjFmt = "R$ " + totalProj.toFixed(2).replace('.', ',').replace(/(\\d)(?=(\\d{{3}})+(?!\\d))/g, '$1.');
        let totalNomFmt = "R$ " + totalNom.toFixed(2).replace('.', ',').replace(/(\\d)(?=(\\d{{3}})+(?!\\d))/g, '$1.');
        
        html += `<tr style="background-color: #1a1a1a; font-weight:800; color:#00f2fe; font-size:16px;">
            <td colspan="8" style="text-align:right;">TOTAL DO PERÍODO</td>
            <td style="text-align:right; color:#ddd;">${{totalNomFmt}}</td>
            <td style="text-align:right;">${{totalProjFmt}}</td>
        </tr>`;
        
        html += `</table></div></div>`;
        
        container.innerHTML = html;
        container.style.display = 'block';
        
        // Scroll suave para os detalhes apenas se for a segunda data
        if (fim) {{
            container.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
        }}
    }}

    // Renderiza a tabela de resumo inicial ao carregar a página
    window.onload = function() {{
        renderResumo();
    }};
    </script>
</body>
</html>
"""
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Dashboard gerado com sucesso em: {output_html}")

if __name__ == '__main__':
    main()
