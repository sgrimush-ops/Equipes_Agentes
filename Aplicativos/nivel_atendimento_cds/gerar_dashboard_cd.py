import os
import pandas as pd
import plotly.express as px

def main():
    # Definindo caminhos
    base_dir = r"C:\Users\usr\Downloads\Equipes_Agentes\Aplicativos"
    input_file = os.path.join(base_dir, "import_querys", "nivel_atendimento_cds.txt")
    output_dir = os.path.join(base_dir, "nivel_atendimento_cds")
    
    # Cria o diretório se não existir
    os.makedirs(output_dir, exist_ok=True)
    
    excel_file = os.path.join(output_dir, "nivel_atendimento_cds_formatado.xlsx")
    html_file = os.path.join(output_dir, "dashboard_atendimento_cd.html")
    
    # 1. Leitura dos dados
    try:
        df = pd.read_csv(input_file, sep=";", encoding="latin1")
    except Exception as e:
        print(f"Erro ao ler o arquivo txt: {e}")
        return

    cols_to_numeric = [
        'TOTAL_QTD_SOLICITADA', 'TOTAL_QTD_EXPEDIDA', 'QTD_PEDIDOS', 
        'VEZES_ATENDIDO_TOTAL', 'VEZES_CORTADO_CANCELADO',
        'VEZES_ATENDIDO_PARCIAL', 'VEZES_EM_TRANSITO', 
        'VEZES_EM_SEPARACAO'
    ]
    for c in cols_to_numeric:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    df['QTD_PENDENTE'] = df['TOTAL_QTD_SOLICITADA'] - df['TOTAL_QTD_EXPEDIDA']
    # Evita valores negativos caso a expedição seja maior que a solicitação por algum motivo
    df['QTD_PENDENTE'] = df['QTD_PENDENTE'].apply(lambda x: x if x > 0 else 0)
    
    # 2. Exportar para Excel
    try:
        df.to_excel(excel_file, index=False)
        print(f"Planilha Excel gerada com sucesso: {excel_file}")
    except PermissionError:
        print(f"Erro de permissão: feche o Excel '{excel_file}' para que ele seja atualizado. O dashboard continuará sendo gerado.")
    
    # 3. Cálculos para o Dashboard
    total_solicitada = df['TOTAL_QTD_SOLICITADA'].sum()
    total_expedida = df['TOTAL_QTD_EXPEDIDA'].sum()
    total_pendente = df['QTD_PENDENTE'].sum()
    
    total_pedidos = df['QTD_PEDIDOS'].sum()
    vezes_cortado = df['VEZES_CORTADO_CANCELADO'].sum()

    # 1. Nível de Serviço Físico (Efetivado / Expedido)
    if total_solicitada > 0:
        nivel_servico_fisico = (total_expedida / total_solicitada) * 100
    else:
        nivel_servico_fisico = 0

    # 2. Taxa de Pedidos Sem Corte (Não Cancelados)
    if total_pedidos > 0:
        taxa_pedidos_ok = ((total_pedidos - vezes_cortado) / total_pedidos) * 100
    else:
        taxa_pedidos_ok = 0
    
    # Valores detalhados de Status de Pedido
    status_cols = {
        'Totalmente Atendido': df['VEZES_ATENDIDO_TOTAL'].sum(),
        'Parcialmente Atendido': df['VEZES_ATENDIDO_PARCIAL'].sum(),
        'Cortado/Cancelado': df['VEZES_CORTADO_CANCELADO'].sum(),
        'Em Trânsito': df['VEZES_EM_TRANSITO'].sum(),
        'Em Separação': df['VEZES_EM_SEPARACAO'].sum()
    }
    status_names = list(status_cols.keys())
    status_values = list(status_cols.values())
    
    # Gráfico 1: Expedida vs Pendente/Cortada (Volume Físico)
    fig_qtd = px.pie(
        names=['Quantidade Expedida', 'Quantidade Pendente/Cortada'],
        values=[total_expedida, total_pendente],
        title='Situação do Volume Físico Solicitado',
        color_discrete_sequence=['#2ecc71', '#e74c3c']
    )
    html_fig_qtd = fig_qtd.to_html(full_html=False, include_plotlyjs=False)
    
    # Gráfico 2: Pedidos Detalhados (Barras)
    fig_ped = px.bar(
        x=status_names,
        y=status_values,
        title='Comparação Detalhada de Status (Vezes)',
        labels={'x': 'Status', 'y': 'Vezes'},
        text=status_values,
        color=status_names,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_ped.update_traces(textposition='auto')
    fig_ped.update_layout(showlegend=False)
    html_fig_ped = fig_ped.to_html(full_html=False, include_plotlyjs=False)
    
    # Tabela Top 10 Produtos Mais Cortados
    top_10 = df.nlargest(10, 'VEZES_CORTADO_CANCELADO')[
        ['CODIGO_PRODUTO', 'DESCRICAO_PRODUTO', 'VEZES_CORTADO_CANCELADO', 'QTD_PENDENTE', 'TOTAL_QTD_SOLICITADA']
    ]
    tabela_html = top_10.to_html(index=False, classes='table table-striped table-hover', justify='center')
    
    # 4. Geração do HTML (Arquitetura No-Server)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard - Nível de Atendimento CD</title>
        <!-- Biblioteca Plotly unificada -->
        <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
        <!-- Bootstrap para estilo rápido -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; }}
            .card {{ border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); border: none; margin-bottom: 20px; }}
            .kpi-title {{ font-size: 1rem; color: #858796; text-transform: uppercase; font-weight: bold; }}
            .kpi-value {{ font-size: 2.2rem; font-weight: 800; color: #5a5c69; margin-top: 10px; }}
            .header-title {{ color: #4e73df; font-weight: 800; margin-bottom: 30px; }}
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <h2 class="header-title text-center">Dashboard Analítico: Nível de Atendimento do CD</h2>
            
            <!-- Linha de KPIs -->
            <div class="row">
                <div class="col-md-4">
                    <div class="card p-4 text-center border-left-primary">
                        <div class="kpi-title">Nível de Serviço (Físico Efetivado)</div>
                        <div class="kpi-value text-primary">{nivel_servico_fisico:.2f}%</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card p-4 text-center">
                        <div class="kpi-title">Volume Total Solicitado</div>
                        <div class="kpi-value">{total_solicitada:,.0f}</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card p-4 text-center">
                        <div class="kpi-title">Total de Pedidos</div>
                        <div class="kpi-value">{total_pedidos:,.0f}</div>
                    </div>
                </div>
            </div>

            <!-- Linha de Gráficos -->
            <div class="row">
                <div class="col-md-6">
                    <div class="card p-3">
                        {html_fig_qtd}
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card p-3">
                        {html_fig_ped}
                    </div>
                </div>
            </div>

            <!-- Tabela -->
            <div class="row">
                <div class="col-12">
                    <div class="card p-4">
                        <h5 class="mb-3 text-secondary font-weight-bold">Top 10 Produtos Mais Cortados (por Vezes Cortado)</h5>
                        <div class="table-responsive">
                            {tabela_html}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Script para garantir o resize dos gráficos Plotly -->
        <script>
            window.dispatchEvent(new Event('resize'));
        </script>
    </body>
    </html>
    """
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Dashboard HTML gerado com sucesso: {html_file}")

if __name__ == "__main__":
    main()
