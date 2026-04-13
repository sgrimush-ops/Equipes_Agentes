import os
import json
import pandas as pd
from pathlib import Path

base_dir = Path(__file__).parent.resolve()
arquivo_parquet = base_dir / 'abc_comprador.parquet'
arquivo_html    = base_dir / 'dashboard_comprador.html'

if not arquivo_parquet.exists():
    print(f"Arquivo nao encontrado: {arquivo_parquet}")
    raise SystemExit(1)

print(f"Lendo: {arquivo_parquet}")
df = pd.read_parquet(arquivo_parquet)

# Ordenar por SUBGRUPO e CODIGO_PRODUTO
df = df.sort_values(['SUBGRUPO', 'CODIGO_PRODUTO'], na_position='last').reset_index(drop=True)

# Colunas a exibir (SUBGRUPO ate ESTOQUE_DEPOSITO)
colunas_exibir = [
    'SUBGRUPO', 'CODIGO_PRODUTO', 'DESCRICAO_PRODUTO', 'EMBALAGEM',
    'PERC_ACM', 'PRECO_CUSTO', 'PRECO_VENDA',
    'MARGEM_ATUAL', 'MARGEM_OBJETIVA',
    'QTD_VENDIDA', 'ESTOQUE_MINIMO', 'ESTOQUE_MAXIMO', 'ESTOQUE_LOJA', 'ESTOQUE_DEPOSITO'
]

if 'PENDENTE_EXPEDIR_CD' in df.columns:
  colunas_exibir.append('PENDENTE_EXPEDIR_CD')

# Opcoes do dropdown COMPRADOR (ordenadas)
compradores = sorted(df['COMPRADOR'].dropna().unique().tolist())

coluna_cod_fornecedor = None
for nome_coluna in ['CODIGO_FORNECEDOR_PRINCIPAL', 'CODIGO_FORNECEDOR']:
  if nome_coluna in df.columns:
    coluna_cod_fornecedor = nome_coluna
    break

# Serializar apenas as colunas necessarias para o JSON embutido
df_export = df[['COMPRADOR', 'FORNECEDOR_PRINCIPAL'] + colunas_exibir].copy()
if coluna_cod_fornecedor:
  df_export['FORNECEDOR_CODIGO'] = df[coluna_cod_fornecedor].astype(str).str.strip()
else:
  df_export['FORNECEDOR_CODIGO'] = ''

# Converter Int64 para int nativo para serializar em JSON
for col in df_export.select_dtypes(include=['Int64', 'int64']).columns:
    df_export[col] = df_export[col].astype(object).where(df_export[col].notna(), None)

registros = df_export.to_dict(orient='records')
dados_json = json.dumps(registros, ensure_ascii=False, default=str)

print(f"   {len(registros)} registros preparados para o dashboard")

cabecalhos = colunas_exibir
cabecalhos_json = json.dumps(cabecalhos)

html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard ABC Comprador</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f0f2f5; color: #333; }}
  header {{ background: #1a3a5c; color: #fff; padding: 16px 24px; display: flex; align-items: center; gap: 16px; }}
  header h1 {{ font-size: 1.2rem; font-weight: 600; }}
  .filtros {{ background: #fff; padding: 16px 24px; display: flex; flex-wrap: wrap; gap: 16px; align-items: flex-end;
              border-bottom: 2px solid #e0e4ea; box-shadow: 0 2px 4px rgba(0,0,0,.06); }}
  .filtro-grupo {{ display: flex; flex-direction: column; gap: 4px; }}
  .filtro-grupo label {{ font-size: .78rem; font-weight: 600; color: #555; text-transform: uppercase; letter-spacing: .04em; }}
  select, input[type=text] {{
    height: 36px; padding: 0 10px; border: 1px solid #c8cdd6; border-radius: 6px;
    font-size: .9rem; outline: none; background: #fff; color: #333;
    transition: border-color .2s;
  }}
  select {{ min-width: 220px; }}
  input[type=text] {{ min-width: 260px; }}
  select:focus, input[type=text]:focus {{ border-color: #1a7fd4; }}
  .btn-limpar {{ height: 36px; padding: 0 16px; background: #e8edf3; color: #555; border: 1px solid #c8cdd6;
                border-radius: 6px; cursor: pointer; font-size: .85rem; transition: background .2s; }}
  .btn-limpar:hover {{ background: #d0d8e4; }}
  .btn-acao {{ height: 36px; padding: 0 14px; background: #1a7fd4; color: #fff; border: 1px solid #166bb1;
              border-radius: 6px; cursor: pointer; font-size: .85rem; transition: background .2s; }}
  .btn-acao:hover {{ background: #166bb1; }}
  .acoes-wrap {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .info-barra {{ padding: 8px 24px; font-size: .82rem; color: #666; background: #f8f9fb; border-bottom: 1px solid #e0e4ea; }}
  .info-barra span {{ font-weight: 600; color: #1a3a5c; }}
  .hint {{ font-size: .75rem; color: #888; margin-top: 2px; }}
  .linha-dupla {{ display: flex; gap: 8px; }}
  .select-pequeno {{ min-width: 170px; }}
  .select-direcao {{ min-width: 120px; }}
  .tabela-wrap {{ padding: 16px 24px; max-height: calc(100vh - 310px); overflow: auto; }}
  #tabela {{
    border-collapse: separate;
    border-spacing: 0;
    font-size: .82rem;
    background: #fff;
    table-layout: fixed;
    box-shadow: 0 1px 4px rgba(0,0,0,.08);
    border-radius: 8px;
  }}
  thead tr {{ background: #1a3a5c; color: #fff; }}
  thead th {{
    padding: 9px 10px;
    text-align: left;
    font-weight: 600;
    white-space: nowrap;
    font-size: .78rem;
    text-transform: uppercase;
    letter-spacing: .03em;
    background: #1a3a5c;
    color: #fff;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  tbody tr {{ background: #fff; }}
  tbody tr:nth-child(even) {{ background: #f4f6fa; }}
  tbody tr:hover {{ background: #dce8f7; }}
  tbody td {{ padding: 7px 10px; border-bottom: 1px solid #eaecf0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .col-num {{ text-align: right; }}
  .subgrupo-tag {{ background: #1a7fd4; color: #fff; border-radius: 4px; padding: 1px 7px; font-size: .74rem; font-weight: 600; }}
  .sem-dados {{ text-align: center; padding: 48px; color: #999; font-size: .95rem; }}
  @media (max-width: 700px) {{
    .filtros {{ flex-direction: column; }}
    select, input[type=text] {{ min-width: 100%; width: 100%; }}
  }}
  @media print {{
    header, .filtros, .info-barra {{ display: none !important; }}
    .tabela-wrap {{ max-height: none !important; overflow: visible !important; padding: 0 !important; }}
    #tabela {{ box-shadow: none !important; width: 100% !important; }}
    thead tr {{ background: #fff !important; color: #000 !important; }}
    thead th {{ background: #fff !important; color: #000 !important; border-bottom: 1px solid #000; }}
  }}
</style>
</head>
<body>

<header>
  <div>
    <h1>Dashboard ABC — Comprador / Fornecedor</h1>
  </div>
</header>

<div class="filtros">
  <div class="filtro-grupo">
    <label>Comprador</label>
    <select id="sel-comprador" onchange="filtrar()">
      <option value="">— Todos —</option>
      {''.join(f'<option value="{c}">{c}</option>' for c in compradores)}
    </select>
  </div>
  <div class="filtro-grupo">
    <label>Fornecedor Principal</label>
    <input type="text" id="inp-fornecedor" placeholder="Ex: NESTLE* ou %IMPORTADORA%" oninput="filtrar()" />
    <span class="hint">Use * ou % como coringa. Ex: NES* &nbsp;|&nbsp; *LTDA &nbsp;|&nbsp; %IMPORT%</span>
  </div>
  <div class="filtro-grupo">
    <label>Codigo do Fornecedor</label>
    <input type="text" id="inp-fornecedor-cod" placeholder="Ex: 12345" oninput="filtrar()" />
    <span class="hint">Busca por contido no codigo do fornecedor</span>
  </div>
  <div class="filtro-grupo">
    <label>Ordenacao 1</label>
    <div class="linha-dupla">
      <select id="sel-ord1" class="select-pequeno" onchange="filtrar()">
        <option value="SUBGRUPO" selected>Subgrupo</option>
        <option value="CODIGO_PRODUTO">Codigo</option>
        <option value="DESCRICAO_PRODUTO">Descricao</option>
        <option value="EMBALAGEM">Embalagem</option>
        <option value="PERC_ACM">% Acum.</option>
        <option value="PRECO_CUSTO">Custo</option>
        <option value="PRECO_VENDA">Preco Venda</option>
        <option value="MARGEM_ATUAL">Margem %</option>
        <option value="MARGEM_OBJETIVA">Margem Obj.</option>
        <option value="QTD_VENDIDA">Qtd Vendida</option>
        <option value="ESTOQUE_MINIMO">Est. Min.</option>
        <option value="ESTOQUE_MAXIMO">Est. Max.</option>
        <option value="ESTOQUE_LOJA">Est. Loja</option>
        <option value="ESTOQUE_DEPOSITO">Est. CD</option>
      </select>
      <select id="sel-dir1" class="select-direcao" onchange="filtrar()">
        <option value="asc" selected>Crescente</option>
        <option value="desc">Decrescente</option>
      </select>
    </div>
  </div>
  <div class="filtro-grupo">
    <label>Ordenacao 2</label>
    <div class="linha-dupla">
      <select id="sel-ord2" class="select-pequeno" onchange="filtrar()">
        <option value="">Sem segundo criterio</option>
        <option value="SUBGRUPO">Subgrupo</option>
        <option value="CODIGO_PRODUTO">Codigo</option>
        <option value="DESCRICAO_PRODUTO">Descricao</option>
        <option value="EMBALAGEM">Embalagem</option>
        <option value="PERC_ACM">% Acum.</option>
        <option value="PRECO_CUSTO">Custo</option>
        <option value="PRECO_VENDA">Preco Venda</option>
        <option value="MARGEM_ATUAL">Margem %</option>
        <option value="MARGEM_OBJETIVA">Margem Obj.</option>
        <option value="QTD_VENDIDA" selected>Qtd Vendida</option>
        <option value="ESTOQUE_MINIMO">Est. Min.</option>
        <option value="ESTOQUE_MAXIMO">Est. Max.</option>
        <option value="ESTOQUE_LOJA">Est. Loja</option>
        <option value="ESTOQUE_DEPOSITO">Est. CD</option>
      </select>
      <select id="sel-dir2" class="select-direcao" onchange="filtrar()">
        <option value="asc">Crescente</option>
        <option value="desc" selected>Decrescente</option>
      </select>
    </div>
  </div>
  <div class="filtro-grupo" style="justify-content: flex-end;">
    <button class="btn-limpar" onclick="limpar()">Limpar filtros</button>
  </div>
  <div class="filtro-grupo" style="justify-content: flex-end;">
    <label>Acoes</label>
    <div class="acoes-wrap">
      <button class="btn-acao" onclick="baixarCsvFiltro()">Download CSV (filtro)</button>
      <button class="btn-acao" onclick="imprimirPdfFiltro()">Imprimir PDF (filtro)</button>
    </div>
  </div>
</div>

<div class="info-barra" id="info-barra">Carregando...</div>

<div class="tabela-wrap">
  <table id="tabela">
    <thead id="thead"></thead>
    <tbody id="tbody"></tbody>
  </table>
</div>

<script>
const DADOS = {dados_json};
const COLS  = {cabecalhos_json};
const LABELS = {{
  SUBGRUPO: 'Subgrupo', CODIGO_PRODUTO: 'Codigo', DESCRICAO_PRODUTO: 'Descricao',
  EMBALAGEM: 'Emb.', PERC_ACM: '% Acum.', PRECO_CUSTO: 'Custo',
  PRECO_VENDA: 'P. Venda', MARGEM_ATUAL: 'Margem %', MARGEM_OBJETIVA: 'Margem Obj.',
  QTD_VENDIDA: 'Qtd Vendida', ESTOQUE_MINIMO: 'Est. Min.', ESTOQUE_MAXIMO: 'Est. Max.',
  ESTOQUE_LOJA: 'Est. Loja', ESTOQUE_DEPOSITO: 'Est. CD', PENDENTE_EXPEDIR_CD: 'A Expedir CD'
}};
const COLS_NUM = new Set(['CODIGO_PRODUTO','EMBALAGEM','PERC_ACM','PRECO_CUSTO','PRECO_VENDA',
                          'MARGEM_ATUAL','MARGEM_OBJETIVA','QTD_VENDIDA',
                          'ESTOQUE_MINIMO','ESTOQUE_MAXIMO','ESTOQUE_LOJA','ESTOQUE_DEPOSITO','PENDENTE_EXPEDIR_CD']);
let DADOS_ATUAIS = [];

// Montar cabecalho uma vez
(function() {{
  const tr = document.createElement('tr');
  COLS.forEach(c => {{
    const th = document.createElement('th');
    th.textContent = LABELS[c] || c;
    tr.appendChild(th);
  }});
  document.getElementById('thead').appendChild(tr);
}})();

function sincronizarCabecalho() {{
  return;
}}

function coringaParaRegex(texto) {{
  // suporta * e % como coringas
  const escaped = texto.replace(/[.+^${{}}()|[\\]\\\\]/g, '\\\\$&');
  const pattern = escaped.replace(/[*%]/g, '.*');
  return new RegExp('^' + pattern + '$', 'i');
}}

function valorOrdenavel(campo, valor) {{
  if (valor == null || valor === '') return null;
  if (COLS_NUM.has(campo)) {{
    const texto = String(valor).trim().replace(/\\./g, '').replace(',', '.');
    const numero = Number(texto);
    return Number.isNaN(numero) ? null : numero;
  }}
  return String(valor).toUpperCase();
}}

function compararPorCampo(a, b, campo, direcao) {{
  const va = valorOrdenavel(campo, a[campo]);
  const vb = valorOrdenavel(campo, b[campo]);

  if (va == null && vb == null) return 0;
  if (va == null) return 1;
  if (vb == null) return -1;

  let comparacao = 0;
  if (typeof va === 'number' && typeof vb === 'number') {{
    comparacao = va - vb;
  }} else {{
    comparacao = String(va).localeCompare(String(vb), 'pt-BR');
  }}

  return direcao === 'desc' ? comparacao * -1 : comparacao;
}}

function ordenarDados(dados) {{
  const campo1 = document.getElementById('sel-ord1').value;
  const dir1 = document.getElementById('sel-dir1').value;
  const campo2 = document.getElementById('sel-ord2').value;
  const dir2 = document.getElementById('sel-dir2').value;

  return [...dados].sort((a, b) => {{
    const cmp1 = compararPorCampo(a, b, campo1, dir1);
    if (cmp1 !== 0) return cmp1;
    if (campo2) return compararPorCampo(a, b, campo2, dir2);
    return 0;
  }});
}}

function filtrar() {{
  const comprador  = document.getElementById('sel-comprador').value;
  const fornStr    = document.getElementById('inp-fornecedor').value.trim();
  const fornCodStr = document.getElementById('inp-fornecedor-cod').value.trim();
  let tornRegex    = null;
  if (fornStr) {{
    // Se nao tem coringa, busca por contido (contains)
    const temCoringa = /[*%]/.test(fornStr);
    tornRegex = temCoringa ? coringaParaRegex(fornStr) : new RegExp(fornStr.replace(/[.+^${{}}()|[\\]\\\\]/g, '\\\\$&'), 'i');
  }}

  const resultado = DADOS.filter(r => {{
    if (comprador && r.COMPRADOR !== comprador) return false;
    if (tornRegex && !tornRegex.test(r.FORNECEDOR_PRINCIPAL || '')) return false;
    if (fornCodStr && !(String(r.FORNECEDOR_CODIGO || '').includes(fornCodStr))) return false;
    return true;
  }});

  const dadosOrdenados = ordenarDados(resultado);
  DADOS_ATUAIS = dadosOrdenados;
  renderizar(dadosOrdenados);
}}

function escaparCsv(valor) {{
  if (valor == null) return '';
  const texto = String(valor);
  if (texto.includes(';') || texto.includes('"') || texto.includes('\\n')) {{
    return '"' + texto.replace(/"/g, '""') + '"';
  }}
  return texto;
}}

function baixarCsvFiltro() {{
  const cabecalhos = COLS.map(c => LABELS[c] || c);
  const linhas = [cabecalhos.join(';')];

  DADOS_ATUAIS.forEach(r => {{
    const linha = COLS.map(c => escaparCsv(r[c] != null ? r[c] : '')).join(';');
    linhas.push(linha);
  }});

  const csv = '\\ufeff' + linhas.join('\\n');
  const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  const timestamp = new Date().toISOString().slice(0,19).replace(/[:T]/g, '-');
  link.href = url;
  link.download = `abc_comprador_filtrado_${{timestamp}}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}}

function imprimirPdfFiltro() {{
  window.print();
}}

function renderizar(dados) {{
  const tbody = document.getElementById('tbody');
  tbody.innerHTML = '';

  document.getElementById('info-barra').innerHTML =
    `Exibindo <span>${{dados.length.toLocaleString('pt-BR')}}</span> de <span>${{DADOS.length.toLocaleString('pt-BR')}}</span> produtos`;

  if (dados.length === 0) {{
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = COLS.length;
    td.className = 'sem-dados';
    td.textContent = 'Nenhum produto encontrado.';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }}

  const frag = document.createDocumentFragment();
  dados.forEach(r => {{
    const tr = document.createElement('tr');
    COLS.forEach(c => {{
      const td = document.createElement('td');
      const val = r[c] != null ? r[c] : '';
      if (c === 'SUBGRUPO') {{
        td.innerHTML = `<span class="subgrupo-tag">${{val}}</span>`;
      }} else {{
        td.textContent = val;
      }}
      if (COLS_NUM.has(c)) td.className = 'col-num';
      tr.appendChild(td);
    }});
    frag.appendChild(tr);
  }});
  tbody.appendChild(frag);
}}

function limpar() {{
  document.getElementById('sel-comprador').value = '';
  document.getElementById('inp-fornecedor').value = '';
  document.getElementById('inp-fornecedor-cod').value = '';
  document.getElementById('sel-ord1').value = 'SUBGRUPO';
  document.getElementById('sel-dir1').value = 'asc';
  document.getElementById('sel-ord2').value = 'QTD_VENDIDA';
  document.getElementById('sel-dir2').value = 'desc';
  filtrar();
}}

// Renderizacao inicial
filtrar();
</script>
</body>
</html>"""

arquivo_html.write_text(html, encoding='utf-8')
print(f"Dashboard gerado: {arquivo_html}")

os.startfile(str(arquivo_html))
