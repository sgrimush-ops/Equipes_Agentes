if __name__ == '__main__':
    import os
    from pathlib import Path
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass
import pandas as pd
import os



# 1. Carregar arquivos
print("Lendo gerencial.xlsx...")
try:
    df_gerencial = pd.read_excel('gerencial.xlsx')
except Exception as e:
    print(f"Erro ao ler gerencial.xlsx: {e}")
    exit(1)

print("Lendo arquivos parquet...")
try:
    path_consinco = os.path.join('bd', 'codigo_consinco.parquet')
    path_sw = os.path.join('bd', 'banco_dados_sw.parquet')
    
    if not os.path.exists(path_consinco) or not os.path.exists(path_sw):
        print("Arquivos parquet não encontrados.")
        exit(1)
        
    df_consinco = pd.read_parquet(path_consinco)
    df_sw = pd.read_parquet(path_sw)
except Exception as e:
    print(f"Erro ao ler arquivos parquet: {e}")
    exit(1)

# 2. Criar coluna 'seqloja' no gerencial
print("Criando coluna 'seqloja' em gerencial...")

def extract_store_code(val):
    try:
        if isinstance(val, str):
            prefix = val[:3]
            return str(int(prefix))
        return ""
    except:
        return ""

# Garantir que não estamos modificando uma cópia de view se houver (boa prática)
df_gerencial = df_gerencial.copy()

df_gerencial['loja_code'] = df_gerencial['Empresa : Produto'].apply(extract_store_code)
df_gerencial['seqloja'] = df_gerencial['Código Produto'].astype(str) + df_gerencial['loja_code']

# Organizar colunas: colocar seqloja na posição H (index 7)
cols = df_gerencial.columns.tolist()
if 'loja_code' in cols:
    cols.remove('loja_code')
if 'seqloja' in cols:
    cols.remove('seqloja')

# Insert 'seqloja' at index 7 (Column H)
cols.insert(7, 'seqloja')
df_gerencial = df_gerencial[cols]

# 3. Cruzar dados
print("Cruzando com codigo_consinco (trazendo CODACESSO)...")
df_consinco['seqloja'] = df_consinco['seqloja'].astype(str)

# Trazendo CODACESSO junto com cod_conexao
# CODACESSO está em codigo_consinco
cols_consinco = ['seqloja', 'cod_conexao', 'CODACESSO']
df_merged = pd.merge(df_gerencial, df_consinco[cols_consinco], on='seqloja', how='left')

print("Cruzando com banco_dados_sw...")
df_sw['cod_conexao'] = df_sw['cod_conexao'].astype(str)
if 'cod_conexao' in df_merged.columns:
    df_merged['cod_conexao'] = df_merged['cod_conexao'].astype(str)

cols_to_bring = ['EmbSeparacao', 'CapacidadeGondola', 'PontoPed', 'EstoqueIdeal', 'ltmix', 'TpComercial']
cols_sw = ['cod_conexao'] + cols_to_bring

df_final = pd.merge(df_merged, df_sw[cols_sw], on='cod_conexao', how='left')

# 4. Organizar colunas finais
# Estrutura desejada:
# [Originais até seqloja] + [Novas do SW] + [Resto originais] + [CODACESSO no final]
# NOTA: O script anterior colocava as colunas do SW logo após 'seqloja' (posição I em diante)
# E o usuário pediu CODACESSO "no final da planilha".

final_cols_available = df_final.columns.tolist()

# Identificar grupos
# seqloja já está em 7.
# Colunas originais do gerencial (menos seqloja que foi inserida)
original_cols_gerencial = [c for c in cols if c != 'seqloja'] # cols tem seqloja inserida.
# Vamos pegar do df_gerencial original (sem seqloja)
cols_before_seqloja = cols[:7]
cols_after_seqloja = cols[8:] # index 7 é seqloja

# Colunas do SW
sw_cols = [c for c in cols_to_bring if c in final_cols_available]

# Coluna CODACESSO
codacesso_col = ['CODACESSO'] if 'CODACESSO' in final_cols_available else []

# Montagem:
# 1. Antes de seqloja
# 2. seqloja
# 3. Colunas SW (I, J, K...)
# 4. Colunas originais depois de seqloja (se houver, ex: Quantidade Disponível estava em H?)
#    Espera, se inserimos seqloja em H (7), o que estava em H vai para I.
#    O usuário pediu SW "a partir da coluna I".
#    Então: [0..6] (A..G) + [seqloja] (H) + [SW Cols] (I..) + [Resto Originais] + [CODACESSO]

ordered_cols = cols_before_seqloja + ['seqloja'] + sw_cols + cols_after_seqloja + codacesso_col

# Filtrar duplicatas ou colunas inexistentes (segurança)
ordered_cols = [c for c in ordered_cols if c in final_cols_available]

df_final = df_final[ordered_cols]

print("Salvando gerencial_atualizado.xlsx...")
df_final.to_excel('gerencial_atualizado.xlsx', index=False)
print("Concluído.")
