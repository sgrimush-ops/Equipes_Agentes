import os
import json
import pandas as pd
from pathlib import Path
from datetime import date

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

    # Saneamento
    cols_saneamento = ['QUANTIDADE_DISPONIVEL', 'EMBL_COMPRA', 'EMBL_TRANSFERENCIA', 
                       'QTD_PEND_PEDCOMPRA', 'QUANTIDADE_ESTOQUE_MINIMO', 'QUANTIDADE_ESTOQUE_MAXIMO', 'QTD_VENDIDA_30D']
    
    for col in cols_saneamento:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Preenchendo NaNs caso falte coluna
    if 'QTD_VENDIDA_30D' not in df.columns:
        df['QTD_VENDIDA_30D'] = 0

    print("Gerando flags booleanas por produto-loja...")
    df['is_rup_cd'] = (df['CODIGO_EMPRESA'] == 15) & ((df['QUANTIDADE_DISPONIVEL'] <= 0) | (df['QUANTIDADE_DISPONIVEL'] < df['EMBL_TRANSFERENCIA']))
    df['is_rup_loja'] = (df['CODIGO_EMPRESA'] != 15) & (df['QUANTIDADE_DISPONIVEL'] <= 0)
    df['is_rup_neg'] = (df['CODIGO_EMPRESA'] != 15) & (df['QUANTIDADE_DISPONIVEL'] < 0)
    df['is_rup_pend'] = (df['CODIGO_EMPRESA'] != 15) & (df['QUANTIDADE_DISPONIVEL'] <= 0) & (df['QTD_PEND_PEDCOMPRA'] > 0)
    df['is_est_pend'] = (df['QUANTIDADE_DISPONIVEL'] > 0) & (df['QTD_PEND_PEDCOMPRA'] > 0)

    print("Agregando métricas bases por Produto...")
    df_base = df.groupby(['COMPRADOR', 'CODIGO_PRODUTO', 'DESCRICAO_PRODUTO']).agg(
        ESTOQUE_TOTAL=('QUANTIDADE_DISPONIVEL', 'sum'),
        PEDIDOS_PEND=('QTD_PEND_PEDCOMPRA', 'sum'),
        VENDA_30D=('QTD_VENDIDA_30D', 'sum'),
        RUPTURA_CD=('is_rup_cd', 'max') 
    ).reset_index()

    print("Consolidando listas de Lojas...")
    def get_lojas_str(df_filtered):
        if df_filtered.empty:
            return pd.DataFrame(columns=['COMPRADOR', 'CODIGO_PRODUTO', 'LOJAS'])
        g = df_filtered.groupby(['COMPRADOR', 'CODIGO_PRODUTO'])['CODIGO_EMPRESA'].apply(
            lambda x: ', '.join(sorted(x.astype(int).astype(str).unique(), key=lambda i: int(i)))
        ).reset_index(name='LOJAS')
        return g

    g_rup_loja = get_lojas_str(df[df['is_rup_loja']])
    g_rup_loja.rename(columns={'LOJAS': 'LOJAS_RUP'}, inplace=True)

    g_rup_neg = get_lojas_str(df[df['is_rup_neg']])
    g_rup_neg.rename(columns={'LOJAS': 'LOJAS_NEG'}, inplace=True)

    g_rup_pend = get_lojas_str(df[df['is_rup_pend']])
    g_rup_pend.rename(columns={'LOJAS': 'LOJAS_RUP_PEND'}, inplace=True)

    g_est_pend = get_lojas_str(df[df['is_est_pend']])
    g_est_pend.rename(columns={'LOJAS': 'LOJAS_EST_PEND'}, inplace=True)

    print("Realizando left joins para montar dataset final...")
    df_final = df_base.merge(g_rup_loja, on=['COMPRADOR', 'CODIGO_PRODUTO'], how='left')
    df_final = df_final.merge(g_rup_neg, on=['COMPRADOR', 'CODIGO_PRODUTO'], how='left')
    df_final = df_final.merge(g_rup_pend, on=['COMPRADOR', 'CODIGO_PRODUTO'], how='left')
    df_final = df_final.merge(g_est_pend, on=['COMPRADOR', 'CODIGO_PRODUTO'], how='left')

    cols_fill = ['LOJAS_RUP', 'LOJAS_NEG', 'LOJAS_RUP_PEND', 'LOJAS_EST_PEND']
    for c in cols_fill:
        if c in df_final.columns:
            df_final[c] = df_final[c].fillna('')

    df_final['RUPTURA_CD'] = df_final['RUPTURA_CD'].astype(bool)

    dados_json = json.dumps(df_final.to_dict(orient='records'))

    compradores = sorted([c for c in df['COMPRADOR'].dropna().unique()])
    options_compradores = '<option value="">-- Selecione o Comprador --</option>'
    for c in compradores:
        options_compradores += f'<option value="{c}">{c}</option>'

    lojas = sorted([int(x) for x in df['CODIGO_EMPRESA'].dropna().unique()])
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
            .btn-rup-cd { background-color: #FF0000; color: white; border: none; }
            .btn-rup-cd:hover { background-color: #cc0000; color: white; }
            .btn-rup-loja { background-color: #FFA500; color: white; border: none; }
            .btn-rup-loja:hover { background-color: #e69500; color: white; }
            .btn-rup-neg { background-color: #800080; color: white; border: none; }
            .btn-rup-neg:hover { background-color: #660066; color: white; }
            .btn-rup-pend { background-color: #FFD700; color: black; border: none; }
            .btn-rup-pend:hover { background-color: #e6c200; color: black; }
            .btn-est-pend { background-color: #008000; color: white; border: none; }
            .btn-est-pend:hover { background-color: #006600; color: white; }
            
            .active-metric { outline: 4px solid #333; outline-offset: -2px; box-shadow: 0 0 10px rgba(0,0,0,0.5); transform: scale(1.05); }
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
                    <label class="form-label mb-1">Selecionar Loja</label>
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

            <div class="card" id="filtros-container" style="display: none;">
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
            
            <div class="card table-container" id="tabela-container" style="display: none;">
                <table class="table table-striped table-hover align-middle">
                    <thead>
                        <tr id="table-head">
                        </tr>
                    </thead>
                    <tbody id="tabela-body">
                    </tbody>
                </table>
            </div>
            
            <div id="mensagem-inicial" class="text-center mt-5">
                <h4 class="text-muted">Selecione um comprador acima para carregar o detalhamento.</h4>
            </div>
        </div>

        <script>
        const masterData = [DADOS_JSON];
        let dadosAtuais = [];
        let visaoAtual = '';

        function aplicarFiltros() {
            const comprador = document.getElementById("FiltroComprador").value;
            
            if (!comprador) {
                document.getElementById("tabela-container").style.display = "none";
                document.getElementById("filtros-container").style.display = "none";
                document.getElementById("mensagem-inicial").style.display = "block";
                return;
            }
            
            document.getElementById("mensagem-inicial").style.display = "none";
            document.getElementById("filtros-container").style.display = "block";
            
            dadosAtuais = masterData.filter(d => d.COMPRADOR === comprador);
            
            if (!visaoAtual) {
                mudarVisao('RUPTURA_LOJA');
            } else {
                renderTable();
            }
        }

        function mudarVisao(novaVisao) {
            visaoAtual = novaVisao;
            
            document.querySelectorAll('.btn-metric').forEach(btn => btn.classList.remove('active-metric'));
            if (visaoAtual === 'RUPTURA_CD') document.getElementById('btn_rup_cd').classList.add('active-metric');
            if (visaoAtual === 'RUPTURA_LOJA') document.getElementById('btn_rup_loja').classList.add('active-metric');
            if (visaoAtual === 'RUPTURA_NEG') document.getElementById('btn_rup_neg').classList.add('active-metric');
            if (visaoAtual === 'RUPTURA_PEND') document.getElementById('btn_rup_pend').classList.add('active-metric');
            if (visaoAtual === 'ESTOQUE_PEND') document.getElementById('btn_est-pend').classList.add('active-metric');

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
            
            function temLoja(strLojas) {
                if (lojaSel === "TODAS") return true; 
                if (!strLojas) return false;
                const lista = strLojas.toString().split(',').map(s => s.trim());
                return lista.includes(lojaSel);
            }

            let colunasHTML = `<th>COD. PŔODUTO</th><th style="text-align: left;">DESCRIÇÃO</th>`;
            
            let dFinal = [];
            
            if (visaoAtual === 'RUPTURA_CD') {
                colunasHTML += `<th>Status CD</th>`;
                dFinal = dadosAtuais.filter(d => d.RUPTURA_CD === true);
            } else if (visaoAtual === 'RUPTURA_LOJA') {
                colunasHTML += `<th>LOJAS (Em Ruptura)</th>`;
                dFinal = dadosAtuais.filter(d => temLoja(d.LOJAS_RUP));
            } else if (visaoAtual === 'RUPTURA_NEG') {
                colunasHTML += `<th>LOJAS (Estoque Negativo)</th>`;
                dFinal = dadosAtuais.filter(d => temLoja(d.LOJAS_NEG));
            } else if (visaoAtual === 'RUPTURA_PEND') {
                colunasHTML += `<th>LOJAS (Rup. com Pedido)</th>`;
                dFinal = dadosAtuais.filter(d => temLoja(d.LOJAS_RUP_PEND));
            } else if (visaoAtual === 'ESTOQUE_PEND') {
                colunasHTML += `<th>LOJAS (Est. com Pedido)</th>`;
                dFinal = dadosAtuais.filter(d => temLoja(d.LOJAS_EST_PEND));
            }

            colunasHTML += `
                <th>Estoque Total</th>
                <th>Pedidos Pendentes</th>
                <th>Venda 30D</th>
            `;
            
            document.getElementById("table-head").innerHTML = colunasHTML;

            dFinal.sort((a, b) => b.VENDA_30D - a.VENDA_30D);

            document.getElementById("contador-linhas").innerText = `Exibindo: ${dFinal.length} produtos`;

            let tbody = '';
            dFinal.forEach(row => {
                let colunaEspecifica = '';
                
                if (visaoAtual === 'RUPTURA_CD') {
                    colunaEspecifica = `<td><span class="badge bg-danger">Em Ruptura</span></td>`;
                } else if (visaoAtual === 'RUPTURA_LOJA') {
                    colunaEspecifica = `<td><span class="fw-bold">${row.LOJAS_RUP}</span></td>`;
                } else if (visaoAtual === 'RUPTURA_NEG') {
                    colunaEspecifica = `<td><span class="fw-bold text-danger">${row.LOJAS_NEG}</span></td>`;
                } else if (visaoAtual === 'RUPTURA_PEND') {
                    colunaEspecifica = `<td><span class="fw-bold">${row.LOJAS_RUP_PEND}</span></td>`;
                } else if (visaoAtual === 'ESTOQUE_PEND') {
                    colunaEspecifica = `<td><span class="fw-bold text-success">${row.LOJAS_EST_PEND}</span></td>`;
                }

                tbody += `<tr>
                    <td class="fw-bold">${row.CODIGO_PRODUTO}</td>
                    <td style="text-align: left;">${row.DESCRICAO_PRODUTO}</td>
                    ${colunaEspecifica}
                    <td>${fmtNum(row.ESTOQUE_TOTAL)}</td>
                    <td>${fmtNum(row.PEDIDOS_PEND)}</td>
                    <td class="text-primary fw-bold">${fmtNum(row.VENDA_30D)}</td>
                </tr>`;
            });
            
            document.getElementById("tabela-body").innerHTML = tbody;
            document.getElementById("tabela-container").style.display = "block";
        }
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
