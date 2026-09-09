import re

path = r'c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\gerenciamento_sql\querys\confronto_compras_vs_incineracao_perdas.sql'
with open(path, 'r', encoding='utf-8') as f:
    sql = f.read()

binds = sorted(list(set(re.findall(r':[A-Za-z0-9_]+', sql))))
print('Binds:', binds)
macros = sorted(list(set(re.findall(r'#[A-Za-z0-9_]+', sql))))
print('Macros:', macros)

lines = sql.splitlines()
comment_warnings = []
for i, line in enumerate(lines, 1):
    clean = re.sub(r'/\*\+\s*MATERIALIZE\s*\*/', '', line)
    clean = re.sub(r"'[^']*'", "''", clean)
    if '--' in clean or '/*' in clean:
        comment_warnings.append((i, line))

print('Comments outside strings:', len(comment_warnings))
for w in comment_warnings:
    print(w)

open_p = sql.count('(')
close_p = sql.count(')')
print(f'Open parens: {open_p}, Close parens: {close_p}, Balanced: {open_p == close_p}')
