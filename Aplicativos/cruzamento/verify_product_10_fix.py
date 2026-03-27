import pandas as pd
import os

def verify_fix():
    file_path = "bd/gerencial_atualizado.parquet"
    if not os.path.exists(file_path):
        print("Output file not found.")
        return

    print("Reading gerencial_atualizado.parquet...")
    df = pd.read_parquet(file_path)
    
    # User said prod 10. Assuming seqloja for store 1 is '101'
    # Or search by 'Código Produto' == '10'
    
    print("Searching for 'Código Produto' == '10'...")
    # Clean if needed
    if 'Código Produto' in df.columns:
        df['Código Produto'] = df['Código Produto'].astype(str).str.strip()
        
    match = df[df['Código Produto'] == '10']
    
    if not match.empty:
        print(f"Found {len(match)} rows for Product 10.")
        cols_to_show = ['seqloja', 'Código Produto', 'CODACESSO', 'PontoPed', 'EstoqueIdeal', 'STATUSCOMPRA']
        cols = [c for c in cols_to_show if c in df.columns]
        
        print(match[cols].head(10).to_string())
        
        # Check if PontoPed is non-zero in at least one row (e.g. store 1)
        # Assuming store 1 is seqloja ending in '1' or similar logic
        # In screenshot, seqloja 101 seems to be store 1 (since code is 10)
        
        row_store_1 = match[match['seqloja'].astype(str) == '101']
        if not row_store_1.empty:
            pp = row_store_1.iloc[0].get('PontoPed', 0)
            print(f"\nStore 1 (seqloja 101) PontoPed: {pp}")
            if pp > 0:
                print("SUCCESS: Linkage working for Store 1!")
            else:
                print("FAILURE: PontoPed is still 0 for Store 1.")
        else:
             print("Store 1 (seqloja 101) not found in results.")
             
    else:
        print("Product 10 not found in output.")

if __name__ == "__main__":
    verify_fix()
