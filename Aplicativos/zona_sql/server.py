import os
import sys
import json
import sqlite3
import re
import time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

PORT = 8550
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database', 'banco_simulador_consinco.db')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# -------------------------------------------------------------
# 1. Funções de Emulação Oracle para SQLite
# -------------------------------------------------------------
def oracle_nvl(val, default_val):
    if val is None or val == '':
        return default_val
    return val

def oracle_to_char(val, fmt=None):
    if val is None:
        return None
    if fmt and 'FM999' in fmt.upper():
        try:
            num = float(val)
            return f"R$ {num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return str(val)
    return str(val)

def oracle_to_number(val):
    if val is None or val == '':
        return None
    try:
        if isinstance(val, str):
            clean = val.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
            return float(clean)
        return float(val)
    except:
        return 0.0

def oracle_to_date(val, fmt=None):
    if not val:
        return None
    val_str = str(val).strip()
    for f in ('%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S'):
        try:
            dt = datetime.strptime(val_str[:19], f)
            return dt.strftime('%Y-%m-%d')
        except:
            continue
    return val_str[:10]

def oracle_trunc(val, fmt=None):
    if val is None:
        return None
    if isinstance(val, str) and len(val) >= 10:
        return val[:10]
    try:
        return int(float(val))
    except:
        return val

def oracle_sysdate():
    return datetime(2026, 8, 21).strftime('%Y-%m-%d')

def oracle_instr(string, substring, start=1, occurrence=1):
    if string is None or substring is None:
        return 0
    s_str = str(string)
    sub_str = str(substring)
    start_idx = max(0, int(start) - 1)
    pos = s_str.find(sub_str, start_idx)
    return pos + 1 if pos != -1 else 0

def oracle_substr(string, start, length=None):
    if string is None:
        return ''
    s_str = str(string)
    st = int(start)
    if st > 0:
        st_idx = st - 1
    elif st < 0:
        st_idx = len(s_str) + st
    else:
        st_idx = 0
    if length is None:
        return s_str[st_idx:]
    return s_str[st_idx : st_idx + int(length)]

def oracle_decode(*args):
    if len(args) < 3:
        return None
    expr = args[0]
    i = 1
    while i < len(args) - 1:
        if expr == args[i]:
            return args[i+1]
        i += 2
    if len(args) % 2 == 0:
        return args[-1]
    return None

def oracle_regexp_like(source, pattern):
    if source is None or pattern is None:
        return 0
    try:
        return 1 if re.search(pattern, str(source), re.IGNORECASE) else 0
    except:
        return 0

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Registrar funções Oracle
    conn.create_function("NVL", 2, oracle_nvl)
    conn.create_function("TO_CHAR", 1, oracle_to_char)
    conn.create_function("TO_CHAR", 2, oracle_to_char)
    conn.create_function("TO_NUMBER", 1, oracle_to_number)
    conn.create_function("TO_DATE", 1, oracle_to_date)
    conn.create_function("TO_DATE", 2, oracle_to_date)
    conn.create_function("TRUNC", 1, oracle_trunc)
    conn.create_function("TRUNC", 2, oracle_trunc)
    conn.create_function("SYSDATE", 0, oracle_sysdate)
    conn.create_function("INSTR", 2, oracle_instr)
    conn.create_function("INSTR", 3, oracle_instr)
    conn.create_function("SUBSTR", 2, oracle_substr)
    conn.create_function("SUBSTR", 3, oracle_substr)
    conn.create_function("DECODE", -1, oracle_decode)
    conn.create_function("REGEXP_LIKE", 2, oracle_regexp_like)
    return conn

# -------------------------------------------------------------
# 2. Pré-processador e Normalizador Oracle -> SQLite
# -------------------------------------------------------------
def preprocess_oracle_sql(sql, binds=None):
    if binds is None:
        binds = {}
    
    clean_sql = sql
    
    # 1. Substituir Macros Hash (#C_NROEMPRESA#, #LS1#, etc)
    for k, v in binds.items():
        macro_key = f"#{k}#"
        if macro_key in clean_sql:
            clean_sql = clean_sql.replace(macro_key, str(v))
            
    # Macros padrões se não fornecidas
    clean_sql = re.sub(r'#C_NROEMPRESA#', '1,2,3,4,5,6,7,8,11,12,13,14,15,17,18', clean_sql, flags=re.IGNORECASE)
    clean_sql = re.sub(r'#LT\d+#', "''", clean_sql, flags=re.IGNORECASE)
    clean_sql = re.sub(r'#LS\d+#', "'0 - TODOS'", clean_sql, flags=re.IGNORECASE)
    clean_sql = re.sub(r'#NR\d+#', '0', clean_sql, flags=re.IGNORECASE)

    # 2. Remover hints Oracle: /*+ MATERIALIZE */, /*+ INDEX(...) */
    clean_sql = re.sub(r'/\*\+\s*MATERIALIZE\s*\*/', '', clean_sql, flags=re.IGNORECASE)
    clean_sql = re.sub(r'/\*\+.*?\*/', '', clean_sql, flags=re.DOTALL)

    # 3. Remover chamadas de tabela DUAL
    clean_sql = re.sub(r'\s+FROM\s+DUAL\b', '', clean_sql, flags=re.IGNORECASE)

    # 4. Normalizar SYSDATE sem parênteses para SYSDATE()
    clean_sql = re.sub(r'\bSYSDATE\b(?!\s*\()', 'SYSDATE()', clean_sql, flags=re.IGNORECASE)

    # 5. Normalizar operador de concatenação Oracle '||' (SQLite suporta '||' nativo!)

    # 6. Injetar Binds (:NROEMPRESA, :NR1, :LS1, :LT1, :DT1)
    # Procurar por :variavel no SQL
    param_matches = re.findall(r':([A-Za-z0-9_]+)', clean_sql)
    for p in param_matches:
        val = binds.get(p, binds.get(p.upper(), None))
        if val is None:
            # Fallback inteligente para bind não preenchido
            if p.upper().startswith('NR') or 'EMPRESA' in p.upper() or 'COD' in p.upper():
                val = 0
            elif p.upper().startswith('DT'):
                val = '2026-08-21'
            elif p.upper().startswith('LS'):
                val = '0 - TODOS'
            else:
                val = ''
        
        # Se for string, escapa para SQL
        if isinstance(val, (int, float)):
            val_sql = str(val)
        else:
            val_escaped = str(val).replace("'", "''")
            val_sql = f"'{val_escaped}'"
            
        clean_sql = re.sub(rf':{p}\b', val_sql, clean_sql)

    return clean_sql

# -------------------------------------------------------------
# 3. Linter e Guardião de Regras Consinco
# -------------------------------------------------------------
def analyze_consinco_rules(raw_sql):
    alerts = []
    
    # Regra 1: Comentários no código SQL
    has_line_comment = bool(re.search(r'--[^\r\n]*', raw_sql))
    has_block_comment = bool(re.search(r'/\*(?!\+).*?\*/', raw_sql, flags=re.DOTALL))
    if has_line_comment or has_block_comment:
        alerts.append({
            'type': 'danger',
            'rule': 'Proibição Absoluta de Comentários no SQL Consinco',
            'message': 'Detectado comentário (-- ou /* */). O validador do Totvs Consinco remove quebras de linha e transforma o restante do código em um comentário gigante, causando erro fatal no SGI!',
            'suggestion': 'Remova todos os comentários antes de salvar ou utilize o botão "Limpar SQL para Consinco".'
        })

    # Regra 2: CTE iniciada diretamente com WITH sem SELECT Fantasma
    stripped = raw_sql.strip()
    if re.match(r'^WITH\b', stripped, flags=re.IGNORECASE):
        alerts.append({
            'type': 'danger',
            'rule': 'Bypass do Validador "Não é uma consulta" (Erro de CTE)',
            'message': 'O módulo de Consulta Criação do Consinco rejeita queries que iniciam com "WITH" acusando "A instrução SQL informada, não é uma consulta".',
            'suggestion': 'Envolva a consulta inteira no SELECT Fantasma: SELECT * FROM ( WITH ... SELECT ... )'
        })

    # Regra 3: CTE sem /*+ MATERIALIZE */
    if 'WITH' in raw_sql.upper():
        ctes = re.findall(r'WITH\s+([A-Za-z0-9_]+)\s+AS\s*\(\s*SELECT', raw_sql, flags=re.IGNORECASE)
        for cte_name in ctes:
            pattern = rf'WITH\s+{cte_name}\s+AS\s*\(\s*SELECT\s+/\*\+\s*MATERIALIZE\s*\*/'
            if not re.search(pattern, raw_sql, flags=re.IGNORECASE):
                alerts.append({
                    'type': 'warning',
                    'rule': 'Obrigatoriedade do Hint /*+ MATERIALIZE */ em CTEs',
                    'message': f'A CTE "{cte_name}" não contém o hint /*+ MATERIALIZE */.',
                    'suggestion': f'Insira /*+ MATERIALIZE */ logo após o SELECT da CTE: WITH {cte_name} AS (SELECT /*+ MATERIALIZE */ ...)'
                })

    # Regra 4: Aliases com aspas duplas ou caracteres especiais (ORA-00923)
    quote_aliases = re.findall(r'AS\s+"([^"]+)"', raw_sql, flags=re.IGNORECASE)
    if quote_aliases:
        alerts.append({
            'type': 'danger',
            'rule': 'Prevenção de ORA-00923 (Aliases com Aspas/Espaços)',
            'message': f'Encontrados aliases com aspas duplas: {quote_aliases[:3]}. O interpretador PL/SQL do Consinco quebra wrappers com aspas e acentos!',
            'suggestion': 'Utilize apenas letras maiúsculas e underscores (ex: AS CODIGO_PRODUTO).'
        })

    # Regra 5: STATUSVENDA na MRL_PRODUTOEMPRESA (ORA-00904)
    if re.search(r'MRL_PRODUTOEMPRESA\b.*?\bSTATUSVENDA\b', raw_sql, flags=re.IGNORECASE | re.DOTALL):
        alerts.append({
            'type': 'danger',
            'rule': 'Coluna Inexistente STATUSVENDA em MRL_PRODUTOEMPRESA (ORA-00904)',
            'message': 'A coluna STATUSVENDA NÃO existe na tabela MRL_PRODUTOEMPRESA no schema do Consinco.',
            'suggestion': 'Utilize STATUSCOMPRA na MRL_PRODUTOEMPRESA ou busque STATUSVENDA na MRL_PRODEMPSEG.'
        })

    # Regra 6: VLRVDA em MRL_PRODVENDADIA
    if re.search(r'MRL_PRODVENDADIA\b.*?\bVLRVDA\b', raw_sql, flags=re.IGNORECASE | re.DOTALL):
        alerts.append({
            'type': 'danger',
            'rule': 'Coluna Inexistente VLRVDA em MRL_PRODVENDADIA (ORA-00904)',
            'message': 'A coluna VLRVDA não existe na MRL_PRODVENDADIA neste ambiente.',
            'suggestion': 'Use QTDVDA * PRCBASE ou utilize a tabela oficial MRL_CUSTODIA para valores monetários de venda.'
        })

    # Regra 7: Join em MAP_FAMEMBALAGEM sem QTDEMBALAGEM = 1
    if 'MAP_FAMEMBALAGEM' in raw_sql.upper():
        if not re.search(r'QTDEMBALAGEM\s*=\s*1', raw_sql, flags=re.IGNORECASE):
            alerts.append({
                'type': 'warning',
                'rule': 'Risco de Multiplicação de Linhas em MAP_FAMEMBALAGEM',
                'message': 'Join com MAP_FAMEMBALAGEM sem filtrar QTDEMBALAGEM = 1 pode duplicar linhas caso haja caixas e embalagens múltiplas.',
                'suggestion': 'Adicione AND K.QTDEMBALAGEM = 1 na cláusula ON do JOIN.'
            })

    # Regra 8: Lista Branca de Lojas da Rede
    if 'MRL_PRODUTOEMPRESA' in raw_sql.upper() or 'MAX_EMPRESA' in raw_sql.upper():
        if not re.search(r'NROEMPRESA\s+IN\s*\(', raw_sql, flags=re.IGNORECASE) and not re.search(r':NROEMPRESA', raw_sql, flags=re.IGNORECASE) and not re.search(r'#C_NROEMPRESA#', raw_sql, flags=re.IGNORECASE):
            alerts.append({
                'type': 'info',
                'rule': 'Lista Branca de Lojas da Rede (Boas Práticas)',
                'message': 'A consulta não filtra empresas ativas da rede.',
                'suggestion': 'Filtre explicitamente: AND NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 17, 18)'
            })

    # Regra 9: Agregação de MRL_CUSTODIA antes do Join
    if 'MRL_CUSTODIA' in raw_sql.upper() and 'MRL_PRODUTOEMPRESA' in raw_sql.upper():
        if not re.search(r'\(.*SELECT.*FROM\s+MRL_CUSTODIA.*GROUP\s+BY.*\)', raw_sql, flags=re.IGNORECASE | re.DOTALL):
            alerts.append({
                'type': 'warning',
                'rule': 'Prevenção de Explosão Cartesiana com MRL_CUSTODIA',
                'message': 'Cruzar MRL_CUSTODIA com tabelas de estoque fixo sem agregação prévia multiplica indevidamente os saldos de estoque!',
                'suggestion': 'Agregue MRL_CUSTODIA por SEQPRODUTO e NROEMPRESA em uma subquery ou CTE antes do JOIN.'
            })

    return alerts

# -------------------------------------------------------------
# 4. Explicador Didático de Query
# -------------------------------------------------------------
def explain_query_pedagogical(sql):
    explanations = []
    sql_upper = sql.upper()
    
    # 1. Identificar Granularidade e Tabelas
    tables_found = []
    known_tables = {
        'MAP_PRODUTO': 'Cadastro geral do Produto (código, descrição, família)',
        'MAP_FAMILIA': 'Família de produtos (hierarquia tributária e comercial)',
        'MAP_CATEGORIA': 'Árvore de Departamentos, Seções e Grupos',
        'MAP_FAMDIVCATEG': 'Vínculo comercial da Família com a Categoria',
        'MAP_FAMDIVISAO': 'Configurações de compra e comprador da Família',
        'MAP_FAMEMBALAGEM': 'Embalagens e unidades de medida (Unitária vs Caixa)',
        'MAP_PRODCODIGO': 'Códigos de barras comerciais (EAN unitário e DUN caixa)',
        'MAX_COMPRADOR': 'Compradores responsáveis pelas categorias',
        'GE_PESSOA': 'Fornecedores e clientes cadastrados',
        'MRL_PRODUTOEMPRESA': 'Estoque operacional da loja, custos e parâmetros',
        'MRL_PRODEMPSEG': 'Preços de venda normais e promocionais por segmento',
        'MRL_PRODVENDADIA': 'Histórico diário de quantidades vendidas',
        'MRL_CUSTODIA': 'Vendas consolidadas e custo médio diário do dia',
        'FI_TITULO': 'Títulos financeiros a pagar (compras) e receber (verbas)',
        'MSU_PEDIDOSUPRIM': 'Pedidos de transferência e suprimento entre CD e Lojas',
        'MSU_PSITEMRECEBER': 'Itens e quantidades a receber em transferência/trânsito'
    }
    
    for t, desc in known_tables.items():
        if re.search(rf'\b{t}\b', sql_upper):
            tables_found.append({'tabela': t, 'funcao': desc})

    # 2. Detecção de Agregações
    aggs = []
    if 'SUM(' in sql_upper:
        aggs.append('Soma (SUM) de valores ou quantidades totais.')
    if 'AVG(' in sql_upper:
        aggs.append('Média aritmética (AVG) de valores ou preços.')
    if 'COUNT(' in sql_upper:
        aggs.append('Contagem de registros (COUNT).')
    if 'MAX(' in sql_upper or 'MIN(' in sql_upper:
        aggs.append('Extremos de datas ou valores (MAX / MIN).')

    # 3. Análise de Filtros
    filters = []
    if 'STATUSCOMPRA' in sql_upper:
        filters.append('Filtro de status de compra do item na filial.')
    if 'FINALIDADEFAMILIA' in sql_upper:
        filters.append('Filtro de finalidade para garantir itens de Revenda comercial.')
    if 'NROEMPRESA' in sql_upper:
        filters.append('Escopo delimitado por filiais/lojas da rede.')
    if 'BETWEEN' in sql_upper or 'DTA' in sql_upper:
        filters.append('Filtro temporal por período de datas.')

    return {
        'tabelas': tables_found,
        'agregacoes': aggs,
        'filtros': filters,
        'has_cte': 'WITH' in sql_upper,
        'is_complex': len(tables_found) > 2 or 'GROUP BY' in sql_upper
    }

# -------------------------------------------------------------
# 5. Handlers HTTP do Servidor
# -------------------------------------------------------------
class ConsincoSimulatorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(post_body) if post_body else {}

        if parsed.path == '/api/execute':
            self.handle_execute(data)
        elif parsed.path == '/api/lint':
            self.handle_lint(data)
        elif parsed.path == '/api/explain':
            self.handle_explain(data)
        elif parsed.path == '/api/clean_sql':
            self.handle_clean_sql(data)
        elif parsed.path == '/api/mission/verify':
            self.handle_mission_verify(data)
        else:
            self.send_error(404, "Endpoint nao encontrado")

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == '/api/tables':
            self.handle_get_tables()
        elif parsed.path.startswith('/api/table/'):
            tbl_name = parsed.path.split('/')[-1]
            self.handle_get_table_info(tbl_name)
        elif parsed.path == '/api/search_dictionary':
            query = params.get('q', [''])[0]
            self.handle_search_dictionary(query)
        elif parsed.path == '/api/missions':
            self.handle_get_missions()
        else:
            super().do_GET()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    # --- Endpoints da API ---
    def handle_execute(self, data):
        raw_sql = data.get('sql', '').strip()
        binds = data.get('binds', {})
        limit = data.get('limit', 500)

        if not raw_sql:
            self.send_json({'success': False, 'error': 'Nenhuma instrução SQL informada.'}, status=400)
            return

        alerts = analyze_consinco_rules(raw_sql)
        processed_sql = preprocess_oracle_sql(raw_sql, binds)

        start_time = time.time()
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(processed_sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchmany(limit)
            
            result_rows = []
            for r in rows:
                result_rows.append(list(r))

            exec_time_ms = round((time.time() - start_time) * 1000, 2)
            conn.close()

            self.send_json({
                'success': True,
                'columns': columns,
                'rows': result_rows,
                'row_count': len(result_rows),
                'execution_time_ms': exec_time_ms,
                'processed_sql': processed_sql,
                'alerts': alerts
            })
        except Exception as e:
            exec_time_ms = round((time.time() - start_time) * 1000, 2)
            error_msg = str(e)
            
            # Formatar erro em estilo Oracle Didático
            ora_code = "ORA-00900"
            if "no such column" in error_msg:
                ora_code = "ORA-00904: invalid identifier"
            elif "no such table" in error_msg:
                ora_code = "ORA-00942: table or view does not exist"
            elif "syntax error" in error_msg:
                ora_code = "ORA-00933: SQL command not properly ended"
            elif "ambiguous column" in error_msg:
                ora_code = "ORA-00918: column ambiguously defined"
            elif "GROUP BY" in error_msg.upper():
                ora_code = "ORA-00979: not a GROUP BY expression"

            self.send_json({
                'success': False,
                'error': f"{ora_code} -> {error_msg}",
                'raw_error': error_msg,
                'execution_time_ms': exec_time_ms,
                'processed_sql': processed_sql,
                'alerts': alerts
            }, status=200)

    def handle_lint(self, data):
        raw_sql = data.get('sql', '')
        alerts = analyze_consinco_rules(raw_sql)
        self.send_json({'alerts': alerts})

    def handle_explain(self, data):
        raw_sql = data.get('sql', '')
        explanation = explain_query_pedagogical(raw_sql)
        alerts = analyze_consinco_rules(raw_sql)
        self.send_json({'explanation': explanation, 'alerts': alerts})

    def handle_clean_sql(self, data):
        raw_sql = data.get('sql', '')
        # Remove comentários de linha e de bloco
        cleaned = re.sub(r'--[^\r\n]*', '', raw_sql)
        cleaned = re.sub(r'/\*(?!\+).*?\*/', '', cleaned, flags=re.DOTALL)
        # Remove linhas em branco extras
        cleaned = "\n".join([line for line in cleaned.splitlines() if line.strip()])
        self.send_json({'cleaned_sql': cleaned})

    def handle_get_tables(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'colunas' ORDER BY name")
        tables = []
        for row in cursor.fetchall():
            t_name = row[0]
            try:
                cursor.execute(f"SELECT count(*) FROM {t_name}")
                cnt = cursor.fetchone()[0]
            except:
                cnt = 0
            tables.append({'name': t_name, 'row_count': cnt})
        conn.close()
        self.send_json({'tables': tables})

    def handle_get_table_info(self, tbl_name):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Estrutura de colunas
        cursor.execute(f"PRAGMA table_info({tbl_name})")
        cols = []
        for c in cursor.fetchall():
            cols.append({
                'cid': c[0],
                'name': c[1],
                'type': c[2],
                'notnull': bool(c[3]),
                'pk': bool(c[5])
            })
            
        # Amostra de dados (20 linhas)
        try:
            cursor.execute(f"SELECT * FROM {tbl_name} LIMIT 20")
            sample_columns = [desc[0] for desc in cursor.description]
            sample_rows = [list(r) for r in cursor.fetchall()]
        except:
            sample_columns = []
            sample_rows = []
            
        conn.close()
        self.send_json({
            'table': tbl_name,
            'columns': cols,
            'sample_columns': sample_columns,
            'sample_rows': sample_rows
        })

    def handle_search_dictionary(self, query):
        conn = get_db_connection()
        cursor = conn.cursor()
        q_upper = f"%{query.upper()}%"
        cursor.execute("""
            SELECT NOME_TABELA, NOME_COLUNA, TIPO_DADOS, DESCRICAO_COLUNA 
            FROM colunas 
            WHERE NOME_TABELA LIKE ? OR NOME_COLUNA LIKE ? OR DESCRICAO_COLUNA LIKE ?
            ORDER BY NOME_TABELA, CAST(ORDEM AS INTEGER)
            LIMIT 100
        """, (q_upper, q_upper, q_upper))
        results = []
        for r in cursor.fetchall():
            results.append({
                'tabela': r['NOME_TABELA'],
                'coluna': r['NOME_COLUNA'],
                'tipo': r['TIPO_DADOS'],
                'descricao': r['DESCRICAO_COLUNA']
            })
        conn.close()
        self.send_json({'results': results})

    def handle_get_missions(self):
        missions = [
            {
                'id': 1,
                'title': 'Missão 1: Conhecendo os Produtos Ativos da Loja 1',
                'difficulty': 'Iniciante',
                'category': 'Básico',
                'description': 'Faça uma consulta listando o código do produto (SEQPRODUTO), a descrição completa (DESCCOMPLETA) e o preço base (PRCBASE) para a empresa 1 onde o produto esteja ativo para compra.',
                'starter_sql': "SELECT\n    A.SEQPRODUTO,\n    A.DESCCOMPLETA,\n    B.PRCBASE\nFROM MAP_PRODUTO A\nINNER JOIN MRL_PRODUTOEMPRESA B ON A.SEQPRODUTO = B.SEQPRODUTO\nWHERE B.NROEMPRESA = 1\n  AND B.STATUSCOMPRA = 'A'",
                'hint': 'Junte MAP_PRODUTO (A) com MRL_PRODUTOEMPRESA (B) por SEQPRODUTO e filtre NROEMPRESA = 1 e STATUSCOMPRA = \'A\'.'
            },
            {
                'id': 2,
                'title': 'Missão 2: Hierarquia Comercial (Departamento Nível 1)',
                'difficulty': 'Iniciante',
                'category': 'Joins',
                'description': 'Descubra a qual Departamento (MAP_CATEGORIA Nível 1) cada produto pertence. Liste SEQPRODUTO, DESCCOMPLETA e o nome da CATEGORIA.',
                'starter_sql': "SELECT\n    A.SEQPRODUTO,\n    A.DESCCOMPLETA,\n    C.CATEGORIA AS DEPARTAMENTO\nFROM MAP_PRODUTO A\nINNER JOIN MAP_FAMDIVCATEG B ON A.SEQFAMILIA = B.SEQFAMILIA AND B.NRODIVISAO = 1\nINNER JOIN MAP_CATEGORIA C ON B.SEQCATEGORIA = C.SEQCATEGORIA AND C.NIVELHIERARQUIA = 1",
                'hint': 'Cruze MAP_PRODUTO com MAP_FAMDIVCATEG pela SEQFAMILIA e depois com MAP_CATEGORIA com filtro C.NIVELHIERARQUIA = 1 para evitar duplicar subníveis.'
            },
            {
                'id': 3,
                'title': 'Missão 3: Cálculo do Estoque Disponível Real',
                'difficulty': 'Intermediário',
                'category': 'Cálculos',
                'description': 'Calcule o estoque disponível real na Loja 1 abatendo as reservas de venda e recebimento: (ESTQLOJA + ESTQDEPOSITO - QTDRESERVADAVDA - QTDRESERVADARECEB - QTDRESERVADAFIXA).',
                'starter_sql': "SELECT\n    A.SEQPRODUTO,\n    A.DESCCOMPLETA,\n    B.ESTQLOJA,\n    B.ESTQDEPOSITO,\n    (B.ESTQLOJA + B.ESTQDEPOSITO - B.QTDRESERVADAVDA - B.QTDRESERVADARECEB - B.QTDRESERVADAFIXA) AS ESTOQUE_DISPONIVEL\nFROM MAP_PRODUTO A\nINNER JOIN MRL_PRODUTOEMPRESA B ON A.SEQPRODUTO = B.SEQPRODUTO\nWHERE B.NROEMPRESA = 1",
                'hint': 'Aplique a fórmula oficial do Consinco para estoque disponível sem esquecer de subtrair as reservas.'
            },
            {
                'id': 4,
                'title': 'Missão 4: Preço Vigente (Promocional vs Normal)',
                'difficulty': 'Intermediário',
                'category': 'Funções Oracle',
                'description': 'Consulte o preço praticado na Loja 1 usando NVL e NULLIF na tabela MRL_PRODEMPSEG: se houver PRECOVALIDPROMOC > 0 use ele, senão use o PRECOVALIDNORMAL.',
                'starter_sql': "SELECT\n    A.SEQPRODUTO,\n    A.DESCCOMPLETA,\n    P.PRECOVALIDNORMAL,\n    P.PRECOVALIDPROMOC,\n    NVL(NULLIF(P.PRECOVALIDPROMOC, 0), P.PRECOVALIDNORMAL) AS PRECO_PRATICADO\nFROM MAP_PRODUTO A\nINNER JOIN MRL_PRODEMPSEG P ON A.SEQPRODUTO = P.SEQPRODUTO\nWHERE P.NROEMPRESA = 1\n  AND P.STATUSVENDA = 'A'",
                'hint': 'NULLIF(PRECOVALIDPROMOC, 0) transforma 0 em NULL, e o NVL assume o PRECOVALIDNORMAL como fallback!'
            },
            {
                'id': 5,
                'title': 'Missão 5: CTE Materializada com Bypass do Consinco',
                'difficulty': 'Avançado',
                'category': 'Performance & CTE',
                'description': 'Construa uma consulta agrupando o total de estoque de toda a rede em uma CTE com /*+ MATERIALIZE */ e envelopada no SELECT * FROM (...) para passar no validador do Consinco.',
                'starter_sql': "SELECT * FROM (\n    WITH ESTOQUE_REDE AS (\n        SELECT /*+ MATERIALIZE */\n            SEQPRODUTO,\n            SUM(ESTQLOJA + ESTQDEPOSITO) AS TOTAL_ESTOQUE_REDE\n        FROM MRL_PRODUTOEMPRESA\n        WHERE NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 17, 18)\n        GROUP BY SEQPRODUTO\n    )\n    SELECT\n        P.SEQPRODUTO,\n        P.DESCCOMPLETA,\n        E.TOTAL_ESTOQUE_REDE\n    FROM MAP_PRODUTO P\n    INNER JOIN ESTOQUE_REDE E ON P.SEQPRODUTO = E.SEQPRODUTO\n    ORDER BY E.TOTAL_ESTOQUE_REDE DESC\n)",
                'hint': 'Lembre-se: SELECT * FROM ( WITH ... ) é a regra inquebrável para salvar CTEs no painel Consulta Criação!'
            },
            {
                'id': 6,
                'title': 'Missão 6: Parametrização Dinâmica de Tela (Var - F7)',
                'difficulty': 'Avançado',
                'category': 'Parametrização',
                'description': 'Crie uma consulta parametrizada com variável bind de Loja (:NROEMPRESA) e Fornecedor (:NR1) com fallback usando NVL e TO_NUMBER.',
                'starter_sql': "SELECT\n    A.SEQPRODUTO,\n    A.DESCCOMPLETA,\n    F.NOMERAZAO AS FORNECEDOR,\n    B.PRCBASE,\n    B.ESTQLOJA\nFROM MAP_PRODUTO A\nINNER JOIN MRL_PRODUTOEMPRESA B ON A.SEQPRODUTO = B.SEQPRODUTO\nINNER JOIN MAP_FAMFORNEC FF ON A.SEQFAMILIA = FF.SEQFAMILIA AND FF.PRINCIPAL = 'S'\nINNER JOIN GE_PESSOA F ON FF.SEQPESSOA = F.SEQPESSOA\nWHERE B.NROEMPRESA = :NROEMPRESA\n  AND (TO_NUMBER(NVL(:NR1, 0)) = 0 OR F.SEQPESSOA = TO_NUMBER(:NR1))",
                'hint': 'Altere o valor de :NROEMPRESA e :NR1 na gaveta Var-F7 para testar a filtragem dinâmica!'
            }
        ]
        self.send_json({'missions': missions})

    def handle_mission_verify(self, data):
        mission_id = data.get('mission_id')
        user_sql = data.get('sql', '').strip()
        
        if not user_sql:
            self.send_json({'success': False, 'message': 'Digite uma query antes de verificar.'})
            return

        processed = preprocess_oracle_sql(user_sql, {'NROEMPRESA': 1, 'NR1': 0})
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(processed)
            rows = cursor.fetchall()
            row_cnt = len(rows)
            conn.close()

            if row_cnt > 0:
                self.send_json({
                    'success': True,
                    'passed': True,
                    'message': f'Parabéns! Sua consulta retornou com sucesso {row_cnt} registros!',
                    'row_count': row_cnt
                })
            else:
                self.send_json({
                    'success': True,
                    'passed': False,
                    'message': 'A consulta executou, mas retornou 0 linhas. Revise os filtros WHERE e JOINs.',
                    'row_count': 0
                })
        except Exception as e:
            self.send_json({
                'success': False,
                'passed': False,
                'message': f'Erro na execução da consulta: {str(e)}'
            })

def run_server():
    print("=======================================================")
    print("INICIANDO ZONA SQL - SIMULADOR & MENTOR CONSINCO")
    print(f"Servidor rodando em: http://127.0.0.1:{PORT}")
    print(f"Banco Conectado: {DB_PATH}")
    print("=======================================================")
    server = ThreadingHTTPServer(('127.0.0.1', PORT), ConsincoSimulatorHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
        server.server_close()

if __name__ == '__main__':
    run_server()
