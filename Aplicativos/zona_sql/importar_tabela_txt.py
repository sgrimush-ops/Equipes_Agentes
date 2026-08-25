"""
Importador Universal de Tabelas TXT / CSV para o Simulador de Banco Consinco (Zona SQL)

Uso Interativo:
    python importar_tabela_txt.py
    (Você digita o nome do arquivo, ex: 'map_produto', ou o número da lista, e ele busca automaticamente na pasta import_querys)

Uso por Linha de Comando:
    python importar_tabela_txt.py map_produto
    python importar_tabela_txt.py ean_dun.txt
    python importar_tabela_txt.py a_pagar
    python importar_tabela_txt.py todas
"""

import os
import sys
import sqlite3
import re
import time

# Garantir compatibilidade total de encoding no console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "banco_simulador_consinco.db")
IMPORT_QUERYS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "import_querys"))

# Mapeamento amigável de nomes e descrições
DESCRICOES_CONHECIDAS = {
    "map_produto": "Cadastro Oficial de Produtos Consinco (97 Colunas)",
    "ean_dun": "Códigos de Barras EAN e Embalagens DUN/CX",
    "a_pagar": "Títulos e Contas a Pagar Financeiro (FI_TITULO)",
    "a_pagar_empresa": "Títulos e Contas a Pagar por Loja/Empresa",
    "ped_pendente": "Pedidos de Suprimento e Transferência Pendentes",
    "nivel_atendimento_cds": "Nível de Atendimento e Ruptura dos CDs",
    "ranking_abc_produtos": "Curva ABC e Ranking de Faturamento de Produtos",
    "ranking": "Ranking e Desempenho de Fornecedores",
    "query": "Base Analítica Consolidada de Estoque e Venda",
    "query_bz": "Base Analítica de Estoque Rede Baklizi",
    "pontas_extraidas": "Manutenção de Pontas de Gôndola / Estoques Mín e Máx"
}

def listar_arquivos_disponiveis():
    """Busca todos os arquivos .txt e .csv na pasta import_querys e zona_sql."""
    encontrados = {}
    
    # 1. Pasta import_querys
    if os.path.exists(IMPORT_QUERYS_DIR):
        for f in sorted(os.listdir(IMPORT_QUERYS_DIR)):
            if (f.lower().endswith(".txt") or f.lower().endswith(".csv")) and f.lower() != "requeirements.txt":
                caminho = os.path.join(IMPORT_QUERYS_DIR, f)
                nome_base = os.path.splitext(f)[0].lower()
                encontrados[nome_base] = {
                    "arquivo": f,
                    "caminho": caminho,
                    "pasta": "import_querys",
                    "tamanho_kb": round(os.path.getsize(caminho) / 1024, 1),
                    "descricao": DESCRICOES_CONHECIDAS.get(nome_base, "Tabela de Dados Consinco")
                }

    # 2. Pasta local zona_sql
    for f in sorted(os.listdir(BASE_DIR)):
        if f.lower().endswith(".txt") or f.lower().endswith(".csv"):
            caminho = os.path.join(BASE_DIR, f)
            nome_base = os.path.splitext(f)[0].lower()
            if nome_base not in encontrados:
                encontrados[nome_base] = {
                    "arquivo": f,
                    "caminho": caminho,
                    "pasta": "zona_sql",
                    "tamanho_kb": round(os.path.getsize(caminho) / 1024, 1),
                    "descricao": DESCRICOES_CONHECIDAS.get(nome_base, "Arquivo Local de Dados")
                }

    return encontrados

def resolver_caminho_arquivo(entrada, arquivos_disp):
    """Localiza o arquivo a partir do nome digitado pelo usuário ou número."""
    entrada_limpa = entrada.strip().lower()

    # Caso 1: Usuário digitou um número da lista
    if entrada_limpa.isdigit():
        idx = int(entrada_limpa) - 1
        lista_chaves = list(arquivos_disp.keys())
        if 0 <= idx < len(lista_chaves):
            chave = lista_chaves[idx]
            return arquivos_disp[chave]["caminho"], chave.upper()

    # Caso 2: Usuário digitou o nome base ou nome com extensão
    nome_base = os.path.splitext(entrada_limpa)[0]
    if nome_base in arquivos_disp:
        return arquivos_disp[nome_base]["caminho"], nome_base.upper()

    # Caso 3: Busca direta por caminho absoluto ou relativo
    if os.path.exists(entrada):
        t_name = os.path.splitext(os.path.basename(entrada))[0].upper()
        return os.path.abspath(entrada), t_name

    # Caso 4: Tentar em import_querys com extensão .txt ou .csv
    for ext in [".txt", ".csv"]:
        cand1 = os.path.join(IMPORT_QUERYS_DIR, entrada_limpa + ext)
        if os.path.exists(cand1):
            return cand1, entrada_limpa.upper()
        cand2 = os.path.join(BASE_DIR, entrada_limpa + ext)
        if os.path.exists(cand2):
            return cand2, entrada_limpa.upper()

    return None, None

def detectar_delimitador(linha):
    """Detecta automaticamente o delimitador da linha."""
    contagens = {
        ';': linha.count(';'),
        '\t': linha.count('\t'),
        ',': linha.count(','),
        '|': linha.count('|')
    }
    delim = max(contagens, key=contagens.get)
    return delim if contagens[delim] > 0 else ';'

def sanitizar_nome_coluna(col):
    """Limpa e formata o nome da coluna para padrão SQL Consinco."""
    c = col.strip().upper()
    c = re.sub(r'[^A-Z0-9_]', '_', c)
    c = re.sub(r'_+', '_', c).strip('_')
    if not c or c[0].isdigit():
        c = 'COL_' + c
    return c

def inferir_tipo_valor(v):
    """Tenta converter strings para int, float ou mantém string limpa."""
    if v is None:
        return None
    s = str(v).strip()
    if s == '' or s.upper() in ('NULL', 'NONE'):
        return None
    
    # Tentar inteiro
    if re.match(r'^-?\d+$', s):
        try:
            return int(s)
        except:
            pass
            
    # Tentar float formato brasileiro (ex: 1.234,56 ou 1234,56)
    if re.match(r'^-?\d{1,3}(\.\d{3})*,\d+$', s) or re.match(r'^-?\d+,\d+$', s):
        try:
            s_clean = s.replace('.', '').replace(',', '.')
            return float(s_clean)
        except:
            pass

    # Tentar float padrão
    if re.match(r'^-?\d+\.\d+$', s):
        try:
            return float(s)
        except:
            pass

    # Limpar datas com excesso de microssegundos se houver
    if re.match(r'^\d{4}-\d{2}-\d{2}-\d{2}\.\d{2}\.\d{2}', s):
        # Ex: 2026-08-25-15.52.54.000000 -> 2026-08-25 15:52:54
        s_date = s[:10] + ' ' + s[11:19].replace('.', ':')
        return s_date

    return s

def garantir_tabela(cursor, nome_tabela, colunas, tipos_amostra):
    """Garante que a tabela existe com todas as colunas necessárias."""
    # Verificar se a tabela já existe
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND UPPER(name)='{nome_tabela.upper()}'")
    existe = cursor.fetchone() is not None

    if not existe:
        col_defs = []
        for col in colunas:
            tipo = tipos_amostra.get(col, 'TEXT')
            if col.startswith('SEQ') or col.startswith('COD') or col.startswith('NRO'):
                # Priorizar campos de sequência como inteiros
                if tipo == 'INTEGER' or tipo == 'TEXT':
                    tipo = 'INTEGER'
            col_defs.append(f"    {col} {tipo}")
            
        sql_create = f"CREATE TABLE {nome_tabela} (\n" + ",\n".join(col_defs) + "\n);"
        cursor.execute(sql_create)
    else:
        # Tabela já existe -> verificar se faltam colunas
        cursor.execute(f"PRAGMA table_info({nome_tabela})")
        existentes = set(r[1].upper() for r in cursor.fetchall())
        
        for col in colunas:
            if col.upper() not in existentes:
                tipo = tipos_amostra.get(col, 'TEXT')
                try:
                    cursor.execute(f"ALTER TABLE {nome_tabela} ADD COLUMN {col} {tipo}")
                except Exception as e:
                    pass

def importar_arquivo(caminho_arquivo, nome_tabela=None):
    """Executa a importação completa do arquivo para o SQLite da Zona SQL."""
    inicio = time.time()
    
    if not os.path.exists(caminho_arquivo):
        print(f"[-] Erro: Arquivo '{caminho_arquivo}' não encontrado.")
        return False

    if nome_tabela is None:
        nome_tabela = os.path.splitext(os.path.basename(caminho_arquivo))[0].upper()

    print(f"\n=======================================================")
    print(f"📥 IMPORTANDO: {os.path.basename(caminho_arquivo)}")
    print(f"📁 Origem: {caminho_arquivo}")
    print(f"💾 Tabela Alvo: {nome_tabela}")
    print(f"=======================================================")

    # 1. Leitura com suporte a latin1 e utf-8
    linhas = []
    for enc in ['latin1', 'utf-8', 'cp1252']:
        try:
            with open(caminho_arquivo, 'r', encoding=enc) as f:
                linhas = [l.strip() for l in f if l.strip()]
            if linhas:
                break
        except Exception:
            continue

    if not linhas:
        print("[-] Arquivo vazio ou ilegível.")
        return False

    delimitador = detectar_delimitador(linhas[0])
    raw_headers = linhas[0].split(delimitador)
    colunas = [sanitizar_nome_coluna(h) for h in raw_headers]

    print(f"[+] Delimitador detectado: '{delimitador}'")
    print(f"[+] Total de Colunas ({len(colunas)}): {', '.join(colunas[:6])}{'...' if len(colunas) > 6 else ''}")
    print(f"[+] Total de Linhas no Arquivo: {len(linhas) - 1:,}")

    # 2. Amostragem de tipos
    tipos_amostra = {}
    linhas_amostra = linhas[1:min(50, len(linhas))]
    for col_idx, col in enumerate(colunas):
        tipo_detectado = 'INTEGER'
        for l in linhas_amostra:
            parts = l.split(delimitador)
            if col_idx < len(parts):
                val = inferir_tipo_valor(parts[col_idx])
                if isinstance(val, float):
                    tipo_detectado = 'REAL'
                elif isinstance(val, str) and tipo_detectado != 'REAL':
                    tipo_detectado = 'TEXT'
        tipos_amostra[col] = tipo_detectado

    # 3. Conectar ao Banco e Garantir Estrutura
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    garantir_tabela(cursor, nome_tabela, colunas, tipos_amostra)

    # 4. Inserção em Lotes (Batch Execution)
    placeholders = ",".join(["?"] * len(colunas))
    cols_str = ",".join(colunas)
    sql_insert = f"INSERT OR REPLACE INTO {nome_tabela} ({cols_str}) VALUES ({placeholders})"

    batch = []
    total_inserido = 0
    primeiros_registros = []

    for l in linhas[1:]:
        parts = l.split(delimitador)
        if len(parts) < len(colunas):
            parts.extend([''] * (len(colunas) - len(parts)))
        elif len(parts) > len(colunas):
            parts = parts[:len(colunas)]

        row_vals = [inferir_tipo_valor(p) for p in parts]
        batch.append(row_vals)

        if len(primeiros_registros) < 3:
            primeiros_registros.append(dict(zip(colunas[:6], row_vals[:6])))

        if len(batch) >= 1000:
            cursor.executemany(sql_insert, batch)
            total_inserido += len(batch)
            batch = []

    if batch:
        cursor.executemany(sql_insert, batch)
        total_inserido += len(batch)

    # 5. Tratamentos Especializados para Consistência Relacional
    if nome_tabela == "MAP_PRODUTO":
        # Se importou MAP_PRODUTO, garantir que STATUS padrão seja 'A'
        try:
            cursor.execute("UPDATE MAP_PRODUTO SET STATUS='A' WHERE STATUS IS NULL OR STATUS=''")
        except Exception:
            pass

    conn.commit()
    conn.close()

    tempo_gasto = round(time.time() - inicio, 2)
    print(f"\n✅ SUCESSO! {total_inserido:,} registros importados para a tabela '{nome_tabela}' em {tempo_gasto}s!")
    
    print("\n🔍 Amostra dos Dados Importados (Primeiras Colunas):")
    for idx, r in enumerate(primeiros_registros, 1):
        print(f"  [{idx}] {r}")

    return True

def main():
    print("=======================================================")
    print("       IMPORTADOR DE TABELAS TXT - ZONA SQL ERP        ")
    print("=======================================================")

    arquivos_disp = listar_arquivos_disponiveis()

    # Se recebeu argumento na linha de comando
    if len(sys.argv) > 1:
        alvo = sys.argv[1].strip()
        if alvo.lower() in ("todas", "all", "*"):
            print(f"\n🚀 Importando todos os {len(arquivos_disp)} arquivos disponíveis...")
            for chave, info in arquivos_disp.items():
                importar_arquivo(info["caminho"], chave.upper())
            print("\n🎉 Todas as tabelas foram importadas com sucesso para a Zona SQL!")
            return
        else:
            caminho, t_name = resolver_caminho_arquivo(alvo, arquivos_disp)
            if caminho:
                importar_arquivo(caminho, t_name)
            else:
                print(f"[-] Arquivo correspondente a '{alvo}' não encontrado.")
            return

    # Modo Interativo: Exibir Lista Numerada
    print("\n📂 Arquivos disponíveis para importação:")
    lista_chaves = list(arquivos_disp.keys())
    for idx, chave in enumerate(lista_chaves, 1):
        info = arquivos_disp[chave]
        print(f"  [{idx:2d}] {info['arquivo']:25s} ({info['tamanho_kb']:>6.1f} KB) - {info['descricao']}")

    print(f"  [ T] TODAS AS TABELAS         - Importa todos os {len(lista_chaves)} arquivos de uma vez")
    print(f"  [ Q] Sair")

    try:
        escolha = input("\n👉 Digite o nome do arquivo (ex: map_produto), número [1-10] ou 'T': ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nOperação cancelada.")
        return

    if not escolha or escolha.lower() in ('q', 'quit', 'exit', 'sair'):
        print("Saindo sem alterações.")
        return

    if escolha.lower() in ('t', 'todas', 'all'):
        print(f"\n🚀 Importando todas as {len(arquivos_disp)} tabelas...")
        for chave, info in arquivos_disp.items():
            importar_arquivo(info["caminho"], chave.upper())
        print("\n🎉 Todas as tabelas foram importadas com sucesso para a Zona SQL!")
        return

    caminho, t_name = resolver_caminho_arquivo(escolha, arquivos_disp)
    if caminho:
        importar_arquivo(caminho, t_name)
    else:
        print(f"\n[-] Erro: Não foi possível localizar o arquivo correspondente a '{escolha}'.")
        print(f"    Verifique se o arquivo existe na pasta '{IMPORT_QUERYS_DIR}'.")

if __name__ == "__main__":
    main()
