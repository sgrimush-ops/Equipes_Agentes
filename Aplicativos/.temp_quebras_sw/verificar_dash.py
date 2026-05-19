import json
from pathlib import Path

html = Path(r'c:\Users\Alessandro.soares.BAKLIZI\Downloads\Equipes_Agentes\Aplicativos\ruptura\dashboard_comprador.html').read_text(encoding='utf-8-sig')
start = html.find('const masterData = ') + len('const masterData = ')
end = html.find(';', start)
data = json.loads(html[start:end])

# JOAO BATISTA na visão TODAS
jb_todas = [d for d in data if d['LOJA'] == 'TODAS' and d['COMPRADOR'] == 'JOAO BATISTA']
if jb_todas:
    jb = jb_todas[0]
    print('=== JOAO BATISTA (TODAS) ===')
    for k in ['Base_CD', 'Ruptura_CD', '% Ruptura CD', 'Base_Loja', 'Ruptura_Loja', '% Ruptura Loja', 'Rup_Loja_Neg', '% Rup. Loja Neg.']:
        v = jb[k]
        if isinstance(v, float):
            print(f'  {k:25s} = {v:.2f}')
        else:
            print(f'  {k:25s} = {v}')

# TOTAL GERAL na visão TODAS
total_todas = [d for d in data if d['LOJA'] == 'TODAS' and d['COMPRADOR'] == 'TOTAL GERAL']
if total_todas:
    t = total_todas[0]
    print()
    print('=== TOTAL GERAL (TODAS) ===')
    for k in ['Base_CD', 'Ruptura_CD', '% Ruptura CD', 'Base_Loja', 'Ruptura_Loja', '% Ruptura Loja', 'Rup_Loja_Neg', '% Rup. Loja Neg.']:
        v = t[k]
        if isinstance(v, float):
            print(f'  {k:25s} = {v:.2f}')
        else:
            print(f'  {k:25s} = {v}')

# Comparar com dashboard_loja para JOAO BATISTA
html2 = Path(r'c:\Users\Alessandro.soares.BAKLIZI\Downloads\Equipes_Agentes\Aplicativos\ruptura\dashboard_loja.html').read_text(encoding='utf-8-sig')
start2 = html2.find('const masterData = ') + len('const masterData = ')
end2 = html2.find(';', start2)
data2 = json.loads(html2[start2:end2])

jb_loja = [d for d in data2 if d['COMPRADOR_FILTER'] == 'JOAO BATISTA' and d['LOJA'] == 'TOTAL GERAL']
if jb_loja:
    jbl = jb_loja[0]
    print()
    print('=== JOAO BATISTA - Dashboard Lojas (TOTAL GERAL) ===')
    for k in ['Base_Loja', 'Ruptura_Loja', '% Ruptura Loja', 'Rup_Loja_Neg', '% Rup. Loja Neg.']:
        v = jbl[k]
        if isinstance(v, float):
            print(f'  {k:25s} = {v:.2f}')
        else:
            print(f'  {k:25s} = {v}')
