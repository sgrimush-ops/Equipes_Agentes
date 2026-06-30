import pandas as pd

# ler aquivo txt e savalr em excel
df = pd.read_csv('margem_objetiva_nivel6.txt', delimiter=';', encoding='latin1')
df = df[df['STATUS'] != 'I']
df.to_excel('margem_objetiva_nivel6.xlsx', index=False)
