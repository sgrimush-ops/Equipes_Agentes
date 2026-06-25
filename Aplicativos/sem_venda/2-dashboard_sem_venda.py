import argparse
from pathlib import Path
import pandas as pd
import json

def carregar_base(caminho_excel: Path) -> pd.DataFrame:
    if not caminho_excel.exists():
        raise FileNotFoundError(f"Arquivo Excel nao encontrado: {caminho_excel}")

    df = pd.read_excel(caminho_excel)
    df.columns = [str(c).strip().upper() for c in df.columns]
    return df

def classificar_risco(qtd_lojas: int) -> str:
    if qtd_lojas >= 5:
        return "Risco Alto (5+ Lojas)"
    elif qtd_lojas >= 2:
        return "Risco Medio (2 a 4 Lojas)"
    else:
        return "Risco Baixo (1 Loja)"

def preparar_dados(df: pd.DataFrame) -> dict:
    base = df.copy()
    base["COMPRADOR"] = base["COMPRADOR"].fillna("SEM GESTOR").astype(str).str.strip()
    
    if "DESCRICAO_PRODUTO" not in base.columns:
        base["DESCRICAO_PRODUTO"] = "N/A"
        
    if "ESTOQUE" not in base.columns:
        base["ESTOQUE"] = 0
    else:
        base["ESTOQUE"] = pd.to_numeric(base["ESTOQUE"], errors="coerce").fillna(0)
        
    if "DIAS_CADASTRO" not in base.columns:
        base["DIAS_CADASTRO"] = 0
    else:
        base["DIAS_CADASTRO"] = pd.to_numeric(base["DIAS_CADASTRO"], errors="coerce").fillna(0)

    # 1. Calcular o risco global de cada produto (em quantas lojas diferentes ele esta parado)
    agrupado_global = base.groupby("CODIGO_PRODUTO", as_index=False).agg(
        QTD_LOJAS_SEM_VENDA_GLOBAL=("EMPRESA", "nunique")
    )
    agrupado_global["NIVEL_RISCO_GLOBAL"] = agrupado_global["QTD_LOJAS_SEM_VENDA_GLOBAL"].apply(classificar_risco)

    # Merge do risco global na base
    base = base.merge(agrupado_global, on="CODIGO_PRODUTO", how="left")
    
    # Prepara JSON raw data com o que interessa para o HTML
    raw_data = base[["COMPRADOR", "EMPRESA", "CODIGO_PRODUTO", "DESCRICAO_PRODUTO", "ESTOQUE", "QTD_LOJAS_SEM_VENDA_GLOBAL", "NIVEL_RISCO_GLOBAL", "DIAS_CADASTRO"]].to_dict(orient="records")
    
    # Listas unicas para popular os filtros (<select>)
    compradores = sorted(base["COMPRADOR"].unique().tolist())
    lojas = sorted(base["EMPRESA"].unique().tolist())
    
    return {
        "raw_data": raw_data,
        "compradores": compradores,
        "lojas": lojas
    }

def gerar_dashboard_html(dados_json: dict, destino_html: Path) -> Path:
    json_str = json.dumps(dados_json)
    
    html_final = f"""
<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Dashboard Sem Venda Dinâmico</title>
  <!-- Biblioteca Plotly importada dinamicamente via CDN -->
  <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
  <style>
    body {{ font-family: Segoe UI, Tahoma, sans-serif; margin: 24px; background: #f5f7fa; color: #1b1f24; }}
    h1 {{ margin-bottom: 8px; }}
    .subtitulo {{ margin-top: 0; margin-bottom: 20px; color: #4b5563; font-size: 14px; line-height: 1.5; }}
    .card {{ background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; margin-bottom: 16px; overflow-x: auto; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    
    .filter-container {{ display: flex; gap: 24px; margin-bottom: 24px; align-items: center; background: #fff; padding: 16px; border-radius: 12px; border: 1px solid #e5e7eb; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
    .filter-box {{ display: flex; flex-direction: column; flex: 1; max-width: 300px; }}
    .filter-box label {{ font-weight: 600; margin-bottom: 6px; font-size: 14px; color: #374151; }}
    .filter-box select {{ padding: 10px 14px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; min-width: 200px; outline: none; transition: border-color 0.2s; cursor: pointer; }}
    .filter-box select:focus {{ border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }}
    
    .stats-container {{ display: flex; gap: 16px; margin-bottom: 20px; }}
    .stat-box {{ flex: 1; background: #fff; padding: 16px; border-radius: 12px; border: 1px solid #e5e7eb; box-shadow: 0 1px 2px rgba(0,0,0,0.05); text-align: center; }}
    .stat-box .number {{ font-size: 28px; font-weight: bold; color: #111827; }}
    .stat-box .label {{ font-size: 13px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }}
    
    table.table-criticos {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
    table.table-criticos th, table.table-criticos td {{ border: 1px solid #e5e7eb; padding: 12px; text-align: left; }}
    table.table-criticos th {{ background: #f9fafb; position: sticky; top: 0; font-weight: 600; color: #374151; z-index: 10; box-shadow: 0 1px 0 #e5e7eb; }}
    table.table-criticos tr:nth-child(even) {{ background: #fafafa; }}
    table.table-criticos tr:hover {{ background: #f3f4f6; }}
  </style>
</head>
<body>
  <h1>Radar de Risco: Itens Sem Venda</h1>
  <p class="subtitulo">
    Selecione os filtros abaixo para investigar. <br/>
    <strong>Atenção:</strong> A classificação de Risco Global do produto e as "Lojas Paradas" referem-se ao status do produto <b>em toda a rede</b>, 
    independentemente de você estar analisando o estoque apenas de uma loja específica.
  </p>
  
  <!-- Controles de Filtro -->
  <div class="filter-container">
      <div class="filter-box">
          <label for="filtroComprador">Filtrar por Comprador:</label>
          <select id="filtroComprador" onchange="atualizarDashboard()">
              <option value="TODOS">🌍 Todos os Compradores</option>
          </select>
      </div>
      <div class="filter-box">
          <label for="filtroLoja">Filtrar por Loja (Empresa):</label>
          <select id="filtroLoja" onchange="atualizarDashboard()">
              <option value="TODAS">🏬 Todas as Lojas</option>
          </select>
      </div>
  </div>

  <!-- Cards de Resumo -->
  <div class="stats-container">
      <div class="stat-box">
          <div class="number" id="stat-produtos">0</div>
          <div class="label">Produtos Únicos Listados</div>
      </div>
      <div class="stat-box">
          <div class="number" id="stat-estoque">0</div>
          <div class="label">Volume de Estoque Fisico Parado</div>
      </div>
      <div class="stat-box" style="border-left: 4px solid #ef4444;">
          <div class="number" id="stat-alto">0</div>
          <div class="label">Produtos em Risco Alto (5+ Lojas)</div>
      </div>
  </div>

  <!-- Gráfico -->
  <div class="card" id="chart_div"></div>
  
  <!-- Tabela -->
  <h2 style="margin-top: 32px;">Top 100 Produtos Mais Críticos <span id="table-subtitle" style="font-size: 16px; font-weight: normal; color: #6b7280;"></span></h2>
  <div class="card" style="max-height: 600px; overflow-y: auto;">
      <table class="table-criticos" id="tabela_produtos">
          <thead>
              <tr>
                  <th>Comprador</th>
                  <th>Cód. Produto</th>
                  <th>Descrição</th>
                  <th>Risco Global</th>
                  <th>Lojas Globalmente Paradas</th>
                  <th>Dias de Cadastro</th>
                  <th>Estoque Total (Neste Filtro)</th>
              </tr>
          </thead>
          <tbody>
          </tbody>
      </table>
  </div>

  <!-- Motor JavaScript -->
  <script>
      const DADOS = {json_str};
      
      // 1. Inicializar Filtros
      const selComprador = document.getElementById('filtroComprador');
      DADOS.compradores.forEach(c => {{
          let opt = document.createElement('option');
          opt.value = c;
          opt.textContent = c;
          selComprador.appendChild(opt);
      }});

      const selLoja = document.getElementById('filtroLoja');
      DADOS.lojas.forEach(l => {{
          let opt = document.createElement('option');
          opt.value = l;
          opt.textContent = "Loja " + l;
          selLoja.appendChild(opt);
      }});

      // 2. Funcao Principal acionada ao alterar filtros
      function atualizarDashboard() {{
          const valComprador = selComprador.value;
          const valLoja = selLoja.value;

          // Filtrar a base bruta JSON de acordo com os Selects
          let dadosFiltrados = DADOS.raw_data;
          
          if (valComprador !== "TODOS") {{
              dadosFiltrados = dadosFiltrados.filter(d => d.COMPRADOR === valComprador);
          }}
          
          if (valLoja !== "TODAS") {{
              const lojaInt = parseInt(valLoja);
              dadosFiltrados = dadosFiltrados.filter(d => d.EMPRESA === lojaInt);
          }}

          // Atualiza Interface
          document.getElementById("table-subtitle").textContent = 
            `(Filtro Ativo: ${{valComprador === 'TODOS' ? 'Geral' : valComprador}} | ${{valLoja === 'TODAS' ? 'Todas as Lojas' : 'Loja ' + valLoja}})`;

          renderizarGrafico(dadosFiltrados);
          renderizarTabelaEKPIS(dadosFiltrados);
      }}

      // 3. Renderizador do Grafico Plotly
      function renderizarGrafico(dados) {{
          let agrupadoMap = {{}};
          
          // O agrupamento precisa ser por Produto Unico para nao somar duas vezes 
          // a "Quantidade de Produtos Diferentes" num mesmo comprador
          dados.forEach(d => {{
              if(!agrupadoMap[d.COMPRADOR]) {{
                  agrupadoMap[d.COMPRADOR] = {{
                      "Risco Alto (5+ Lojas)": new Set(),
                      "Risco Medio (2 a 4 Lojas)": new Set(),
                      "Risco Baixo (1 Loja)": new Set()
                  }};
              }}
              agrupadoMap[d.COMPRADOR][d.NIVEL_RISCO_GLOBAL].add(d.CODIGO_PRODUTO);
          }});

          let compradoresOrdenados = Object.keys(agrupadoMap).sort();
          let x_vals = compradoresOrdenados;
          let y_alto = [], y_medio = [], y_baixo = [];

          compradoresOrdenados.forEach(c => {{
              y_alto.push(agrupadoMap[c]["Risco Alto (5+ Lojas)"].size);
              y_medio.push(agrupadoMap[c]["Risco Medio (2 a 4 Lojas)"].size);
              y_baixo.push(agrupadoMap[c]["Risco Baixo (1 Loja)"].size);
          }});

          var traceAlto = {{ x: x_vals, y: y_alto, name: 'Risco Alto (5+ Lojas)', type: 'bar', marker: {{color: '#ef4444'}} }};
          var traceMedio = {{ x: x_vals, y: y_medio, name: 'Risco Médio (2 a 4 Lojas)', type: 'bar', marker: {{color: '#f59e0b'}} }};
          var traceBaixo = {{ x: x_vals, y: y_baixo, name: 'Risco Baixo (1 Loja)', type: 'bar', marker: {{color: '#10b981'}} }};

          var data = [traceAlto, traceMedio, traceBaixo];
          var layout = {{
              barmode: 'stack',
              title: "Distribuição de Produtos Diferentes Encalhados por Comprador",
              xaxis: {{title: "", tickangle: -45}},
              yaxis: {{title: "Volume de SKU (Qtd)"}},
              hovermode: "x unified",
              margin: {{b: 100}} 
          }};

          // Atualiza grafico com transicao suave
          Plotly.react('chart_div', data, layout);
      }}

      // 4. Renderizador da Tabela e Indicadores Superiores
      function renderizarTabelaEKPIS(dados) {{
          let mapProdutos = {{}};
          let totalEstoqueFisico = 0;
          
          dados.forEach(d => {{
              if(!mapProdutos[d.CODIGO_PRODUTO]) {{
                  mapProdutos[d.CODIGO_PRODUTO] = {{
                      COMPRADOR: d.COMPRADOR,
                      CODIGO_PRODUTO: d.CODIGO_PRODUTO,
                      DESCRICAO_PRODUTO: d.DESCRICAO_PRODUTO,
                      NIVEL_RISCO_GLOBAL: d.NIVEL_RISCO_GLOBAL,
                      QTD_LOJAS_SEM_VENDA_GLOBAL: d.QTD_LOJAS_SEM_VENDA_GLOBAL,
                      DIAS_CADASTRO: d.DIAS_CADASTRO,
                      ESTOQUE_TOTAL: 0
                  }};
              }}
              mapProdutos[d.CODIGO_PRODUTO].ESTOQUE_TOTAL += d.ESTOQUE;
              totalEstoqueFisico += d.ESTOQUE;
          }});

          let listaProdutos = Object.values(mapProdutos);
          
          // Atualiza Indicadores KPI
          document.getElementById('stat-produtos').textContent = listaProdutos.length.toLocaleString('pt-BR');
          document.getElementById('stat-estoque').textContent = Math.round(totalEstoqueFisico).toLocaleString('pt-BR');
          
          let riscoAlto = listaProdutos.filter(p => p.NIVEL_RISCO_GLOBAL.includes("Alto")).length;
          document.getElementById('stat-alto').textContent = riscoAlto.toLocaleString('pt-BR');
          
          // Ordenacao Forte da Tabela: Maior quantidade de lojas global > Maior estoque filtrado
          listaProdutos.sort((a, b) => {{
              if(b.QTD_LOJAS_SEM_VENDA_GLOBAL !== a.QTD_LOJAS_SEM_VENDA_GLOBAL) {{
                  return b.QTD_LOJAS_SEM_VENDA_GLOBAL - a.QTD_LOJAS_SEM_VENDA_GLOBAL;
              }}
              return b.ESTOQUE_TOTAL - a.ESTOQUE_TOTAL;
          }});

          let top100 = listaProdutos.slice(0, 100);
          let tbody = document.querySelector("#tabela_produtos tbody");
          tbody.innerHTML = "";

          top100.forEach(p => {{
              let tr = document.createElement('tr');
              
              let corRisco = "";
              let bgRisco = "";
              if(p.NIVEL_RISCO_GLOBAL.includes("Alto")) {{ corRisco = "#b91c1c"; bgRisco = "#fef2f2"; }}
              else if(p.NIVEL_RISCO_GLOBAL.includes("Medio")) {{ corRisco = "#b45309"; bgRisco = "#fffbeb"; }}
              else {{ corRisco = "#047857"; bgRisco = "#ecfdf5"; }}

              tr.innerHTML = `
                  <td>${{p.COMPRADOR}}</td>
                  <td style="font-weight: 500;">${{p.CODIGO_PRODUTO}}</td>
                  <td>${{p.DESCRICAO_PRODUTO}}</td>
                  <td style="color: ${{corRisco}}; background: ${{bgRisco}}; font-weight: 600; text-align: center; border-radius: 4px;">
                     ${{p.NIVEL_RISCO_GLOBAL}}
                  </td>
                  <td style="text-align: center; font-weight: bold; font-size: 16px;">${{p.QTD_LOJAS_SEM_VENDA_GLOBAL}}</td>
                  <td style="text-align: center;">${{p.DIAS_CADASTRO}}</td>
                  <td style="text-align: right; padding-right: 24px;">${{Math.round(p.ESTOQUE_TOTAL).toLocaleString('pt-BR')}}</td>
              `;
              tbody.appendChild(tr);
          }});
      }}

      // Start App
      window.onload = function() {{
          atualizarDashboard();
      }};
  </script>
</body>
</html>
"""

    destino_html.parent.mkdir(parents=True, exist_ok=True)
    destino_html.write_text(html_final, encoding="utf-8")
    return destino_html

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera dashboard dinamico (SPA) a partir do Excel de sem_venda."
    )
    parser.add_argument(
        "--origem",
        type=Path,
        default=Path(__file__).resolve().parent / "sem_venda.xlsx",
        help="Arquivo Excel de origem (padrao: sem_venda.xlsx na mesma pasta).",
    )
    parser.add_argument(
        "--saida",
        type=Path,
        default=Path(__file__).resolve().parent / "dashboard_sem_venda.html",
        help="Arquivo HTML de saida.",
    )
    args = parser.parse_args()

    df = carregar_base(args.origem)
    dados_json = preparar_dados(df)
    caminho_html = gerar_dashboard_html(dados_json, args.saida)

    print(f"Dashboard gerado com sucesso em: {caminho_html}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
