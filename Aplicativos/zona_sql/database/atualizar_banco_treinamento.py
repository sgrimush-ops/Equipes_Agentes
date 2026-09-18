import os
import sys
import sqlite3
import re
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ZONA_SQL_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
DB_PATH = os.path.join(BASE_DIR, "banco_simulador_consinco.db")
IMPORT_QUERYS_DIR = os.path.abspath(os.path.join(ZONA_SQL_DIR, "..", "import_querys"))
BANCO_CONSINCO_DIR = os.path.join(IMPORT_QUERYS_DIR, "Banco_Consico")

MAPA_TABELAS_OFICIAIS = {
    "mlfv_basenfe": "MLFV_BASENFE",
    "mflv_basedfitem": "MFLV_BASEDFITEM",
    "mlf_notafiscal": "MLF_NOTAFISCAL",
    "mlf_nfitem": "MLF_NFITEM",
    "max_codgeraloper": "MAX_CODGERALOPER",
    "cgos": "MAX_CODGERALOPER",
    "map_produto": "MAP_PRODUTO",
    "map_familia": "MAP_FAMILIA",
    "map_categoria": "MAP_CATEGORIA",
    "map_famdivcateg": "MAP_FAMDIVCATEG",
    "map_famfornec": "MAP_FAMFORNEC",
    "map_prodcodigo": "MAP_PRODCODIGO",
    "max_empresa": "MAX_EMPRESA",
    "max_comprador": "MAX_COMPRADOR",
    "ge_pessoa": "GE_PESSOA",
    "ge_redepessoa": "GE_REDEPESSOA",
    "ge_rede": "GE_REDE",
    "mrl_produtoempresa": "MRL_PRODUTOEMPRESA",
    "mrl_prodempseg": "MRL_PRODEMPSEG",
    "mrl_pontoextra": "MRL_PONTOEXTRA",
    "mrl_pontoextraprodutoempresa": "MRL_PONTOEXTRAPRODUTOEMPRESA",
    "fi_titulo": "FI_TITULO",
    "msu_pedidosuprim": "MSU_PEDIDOSUPRIM",
    "mbi_tabcdistrib": "MBI_TABCDISTRIB",
    "mrl_custodia": "MRL_CUSTODIA",
    "mrl_prodvendadia": "MRL_PRODVENDADIA"
}

def detectar_delimitador(linha):
    contagens = {
        ';': linha.count(';'),
        '\t': linha.count('\t'),
        ',': linha.count(','),
        '|': linha.count('|')
    }
    return max(contagens, key=contagens.get) if max(contagens.values()) > 0 else ';'

def sanitizar_valor(val):
    if val is None:
        return None
    s = str(val).strip().strip('"').strip("'")
    if s == '' or s.upper() == 'NULL':
        return None
    
    # Número com formato brasileiro (ex: 1.234,56 ou 123,45)
    if re.match(r'^-?\d{1,3}(\.\d{3})*,\d+$', s):
        try:
            return float(s.replace('.', '').replace(',', '.'))
        except:
            return s
    
    # Decimal com vírgula
    if re.match(r'^-?\d+,\d+$', s):
        try:
            return float(s.replace(',', '.'))
        except:
            return s

    # Inteiro (apenas se tiver até 15 dígitos para caber com segurança no INTEGER do SQLite)
    if re.match(r'^-?\d+$', s):
        if len(s) <= 15:
            try:
                return int(s)
            except:
                return s
        else:
            return s

    # Float com ponto
    if re.match(r'^-?\d+\.\d+$', s):
        try:
            return float(s)
        except:
            return s

    return s

def importar_tabela_txt(file_path, table_name):
    if not os.path.exists(file_path):
        return 0

    with open(file_path, 'r', encoding='latin1', errors='replace') as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        return 0

    sep = detectar_delimitador(lines[0])
    raw_headers = [h.strip().replace('"', '').replace("'", "") for h in lines[0].split(sep)]
    headers = [re.sub(r'[^A-Za-z0-9_]', '_', h).upper() for h in raw_headers]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Compatibilidade amigável para MAX_EMPRESA (garantir NOMERAZAO)
    if table_name == 'MAX_EMPRESA' and 'NOMERAZAO' not in headers:
        headers.append('NOMERAZAO')
        has_nomerazao = False
    else:
        has_nomerazao = True

    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    col_defs = ", ".join([f'"{h}" TEXT' for h in headers])
    cursor.execute(f'CREATE TABLE "{table_name}" ({col_defs})')

    placeholders = ", ".join(["?"] * len(headers))
    cols_joined = ", ".join([f'"{h}"' for h in headers])
    insert_sql = f'INSERT INTO "{table_name}" ({cols_joined}) VALUES ({placeholders})'

    batch = []
    count = 0

    for line in lines[1:]:
        parts = [p.strip().replace('"', '').replace("'", "") for p in line.split(sep)]
        if not has_nomerazao:
            rz = ''
            if 'RAZAOSOCIAL' in raw_headers:
                rz_idx = raw_headers.index('RAZAOSOCIAL')
                rz = parts[rz_idx] if rz_idx < len(parts) else ''
            elif 'FANTASIA' in raw_headers:
                f_idx = raw_headers.index('FANTASIA')
                rz = parts[f_idx] if f_idx < len(parts) else ''
            parts.append(rz)

        if len(parts) < len(headers):
            parts.extend([''] * (len(headers) - len(parts)))

        row_vals = [sanitizar_valor(parts[i]) if i < len(parts) else None for i in range(len(headers))]
        batch.append(row_vals)
        count += 1

        if len(batch) >= 2500:
            cursor.executemany(insert_sql, batch)
            batch = []

    if batch:
        cursor.executemany(insert_sql, batch)

    # Criar índices inteligentes nas chaves mais consultadas
    try:
        if 'SEQPRODUTO' in headers:
            cursor.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_prod" ON "{table_name}" ("SEQPRODUTO")')
        if 'NROEMPRESA' in headers:
            cursor.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_emp" ON "{table_name}" ("NROEMPRESA")')
        if 'SEQPESSOA' in headers:
            cursor.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_pes" ON "{table_name}" ("SEQPESSOA")')
        if 'SEQFAMILIA' in headers:
            cursor.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_fam" ON "{table_name}" ("SEQFAMILIA")')
        if 'SEQCATEGORIA' in headers:
            cursor.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_cat" ON "{table_name}" ("SEQCATEGORIA")')
        if 'CODGERALOPER' in headers:
            cursor.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_cgo" ON "{table_name}" ("CODGERALOPER")')
        if 'NUMERONF' in headers:
            cursor.execute(f'CREATE INDEX IF NOT EXISTS "idx_{table_name}_nf" ON "{table_name}" ("NUMERONF")')
    except Exception as e:
        pass

    conn.commit()
    conn.close()
    return count

def garantir_tabela_ge_rede():
    """Garante que a tabela GE_REDE exista e tenha registros vinculados a GE_REDEPESSOA."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS "GE_REDE" (
            "SEQREDE" INTEGER PRIMARY KEY,
            "DESCRICAO" TEXT,
            "STATUS" TEXT
        )
    ''')
    
    # Inserir redes padrão caso não existam
    redes_padrao = [
        (81, 'REDE 81 - DISTRIBUICAO', 'A'),
        (201, 'REDE 201 - FORNECEDORES MERCEARIA', 'A'),
        (361, 'REDE 361 - BEBIDAS E LATICINIOS', 'A'),
        (441, 'REDE 441 - HORTIFRUTI E PERECIVEIS', 'A'),
        (500, 'REDE 500 - HIGIENE E LIMPEZA', 'A')
    ]
    c.executemany('INSERT OR IGNORE INTO GE_REDE (SEQREDE, DESCRICAO, STATUS) VALUES (?, ?, ?)', redes_padrao)
    
    # Se existirem redes em GE_REDEPESSOA que não estejam em GE_REDE, insere automaticamente
    try:
        c.execute('''
            INSERT OR IGNORE INTO GE_REDE (SEQREDE, DESCRICAO, STATUS)
            SELECT DISTINCT SEQREDE, 'REDE ' || SEQREDE, 'A'
            FROM GE_REDEPESSOA
            WHERE SEQREDE IS NOT NULL AND SEQREDE > 0
        ''')
    except Exception:
        pass

    conn.commit()
    conn.close()

def garantir_map_famdivisao():
    """Garante que a tabela MAP_FAMDIVISAO exista associada às famílias e compradores."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS "MAP_FAMDIVISAO" (
            "SEQFAMILIA" INTEGER,
            "NRODIVISAO" INTEGER,
            "SEQCOMPRADOR" INTEGER,
            "STATUS" TEXT,
            PRIMARY KEY (SEQFAMILIA, NRODIVISAO)
        )
    ''')
    
    # Popular MAP_FAMDIVISAO a partir de MAP_FAMILIA e MAP_PRODUTO
    try:
        c.execute('''
            INSERT OR IGNORE INTO MAP_FAMDIVISAO (SEQFAMILIA, NRODIVISAO, SEQCOMPRADOR, STATUSCOMPRA)
            SELECT DISTINCT SEQFAMILIA, 1, ((SEQFAMILIA % 10) + 1), 'A'
            FROM MAP_PRODUTO
            WHERE SEQFAMILIA IS NOT NULL AND SEQFAMILIA > 0
        ''')
    except Exception:
        pass

    conn.commit()
    conn.close()

def executar_sincronizacao_completa():
    print("\n" + "="*75)
    print("  INICIANDO ATUALIZAÇÃO DO BANCO DE TREINAMENTO (ZONA SQL / CONSINCO)")
    print("="*75)
    print(f"Pasta de Origem: {BANCO_CONSINCO_DIR}")
    print(f"Banco SQLite Destino: {DB_PATH}\n")

    t_inicio = time.time()
    tabelas_atualizadas = {}

    # 1. Varre e importa todas as tabelas oficiais presentes em Banco_Consico
    arquivos_prioritarios = [
        "MLFV_BASENFE.txt",
        "MFLV_BASEDFITEM.txt",
        "MLF_NOTAFISCAL.txt",
        "MLF_NFITEM.txt",
        "MAX_CODGERALOPER.txt",
        "GE_PESSOA.txt",
        "GE_REDEPESSOA.txt",
        "MAP_CATEGORIA.txt",
        "MAP_FAMDIVCATEG.txt",
        "MAP_FAMFORNEC.txt",
        "MAP_PRODUTO.txt",
        "MAP_FAMILIA.txt",
        "MAP_PRODCODIGO.txt",
        "MAX_EMPRESA.txt",
        "MAX_COMPRADOR.txt",
        "MRL_PRODUTOEMPRESA.txt",
        "MRL_PRODEMPSEG.txt",
        "FI_TITULO.txt",
        "MSU_PEDIDOSUPRIM.txt",
        "MRL_PONTOEXTRA.txt",
        "MRL_PONTOEXTRAPRODUTOEMPRESA.txt"
    ]

    for arq in arquivos_prioritarios:
        caminho = os.path.join(BANCO_CONSINCO_DIR, arq)
        if not os.path.exists(caminho):
            caminho = os.path.join(IMPORT_QUERYS_DIR, arq)
        if os.path.exists(caminho):
            nome_base = os.path.splitext(arq)[0].lower()
            tbl_destino = MAPA_TABELAS_OFICIAIS.get(nome_base, nome_base.upper())
            print(f"[*] Importando {arq} -> {tbl_destino}...")
            qtd = importar_tabela_txt(caminho, tbl_destino)
            tabelas_atualizadas[tbl_destino] = qtd
            print(f"    -> [OK] {qtd:,} registros inseridos em {tbl_destino}.")
        else:
            print(f"[-] Arquivo não encontrado: {arq}")

    # 2. Garantir integridade de tabelas complementares
    print("[*] Verificando tabelas complementares (GE_REDE e MAP_FAMDIVISAO)...")
    garantir_tabela_ge_rede()
    garantir_map_famdivisao()

    t_total = time.time() - t_inicio
    print("\n" + "="*75)
    print("  ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!")
    print(f"  Tempo Total: {t_total:.2f} segundos")
    print("="*75)
    print("\nResumo das Tabelas Atualizadas no Banco de Treinamento:")
    for tbl, qtd in tabelas_atualizadas.items():
        print(f"  ✓ {tbl:<28}: {qtd:>8,} registros")
    print("="*75)

if __name__ == "__main__":
    executar_sincronizacao_completa()
