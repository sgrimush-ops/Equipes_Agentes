import pandas as pd

print("Lendo o primeiro arquivo: margem_objetiva_nivel6.xlsx...")
df1 = pd.read_excel('margem_objetiva_nivel6.xlsx')

print("Lendo o segundo arquivo: vendade30-04a29-06.xlsx...")
df2 = pd.read_excel('vendade30-04a29-06.xlsx')

# Garantir que a coluna chave no df1 seja limpa (sem casas decimais perdidas e sem espaços)
df1['CODIGO_PRODUTO'] = df1['CODIGO_PRODUTO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

# Renomear a coluna problemática (com caracteres estranhos "Cdigo Produto") para cruzar com facilidade
col_codigo = df2.columns[0] # A primeira coluna é a do Código
df2 = df2.rename(columns={col_codigo: 'CODIGO_PRODUTO'})
# Limpar também a chave do df2 para garantir o match perfeito
df2['CODIGO_PRODUTO'] = df2['CODIGO_PRODUTO'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()

# Pegar as colunas da C até a R do segundo arquivo (índices de 2 até 17) e a coluna chave
colunas_c_a_r = list(df2.columns[2:18])
colunas_necessarias = ['CODIGO_PRODUTO'] + colunas_c_a_r

df2_recorte = df2[colunas_necessarias]

print("Realizando o cruzamento (Left Join / PROCX)...")
# O how='left' garante que os itens da primeira planilha que não existem na segunda ficarão em branco (NaN)
df_final = pd.merge(df1, df2_recorte, on='CODIGO_PRODUTO', how='left')

# Salvar o resultado
nome_saida = 'cruzamento_final_margens_vendas.xlsx'
print(f"Salvando resultado em: {nome_saida}...")
df_final.to_excel(nome_saida, index=False)

print("Processo concluído com sucesso!")
