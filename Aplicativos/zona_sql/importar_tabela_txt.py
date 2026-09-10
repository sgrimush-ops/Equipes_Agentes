"""
Importador e Sincronizador Mestre de Dados Oficiais Totvs Consinco (Zona SQL)

Este é o ÚNICO script central de importação e sincronização de dados para o simulador.
Ele suporta:
1. Tabelas Oficiais de Dados (MAP_PRODUTO, MRL_PRODUTOEMPRESA, MRL_PRODEMPSEG, etc.)
2. Carga de Pontas de Gôndola (MRL_PONTOEXTRA, MRL_PONTOEXTRAPRODUTO, MRL_PONTOEXTRAPRODUTOEMPRESA)
3. Catálogo e Dicionário Oficial (TABELAS_CONSICO_OFICIAIS.txt e TODAS_COLUNAS_CONSICO_OFICIAIS.txt)
4. Mapeamento inteligente de arquivos para tabelas canônicas oficiais do Consinco.

Uso Interativo:
    python importar_tabela_txt.py
    (Você digita o nome do arquivo, ex: 'map_produto', ou o número da lista)

Uso por Linha de Comando:
    python importar_tabela_txt.py map_produto
    python importar_tabela_txt.py tabelas_oficiais
    python importar_tabela_txt.py colunas_oficiais
    python importar_tabela_txt.py pontas
    python importar_tabela_txt.py todas
"""

import os
import sys
import sqlite3
import re
import time

# Compatibilidade de encoding no console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "banco_simulador_consinco.db")
IMPORT_QUERYS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "import_querys"))
BANCO_CONSINCO_DIR = os.path.join(IMPORT_QUERYS_DIR, "Banco_Consico")
APRENDIZADO_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "gerenciamento_sql", "aprendizado"))

# Mapeamento de arquivos para Tabelas Canônicas Oficiais do Consinco
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
    "mrl_prodvendadia": "MRL_PRODVENDADIA",
    "pontas_extraidas": "MRL_PONTOEXTRAPRODUTOEMPRESA",
    "pontas": "MRL_PONTOEXTRAPRODUTOEMPRESA",
    "tabelas_consico_oficiais": "DICIONARIO_TABELAS",
    "tabelas_consinco_oficiais": "DICIONARIO_TABELAS",
    "todas_colunas_consico_oficiais": "COLUNAS",
    "todas_colunas_consinco_oficiais": "COLUNAS"
}

DESCRICOES_CONHECIDAS = {
    "map_produto": "Cadastro Oficial de Produtos Consinco (97 Colunas)",
    "map_familia": "Cadastro Oficial de Famílias Comerciais Consinco",
    "map_categoria": "Departamentos, Seções e Grupos Mercadológicos",
    "map_famdivcateg": "Vínculo Família x Categoria / Departamento",
    "map_famfornec": "Fornecedor Principal de Produtos e Famílias",
    "map_prodcodigo": "Códigos de Barras EAN e Embalagens DUN/CX",
    "max_empresa": "Cadastro Oficial de Lojas e Centros de Distribuição",
    "max_comprador": "Cadastro de Compradores da Rede",
    "ge_pessoa": "Cadastro Geral de Fornecedores e Parceiros Comerciais",
    "mrl_produtoempresa": "Estoque de Loja, Depósito e Custos por Empresa",
    "mrl_prodempseg": "Tabela de Preços de Venda Normal e Promocional",
    "mrl_pontoextra": "Cadastro de Pontas de Gôndola e Ilhas",
    "mrl_pontoextraprodutoempresa": "Estoque Mínimo, Máximo e Vigência de Pontas por Loja",
    "fi_titulo": "Títulos Financeiros e Contas a Pagar",
    "msu_pedidosuprim": "Pedidos de Suprimento e Transferência em Trânsito",
    "tabelas_consico_oficiais": "Dicionário de Tabelas Oficiais do ERP Consinco (7.111 Tabelas)",
    "todas_colunas_consico_oficiais": "Dicionário de Colunas e Tipos de Dados Consinco (126.636 Colunas)"
}

def listar_arquivos_disponiveis():
    """Busca todos os arquivos .txt e .csv na pasta Banco_Consico, import_querys, aprendizado e zona_sql."""
    encontrados = {}
    
    # 1. Pasta Banco_Consico (Prioritária para tabelas oficiais Consinco)
    if os.path.exists(BANCO_CONSINCO_DIR):
        for f in sorted(os.listdir(BANCO_CONSINCO_DIR)):
            if (f.lower().endswith(".txt") or f.lower().endswith(".csv")) and f.lower() != "requeirements.txt":
                caminho = os.path.join(BANCO_CONSINCO_DIR, f)
                nome_base = os.path.splitext(f)[0].lower()
                tbl_oficial = MAPA_TABELAS_OFICIAIS.get(nome_base, nome_base.upper())
                encontrados[nome_base] = {
                    "arquivo": f,
                    "caminho": caminho,
                    "pasta": "Banco_Consico",
                    "tabela_destino": tbl_oficial,
                    "tamanho_kb": round(os.path.getsize(caminho) / 1024, 1),
                    "descricao": DESCRICOES_CONHECIDAS.get(nome_base, f"Tabela Oficial {tbl_oficial}")
                }

    # 2. Pasta import_querys (Arquivos adicionais)
    if os.path.exists(IMPORT_QUERYS_DIR):
        for f in sorted(os.listdir(IMPORT_QUERYS_DIR)):
            caminho_arq = os.path.join(IMPORT_QUERYS_DIR, f)
            if os.path.isfile(caminho_arq):
                if (f.lower().endswith(".txt") or f.lower().endswith(".csv")) and f.lower() != "requeirements.txt":
                    nome_base = os.path.splitext(f)[0].lower()
                    if nome_base not in encontrados:
                        tbl_oficial = MAPA_TABELAS_OFICIAIS.get(nome_base, nome_base.upper())
                        encontrados[nome_base] = {
                            "arquivo": f,
                            "caminho": caminho_arq,
                            "pasta": "import_querys",
                            "tabela_destino": tbl_oficial,
                            "tamanho_kb": round(os.path.getsize(caminho_arq) / 1024, 1),
                            "descricao": DESCRICOES_CONHECIDAS.get(nome_base, f"Tabela Oficial {tbl_oficial}")
                        }

    # 3. Pasta gerenciamento_sql/aprendizado (Dicionários oficiais)
    if os.path.exists(APRENDIZADO_DIR):
        for f in sorted(os.listdir(APRENDIZADO_DIR)):
            if f.lower().endswith(".txt"):
                caminho_arq = os.path.join(APRENDIZADO_DIR, f)
                nome_base = os.path.splitext(f)[0].lower()
                if nome_base not in encontrados:
                    tbl_oficial = MAPA_TABELAS_OFICIAIS.get(nome_base, nome_base.upper())
                    encontrados[nome_base] = {
                        "arquivo": f,
                        "caminho": caminho_arq,
                        "pasta": "aprendizado",
                        "tabela_destino": tbl_oficial,
                        "tamanho_kb": round(os.path.getsize(caminho_arq) / 1024, 1),
                        "descricao": DESCRICOES_CONHECIDAS.get(nome_base, f"Tabela Oficial {tbl_oficial}")
                    }

    # 4. Pasta local zona_sql
    for f in sorted(os.listdir(BASE_DIR)):
        if f.lower().endswith(".txt") or f.lower().endswith(".csv"):
            caminho_arq = os.path.join(BASE_DIR, f)
            nome_base = os.path.splitext(f)[0].lower()
            if nome_base not in encontrados:
                tbl_oficial = MAPA_TABELAS_OFICIAIS.get(nome_base, nome_base.upper())
                encontrados[nome_base] = {
                    "arquivo": f,
                    "caminho": caminho_arq,
                    "pasta": "zona_sql",
                    "tabela_destino": tbl_oficial,
                    "tamanho_kb": round(os.path.getsize(caminho_arq) / 1024, 1),
                    "descricao": DESCRICOES_CONHECIDAS.get(nome_base, f"Tabela Oficial {tbl_oficial}")
                }

    return encontrados

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
    
    # Número decimal simples com vírgula (ex: 10,50)
    if re.match(r'^-?\d+,\d+$', s):
        try:
            return float(s.replace(',', '.'))
        except:
            return s

    # Número inteiro (até 15 dígitos para evitar overflow em chaves de 44 dígitos)
    if re.match(r'^-?\d+$', s):
        if len(s) <= 15:
            try:
                return int(s)
            except:
                return s
        else:
            return s

    # Número float com ponto
    if re.match(r'^-?\d+\.\d+$', s):
        try:
            return float(s)
        except:
            return s

    return s

def importar_dicionario_tabelas(file_path):
    """Importa o catálogo oficial de 7.111 tabelas do Consinco."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS dicionario_tabelas')
    c.execute('''
        CREATE TABLE dicionario_tabelas (
            NOME_TABELA TEXT PRIMARY KEY,
            DESCRICAO_TABELA TEXT,
            QTD_LINHAS_ESTIMADA INTEGER,
            TABLESPACE_NAME TEXT,
            DATA_ULTIMA_ANALISE TEXT
        )
    ''')
    
    rows = []
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        header = f.readline()
        for line in f:
            line = line.strip()
            if not line: continue
            parts = line.split(';')
            if len(parts) >= 5:
                rows.append((parts[0].strip().upper(), parts[1].strip(), int(parts[2]) if parts[2].isdigit() else None, parts[3].strip(), parts[4].strip()))
            elif len(parts) >= 1:
                rows.append((parts[0].strip().upper(), '', None, '', ''))

    c.executemany('INSERT OR REPLACE INTO dicionario_tabelas VALUES (?, ?, ?, ?, ?)', rows)
    c.execute('CREATE INDEX IF NOT EXISTS idx_dict_tab ON dicionario_tabelas(NOME_TABELA)')
    conn.commit()
    conn.close()
    print(f"[+] Sucesso! {len(rows):,} tabelas oficiais salvas no catálogo dicionario_tabelas.")
    return True

def importar_dicionario_colunas(file_path):
    """Importa o catálogo oficial de 126.636 colunas do Consinco."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS colunas')
    c.execute('''
        CREATE TABLE colunas (
            NOME_TABELA TEXT,
            DESCRICAO_TABELA TEXT,
            ORDEM INTEGER,
            NOME_COLUNA TEXT,
            TIPO_DADOS TEXT,
            PERMITE_NULO TEXT,
            DESCRICAO_COLUNA TEXT
        )
    ''')
    
    rows = []
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        header = f.readline()
        for line in f:
            line = line.strip()
            if not line: continue
            parts = line.split(';')
            if len(parts) >= 7:
                ordem = int(parts[2]) if parts[2].isdigit() else 0
                rows.append((parts[0].strip().upper(), parts[1].strip(), ordem, parts[3].strip().upper(), parts[4].strip(), parts[5].strip(), parts[6].strip()))
            elif len(parts) >= 5:
                ordem = int(parts[2]) if parts[2].isdigit() else 0
                rows.append((parts[0].strip().upper(), parts[1].strip(), ordem, parts[3].strip().upper(), parts[4].strip(), 'Y', ''))

    c.executemany('INSERT INTO colunas VALUES (?, ?, ?, ?, ?, ?, ?)', rows)
    c.execute('CREATE INDEX IF NOT EXISTS idx_colunas_tab ON colunas(NOME_TABELA)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_colunas_col ON colunas(NOME_COLUNA)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_colunas_ord ON colunas(NOME_TABELA, ORDEM)')
    conn.commit()
    conn.close()
    print(f"[+] Sucesso! {len(rows):,} colunas oficiais salvas na tabela colunas.")
    return True

def importar_map_produto_oficial(file_path):
    """Importa a tabela MAP_PRODUTO garantindo os 97 campos oficiais."""
    with open(file_path, 'r', encoding='latin1', errors='replace') as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        print("[-] Arquivo vazio.")
        return False

    headers = [h.strip().upper() for h in lines[0].split(';')]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM MAP_PRODUTO")  # Limpar registros antigos para garantir 100% dados reais

    count_imported = 0
    for line in lines[1:]:
        parts = line.split(';')
        if len(parts) < len(headers):
            parts.extend([''] * (len(headers) - len(parts)))
        row = dict(zip(headers, parts))
        
        seqp = int(row.get('SEQPRODUTO') or 0)
        if seqp <= 0:
            continue
            
        cols = []
        vals = []
        for k, v in row.items():
            cols.append(k)
            sanitized = sanitizar_valor(v)
            vals.append(sanitized)

        if 'STATUS' not in cols:
            cols.append('STATUS')
            vals.append('A')

        placeholders = ','.join(['?'] * len(cols))
        col_names = ','.join(cols)
        update_clause = ', '.join([f"{c}=excluded.{c}" for c in cols if c != 'SEQPRODUTO'])

        cursor.execute(f"""
            INSERT INTO MAP_PRODUTO ({col_names})
            VALUES ({placeholders})
            ON CONFLICT(SEQPRODUTO) DO UPDATE SET {update_clause}
        """, vals)
        count_imported += 1

    conn.commit()
    conn.close()
    print(f"[+] Sucesso! {count_imported} produtos oficiais importados para MAP_PRODUTO.")
    return True

def importar_pontas_gondola(file_path):
    """Importa dados de pontas de gôndola garantindo capas e regras por empresa."""
    with open(file_path, 'r', encoding='latin1', errors='ignore') as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines: return False
    sep = detectar_delimitador(lines[0])
    headers = [h.strip().upper().replace('"', '') for h in lines[0].split(sep)]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    records = 0
    for l_idx, line in enumerate(lines[1:], start=2):
        parts = [p.strip().replace('"', '') for p in line.split(sep)]
        if len(parts) < len(headers): parts.extend([''] * (len(headers) - len(parts)))
        row = dict(zip(headers, parts))

        seqponto = int(float(str(row.get('SEQPONTOEXTRA') or row.get('COD_PONTO_EXTRA') or 203).replace(',', '.')))
        nome_ponto = row.get('NOME_PONTO_EXTRA') or row.get('DESCRICAO_PONTO') or f"Ponto {seqponto}"
        seqprod = int(float(str(row.get('SEQPRODUTO') or row.get('COD_PRODUTO') or 0).replace(',', '.')))
        desc_prod = row.get('DESCRICAO_PRODUTO') or row.get('DESCCOMPLETA') or f"Produto {seqprod}"
        nroemp = int(float(str(row.get('NROEMPRESA') or row.get('LOJA') or 1).replace(',', '.')))
        nome_emp = row.get('NOME_LOJA') or row.get('FANTASIA') or f"Loja {nroemp}"

        estqmin = float(str(row.get('ESTQMINIMO') or 0).replace(',', '.'))
        estqmax = float(str(row.get('ESTQMAXIMO') or 0).replace(',', '.'))
        dt_ini = row.get('DTAVIGENCIAINICIO') or '2026-08-01'
        dt_fim = row.get('DTAVIGENCIAFIM') or '2026-12-31'
        seqvig = int(float(str(row.get('SEQVIGENCIA') or (500 + l_idx)).replace(',', '.')))

        if seqprod <= 0: continue

        cursor.execute("INSERT INTO MRL_PONTOEXTRA (SEQPONTOEXTRA, DESCRICAO, STATUS) VALUES (?, ?, 'A') ON CONFLICT(SEQPONTOEXTRA) DO UPDATE SET DESCRICAO=excluded.DESCRICAO", (seqponto, nome_ponto))
        cursor.execute("INSERT INTO MAP_PRODUTO (SEQPRODUTO, DESCCOMPLETA, DESCREDUZIDA, SEQFAMILIA, STATUS) VALUES (?, ?, ?, 100, 'A') ON CONFLICT(SEQPRODUTO) DO NOTHING", (seqprod, desc_prod, desc_prod[:20]))
        cursor.execute("INSERT INTO MAX_EMPRESA (NROEMPRESA, NOMERAZAO, FANTASIA, RAZAOSOCIAL) VALUES (?, ?, ?, ?) ON CONFLICT(NROEMPRESA) DO UPDATE SET FANTASIA=excluded.FANTASIA", (nroemp, nome_emp, nome_emp, nome_emp))
        cursor.execute("INSERT INTO MRL_PONTOEXTRAPRODUTO (SEQPONTOEXTRA, SEQPRODUTO, STATUS) VALUES (?, ?, 'A') ON CONFLICT(SEQPONTOEXTRA, SEQPRODUTO) DO UPDATE SET STATUS='A'", (seqponto, seqprod))
        cursor.execute("""
            INSERT INTO MRL_PONTOEXTRAPRODUTOEMPRESA (
                SEQPONTOEXTRA, SEQPRODUTO, NROEMPRESA, SEQVIGENCIA,
                ESTQMINIMO, ESTQMAXIMO, DTAVIGENCIAINICIO, DTAVIGENCIAFIM,
                QTDDIASSUGESTAO, STATUS
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'A')
            ON CONFLICT(SEQPONTOEXTRA, SEQPRODUTO, NROEMPRESA, SEQVIGENCIA) DO UPDATE SET
                ESTQMINIMO=excluded.ESTQMINIMO,
                ESTQMAXIMO=excluded.ESTQMAXIMO,
                DTAVIGENCIAINICIO=excluded.DTAVIGENCIAINICIO,
                DTAVIGENCIAFIM=excluded.DTAVIGENCIAFIM,
                STATUS=excluded.STATUS
        """, (seqponto, seqprod, nroemp, seqvig, estqmin, estqmax, dt_ini, dt_fim))
        records += 1

    conn.commit()
    conn.close()
    print(f"[+] Sucesso! {records} regras de pontas gravadas em MRL_PONTOEXTRAPRODUTOEMPRESA.")
    return True

def importar_arquivo_generico(file_path, table_name):
    """Importação universal para qualquer tabela oficial do Consinco."""
    if not os.path.exists(file_path):
        print(f"[-] Arquivo não encontrado: {file_path}")
        return False

    with open(file_path, 'r', encoding='latin1', errors='replace') as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        print("[-] Arquivo vazio.")
        return False

    sep = detectar_delimitador(lines[0])
    raw_headers = [h.strip().replace('"', '').replace("'", "") for h in lines[0].split(sep)]
    headers = [re.sub(r'[^A-Za-z0-9_]', '_', h).upper() for h in raw_headers]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Compatibilidade amigável para MAX_EMPRESA (garantir NOMERAZAO se tiver RAZAOSOCIAL)
    if table_name == 'MAX_EMPRESA' and 'NOMERAZAO' not in headers:
        headers.append('NOMERAZAO')
        has_nomerazao_in_txt = False
    else:
        has_nomerazao_in_txt = True

    # Recriar tabela com o schema exato do arquivo oficial
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
        if not has_nomerazao_in_txt:
            # Pegar RAZAOSOCIAL ou FANTASIA
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
        if len(batch) >= 2000:
            cursor.executemany(insert_sql, batch)
            batch = []

    if batch:
        cursor.executemany(insert_sql, batch)

    conn.commit()
    conn.close()
    print(f"[+] Sucesso! {count:,} registros importados para a tabela oficial {table_name}.")
    return True

def executar_importacao(caminho, nome_identificador):
    """Roteador de importação especializada ou genérica."""
    nome_low = nome_identificador.lower()
    tbl_oficial = MAPA_TABELAS_OFICIAIS.get(nome_low, nome_identificador.upper())

    print(f"\n=======================================================")
    print(f"IMPORTANDO DADOS: {os.path.basename(caminho)}")
    print(f"Tabela Destino Oficial Consinco: {tbl_oficial}")
    print(f"=======================================================")

    t0 = time.time()
    if tbl_oficial == "DICIONARIO_TABELAS":
        res = importar_dicionario_tabelas(caminho)
    elif tbl_oficial == "COLUNAS":
        res = importar_dicionario_colunas(caminho)
    elif tbl_oficial == "MAP_PRODUTO":
        res = importar_map_produto_oficial(caminho)
    elif nome_low in ["pontas_extraidas", "pontas"]:
        res = importar_pontas_gondola(caminho)
    else:
        res = importar_arquivo_generico(caminho, tbl_oficial)

    print(f"Tempo total: {time.time() - t0:.2f}s")
    return res

def menu_interativo():
    print("\n" + "="*70)
    print("  SIMULADOR ZONA SQL - IMPORTADOR MESTRE DE TABELAS CONSINCO")
    print("="*70)
    
    arquivos = listar_arquivos_disponiveis()
    if not arquivos:
        print("[!] Nenhum arquivo .txt ou .csv encontrado na pasta Banco_Consico ou import_querys.")
        return

    print("\nArquivos disponíveis para sincronização:")
    lista_chaves = list(arquivos.keys())
    for idx, chave in enumerate(lista_chaves, 1):
        info = arquivos[chave]
        print(f"  [{idx:2d}] {info['arquivo']:<35s} -> {info['tabela_destino']:<25s} ({info['tamanho_kb']:>6.1f} KB)")
        print(f"       └─ {info['descricao']}")

    print("\nOpções:")
    print("  - Digite o NÚMERO (ex: 1) ou o NOME do arquivo (ex: map_produto)")
    print("  - Digite 'todas' para importar todas as tabelas em lote")
    print("  - Digite 'sair' para encerrar")
    
    try:
        escolha = input("\nQual tabela deseja importar? > ").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if not escolha or escolha.lower() in ('sair', 'exit', 'q'):
        print("Operação cancelada.")
        return

    if escolha.lower() in ('todas', 'all', '*'):
        print(f"\n[+] Iniciando importação em lote de {len(lista_chaves)} arquivos...")
        for k in lista_chaves:
            executar_importacao(arquivos[k]["caminho"], k)
        return

    # Buscar arquivo escolhido
    caminho, ident = None, None
    if escolha.isdigit():
        idx = int(escolha) - 1
        if 0 <= idx < len(lista_chaves):
            ident = lista_chaves[idx]
            caminho = arquivos[ident]["caminho"]
    else:
        nome_low = os.path.splitext(escolha.lower())[0]
        if nome_low in arquivos:
            ident = nome_low
            caminho = arquivos[nome_low]["caminho"]

    if caminho and os.path.exists(caminho):
        executar_importacao(caminho, ident)
    else:
        print(f"[-] Arquivo ou opção '{escolha}' não encontrada.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        param = sys.argv[1].strip()
        arquivos = listar_arquivos_disponiveis()
        if param.lower() == "todas":
            for k, info in arquivos.items():
                executar_importacao(info["caminho"], k)
        else:
            nome_low = os.path.splitext(param.lower())[0]
            if nome_low in arquivos:
                executar_importacao(arquivos[nome_low]["caminho"], nome_low)
            elif os.path.exists(param):
                executar_importacao(param, os.path.splitext(os.path.basename(param))[0])
            else:
                print(f"[-] Arquivo '{param}' não encontrado.")
    else:
        menu_interativo()
