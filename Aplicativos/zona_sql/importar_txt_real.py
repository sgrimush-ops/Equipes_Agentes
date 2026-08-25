"""
Script para importar dados REAIS exportados do Totvs Consinco (arquivo .txt ou .csv)
diretamente para o banco de dados da Zona SQL (banco_simulador_consinco.db).

Uso:
    python importar_txt_real.py caminho_do_arquivo.txt
ou simplesmente coloque o arquivo como 'pontas_extraidas.txt' nesta pasta e execute:
    python importar_txt_real.py
"""

import os
import sys
import sqlite3
import re
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "banco_simulador_consinco.db")

def parse_val(v, default=0.0):
    if v is None:
        return default
    s = str(v).strip().replace(',', '.')
    try:
        return float(s)
    except:
        return default

def parse_int(v, default=0):
    if v is None:
        return default
    s = str(v).strip()
    try:
        return int(float(s.replace(',', '.')))
    except:
        return default

def import_real_txt(file_path):
    if not os.path.exists(file_path):
        print(f"[-] Erro: Arquivo nao encontrado: {file_path}")
        return False

    print(f"[+] Lendo arquivo real exportado do Consinco: {file_path}")
    
    with open(file_path, 'r', encoding='latin1', errors='ignore') as f:
        content = f.read()

    lines = [l.strip() for l in content.splitlines() if l.strip()]
    if not lines:
        print("[-] Arquivo vazio.")
        return False

    # Detectar delimitador (tab, ponto e virgula ou virgula)
    header_line = lines[0]
    if '\t' in header_line:
        sep = '\t'
    elif ';' in header_line:
        sep = ';'
    else:
        sep = ','

    headers = [h.strip().upper().replace('"', '') for h in header_line.split(sep)]
    print(f"[+] Cabecalhos detectados ({len(headers)} colunas): {headers}")

    col_map = {}
    for idx, h in enumerate(headers):
        col_map[h] = idx

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    pontos_map = {}
    produtos_map = {}
    empresas_map = {}
    records_count = 0

    for l_idx, line in enumerate(lines[1:], start=2):
        parts = [p.strip().replace('"', '') for p in line.split(sep)]
        if len(parts) < len(headers):
            # Preencher colunas faltantes se houver
            parts.extend([''] * (len(headers) - len(parts)))

        row = {}
        for h, idx in col_map.items():
            row[h] = parts[idx] if idx < len(parts) else ''

        # Identificar colunas essenciais com suporte a variacoes de nomes
        seqponto = parse_int(row.get('SEQPONTOEXTRA') or row.get('COD_PONTO_EXTRA') or row.get('SEQPONTO') or 203)
        nome_ponto = row.get('NOME_PONTO_EXTRA') or row.get('DESCRICAO_PONTO') or row.get('DESCRICAO') or f"Ponto Extra {seqponto}"
        
        seqprod = parse_int(row.get('SEQPRODUTO') or row.get('COD_PRODUTO') or 0)
        desc_prod = row.get('DESCRICAO_PRODUTO') or row.get('DESCCOMPLETA') or row.get('PRODUTO') or f"Produto {seqprod}"
        
        nroemp = parse_int(row.get('NROEMPRESA') or row.get('LOJA') or row.get('EMPRESA') or 1)
        nome_emp = row.get('NOME_LOJA') or row.get('LOJA') or row.get('FANTASIA') or f"Loja {nroemp}"
        
        estqmin = parse_val(row.get('ESTQMINIMO') or row.get('MINIMO') or row.get('MINIMO_PONTO_EXTRA') or 0)
        estqmax = parse_val(row.get('ESTQMAXIMO') or row.get('MAXIMO') or row.get('MAXIMO_PONTO_EXTRA') or 0)
        
        dt_ini = row.get('DTAVIGENCIAINICIO') or row.get('INICIO_VIGENCIA') or '2026-08-01'
        dt_fim = row.get('DTAVIGENCIAFIM') or row.get('FIM_VIGENCIA') or '2026-12-31'
        
        # Normalizar datas DD/MM/YYYY para YYYY-MM-DD se necessario
        if '/' in dt_ini:
            p = dt_ini.split('/')
            if len(p) == 3:
                dt_ini = f"{p[2]}-{p[1].zfill(2)}-{p[0].zfill(2)}"
        if '/' in dt_fim:
            p = dt_fim.split('/')
            if len(p) == 3:
                dt_fim = f"{p[2]}-{p[1].zfill(2)}-{p[0].zfill(2)}"

        sugestao = parse_val(row.get('QTDDIASSUGESTAO') or 0)
        status = (row.get('STATUS') or row.get('STATUS_ITEM_EMP') or 'A').strip().upper()[:1] or 'A'
        seqvig = parse_int(row.get('SEQVIGENCIA') or (500 + l_idx))
        estq_loja = parse_val(row.get('ESTOQUE_ATUAL_LOJA') or row.get('ESTQLOJA') or 0)

        if seqprod <= 0:
            continue

        pontos_map[seqponto] = nome_ponto
        produtos_map[seqprod] = desc_prod
        empresas_map[nroemp] = nome_emp

        # Inserir/Atualizar PONTOEXTRA
        cursor.execute("""
            INSERT INTO MRL_PONTOEXTRA (SEQPONTOEXTRA, DESCRICAO, STATUS)
            VALUES (?, ?, 'A')
            ON CONFLICT(SEQPONTOEXTRA) DO UPDATE SET DESCRICAO=excluded.DESCRICAO
        """, (seqponto, nome_ponto))

        # Inserir/Atualizar PRODUTO
        cursor.execute("""
            INSERT INTO MAP_PRODUTO (SEQPRODUTO, DESCCOMPLETA, DESCREDUZIDA, SEQFAMILIA, STATUS)
            VALUES (?, ?, ?, 100, 'A')
            ON CONFLICT(SEQPRODUTO) DO UPDATE SET DESCCOMPLETA=excluded.DESCCOMPLETA
        """, (seqprod, desc_prod, desc_prod[:20]))

        # Inserir/Atualizar EMPRESA
        cursor.execute("""
            INSERT INTO MAX_EMPRESA (NROEMPRESA, NOMERAZAO, FANTASIA, RAZAOSOCIAL)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(NROEMPRESA) DO UPDATE SET FANTASIA=excluded.FANTASIA, RAZAOSOCIAL=excluded.RAZAOSOCIAL
        """, (nroemp, nome_emp, nome_emp, nome_emp))

        # Inserir vinculo PONTOEXTRAPRODUTO
        cursor.execute("""
            INSERT INTO MRL_PONTOEXTRAPRODUTO (SEQPONTOEXTRA, SEQPRODUTO, STATUS)
            VALUES (?, ?, 'A')
            ON CONFLICT(SEQPONTOEXTRA, SEQPRODUTO) DO UPDATE SET STATUS='A'
        """, (seqponto, seqprod))

        # Inserir regra PONTOEXTRAPRODUTOEMPRESA
        cursor.execute("""
            INSERT INTO MRL_PONTOEXTRAPRODUTOEMPRESA (
                SEQPONTOEXTRA, SEQPRODUTO, NROEMPRESA, SEQVIGENCIA,
                ESTQMINIMO, ESTQMAXIMO, DTAVIGENCIAINICIO, DTAVIGENCIAFIM,
                QTDDIASSUGESTAO, STATUS
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(SEQPONTOEXTRA, SEQPRODUTO, NROEMPRESA, SEQVIGENCIA) DO UPDATE SET
                ESTQMINIMO=excluded.ESTQMINIMO,
                ESTQMAXIMO=excluded.ESTQMAXIMO,
                DTAVIGENCIAINICIO=excluded.DTAVIGENCIAINICIO,
                DTAVIGENCIAFIM=excluded.DTAVIGENCIAFIM,
                STATUS=excluded.STATUS
        """, (seqponto, seqprod, nroemp, seqvig, estqmin, estqmax, dt_ini, dt_fim, sugestao, status))

        # Atualizar estoque loja de balizamento
        if estq_loja > 0:
            cursor.execute("""
                INSERT INTO MRL_PRODUTOEMPRESA (SEQPRODUTO, NROEMPRESA, ESTQLOJA, STATUSCOMPRA)
                VALUES (?, ?, ?, 'A')
                ON CONFLICT(SEQPRODUTO, NROEMPRESA) DO UPDATE SET ESTQLOJA=excluded.ESTQLOJA
            """, (seqprod, nroemp, estq_loja))

        records_count += 1

    conn.commit()
    conn.close()

    print(f"[+] Sucesso! {records_count} linhas reais importadas para o banco da Zona SQL!")
    print(f"    - {len(pontos_map)} Pontos Extras cadastrados")
    print(f"    - {len(produtos_map)} Produtos reais cadastrados")
    print(f"    - {len(empresas_map)} Lojas cadastradas")
    return True

if __name__ == "__main__":
    target = None
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        candidates = ["pontas_extraidas.txt", "pontas.txt", "pontas.csv", "extracao_consinco.txt"]
        for c in candidates:
            if os.path.exists(c):
                target = c
                break

    if not target:
        print("[!] Por favor, informe o caminho do arquivo TXT/CSV exportado do Consinco.")
        print("    Exemplo: python importar_txt_real.py C:\\Users\\usr\\Downloads\\meu_arquivo.txt")
    else:
        import_real_txt(target)
