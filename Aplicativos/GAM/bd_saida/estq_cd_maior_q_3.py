#ler arquivo csv da pasta bd_saida
if __name__ == '__main__':
    import os
    from pathlib import Path
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass

import pandas as pd

# O arquivo original usa separador ponto e vírgula e enconding compatível, recomendável manter o padrão
df = pd.read_csv('digitar.csv', sep=';', encoding='utf-8-sig', decimal=',')

# Converter estq_CD para numérico de forma coerciva para evitar erro "dtype=str and int"
df['Estq_CD_cx'] = pd.to_numeric(df['Estq_CD_cx'], errors='coerce').fillna(0)

# Aplicar Saneamento Global: CODIGO_CONSINCO sem vírgula/decimal (forçar Inteiro -> String)
if 'CODIGO_CONSINCO' in df.columns:
    df['CODIGO_CONSINCO'] = pd.to_numeric(df['CODIGO_CONSINCO'], errors='coerce').fillna(0).astype(int).astype(str)

#remover linhas com valores menor que 3 da coluna Estq_CD
df = df[df['Estq_CD_cx'] >= 3]

#salvar arquivo csv na pasta bd_saida
df.to_csv('digitar.csv', index=False, sep=';', encoding='utf-8-sig', decimal=',')

# limpar tela com cls e depois msg de finalizado
os.system('cls')
print("[OK] Processo concluído!")
