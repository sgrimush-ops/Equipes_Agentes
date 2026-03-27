if __name__ == '__main__':
    import os
    from pathlib import Path
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path



def gerar_dashboard():
    base_dir = Path(__file__).parent
    pasta_resultados = base_dir / "bd_resultados"
    arquivo_csv = pasta_resultados / "consolidado.csv"
    
    print(f"Lendo {arquivo_csv} para gerar o Dashboard Interativo...")
    try:
        df = pd.read_csv(arquivo_csv, sep=';')
    except FileNotFoundError:
        print(f"Arquivo '{arquivo_csv}' não encontrado. Execute consolidado.py primeiro.")
        return

    # Remover dados de Janeiro ('/01/')
    df = df[~df['Data'].str.contains(r'/01/\d{4}', na=False)]

    # Preparar Dados (Contar pedidos únicos via 'Nro Pedido' em vez de linhas)
    total_pedidos = df['Nro Pedido'].nunique()
    volume_total = df['Qtde Expedir'].sum()

    pedidos_por_dia = df.groupby('Data')['Nro Pedido'].nunique().reset_index(name='Pedidos')
    
    pedidos_por_loja = df.groupby('Loja')['Nro Pedido'].nunique().reset_index(name='Pedidos')

    # Volume por Dia e Loja
    vol_por_dia = df.groupby('Data')['Qtde Expedir'].sum().reset_index()
    vol_por_loja = df.groupby('Loja')['Qtde Expedir'].sum().reset_index()
    
    # Criar a figura principal com subplots
    fig = make_subplots(
        rows=3, cols=2,
        specs=[
            [{"type": "indicator"}, {"type": "indicator"}],
            [{"type": "xy"}, {"type": "xy"}],
            [{"type": "xy"}, {"type": "xy"}]
        ],
        subplot_titles=(
            "", "",  # Titulos dos indicadores ficam vazios pois o texto é interno
            "Pedidos Feitos por Dia", "Volume de Expedição por Dia",
            "Pedidos Totais por Loja", "Volume Total por Loja"
        ),
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )

    # 1. Total Pedidos (KPI)
    fig.add_trace(go.Indicator(
        mode="number",
        value=total_pedidos,
        title={"text": "🛒 Pedidos Totais", "font": {"size": 24}},
        number={"font": {"size": 50, "color": "#1f77b4"}}
    ), row=1, col=1)

    # 2. Volume Total (KPI)
    fig.add_trace(go.Indicator(
        mode="number",
        value=volume_total,
        title={"text": "📦 Volume de Mercadorias Total", "font": {"size": 24}},
        number={"valueformat": ",.0f", "font": {"size": 50, "color": "#2ca02c"}}
    ), row=1, col=2)

    # 3. Pedidos por Dia (Gráfico de Linha)
    fig.add_trace(go.Scatter(
        x=pedidos_por_dia['Data'],
        y=pedidos_por_dia['Pedidos'],
        mode='lines+markers',
        marker=dict(size=8, color="#1f77b4"),
        line=dict(width=3),
        name='Pedidos/Dia'
    ), row=2, col=1)

    # 4. Volume por Dia (Gráfico de Barras)
    fig.add_trace(go.Bar(
        x=vol_por_dia['Data'],
        y=vol_por_dia['Qtde Expedir'],
        marker_color='#2ca02c',
        name='Volume/Dia'
    ), row=2, col=2)

    # 5. Pedidos por Loja (Gráfico de Barras)
    pedidos_por_loja_sorted = pedidos_por_loja.sort_values('Pedidos', ascending=True)
    fig.add_trace(go.Bar(
        y='Loja ' + pedidos_por_loja_sorted['Loja'].astype(str),
        x=pedidos_por_loja_sorted['Pedidos'],
        orientation='h',
        marker_color='#d62728',
        name='Pedidos/Loja'
    ), row=3, col=1)

    # 6. Volume por Loja (Gráfico de Barras Horizontais)
    # Sort for better bar chart visualization
    vol_por_loja_sorted = vol_por_loja.sort_values('Qtde Expedir', ascending=True)
    fig.add_trace(go.Bar(
        y='Loja ' + vol_por_loja_sorted['Loja'].astype(str),
        x=vol_por_loja_sorted['Qtde Expedir'],
        orientation='h',
        marker_color='#ff7f0e',
        name='Volume/Loja'
    ), row=3, col=2)

    # Customizar Layout geral do Dashboard
    fig.update_layout(
        title_text="📊 Dashboard Interativo Baklizi Analytics",
        title_x=0.5,
        title_font_size=28,
        height=1000,
        showlegend=False,
        template="plotly_dark", # Tema escuro pra dar um "WOW"
        margin=dict(t=100, b=50, l=50, r=50)
    )

    # Salvar em HTML Interativo e Print
    output_html = pasta_resultados / "dashboard_resumo.html"
    fig.write_html(str(output_html))
    
    print(f"\n✨ SURPRESA! ✨")
    print(f"Acabei de criar um Dashboard Interativo Profissional com {total_pedidos} pedidos e {volume_total:,.0f} volumes.")
    print(f"Abra o arquivo '{output_html}' no seu navegador (Chrome/Edge/Firefox) para ver os gráficos!")
    os.startfile(output_html)

if __name__ == "__main__":
    gerar_dashboard()
