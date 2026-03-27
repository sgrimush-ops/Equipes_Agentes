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
arquivo_entrada = Path(r'c:\Users\Alessandro.soares.BAKLIZI\Downloads\Equipes_Agentes\Aplicativos\import_querys\query.parquet')

def principal():
    if not arquivo_entrada.exists():
        print(f"Erro: {arquivo_entrada} não encontrado.")
        return

    print("Carregando dados para painel detalhado...")
    df = pd.read_parquet(arquivo_entrada)

    # Saneamento (Regra 65)
    cols_saneamento = ['QUANTIDADE_DISPONIVEL', 'EMBL_COMPRA', 'EMBL_TRANSFERENCIA', 
                       'QTD_PEND_PEDCOMPRA', 'QUANTIDADE_ESTOQUE_MINIMO', 'QUANTIDADE_ESTOQUE_MAXIMO', 'QTD_VENDIDA_30D']
    
    for col in cols_saneamento:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if 'QTD_VENDIDA_30D' not in df.columns:
        df['QTD_VENDIDA_30D'] = 0

    print("Gerando flags booleanas...")
    df['is_rup_cd'] = (df['CODIGO_EMPRESA'] == 15) & ((df['QUANTIDADE_DISPONIVEL'] <= 0) | (df['QUANTIDADE_DISPONIVEL'] < df['EMBL_TRANSFERENCIA']))
    df['is_rup_loja'] = (df['CODIGO_EMPRESA'] != 15) & (df['QUANTIDADE_DISPONIVEL'] <= 0)
    df['is_rup_neg'] = (df['CODIGO_EMPRESA'] != 15) & (df['QUANTIDADE_DISPONIVEL'] < 0)
    df['is_rup_pend'] = (df['CODIGO_EMPRESA'] != 15) & (df['QUANTIDADE_DISPONIVEL'] <= 0) & (df['QTD_PEND_PEDCOMPRA'] > 0)
    df['is_est_pend'] = (df['QUANTIDADE_DISPONIVEL'] > 0) & (df['QTD_PEND_PEDCOMPRA'] > 0)

    print("Agregando métricas por Produto e Empresa...")
    df_grouped = df.groupby(['COMPRADOR', 'CODIGO_PRODUTO', 'DESCRICAO_PRODUTO', 'CODIGO_EMPRESA']).agg(
        ESTOQUE=('QUANTIDADE_DISPONIVEL', 'sum'),
        PEDIDOS=('QTD_PEND_PEDCOMPRA', 'sum'),
        VENDA=('QTD_VENDIDA_30D', 'sum'),
        RUP_CD=('is_rup_cd', 'max'),
        RUP_LOJA=('is_rup_loja', 'max'),
        RUP_NEG=('is_rup_neg', 'max'),
        RUP_PEND=('is_rup_pend', 'max'),
        EST_PEND=('is_est_pend', 'max')
    ).reset_index()

    print("Consolidando JSON por Produto...")
    produtos_dict = {}
    for _, row in df_grouped.iterrows():
        key = (row['COMPRADOR'], row['CODIGO_PRODUTO'], row['DESCRICAO_PRODUTO'])
        if key not in produtos_dict:
            produtos_dict[key] = {
                'COMPRADOR': row['COMPRADOR'],
                'CODIGO_PRODUTO': int(row['CODIGO_PRODUTO']),
                'DESCRICAO_PRODUTO': row['DESCRICAO_PRODUTO'],
                'LOJAS_MAP': {},
                'ESTOQUE_CD': 0,
                'PEDIDOS_CD': 0,
                'RUPTURA_CD': False
            }
        
        empresa = int(row['CODIGO_EMPRESA'])
        metrics = {
            'est': float(row['ESTOQUE']),
            'ped': float(row['PEDIDOS']),
            'vda': float(row['VENDA']),
            'r_l': bool(row['RUP_LOJA']),
            'r_n': bool(row['RUP_NEG']),
            'r_p': bool(row['RUP_PEND']),
            'e_p': bool(row['EST_PEND'])
        }
        
        if empresa == 15:
            produtos_dict[key]['ESTOQUE_CD'] = metrics['est']
            produtos_dict[key]['PEDIDOS_CD'] = metrics['ped']
            produtos_dict[key]['RUPTURA_CD'] = bool(row['RUP_CD'])
        else:
            produtos_dict[key]['LOJAS_MAP'][str(empresa)] = metrics

    final_data = list(produtos_dict.values())
    dados_json = json.dumps(final_data)

    compradores = sorted([c for c in df['COMPRADOR'].dropna().unique()])
    options_compradores = '<option value="TODOS">-- TODOS OS COMPRADORES --</option>'
    for c in compradores:
        options_compradores += f'<option value="{c}">{c}</option>'

    lojas = sorted([int(x) for x in df['CODIGO_EMPRESA'].dropna().unique() if x != 15])
    options_lojas = '<option value="TODAS">TODAS AS LOJAS</option>'
    for l in lojas:
        options_lojas += f'<option value="{l}">Loja {l}</option>'

    html_template = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Detalhado (Nível Tático)</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background-color: #f8f9fa; padding: 20px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            .card { border: none; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-radius: 12px; margin-bottom: 20px; padding: 20px; }
            .header-info { background: #2c3e50; color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
            .table-container { overflow-x: auto; max-height: 800px; }
            .table th { text-align: center; font-weight: bold; background-color: #f1f3f5; border-bottom: 2px solid #dee2e6; position: sticky; top: 0; z-index: 2; }
            .table td { text-align: center; vertical-align: middle; }
            .table th:first-child, .table td:first-child { text-align: left; padding-left: 15px; }
            .btn-metric { margin-right: 5px; margin-bottom: 10px; font-weight: 500; }
            .btn-rup-cd { background-color: #EF553B; color: white; border: none; }
            .btn-rup-loja { background-color: #636EFA; color: white; border: none; }
            .btn-rup-neg { background-color: #800080; color: white; border: none; }
            .btn-rup-pend { background-color: #FFD700; color: black; border: none; }
            .btn-est-pend { background-color: #00CC96; color: white; border: none; }
            .active-metric { outline: 3px solid #333; transform: scale(1.05); }
            .cd-column { background-color: #fff4f2 !important; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="header-info row align-items-center">
                <div class="col-md-6">
                    <h2>🔍 Detalhamento Tático de Produtos</h2>
                    <p class="mb-0">Atualizado em: [DATA_HOJE]</p>
                </div>
                <div class="col-md-3">
                    <label class="form-label mb-1">Selecionar Loja (Filtro Contextual)</label>
                    <select id="FiltroLoja" class="form-select form-select-lg" onchange="aplicarFiltros()">
                        [OPTIONS_LOJAS]
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label mb-1">Selecionar Comprador</label>
                    <select id="FiltroComprador" class="form-select form-select-lg" onchange="aplicarFiltros()">
                        [OPTIONS_COMPRADORES]
                    </select>
                </div>
            </div>

            <div class="card" id="filtros-container">
                <h5 class="mb-3">Selecione uma Visão:</h5>
                <div>
                    <button class="btn btn-metric btn-rup-cd" id="btn_rup_cd" onclick="mudarVisao('RUPTURA_CD')">Ruptura CD</button>
                    <button class="btn btn-metric btn-rup-loja" id="btn_rup_loja" onclick="mudarVisao('RUPTURA_LOJA')">Ruptura Loja</button>
                    <button class="btn btn-metric btn-rup-neg" id="btn_rup_neg" onclick="mudarVisao('RUPTURA_NEG')">Estoque Neg. Loja</button>
                    <button class="btn btn-metric btn-rup-pend" id="btn_rup_pend" onclick="mudarVisao('RUPTURA_PEND')">Rup. Loja Pend.</button>
                    <button class="btn btn-metric btn-est-pend" id="btn_est-pend" onclick="mudarVisao('ESTOQUE_PEND')">Est. com Ped.</button>
                    <span id="contador-linhas" class="ms-3 text-muted fw-bold"></span>
                </div>
            </div>
            
            <div class="card table-container" id="tabela-container">
                <table class="table table-striped table-hover align-middle">
                    <thead>
                        <tr>
                            <th>COD. PŔODUTO</th>
                            <th style="text-align: left;">DESCRIÇÃO</th>
                            <th id="col-dinamica">LOJAS</th>
                            <th class="cd-column">Estoque CD 15</th>
                            <th id="header-estoque">Estoque Local</th>
                            <th id="header-pedidos">Pedidos Local</th>
                            <th id="header-venda">Venda 30D (Local)</th>
                        </tr>
                    </thead>
                    <tbody id="tabela-body">
                    </tbody>
                </table>
            </div>
        </div>

        <script>
        const masterData = [DADOS_JSON];
        let dadosAtuais = [];
        let visaoAtual = '';

        function aplicarFiltros() {
            const comprador = document.getElementById("FiltroComprador").value;
            const loja = document.getElementById("FiltroLoja").value;
            
            if (comprador === "TODOS") {
                dadosAtuais = masterData;
            } else {
                dadosAtuais = masterData.filter(d => d.COMPRADOR === comprador);
            }
            
            // Atualizar headers da tabela
            document.getElementById("header-estoque").innerText = (loja === "TODAS") ? "Estoque TOTAL (Rede)" : "Estoque na Loja " + loja;
            document.getElementById("header-pedidos").innerText = (loja === "TODAS") ? "Pedidos TOTAL (Rede)" : "Pedidos na Loja " + loja;
            document.getElementById("header-venda").innerText = (loja === "TODAS") ? "Venda TOTAL (Rede)" : "Venda na Loja " + loja;

            if (!visaoAtual) {
                mudarVisao('RUPTURA_LOJA');
            } else {
                renderTable();
            }
        }

        function mudarVisao(novaVisao) {
            visaoAtual = novaVisao;
            document.querySelectorAll('.btn-metric').forEach(btn => btn.classList.remove('active-metric'));
            const btnMap = {'RUPTURA_CD': 'btn_rup_cd', 'RUPTURA_LOJA': 'btn_rup_loja', 'RUPTURA_NEG': 'btn_rup_neg', 'RUPTURA_PEND': 'btn_rup_pend', 'ESTOQUE_PEND': 'btn_est-pend'};
            document.getElementById(btnMap[visaoAtual]).classList.add('active-metric');
            renderTable();
        }

        function fmtNum(val) {
            if (val == null) return "0";
            if (typeof val === 'number') {
                if (val % 1 !== 0) return val.toFixed(2).replace('.', ',');
                return val.toLocaleString('pt-BR');
            }
            return val;
        }

        function renderTable() {
            const lojaSel = document.getElementById("FiltroLoja").value;
            let dFinal = [];

            function match(prod) {
                if (visaoAtual === 'RUPTURA_CD') return prod.RUPTURA_CD;
                const lojasMap = prod.LOJAS_MAP;
                const flagMap = {'RUPTURA_LOJA': 'r_l', 'RUPTURA_NEG': 'r_n', 'RUPTURA_PEND': 'r_p', 'ESTOQUE_PEND': 'e_p'};
                const flag = flagMap[visaoAtual];
                if (lojaSel === "TODAS") {
                    return Object.values(lojasMap).some(m => m[flag]);
                } else {
                    return lojasMap[lojaSel] && lojasMap[lojaSel][flag];
                }
            }

            dFinal = dadosAtuais.filter(match);
            dFinal.sort((a, b) => {
                let vA = 0, vB = 0;
                if (lojaSel === "TODAS") {
                    vA = Object.values(a.LOJAS_MAP).reduce((s, m) => s + (m.vda || 0), 0);
                    vB = Object.values(b.LOJAS_MAP).reduce((s, m) => s + (m.vda || 0), 0);
                } else {
                    vA = a.LOJAS_MAP[lojaSel] ? a.LOJAS_MAP[lojaSel].vda : 0;
                    vB = b.LOJAS_MAP[lojaSel] ? b.LOJAS_MAP[lojaSel].vda : 0;
                }
                return vB - vA;
            });

            document.getElementById("contador-linhas").innerText = `Exibindo: ${dFinal.length} SKUs`;

            let tbody = '';
            // Limite de 2000 linhas para performance se for visão global
            const exibe = dFinal.slice(0, 2000);

            exibe.forEach(row => {
                let est_loc = 0, ped_loc = 0, vda_loc = 0;
                let lojas_list = "";
                const flagMap = {'RUPTURA_LOJA': 'r_l', 'RUPTURA_NEG': 'r_n', 'RUPTURA_PEND': 'r_p', 'ESTOQUE_PEND': 'e_p'};
                const flag = flagMap[visaoAtual] || 'r_l';

                if (lojaSel === "TODAS") {
                    Object.keys(row.LOJAS_MAP).forEach(lId => {
                        const m = row.LOJAS_MAP[lId];
                        est_loc += m.est;
                        ped_loc += m.ped;
                        vda_loc += m.vda;
                        if (m[flag]) lojas_list += (lojas_list ? ", " : "") + lId;
                    });
                } else {
                    const m = row.LOJAS_MAP[lojaSel] || {est:0, ped:0, vda:0};
                    est_loc = m.est;
                    ped_loc = m.ped;
                    vda_loc = m.vda;
                    lojas_list = lojaSel;
                }

                tbody += `<tr>
                    <td class="fw-bold">${row.CODIGO_PRODUTO}</td>
                    <td style="text-align: left;">${row.DESCRICAO_PRODUTO}</td>
                    <td><span class="fw-bold text-muted" title="${lojas_list}">${lojas_list.length > 30 ? lojas_list.substring(0,27)+'...' : lojas_list}</span></td>
                    <td class="cd-column">${fmtNum(row.ESTOQUE_CD)}</td>
                    <td class="${est_loc < 0 ? 'text-danger fw-bold' : ''}">${fmtNum(est_loc)}</td>
                    <td>${fmtNum(ped_loc)}</td>
                    <td class="text-primary fw-bold">${fmtNum(vda_loc)}</td>
                </tr>`;
            });
            
            document.getElementById("tabela-body").innerHTML = tbody;
            if (dFinal.length > 2000) {
                document.getElementById("tabela-body").innerHTML += `<tr><td colspan="7" class="text-center text-muted p-3">Exibindo apenas os 2000 itens com maior venda para melhor performance. Refine o filtro para ver mais.</td></tr>`;
            }
        }
        window.onload = aplicarFiltros;
        </script>
    </body>
    </html>
    """
    html_template = html_template.replace('[DATA_HOJE]', date.today().strftime('%d/%m/%Y'))
    html_template = html_template.replace('[OPTIONS_COMPRADORES]', options_compradores)
    html_template = html_template.replace('[OPTIONS_LOJAS]', options_lojas)
    html_template = html_template.replace('[DADOS_JSON]', dados_json)

    output_path = base_dir / "dashboard_detalhado.html"
    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(html_template)
    
    print(f"Dashboard Detalhado gerado com sucesso em: {output_path}")

if __name__ == '__main__':
    principal()
