# barras.py
# Converte ean_dun.txt -> ean_dun.parquet
# Padrão: pathlib, sep=';', encoding='utf-8-sig', saneamento de EAN/Código sem decimal
import os
import pandas as pd
from pathlib import Path

if __name__ == '__main__':
    os.chdir(Path(__file__).parent.resolve())

base_dir = Path(__file__).parent.resolve()

arquivo_txt    = base_dir / 'ean_dun.txt'
arquivo_parquet = base_dir / 'ean_dun.parquet'

# 1. Verificação de existência
if not arquivo_txt.exists():
    print(f"❌ Arquivo não encontrado: {arquivo_txt}")
    raise SystemExit(1)

print(f"📂 Lendo: {arquivo_txt}")

# 2. Ingestão respeitando o padrão Pt-BR (sep=';', encoding='utf-8-sig')
df = pd.read_csv(
    arquivo_txt,
    sep=';',
    encoding='cp1252',
    dtype=str,          # lê tudo como string para evitar imposição de tipo prematura
    low_memory=False
)

print(f"   {len(df)} registros carregados — colunas: {list(df.columns)}")

# 3. Saneamento conforme rules.md §6
#    EAN_DUN e CODIGO_PRODUTO: sem vírgula/decimal, inteiro puro como string limpa
for col in ['EAN_DUN', 'CODIGO_PRODUTO']:
    if col in df.columns:
        # Remove espaços extras, converte para numérico e descarta casas decimais
        df[col] = (
            df[col]
            .str.strip()
            .apply(lambda v: str(int(float(v))) if pd.notna(v) and v != '' else '')
        )

# Demais colunas de texto: strip simples
for col in df.select_dtypes(include=['object', 'str']).columns:
    df[col] = df[col].str.strip()

# Garante tipagem compatível com Parquet (sem object misto)
for col in df.select_dtypes(include=['object']).columns:
    df[col] = df[col].astype('string')

# 4. Exportar para Parquet
df.to_parquet(arquivo_parquet, index=False)
print(f"✅ Parquet gerado: {arquivo_parquet}")

# 5. Validação de integridade
df_check = pd.read_parquet(arquivo_parquet)
if df_check.shape == df.shape:
    print(f"✅ SUCESSO: {df_check.shape[0]} linhas × {df_check.shape[1]} colunas intactas.")
else:
    print(f"❌ ALERTA! Divergência: origem {df.shape} vs parquet {df_check.shape}")
