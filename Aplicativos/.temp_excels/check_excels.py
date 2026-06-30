import pandas as pd
import sys

def inspect():
    fusao = pd.read_excel('fusao.xlsx', nrows=5)
    classificador = pd.read_excel('classificador.xlsx')
    print("Fusao columns:", fusao.columns.tolist())
    print("Classificador columns:", classificador.columns.tolist())
    print("\nClassificador sample:")
    print(classificador.head())

if __name__ == "__main__":
    inspect()
