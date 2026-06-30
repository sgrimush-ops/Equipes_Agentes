import pandas as pd
import numpy as np

print("Lendo a planilha sugestao.xlsx...")
df = pd.read_excel('sugestao.xlsx')

# Garantir que as colunas financeiras sejam números (para evitar concatenação de texto em vez de soma matemática)
colunas_financeiras = ['Valor Total', 'Valor Desconto', 'Custo Liquido', 'Impostos']
for col in colunas_financeiras:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# Níveis da hierarquia que precisamos calcular a média
niveis = ['DEPARTAMENTO', 'SECAO', 'GRUPO', 'SUBGRUPO', 'NIVEL5', 'NIVEL6']

for nivel in niveis:
    print(f"Calculando margem média ponderada para: {nivel}...")
    
    # Substituir strings vazias ou só com espaços por NaN de verdade para o pandas ignorar corretamente
    df[nivel] = df[nivel].replace(r'^\s*$', np.nan, regex=True)
    
    # Agrupar pelo nome da categoria neste nível e somar as métricas
    # dropna=True é essencial: não queremos calcular a média de "todos os produtos sem categoria" juntos!
    agrupado = df.groupby(nivel, dropna=True).agg({
        'Valor Total': 'sum',
        'Valor Desconto': 'sum',
        'Custo Liquido': 'sum',
        'Impostos': 'sum'
    }).reset_index()
    
    # Calcular Venda Real do grupo
    venda_real = agrupado['Valor Total'] - agrupado['Valor Desconto']
    
    # Calcular Lucro Líquido do grupo
    lucro_liq = venda_real - agrupado['Custo Liquido'] - agrupado['Impostos']
    
    # Calcular a Margem % (evitando divisão por zero)
    margem_perc = np.where(venda_real > 0, (lucro_liq / venda_real) * 100, 0)
    
    # Salvar a margem calculada
    agrupado['MARGEM_CALCULADA'] = margem_perc
    
    # Criar um dicionário (mapa) para jogar a margem de volta no arquivo original
    # Ex: 'AGUAS' -> 24.50%
    mapa_margem = dict(zip(agrupado[nivel], agrupado['MARGEM_CALCULADA']))
    
    # A segunda coluna com o mesmo nome vira '.1' no pandas
    coluna_destino = f"{nivel}.1"
    
    if coluna_destino in df.columns:
        # Puxa o valor do mapa e já arredonda para 2 casas
        df[coluna_destino] = df[nivel].map(mapa_margem).round(2)

print("Aplicando regra de preenchimento para o NIVEL6...")
# Se o NIVEL6 estiver vazio (NaN) ou zerado porque não há categoria definida, herda a margem do NIVEL5
if 'NIVEL6.1' in df.columns and 'NIVEL5.1' in df.columns:
    # Cobre tanto o caso de vir como NaN quanto de vir como 0.0
    df['NIVEL6.1'] = np.where((df['NIVEL6.1'].isna()) | (df['NIVEL6.1'] == 0), 
                              df['NIVEL5.1'], 
                              df['NIVEL6.1'])

print("Limpando nomes de colunas e salvando...")
# Renomear as colunas tirando o '.1' do final para ficar igual a sua planilha original
nova_lista_colunas = []
for c in df.columns:
    if c.endswith('.1'):
        nova_lista_colunas.append(c[:-2])
    else:
        nova_lista_colunas.append(c)

df.columns = nova_lista_colunas

nome_saida = 'sugestao_processada.xlsx'
df.to_excel(nome_saida, index=False)

print(f"Sucesso! Planilha salva como {nome_saida}")
