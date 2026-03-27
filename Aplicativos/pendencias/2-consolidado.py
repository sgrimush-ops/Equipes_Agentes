if __name__ == '__main__':
    import os
    from pathlib import Path
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass
import pandas as pd
from pathlib import Path



def consolidar_planilhas():
    base_dir = Path(__file__).parent
    pasta_entrada = base_dir / "bd_saida"
    pasta_saida = base_dir / "bd_resultados"
    
    pasta_saida.mkdir(exist_ok=True)
    
    excel_files = list(pasta_entrada.glob("Loja *.xlsx"))
    
    if not excel_files:
        print("Nenhum arquivo Excel encontrado para consolidar.")
        return
        
    print(f"Encontrados {len(excel_files)} arquivos Excel. Iniciando consolidação...")
    
    dataframes = []
    
    for file_path in excel_files:
        print(f"Lendo {file_path.name}...")
        df = pd.read_excel(file_path, dtype={'Loja': str})
        dataframes.append(df)
        
    # Concatenar todos os dataframes
    df_consolidado = pd.concat(dataframes, ignore_index=True)
    
    # Ordenar pela coluna 'Loja' de forma sequencial
    df_consolidado = df_consolidado.sort_values(by='Loja')
    
    # Salvar em CSV na pasta de resultados
    output_file = pasta_saida / "consolidado.csv"
    
    # Salvar usando separador ponto e vírgula e encoding iso-8859-1 (padrão Brasil/Excel) ou utf-8
    df_consolidado.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')
    
    print(f"\nSucesso! Arquivo consolidado salvo com {len(df_consolidado)} registros na pasta bd_resultados.")

    print("\nExecutando a geração do Dashboard (resumo.py)...")
    import subprocess
    import sys
    script_resumo = base_dir / "3-resumo.py"
    try:
        subprocess.run([sys.executable, str(script_resumo)], check=True)
    except Exception as e:
        print(f"Ocorreu um erro ao rodar o script resumo.py: {e}")

if __name__ == "__main__":
    consolidar_planilhas()
