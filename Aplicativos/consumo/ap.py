import pandas as pd
import os

def converter_excel_para_parquet(input_file, output_file):
    """
    Converte um arquivo Excel para format Parquet.
    
    Args:
        input_file (str): Caminho para o arquivo Excel de entrada.
        output_file (str): Caminho para o arquivo Parquet de saída.
    """
    try:
        print(f"Lendo arquivo Excel: {input_file}")
        # Ler o arquivo Excel
        df = pd.read_excel(input_file)
        
        # Garantir que os nomes das colunas sejam strings (necessário para Parquet)
        df.columns = df.columns.astype(str)
        
        # Limpeza de dados: converter 'codigo' para numérico, transformando erros em NaN
        if 'codigo' in df.columns:
            print("Realizando limpeza na coluna 'codigo'...")
            # Guardar o número de linhas antes
            rows_before = len(df)
            
            # Converter para numérico, coagindo erros (como ' ') para NaN
            df['codigo'] = pd.to_numeric(df['codigo'], errors='coerce')
            
            # Remover linhas com 'codigo' NaN (opcional, mas recomendado se o código for chave)
            df = df.dropna(subset=['codigo'])
            
            # Converter para inteiro
            df['codigo'] = df['codigo'].astype(int)
            
            rows_after = len(df)
            print(f"Linhas removidas (códigos inválidos): {rows_before - rows_after}")
        
        print(f"Convertendo para Parquet: {output_file}")
        # Salvar como Parquet
        df.to_parquet(output_file, engine='pyarrow')
        
        print("Conversão concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro durante a conversão: {e}")

if __name__ == "__main__":
    # Caminhos dos arquivos
    input_filename = "consumo.xlsx"
    output_filename = "consumo.parquet"
    
    # Obter o diretório atual do script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    input_path = os.path.join(current_dir, input_filename)
    output_path = os.path.join(current_dir, output_filename)
    
    # Verificar se o arquivo de entrada existe
    if os.path.exists(input_path):
        converter_excel_para_parquet(input_path, output_path)
    else:
        print(f"Arquivo de entrada não encontrado: {input_path}")
