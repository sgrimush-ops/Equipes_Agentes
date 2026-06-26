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

    if is_todos_compradores:
        # Agrega por Data e Origem (para separar cores)
        df_chart = curr_df.groupby(['DATA_VENCIMENTO_DT', 'ORIGEM'], as_index=False)['VALOR_PROJETADO'].sum()
        df_chart = df_chart.sort_values('DATA_VENCIMENTO_DT')
        
        # Calcula Total do Dia e Formatação para Tooltip
        df_totais = df_chart.groupby('DATA_VENCIMENTO_DT', as_index=False)['VALOR_PROJETADO'].sum()
        df_totais = df_totais.rename(columns={'VALOR_PROJETADO': 'TOTAL_DIA'})
        df_chart = pd.merge(df_chart, df_totais, on='DATA_VENCIMENTO_DT')
        
        df_chart['Data Formatada'] = df_chart['DATA_VENCIMENTO_DT'].apply(lambda x: f"{x.strftime('%d/%m/%Y')} ({dias_semana[x.weekday()]})" if pd.notnull(x) else "Sem Data")
        df_chart['Valor Formatado'] = df_chart['VALOR_PROJETADO'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        df_chart['Total Formatado'] = df_chart['TOTAL_DIA'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        # Mapeia os nomes limpos para a legenda
        df_chart['Origem_Nome'] = df_chart['ORIGEM'].map({'1-TITULO_REAL': 'Real', '2-PROJECAO_PEDIDO': 'Projetado'})
        df_chart['Origem_Nome'] = df_chart['Origem_Nome'].fillna('Outros')

        fig = px.bar(
            df_chart, 
            x='DATA_VENCIMENTO_DT', 
            y='VALOR_PROJETADO', 
            color='Origem_Nome',
            color_discrete_map={'Real': '#4facfe', 'Projetado': '#ff9800'},
            custom_data=['Data Formatada', 'Valor Formatado', 'Total Formatado'],
            title=f"Evolução Diária - {nome_visao}",
            template='plotly_dark',
            barmode='stack'
        )
        
        fig.update_traces(
            hovertemplate="<b>Data:</b> %{customdata[0]}<br>" +
                          "<b>Tipo:</b> %{data.name}<br>" +
                          "<b>Valor:</b> %{customdata[1]}<br>" +
                          "<b>TOTAL DO DIA:</b> %{customdata[2]}<extra></extra>",
            marker_line_width=0
        )
    else:
        # Gráfico quebrado por comprador
        df_chart = curr_df.groupby(['DATA_VENCIMENTO_DT', 'COMPRADOR'], as_index=False)['VALOR_PROJETADO'].sum()
        df_chart = df_chart.sort_values('DATA_VENCIMENTO_DT')
        
        # Calcula Total do Dia e Formatação para Tooltip
        df_totais = df_chart.groupby('DATA_VENCIMENTO_DT', as_index=False)['VALOR_PROJETADO'].sum()
        df_totais = df_totais.rename(columns={'VALOR_PROJETADO': 'TOTAL_DIA'})
        df_chart = pd.merge(df_chart, df_totais, on='DATA_VENCIMENTO_DT')
        
        df_chart['Data Formatada'] = df_chart['DATA_VENCIMENTO_DT'].apply(lambda x: f"{x.strftime('%d/%m/%Y')} ({dias_semana[x.weekday()]})" if pd.notnull(x) else "Sem Data")
        df_chart['Valor Formatado'] = df_chart['VALOR_PROJETADO'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        df_chart['Total Formatado'] = df_chart['TOTAL_DIA'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        fig = px.bar(
            df_chart, 
            x='DATA_VENCIMENTO_DT', 
            y='VALOR_PROJETADO', 
            color='COMPRADOR',
            custom_data=['Data Formatada', 'Valor Formatado', 'Total Formatado'],
            title=f"Evolução Diária - {nome_visao}",
            template='plotly_dark',
            barmode='stack',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_traces(
            hovertemplate="<b>Data:</b> %{customdata[0]}<br>" +
                          "<b>Comprador:</b> %{data.name}<br>" +
                          "<b>Gasto deste Comprador:</b> %{customdata[1]}<br>" +
                          "<b>TOTAL DO DIA:</b> %{customdata[2]}<extra></extra>",
            marker_line_width=0
        )
    
    fig.update_layout(
        xaxis_title="Data de Vencimento",
        yaxis_title="Valor a Pagar (R$)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter", size=14, color="#e0e0e0"),
        margin=dict(l=40, r=40, t=60, b=40),
        legend_title_text='Comprador' if not (is_single_comprador or is_todos_compradores) else '',
        showlegend=not is_single_comprador and not is_todos_compradores
    )
    
    if is_single_comprador:
        fig.update_layout(showlegend=False)
        
    # Configurar eixo X para traços semanais e datas centralizadas
    min_date = curr_df['DATA_VENCIMENTO_DT'].min()
    max_date = curr_df['DATA_VENCIMENTO_DT'].max()
    if pd.notnull(min_date) and pd.notnull(max_date):
        monday = min_date - pd.Timedelta(days=min_date.weekday())
        
        tickvals = []
        ticktext = []
        
        curr_mon = monday
        while curr_mon <= max_date + pd.Timedelta(days=7):
            # A linha divisória da semana fica no Domingo 12:00 (Borda esquerda da barra de Segunda)
            vline_dt = curr_mon - pd.Timedelta(hours=12)
            fig.add_vline(
                x=vline_dt, 
                line_width=1, 
                line_dash="dash", 
                line_color="rgba(255, 255, 255, 0.2)"
            )
            
            # O texto fica exatamente no centro do período de 7 dias (Quinta-feira 00:00)
            center_dt = vline_dt + pd.Timedelta(days=3.5)
            tickvals.append(center_dt)
            ticktext.append(curr_mon.strftime('%d/%m/%Y'))
            
            curr_mon += pd.Timedelta(days=7)

        fig.update_xaxes(
            tickmode='array',
            tickvals=tickvals,
            ticktext=ticktext,
            tickangle=0,
            showgrid=False # Grade nativa desligada pois usamos add_vline
        )
    
    grafico_html = fig.to_html(full_html=False, include_plotlyjs=False)
    
    # Tabela (Composição Real vs Projetado)
    if is_single_comprador and 'FORNECEDOR' in curr_df.columns:
        col_label = 'FORNECEDOR'
        table_title = f"Detalhamento por Fornecedor (Comprador: {curr_df['COMPRADOR'].iloc[0]})"
    else:
        col_label = 'COMPRADOR'
        table_title = "Resumo Geral por Comprador"

    df_pivot = curr_df.pivot_table(index=col_label, columns='ORIGEM', values='VALOR_PROJETADO', aggfunc='sum', fill_value=0).reset_index()
    
    if '1-TITULO_REAL' not in df_pivot.columns:
        df_pivot['1-TITULO_REAL'] = 0.0
    if '2-PROJECAO_PEDIDO' not in df_pivot.columns:
        df_pivot['2-PROJECAO_PEDIDO'] = 0.0
        
    df_pivot['TOTAL_GERAL'] = df_pivot['1-TITULO_REAL'] + df_pivot['2-PROJECAO_PEDIDO']
    df_pivot = df_pivot.sort_values('TOTAL_GERAL', ascending=False)
    
    total_real = df_pivot['1-TITULO_REAL'].sum()
    total_proj = df_pivot['2-PROJECAO_PEDIDO'].sum()
    total_geral = df_pivot['TOTAL_GERAL'].sum()
    
    df_pivot.loc[len(df_pivot)] = ['TOTAL GERAL', total_real, total_proj, total_geral]
    
    def fmt(x):
        return f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
    df_pivot['Valor Real'] = df_pivot['1-TITULO_REAL'].apply(fmt)
    df_pivot['Valor Projetado'] = df_pivot['2-PROJECAO_PEDIDO'].apply(fmt)
    df_pivot['Total'] = df_pivot['TOTAL_GERAL'].apply(fmt)
    
    df_table = df_pivot[[col_label, 'Valor Real', 'Valor Projetado', 'Total']]
    
    tabela_html = df_table.to_html(index=False, classes='', border=0, justify='left')
    
    return grafico_html, tabela_html, table_title

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
    
    df_details = df[['ORIGEM', 'TITULO', 'FORNECEDOR', 'COMPRADOR', 'DATA_VENCIMENTO_DT', 'PARCELA', 'VALOR_PROJETADO', 'EMPRESA', 'STATUS_PEDIDO']].copy()
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
    json_data = df_valid[['ORIGEM', 'TITULO', 'FORNECEDOR', 'COMPRADOR', 'COMPRADOR_ID', 'DATA_FORMATADA', 'DATA_ISO', 'PARCELA', 'VALOR_PROJETADO', 'VALOR_FORMATADO', 'EMPRESA', 'STATUS_PEDIDO']].to_json(orient='records', force_ascii=False)
    
    visoes_html = ""
    botoes_html = ""
    
    for i, orig in enumerate(origens):
        active_btn = "active" if i == 0 else ""
        botoes_html += f'<button class="btn {active_btn}" onclick="changeOrigem(\'{orig["id"]}\', this)">{orig["nome"]}</button>\n'
        
        # Visão: Todos os Compradores (para esta Origem)
        gf, tb, title = compilar_visao(orig["nome"], orig["df"], f'{orig["id"]}_todos', is_todos_compradores=True)
        display_css = "block" if i == 0 else "none"
        visoes_html += f'<div id="view_{orig["id"]}_todos" class="sub-view" style="display:{display_css};">\n{gf}\n<div class="table-container">\n<h3>{title}</h3>\n{tb}\n</div>\n</div>\n'
        
        # Visões Específicas: Um por um dos Compradores (para esta Origem)
        for comp in compradores:
            df_comp = orig["df"][orig["df"]['COMPRADOR'] == comp]
            cid = clean_id(comp)
            gf, tb, title = compilar_visao(f"{orig['nome']} - {comp}", df_comp, f'{orig["id"]}_{cid}', is_single_comprador=True)
            visoes_html += f'<div id="view_{orig["id"]}_{cid}" class="sub-view" style="display:none;">\n{gf}\n<div class="table-container">\n<h3>{title}</h3>\n{tb}\n</div>\n</div>\n'
        
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
            <label for="filtroData">Detalhar Dia:</label>
            <input type="date" id="filtroData" onchange="changeData()">
            <button class="btn-clear" onclick="clearData()" title="Limpar Data">X</button>
        </div>
    </div>
    
    {visoes_html}

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
        renderDetalhes();
    }}

    function changeComprador(selectObj) {{
        current_comprador = selectObj.value;
        updateView();
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
        renderDetalhes();
    }}
    
    function clearData() {{
        document.getElementById('filtroData').value = '';
        renderDetalhes();
    }}

    function renderDetalhes() {{
        const dataIso = document.getElementById('filtroData').value;
        const container = document.getElementById('detalhesDataContainer');
        
        if (!dataIso) {{
            container.style.display = 'none';
            return;
        }}
        
        let filtrados = contas_detalhes.filter(item => item.DATA_ISO === dataIso);
        
        if (current_comprador !== 'todos') {{
            filtrados = filtrados.filter(item => item.COMPRADOR_ID === current_comprador);
        }}
        
        if (current_origem === 'real') {{
            filtrados = filtrados.filter(item => item.ORIGEM === '1-TITULO_REAL');
        }} else if (current_origem === 'projetado') {{
            filtrados = filtrados.filter(item => item.ORIGEM === '2-PROJECAO_PEDIDO');
        }}
        
        if (filtrados.length === 0) {{
            container.innerHTML = `<div class="sub-view"><h3 style="color:#4facfe; margin-top:0;">Detalhes do Dia ${{dataIso.split('-').reverse().join('/')}}</h3><p>Nenhuma conta a pagar encontrada para esta data e filtros selecionados.</p></div>`;
            container.style.display = 'block';
            return;
        }}
        
        let html = `<div class="sub-view">
            <h3 style="color:#4facfe; margin-top:0; border-bottom: 1px solid #333; padding-bottom: 10px;">
                Detalhes do Dia ${{filtrados[0].DATA_FORMATADA}}
            </h3>
            <div style="overflow-x:auto;">
            <table style="width:100%; border-collapse:collapse; margin-top:10px;">
                <tr>
                    <th>Loja</th>
                    <th>Fornecedor</th>
                    <th>Título/Pedido</th>
                    <th>Comprador</th>
                    <th>Origem</th>
                    <th>Status</th>
                    <th>Parcela</th>
                    <th style="text-align:right;">Valor</th>
                </tr>`;
                
        let total = 0;
        
        filtrados.forEach(item => {{
            html += `<tr>
                <td>${{item.EMPRESA}}</td>
                <td>${{item.FORNECEDOR}}</td>
                <td>${{item.TITULO}}</td>
                <td>${{item.COMPRADOR}}</td>
                <td>${{item.ORIGEM === '1-TITULO_REAL' ? '<span style="color:#2ecc71;">Faturado</span>' : '<span style="color:#f39c12;">Projetado</span>'}}</td>
                <td>${{item.STATUS_PEDIDO}}</td>
                <td>${{item.PARCELA}}</td>
                <td style="text-align:right;">${{item.VALOR_FORMATADO}}</td>
            </tr>`;
            total += item.VALOR_PROJETADO;
        }});
        
        let totalFmt = "R$ " + total.toFixed(2).replace('.', ',').replace(/(\\d)(?=(\\d{{3}})+(?!\\d))/g, '$1.');
        
        html += `<tr style="background-color: #1a1a1a; font-weight:800; color:#00f2fe; font-size:16px;">
            <td colspan="7" style="text-align:right;">TOTAL DO DIA</td>
            <td style="text-align:right;">${{totalFmt}}</td>
        </tr>`;
        
        html += `</table></div></div>`;
        
        container.innerHTML = html;
        container.style.display = 'block';
        
        // Scroll suave para os detalhes
        container.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }}
    </script>
</body>
</html>
"""
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Dashboard gerado com sucesso em: {output_html}")

if __name__ == '__main__':
    main()
