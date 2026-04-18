import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import os
import glob
from datetime import datetime, timedelta

def formatar_kpi(valor, is_float=False):
    if pd.isna(valor):
        return "0"
    if is_float:
        return f"{valor:,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"{int(valor):,}.".replace(',', '.')[:-1]

def compilar_visao(nome_visao, curr_df, is_global=False):
    # --- 1. Top KPIs ---
    qtd_pedidos = curr_df['NRO_PEDIDO'].nunique()
    qtd_itens = len(curr_df)
    
    # Média de dias sem atendimento (Pedidos vs Itens)
    avg_dias_pedido = curr_df.groupby('NRO_PEDIDO')['DIAS_ESPERA'].max().mean()
    avg_dias_item = curr_df['DIAS_ESPERA'].mean()
    
    # Estoque < 1 Cx e Volume a expedir
    itens_sem_estoque_cd = curr_df[curr_df['ESTOQUE_CRITICO']].shape[0]
    volume_caixas_expedir = curr_df['CAIXAS_ESPERA'].sum()

    # --- 2. Gráfico 1: Dia a Dia (Line + Bar) ---
    df_dia = curr_df.groupby('DATA').agg(
        PEDIDOS=('NRO_PEDIDO', 'nunique'),
        CAIXAS=('CAIXAS_ESPERA', 'sum')
    ).reset_index()
    
    df_dia = df_dia.sort_values('DATA')

    fig_dia = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig_dia.add_trace(
        go.Bar(x=df_dia['DATA'], y=df_dia['CAIXAS'], name="Volume Caixas (Pendentes)", opacity=0.7, marker_color='#E74C3C'),
        secondary_y=False,
    )
    
    fig_dia.add_trace(
        go.Scatter(x=df_dia['DATA'], y=df_dia['PEDIDOS'], name="Pedidos (Não Atend.)", mode='lines+markers', line=dict(color='#2980B9', width=3)),
        secondary_y=True,
    )
    
    fig_dia.update_layout(
        title="Curva de Pendências Ao Longo do SLA (Dia a Dia)",
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    gf_dia_html = fig_dia.to_html(full_html=False, include_plotlyjs=False)
    gf_ranks_html = ""
    
    # --- 3. Rankings (Somente para Visão Global) ---
    if is_global:
        df_loja = curr_df.groupby('CODIGO_EMPRESA').agg(
            PEDIDOS=('NRO_PEDIDO', 'nunique'),
            CAIXAS=('CAIXAS_ESPERA', 'sum'),
            AVG_DIAS_ITEM=('DIAS_ESPERA', 'mean')
        ).reset_index()
        
        # Média por Pedido exige sub-agrupamento para evitar distorção de itens e calcular a ponta exata
        df_loja_ped = curr_df.groupby(['CODIGO_EMPRESA', 'NRO_PEDIDO'])['DIAS_ESPERA'].max().groupby('CODIGO_EMPRESA').mean().reset_index(name='AVG_DIAS_PED')
        df_loja = pd.merge(df_loja, df_loja_ped, on='CODIGO_EMPRESA', how='left')
        
        # Converte para string descritiva da Loja
        df_loja['LOJA'] = "Loja " + df_loja['CODIGO_EMPRESA'].astype(str)
        
        fig_rank = make_subplots(rows=2, cols=2, 
                                 subplot_titles=("Ranking: Qtd. Pedidos p/ Filial", 
                                                 "Ranking: Caixas p/ Filial",
                                                 "Média de Atraso por Pedido (Dias)",
                                                 "Média de Atraso por Item (Dias)"))
        
        df_rank_ped = df_loja.sort_values('PEDIDOS', ascending=True).tail(15)
        df_rank_cx = df_loja.sort_values('CAIXAS', ascending=True).tail(15)
        df_rank_avg_ped = df_loja.sort_values('AVG_DIAS_PED', ascending=True).tail(15)
        df_rank_avg_item = df_loja.sort_values('AVG_DIAS_ITEM', ascending=True).tail(15)
        
        fig_rank.add_trace(
            go.Bar(y=df_rank_ped['LOJA'], x=df_rank_ped['PEDIDOS'], orientation='h', marker_color='#3498DB', text=df_rank_ped['PEDIDOS'], textposition='auto'),
            row=1, col=1
        )
        
        fig_rank.add_trace(
            go.Bar(y=df_rank_cx['LOJA'], x=df_rank_cx['CAIXAS'], orientation='h', marker_color='#E67E22', text=df_rank_cx['CAIXAS'].apply(lambda x: formatar_kpi(x, True)), textposition='auto'),
            row=1, col=2
        )
        
        fig_rank.add_trace(
            go.Bar(y=df_rank_avg_ped['LOJA'], x=df_rank_avg_ped['AVG_DIAS_PED'], orientation='h', marker_color='#9B59B6', text=df_rank_avg_ped['AVG_DIAS_PED'].apply(lambda x: formatar_kpi(x, True)), textposition='auto'),
            row=2, col=1
        )
        
        fig_rank.add_trace(
            go.Bar(y=df_rank_avg_item['LOJA'], x=df_rank_avg_item['AVG_DIAS_ITEM'], orientation='h', marker_color='#E74C3C', text=df_rank_avg_item['AVG_DIAS_ITEM'].apply(lambda x: formatar_kpi(x, True)), textposition='auto'),
            row=2, col=2
        )
        
        fig_rank.update_layout(height=800, showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
        gf_ranks_html = fig_rank.to_html(full_html=False, include_plotlyjs=False)

    # --- 4. Montar a Tray HTML desta Visão ---
    html = f"""
    <div style="background: linear-gradient(135deg, #1A2530 0%, #2C3E50 100%); color:white; padding:20px; border-radius:10px; margin-bottom:20px; display:flex; gap:15px; flex-wrap:wrap; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <!-- Cards -->
        <div style="flex:1; min-width:150px; background:rgba(255,255,255,0.1); padding:15px; border-radius:8px; text-align:center;">
            <div style="font-size:12px; color:#BDC3C7; text-transform:uppercase;">Pedidos Atrasados</div>
            <div style="font-size:24px; font-weight:bold; color:#F1C40F;">{formatar_kpi(qtd_pedidos)}</div>
        </div>
        <div style="flex:1; min-width:150px; background:rgba(255,255,255,0.1); padding:15px; border-radius:8px; text-align:center;">
            <div style="font-size:12px; color:#BDC3C7; text-transform:uppercase;">Itens Pendentes</div>
            <div style="font-size:24px; font-weight:bold; color:#E74C3C;">{formatar_kpi(qtd_itens)}</div>
        </div>
        <div style="flex:1; min-width:150px; background:rgba(255,255,255,0.1); padding:15px; border-radius:8px; text-align:center;">
            <div style="font-size:12px; color:#BDC3C7; text-transform:uppercase;">Avg Atraso (Pedido)</div>
            <div style="font-size:24px; font-weight:bold; color:#3498DB;">{formatar_kpi(avg_dias_pedido, True)} dias</div>
        </div>
        <div style="flex:1; min-width:150px; background:rgba(255,255,255,0.1); padding:15px; border-radius:8px; text-align:center;">
            <div style="font-size:12px; color:#BDC3C7; text-transform:uppercase;">Avg Atraso (Item)</div>
            <div style="font-size:24px; font-weight:bold; color:#9B59B6;">{formatar_kpi(avg_dias_item, True)} dias</div>
        </div>
        <div style="flex:1; min-width:150px; background:rgba(255,255,255,0.1); padding:15px; border-radius:8px; text-align:center;">
            <div style="font-size:12px; color:#BDC3C7; text-transform:uppercase;">Sem Estoque (< 1Cx)</div>
            <div style="font-size:24px; font-weight:bold; color:#E67E22;">{formatar_kpi(itens_sem_estoque_cd)} SKUs</div>
        </div>
        <div style="flex:1; min-width:150px; background:rgba(255,255,255,0.1); padding:15px; border-radius:8px; text-align:center;">
            <div style="font-size:12px; color:#BDC3C7; text-transform:uppercase;">Volume a Expedir</div>
            <div style="font-size:24px; font-weight:bold; color:#2ECC71;">{formatar_kpi(volume_caixas_expedir, True)} cxs</div>
        </div>
    </div>
    
    <div style="background:white; border-radius:10px; padding:15px; margin-bottom:20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        {gf_dia_html}
    </div>
    """
    
    if is_global:
        html += f"""
        <div style="background:white; border-radius:10px; padding:15px; margin-bottom:20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
            {gf_ranks_html}
        </div>
        """
        
    return html

def gerar_dashboard():
    base_dir = Path(__file__).resolve().parent
    pasta_entrada = base_dir / 'bd_saida'
    
    arquivos = glob.glob(str(pasta_entrada / 'ped_pendentes_formatado_*.csv'))
    if not arquivos:
        print("❌ Nenhum arquivo ped_pendentes_formatado_*.csv encontrado em bd_saida!")
        return
        
    arquivo_recente = max(arquivos, key=os.path.getctime)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Lendo fonte base: {Path(arquivo_recente).name}")
    
    df = pd.read_csv(arquivo_recente, sep=';', encoding='utf-8-sig', dtype=str)

    # Remove CD 16 do relatorio conforme regra operacional atual
    if 'CODIGO_EMPRESA' in df.columns:
        df = df[df['CODIGO_EMPRESA'].astype(str).str.strip() != '16'].copy()
    
    # --- A. Saneamento e Matemática Intocável ---
    cols_numericas = ['QUANTIDADE_A_EXPEDIR', 'EMBALAGEM', 'ESTOQUE_DISPONIVEL_CD']
    for c in cols_numericas:
        if c in df.columns:
            # Substituição puramente em memória para viabilizar cálculos em Python (Regra Anti-Ponto Global respeitada)
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.', regex=False), errors='coerce').fillna(0)
            
    data_texto = df['DATA'].astype(str).str[:10].str.strip()
    data_iso = pd.to_datetime(data_texto, format='%Y-%m-%d', errors='coerce')
    data_br = pd.to_datetime(data_texto, format='%d/%m/%Y', errors='coerce')
    df['DATA'] = data_iso.fillna(data_br)
    df = df.dropna(subset=['DATA'])
    
    # --- B. Regras de Negócio e SLAs ---
    hoje = datetime.now()
    data_fim_referencia = hoje - timedelta(days=2) # data final: hoje menos 2 dias
    data_inicio_referencia = hoje - timedelta(days=31) # data inicial: hoje menos 31 dias
    
    # Filtro rígido do range de 30 dias de interesse:
    df = df[(df['DATA'] >= data_inicio_referencia) & (df['DATA'] <= data_fim_referencia)].copy()
    
    if len(df) == 0:
        print("⚠️ Nenhum registro classificado no critério de SLA (30 dias antes das últimas 48h).")
        return
    
    # Cálculos das colunas alvo
    df['DIAS_ESPERA'] = (data_fim_referencia - df['DATA']).dt.days
    df['DIAS_ESPERA'] = df['DIAS_ESPERA'].clip(lower=0) # Evita delay negativo (conceitualmente inválido)
    df['CAIXAS_ESPERA'] = df['QUANTIDADE_A_EXPEDIR'] / df['EMBALAGEM'].replace(0, 1) # Previne div/0
    df['ESTOQUE_CRITICO'] = df['ESTOQUE_DISPONIVEL_CD'] < df['EMBALAGEM']

    # --- C. Framework No-Server ---
    visoes_html = ""
    opcoes_select = ""
    
    # Visão 1: Global
    html_global = compilar_visao("Todas as Filiais", df, is_global=True)
    visoes_html += f'<div id="view_global" class="sub-view" style="display:block;">{html_global}</div>'
    opcoes_select += '<option value="global">🏢 Visão Consolidada CD (Todas Lojas)</option>'
    
    # Visão N: Lojas Individuais
    lojas = sorted(df['CODIGO_EMPRESA'].dropna().unique(), key=lambda x: str(x).zfill(4))
    for loja in lojas:
        df_loja = df[df['CODIGO_EMPRESA'] == loja]
        html_loja = compilar_visao(f"Loja {loja}", df_loja, is_global=False)
        visoes_html += f'<div id="view_loja_{loja}" class="sub-view" style="display:none;">{html_loja}</div>'
        opcoes_select += f'<option value="loja_{loja}">🏪 Filial {loja}</option>'
        
    pagina_html = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Varejo Insight - Dashboard Pendências Supply</title>
        <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #F8F9FA; margin:0; padding:20px; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background:white; padding:15px; border-radius:10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
            h1 {{ margin:0; color: #2C3E50; font-size:24px; }}
            select {{ padding:10px; font-size:16px; border:2px solid #3498DB; border-radius:5px; background:white; cursor:pointer; font-weight:bold; min-width:300px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>📦 Radar de Pendências Ocultas | SLA Critico</h1>
                <span style="color:#7F8C8D; font-size:14px;">Analise Cohort: 30 dias cortando o target D-2</span>
            </div>
            <select id="FiltroMestre" onchange="trocarVisao()">
                {opcoes_select}
            </select>
        </div>
        
        {visoes_html}

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

    # --- D. Salvar Arquivo Resultante ---
    data_hoje = hoje.strftime('%d_%m_%Y')
    pasta_resultado = base_dir / 'bd_resultados'
    pasta_resultado.mkdir(parents=True, exist_ok=True)
    arquivo_saida_html = pasta_resultado / f'Painel_Pendencias_SLA_{data_hoje}.html'
    
    with open(arquivo_saida_html, 'w', encoding='utf-8') as f:
        f.write(pagina_html)
        
    print(f"✅ SUCESSO! Dashboard de SLA No-Server gerado.")
    print(f"Salvo em: {arquivo_saida_html}")
    print(f"Total de Lojas Mapeadas: {len(lojas)}")

if __name__ == '__main__':
    os.chdir(Path(__file__).parent.resolve())
    gerar_dashboard()
    os.system('cls' if os.name == 'nt' else 'clear')
    print("✅ Dashboard gerado com sucesso!")