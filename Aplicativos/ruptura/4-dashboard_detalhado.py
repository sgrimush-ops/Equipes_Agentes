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
arquivo_entrada = Path(r'C:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\import_querys\query.parquet')

def principal():
    if not arquivo_entrada.exists():
        print(f"Erro: {arquivo_entrada} não encontrado.")
        return

    print("Carregando dados para painel detalhado...")
    df = pd.read_parquet(arquivo_entrada)

    # Salvar cópia detalhada no histórico automaticamente
    dir_historico = base_dir / "historico_ruptura"
    dir_historico.mkdir(exist_ok=True)
    arquivo_detalhado = dir_historico / f"ruptura_snapshot_{date.today().strftime('%Y-%m-%d')}_detalhe.parquet"
    if not arquivo_detalhado.exists():
        df.to_parquet(arquivo_detalhado, index=False)
        print(f"Snapshot detalhado salvo no histórico: {arquivo_detalhado}")

    if 'QTD_VENDIDA' not in df.columns and 'QTD_VENDIDA_PERIODO' in df.columns:
        df['QTD_VENDIDA'] = df['QTD_VENDIDA_PERIODO']

    # Saneamento (Regra 65)
    cols_saneamento = ['QUANTIDADE_DISPONIVEL', 'EMBL_COMPRA', 'EMBL_TRANSFERENCIA', 
                       'QTD_PEND_PEDCOMPRA', 'QTD_PEND_PEDTRANSF', 'QUANTIDADE_ESTOQUE_MINIMO', 'QUANTIDADE_ESTOQUE_MAXIMO', 'QTD_VENDIDA']
    
    for col in cols_saneamento:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if 'QTD_VENDIDA' not in df.columns:
        df['QTD_VENDIDA'] = 0

    print("Gerando flags booleanas...")
    df['is_rup_cd15'] = (df['CODIGO_EMPRESA'] == 15) & (df['FORMA_ABASTECIMENTO'].isin(['M', 'C'])) & ((df['QUANTIDADE_DISPONIVEL'] <= 0) | (df['QUANTIDADE_DISPONIVEL'] < df['EMBL_TRANSFERENCIA']))
    df['is_rup_cd16'] = (df['CODIGO_EMPRESA'] == 16) & (df['FORMA_ABASTECIMENTO'].isin(['M', 'C'])) & ((df['QUANTIDADE_DISPONIVEL'] <= 0) | (df['QUANTIDADE_DISPONIVEL'] < df['EMBL_TRANSFERENCIA']))
    
    df['is_rup_loja'] = (~df['CODIGO_EMPRESA'].isin([15, 16])) & (df['QUANTIDADE_DISPONIVEL'] <= 0)
    df['is_rup_neg'] = (~df['CODIGO_EMPRESA'].isin([15, 16])) & (df['QUANTIDADE_DISPONIVEL'] < 0)
    df['is_rup_cross'] = (~df['CODIGO_EMPRESA'].isin([15, 16])) & (df['QUANTIDADE_DISPONIVEL'] <= 0) & (df['FORMA_ABASTECIMENTO'] == 'I')
    
    if 'QTD_PEND_PEDTRANSF' in df.columns:
        df['is_rup_pend'] = (~df['CODIGO_EMPRESA'].isin([15, 16])) & (df['QUANTIDADE_DISPONIVEL'] <= 0) & ((df['QTD_PEND_PEDCOMPRA'] > 0) | (df['QTD_PEND_PEDTRANSF'] > 0))
    else:
        df['is_rup_pend'] = (~df['CODIGO_EMPRESA'].isin([15, 16])) & (df['QUANTIDADE_DISPONIVEL'] <= 0) & (df['QTD_PEND_PEDCOMPRA'] > 0)

    print("Agregando métricas por Produto e Empresa...")
    if 'QTD_PEND_PEDTRANSF' in df.columns:
        df_grouped = df.groupby(['COMPRADOR', 'CODIGO_PRODUTO', 'DESCRICAO_PRODUTO', 'CODIGO_EMPRESA']).agg(
            ESTOQUE=('QUANTIDADE_DISPONIVEL', 'sum'),
            PEDIDOS_COMPRA=('QTD_PEND_PEDCOMPRA', 'sum'),
            PEDIDOS_TRANSF=('QTD_PEND_PEDTRANSF', 'sum'),
            VENDA=('QTD_VENDIDA', 'sum'),
            RUP_CD15=('is_rup_cd15', 'max'),
            RUP_CD16=('is_rup_cd16', 'max'),
            RUP_LOJA=('is_rup_loja', 'max'),
            RUP_NEG=('is_rup_neg', 'max'),
            RUP_PEND=('is_rup_pend', 'max'),
            RUP_CROSS=('is_rup_cross', 'max')
        ).reset_index()
        df_grouped['PEDIDOS'] = df_grouped['PEDIDOS_COMPRA'] + df_grouped['PEDIDOS_TRANSF']
    else:
        df_grouped = df.groupby(['COMPRADOR', 'CODIGO_PRODUTO', 'DESCRICAO_PRODUTO', 'CODIGO_EMPRESA']).agg(
            ESTOQUE=('QUANTIDADE_DISPONIVEL', 'sum'),
            PEDIDOS_COMPRA=('QTD_PEND_PEDCOMPRA', 'sum'),
            VENDA=('QTD_VENDIDA', 'sum'),
            RUP_CD15=('is_rup_cd15', 'max'),
            RUP_CD16=('is_rup_cd16', 'max'),
            RUP_LOJA=('is_rup_loja', 'max'),
            RUP_NEG=('is_rup_neg', 'max'),
            RUP_PEND=('is_rup_pend', 'max'),
            RUP_CROSS=('is_rup_cross', 'max')
        ).reset_index()
        df_grouped['PEDIDOS_TRANSF'] = 0.0
        df_grouped['PEDIDOS'] = df_grouped['PEDIDOS_COMPRA']

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
                'ESTOQUE_CD15': 0,
                'PEDIDOS_CD15_TRANSF': 0,
                'PEDIDOS_CD15_COMPRA': 0,
                'VENDA_CD15': 0,
                'RUPTURA_CD15': False,
                'ESTOQUE_CD16': 0,
                'PEDIDOS_CD16_TRANSF': 0,
                'PEDIDOS_CD16_COMPRA': 0,
                'VENDA_CD16': 0,
                'RUPTURA_CD16': False,
                'BASE_LOJA': 0
            }
        
        empresa = int(row['CODIGO_EMPRESA'])
        metrics = {
            'est': float(row['ESTOQUE']),
            'ped_tran': float(row['PEDIDOS_TRANSF']),
            'ped_comp': float(row['PEDIDOS_COMPRA']),
            'vda': float(row['VENDA']),
            'r_l': bool(row['RUP_LOJA']),
            'r_n': bool(row['RUP_NEG']),
            'r_p': bool(row['RUP_PEND']),
            'r_c': bool(row['RUP_CROSS'])
        }
        
        if empresa == 15:
            produtos_dict[key]['ESTOQUE_CD15'] = metrics['est']
            produtos_dict[key]['PEDIDOS_CD15_TRANSF'] = metrics['ped_tran']
            produtos_dict[key]['PEDIDOS_CD15_COMPRA'] = metrics['ped_comp']
            produtos_dict[key]['VENDA_CD15'] = metrics['vda']
            produtos_dict[key]['RUPTURA_CD15'] = bool(row['RUP_CD15'])
        elif empresa == 16:
            produtos_dict[key]['ESTOQUE_CD16'] = metrics['est']
            produtos_dict[key]['PEDIDOS_CD16_TRANSF'] = metrics['ped_tran']
            produtos_dict[key]['PEDIDOS_CD16_COMPRA'] = metrics['ped_comp']
            produtos_dict[key]['VENDA_CD16'] = metrics['vda']
            produtos_dict[key]['RUPTURA_CD16'] = bool(row['RUP_CD16'])
        else:
            produtos_dict[key]['LOJAS_MAP'][str(empresa)] = metrics

    # Calcular Base Loja (quantidade de filiais onde o produto está ativo)
    for p in produtos_dict.values():
        p['BASE_LOJA'] = len(p['LOJAS_MAP'])

    final_data = list(produtos_dict.values())
    dados_json = json.dumps(final_data)

    compradores = sorted([c for c in df['COMPRADOR'].dropna().unique()])
    options_compradores = '<option value="TODOS">-- TODOS OS COMPRADORES --</option>'
    for c in compradores:
        options_compradores += f'<option value="{c}">{c}</option>'

    lojas = sorted([int(x) for x in df['CODIGO_EMPRESA'].dropna().unique()])
    options_lojas = '<option value="TODAS">TODAS AS LOJAS</option>'
    for l in lojas:
        if l == 15:
            options_lojas += f'<option value="{l}">Loja 15 (CD 15)</option>'
        elif l == 16:
            options_lojas += f'<option value="{l}">Loja 16 (CD 16)</option>'
        else:
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
            .btn-rup-cd15 { background-color: #EF553B; color: white; border: none; }
            .btn-rup-cd16 { background-color: #C62828; color: white; border: none; }
            .btn-rup-loja { background-color: #636EFA; color: white; border: none; }
            .btn-rup-neg { background-color: #800080; color: white; border: none; }
            .btn-rup-pend { background-color: #FFD700; color: black; border: none; }
            .btn-cross { background-color: #8E24AA; color: white; border: none; }
            .active-metric { outline: 3px solid #333; transform: scale(1.05); }
            .cd15-column { background-color: #ffebee !important; font-weight: bold; color: #b71c1c; }
            .cd16-column { background-color: #fbe9e7 !important; font-weight: bold; color: #bf360c; }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="header-info row align-items-center">
                <div class="col-md-6">
                    <h2>🔍 Detalhamento Tático de Produtos Multi-CD</h2>
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
                    <button class="btn btn-metric btn-rup-cd15" id="btn_rup_cd15" onclick="mudarVisao('RUPTURA_CD15')">Ruptura CD 15</button>
                    <button class="btn btn-metric btn-rup-cd16" id="btn_rup_cd16" onclick="mudarVisao('RUPTURA_CD16')">Ruptura CD 16</button>
                    <button class="btn btn-metric btn-rup-loja" id="btn_rup_loja" onclick="mudarVisao('RUPTURA_LOJA')">Ruptura Loja</button>
                    <button class="btn btn-metric btn-rup-neg" id="btn_rup_neg" onclick="mudarVisao('RUPTURA_NEG')">Estoque Neg. Loja</button>
                    <button class="btn btn-metric btn-rup-pend" id="btn_rup_pend" onclick="mudarVisao('RUPTURA_PEND')">Rup. Loja Pend.</button>
                    <button class="btn btn-metric btn-cross" id="btn_cross" onclick="mudarVisao('CROSSDOCKING')">Crossdocking</button>
                    <span id="contador-linhas" class="ms-3 text-muted fw-bold"></span>
                </div>
            </div>
            
            <div class="card table-container" id="tabela-container">
                <table class="table table-striped table-hover align-middle">
                    <thead>
                        <tr>
                            <th>COD. PRODUTO</th>
                            <th style="text-align: left;">DESCRIÇÃO</th>
                            <th>Base Lojas</th>
                            <th id="col-dinamica">LOJAS (Filtro)</th>
                            <th class="cd15-column">Estoque CD 15</th>
                            <th class="cd16-column">Estoque CD 16</th>
                            <th id="header-estoque">Estoque Local</th>
                            <th id="header-pedidos-transf">Pedidos Trans (Local)</th>
                            <th id="header-pedidos-forn">Pedidos Forn (Local)</th>
                            <th id="header-venda">Qtd. Vendida (Local)</th>
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
            document.getElementById("header-estoque").innerText = (loja === "TODAS") ? "Estoque TOTAL (Rede)" : (loja === "15" ? "Estoque CD 15" : (loja === "16" ? "Estoque CD 16" : "Estoque na Loja " + loja));
            document.getElementById("header-pedidos-transf").innerText = (loja === "TODAS") ? "Pedidos Trans (Rede)" : "Pedidos Trans " + (loja === "15" ? "CD 15" : (loja === "16" ? "CD 16" : "Loja " + loja));
            document.getElementById("header-pedidos-forn").innerText = (loja === "TODAS") ? "Pedidos Forn (Rede)" : "Pedidos Forn " + (loja === "15" ? "CD 15" : (loja === "16" ? "CD 16" : "Loja " + loja));
            document.getElementById("header-venda").innerText = (loja === "TODAS") ? "Qtd. Vendida (Rede)" : "Qtd. Vendida " + (loja === "15" ? "CD 15" : (loja === "16" ? "CD 16" : "Loja " + loja));

            if (!visaoAtual) {
                mudarVisao('RUPTURA_LOJA');
            } else {
                renderTable();
            }
        }

        function mudarVisao(novaVisao) {
            visaoAtual = novaVisao;
            document.querySelectorAll('.btn-metric').forEach(btn => btn.classList.remove('active-metric'));
            const btnMap = {
                'RUPTURA_CD15': 'btn_rup_cd15',
                'RUPTURA_CD16': 'btn_rup_cd16',
                'RUPTURA_LOJA': 'btn_rup_loja',
                'RUPTURA_NEG': 'btn_rup_neg',
                'RUPTURA_PEND': 'btn_rup_pend',
                'CROSSDOCKING': 'btn_cross'
            };
            if (btnMap[visaoAtual]) {
                document.getElementById(btnMap[visaoAtual]).classList.add('active-metric');
            }
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
                if (visaoAtual === 'RUPTURA_CD15') return prod.RUPTURA_CD15;
                if (visaoAtual === 'RUPTURA_CD16') return prod.RUPTURA_CD16;
                
                if (lojaSel === "15") {
                    const has_neg = prod.ESTOQUE_CD15 < 0;
                    const has_pend = prod.PEDIDOS_CD15_COMPRA > 0 || prod.PEDIDOS_CD15_TRANSF > 0;
                    if (visaoAtual === 'RUPTURA_LOJA') return prod.RUPTURA_CD15;
                    if (visaoAtual === 'RUPTURA_NEG') return has_neg;
                    if (visaoAtual === 'RUPTURA_PEND') return prod.RUPTURA_CD15 && has_pend;
                    if (visaoAtual === 'CROSSDOCKING') return false;
                } else if (lojaSel === "16") {
                    const has_neg = prod.ESTOQUE_CD16 < 0;
                    const has_pend = prod.PEDIDOS_CD16_COMPRA > 0 || prod.PEDIDOS_CD16_TRANSF > 0;
                    if (visaoAtual === 'RUPTURA_LOJA') return prod.RUPTURA_CD16;
                    if (visaoAtual === 'RUPTURA_NEG') return has_neg;
                    if (visaoAtual === 'RUPTURA_PEND') return prod.RUPTURA_CD16 && has_pend;
                    if (visaoAtual === 'CROSSDOCKING') return false;
                }
                
                const lojasMap = prod.LOJAS_MAP;
                const flagMap = {'RUPTURA_LOJA': 'r_l', 'RUPTURA_NEG': 'r_n', 'RUPTURA_PEND': 'r_p', 'CROSSDOCKING': 'r_c'};
                const flag = flagMap[visaoAtual];
                if (lojaSel === "TODAS") {
                    return Object.values(lojasMap).some(m => m[flag]);
                } else {
                    return lojasMap[lojaSel] && lojasMap[lojaSel][flag];
                }
            }

            dFinal = dadosAtuais.filter(match);
            dFinal.sort((a, b) => {
                let baseA = a.BASE_LOJA !== undefined ? a.BASE_LOJA : Object.keys(a.LOJAS_MAP || {}).length;
                let baseB = b.BASE_LOJA !== undefined ? b.BASE_LOJA : Object.keys(b.LOJAS_MAP || {}).length;
                if (baseB !== baseA) {
                    return baseB - baseA;
                }
                let vA = 0, vB = 0;
                if (lojaSel === "TODAS") {
                    vA = Object.values(a.LOJAS_MAP).reduce((s, m) => s + (m.vda || 0), 0) + (a.VENDA_CD15 || 0) + (a.VENDA_CD16 || 0);
                    vB = Object.values(b.LOJAS_MAP).reduce((s, m) => s + (m.vda || 0), 0) + (b.VENDA_CD15 || 0) + (b.VENDA_CD16 || 0);
                } else if (lojaSel === "15") {
                    vA = a.VENDA_CD15 || 0;
                    vB = b.VENDA_CD15 || 0;
                } else if (lojaSel === "16") {
                    vA = a.VENDA_CD16 || 0;
                    vB = b.VENDA_CD16 || 0;
                } else {
                    vA = a.LOJAS_MAP[lojaSel] ? a.LOJAS_MAP[lojaSel].vda : 0;
                    vB = b.LOJAS_MAP[lojaSel] ? b.LOJAS_MAP[lojaSel].vda : 0;
                }
                return vB - vA;
            });

            document.getElementById("contador-linhas").innerText = `Exibindo: ${dFinal.length} SKUs`;

            let tbody = '';
            const exibe = dFinal.slice(0, 2000);

            exibe.forEach(row => {
                let est_loc = 0, ped_transf_loc = 0, ped_forn_loc = 0, vda_loc = 0;
                let lojas_list = "";
                const flagMap = {'RUPTURA_LOJA': 'r_l', 'RUPTURA_NEG': 'r_n', 'RUPTURA_PEND': 'r_p', 'CROSSDOCKING': 'r_c'};
                const flag = flagMap[visaoAtual] || 'r_l';

                if (lojaSel === "TODAS") {
                    Object.keys(row.LOJAS_MAP).forEach(lId => {
                        const m = row.LOJAS_MAP[lId];
                        est_loc += m.est;
                        ped_transf_loc += (m.ped_tran || 0);
                        ped_forn_loc += (m.ped_comp || 0);
                        vda_loc += m.vda;
                        if (m[flag]) lojas_list += (lojas_list ? ", " : "") + lId;
                    });
                    ped_forn_loc += ((row.PEDIDOS_CD15_COMPRA || 0) + (row.PEDIDOS_CD16_COMPRA || 0));
                    vda_loc += ((row.VENDA_CD15 || 0) + (row.VENDA_CD16 || 0));
                    
                    if (visaoAtual === 'RUPTURA_CD15' && row.RUPTURA_CD15) {
                        lojas_list += (lojas_list ? ", " : "") + "CD 15";
                    } else if (visaoAtual === 'RUPTURA_CD16' && row.RUPTURA_CD16) {
                        lojas_list += (lojas_list ? ", " : "") + "CD 16";
                    }
                } else if (lojaSel === "15") {
                    est_loc = row.ESTOQUE_CD15 || 0;
                    ped_transf_loc = row.PEDIDOS_CD15_TRANSF || 0;
                    ped_forn_loc = row.PEDIDOS_CD15_COMPRA || 0;
                    vda_loc = row.VENDA_CD15 || 0;
                    lojas_list = "CD 15";
                } else if (lojaSel === "16") {
                    est_loc = row.ESTOQUE_CD16 || 0;
                    ped_transf_loc = row.PEDIDOS_CD16_TRANSF || 0;
                    ped_forn_loc = row.PEDIDOS_CD16_COMPRA || 0;
                    vda_loc = row.VENDA_CD16 || 0;
                    lojas_list = "CD 16";
                } else {
                    const m = row.LOJAS_MAP[lojaSel] || {est:0, ped_tran:0, ped_comp:0, vda:0};
                    est_loc = m.est;
                    ped_transf_loc = m.ped_tran || 0;
                    ped_forn_loc = m.ped_comp || 0;
                    vda_loc = m.vda;
                    lojas_list = lojaSel;
                }

                const base_lojas_count = row.BASE_LOJA !== undefined ? row.BASE_LOJA : Object.keys(row.LOJAS_MAP).length;

                tbody += `<tr>
                    <td class="fw-bold">${row.CODIGO_PRODUTO}</td>
                    <td style="text-align: left;">${row.DESCRICAO_PRODUTO}</td>
                    <td class="fw-bold text-secondary">${base_lojas_count}</td>
                    <td><span class="fw-bold text-muted" title="${lojas_list}">${lojas_list.length > 30 ? lojas_list.substring(0,27)+'...' : lojas_list}</span></td>
                    <td class="cd15-column">${fmtNum(row.ESTOQUE_CD15)}</td>
                    <td class="cd16-column">${fmtNum(row.ESTOQUE_CD16)}</td>
                    <td class="${est_loc < 0 ? 'text-danger fw-bold' : ''}">${fmtNum(est_loc)}</td>
                    <td>${fmtNum(ped_transf_loc)}</td>
                    <td>${fmtNum(ped_forn_loc)}</td>
                    <td class="text-primary fw-bold">${fmtNum(vda_loc)}</td>
                </tr>`;
            });
            
            document.getElementById("tabela-body").innerHTML = tbody;
            if (dFinal.length > 2000) {
                document.getElementById("tabela-body").innerHTML += `<tr><td colspan="10" class="text-center text-muted p-3">Exibindo apenas os 2000 itens com maior base de loja para melhor performance. Refine o filtro para ver mais.</td></tr>`;
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

    # ===============================
    # GERAÇÃO DE EXCELS POR COMPRADOR
    # ===============================
    print("Gerando planilhas de Excel individuais por comprador...")
    pasta_excel = base_dir / "excel_comprador"
    pasta_excel.mkdir(exist_ok=True)
    
    import datetime
    import re
    hoje_str = datetime.date.today().strftime('%d-%m-%Y')

    # Agrupar itens finais por comprador
    comprador_data = {}
    for prod in final_data:
        comp = str(prod['COMPRADOR']).strip()
        if comp not in comprador_data:
            comprador_data[comp] = []
        comprador_data[comp].append(prod)
        
    for comp, produtos in comprador_data.items():
        if not comp or comp.upper() == "NAN":
            continue
            
        rows_excel = []
        for p in produtos:
            lojas_rup = [l for l, m in p['LOJAS_MAP'].items() if m['r_l']]
            lojas_neg = [l for l, m in p['LOJAS_MAP'].items() if m['r_n']]
            lojas_pend = [l for l, m in p['LOJAS_MAP'].items() if m['r_p']]
            lojas_cross = [l for l, m in p['LOJAS_MAP'].items() if m.get('r_c', False)]
            
            est_loc = sum(m['est'] for m in p['LOJAS_MAP'].values())
            ped_transf_loc = sum(m.get('ped_tran', 0) for m in p['LOJAS_MAP'].values())
            ped_forn_loc = sum(m.get('ped_comp', 0) for m in p['LOJAS_MAP'].values())
            vda_loc = sum(m['vda'] for m in p['LOJAS_MAP'].values())
            
            rows_excel.append({
                'Cód. Produto': p['CODIGO_PRODUTO'],
                'Descrição': p['DESCRICAO_PRODUTO'],
                'Base Lojas': len(p['LOJAS_MAP']),
                'Ruptura CD 15?': 'SIM' if p['RUPTURA_CD15'] else 'NÃO',
                'Estoque CD 15': p['ESTOQUE_CD15'],
                'Ruptura CD 16?': 'SIM' if p['RUPTURA_CD16'] else 'NÃO',
                'Estoque CD 16': p['ESTOQUE_CD16'],
                'Ped. Forn CDs': p.get('PEDIDOS_CD15_COMPRA', 0) + p.get('PEDIDOS_CD16_COMPRA', 0),
                'Lojas c/ Ruptura': ", ".join(lojas_rup),
                'Lojas c/ Est. Negativo': ", ".join(lojas_neg),
                'Lojas c/ Rup. Pendente': ", ".join(lojas_pend),
                'Lojas c/ Crossdocking': ", ".join(lojas_cross),
                'Estoque Local (Rede)': est_loc,
                'Ped. Transf Local (Rede)': ped_transf_loc,
                'Ped. Forn Local (Rede)': ped_forn_loc,
                'Qtd. Vendida (Rede)': vda_loc
            })
            
        df_comp = pd.DataFrame(rows_excel)
        
        mask_tem_problema = (
            (df_comp['Ruptura CD 15?'] == 'SIM') |
            (df_comp['Ruptura CD 16?'] == 'SIM') |
            (df_comp['Lojas c/ Ruptura'] != "") |
            (df_comp['Lojas c/ Est. Negativo'] != "") |
            (df_comp['Lojas c/ Rup. Pendente'] != "") |
            (df_comp['Lojas c/ Crossdocking'] != "")
        )
        df_comp_filtrado = df_comp[mask_tem_problema]
        
        if not df_comp_filtrado.empty:
            primeiro_nome = comp.split(' ')[0].upper()
            primeiro_nome = re.sub(r'[\\/*?:"<>|]', "", primeiro_nome)
            file_name = f"{primeiro_nome}_{hoje_str}.xlsx"
            file_path = pasta_excel / file_name
            
            df_comp_filtrado = df_comp_filtrado.sort_values(by=['Base Lojas', 'Qtd. Vendida (Rede)'], ascending=[False, False])
            df_comp_filtrado.to_excel(file_path, index=False)

    print(f"Todas as planilhas geradas em: {pasta_excel}")

if __name__ == '__main__':
    principal()
