import pandas as pd

try:
    df = pd.read_parquet(r'C:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\consumo\consumo.parquet')
    df.to_csv('consumo_confere.csv', index=False, sep=';')
    print('Arquivo consumo_confere.csv gerado com sucesso!')
except Exception as e:
    print(f'Erro ao processar: {e}')
