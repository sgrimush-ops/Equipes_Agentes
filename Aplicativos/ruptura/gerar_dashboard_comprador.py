import os
import json
import pandas as pd
import plotly.graph_objects as go
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
arquivo_entrada = Path('c:/Users/Alessandro.soares.BAKLIZI/Downloads/Equipes_Agentes/Aplicativos/import_querys/query.parquet')

def compile_view(view_name: str, df_view: pd.DataFrame) -> tuple:
    """Gera o HTML do gráfico e da tabela para uma visão específica.
    
    Args:
        view_name: Nome da visão (ex: Comprador X).
        df_view: DataFrame filtrado para a visão.
        
    Returns:
        tuple: (grafico_html, tabela_html)
    """
    # Agrupamento por Comprador para a tabela
    df_resumo = df_view.groupby('COMPRADOR').agg(
        Mix_Ativo=('CODIGO_PRODUTO', 'nunique'),
        Ruptura_CD=('CODIGO_PRODUTO', lambda x: x[df_view.loc[x.index, 'CODIGO_EMPRESA'] == 15][df_view.loc[x.index, 'QUANTIDADE_DISPONIVEL'] <= 0].nunique()),
        Base_CD=('CODIGO_PRODUTO', lambda x: x[df_view.loc[x.index, 'CODIGO_EMPRESA'] == 15].nunique()),
        Ruptura_Loja=('CODIGO_PRODUTO', lambda x: x[df_view.loc[x.index, 'CODIGO_EMPRESA'] != 15][df_view.loc[x.index, 'QUANTIDADE_DISPONIVEL'] <= 0].nunique()),
        Base_Loja=('CODIGO_PRODUTO', lambda x: x[df_view.loc[x.index, 'CODIGO_EMPRESA'] != 15].nunique()),
        Pendencias=('CODIGO_PRODUTO', lambda x: x[df_view.loc[x.index, 'CODIGO_EMPRESA'] == 15][df_view.loc[x.index, 'QTD_PEND_PEDCOMPRA'] > 0].nunique())
    ).reset_index()

    # Cálculos de Percentuais
    df_resumo['% Ruptura CD'] = (df_resumo['Ruptura_CD'] / df_resumo['Base_CD'].replace(0, np.nan) * 100).fillna(0)
    df_resumo['% Ruptura Loja'] = (df_resumo['Ruptura_Loja'] / df_resumo['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
    df_resumo['% Pendencias'] = (df_resumo['Pendencias'] / df_resumo['Base_CD'].replace(0, np.nan) * 100).fillna(0)

    # Ordenação: TOTAL GERAL primeiro no gráfico, então compradores ordenados
    if view_name == "TOTAL GERAL":
        # Criar linha de Total Geral para o gráfico
        total_geral = pd.DataFrame({
            'COMPRADOR': ['TOTAL GERAL'],
            'Mix_Ativo': [df_resumo['Mix_Ativo'].max()], # Mix total não é soma, é o maior ou nunique global
            'Ruptura_CD': [df_resumo['Ruptura_CD'].sum()],
            'Base_CD': [df_resumo['Base_CD'].sum()],
            'Ruptura_Loja': [df_resumo['Ruptura_Loja'].sum()],
            'Base_Loja': [df_resumo['Base_Loja'].sum()],
            'Pendencias': [df_resumo['Pendencias'].sum()]
        })
        # Recalcular percentuais para o Total Geral
        total_geral['% Ruptura CD'] = (total_geral['Ruptura_CD'] / total_geral['Base_CD'].replace(0, np.nan) * 100).fillna(0)
        total_geral['% Ruptura Loja'] = (total_geral['Ruptura_Loja'] / total_geral['Base_Loja'].replace(0, np.nan) * 100).fillna(0)
        total_geral['% Pendencias'] = (total_geral['Pendencias'] / total_geral['Base_CD'].replace(0, np.nan) * 100).fillna(0)
        
        df_plot = pd.concat([total_geral, df_resumo.sort_values('% Ruptura CD', ascending=False)], ignore_index=True)
    else:
        df_plot = df_resumo.copy()

    # Gráfico Plotly
    fig = go.Figure()
    
    # Ordem das barras: Ruptura CD, Ruptura Loja, Pendencias
    metrics = ['% Ruptura CD', '% Ruptura Loja', '% Pendencias']
    colors = ['#EF553B', '#636EFA', '#00CC96']
    
    for metric, color in zip(metrics, colors):
        fig.add_trace(go.Bar(
            name=metric,
            x=df_plot['COMPRADOR'],
            y=df_plot[metric],
            marker_color=color,
            text=df_plot[metric].round(1).astype(str) + '%',
            textposition='auto'
        ))

    fig.update_layout(
        title=f"Ruptura por Comprador - {view_name}",
        barmode='group',
        xaxis_title="Comprador",
        yaxis_title="Percentual (%)",
        legend_title="Métricas",
        template="plotly_white",
        height=500,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    grafico_html = fig.to_html(full_html=False, include_plotlyjs=False)
    
    # Tabela HTML
    df_resumo.columns.name = None
    df_resumo.index.name = None
    
    tabela_html = df_resumo.to_html(
        classes='table table-striped table-hover align-middle',
        index=False,
        border=0,
        justify='center',
        float_format=lambda x: f'{x:,.2f}'.replace('.', 'X').replace(',', '.').replace('X', ',') if isinstance(x, (float, int)) else x
    )
    
    return grafico_html, tabela_html

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

    # Preparação de Visões
    opcoes_select = '<option value="TOTAL_GERAL">TOTAL GERAL</option>'
    visoes_html = ""
    
    # 1. Visão Global
    print("Gerando visão TOTAL GERAL...")
    gf, tb = compile_view("TOTAL GERAL", df)
    visoes_html += f'<div id="view_TOTAL_GERAL" class="sub-view" style="display:block;">{gf}<div class="mt-4">{tb}</div></div>'
    
    # 2. Visões por Comprador
    compradores = sorted(df['COMPRADOR'].unique())
    for comp in compradores:
        print(f"Gerando visão para {comp}...")
        df_comp = df[df['COMPRADOR'] == comp]
        gf, tb = compile_view(comp, df_comp)
        
        # ID seguro para o HTML
        comp_id = comp.replace(' ', '_').replace('.', '').replace('-', '_')
        opcoes_select += f'<option value="{comp_id}">{comp}</option>'
        visoes_html += f'<div id="view_{comp_id}" class="sub-view" style="display:none;">{gf}<div class="mt-4">{tb}</div></div>'

    # Gerar Snapshot Histórico (Novo)
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

    # Template HTML Final
    html_template = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard de Ruptura - Compradores</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
        <style>
            body {{ background-color: #f8f9fa; padding: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            .card {{ border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 12px; margin-bottom: 20px; }}
            .header-info {{ background: #2c3e50; color: white; padding: 20px; border-radius: 12px; margin-bottom: 30px; }}
            select.form-select {{ max-width: 400px; border-radius: 8px; border: 2px solid #dee2e6; }}
            .table-striped tbody tr:nth-of-type(odd) {{ background-color: rgba(0,0,0,.02); }}
            .sub-view {{ animation: fadeIn 0.5s; }}
            @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
            
            /* Alinhamento de Tabela */
            .table th {{ text-align: center !important; font-weight: bold; background-color: #f1f3f5 !important; border-bottom: 2px solid #dee2e6; }}
            .table td {{ text-align: center; vertical-align: middle; }}
            .table th:first-child, .table td:first-child {{ text-align: left; padding-left: 15px; }}
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="header-info d-flex justify-content-between align-items-center">
                <div>
                    <h1>📊 Dashboard de Ruptura</h1>
                    <p class="mb-0">Visão Gerencial por Comprador (Atualizado em: {date.today().strftime('%d/%m/%Y')})</p>
                </div>
                <div>
                    <select id="FiltroMestre" class="form-select form-select-lg" onchange="trocarVisao()">
                        {opcoes_select}
                    </select>
                </div>
            </div>

            <div class="card p-4">
                {visoes_html}
            </div>
        </div>

        <script>
        function trocarVisao() {{
            var selecionado = document.getElementById("FiltroMestre").value;
            var abas = document.getElementsByClassName("sub-view");
            for(var i=0; i < abas.length; i++) {{
                abas[i].style.display = (abas[i].id === "view_" + selecionado) ? "block" : "none";
            }}
            window.dispatchEvent(new Event('resize')); 
        }}
        </script>
    </body>
    </html>
    """

    output_path = base_dir / "dashboard_comprador.html"
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(html_template)
    
    print(f"Dashboard gerado com sucesso em: {output_path}")

if __name__ == '__main__':
    principal()
