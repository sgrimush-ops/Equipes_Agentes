"""
Dashboard de Quebras — Ranking por Comprador com visão por Loja.
Arquitetura No-Server: gera HTML único com dados JSON embutidos.
"""
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date

if __name__ == '__main__':
    os.chdir(Path(__file__).parent.resolve())


def gerar_dashboard() -> None:
    """Gera dashboard HTML de quebras a partir do itens_extraidos_preenchido.xlsx."""
    caminho = Path("itens_extraidos_preenchido.xlsx")
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    print("[1/4] Carregando dados...")
    df = pd.read_excel(caminho, engine="openpyxl")
    print(f"  {len(df):,} linhas carregadas")

    col_loja = df.columns[3]
    col_qtd = "Qtd"
    col_custo = "Custo Nt"
    col_total = "Total Nota"
    col_desc = df.columns[1]
    col_cod = "Codigo Consico"
    col_comp = "Apelido Comprador"

    df[col_comp] = df[col_comp].fillna("SEM COMPRADOR")
    df[col_loja] = df[col_loja].astype(int)

    for c in [col_qtd, col_custo, col_total]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    print("[2/4] Computando métricas...")

    def compute(subset: pd.DataFrame, loja_nome: str) -> list:
        resumo = subset.groupby(col_comp).agg(
            Itens=(col_total, "count"),
            SKUs=(col_cod, "nunique"),
            Qtd_Total=(col_qtd, "sum"),
            Valor_Total=(col_total, "sum"),
        ).reset_index()
        resumo = resumo.rename(columns={col_comp: "COMPRADOR"})
        resumo = resumo.sort_values("Valor_Total", ascending=False).reset_index(drop=True)

        total = {
            "COMPRADOR": "TOTAL GERAL",
            "Itens": int(resumo["Itens"].sum()),
            "SKUs": int(subset[col_cod].nunique()),
            "Qtd_Total": round(float(resumo["Qtd_Total"].sum()), 2),
            "Valor_Total": round(float(resumo["Valor_Total"].sum()), 2),
        }

        grand_total = total["Valor_Total"]
        resumo["Pct_Valor"] = np.where(
            grand_total > 0,
            (resumo["Valor_Total"] / grand_total * 100).round(2),
            0,
        )
        total["Pct_Valor"] = 100.0

        resumo["Rank"] = range(1, len(resumo) + 1)
        total["Rank"] = 0

        resumo["LOJA"] = loja_nome
        total["LOJA"] = loja_nome

        rows = resumo.to_dict("records")
        rows.insert(0, total)

        for r in rows:
            for k in ["Itens", "SKUs"]:
                r[k] = int(r[k])
            for k in ["Qtd_Total", "Valor_Total", "Pct_Valor"]:
                r[k] = round(float(r[k]), 2)
        return rows

    all_rows = []
    all_rows.extend(compute(df, "TODAS"))

    lojas = sorted(df[col_loja].dropna().unique())
    for loja in lojas:
        all_rows.extend(compute(df[df[col_loja] == loja], str(int(loja))))

    dados_json = json.dumps(all_rows, ensure_ascii=False)

    compradores = sorted(df[col_comp].unique())
    opts_comp = '<option value="TODOS">TODOS OS COMPRADORES</option>'
    for c in compradores:
        opts_comp += f'<option value="{c}">{c}</option>'

    opts_lojas = '<option value="TODAS">TODAS AS LOJAS</option>'
    for l in lojas:
        opts_lojas += f'<option value="{int(l)}">Loja {int(l)}</option>'

    lojas_js = ','.join(['"' + str(int(l)) + '"' for l in lojas])

    print("[3/4] Gerando HTML...")
    html = build_html(dados_json, opts_comp, opts_lojas, lojas_js)

    saida = Path("dashboard_quebra.html")
    with open(saida, "w", encoding="utf-8-sig") as f:
        f.write(html)
    print(f"[4/4] Dashboard salvo: {saida.resolve()}")


def build_html(dados_json: str, opts_comp: str, opts_lojas: str, lojas_js: str) -> str:
    """Monta o HTML completo do dashboard."""
    hoje = date.today().strftime("%d/%m/%Y")
    return f'''<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Quebras - Varejo Insight</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0f1117;color:#e1e4e8;font-family:'Inter',sans-serif;padding:20px}}
.header{{background:linear-gradient(135deg,#1a1e2e 0%,#2d1b4e 50%,#1a1e2e 100%);padding:28px 32px;border-radius:16px;margin-bottom:24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;border:1px solid rgba(139,92,246,0.3);box-shadow:0 8px 32px rgba(139,92,246,0.15)}}
.header h2{{font-size:1.6rem;font-weight:800;background:linear-gradient(135deg,#a78bfa,#f472b6);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.header p{{color:#9ca3af;font-size:0.9rem;margin-top:4px}}
.filters{{display:flex;gap:16px;flex-wrap:wrap}}
.filter-group label{{display:block;color:#9ca3af;font-size:0.75rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;font-weight:600}}
.filter-group select{{background:#1a1e2e;color:#e1e4e8;border:1px solid rgba(139,92,246,0.4);border-radius:10px;padding:10px 16px;font-size:0.95rem;min-width:220px;outline:none;cursor:pointer;transition:all .2s}}
.filter-group select:hover{{border-color:#a78bfa;box-shadow:0 0 12px rgba(139,92,246,0.3)}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:14px;padding:24px;margin-bottom:20px;box-shadow:0 4px 16px rgba(0,0,0,0.3)}}
.card-title{{font-size:1.1rem;font-weight:700;color:#c9d1d9;margin-bottom:16px;display:flex;align-items:center;gap:8px}}
.kpi-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:20px}}
.kpi{{background:linear-gradient(135deg,#1a1e2e,#21262d);border:1px solid #30363d;border-radius:12px;padding:20px;text-align:center;transition:transform .2s,box-shadow .2s}}
.kpi:hover{{transform:translateY(-2px);box-shadow:0 6px 20px rgba(139,92,246,0.2)}}
.kpi .value{{font-size:1.8rem;font-weight:800;margin-bottom:4px}}
.kpi .label{{font-size:0.75rem;color:#8b949e;text-transform:uppercase;letter-spacing:1px}}
.kpi.purple .value{{color:#a78bfa}}
.kpi.pink .value{{color:#f472b6}}
.kpi.cyan .value{{color:#22d3ee}}
.kpi.green .value{{color:#34d399}}
.table-wrap{{overflow-x:auto;max-height:600px;border-radius:10px}}
table{{width:100%;border-collapse:collapse;font-size:0.85rem}}
thead th{{background:#21262d;color:#8b949e;text-transform:uppercase;font-size:0.7rem;letter-spacing:1px;padding:12px 10px;position:sticky;top:0;z-index:2;text-align:center;border-bottom:2px solid #30363d}}
thead th:first-child{{text-align:left;padding-left:16px}}
tbody td{{padding:10px;text-align:center;border-bottom:1px solid #21262d}}
tbody td:first-child{{text-align:left;padding-left:16px;font-weight:600}}
tbody tr:hover{{background:rgba(139,92,246,0.08)}}
tbody tr.total-row{{background:#1a1e2e;font-weight:700;border-top:2px solid #a78bfa}}
tbody tr.total-row td{{color:#a78bfa}}
.rank-badge{{display:inline-block;width:28px;height:28px;line-height:28px;border-radius:50%;text-align:center;font-weight:700;font-size:0.75rem}}
.rank-1{{background:linear-gradient(135deg,#fbbf24,#f59e0b);color:#000}}
.rank-2{{background:linear-gradient(135deg,#9ca3af,#6b7280);color:#fff}}
.rank-3{{background:linear-gradient(135deg,#d97706,#b45309);color:#fff}}
.rank-n{{background:#30363d;color:#8b949e}}
.pct-bar{{height:6px;border-radius:3px;background:#21262d;position:relative;min-width:60px}}
.pct-fill{{height:100%;border-radius:3px;background:linear-gradient(90deg,#a78bfa,#f472b6);transition:width .3s}}
.legend{{display:flex;gap:20px;flex-wrap:wrap;margin-top:16px;padding:16px;background:#1a1e2e;border-radius:10px;border:1px solid #30363d}}
.legend-item{{display:flex;align-items:center;gap:6px;font-size:0.8rem;color:#8b949e}}
.legend-dot{{width:12px;height:12px;border-radius:3px}}
</style>
</head>
<body>
<div class="header">
 <div>
  <h2>📊 Dashboard de Quebras</h2>
  <p>Atualizado em: {hoje}</p>
 </div>
 <div class="filters">
  <div class="filter-group">
   <label>Visão por Loja</label>
   <select id="FiltroLoja" onchange="att()">{opts_lojas}</select>
  </div>
  <div class="filter-group">
   <label>Filtro Comprador</label>
   <select id="FiltroComp" onchange="att()">{opts_comp}</select>
  </div>
 </div>
</div>

<div class="kpi-row">
 <div class="kpi purple"><div class="value" id="kpi-valor">-</div><div class="label">Valor Total Quebra</div></div>
 <div class="kpi pink"><div class="value" id="kpi-itens">-</div><div class="label">Total de Itens</div></div>
 <div class="kpi cyan"><div class="value" id="kpi-skus">-</div><div class="label">SKUs Distintos</div></div>
 <div class="kpi green"><div class="value" id="kpi-qtd">-</div><div class="label">Qtd Total</div></div>
</div>

<div class="card">
 <div class="card-title">📈 Quebra por Loja (R$)</div>
 <div id="chart-loja" style="width:100%;height:420px;"></div>
</div>

<div class="card">
 <div class="card-title">🏆 Ranking por Comprador</div>
 <div id="chart-rank" style="width:100%;height:380px;"></div>
</div>

<div class="card">
 <div class="card-title">📋 Tabela Detalhada</div>
 <div class="table-wrap">
  <table>
   <thead><tr>
    <th>#</th><th>Comprador</th><th>Itens</th><th>SKUs</th>
    <th>Qtd Total</th><th>Valor Total (R$)</th><th>% do Total</th><th>Participação</th>
   </tr></thead>
   <tbody id="tbody"></tbody>
  </table>
 </div>
</div>

<script>
var MD={dados_json};

function fmtR(v){{return"R$ "+v.toFixed(2).replace(".",",").replace(/\\B(?=(\\d{{3}})+(?!\\d))/g,".")}}
function fmtN(v){{return v.toLocaleString("pt-BR")}}
function fmtP(v){{return v.toFixed(1).replace(".",",")+"%"}}

function att(){{
 var loja=document.getElementById("FiltroLoja").value;
 var comp=document.getElementById("FiltroComp").value;
 var dl=MD.filter(function(d){{return d.LOJA===loja}});

 var total=dl.find(function(d){{return d.COMPRADOR==="TOTAL GERAL"}});
 var rows=dl.filter(function(d){{return d.COMPRADOR!=="TOTAL GERAL"}});

 if(comp!=="TODOS"){{
  rows=rows.filter(function(d){{return d.COMPRADOR===comp}});
  var t2={{COMPRADOR:"TOTAL GERAL",Itens:0,SKUs:0,Qtd_Total:0,Valor_Total:0,Pct_Valor:100,Rank:0,LOJA:loja}};
  rows.forEach(function(r){{t2.Itens+=r.Itens;t2.Qtd_Total+=r.Qtd_Total;t2.Valor_Total+=r.Valor_Total}});
  t2.SKUs=rows.reduce(function(a,r){{return a+r.SKUs}},0);
  total=t2;
 }}

 rows.sort(function(a,b){{return b.Valor_Total-a.Valor_Total}});
 for(var i=0;i<rows.length;i++)rows[i].Rank=i+1;

 var gt=total?total.Valor_Total:0;
 document.getElementById("kpi-valor").textContent=fmtR(gt);
 document.getElementById("kpi-itens").textContent=fmtN(total?total.Itens:0);
 document.getElementById("kpi-skus").textContent=fmtN(total?total.SKUs:0);
 document.getElementById("kpi-qtd").textContent=fmtN(Math.round(total?total.Qtd_Total:0));

 renderTabela(rows,total,gt);
 renderChartLoja(loja,comp);
 renderChartRank(rows);
}}

function renderTabela(rows,total,gt){{
 var html="";
 rows.forEach(function(r){{
  var pct=gt>0?(r.Valor_Total/gt*100):0;
  var rc=r.Rank<=3?"rank-"+r.Rank:"rank-n";
  html+="<tr>"
   +"<td><span class='rank-badge "+rc+"'>"+r.Rank+"</span></td>"
   +"<td>"+r.COMPRADOR+"</td>"
   +"<td>"+fmtN(r.Itens)+"</td>"
   +"<td>"+fmtN(r.SKUs)+"</td>"
   +"<td>"+fmtN(Math.round(r.Qtd_Total))+"</td>"
   +"<td style='color:#a78bfa;font-weight:700'>"+fmtR(r.Valor_Total)+"</td>"
   +"<td>"+fmtP(pct)+"</td>"
   +"<td><div class='pct-bar'><div class='pct-fill' style='width:"+Math.min(pct,100)+"%'></div></div></td>"
   +"</tr>";
 }});
 if(total){{
  html+="<tr class='total-row'>"
   +"<td></td><td>TOTAL GERAL</td>"
   +"<td>"+fmtN(total.Itens)+"</td>"
   +"<td>"+fmtN(total.SKUs)+"</td>"
   +"<td>"+fmtN(Math.round(total.Qtd_Total))+"</td>"
   +"<td>"+fmtR(total.Valor_Total)+"</td>"
   +"<td>100%</td><td></td></tr>";
 }}
 document.getElementById("tbody").innerHTML=html;
}}

function renderChartLoja(lojaFiltro,compFiltro){{
 var lojas=[{lojas_js}];
 var vals=[];
 lojas.forEach(function(l){{
  var dl=MD.filter(function(d){{return d.LOJA===l}});
  if(compFiltro!=="TODOS"){{
   var cr=dl.filter(function(d){{return d.COMPRADOR===compFiltro}});
   vals.push(cr.length>0?cr[0].Valor_Total:0);
  }}else{{
   var t=dl.find(function(d){{return d.COMPRADOR==="TOTAL GERAL"}});
   vals.push(t?t.Valor_Total:0);
  }}
 }});
 var colors=lojas.map(function(l){{return l===lojaFiltro?"#f472b6":"#a78bfa"}});
 var trace={{
  x:lojas.map(function(l){{return"Loja "+l}}),
  y:vals,type:"bar",
  marker:{{color:colors,line:{{color:"rgba(139,92,246,0.5)",width:1}}}},
  text:vals.map(function(v){{return fmtR(v)}}),textposition:"outside",
  textfont:{{color:"#e1e4e8",size:11}},
  hovertemplate:"Loja %{{x}}<br>%{{text}}<extra></extra>"
 }};
 var layout={{
  paper_bgcolor:"transparent",plot_bgcolor:"transparent",
  font:{{color:"#8b949e",family:"Inter"}},
  xaxis:{{gridcolor:"#21262d",title:""}},
  yaxis:{{gridcolor:"#21262d",title:"Valor (R$)",tickformat:",.0f"}},
  margin:{{l:80,r:20,t:20,b:60}},
  showlegend:false
 }};
 Plotly.react("chart-loja",[trace],layout,{{displayModeBar:false,responsive:true}});
}}

function renderChartRank(rows){{
 var top=rows.slice(0,15);
 top.reverse();
 var trace={{
  y:top.map(function(r){{return r.COMPRADOR}}),
  x:top.map(function(r){{return r.Valor_Total}}),
  type:"bar",orientation:"h",
  marker:{{color:top.map(function(r,i){{
   var t=top.length;
   var h=280-((t-1-i)/Math.max(t-1,1))*200;
   return"hsl("+h+",70%,60%)"
  }}),line:{{color:"rgba(139,92,246,0.3)",width:1}}}},
  text:top.map(function(r){{return fmtR(r.Valor_Total)}}),textposition:"outside",
  textfont:{{color:"#e1e4e8",size:11}},
  hovertemplate:"%{{y}}<br>%{{text}}<extra></extra>"
 }};
 var layout={{
  paper_bgcolor:"transparent",plot_bgcolor:"transparent",
  font:{{color:"#8b949e",family:"Inter"}},
  xaxis:{{gridcolor:"#21262d",title:"Valor Total Quebra (R$)",tickformat:",.0f"}},
  yaxis:{{gridcolor:"#21262d",automargin:true}},
  margin:{{l:200,r:100,t:10,b:50}},
  showlegend:false
 }};
 Plotly.react("chart-rank",[trace],layout,{{displayModeBar:false,responsive:true}});
}}

window.onload=att;
</script>
</body>
</html>'''


if __name__ == '__main__':
    gerar_dashboard()
