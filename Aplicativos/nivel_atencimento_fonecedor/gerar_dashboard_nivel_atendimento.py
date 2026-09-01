import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

def formatar_numero(valor, decimais=2):
    if pd.isna(valor) or valor is None:
        return "0"
    try:
        val = float(valor)
        if val % 1 == 0:
            return f"{int(val):,}".replace(",", ".")
        return f"{val:,.{decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(valor)

def gerar_dashboard():
    base_dir = Path(r"C:\Users\usr\Downloads\Equipes_Agentes\Aplicativos")
    input_file = base_dir / "import_querys" / "ped_pendente_fornecedor.txt"
    output_dir = base_dir / "nivel_atencimento_fonecedor"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    html_output = output_dir / "dashboard_nivel_atendimento.html"
    excel_output = output_dir / "nivel_atendimento_fornecedor.xlsx"
    
    if not input_file.exists():
        print(f"Erro: Arquivo não encontrado em {input_file}")
        return

    print(f"Lendo base de dados: {input_file}...")
    try:
        df = pd.read_csv(input_file, sep=";", encoding="latin1", dtype=str)
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        df = pd.read_csv(input_file, sep=";", encoding="utf-8", dtype=str)

    print(f"Total de registros carregados: {len(df):,}")

    # Tratamento e Saneamento das Colunas
    cols_num = ['QTD_EMBALAGEM', 'QUANTIDADE_PEDIDA', 'QUANTIDADE_ATENDIDA', 'PERC_ATENDIMENTO']
    for col in cols_num:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0.0

    # Normalização de Status de Entrega
    def normalizar_status_entrega(val):
        s = str(val).upper().strip()
        if 'TOT' in s or '100' in s:
            return 'TOT_ATEND'
        elif 'ATRASO' in s:
            return 'ATRASO'
        elif 'AGUARD' in s:
            return 'AGUARDANDO'
        elif 'N' in s and 'ATEND' in s:
            return 'NÃO_.ATENDIDO'
        return s

    df['STATUS_ENTREGA_NORM'] = df['STATUS_ENTREGA'].apply(normalizar_status_entrega)
    df['STATUS_PEDIDO_NORM'] = df['STATUS_PEDIDO'].fillna('ATIVO').astype(str).str.upper().str.strip()
    df['COMPRADOR'] = df['COMPRADOR'].fillna('SEM COMPRADOR').astype(str).str.strip()
    df['FORNECEDOR'] = df['FORNECEDOR'].fillna('SEM FORNECEDOR').astype(str).str.strip()
    df['LOJA_DESTINO'] = pd.to_numeric(df['LOJA_DESTINO'], errors='coerce').fillna(0).astype(int)
    df['CODIGO_PRODUTO'] = pd.to_numeric(df['CODIGO_PRODUTO'], errors='coerce').fillna(0).astype(int)
    df['DESCRICAO'] = df['DESCRICAO'].fillna('').astype(str).str.strip()

    # Identificar período global
    datas_dt = pd.to_datetime(df['DATA_EMISSAO'], format='%d/%m/%Y', errors='coerce').dropna()
    min_data_iso = datas_dt.min().strftime('%Y-%m-%d') if not datas_dt.empty else ""
    max_data_iso = datas_dt.max().strftime('%Y-%m-%d') if not datas_dt.empty else ""

    # Totais Globais
    total_linhas = len(df)
    total_pedidos = df['NUMERO_PEDIDO'].nunique()

    # Criar JSON para o Dashboard
    print("Gerando estrutura JSON para o Dashboard...")
    dados_tabela = []
    for row in df.itertuples(index=False):
        dados_tabela.append([
            row.COMPRADOR,
            row.FORNECEDOR,
            str(row.NUMERO_PEDIDO),
            int(row.LOJA_DESTINO),
            str(row.DATA_EMISSAO) if pd.notna(row.DATA_EMISSAO) else "",
            str(row.DATA_PREV_ENTREGA) if pd.notna(row.DATA_PREV_ENTREGA) else "",
            str(row.DATA_LIMITE_ENTREGA) if pd.notna(row.DATA_LIMITE_ENTREGA) else "",
            int(row.CODIGO_PRODUTO),
            row.DESCRICAO,
            float(row.QTD_EMBALAGEM),
            float(row.QUANTIDADE_PEDIDA),
            float(row.QUANTIDADE_ATENDIDA),
            float(row.PERC_ATENDIMENTO),
            row.STATUS_ENTREGA_NORM,
            row.STATUS_PEDIDO_NORM
        ])

    json_dados_tabela = json.dumps(dados_tabela, ensure_ascii=False)

    # Listas para os filtros
    compradores = sorted(df['COMPRADOR'].dropna().unique().tolist())
    lojas = sorted(df['LOJA_DESTINO'].dropna().unique().tolist())
    fornecedores = sorted(df['FORNECEDOR'].dropna().unique().tolist())

    options_compradores = '<option value="TODOS">-- TODOS OS COMPRADORES --</option>'
    for c in compradores:
        options_compradores += f'<option value="{c}">{c}</option>'

    options_lojas = '<option value="TODAS">TODAS AS LOJAS</option>'
    for l in lojas:
        options_lojas += f'<option value="{l}">Loja {l}</option>'

    options_fornecedores = ''
    for f in fornecedores:
        options_fornecedores += f'<option value="{f}">\n'

    # Exportar Excel estruturado
    try:
        print("Exportando resumo em Excel...")
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            df.head(10000).to_excel(writer, sheet_name='Amostra_Pedidos', index=False)
        print(f"Arquivo Excel gerado: {excel_output}")
    except Exception as e:
        print(f"Aviso Excel: {e}")

    data_geracao = datetime.now().strftime("%d/%m/%Y às %H:%M")

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Analítico: Nível de Atendimento por Fornecedor</title>
    <!-- Bootstrap 5 CSS & FontAwesome Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <!-- Google Fonts Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">

    <style>
        :root {{
            --bg-body: #0f172a;
            --card-bg: #1e293b;
            --card-border: #334155;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --accent-red: #ef4444;
            --accent-blue: #3b82f6;
            --accent-purple: #8b5cf6;
        }}

        * {{
            box-sizing: border-box;
            font-family: 'Inter', sans-serif;
        }}

        body {{
            background-color: var(--bg-body);
            color: var(--text-main);
            padding: 16px;
            min-height: 100vh;
            font-size: 0.82rem;
        }}

        .main-header {{
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 16px 20px;
            margin-bottom: 16px;
            box-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.3);
        }}

        .date-filter-box {{
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid #475569;
            border-radius: 10px;
            padding: 6px 12px;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }}

        .date-input-field {{
            background-color: #0f172a !important;
            color: #f8fafc !important;
            border: 1px solid #334155 !important;
            border-radius: 6px;
            font-size: 0.78rem;
            padding: 4px 8px;
            color-scheme: dark;
        }}

        .date-input-field:focus {{
            border-color: var(--accent-blue) !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25) !important;
        }}

        .filter-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }}

        .form-select, .form-control {{
            background-color: #0f172a !important;
            color: #f8fafc !important;
            border: 1px solid var(--card-border) !important;
            border-radius: 8px;
            font-size: 0.84rem;
            padding: 8px 12px;
        }}

        .form-select:focus, .form-control:focus {{
            border-color: var(--accent-blue) !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25) !important;
        }}

        /* KPI Cards */
        .kpi-card {{
            background: linear-gradient(145deg, #1e293b 0%, #172033 100%);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 14px 16px;
            height: 100%;
            transition: all 0.25s ease;
            position: relative;
            overflow: hidden;
        }}

        .kpi-card:hover {{
            transform: translateY(-3px);
            border-color: #475569;
            box-shadow: 0 10px 18px -4px rgba(0, 0, 0, 0.4);
        }}

        .kpi-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
        }}

        .kpi-total::before {{ background-color: var(--accent-blue); }}
        .kpi-atend::before {{ background-color: var(--accent-green); }}
        .kpi-atraso::before {{ background-color: var(--accent-amber); }}
        .kpi-nao-atend::before {{ background-color: var(--accent-red); }}
        .kpi-aguard::before {{ background-color: var(--accent-purple); }}

        .kpi-label {{
            font-size: 0.74rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 4px;
        }}

        .kpi-val {{
            font-size: 1.65rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.2;
        }}

        .kpi-sub {{
            font-size: 0.72rem;
            color: var(--text-muted);
            margin-top: 4px;
        }}

        /* Status Buttons */
        .btn-status-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }}

        .btn-status {{
            background-color: #0f172a;
            border: 1px solid var(--card-border);
            color: #cbd5e1;
            padding: 7px 14px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.8rem;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .btn-status:hover {{
            background-color: #1e293b;
            color: #ffffff;
            border-color: #64748b;
        }}

        .btn-status.active-all {{
            background-color: #3b82f6 !important;
            color: #ffffff !important;
            border-color: #3b82f6 !important;
            box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
        }}

        .btn-status.active-tot {{
            background-color: #10b981 !important;
            color: #ffffff !important;
            border-color: #10b981 !important;
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
        }}

        .btn-status.active-atraso {{
            background-color: #f59e0b !important;
            color: #ffffff !important;
            border-color: #f59e0b !important;
            box-shadow: 0 0 12px rgba(245, 158, 11, 0.4);
        }}

        .btn-status.active-nao-atend {{
            background-color: #ef4444 !important;
            color: #ffffff !important;
            border-color: #ef4444 !important;
            box-shadow: 0 0 12px rgba(239, 68, 68, 0.4);
        }}

        .btn-status.active-aguard {{
            background-color: #8b5cf6 !important;
            color: #ffffff !important;
            border-color: #8b5cf6 !important;
            box-shadow: 0 0 12px rgba(139, 92, 246, 0.4);
        }}

        .badge-count {{
            background: rgba(255, 255, 255, 0.15);
            padding: 2px 7px;
            border-radius: 16px;
            font-size: 0.68rem;
        }}

        /* Barra de Alternância de Visão */
        .view-switch-bar {{
            background: linear-gradient(135deg, #1e293b 0%, #172033 100%);
            border: 1px solid #3b82f6;
            border-radius: 12px;
            padding: 10px 16px;
            margin-bottom: 16px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
        }}

        .btn-view-toggle {{
            background-color: #0f172a;
            border: 1px solid var(--card-border);
            color: #cbd5e1;
            padding: 7px 16px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .btn-view-toggle.active {{
            background-color: #0284c7 !important;
            color: #ffffff !important;
            border-color: #0284c7 !important;
            box-shadow: 0 0 12px rgba(2, 132, 199, 0.4);
        }}

        /* Seção Diagnóstico / Ranking */
        .diagnostic-card {{
            background: linear-gradient(145deg, #1e293b 0%, #151f30 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 18px;
        }}

        .forn-rank-item {{
            background: #0f172a;
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 12px 14px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .forn-rank-item:hover {{
            border-color: var(--accent-blue);
            transform: translateX(3px);
            background: #131d33;
        }}

        .progress-bar-custom {{
            height: 7px;
            border-radius: 4px;
            background-color: #334155;
            overflow: hidden;
            display: flex;
            margin-top: 6px;
        }}

        /* Tabela Analítica */
        .table-responsive-container {{
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }}

        .custom-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            color: var(--text-main);
            font-size: 0.78rem;
        }}

        .custom-table th {{
            background-color: #0f172a;
            color: var(--text-muted);
            font-weight: 700;
            text-transform: uppercase;
            font-size: 0.68rem;
            letter-spacing: 0.5px;
            padding: 10px 12px;
            border-bottom: 2px solid var(--card-border);
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        .custom-table td {{
            padding: 8px 12px;
            border-bottom: 1px solid #243247;
            vertical-align: middle;
        }}

        .custom-table tbody tr:hover {{
            background-color: #172338;
        }}

        /* Badges de Status na Tabela */
        .status-badge {{
            padding: 3px 8px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 0.68rem;
            display: inline-block;
            text-align: center;
        }}

        .badge-tot-atend {{ background-color: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b981; }}
        .badge-atraso {{ background-color: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #f59e0b; }}
        .badge-nao-atend {{ background-color: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid #ef4444; }}
        .badge-aguardando {{ background-color: rgba(139, 92, 246, 0.15); color: #a78bfa; border: 1px solid #8b5cf6; }}

        .perc-badge {{
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 5px;
            font-size: 0.72rem;
        }}
        .perc-100 {{ background-color: rgba(16, 185, 129, 0.2); color: #10b981; }}
        .perc-partial {{ background-color: rgba(245, 158, 11, 0.2); color: #f59e0b; }}
        .perc-zero {{ background-color: rgba(239, 68, 68, 0.2); color: #ef4444; }}

        /* Paginação */
        .pagination-btn {{
            background-color: #0f172a;
            border: 1px solid var(--card-border);
            color: #cbd5e1;
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 0.76rem;
            cursor: pointer;
        }}

        .pagination-btn:hover:not(:disabled) {{
            background-color: var(--accent-blue);
            color: #ffffff;
        }}

        .pagination-btn:disabled {{
            opacity: 0.4;
            cursor: not-allowed;
        }}
    </style>
</head>
<body>

    <div class="container-fluid">
        <!-- Cabeçalho Principal com Filtro de Datas no Centro -->
        <div class="main-header row align-items-center g-3">
            <div class="col-xxl-4 col-xl-4 col-lg-12">
                <div class="d-flex align-items-center gap-3">
                    <div style="background: rgba(59, 130, 246, 0.2); border: 1px solid #3b82f6; width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                        <i class="fa-solid fa-truck-ramp-box text-primary"></i>
                    </div>
                    <div>
                        <h2 class="mb-0 fw-bold text-white" style="font-size: 1.3rem;">Nível de Atendimento por Fornecedor</h2>
                        <p class="mb-0 text-secondary" style="font-size: 0.75rem;">
                            Monitoramento tático de entregas direto em loja • Atualizado em <span class="text-info fw-semibold">{data_geracao}</span>
                        </p>
                    </div>
                </div>
            </div>

            <!-- Espaço do Título com Filtro de Datas: De: Até: -->
            <div class="col-xxl-5 col-xl-5 col-lg-7 text-xl-center text-start">
                <div class="date-filter-box">
                    <span class="text-info small fw-bold text-nowrap" style="font-size: 0.78rem;">
                        <i class="fa-solid fa-calendar-days me-1"></i> Período Emissão:
                    </span>
                    <div class="d-flex align-items-center gap-1">
                        <label for="FiltroDataDe" class="text-secondary small fw-bold mb-0" style="font-size: 0.75rem;">De:</label>
                        <input type="date" id="FiltroDataDe" class="date-input-field" value="{min_data_iso}" onchange="aplicarFiltros()">
                    </div>
                    <div class="d-flex align-items-center gap-1">
                        <label for="FiltroDataAte" class="text-secondary small fw-bold mb-0" style="font-size: 0.75rem;">Até:</label>
                        <input type="date" id="FiltroDataAte" class="date-input-field" value="{max_data_iso}" onchange="aplicarFiltros()">
                    </div>
                    <button class="btn btn-sm btn-outline-info px-2 py-1" type="button" onclick="limparFiltroData()" title="Redefinir Período Total" style="font-size: 0.75rem;">
                        <i class="fa-solid fa-rotate-left"></i>
                    </button>
                </div>
            </div>

            <!-- Badges Resumo -->
            <div class="col-xxl-3 col-xl-3 col-lg-5 text-xl-end text-start">
                <span class="badge bg-dark border border-secondary px-2 py-1 text-white-50 me-1" id="badge-linhas-total" style="font-size: 0.75rem;">
                    <i class="fa-solid fa-database text-info me-1"></i> {total_linhas:,} Linhas
                </span>
                <span class="badge bg-dark border border-secondary px-2 py-1 text-white-50" id="badge-pedidos-total" style="font-size: 0.75rem;">
                    <i class="fa-solid fa-file-invoice text-success me-1"></i> {total_pedidos:,} Pedidos
                </span>
            </div>
        </div>

        <!-- Barra de Filtros -->
        <div class="filter-card">
            <div class="row g-2">
                <div class="col-lg-3 col-md-6">
                    <label class="form-label text-secondary fw-semibold small mb-1" style="font-size: 0.75rem;">
                        <i class="fa-solid fa-user-tie text-info me-1"></i> Filtro Comprador
                    </label>
                    <select id="FiltroComprador" class="form-select form-select-sm" onchange="aplicarFiltros()">
                        {options_compradores}
                    </select>
                </div>

                <div class="col-lg-3 col-md-6">
                    <label class="form-label text-secondary fw-semibold small mb-1" style="font-size: 0.75rem;">
                        <i class="fa-solid fa-store text-warning me-1"></i> Loja Destino
                    </label>
                    <select id="FiltroLoja" class="form-select form-select-sm" onchange="aplicarFiltros()">
                        {options_lojas}
                    </select>
                </div>

                <div class="col-lg-4 col-md-8">
                    <label class="form-label text-secondary fw-semibold small mb-1" style="font-size: 0.75rem;">
                        <i class="fa-solid fa-building text-primary me-1"></i> Pesquisar Fornecedor
                    </label>
                    <div class="input-group input-group-sm">
                        <input type="search" id="FiltroFornecedor" class="form-control form-control-sm" list="lista-fornecedores" placeholder="Digite código ou nome do fornecedor..." oninput="aplicarFiltros()" autocomplete="off">
                        <button class="btn btn-outline-secondary btn-sm" type="button" onclick="limparFiltroFornecedor()" title="Limpar Fornecedor">
                            <i class="fa-solid fa-xmark"></i>
                        </button>
                    </div>
                    <datalist id="lista-fornecedores">
                        {options_fornecedores}
                    </datalist>
                </div>

                <div class="col-lg-2 col-md-4">
                    <label class="form-label text-secondary fw-semibold small mb-1" style="font-size: 0.75rem;">
                        <i class="fa-solid fa-barcode text-success me-1"></i> Buscar Produto
                    </label>
                    <input type="text" id="FiltroProduto" class="form-control form-control-sm" placeholder="Cód. ou Descrição..." oninput="aplicarFiltros()">
                </div>
            </div>

            <!-- Botões de Seleção Rápida por Status de Entrega -->
            <div class="mt-2 pt-2 border-top border-secondary border-opacity-25">
                <div class="d-flex align-items-center justify-content-between flex-wrap gap-2">
                    <div class="fw-semibold text-secondary small" style="font-size: 0.75rem;">
                        <i class="fa-solid fa-filter me-1"></i> Status de Entrega (Clique para Filtrar):
                    </div>
                    <div class="btn-status-group" id="grupo-botoes-status">
                        <button class="btn-status active-all" id="btn_status_TODOS" onclick="mudarStatusEntrega('TODOS')">
                            <i class="fa-solid fa-layer-group"></i> Todos os Status <span class="badge-count" id="cnt_TODOS">0</span>
                        </button>
                        <button class="btn-status" id="btn_status_TOT_ATEND" onclick="mudarStatusEntrega('TOT_ATEND')">
                            <i class="fa-solid fa-circle-check text-success"></i> Totalmente Atendido <span class="badge-count" id="cnt_TOT_ATEND">0</span>
                        </button>
                        <button class="btn-status" id="btn_status_ATRASO" onclick="mudarStatusEntrega('ATRASO')">
                            <i class="fa-solid fa-clock text-warning"></i> Em Atraso <span class="badge-count" id="cnt_ATRASO">0</span>
                        </button>
                        <button class="btn-status" id="btn_status_NAO_ATEND" onclick="mudarStatusEntrega('NÃO_.ATENDIDO')">
                            <i class="fa-solid fa-circle-xmark text-danger"></i> Não Atendido <span class="badge-count" id="cnt_NAO_ATEND">0</span>
                        </button>
                        <button class="btn-status" id="btn_status_AGUARDANDO" onclick="mudarStatusEntrega('AGUARDANDO')">
                            <i class="fa-solid fa-hourglass-half text-primary"></i> Aguardando Entrega <span class="badge-count" id="cnt_AGUARDANDO">0</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Linha de KPIs Globais / Filtrados -->
        <div class="row g-2 mb-3">
            <div class="col-xl-2 col-md-4 col-sm-6">
                <div class="kpi-card kpi-total">
                    <div class="kpi-label">Itens Pedidos</div>
                    <div class="kpi-val text-white" id="kpi_total_itens">0</div>
                    <div class="kpi-sub" id="kpi_total_pedidos">0 pedidos</div>
                </div>
            </div>

            <div class="col-xl-3 col-md-4 col-sm-6">
                <div class="kpi-card kpi-atend">
                    <div class="kpi-label">Totalmente Atendido (100%)</div>
                    <div class="kpi-val text-success" id="kpi_tot_atend">0</div>
                    <div class="kpi-sub" id="kpi_perc_tot_atend">0% do total de itens</div>
                </div>
            </div>

            <div class="col-xl-2 col-md-4 col-sm-6">
                <div class="kpi-card kpi-atraso">
                    <div class="kpi-label">Em Atraso (Previsão Vencida)</div>
                    <div class="kpi-val text-warning" id="kpi_atraso">0</div>
                    <div class="kpi-sub" id="kpi_perc_atraso">0% do total</div>
                </div>
            </div>

            <div class="col-xl-3 col-md-6 col-sm-6">
                <div class="kpi-card kpi-nao-atend">
                    <div class="kpi-label">Não Atendido (Data Limite Vencida)</div>
                    <div class="kpi-val text-danger" id="kpi_nao_atend">0</div>
                    <div class="kpi-sub" id="kpi_perc_nao_atend">0% do total</div>
                </div>
            </div>

            <div class="col-xl-2 col-md-6 col-sm-6">
                <div class="kpi-card kpi-aguard">
                    <div class="kpi-label">Aguardando Entrega</div>
                    <div class="kpi-val text-info" id="kpi_aguardando">0</div>
                    <div class="kpi-sub" id="kpi_perc_aguardando">0% no prazo</div>
                </div>
            </div>
        </div>

        <!-- Barra de Alternância de Visão (Exibe uma visão por vez) -->
        <div class="view-switch-bar d-flex align-items-center justify-content-between flex-wrap gap-2">
            <div class="d-flex align-items-center gap-2">
                <span class="text-info small fw-bold"><i class="fa-solid fa-eye me-1"></i> Modo de Exibição Ativo:</span>
                <div class="btn-group btn-group-sm">
                    <button type="button" class="btn btn-view-toggle active" id="btn-modo-ranking" onclick="definirVisao('RANKING')">
                        <i class="fa-solid fa-chart-simple me-1"></i> 1. Ranking de Fornecedores
                    </button>
                    <button type="button" class="btn btn-view-toggle" id="btn-modo-tabela" onclick="definirVisao('TABELA')">
                        <i class="fa-solid fa-table-list me-1"></i> 2. Detalhamento de Pedidos
                    </button>
                </div>
            </div>

            <div>
                <button class="btn btn-sm btn-info text-dark fw-bold px-3 py-1 shadow" id="btn-alternar-visao" onclick="alternarVisaoPrincipal()" style="font-size: 0.8rem;">
                    <i class="fa-solid fa-arrow-right-arrow-left me-1"></i> Alternar Visão
                </button>
            </div>
        </div>

        <!-- VISÃO 1: Seção de Diagnóstico Dinâmico: Ranking de Fornecedores e Produtos Críticos -->
        <div class="diagnostic-card" id="secao-diagnostico" style="display: block;">
            <div class="d-flex align-items-center justify-content-between mb-2 flex-wrap gap-2">
                <div>
                    <h6 class="fw-bold text-white mb-0" style="font-size: 0.95rem;">
                        <i class="fa-solid fa-triangle-exclamation text-danger me-2"></i> Diagnóstico Dinâmico: Fornecedores com Maior Índice de Falha (Não Atendido / Atraso)
                    </h6>
                    <p class="text-secondary small mb-0" style="font-size: 0.74rem;">
                        Ranking analítico do período filtrado. (Clique no card de qualquer fornecedor para abrir automaticamente o detalhamento dos pedidos dele na tabela).
                    </p>
                </div>
            </div>

            <div class="row g-2 mt-1" id="container-diagnostico-fornecedores">
                <!-- Gerado dinamicamente via JS com base no filtro ativo -->
            </div>
        </div>

        <!-- VISÃO 2: Tabela Analítica de Pedidos (Oculta inicialmente, exposta ao alternar visão) -->
        <div class="table-responsive-container" id="secao-tabela-analitica" style="display: none;">
            <div class="d-flex align-items-center justify-content-between mb-2 flex-wrap gap-2">
                <div>
                    <h6 class="fw-bold text-white mb-0" style="font-size: 0.95rem;">
                        <i class="fa-solid fa-table-list text-primary me-2"></i> Detalhamento Analítico dos Pedidos
                    </h6>
                    <span class="text-secondary small" id="info-registros-filtrados" style="font-size: 0.74rem;">Mostrando 0 registros</span>
                </div>
                <div class="d-flex align-items-center gap-2">
                    <div class="d-flex align-items-center gap-1">
                        <label class="text-secondary small" style="font-size: 0.74rem;">Linhas:</label>
                        <select id="linhasPorPagina" class="form-select form-select-sm" style="width: 80px; font-size: 0.76rem; padding: 4px 8px;" onchange="mudarLinhasPorPagina()">
                            <option value="50">50</option>
                            <option value="100" selected>100</option>
                            <option value="250">250</option>
                            <option value="500">500</option>
                            <option value="1000">1000</option>
                        </select>
                    </div>
                    <button class="btn btn-sm btn-outline-success" onclick="exportarCSV()" style="font-size: 0.76rem; padding: 4px 10px;">
                        <i class="fa-solid fa-file-csv me-1"></i> Baixar CSV
                    </button>
                </div>
            </div>

            <div style="overflow-x: auto; max-height: 700px;" class="border rounded border-secondary border-opacity-25">
                <table class="custom-table table-hover">
                    <thead>
                        <tr>
                            <th onclick="ordenarPor(0)" style="cursor: pointer;">Comprador <i class="fa-solid fa-sort small text-muted"></i></th>
                            <th onclick="ordenarPor(1)" style="cursor: pointer;">Fornecedor <i class="fa-solid fa-sort small text-muted"></i></th>
                            <th onclick="ordenarPor(2)" style="cursor: pointer; text-align: center;">Pedido <i class="fa-solid fa-sort small text-muted"></i></th>
                            <th onclick="ordenarPor(3)" style="cursor: pointer; text-align: center;">Loja <i class="fa-solid fa-sort small text-muted"></i></th>
                            <th onclick="ordenarPor(4)" style="cursor: pointer; text-align: center;">Emissão <i class="fa-solid fa-sort small text-muted"></i></th>
                            <th onclick="ordenarPor(5)" style="cursor: pointer; text-align: center;">Previsão <i class="fa-solid fa-sort small text-muted"></i></th>
                            <th onclick="ordenarPor(6)" style="cursor: pointer; text-align: center;">Limite <i class="fa-solid fa-sort small text-muted"></i></th>
                            <th onclick="ordenarPor(7)" style="cursor: pointer; text-align: center;">Cód. Prod <i class="fa-solid fa-sort small text-muted"></i></th>
                            <th onclick="ordenarPor(8)" style="cursor: pointer;">Descrição do Produto <i class="fa-solid fa-sort small text-muted"></i></th>
                            <th style="text-align: center;">Emb</th>
                            <th onclick="ordenarPor(10)" style="cursor: pointer; text-align: right;">Qtd Ped (Cx) <i class="fa-solid fa-sort small text-muted"></i></th>
                            <th onclick="ordenarPor(11)" style="cursor: pointer; text-align: right;">Qtd Atend (Cx) <i class="fa-solid fa-sort small text-muted"></i></th>
                            <th onclick="ordenarPor(12)" style="cursor: pointer; text-align: center;">% Atend <i class="fa-solid fa-sort small text-muted"></i></th>
                            <th onclick="ordenarPor(13)" style="cursor: pointer; text-align: center;">Status Entrega <i class="fa-solid fa-sort small text-muted"></i></th>
                            <th style="text-align: center;">Status Ped</th>
                        </tr>
                    </thead>
                    <tbody id="tabela-pedidos-body">
                        <!-- Linhas renderizadas dinamicamente via JS -->
                    </tbody>
                </table>
            </div>

            <!-- Controles de Paginação -->
            <div class="d-flex align-items-center justify-content-between mt-2 flex-wrap gap-2">
                <div class="text-secondary small" id="texto-paginacao" style="font-size: 0.74rem;">
                    Página 1 de 1
                </div>
                <div class="d-flex gap-1">
                    <button class="pagination-btn" id="btn-primeira" onclick="irParaPagina(1)">
                        <i class="fa-solid fa-angles-left"></i>
                    </button>
                    <button class="pagination-btn" id="btn-anterior" onclick="irParaPagina(paginaAtual - 1)">
                        <i class="fa-solid fa-chevron-left"></i> Anterior
                    </button>
                    <button class="pagination-btn" id="btn-proxima" onclick="irParaPagina(paginaAtual + 1)">
                        Próxima <i class="fa-solid fa-chevron-right"></i>
                    </button>
                    <button class="pagination-btn" id="btn-ultima" onclick="irParaPagina(totalPaginas)">
                        <i class="fa-solid fa-angles-right"></i>
                    </button>
                </div>
            </div>
        </div>

    </div>

    <!-- Bootstrap Bundle JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>

    <script>
        // Dados Mestres Injetados pelo Python
        const masterData = {json_dados_tabela};
        const defaultMinDate = "{min_data_iso}";
        const defaultMaxDate = "{max_data_iso}";

        let dadosFiltrados = [];
        let statusSelecionado = 'TODOS';
        let visaoAtiva = 'RANKING'; // 'RANKING' (Visão 1) ou 'TABELA' (Visão 2)
        let paginaAtual = 1;
        let linhasPorPagina = 100;
        let totalPaginas = 1;
        let colunaOrdenacao = 4; // Data de emissão por padrão
        let direcaoAsc = false; // Descendente

        function converterDataParaISO(dataBR) {{
            if (!dataBR || dataBR.length < 10) return null;
            const p = dataBR.split('/');
            if (p.length === 3) {{
                return `${{p[2]}}-${{p[1].padStart(2, '0')}}-${{p[0].padStart(2, '0')}}`;
            }}
            return null;
        }}

        function limparFiltroData() {{
            document.getElementById("FiltroDataDe").value = defaultMinDate;
            document.getElementById("FiltroDataAte").value = defaultMaxDate;
            aplicarFiltros();
        }}

        // 1. Mecânica de Alternância de Visão Exclusiva (Uma por vez)
        function alternarVisaoPrincipal() {{
            if (visaoAtiva === 'RANKING') {{
                definirVisao('TABELA');
            }} else {{
                definirVisao('RANKING');
            }}
        }}

        function definirVisao(modo) {{
            visaoAtiva = modo;
            const secDiag = document.getElementById("secao-diagnostico");
            const secTab = document.getElementById("secao-tabela-analitica");
            const btnModoRank = document.getElementById("btn-modo-ranking");
            const btnModoTab = document.getElementById("btn-modo-tabela");
            const btnAlt = document.getElementById("btn-alternar-visao");

            if (modo === 'RANKING') {{
                secDiag.style.display = "block";
                secTab.style.display = "none";
                btnModoRank.classList.add("active");
                btnModoTab.classList.remove("active");
                btnAlt.innerHTML = '<i class="fa-solid fa-table-list me-1"></i> Alternar para Detalhamento';
                secDiag.scrollIntoView({{ behavior: 'smooth' }});
            }} else {{
                secDiag.style.display = "none";
                secTab.style.display = "block";
                btnModoRank.classList.remove("active");
                btnModoTab.classList.add("active");
                btnAlt.innerHTML = '<i class="fa-solid fa-chart-simple me-1"></i> Alternar para Ranking';
                renderizarTabela();
                secTab.scrollIntoView({{ behavior: 'smooth' }});
            }}
        }}

        // 2. Renderização Dinâmica do Diagnóstico de Fornecedores baseado no recorte filtrado
        function renderizarDiagnosticoDinamico(datasetBase) {{
            const container = document.getElementById("container-diagnostico-fornecedores");
            container.innerHTML = "";

            if (!datasetBase || datasetBase.length === 0) {{
                container.innerHTML = `<div class="col-12 text-center py-3 text-secondary" style="font-size: 0.78rem;">Nenhum dado encontrado para o período selecionado.</div>`;
                return;
            }}

            // Agrupar fornecedores a partir do dataset atual
            const fornMap = {{}};
            for (let i = 0; i < datasetBase.length; i++) {{
                const d = datasetBase[i];
                const forn = d[1];
                const status = d[13];
                const codProd = d[7];
                const descProd = d[8];
                const qtdPed = d[10];
                const qtdAtend = d[11];

                if (!fornMap[forn]) {{
                    fornMap[forn] = {{
                        fornecedor: forn,
                        totalItens: 0,
                        totAtend: 0,
                        atraso: 0,
                        naoAtend: 0,
                        aguardando: 0,
                        falhas: 0,
                        produtosFalhas: {{}}
                    }};
                }}

                const fObj = fornMap[forn];
                fObj.totalItens++;

                if (status === 'TOT_ATEND') {{
                    fObj.totAtend++;
                }} else if (status === 'ATRASO') {{
                    fObj.atraso++;
                    fObj.falhas++;
                }} else if (status === 'NÃO_.ATENDIDO') {{
                    fObj.naoAtend++;
                    fObj.falhas++;
                }} else if (status === 'AGUARDANDO') {{
                    fObj.aguardando++;
                }}

                if (status === 'NÃO_.ATENDIDO' || status === 'ATRASO') {{
                    if (!fObj.produtosFalhas[codProd]) {{
                        fObj.produtosFalhas[codProd] = {{
                            cod: codProd,
                            desc: descProd,
                            falhas: 0,
                            naoAtend: 0,
                            atraso: 0,
                            volCortado: 0
                        }};
                    }}
                    const pObj = fObj.produtosFalhas[codProd];
                    pObj.falhas++;
                    if (status === 'NÃO_.ATENDIDO') pObj.naoAtend++;
                    if (status === 'ATRASO') pObj.atraso++;
                    pObj.volCortado += Math.max(0, qtdPed - qtdAtend);
                }}
            }}

            // Transformar em array e ordenar pelos que tem mais falhas
            const listaForn = Object.values(fornMap)
                .sort((a, b) => b.falhas - a.falhas || b.naoAtend - a.naoAtend)
                .slice(0, 10);

            if (listaForn.length === 0 || listaForn[0].falhas === 0) {{
                container.innerHTML = `<div class="col-12 text-center py-3 text-success" style="font-size: 0.8rem;"><i class="fa-solid fa-circle-check me-2"></i>Todos os pedidos no período selecionado estão 100% atendidos ou no prazo!</div>`;
                return;
            }}

            listaForn.forEach((d, idx) => {{
                const taxaAtend = (d.totAtend / d.totalItens) * 100;
                
                // Top 4 produtos mais falhos deste fornecedor
                const topProds = Object.values(d.produtosFalhas)
                    .sort((a, b) => b.falhas - a.falhas || b.volCortado - a.volCortado)
                    .slice(0, 4);

                let prodsHtml = "";
                topProds.forEach(p => {{
                    prodsHtml += `
                        <div class="d-flex align-items-center justify-content-between py-1 border-bottom border-secondary border-opacity-10" style="font-size: 0.72rem;">
                            <div class="text-truncate me-2" title="${{p.cod}} - ${{p.desc}}">
                                <span class="text-info fw-semibold">${{p.cod}}</span> - <span class="text-light">${{p.desc}}</span>
                            </div>
                            <div class="text-nowrap">
                                <span class="badge bg-danger bg-opacity-25 text-danger border border-danger border-opacity-25 me-1" style="font-size: 0.65rem;">${{p.falhas}}x falhas</span>
                                <span class="text-warning" style="font-size: 0.7rem;">${{p.volCortado.toLocaleString('pt-BR')}} cx cortadas</span>
                            </div>
                        </div>
                    `;
                }});

                const col = document.createElement("div");
                col.className = "col-xl-6 col-lg-12";
                col.innerHTML = `
                    <div class="forn-rank-item" onclick="filtrarPorFornecedorDireto('${{d.fornecedor.replace(/'/g, "\\\\'")}}')">
                        <div class="d-flex align-items-start justify-content-between mb-1">
                            <div>
                                <span class="badge bg-secondary bg-opacity-50 text-white-50 me-1" style="font-size: 0.68rem;">#${{idx + 1}}</span>
                                <span class="fw-bold text-white" style="font-size: 0.84rem;">${{d.fornecedor}}</span>
                            </div>
                            <div class="text-end">
                                <span class="badge ${{taxaAtend >= 70 ? 'bg-success' : (taxaAtend >= 40 ? 'bg-warning text-dark' : 'bg-danger')}}" style="font-size: 0.72rem;">
                                    ${{taxaAtend.toFixed(1)}}% Atendido
                                </span>
                            </div>
                        </div>

                        <div class="progress-bar-custom mb-1">
                            <div style="width: ${{taxaAtend}}%; background-color: #10b981;" title="Atendido: ${{d.totAtend}} itens"></div>
                            <div style="width: ${{(d.atraso / d.totalItens * 100)}}%; background-color: #f59e0b;" title="Atraso: ${{d.atraso}} itens"></div>
                            <div style="width: ${{(d.naoAtend / d.totalItens * 100)}}%; background-color: #ef4444;" title="Não Atendido: ${{d.naoAtend}} itens"></div>
                            <div style="width: ${{(d.aguardando / d.totalItens * 100)}}%; background-color: #8b5cf6;" title="Aguardando: ${{d.aguardando}} itens"></div>
                        </div>

                        <div class="d-flex justify-content-between text-secondary small mb-1" style="font-size: 0.72rem;">
                            <span>Total: <strong class="text-white">${{d.totalItens.toLocaleString('pt-BR')}}</strong> itens</span>
                            <span>Atendidos: <strong class="text-success">${{d.totAtend.toLocaleString('pt-BR')}}</strong></span>
                            <span>Atraso: <strong class="text-warning">${{d.atraso.toLocaleString('pt-BR')}}</strong></span>
                            <span>Não Atend: <strong class="text-danger">${{d.naoAtend.toLocaleString('pt-BR')}}</strong></span>
                        </div>

                        <div class="mt-1 pt-1 border-top border-secondary border-opacity-25">
                            <div class="text-secondary small fw-semibold mb-1" style="font-size: 0.7rem;">
                                <i class="fa-solid fa-boxes-stacked text-danger me-1"></i> Produtos que mais falham na entrega (Clique para abrir na tabela):
                            </div>
                            ${{prodsHtml || '<div class="text-muted small" style="font-size: 0.7rem;">Sem falhas registradas no período.</div>'}}
                        </div>
                    </div>
                `;
                container.appendChild(col);
            }});
        }}

        // 3. Filtro Rápido ao Clicar no Fornecedor (Filtra e alterna para a Tabela)
        function filtrarPorFornecedorDireto(nomeForn) {{
            document.getElementById("FiltroFornecedor").value = nomeForn;
            aplicarFiltros();
            definirVisao('TABELA');
        }}

        function limparFiltroFornecedor() {{
            document.getElementById("FiltroFornecedor").value = "";
            aplicarFiltros();
        }}

        // 4. Mecânica Completa de Filtros (Datas + Comprador + Loja + Fornecedor + Produto + Status)
        function aplicarFiltros() {{
            const comprador = document.getElementById("FiltroComprador").value;
            const loja = document.getElementById("FiltroLoja").value;
            const termoForn = document.getElementById("FiltroFornecedor").value.trim().toUpperCase();
            const termoProd = document.getElementById("FiltroProduto").value.trim().toUpperCase();
            
            const dataDe = document.getElementById("FiltroDataDe").value;
            const dataAte = document.getElementById("FiltroDataAte").value;

            // Filtragem base (comprador, loja, fornecedor, produto, datas)
            let base = masterData.filter(d => {{
                // d[0] = Comprador, d[1] = Fornecedor, d[3] = Loja, d[4] = Data Emissão, d[7] = Cod Prod, d[8] = Descricao, d[13] = Status Entrega
                if (comprador !== "TODOS" && d[0] !== comprador) return false;
                if (loja !== "TODAS" && d[3] !== parseInt(loja)) return false;
                
                // Filtro de Data
                if (dataDe || dataAte) {{
                    const dtISO = converterDataParaISO(d[4]);
                    if (dtISO) {{
                        if (dataDe && dtISO < dataDe) return false;
                        if (dataAte && dtISO > dataAte) return false;
                    }} else {{
                        return false;
                    }}
                }}

                if (termoForn) {{
                    const fornStr = d[1].toUpperCase();
                    if (!fornStr.includes(termoForn)) return false;
                }}

                if (termoProd) {{
                    const codStr = String(d[7]);
                    const descStr = d[8].toUpperCase();
                    if (!codStr.includes(termoProd) && !descStr.includes(termoProd)) return false;
                }}

                return true;
            }});

            // Atualizar Diagnóstico Dinâmico com a base atual
            renderizarDiagnosticoDinamico(base);

            // Atualizar contadores nos botões de status
            atualizarContadoresBotoes(base);

            // Filtrar pelo Status Selecionado
            if (statusSelecionado === 'TODOS') {{
                dadosFiltrados = base;
            }} else {{
                dadosFiltrados = base.filter(d => d[13] === statusSelecionado);
            }}

            // Atualizar KPIs
            atualizarKPIs(dadosFiltrados);

            // Resetar Paginação
            paginaAtual = 1;
            reordenarDados();
            renderizarTabela();
        }}

        function atualizarContadoresBotoes(dataset) {{
            let cTodos = dataset.length;
            let cTot = 0, cAtraso = 0, cNaoAtend = 0, cAguard = 0;

            for (let i = 0; i < dataset.length; i++) {{
                const st = dataset[i][13];
                if (st === 'TOT_ATEND') cTot++;
                else if (st === 'ATRASO') cAtraso++;
                else if (st === 'NÃO_.ATENDIDO') cNaoAtend++;
                else if (st === 'AGUARDANDO') cAguard++;
            }}

            document.getElementById("cnt_TODOS").innerText = cTodos.toLocaleString('pt-BR');
            document.getElementById("cnt_TOT_ATEND").innerText = cTot.toLocaleString('pt-BR');
            document.getElementById("cnt_ATRASO").innerText = cAtraso.toLocaleString('pt-BR');
            document.getElementById("cnt_NAO_ATEND").innerText = cNaoAtend.toLocaleString('pt-BR');
            document.getElementById("cnt_AGUARDANDO").innerText = cAguard.toLocaleString('pt-BR');
        }}

        function mudarStatusEntrega(novoStatus) {{
            statusSelecionado = novoStatus;
            
            // Atualizar classes ativas nos botões
            document.querySelectorAll('.btn-status').forEach(btn => {{
                btn.classList.remove('active-all', 'active-tot', 'active-atraso', 'active-nao-atend', 'active-aguard');
            }});

            if (statusSelecionado === 'TODOS') {{
                document.getElementById('btn_status_TODOS').classList.add('active-all');
            }} else if (statusSelecionado === 'TOT_ATEND') {{
                document.getElementById('btn_status_TOT_ATEND').classList.add('active-tot');
            }} else if (statusSelecionado === 'ATRASO') {{
                document.getElementById('btn_status_ATRASO').classList.add('active-atraso');
            }} else if (statusSelecionado === 'NÃO_.ATENDIDO') {{
                document.getElementById('btn_status_NAO_ATEND').classList.add('active-nao-atend');
            }} else if (statusSelecionado === 'AGUARDANDO') {{
                document.getElementById('btn_status_AGUARDANDO').classList.add('active-aguard');
            }}

            aplicarFiltros();
        }}

        function atualizarKPIs(dataset) {{
            const totalLinhas = dataset.length;
            const setPedidos = new Set();
            let cTot = 0, cAtraso = 0, cNaoAtend = 0, cAguard = 0;

            for (let i = 0; i < totalLinhas; i++) {{
                setPedidos.add(dataset[i][2]);
                const st = dataset[i][13];
                if (st === 'TOT_ATEND') cTot++;
                else if (st === 'ATRASO') cAtraso++;
                else if (st === 'NÃO_.ATENDIDO') cNaoAtend++;
                else if (st === 'AGUARDANDO') cAguard++;
            }}

            document.getElementById("kpi_total_itens").innerText = totalLinhas.toLocaleString('pt-BR');
            document.getElementById("kpi_total_pedidos").innerText = setPedidos.size.toLocaleString('pt-BR') + " pedidos únicos";

            document.getElementById("kpi_tot_atend").innerText = cTot.toLocaleString('pt-BR');
            document.getElementById("kpi_perc_tot_atend").innerText = (totalLinhas > 0 ? (cTot / totalLinhas * 100).toFixed(1) : 0) + "% do total";

            document.getElementById("kpi_atraso").innerText = cAtraso.toLocaleString('pt-BR');
            document.getElementById("kpi_perc_atraso").innerText = (totalLinhas > 0 ? (cAtraso / totalLinhas * 100).toFixed(1) : 0) + "% do total";

            document.getElementById("kpi_nao_atend").innerText = cNaoAtend.toLocaleString('pt-BR');
            document.getElementById("kpi_perc_nao_atend").innerText = (totalLinhas > 0 ? (cNaoAtend / totalLinhas * 100).toFixed(1) : 0) + "% do total";

            document.getElementById("kpi_aguardando").innerText = cAguard.toLocaleString('pt-BR');
            document.getElementById("kpi_perc_aguardando").innerText = (totalLinhas > 0 ? (cAguard / totalLinhas * 100).toFixed(1) : 0) + "% no prazo";
        }}

        // 5. Ordenação e Renderização da Tabela
        function ordenarPor(colIndex) {{
            if (colunaOrdenacao === colIndex) {{
                direcaoAsc = !direcaoAsc;
            }} else {{
                colunaOrdenacao = colIndex;
                direcaoAsc = true;
            }}
            reordenarDados();
            renderizarTabela();
        }}

        function reordenarDados() {{
            dadosFiltrados.sort((a, b) => {{
                let valA = a[colunaOrdenacao];
                let valB = b[colunaOrdenacao];

                // Tratamento numérico
                if (typeof valA === 'number' && typeof valB === 'number') {{
                    return direcaoAsc ? valA - valB : valB - valA;
                }}

                // Tratamento de datas (DD/MM/YYYY)
                if (colunaOrdenacao === 4 || colunaOrdenacao === 5 || colunaOrdenacao === 6) {{
                    const parseData = (d) => {{
                        if (!d || d.length < 10) return 0;
                        const p = d.split('/');
                        return new Date(p[2], p[1] - 1, p[0]).getTime();
                    }};
                    const dtA = parseData(valA);
                    const dtB = parseData(valB);
                    return direcaoAsc ? dtA - dtB : dtB - dtA;
                }}

                valA = String(valA || '').toUpperCase();
                valB = String(valB || '').toUpperCase();
                if (valA < valB) return direcaoAsc ? -1 : 1;
                if (valA > valB) return direcaoAsc ? 1 : -1;
                return 0;
            }});
        }}

        function mudarLinhasPorPagina() {{
            linhasPorPagina = parseInt(document.getElementById("linhasPorPagina").value);
            paginaAtual = 1;
            renderizarTabela();
        }}

        function irParaPagina(num) {{
            if (num < 1 || num > totalPaginas) return;
            paginaAtual = num;
            renderizarTabela();
        }}

        function renderizarTabela() {{
            const total = dadosFiltrados.length;
            totalPaginas = Math.ceil(total / linhasPorPagina) || 1;
            if (paginaAtual > totalPaginas) paginaAtual = totalPaginas;

            const inicio = (paginaAtual - 1) * linhasPorPagina;
            const fim = Math.min(inicio + linhasPorPagina, total);
            const dadosPagina = dadosFiltrados.slice(inicio, fim);

            const tbody = document.getElementById("tabela-pedidos-body");
            tbody.innerHTML = "";

            if (dadosPagina.length === 0) {{
                tbody.innerHTML = `<tr><td colspan="15" class="text-center py-4 text-secondary" style="font-size: 0.8rem;">Nenhum registro encontrado para os filtros selecionados.</td></tr>`;
                document.getElementById("info-registros-filtrados").innerText = "Mostrando 0 de 0 registros";
                document.getElementById("texto-paginacao").innerText = "Página 0 de 0";
                return;
            }}

            let htmlBuffer = "";
            for (let i = 0; i < dadosPagina.length; i++) {{
                const r = dadosPagina[i];
                // r = [COMPRADOR, FORNECEDOR, NUMERO_PEDIDO, LOJA, DTA_EMISSAO, DTA_PREV, DTA_LIMITE, COD_PROD, DESCRICAO, EMB, QTD_PED, QTD_ATEND, PERC_ATEND, STATUS_ENTREGA, STATUS_PED]

                let badgeStatus = "";
                if (r[13] === 'TOT_ATEND') {{
                    badgeStatus = '<span class="status-badge badge-tot-atend">TOT_ATEND</span>';
                }} else if (r[13] === 'ATRASO') {{
                    badgeStatus = '<span class="status-badge badge-atraso">ATRASO</span>';
                }} else if (r[13] === 'NÃO_.ATENDIDO') {{
                    badgeStatus = '<span class="status-badge badge-nao-atend">NÃO_.ATENDIDO</span>';
                }} else {{
                    badgeStatus = '<span class="status-badge badge-aguardando">AGUARDANDO</span>';
                }}

                let badgePerc = "";
                if (r[12] >= 100) {{
                    badgePerc = `<span class="perc-badge perc-100">${{r[12].toFixed(0)}}%</span>`;
                }} else if (r[12] > 0) {{
                    badgePerc = `<span class="perc-badge perc-partial">${{r[12].toFixed(1)}}%</span>`;
                }} else {{
                    badgePerc = `<span class="perc-badge perc-zero">0%</span>`;
                }}

                htmlBuffer += `
                    <tr>
                        <td class="fw-semibold text-info" style="font-size: 0.76rem;">${{r[0]}}</td>
                        <td class="text-truncate" style="max-width: 240px; font-size: 0.76rem;" title="${{r[1]}}">${{r[1]}}</td>
                        <td style="text-align: center;" class="fw-bold text-white">${{r[2]}}</td>
                        <td style="text-align: center;"><span class="badge bg-secondary bg-opacity-25 text-light" style="font-size: 0.7rem;">L${{r[3]}}</span></td>
                        <td style="text-align: center;" class="text-secondary small">${{r[4]}}</td>
                        <td style="text-align: center;" class="text-warning small">${{r[5]}}</td>
                        <td style="text-align: center;" class="text-danger small">${{r[6]}}</td>
                        <td style="text-align: center;" class="fw-semibold text-white-50">${{r[7]}}</td>
                        <td class="text-truncate text-light fw-medium" style="max-width: 270px; font-size: 0.76rem;" title="${{r[8]}}">${{r[8]}}</td>
                        <td style="text-align: center;" class="text-secondary">${{r[9]}}</td>
                        <td style="text-align: right;" class="fw-bold text-white">${{r[10].toLocaleString('pt-BR')}}</td>
                        <td style="text-align: right;" class="fw-bold ${{r[11] > 0 ? 'text-success' : 'text-secondary'}}">${{r[11].toLocaleString('pt-BR')}}</td>
                        <td style="text-align: center;">${{badgePerc}}</td>
                        <td style="text-align: center;">${{badgeStatus}}</td>
                        <td style="text-align: center;">
                            <span class="badge ${{r[14] === 'ATIVO' ? 'bg-success bg-opacity-25 text-success' : 'bg-danger bg-opacity-25 text-danger'}}" style="font-size: 0.68rem;">${{r[14]}}</span>
                        </td>
                    </tr>
                `;
            }}

            tbody.innerHTML = htmlBuffer;

            // Atualizar textos e estados dos botões de paginação
            document.getElementById("info-registros-filtrados").innerText = `Mostrando ${{inicio + 1}} a ${{fim}} de ${{total.toLocaleString('pt-BR')}} registros filtrados`;
            document.getElementById("texto-paginacao").innerText = `Página ${{paginaAtual}} de ${{totalPaginas}} (${{total.toLocaleString('pt-BR')}} itens)`;

            document.getElementById("btn-primeira").disabled = (paginaAtual === 1);
            document.getElementById("btn-anterior").disabled = (paginaAtual === 1);
            document.getElementById("btn-proxima").disabled = (paginaAtual === totalPaginas);
            document.getElementById("btn-ultima").disabled = (paginaAtual === totalPaginas);
        }}

        // 6. Exportar CSV
        function exportarCSV() {{
            if (dadosFiltrados.length === 0) {{
                alert("Nenhum dado para exportar.");
                return;
            }}

            let csv = "COMPRADOR;FORNECEDOR;NUMERO_PEDIDO;LOJA_DESTINO;DATA_EMISSAO;DATA_PREV_ENTREGA;DATA_LIMITE_ENTREGA;CODIGO_PRODUTO;DESCRICAO;QTD_EMBALAGEM;QUANTIDADE_PEDIDA;QUANTIDADE_ATENDIDA;PERC_ATENDIMENTO;STATUS_ENTREGA;STATUS_PEDIDO\\n";
            
            dadosFiltrados.forEach(r => {{
                csv += `"${{r[0]}}";"${{r[1]}}";"${{r[2]}}";${{r[3]}};"${{r[4]}}";"${{r[5]}}";"${{r[6]}}";${{r[7]}};"${{r[8].replace(/"/g, '""')}}";${{r[9]}};${{r[10]}};${{r[11]}};${{r[12]}};"${{r[13]}}";"${{r[14]}}"\\n`;
            }});

            const blob = new Blob(["\\ufeff" + csv], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement("a");
            link.href = URL.createObjectURL(blob);
            link.setAttribute("download", `nivel_atendimento_pedidos_${{new Date().toISOString().slice(0,10)}}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }}

        // Inicialização
        document.addEventListener("DOMContentLoaded", () => {{
            aplicarFiltros();
            definirVisao('RANKING'); // Inicia exibindo exclusivamente o Ranking
        }});
    </script>
</body>
</html>
"""

    with open(html_output, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\nDashboard HTML gerado com sucesso em: {html_output}")

if __name__ == "__main__":
    gerar_dashboard()
