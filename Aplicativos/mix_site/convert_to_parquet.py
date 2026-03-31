if __name__ == '__main__':
    import os
    from pathlib import Path
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass
import pandas as pd
import os



def convert_excel_to_parquet():
    input_file = 'con5cod.xlsx'
    output_dir = 'resultado'
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Erro: Arquivo '{input_file}' não encontrado.")
        return

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Diretório '{output_dir}' criado.")
        except OSError as e:
            print(f"Erro ao criar diretório '{output_dir}': {e}")
            return

    try:
        print(f"Lendo '{input_file}'...")
        # Read the Excel file
        df = pd.read_excel(input_file)
        
        # Define output path
        output_file = os.path.join(output_dir, 'con5cod.parquet')
        
        print(f"Salvando como Parquet em '{output_file}'...")
        # Save as Parquet
        df.to_parquet(output_file, engine='pyarrow')
        
        print("Conversão concluída com sucesso!")
        
    except Exception as e:
        print(f"Ocorreu um erro durante a conversão: {e}")

if __name__ == "__main__":
    convert_excel_to_parquet()
