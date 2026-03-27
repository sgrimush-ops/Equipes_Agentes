import pandas as pd
import os

input_file = "codido_consico.csv"
output_file = "bd/codigo_consinco.parquet"

if os.path.exists(input_file):
    print(f"Lendo {input_file}...")
    try:
        # Try reading with ; first, fallback to , if needed or check lines
        # But for now assuming ; as per other files in this project
        df = pd.read_csv(input_file, sep=';', encoding='latin1', dtype=str, low_memory=False)
        
        # Clean column names
        df.columns = df.columns.str.strip().str.replace('"', '')
        
        # Clean data
        for col in df.select_dtypes(include=['object']).columns:
             df[col] = df[col].astype(str).str.strip().str.replace('"', '')

        print(f"Salvando como {output_file}...")
        df.to_parquet(output_file, engine='pyarrow')
        print("Conversão concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro durante a conversão: {e}")
else:
    print(f"Arquivo {input_file} não encontrado.")
