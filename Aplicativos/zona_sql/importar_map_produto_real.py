"""
Script para sincronizar e atualizar a tabela MAP_PRODUTO da Zona SQL
a partir do arquivo oficial map_produto.txt da pasta import_querys.

Uso:
    python importar_map_produto_real.py
"""

import os
import sys
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "database", "banco_simulador_consinco.db")
DEFAULT_TXT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "import_querys", "map_produto.txt"))

def sync_map_produto(txt_path=None):
    if txt_path is None:
        txt_path = DEFAULT_TXT

    if not os.path.exists(txt_path):
        print(f"[-] Erro: Arquivo map_produto.txt nao encontrado em: {txt_path}")
        return False

    print(f"[+] Lendo arquivo oficial MAP_PRODUTO: {txt_path}")
    with open(txt_path, 'r', encoding='latin1') as f:
        lines = [l.strip() for l in f if l.strip()]

    if not lines:
        print("[-] Arquivo vazio.")
        return False

    headers = [h.strip().upper() for h in lines[0].split(';')]
    print(f"[+] Estrutura oficial detectada com {len(headers)} colunas!")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

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
            if k in ('SEQPRODUTO', 'SEQFAMILIA', 'PZOVALIDADEDIA', 'PZOVALIDADEMES', 'NROITEMFIXO', 'SEQBULARIO', 'SEQPRODUTOTMP', 'PZOVALIDLOTE', 'SEQPRODRELACLOTE', 'SEQPRODUTOSECUNDARIO', 'SEQPRODUTOBASEANTIGO', 'SEQPRODUTOEMBALAGEM', 'PZOVALIDADENATIMORTO', 'PZOVALIDADEDIASAIDA', 'NRODIASVALPRODRESFRIADO', 'NRODIASVALPRODABERTO', 'SEQPRODUTOIMPORTACAOERP', 'NRODIASADVERMAXRECBTO', 'NROBASEEXPORTACAOERP'):
                try:
                    vals.append(int(float(v.replace(',', '.'))) if v else None)
                except:
                    vals.append(None)
            elif k in ('QTDFABRICADALOTE', 'PERCACRESPRECO', 'FATORCONVERSAO', 'PROPQTDPRODUTOBASE', 'PERCALTPRECRELAC', 'PERCDIASADVERRECBTO', 'QTDLIMITEPROMOCECOMMERCE', 'PERCGASNATURAL', 'PERCACRESCCUSTORELAC', 'PERCACRESCCUSTORELACVIG', 'QTDMULTIPLOVDAECOMMERCE', 'PERSIMILIARECOMMERCE', 'ALIQADJUD', 'PROPQTDPERDAAUTO', 'PERCGASNATURALNACIONAL', 'PERCGASNATURALIMPORTADO', 'VLRPARTIDAGLP', 'TEMPIDEALMIN', 'TEMPIDEALMAX', 'PERCALIQADREM', 'PERCINDMISTBIODIESEL'):
                try:
                    vals.append(float(v.replace(',', '.')) if v else None)
                except:
                    vals.append(None)
            else:
                vals.append(v if v != '' else None)

        cols.extend(['STATUS'])
        vals.extend(['A'])

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

    print(f"[+] Sucesso! {count_imported} produtos da tabela oficial MAP_PRODUTO gravados no banco simulador com 97 colunas!")
    return True

if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else None
    sync_map_produto(caminho)
