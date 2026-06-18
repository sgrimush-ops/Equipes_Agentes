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

def compilar_visao(nome_visao, curr_df, id_visao, is_single_comprador=False):
    if curr_df.empty:
        return f"<div style='text-align:center; padding: 50px; color: #888;'><h3>Não há dados para este filtro.</h3></div>", "", "Resumo"

    # Gráfico
    df_chart = curr_df.groupby(['DATA_VENCIMENTO_DT', 'COMPRADOR'], as_index=False)['VALOR_PROJETADO'].sum()
    df_chart = df_chart.sort_values('DATA_VENCIMENTO_DT')

    fig = px.bar(
        df_chart, 
        x='DATA_VENCIMENTO_DT', 
        y='VALOR_PROJETADO', 
        color='COMPRADOR',
        title=f"Evolução Diária - {nome_visao}",
        template='plotly_dark',
        barmode='stack',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_layout(
        xaxis_title="Data de Vencimento",
        yaxis_title="Valor a Pagar (R$)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter", size=14, color="#e0e0e0"),
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40),
        legend_title_text='Comprador' if not is_single_comprador else ''
    )
    
    if is_single_comprador:
        fig.update_layout(showlegend=False)
    
    grafico_html = fig.to_html(full_html=False, include_plotlyjs=False)
    
    # Tabela (Se for apenas um comprador, mostramos quebra por Fornecedor!)
    if is_single_comprador and 'FORNECEDOR' in curr_df.columns:
        df_table = curr_df.groupby('FORNECEDOR', as_index=False)['VALOR_PROJETADO'].sum()
        col_label = 'FORNECEDOR'
        table_title = f"Detalhamento por Fornecedor (Comprador: {curr_df['COMPRADOR'].iloc[0]})"
    else:
        df_table = curr_df.groupby('COMPRADOR', as_index=False)['VALOR_PROJETADO'].sum()
        col_label = 'COMPRADOR'
        table_title = "Resumo Geral por Comprador"

    df_table = df_table.sort_values('VALOR_PROJETADO', ascending=False)
    
    total = df_table['VALOR_PROJETADO'].sum()
    df_table.loc[len(df_table)] = ['TOTAL GERAL', total]
    
    df_table['Valor Projetado'] = df_table['VALOR_PROJETADO'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    df_table = df_table[[col_label, 'Valor Projetado']]
    
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
    
    visoes_html = ""
    botoes_html = ""
    
    for i, orig in enumerate(origens):
        active_btn = "active" if i == 0 else ""
        botoes_html += f'<button class="btn {active_btn}" onclick="changeOrigem(\'{orig["id"]}\', this)">{orig["nome"]}</button>\n'
        
        # Visão: Todos os Compradores (para esta Origem)
        gf, tb, title = compilar_visao(orig["nome"], orig["df"], f'{orig["id"]}_todos', is_single_comprador=False)
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
    </div>
    
    {visoes_html}

    <script>
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
    }}

    function changeComprador(selectObj) {{
        current_comprador = selectObj.value;
        updateView();
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
    </script>
</body>
</html>
"""
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Dashboard gerado com sucesso em: {output_html}")

if __name__ == '__main__':
    main()
