"""Script auxiliar para análise rápida dos dados de quebra."""
import os
from pathlib import Path
import pandas as pd

if __name__ == '__main__':
    os.chdir(Path(__file__).parent.resolve())

df = pd.read_excel("itens_extraidos_preenchido.xlsx", engine="openpyxl")

print("=== STATS TOTAL NOTA ===")
print(df['Total Nota'].describe())
print(f"\nTotal geral: R$ {df['Total Nota'].sum():,.2f}")

print("\n=== POR LOJA ===")
lojas = df.groupby(df.columns[3]).agg(
    Itens=('Total Nota', 'count'),
    ValorTotal=('Total Nota', 'sum')
).sort_values('ValorTotal', ascending=False)
print(lojas.to_string())

print("\n=== POR COMPRADOR ===")
comp = df.groupby('Apelido Comprador').agg(
    Itens=('Total Nota', 'count'),
    ValorTotal=('Total Nota', 'sum')
).sort_values('ValorTotal', ascending=False)
print(comp.to_string())

print("\n=== SEM COMPRADOR ===")
sem = df[df['Apelido Comprador'].isna()]
print(f"Linhas sem comprador: {len(sem):,}")
print(f"Valor sem comprador: R$ {sem['Total Nota'].sum():,.2f}")

print("\n=== NOMES DAS LOJAS ===")
print(sorted(df[df.columns[3]].dropna().unique()))
