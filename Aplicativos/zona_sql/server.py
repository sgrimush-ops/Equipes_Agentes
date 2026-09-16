import os
import sys
import json
import sqlite3
import re
import time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from mentor_ai import ollama_mentor, GEMINI_MODELS

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
    val_str = str(val).strip()
    if fmt:
        fmt_upper = fmt.upper()
        if 'FM999' in fmt_upper or '999G999' in fmt_upper:
            try:
                num = float(val)
                # Formato brasileiro com milhar . e decimal ,
                return f"{num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            except:
                return val_str
        elif 'DD/MM/YYYY' in fmt_upper:
            for f in ('%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S'):
                try:
                    dt = datetime.strptime(val_str[:19], f)
                    return dt.strftime('%d/%m/%Y')
                except:
                    continue
            return val_str[:10]
    return val_str

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
    for f in ('%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%d-%m-%Y'):
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

def oracle_lpad(val, length, pad=' '):
    if val is None:
        return ''
    s = str(val)
    pad_str = str(pad)[:1] if pad else ' '
    l = int(length)
    if len(s) >= l:
        return s[:l]
    return (pad_str * (l - len(s))) + s

def oracle_rpad(val, length, pad=' '):
    if val is None:
        return ''
    s = str(val)
    pad_str = str(pad)[:1] if pad else ' '
    l = int(length)
    if len(s) >= l:
        return s[:l]
    return s + (pad_str * (l - len(s)))

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
    conn.create_function("LPAD", 2, lambda v, l: oracle_lpad(v, l, ' '))
    conn.create_function("LPAD", 3, oracle_lpad)
    conn.create_function("RPAD", 2, lambda v, l: oracle_rpad(v, l, ' '))
    conn.create_function("RPAD", 3, oracle_rpad)
    return conn

def transpile_oracle_merge(sql):
    if not re.search(r'^\s*MERGE\s+INTO\b', sql, flags=re.IGNORECASE):
        return sql
    
    using_match = re.search(r'USING\s*\((.*?)\)\s*ORIG', sql, flags=re.IGNORECASE | re.DOTALL)
    if not using_match:
        return sql
    
    selects = re.findall(r'SELECT\s+(.*?)\s+FROM\s+DUAL', using_match.group(1), flags=re.IGNORECASE)
    dml_statements = []
    
    for s in selects:
        items = re.findall(r'(.*?)\s+AS\s+([A-Za-z0-9_]+)', s, flags=re.IGNORECASE)
        d = {}
        for val, col in items:
            val_clean = val.strip().lstrip(',').strip()
            val_clean = re.sub(r"TO_DATE\s*\(\s*'([^']+)'\s*,\s*'[^']+'\s*\)", r"'\1'", val_clean, flags=re.IGNORECASE)
            d[col.upper()] = val_clean
            
        ponto = d.get('SEQPONTOEXTRA', '0')
        prod = d.get('SEQPRODUTO', '0')
        emp = d.get('NROEMPRESA', '1')
        minimo = d.get('ESTQMINIMO', '0.0')
        maximo = d.get('ESTQMAXIMO', '0.0')
        ini = d.get('DTAVIGENCIAINICIO', "'2026-08-01'")
        fim = d.get('DTAVIGENCIAFIM', "'2026-12-31'")
        status = d.get('STATUS', "'A'")
        seqvig = d.get('SEQVIGENCIA', '1')
        qtddias = d.get('QTDDIASSUGESTAO', '0.0')
        
        dml_statements.append(f"INSERT OR IGNORE INTO MRL_PONTOEXTRAPRODUTO (SEQPONTOEXTRA, SEQPRODUTO, STATUS) VALUES ({ponto}, {prod}, 'A');")
        dml_statements.append(f"UPDATE MRL_PONTOEXTRAPRODUTOEMPRESA SET ESTQMINIMO = {minimo}, ESTQMAXIMO = {maximo}, DTAVIGENCIAINICIO = {ini}, DTAVIGENCIAFIM = {fim}, STATUS = {status} WHERE SEQPONTOEXTRA = {ponto} AND SEQPRODUTO = {prod} AND NROEMPRESA = {emp};")
        dml_statements.append(f"INSERT OR IGNORE INTO MRL_PONTOEXTRAPRODUTOEMPRESA (SEQPONTOEXTRA, SEQPRODUTO, NROEMPRESA, SEQVIGENCIA, ESTQMINIMO, ESTQMAXIMO, DTAVIGENCIAINICIO, DTAVIGENCIAFIM, QTDDIASSUGESTAO, STATUS) VALUES ({ponto}, {prod}, {emp}, {seqvig}, {minimo}, {maximo}, {ini}, {fim}, {qtddias}, {status});")
        
    return "\n".join(dml_statements)

# -------------------------------------------------------------
# 2. Pré-processador e Normalizador Oracle -> SQLite
# -------------------------------------------------------------
def preprocess_oracle_sql(sql, binds=None):
    if binds is None:
        binds = {}
    
    clean_sql = sql

    # 0. Transpilar MERGE INTO do Oracle para instruções compatíveis com SQLite
    clean_sql = transpile_oracle_merge(clean_sql)
    
    # 1. Substituir Macros Hash (#C_NROEMPRESA#, #LS1#, #LT1, etc)
    for k, v in binds.items():
        val_macro = str(v).strip()
        if val_macro == '':
            if k.upper().startswith('LT'):
                val_macro = 'NULL'
            elif k.upper().startswith('NR'):
                val_macro = '0'
            else:
                val_macro = "''"
        clean_sql = re.sub(rf'#{re.escape(k)}#?', val_macro, clean_sql, flags=re.IGNORECASE)
            
    # Macros padrões se não fornecidas
    clean_sql = re.sub(r'#C_NROEMPRESA#?', '1,2,3,4,5,6,7,8,11,12,13,14,15,16,17,18,50', clean_sql, flags=re.IGNORECASE)
    clean_sql = re.sub(r'#LT\d+#?', 'NULL', clean_sql, flags=re.IGNORECASE)
    clean_sql = re.sub(r'#LS\d+#?', "''", clean_sql, flags=re.IGNORECASE)
    clean_sql = re.sub(r'#NR\d+#?', '0', clean_sql, flags=re.IGNORECASE)
    clean_sql = re.sub(r'#DT\d+#?', "''", clean_sql, flags=re.IGNORECASE)

    # 2. Remover hints Oracle: /*+ MATERIALIZE */, /*+ INDEX(...) */
    clean_sql = re.sub(r'/\*\+\s*MATERIALIZE\s*\*/', '', clean_sql, flags=re.IGNORECASE)
    clean_sql = re.sub(r'/\*\+.*?\*/', '', clean_sql, flags=re.DOTALL)

    # 3. Normalizar TO_DATE('YYYY-MM-DD', '...')
    clean_sql = re.sub(r"TO_DATE\s*\(\s*'([^']+)'\s*,\s*'[^']+'\s*\)", r"'\1'", clean_sql, flags=re.IGNORECASE)

    # 4. Remover chamadas de tabela DUAL
    clean_sql = re.sub(r'\s+FROM\s+DUAL\b', '', clean_sql, flags=re.IGNORECASE)

    # 5. Normalizar SYSDATE sem parênteses para SYSDATE()
    clean_sql = re.sub(r'\bSYSDATE\b(?!\s*\()', 'SYSDATE()', clean_sql, flags=re.IGNORECASE)

    # 5.1 Transpilar aritmética de datas Oracle para SQLite (TRUNC(:DT) + N / TRUNC(:DT) - N)
    clean_sql = re.sub(r"TRUNC\s*\(\s*(:\w+)\s*\)\s*\+\s*(\d+)", r"DATE(\1, '+\2 day')", clean_sql, flags=re.IGNORECASE)
    clean_sql = re.sub(r"TRUNC\s*\(\s*(:\w+)\s*\)\s*-\s*(\d+)", r"DATE(\1, '-\2 day')", clean_sql, flags=re.IGNORECASE)

    # 6. Injetar Binds (:NROEMPRESA, :NR1..4, :LS1..4, :LT1..4, :DT1..4)
    param_matches = re.findall(r':([A-Za-z0-9_]+)', clean_sql)
    for p in param_matches:
        val = binds.get(p, binds.get(p.upper(), None))
        p_upper = p.upper()
        if val is None or val == '':
            if p_upper.startswith('NR') or 'EMPRESA' in p_upper or 'COD' in p_upper or 'PONTO' in p_upper:
                val = 0
            else:
                val = ''
        
        # Se for numérico, injeta número; senão, escapa string
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
    sql_upper = raw_sql.upper()
    
    # Regra 1: Comentários no código SQL (ignorar strings literais como '--')
    sql_without_strings = re.sub(r"'(''|[^'])*'", "''", raw_sql)
    has_line_comment = bool(re.search(r'--[^\r\n]*', sql_without_strings))
    has_block_comment = bool(re.search(r'/\*(?!\+).*?\*/', sql_without_strings, flags=re.DOTALL))
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
    if 'WITH' in sql_upper:
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

    # Regra DML: UPDATE sem WHERE
    if re.search(r'^\s*UPDATE\b', stripped, flags=re.IGNORECASE) and not re.search(r'\bWHERE\b', stripped, flags=re.IGNORECASE):
        alerts.append({
            'type': 'danger',
            'rule': 'ALERTA CRÍTICO: UPDATE sem Cláusula WHERE!',
            'message': 'Comando UPDATE sem WHERE afetará TODOS os registros da tabela no banco de dados da rede inteira!',
            'suggestion': 'Especifique as chaves primárias no WHERE (ex: WHERE SEQPONTOEXTRA = :SEQPONTOEXTRA AND SEQPRODUTO = :SEQPRODUTO AND NROEMPRESA = :NROEMPRESA).'
        })

    # Regra DML: DELETE sem WHERE
    if re.search(r'^\s*DELETE\b', stripped, flags=re.IGNORECASE) and not re.search(r'\bWHERE\b', stripped, flags=re.IGNORECASE):
        alerts.append({
            'type': 'danger',
            'rule': 'ALERTA CRÍTICO: DELETE sem Cláusula WHERE!',
            'message': 'Comando DELETE sem WHERE apagará todas as linhas da tabela permanentemente!',
            'suggestion': 'Adicione cláusula WHERE com os filtros ou chaves primárias.'
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
    if 'MAP_FAMEMBALAGEM' in sql_upper:
        if not re.search(r'QTDEMBALAGEM\s*=\s*1', raw_sql, flags=re.IGNORECASE):
            alerts.append({
                'type': 'warning',
                'rule': 'Risco de Multiplicação de Linhas em MAP_FAMEMBALAGEM',
                'message': 'Join com MAP_FAMEMBALAGEM sem filtrar QTDEMBALAGEM = 1 pode duplicar linhas caso haja caixas e embalagens múltiplas.',
                'suggestion': 'Adicione AND K.QTDEMBALAGEM = 1 na cláusula ON do JOIN.'
            })

    # Regra 8: Lista Branca de Lojas da Rede
    if ('MRL_PRODUTOEMPRESA' in sql_upper or 'MAX_EMPRESA' in sql_upper or 'MRL_PONTOEXTRAPRODUTOEMPRESA' in sql_upper) and 'UPDATE' not in sql_upper:
        if not re.search(r'NROEMPRESA\s+IN\s*\(', raw_sql, flags=re.IGNORECASE) and not re.search(r':NROEMPRESA', raw_sql, flags=re.IGNORECASE) and not re.search(r'#C_NROEMPRESA#', raw_sql, flags=re.IGNORECASE) and not re.search(r'NROEMPRESA\s*=', raw_sql, flags=re.IGNORECASE):
            alerts.append({
                'type': 'info',
                'rule': 'Lista Branca de Lojas da Rede (Boas Práticas)',
                'message': 'A consulta não filtra empresas ativas da rede.',
                'suggestion': 'Filtre explicitamente: AND NROEMPRESA IN (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 17, 18)'
            })

    # Regra 9: Agregação de MRL_CUSTODIA antes do Join
    if 'MRL_CUSTODIA' in sql_upper and 'MRL_PRODUTOEMPRESA' in sql_upper:
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
        'MAX_EMPRESA': 'Cadastro das Lojas, Filiais e Centros de Distribuição (CDs)',
        'GE_PESSOA': 'Fornecedores e clientes cadastrados',
        'MRL_PONTOEXTRA': 'Capa de Pontos Extras / Pontas de Gôndola / Ilhas de Loja',
        'MRL_PONTOEXTRAPRODUTO': 'Vínculo do Produto ao Ponto Extra (SEQPONTOEXTRA + SEQPRODUTO)',
        'MRL_PONTOEXTRAPRODUTOEMPRESA': 'Regras de Estoque Mínimo/Máximo, Vigência e Sugestão por Loja',
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

    # 2. Detecção de Agregações e Ações
    aggs = []
    if 'UPDATE ' in sql_upper:
        aggs.append('Instrução DML UPDATE: altera registros existentes no banco.')
    if 'INSERT INTO' in sql_upper:
        aggs.append('Instrução DML INSERT: insere novos registros na tabela.')
    if 'MERGE INTO' in sql_upper:
        aggs.append('Instrução MERGE INTO: sincronização inteligente (atualiza se existir, insere se não existir).')
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
    if 'SEQPONTOEXTRA' in sql_upper:
        filters.append('Filtro por Identificador do Ponto Extra (ex: 203 Ponta de Gôndola).')
    if 'SEQPRODUTO' in sql_upper:
        filters.append('Chave primária do produto (SEQPRODUTO) utilizada para amarração exata.')
    if 'STATUSCOMPRA' in sql_upper or 'STATUS' in sql_upper:
        filters.append('Filtro de status de ativação (A = Ativo / I = Inativo).')
    if 'FINALIDADEFAMILIA' in sql_upper:
        filters.append('Filtro de finalidade para garantir itens de Revenda comercial.')
    if 'NROEMPRESA' in sql_upper:
        filters.append('Escopo delimitado por filiais/lojas da rede.')
    if 'BETWEEN' in sql_upper or 'DTA' in sql_upper or 'VIGENCIA' in sql_upper:
        filters.append('Filtro temporal por período de datas ou vigência da promoção/ponta.')

    return {
        'tabelas': tables_found,
        'agregacoes': aggs,
        'filtros': filters,
        'has_cte': 'WITH' in sql_upper,
        'is_complex': len(tables_found) > 2 or 'GROUP BY' in sql_upper
    }

# -------------------------------------------------------------
# 5. Gerador de Scripts Oracle de Carga / MERGE / UPDATE
# -------------------------------------------------------------
def generate_oracle_update_scripts(valid_rows):
    if not valid_rows:
        return {'merge_sql': '', 'batch_dml_sql': '', 'select_check_sql': ''}

    # 1. Script MERGE INTO (Padrão Oficial Oracle)
    select_unions = []
    seqponto_set = set()
    seqprod_set = set()

    for r in valid_rows:
        seqponto_set.add(str(r['seqpontoextra']))
        seqprod_set.add(str(r['seqproduto']))
        select_unions.append(
            f"    SELECT {r['seqpontoextra']} AS SEQPONTOEXTRA, {r['seqproduto']} AS SEQPRODUTO, {r['nroempresa']} AS NROEMPRESA, {r['seqvigencia']} AS SEQVIGENCIA, {r['estqminimo']:.1f} AS ESTQMINIMO, {r['estqmaximo']:.1f} AS ESTQMAXIMO, TO_DATE('{r['dtavigenciainicio']}', 'YYYY-MM-DD') AS DTAVIGENCIAINICIO, TO_DATE('{r['dtavigenciafim']}', 'YYYY-MM-DD') AS DTAVIGENCIAFIM, {r['qtddiassugestao']:.1f} AS QTDDIASSUGESTAO, '{r['status']}' AS STATUS FROM DUAL"
        )

    union_block = "\n    UNION ALL\n".join(select_unions)

    merge_sql = f"""MERGE INTO MRL_PONTOEXTRAPRODUTOEMPRESA DEST
USING (
{union_block}
) ORIG
ON (
    DEST.SEQPONTOEXTRA = ORIG.SEQPONTOEXTRA
    AND DEST.SEQPRODUTO = ORIG.SEQPRODUTO
    AND DEST.NROEMPRESA = ORIG.NROEMPRESA
)
WHEN MATCHED THEN
    UPDATE SET
        DEST.ESTQMINIMO         = ORIG.ESTQMINIMO,
        DEST.ESTQMAXIMO         = ORIG.ESTQMAXIMO,
        DEST.DTAVIGENCIAINICIO  = ORIG.DTAVIGENCIAINICIO,
        DEST.DTAVIGENCIAFIM     = ORIG.DTAVIGENCIAFIM,
        DEST.QTDDIASSUGESTAO    = ORIG.QTDDIASSUGESTAO,
        DEST.STATUS             = ORIG.STATUS
WHEN NOT MATCHED THEN
    INSERT (
        SEQPONTOEXTRA, SEQPRODUTO, NROEMPRESA, SEQVIGENCIA,
        ESTQMINIMO, ESTQMAXIMO, DTAVIGENCIAINICIO, DTAVIGENCIAFIM,
        QTDDIASSUGESTAO, STATUS
    ) VALUES (
        ORIG.SEQPONTOEXTRA, ORIG.SEQPRODUTO, ORIG.NROEMPRESA, ORIG.SEQVIGENCIA,
        ORIG.ESTQMINIMO, ORIG.ESTQMAXIMO, ORIG.DTAVIGENCIAINICIO, ORIG.DTAVIGENCIAFIM,
        ORIG.QTDDIASSUGESTAO, ORIG.STATUS
    );
COMMIT;"""

    # 2. Script Blocos DML Transacionais (UPDATE / INSERT)
    dml_lines = []
    # Garantir capa na MRL_PONTOEXTRAPRODUTO
    pairs_done = set()
    for r in valid_rows:
        pair = (r['seqpontoextra'], r['seqproduto'])
        if pair not in pairs_done:
            pairs_done.add(pair)
            dml_lines.append(f"INSERT INTO MRL_PONTOEXTRAPRODUTO (SEQPONTOEXTRA, SEQPRODUTO, STATUS) SELECT {r['seqpontoextra']}, {r['seqproduto']}, 'A' FROM DUAL WHERE NOT EXISTS (SELECT 1 FROM MRL_PONTOEXTRAPRODUTO WHERE SEQPONTOEXTRA = {r['seqpontoextra']} AND SEQPRODUTO = {r['seqproduto']});")

    for r in valid_rows:
        if r['action'] == 'UPDATE':
            dml_lines.append(f"UPDATE MRL_PONTOEXTRAPRODUTOEMPRESA SET ESTQMINIMO = {r['estqminimo']:.1f}, ESTQMAXIMO = {r['estqmaximo']:.1f}, DTAVIGENCIAINICIO = TO_DATE('{r['dtavigenciainicio']}', 'YYYY-MM-DD'), DTAVIGENCIAFIM = TO_DATE('{r['dtavigenciafim']}', 'YYYY-MM-DD'), STATUS = '{r['status']}' WHERE SEQPONTOEXTRA = {r['seqpontoextra']} AND SEQPRODUTO = {r['seqproduto']} AND NROEMPRESA = {r['nroempresa']};")
        else:
            dml_lines.append(f"INSERT INTO MRL_PONTOEXTRAPRODUTOEMPRESA (SEQPONTOEXTRA, SEQPRODUTO, NROEMPRESA, SEQVIGENCIA, ESTQMINIMO, ESTQMAXIMO, DTAVIGENCIAINICIO, DTAVIGENCIAFIM, QTDDIASSUGESTAO, STATUS) VALUES ({r['seqpontoextra']}, {r['seqproduto']}, {r['nroempresa']}, {r['seqvigencia']}, {r['estqminimo']:.1f}, {r['estqmaximo']:.1f}, TO_DATE('{r['dtavigenciainicio']}', 'YYYY-MM-DD'), TO_DATE('{r['dtavigenciafim']}', 'YYYY-MM-DD'), {r['qtddiassugestao']:.1f}, '{r['status']}');")

    dml_lines.append("COMMIT;")
    batch_dml_sql = "\n".join(dml_lines)

    # 3. Consulta de Auditoria e Conferência
    pontos_str = ",".join(list(seqponto_set)[:10]) or "203"
    prods_str = ",".join(list(seqprod_set)[:20]) or "10"

    select_check_sql = f"""SELECT
    A.SEQPONTOEXTRA,
    PE.DESCRICAO AS DESCRICAO_PONTO,
    A.SEQPRODUTO,
    P.DESCCOMPLETA AS PRODUTO,
    A.NROEMPRESA,
    LPAD(E.NROEMPRESA, 6, '0') || ' - ' || E.NOMERAZAO AS LOJA,
    A.ESTQMINIMO,
    A.ESTQMAXIMO,
    A.DTAVIGENCIAINICIO,
    A.DTAVIGENCIAFIM,
    A.STATUS
FROM MRL_PONTOEXTRAPRODUTOEMPRESA A
INNER JOIN MRL_PONTOEXTRA PE ON A.SEQPONTOEXTRA = PE.SEQPONTOEXTRA
INNER JOIN MAP_PRODUTO P ON A.SEQPRODUTO = P.SEQPRODUTO
INNER JOIN MAX_EMPRESA E ON A.NROEMPRESA = E.NROEMPRESA
WHERE A.SEQPONTOEXTRA IN ({pontos_str})
  AND A.SEQPRODUTO IN ({prods_str})
ORDER BY A.SEQPONTOEXTRA, A.SEQPRODUTO, A.NROEMPRESA"""

    return {
        'merge_sql': merge_sql,
        'batch_dml_sql': batch_dml_sql,
        'select_check_sql': select_check_sql
    }

# -------------------------------------------------------------
# 6. Handlers HTTP do Servidor
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
        elif parsed.path == '/api/carga/preview':
            self.handle_carga_preview(data)
        elif parsed.path == '/api/carga/apply':
            self.handle_carga_apply(data)
        elif parsed.path == '/api/carga/reset':
            self.handle_carga_reset()
        elif parsed.path == '/api/ai/chat':
            self.handle_ai_chat(data)
        elif parsed.path == '/api/ai/explain_error':
            self.handle_ai_explain_error(data)
        elif parsed.path == '/api/ai/text_to_sql':
            self.handle_ai_text_to_sql(data)
        elif parsed.path == '/api/ai/find_table':
            self.handle_ai_find_table(data)
        elif parsed.path == '/api/ai/model':
            self.handle_ai_set_model(data)
        elif parsed.path == '/api/ai/config':
            self.handle_ai_save_config(data)
        elif parsed.path == '/api/ai/test_gemini':
            self.handle_ai_test_gemini(data)
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
        elif parsed.path == '/api/carga/monitor_trace':
            ponto = int(params.get('ponto', [203])[0])
            produto = int(params.get('produto', [10])[0])
            empresa = int(params.get('empresa', [12])[0])
            self.handle_carga_monitor_trace(ponto, produto, empresa)
        elif parsed.path == '/api/ai/status':
            self.handle_ai_status()
        elif parsed.path == '/api/ai/config':
            self.handle_ai_get_config()
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

            # Detectar se é instrução DML (UPDATE, INSERT, DELETE)
            is_dml = bool(re.match(r'^\s*(UPDATE|INSERT|DELETE)\b', processed_sql, flags=re.IGNORECASE))
            
            # Se for script múltiplo com ponto e vírgula
            statements = [s.strip() for s in processed_sql.split(';') if s.strip() and s.strip().upper() != 'COMMIT']

            if is_dml or len(statements) > 1:
                total_affected = 0
                for stmt in statements:
                    cursor.execute(stmt)
                    if cursor.rowcount > 0:
                        total_affected += cursor.rowcount
                conn.commit()
                exec_time_ms = round((time.time() - start_time) * 1000, 2)
                conn.close()

                self.send_json({
                    'success': True,
                    'is_dml': True,
                    'rows_affected': total_affected,
                    'message': f'{total_affected} registro(s) afetado(s) com sucesso na base de dados.',
                    'columns': ['STATUS_EXECUCAO', 'REGISTROS_AFETADOS', 'MENSAGEM'],
                    'rows': [['SUCESSO', total_affected, 'Instrução DML aplicada e comitada com sucesso']],
                    'row_count': 1,
                    'execution_time_ms': exec_time_ms,
                    'processed_sql': processed_sql,
                    'alerts': alerts
                })
                return

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
                'is_dml': False,
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
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'colunas' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        tables = []
        for row in cursor.fetchall():
            t_name = row[0]
            try:
                cursor.execute(f"SELECT count(*) FROM {t_name}")
                cnt = cursor.fetchone()[0]
            except:
                cnt = 0
            if cnt > 0:
                tables.append({'name': t_name, 'row_count': cnt})
        conn.close()
        self.send_json({'tables': tables})

    def handle_get_table_info(self, tbl_name):
        conn = get_db_connection()
        cursor = conn.cursor()
        
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

    # --- Módulo Carga & Atualização de Tabelas ---
    def handle_carga_preview(self, data):
        raw_data = data.get('raw_data', '').strip()
        ponto_default = int(data.get('default_ponto', 203))
        vigencia_ini_default = data.get('default_vigencia_ini', '2026-08-01')
        vigencia_fim_default = data.get('default_vigencia_fim', '2026-12-31')

        if not raw_data:
            self.send_json({'success': False, 'error': 'Nenhum dado informado para pré-visualização.'})
            return

        conn = get_db_connection()
        cursor = conn.cursor()

        lines = [l.strip() for l in raw_data.splitlines() if l.strip()]
        if not lines:
            self.send_json({'success': False, 'error': 'Dados vazios.'})
            conn.close()
            return

        first_line = lines[0]
        if '\t' in first_line:
            sep = '\t'
        elif ';' in first_line:
            sep = ';'
        elif ',' in first_line:
            sep = ','
        else:
            sep = r'\s+'

        header_candidate = [c.strip().upper() for c in (re.split(sep, first_line) if sep != r'\s+' else first_line.split())]
        has_header = any(k in header_candidate for k in ['SEQPRODUTO', 'PRODUTO', 'CODIGO', 'NROEMPRESA', 'LOJA', 'ESTQMINIMO', 'MINIMO', 'ESTQMAXIMO', 'MAXIMO'])
        
        data_lines = lines[1:] if has_header else lines

        col_idx_map = {}
        if has_header:
            for idx, col in enumerate(header_candidate):
                col_clean = re.sub(r'[^A-Z0-9]', '', col)
                if col_clean in ['SEQPRODUTO', 'SEQPROD', 'CODPRODUTO', 'CODPROD']:
                    col_idx_map['seqproduto'] = idx
                elif col_clean in ['SEQPONTOEXTRA', 'SEQPONTO']:
                    col_idx_map['seqpontoextra'] = idx
                elif col_clean in ['NROEMPRESA', 'NROEMP', 'LOJA', 'FILIAL']:
                    col_idx_map['nroempresa'] = idx
                elif col_clean in ['ESTQMINIMO', 'ESTQMIN', 'MINIMO', 'MIN']:
                    col_idx_map['estqminimo'] = idx
                elif col_clean in ['ESTQMAXIMO', 'ESTQMAX', 'MAXIMO', 'MAX']:
                    col_idx_map['estqmaximo'] = idx
                elif col_clean in ['DTAVIGENCIAINICIO', 'DTAVIGENCIAINI', 'DTAINICIO', 'DTAINI', 'VIGENCIAINI', 'INICIO']:
                    col_idx_map['dtavigenciainicio'] = idx
                elif col_clean in ['DTAVIGENCIAFIM', 'DTAFIM', 'VIGENCIAFIM', 'FIM']:
                    col_idx_map['dtavigenciafim'] = idx
                elif col_clean in ['QTDDIASSUGESTAO', 'QTDDIAS', 'SUGESTAO', 'DIAS']:
                    col_idx_map['qtddiassugestao'] = idx
                elif col_clean in ['STATUS', 'SITUACAO']:
                    col_idx_map['status'] = idx

        parsed_rows = []
        total_valid = 0
        total_updates = 0
        total_inserts = 0
        total_errors = 0

        for line_idx, line in enumerate(data_lines):
            parts = [p.strip() for p in (re.split(sep, line) if sep != r'\s+' else line.split())]
            if not parts or not any(parts):
                continue

            def get_val(key, default_idx, fallback=''):
                if has_header and key in col_idx_map:
                    idx = col_idx_map[key]
                    return parts[idx] if idx < len(parts) else fallback
                return parts[default_idx] if default_idx < len(parts) else fallback

            if has_header:
                seqprod_str = get_val('seqproduto', 2, '')
                nroemp_str = get_val('nroempresa', 4, '1')
                seqponto_str = get_val('seqpontoextra', 0, str(ponto_default))
                estqmin_str = get_val('estqminimo', 5, '50')
                estqmax_str = get_val('estqmaximo', 6, '100')
                dtaini_str = get_val('dtavigenciainicio', 7, vigencia_ini_default)
                dtafim_str = get_val('dtavigenciafim', 8, vigencia_fim_default)
                qtddias_str = get_val('qtddiassugestao', 9, '0')
                status_str = get_val('status', 10, 'A').upper() or 'A'
            elif len(parts) >= 9:
                # Formato oficial 9 colunas do download:
                # 0: SEQPONTOEXTRA, 1: DESCRICAO, 2: SEQPRODUTO, 3: DESCCOMPLETA, 4: NROEMPRESA, 5: ESTQMINIMO, 6: ESTQMAXIMO, 7: DTAVIGENCIAINICIO, 8: DTAVIGENCIAFIM
                seqponto_str = parts[0]
                seqprod_str = parts[2]
                nroemp_str = parts[4]
                estqmin_str = parts[5]
                estqmax_str = parts[6]
                dtaini_str = parts[7]
                dtafim_str = parts[8]
                qtddias_str = '0'
                status_str = 'A'
            else:
                # Formato enxuto 7 colunas
                seqprod_str = parts[0] if len(parts) > 0 else ''
                nroemp_str = parts[1] if len(parts) > 1 else '1'
                seqponto_str = parts[2] if len(parts) > 2 else str(ponto_default)
                estqmin_str = parts[3] if len(parts) > 3 else '50'
                estqmax_str = parts[4] if len(parts) > 4 else '100'
                dtaini_str = parts[5] if len(parts) > 5 else vigencia_ini_default
                dtafim_str = parts[6] if len(parts) > 6 else vigencia_fim_default
                qtddias_str = '0'
                status_str = 'A'

            try:
                seqproduto = int(re.sub(r'\D', '', seqprod_str))
            except:
                seqproduto = 0

            try:
                nroempresa = int(re.sub(r'\D', '', nroemp_str))
            except:
                nroempresa = 1

            try:
                seqpontoextra = int(re.sub(r'\D', '', seqponto_str)) if seqponto_str else ponto_default
            except:
                seqpontoextra = ponto_default

            try:
                estqminimo = float(estqmin_str.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.'))
            except:
                estqminimo = 0.0

            try:
                estqmaximo = float(estqmax_str.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.'))
            except:
                estqmaximo = estqminimo * 2

            dta_ini = oracle_to_date(dtaini_str) or vigencia_ini_default
            dta_fim = oracle_to_date(dtafim_str) or vigencia_fim_default
            try:
                qtddias = float(qtddias_str)
            except:
                qtddias = 0.0

            # Validações
            cursor.execute("SELECT DESCCOMPLETA FROM MAP_PRODUTO WHERE SEQPRODUTO = ?", (seqproduto,))
            prod_row = cursor.fetchone()
            desc_produto = prod_row['DESCCOMPLETA'] if prod_row else None

            cursor.execute("SELECT NOMERAZAO FROM MAX_EMPRESA WHERE NROEMPRESA = ?", (nroempresa,))
            emp_row = cursor.fetchone()
            nome_empresa = emp_row['NOMERAZAO'] if emp_row else None

            cursor.execute("SELECT DESCRICAO FROM MRL_PONTOEXTRA WHERE SEQPONTOEXTRA = ?", (seqpontoextra,))
            ponto_row = cursor.fetchone()
            desc_ponto = ponto_row['DESCRICAO'] if ponto_row else f"PONTO {seqpontoextra}"

            errors = []
            if not seqproduto:
                errors.append("Código SEQPRODUTO ausente ou inválido.")
            elif not desc_produto:
                errors.append(f"SEQPRODUTO {seqproduto} não cadastrado na MAP_PRODUTO.")

            if not nome_empresa:
                errors.append(f"NROEMPRESA {nroempresa} não cadastrada na MAX_EMPRESA.")

            is_valid = len(errors) == 0

            old_record = None
            action = "INSERT"
            seqvigencia = 1

            if is_valid:
                cursor.execute("""
                    SELECT SEQPONTOEXTRA, SEQPRODUTO, NROEMPRESA, SEQVIGENCIA,
                           ESTQMINIMO, ESTQMAXIMO, DTAVIGENCIAINICIO, DTAVIGENCIAFIM,
                           QTDDIASSUGESTAO, STATUS
                    FROM MRL_PONTOEXTRAPRODUTOEMPRESA
                    WHERE SEQPONTOEXTRA = ? AND SEQPRODUTO = ? AND NROEMPRESA = ?
                    ORDER BY SEQVIGENCIA DESC LIMIT 1
                """, (seqpontoextra, seqproduto, nroempresa))
                curr = cursor.fetchone()
                if curr:
                    action = "UPDATE"
                    seqvigencia = curr['SEQVIGENCIA']
                    old_record = {
                        'estqminimo': curr['ESTQMINIMO'],
                        'estqmaximo': curr['ESTQMAXIMO'],
                        'dtavigenciainicio': curr['DTAVIGENCIAINICIO'],
                        'dtavigenciafim': curr['DTAVIGENCIAFIM'],
                        'qtddiassugestao': curr['QTDDIASSUGESTAO'],
                        'status': curr['STATUS'],
                        'seqvigencia': curr['SEQVIGENCIA']
                    }
                    total_updates += 1
                else:
                    action = "INSERT"
                    total_inserts += 1
                total_valid += 1
            else:
                total_errors += 1
                action = "ERROR"

            parsed_rows.append({
                'line_number': line_idx + (2 if has_header else 1),
                'seqproduto': seqproduto,
                'desc_produto': desc_produto or 'PRODUTO NÃO ENCONTRADO',
                'nroempresa': nroempresa,
                'nome_empresa': nome_empresa or 'LOJA NÃO ENCONTRADA',
                'seqpontoextra': seqpontoextra,
                'desc_ponto': desc_ponto,
                'seqvigencia': seqvigencia,
                'estqminimo': estqminimo,
                'estqmaximo': estqmaximo,
                'dtavigenciainicio': dta_ini,
                'dtavigenciafim': dta_fim,
                'qtddiassugestao': qtddias,
                'status': status_str,
                'action': action,
                'is_valid': is_valid,
                'errors': errors,
                'old_record': old_record
            })

        conn.close()

        valid_rows = [r for r in parsed_rows if r['is_valid']]
        generated_scripts = generate_oracle_update_scripts(valid_rows)

        self.send_json({
            'success': True,
            'parsed_rows': parsed_rows,
            'summary': {
                'total_rows': len(parsed_rows),
                'total_valid': total_valid,
                'total_updates': total_updates,
                'total_inserts': total_inserts,
                'total_errors': total_errors
            },
            'generated_scripts': generated_scripts
        })

    def handle_carga_apply(self, data):
        rows = data.get('rows', [])
        if not rows:
            self.send_json({'success': False, 'error': 'Nenhuma linha válida para aplicar.'})
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        updated_count = 0
        inserted_count = 0
        diff_log = []

        try:
            for r in rows:
                if not r.get('is_valid', True):
                    continue

                seqp = int(r['seqproduto'])
                nroemp = int(r['nroempresa'])
                seqponto = int(r['seqpontoextra'])
                estqmin = float(r['estqminimo'])
                estqmax = float(r['estqmaximo'])
                dtaini = str(r['dtavigenciainicio'])
                dtafim = str(r['dtavigenciafim'])
                qtddias = float(r.get('qtddiassugestao', 0.0))
                status = str(r.get('status', 'A'))
                seqvig = int(r.get('seqvigencia', 1))

                # Garantir capa em MRL_PONTOEXTRAPRODUTO
                cursor.execute("""
                    INSERT OR IGNORE INTO MRL_PONTOEXTRAPRODUTO (SEQPONTOEXTRA, SEQPRODUTO, STATUS)
                    VALUES (?, ?, ?)
                """, (seqponto, seqp, 'A'))

                # Checar se existe
                cursor.execute("""
                    SELECT ESTQMINIMO, ESTQMAXIMO, DTAVIGENCIAINICIO, DTAVIGENCIAFIM, STATUS
                    FROM MRL_PONTOEXTRAPRODUTOEMPRESA
                    WHERE SEQPONTOEXTRA = ? AND SEQPRODUTO = ? AND NROEMPRESA = ?
                """, (seqponto, seqp, nroemp))
                current = cursor.fetchone()

                if current:
                    old_min = current['ESTQMINIMO']
                    old_max = current['ESTQMAXIMO']
                    old_ini = current['DTAVIGENCIAINICIO']
                    old_fim = current['DTAVIGENCIAFIM']
                    old_st = current['STATUS']

                    cursor.execute("""
                        UPDATE MRL_PONTOEXTRAPRODUTOEMPRESA
                        SET ESTQMINIMO = ?, ESTQMAXIMO = ?, DTAVIGENCIAINICIO = ?, DTAVIGENCIAFIM = ?,
                            QTDDIASSUGESTAO = ?, STATUS = ?
                        WHERE SEQPONTOEXTRA = ? AND SEQPRODUTO = ? AND NROEMPRESA = ?
                    """, (estqmin, estqmax, dtaini, dtafim, qtddias, status, seqponto, seqp, nroemp))
                    updated_count += 1
                    diff_log.append({
                        'action': 'UPDATE',
                        'seqpontoextra': seqponto,
                        'seqproduto': seqp,
                        'desc_produto': r.get('desc_produto', ''),
                        'nroempresa': nroemp,
                        'nome_empresa': r.get('nome_empresa', ''),
                        'old_min': old_min,
                        'new_min': estqmin,
                        'old_max': old_max,
                        'new_max': estqmax,
                        'old_ini': old_ini,
                        'new_ini': dtaini,
                        'old_fim': old_fim,
                        'new_fim': dtafim,
                        'status': status
                    })
                else:
                    cursor.execute("""
                        INSERT INTO MRL_PONTOEXTRAPRODUTOEMPRESA (
                            SEQPONTOEXTRA, SEQPRODUTO, NROEMPRESA, SEQVIGENCIA,
                            ESTQMINIMO, ESTQMAXIMO, DTAVIGENCIAINICIO, DTAVIGENCIAFIM,
                            QTDDIASSUGESTAO, STATUS
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (seqponto, seqp, nroemp, seqvig, estqmin, estqmax, dtaini, dtafim, qtddias, status))
                    inserted_count += 1
                    diff_log.append({
                        'action': 'INSERT',
                        'seqpontoextra': seqponto,
                        'seqproduto': seqp,
                        'desc_produto': r.get('desc_produto', ''),
                        'nroempresa': nroemp,
                        'nome_empresa': r.get('nome_empresa', ''),
                        'old_min': None,
                        'new_min': estqmin,
                        'old_max': None,
                        'new_max': estqmax,
                        'old_ini': None,
                        'new_ini': dtaini,
                        'old_fim': None,
                        'new_fim': dtafim,
                        'status': status
                    })

            conn.commit()
            conn.close()

            self.send_json({
                'success': True,
                'message': f'Carga aplicada com sucesso! {updated_count} registro(s) atualizados, {inserted_count} novos inseridos.',
                'updated_count': updated_count,
                'inserted_count': inserted_count,
                'total_affected': updated_count + inserted_count,
                'diff_log': diff_log
            })
        except Exception as e:
            conn.rollback()
            conn.close()
            self.send_json({'success': False, 'error': f'Erro ao aplicar carga: {str(e)}'})

    def handle_carga_reset(self):
        try:
            # Re-executar o script de seed
            seed_script = os.path.join(BASE_DIR, 'database', 'seed_data.py')
            os.system(f'python "{seed_script}"')
            self.send_json({'success': True, 'message': 'Banco de dados do simulador restaurado para o estado inicial padrão!'})
        except Exception as e:
            self.send_json({'success': False, 'error': str(e)})

    def handle_carga_monitor_trace(self, ponto=203, produto=10, empresa=12):
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Capa MRL_PONTOEXTRA
        cursor.execute("SELECT SEQPONTOEXTRA, DESCRICAO, STATUS FROM MRL_PONTOEXTRA WHERE SEQPONTOEXTRA = ?", (ponto,))
        pe = cursor.fetchone()
        pe_desc = pe['DESCRICAO'] if pe else ''
        pe_st = pe['STATUS'] if pe else 'A'

        # 2. Produto MRL_PONTOEXTRAPRODUTO
        cursor.execute("""
            SELECT MRL_PONTOEXTRAPRODUTO.SEQPONTOEXTRA, MRL_PONTOEXTRAPRODUTO.SEQPRODUTO, PROD.DESCCOMPLETA, MRL_PONTOEXTRAPRODUTO.STATUS
            FROM MRL_PONTOEXTRAPRODUTO
            INNER JOIN MAP_PRODUTO PROD ON PROD.SEQPRODUTO = MRL_PONTOEXTRAPRODUTO.SEQPRODUTO
            WHERE MRL_PONTOEXTRAPRODUTO.SEQPONTOEXTRA = ? AND MRL_PONTOEXTRAPRODUTO.SEQPRODUTO = ?
        """, (ponto, produto))
        pep = cursor.fetchone()

        # 3. Loja MRL_PONTOEXTRAPRODUTOEMPRESA
        cursor.execute("""
            SELECT MRL_PONTOEXTRAPRODUTOEMPRESA.SEQPONTOEXTRA, MRL_PONTOEXTRAPRODUTOEMPRESA.SEQPRODUTO, MRL_PONTOEXTRAPRODUTOEMPRESA.NROEMPRESA,
                   LPAD(EMP.NROEMPRESA, 6, '0') || ' - ' || EMP.RAZAOSOCIAL AS EMPRESA_LABEL,
                   MRL_PONTOEXTRAPRODUTOEMPRESA.ESTQMINIMO, MRL_PONTOEXTRAPRODUTOEMPRESA.ESTQMAXIMO,
                   MRL_PONTOEXTRAPRODUTOEMPRESA.DTAVIGENCIAINICIO, MRL_PONTOEXTRAPRODUTOEMPRESA.DTAVIGENCIAFIM,
                   MRL_PONTOEXTRAPRODUTOEMPRESA.QTDDIASSUGESTAO, MRL_PONTOEXTRAPRODUTOEMPRESA.STATUS,
                   MRL_PONTOEXTRAPRODUTOEMPRESA.SEQVIGENCIA
            FROM MRL_PONTOEXTRAPRODUTOEMPRESA
            INNER JOIN MAX_EMPRESA EMP ON MRL_PONTOEXTRAPRODUTOEMPRESA.NROEMPRESA = EMP.NROEMPRESA
            WHERE MRL_PONTOEXTRAPRODUTOEMPRESA.SEQPONTOEXTRA = ?
              AND MRL_PONTOEXTRAPRODUTOEMPRESA.SEQPRODUTO = ?
              AND MRL_PONTOEXTRAPRODUTOEMPRESA.NROEMPRESA = ?
        """, (ponto, produto, empresa))
        pepe = cursor.fetchone()

        now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        trace_blocks = [
            {
                'id': '<ID-00001>',
                'timestamp': now_str,
                'title': '1. Busca da Capa do Ponto Extra (MRL_PONTOEXTRA)',
                'sql': f"SELECT\n\tMRL_PONTOEXTRA.SEQPONTOEXTRA, MRL_PONTOEXTRA.DESCRICAO, MRL_PONTOEXTRA.STATUS\nINTO\n\t{ponto}, '{pe_desc}', '{pe_st}'\nFROM MRL_PONTOEXTRA\nWHERE\n\tMRL_PONTOEXTRA.SEQPONTOEXTRA = {ponto}",
                'explanation': 'O ERP valida se a ponta de gôndola/ilha está cadastrada e ativa no sistema comercial.'
            },
            {
                'id': '<ID-00004>',
                'timestamp': now_str,
                'title': '2. Verificação de Vínculo Produto x Ponto Extra (MRL_PONTOEXTRAPRODUTO)',
                'sql': f"SELECT\n\tMRL_PONTOEXTRAPRODUTO.SEQPONTOEXTRA, MRL_PONTOEXTRAPRODUTO.SEQPRODUTO, PROD.DESCCOMPLETA, MRL_PONTOEXTRAPRODUTO.STATUS\nINTO\n\t{ponto}, {produto}, '{pep['DESCCOMPLETA'] if pep else ''}', '{pep['STATUS'] if pep else ''}'\nFROM MRL_PONTOEXTRAPRODUTO, MAP_PRODUTO PROD\nWHERE\n\tPROD.SEQPRODUTO = MRL_PONTOEXTRAPRODUTO.SEQPRODUTO\n\tAND MRL_PONTOEXTRAPRODUTO.SEQPONTOEXTRA = {ponto}",
                'explanation': 'Localiza todos os produtos amarrados a este Ponto Extra trazendo a descrição do cadastro geral MAP_PRODUTO.'
            },
            {
                'id': '<ID-00007>',
                'timestamp': now_str,
                'title': '3. Leitura Inicial de Parâmetros por Empresa (Check de Template)',
                'sql': f"SELECT\n\tMRL_PONTOEXTRAPRODUTOEMPRESA.SEQPONTOEXTRA, MRL_PONTOEXTRAPRODUTOEMPRESA.SEQPRODUTO, MRL_PONTOEXTRAPRODUTOEMPRESA.NROEMPRESA, LPAD(EMP.NROEMPRESA, 6, '0') || ' - ' || EMP.RAZAOSOCIAL, MRL_PONTOEXTRAPRODUTOEMPRESA.ESTQMINIMO, MRL_PONTOEXTRAPRODUTOEMPRESA.ESTQMAXIMO, MRL_PONTOEXTRAPRODUTOEMPRESA.DTAVIGENCIAINICIO, MRL_PONTOEXTRAPRODUTOEMPRESA.DTAVIGENCIAFIM, MRL_PONTOEXTRAPRODUTOEMPRESA.QTDDIASSUGESTAO, MRL_PONTOEXTRAPRODUTOEMPRESA.STATUS, MRL_PONTOEXTRAPRODUTOEMPRESA.SEQVIGENCIA\nINTO\n\t0, 0, 0, '', 0, 0, , , 0, '', 0\nFROM MRL_PONTOEXTRAPRODUTOEMPRESA, MAX_EMPRESA EMP\nWHERE\n\tMRL_PONTOEXTRAPRODUTOEMPRESA.NROEMPRESA = EMP.NROEMPRESA\n\tAND MRL_PONTOEXTRAPRODUTOEMPRESA.SEQPONTOEXTRA = {ponto}\n\tAND MRL_PONTOEXTRAPRODUTOEMPRESA.SEQPRODUTO = 0",
                'explanation': 'O grid do Delphi carrega uma linha padrão (SEQPRODUTO = 0) para inicializar as colunas da grade de filiais.'
            },
            {
                'id': '<ID-00010>',
                'timestamp': now_str,
                'title': f'4. Consulta dos Registros da Grade para SEQPRODUTO = {produto}',
                'sql': f"SELECT\n\tMRL_PONTOEXTRAPRODUTOEMPRESA.SEQPONTOEXTRA, MRL_PONTOEXTRAPRODUTOEMPRESA.SEQPRODUTO, MRL_PONTOEXTRAPRODUTOEMPRESA.NROEMPRESA, LPAD(EMP.NROEMPRESA, 6, '0') || ' - ' || EMP.RAZAOSOCIAL, MRL_PONTOEXTRAPRODUTOEMPRESA.ESTQMINIMO, MRL_PONTOEXTRAPRODUTOEMPRESA.ESTQMAXIMO, MRL_PONTOEXTRAPRODUTOEMPRESA.DTAVIGENCIAINICIO, MRL_PONTOEXTRAPRODUTOEMPRESA.DTAVIGENCIAFIM, MRL_PONTOEXTRAPRODUTOEMPRESA.QTDDIASSUGESTAO, MRL_PONTOEXTRAPRODUTOEMPRESA.STATUS, MRL_PONTOEXTRAPRODUTOEMPRESA.SEQVIGENCIA\nINTO\n\t0, 0, 0, '', 0, 0, , , 0, '', 0\nFROM MRL_PONTOEXTRAPRODUTOEMPRESA, MAX_EMPRESA EMP\nWHERE\n\tMRL_PONTOEXTRAPRODUTOEMPRESA.NROEMPRESA = EMP.NROEMPRESA\n\tAND MRL_PONTOEXTRAPRODUTOEMPRESA.SEQPONTOEXTRA = {ponto}\n\tAND MRL_PONTOEXTRAPRODUTOEMPRESA.SEQPRODUTO = {produto}",
                'explanation': 'Dispara a busca das filiais vinculadas a este produto específico.'
            },
            {
                'id': '<ID-00013>',
                'timestamp': now_str,
                'title': f'5. Retorno dos Dados Preenchidos da Loja {empresa}',
                'sql': f"SELECT\n\tMRL_PONTOEXTRAPRODUTOEMPRESA.SEQPONTOEXTRA, MRL_PONTOEXTRAPRODUTOEMPRESA.SEQPRODUTO, MRL_PONTOEXTRAPRODUTOEMPRESA.NROEMPRESA, LPAD(EMP.NROEMPRESA, 6, '0') || ' - ' || EMP.RAZAOSOCIAL, MRL_PONTOEXTRAPRODUTOEMPRESA.ESTQMINIMO, MRL_PONTOEXTRAPRODUTOEMPRESA.ESTQMAXIMO, MRL_PONTOEXTRAPRODUTOEMPRESA.DTAVIGENCIAINICIO, MRL_PONTOEXTRAPRODUTOEMPRESA.DTAVIGENCIAFIM, MRL_PONTOEXTRAPRODUTOEMPRESA.QTDDIASSUGESTAO, MRL_PONTOEXTRAPRODUTOEMPRESA.STATUS, MRL_PONTOEXTRAPRODUTOEMPRESA.SEQVIGENCIA\nINTO\n\t{pepe['SEQPONTOEXTRA'] if pepe else ponto}, {pepe['SEQPRODUTO'] if pepe else produto}, {pepe['NROEMPRESA'] if pepe else empresa}, '{pepe['EMPRESA_LABEL'] if pepe else ''}', {pepe['ESTQMINIMO'] if pepe else 0}, {pepe['ESTQMAXIMO'] if pepe else 0}, {pepe['DTAVIGENCIAINICIO'] if pepe else ''}, {pepe['DTAVIGENCIAFIM'] if pepe else ''}, {pepe['QTDDIASSUGESTAO'] if pepe else 0}, '{pepe['STATUS'] if pepe else 'A'}', {pepe['SEQVIGENCIA'] if pepe else 1}\nFROM MRL_PONTOEXTRAPRODUTOEMPRESA, MAX_EMPRESA EMP\nWHERE\n\tMRL_PONTOEXTRAPRODUTOEMPRESA.NROEMPRESA = EMP.NROEMPRESA\n\tAND MRL_PONTOEXTRAPRODUTOEMPRESA.SEQPONTOEXTRA = {ponto}\n\tAND MRL_PONTOEXTRAPRODUTOEMPRESA.SEQPRODUTO = {produto}",
                'explanation': 'Os dados reais são injetados nas variáveis internas do formulário Delphi/Consinco para exibição na tela.'
            }
        ]

        conn.close()
        self.send_json({
            'success': True,
            'ponto': ponto,
            'produto': produto,
            'empresa': empresa,
            'trace_blocks': trace_blocks
        })

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
            },
            {
                'id': 7,
                'title': 'Missão 7: Atualizar Estoque Mínimo e Máximo de Ponta de Gôndola',
                'difficulty': 'Intermediário',
                'category': 'Atualização de Tabela',
                'description': 'Execute um comando UPDATE na tabela MRL_PONTOEXTRAPRODUTOEMPRESA para definir ESTQMINIMO = 500 e ESTQMAXIMO = 600 para a Loja 12 no Ponto 203 do Produto 10.',
                'starter_sql': "UPDATE MRL_PONTOEXTRAPRODUTOEMPRESA\nSET ESTQMINIMO = 500,\n    ESTQMAXIMO = 600\nWHERE SEQPONTOEXTRA = 203\n  AND SEQPRODUTO = 10\n  AND NROEMPRESA = 12",
                'hint': 'Lembre-se de sempre especificar o WHERE com SEQPONTOEXTRA, SEQPRODUTO e NROEMPRESA para não alterar outras lojas!'
            },
            {
                'id': 8,
                'title': 'Missão 8: Consulta de Auditoria de Pontas Extras vs Estoque Real',
                'difficulty': 'Intermediário',
                'category': 'Consultas de Pontas',
                'description': 'Cruze as configurações de Pontas de Gôndola (MRL_PONTOEXTRAPRODUTOEMPRESA) com o Estoque Operacional da Loja (MRL_PRODUTOEMPRESA) para comparar ESTQMINIMO da ponta com ESTQLOJA.',
                'starter_sql': "SELECT\n    PE.SEQPONTOEXTRA,\n    P.SEQPRODUTO,\n    P.DESCCOMPLETA,\n    PE.NROEMPRESA,\n    PE.ESTQMINIMO AS MINIMO_PONTA,\n    PE.ESTQMAXIMO AS MAXIMO_PONTA,\n    E.ESTQLOJA AS ESTOQUE_ATUAL_LOJA,\n    PE.STATUS AS STATUS_PONTA\nFROM MRL_PONTOEXTRAPRODUTOEMPRESA PE\nINNER JOIN MAP_PRODUTO P ON PE.SEQPRODUTO = P.SEQPRODUTO\nINNER JOIN MRL_PRODUTOEMPRESA E ON PE.SEQPRODUTO = E.SEQPRODUTO AND PE.NROEMPRESA = E.NROEMPRESA\nWHERE PE.SEQPONTOEXTRA = 203\nORDER BY PE.NROEMPRESA",
                'hint': 'Faça JOIN de MRL_PONTOEXTRAPRODUTOEMPRESA com MAP_PRODUTO e MRL_PRODUTOEMPRESA pela chave composta (SEQPRODUTO e NROEMPRESA).'
            },
            {
                'id': 9,
                'title': 'Missão 9: Atualização de Vigência Promocional de Pontas de Gôndola',
                'difficulty': 'Avançado',
                'category': 'Atualização de Tabela',
                'description': 'Atualize a data de fim de vigência (DTAVIGENCIAFIM) para \'2026-12-31\' de todos os produtos do Ponto Extra 203 mantendo STATUS = \'A\'.',
                'starter_sql': "UPDATE MRL_PONTOEXTRAPRODUTOEMPRESA\nSET DTAVIGENCIAFIM = '2026-12-31',\n    STATUS = 'A'\nWHERE SEQPONTOEXTRA = 203",
                'hint': 'O filtro por SEQPONTOEXTRA = 203 atualiza a vigência de todas as lojas e produtos alocados nessa ponta de gôndola.'
            },
            {
                'id': 10,
                'title': 'Missão 10: Extração Oficial de Pontas para Planilha de Manutenção',
                'difficulty': 'Avançado',
                'category': 'Extração & Carga',
                'description': 'Construa a consulta de extração completa das pontas de gôndola (MRL_PONTOEXTRA, MRL_PONTOEXTRAPRODUTO, MRL_PONTOEXTRAPRODUTOEMPRESA, MAP_PRODUTO, MAX_EMPRESA) formatando as colunas exatas para download em TXT/Excel.',
                'starter_sql': "SELECT\n    PEPE.SEQPONTOEXTRA,\n    PE.DESCRICAO,\n    PEPE.SEQPRODUTO,\n    PROD.DESCCOMPLETA,\n    PEPE.NROEMPRESA,\n    PEPE.ESTQMINIMO,\n    PEPE.ESTQMAXIMO,\n    PEPE.DTAVIGENCIAINICIO,\n    PEPE.DTAVIGENCIAFIM\nFROM MRL_PONTOEXTRA PE\nINNER JOIN MRL_PONTOEXTRAPRODUTO PEP ON PEP.SEQPONTOEXTRA = PE.SEQPONTOEXTRA\nINNER JOIN MRL_PONTOEXTRAPRODUTOEMPRESA PEPE ON PEPE.SEQPONTOEXTRA = PEP.SEQPONTOEXTRA AND PEPE.SEQPRODUTO = PEP.SEQPRODUTO\nINNER JOIN MAP_PRODUTO PROD ON PROD.SEQPRODUTO = PEPE.SEQPRODUTO\nWHERE PE.STATUS = 'A'\nORDER BY PEPE.SEQPONTOEXTRA, PEPE.NROEMPRESA, PEPE.SEQPRODUTO",
                'hint': 'Esta é a query oficial com as 9 colunas exatas que gera o arquivo CSV/Excel de todas as pontas da rede para você editar os mínimos/máximos e depois colar no módulo de Carga!'
            }
        ]
        self.send_json({'missions': missions})

    def handle_mission_verify(self, data):
        mission_id = data.get('mission_id')
        user_sql = data.get('sql', '').strip()
        
        if not user_sql:
            self.send_json({'success': False, 'message': 'Digite uma instrução SQL antes de verificar.'})
            return

        processed = preprocess_oracle_sql(user_sql, {'NROEMPRESA': 1, 'NR1': 0})
        is_dml = bool(re.match(r'^\s*(UPDATE|INSERT|DELETE)\b', processed, flags=re.IGNORECASE))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if is_dml:
                cursor.execute(processed)
                affected = cursor.rowcount
                conn.commit()
                conn.close()
                if affected > 0:
                    self.send_json({
                        'success': True,
                        'passed': True,
                        'message': f'Parabéns! O comando DML executou com sucesso e afetou {affected} linha(s)!',
                        'row_count': affected
                    })
                else:
                    self.send_json({
                        'success': True,
                        'passed': False,
                        'message': 'O comando executou, mas 0 linhas foram afetadas. Revise a condição WHERE.',
                        'row_count': 0
                    })
                return

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
                'message': f'Erro na execução: {str(e)}'
            })

    # --- Módulo Mentor IA (Ollama) ---
    def handle_ai_status(self):
        status = ollama_mentor.check_status()
        self.send_json(status)

    def handle_ai_chat(self, data):
        user_msg = data.get('message', '').strip()
        current_sql = data.get('current_sql', '')
        history = data.get('history', [])
        model = data.get('model')
        if model:
            ollama_mentor.current_model = model
        result = ollama_mentor.chat(user_msg, current_sql=current_sql, history=history)
        self.send_json(result)

    def handle_ai_explain_error(self, data):
        sql = data.get('sql', '').strip()
        error_msg = data.get('error', '').strip()
        binds = data.get('binds', {})
        model = data.get('model')
        if model:
            ollama_mentor.current_model = model
        result = ollama_mentor.explain_and_fix_error(sql, error_msg, binds=binds)
        self.send_json(result)

    def handle_ai_text_to_sql(self, data):
        request_text = data.get('request', '').strip()
        model = data.get('model')
        if model:
            ollama_mentor.current_model = model
        result = ollama_mentor.text_to_sql(request_text)
        self.send_json(result)

    def handle_ai_find_table(self, data):
        query = data.get('query', '').strip()
        model = data.get('model')
        if model:
            ollama_mentor.current_model = model
        result = ollama_mentor.find_table(query)
        self.send_json(result)

    def handle_ai_set_model(self, data):
        model_name = data.get('model', '').strip()
        success, msg = ollama_mentor.set_model(model_name)
        self.send_json({'success': success, 'message': msg, 'current_model': ollama_mentor.current_model})

    def handle_ai_get_config(self):
        gemini_key = ollama_mentor.get_gemini_key()
        masked_key = gemini_key[:6] + "..." + gemini_key[-4:] if len(gemini_key) > 10 else ("***" if gemini_key else "")
        self.send_json({
            'has_gemini_key': bool(gemini_key),
            'masked_key': masked_key,
            'current_model': ollama_mentor.current_model,
            'provider': 'gemini' if ollama_mentor.is_gemini_model() else 'ollama',
            'gemini_models': GEMINI_MODELS
        })

    def handle_ai_save_config(self, data):
        gemini_key = data.get('gemini_api_key', '').strip()
        model_name = data.get('model', '').strip()
        if gemini_key:
            ollama_mentor.set_gemini_key(gemini_key)
        if model_name:
            ollama_mentor.set_model(model_name)
        self.send_json({
            'success': True,
            'message': 'Configurações de IA salvas com sucesso!',
            'current_model': ollama_mentor.current_model,
            'has_gemini_key': bool(ollama_mentor.get_gemini_key())
        })

    def handle_ai_test_gemini(self, data):
        api_key = data.get('gemini_api_key', '').strip()
        model = data.get('model', 'gemini-2.5-flash').strip()
        result = ollama_mentor.test_gemini_connection(api_key=api_key, model=model)
        self.send_json(result)

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
