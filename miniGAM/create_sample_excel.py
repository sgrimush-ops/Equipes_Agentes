import os
import pandas as pd

def gerar_planilha():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "conferencia.csv")
    xlsx_path = os.path.join(base_dir, "conferencia.xlsx")

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, sep=';', engine='python')
    else:
        dados = [
            {"Titulo": "9-700/1", "Valor": "37,44", "Observacao": "Devolucao Aprovada"},
            {"Titulo": "15-700/1", "Valor": "138,24", "Observacao": "Devolucao Aprovada"},
            {"Titulo": "25-700/1", "Valor": "8,25", "Observacao": "Conferido Loja"},
            {"Titulo": "30-700/1", "Valor": "69,12", "Observacao": "Conferido Loja"},
            {"Titulo": "35-700/1", "Valor": "5,99", "Observacao": "Ajuste Pequeno"},
            {"Titulo": "55-700/1", "Valor": "5,76", "Observacao": "Ajuste Pequeno"},
            {"Titulo": "78-700/1", "Valor": "69,12", "Observacao": "Conferido"},
            {"Titulo": "21-700/1", "Valor": "25,92", "Observacao": "Conferido"},
            {"Titulo": "24-700/1", "Valor": "136,96", "Observacao": "Aprovado"},
            {"Titulo": "54-700/1", "Valor": "53,71", "Observacao": "Aprovado"},
            {"Titulo": "75-700/1", "Valor": "109,97", "Observacao": "Aprovado"},
            {"Titulo": "51-700/1", "Valor": "34,56", "Observacao": "Aprovado"}
        ]
        df = pd.DataFrame(dados)

    df.to_excel(xlsx_path, index=False)
    print(f"[OK] Arquivo {xlsx_path} gerado com sucesso!")

if __name__ == "__main__":
    gerar_planilha()
