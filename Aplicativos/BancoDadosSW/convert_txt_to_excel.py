if __name__ == '__main__':
    import os
    from pathlib import Path
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass

import pandas as pd
import os
import math



try:
    # Read the text file with pandas
    # using sep=';', thousands='.', decimal=',' based on the sample output
    # Trying utf-8 first, fallback to latin1
    input_file = 'banco_de_dados_10-02.txt'
    try:
        df = pd.read_csv(input_file, sep=';', decimal=',', encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(input_file, sep=';', decimal=',', encoding='latin1')
    
    
    # Filter rows logic
    print(f"Original row count: {len(df)}")
    
    # Inspect column names to ensure exact match (sometimes spaces exist)
    # The read_csv should handle quotes if formatted correctly
    # If not, strip whitespace from column names
    df.columns = df.columns.str.strip()
    
    # Filter out rows where TpComercial is 'I'
    # Also handle leading/trailing spaces in the 'TpComercial' column values if present
    if 'TpComercial' in df.columns:
        # Convert to string to be safe and strip spaces
        df['TpComercial'] = df['TpComercial'].astype(str).str.strip()
        df = df[df['TpComercial'] != 'I']
        print(f"Row count after filtering 'I': {len(df)}")
    else:
        print("Warning: Column 'TpComercial' not found. Skipping filter.")
        # Debug: Print columns
        print(f"Columns found: {df.columns.tolist()}")

    # Calculate chunks
    rows_per_sheet = 900000  # Leave padding for safety
    total_rows = len(df)
    
    output_file = 'bdsw.xlsx'
    
    # Create Excel writer object
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        start = 0
        sheet_num = 1
        while start < total_rows:
            end = min(start + rows_per_sheet, total_rows)
            chunk = df.iloc[start:end]
            sheet_name = f'Sheet{sheet_num}'
            chunk.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"Written rows {start} to {end} to {sheet_name}")
            start += rows_per_sheet
            sheet_num += 1
            
    print(f"Successfully converted '{input_file}' to '{output_file}' with {sheet_num-1} sheets.")
    
except Exception as e:
    print(f"An error occurred: {e}")
