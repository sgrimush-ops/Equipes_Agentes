import pandas as pd
import numpy as np

# We will read relatorio_gerado.csv
df = pd.read_csv('scratch/relatorio_gerado.csv', sep=';', dtype=str)

def parse_money(val):
    if pd.isna(val) or val == '':
        return 0.0
    val = str(val).replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(val)
    except:
        return 0.0

def parse_int(val):
    if pd.isna(val) or val == '':
        return 0
    try:
        return int(float(str(val).replace('.', '').replace(',', '.')))
    except:
        return 0

# Separate data and total row
data_rows = df[df['FORNECEDOR'] != 'TOTAL GERAL ->'].copy()
total_row = df[df['FORNECEDOR'] == 'TOTAL GERAL ->'].copy()

print(f"Total data rows: {len(data_rows)}")
print(f"Total rows in total_row: {len(total_row)}")

# Parse monetary columns
money_cols = ['VALOR_ACORDO', 'VLR_EM_ABERTO', 'VLR_FIN_VENCIDO', 'VLR_JA_QUITADO', 'VALOR_SALDO_ACORDO', 'VALOR_UTILIZADO_PRODUTO']
for c in money_cols:
    data_rows[c + '_num'] = data_rows[c].apply(parse_money)

parcel_cols = ['TOTAL_PARCELAS', 'PARCELAS_PAGAS', 'PARCELAS_PENDENTES']
for c in parcel_cols:
    data_rows[c + '_num'] = data_rows[c].apply(parse_int)

# Check sum of data rows vs total row
print("\n=== TOTALS COMPARISON ===")
for c in money_cols:
    sum_data = data_rows[c + '_num'].sum()
    if len(total_row) > 0:
        tot_val = parse_money(total_row[c].values[0])
        diff = sum_data - tot_val
        print(f"{c}: Sum of Rows = {sum_data:,.2f} | Total Row = {tot_val:,.2f} | Diff = {diff:,.2f}")
    else:
        print(f"{c}: Sum of Rows = {sum_data:,.2f}")

for c in parcel_cols:
    sum_data = data_rows[c + '_num'].sum()
    if len(total_row) > 0:
        tot_val = parse_int(total_row[c].values[0])
        print(f"{c}: Sum of Rows = {sum_data} | Total Row = {tot_val}")

# Mathematical check 1: VALOR_ACORDO vs (VLR_EM_ABERTO + VLR_JA_QUITADO) row by row
data_rows['SOMA_ABERTO_QUITADO'] = data_rows['VLR_EM_ABERTO_num'] + data_rows['VLR_JA_QUITADO_num']
data_rows['DIFF_ACORDO_VS_SOMA'] = (data_rows['VALOR_ACORDO_num'] - data_rows['SOMA_ABERTO_QUITADO']).round(2)

inconsistent_sum = data_rows[data_rows['DIFF_ACORDO_VS_SOMA'].abs() > 0.05]
print(f"\n=== CHECK 1: VALOR_ACORDO != VLR_EM_ABERTO + VLR_JA_QUITADO ===")
print(f"Inconsistent rows count: {len(inconsistent_sum)}")
if len(inconsistent_sum) > 0:
    for idx, row in inconsistent_sum.head(20).iterrows():
        print(f"Empresa: {row['CODIGO_EMPRESA']} | Acordo: {row['NUMERO_ACORDO']} | Fornec: {row['FORNECEDOR']} | Tipo: {row['TIPO_ACORDO']} | Prod: {row['CODIGO_PRODUTO']} | Acordo: {row['VALOR_ACORDO_num']} | Aberto: {row['VLR_EM_ABERTO_num']} | Quitado: {row['VLR_JA_QUITADO_num']} | Diff: {row['DIFF_ACORDO_VS_SOMA']}")

# Mathematical check 2: VLR_FIN_VENCIDO > VLR_EM_ABERTO
data_rows['DIFF_VENCIDO_ABERTO'] = (data_rows['VLR_FIN_VENCIDO_num'] - data_rows['VLR_EM_ABERTO_num']).round(2)
vencido_maior = data_rows[data_rows['DIFF_VENCIDO_ABERTO'] > 0.05]
print(f"\n=== CHECK 2: VLR_FIN_VENCIDO > VLR_EM_ABERTO ===")
print(f"Rows where Vencido > Aberto: {len(vencido_maior)}")
if len(vencido_maior) > 0:
    for idx, row in vencido_maior.head(20).iterrows():
        print(f"Empresa: {row['CODIGO_EMPRESA']} | Acordo: {row['NUMERO_ACORDO']} | Fornec: {row['FORNECEDOR']} | Aberto: {row['VLR_EM_ABERTO_num']} | Vencido: {row['VLR_FIN_VENCIDO_num']}")

# Check 3: VLR_EM_ABERTO > VALOR_ACORDO
aberto_maior_acordo = data_rows[data_rows['VLR_EM_ABERTO_num'] > data_rows['VALOR_ACORDO_num'] + 0.05]
print(f"\n=== CHECK 3: VLR_EM_ABERTO > VALOR_ACORDO ===")
print(f"Rows where Aberto > Acordo: {len(aberto_maior_acordo)}")
if len(aberto_maior_acordo) > 0:
    for idx, row in aberto_maior_acordo.head(20).iterrows():
        print(f"Empresa: {row['CODIGO_EMPRESA']} | Acordo: {row['NUMERO_ACORDO']} | Fornec: {row['FORNECEDOR']} | Tipo: {row['TIPO_ACORDO']} | Prod: {row['CODIGO_PRODUTO']} | Acordo: {row['VALOR_ACORDO_num']} | Aberto: {row['VLR_EM_ABERTO_num']}")

# Check 4: Check if CANCELADOS exist
cancelados = data_rows[data_rows['STATUS_ACORDO'] == 'CANCELADO']
print(f"\n=== CHECK 4: CANCELADOS ===")
print(f"Cancelados count: {len(cancelados)}")

# Check 5: Status vs Situacao Financeira distribution
print(f"\n=== SITUACAO FINANCEIRA DISTRIBUTION ===")
print(data_rows['SITUACAO_FINANCEIRA'].value_counts())

print(f"\n=== STATUS ACORDO DISTRIBUTION ===")
print(data_rows['STATUS_ACORDO'].value_counts())
