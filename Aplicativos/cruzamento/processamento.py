if __name__ == '__main__':
    import os
    from pathlib import Path
    try:
        os.chdir(Path(__file__).parent.resolve())
    except NameError:
        pass
import pandas as pd
import os



def extract_store_code(val):
    try:
        if isinstance(val, str):
            prefix = val[:3]
            return str(int(prefix))
        return ""
    except:
        return ""

def atualizar_gerencial():
    """
    Atualiza o arquivo gerencial.xlsx com dados dos arquivos parquet.
    Retorna uma tupla (sucesso: bool, mensagem: str)
    """
    print("Iniciando atualização do gerencial...")
    
    # 1. Carregar arquivos
    try:
        if not os.path.exists('gerencial.xlsx'):
            return False, "Arquivo gerencial.xlsx não encontrado."
            
        df_gerencial = pd.read_excel('gerencial.xlsx')
    except Exception as e:
        return False, f"Erro ao ler gerencial.xlsx: {e}"

    try:
        path_consinco = os.path.join('bd', 'codigo_consinco.parquet')
        path_sw = os.path.join('bd', 'banco_dados_sw.parquet')
        
        if not os.path.exists(path_consinco) or not os.path.exists(path_sw):
            return False, "Arquivos parquet não encontrados na pasta 'bd'."
            
        df_consinco = pd.read_parquet(path_consinco)
        df_sw = pd.read_parquet(path_sw)

        # Normalizar cod_conexao no Consinco (remover zeros à esquerda)
        try:
             # Converter para numeric coercing errors
             df_consinco['cod_acesso_clean'] = pd.to_numeric(df_consinco['CODACESSO'], errors='coerce').fillna(0).astype(int).astype(str)
             df_consinco['nro_empresa_clean'] = pd.to_numeric(df_consinco['NROEMPRESA'], errors='coerce').fillna(0).astype(int).astype(str)
             
             # Recriar cod_conexao com hífen
             df_consinco['cod_conexao'] = df_consinco['cod_acesso_clean'] + '-' + df_consinco['nro_empresa_clean']
             
             # Recriar seqloja com hífen (SEQPRODUTO + '-' + NROEMPRESA)
             df_consinco['seq_clean'] = pd.to_numeric(df_consinco['SEQPRODUTO'], errors='coerce').fillna(0).astype(int).astype(str)
             df_consinco['seqloja'] = df_consinco['seq_clean'] + '-' + df_consinco['nro_empresa_clean']

             # Limpar colunas temporárias
             df_consinco.drop(columns=['cod_acesso_clean', 'nro_empresa_clean', 'seq_clean'], inplace=True)
             
        except Exception as e:
             print(f"Aviso: Erro ao regenerar cod_conexao no Consinco: {e}")

        # Padronizar cod_conexao no SW (remover zeros à esquerda)
        # CODIGOINT e LOJA para int, depois str, depois concatena
        try:
             # Converter para numeric coercing errors
             df_sw['cod_int_clean'] = pd.to_numeric(df_sw['CODIGOINT'], errors='coerce').fillna(0).astype(int).astype(str)
             df_sw['loja_clean'] = pd.to_numeric(df_sw['LOJA'], errors='coerce').fillna(0).astype(int).astype(str)
             
             # Recriar cod_conexao com hífen
             df_sw['cod_conexao'] = df_sw['cod_int_clean'] + '-' + df_sw['loja_clean']

             # Limpar colunas temporárias
             df_sw.drop(columns=['cod_int_clean', 'loja_clean'], inplace=True)
             
        except Exception as e:
             print(f"Aviso: Erro ao regenerar cod_conexao no SW: {e}")
            
    except Exception as e:
        return False, f"Erro ao ler arquivos parquet: {e}"

    try:
        # 2. Criar coluna 'seqloja' no gerencial
        # Garantir cópia para não afetar referência original
        df_gerencial = df_gerencial.copy()
        # Create original_index to preserve order
        df_gerencial['original_index'] = range(len(df_gerencial))

        df_gerencial['loja_code'] = df_gerencial['Empresa : Produto'].apply(extract_store_code)
        # Adicionando hífen no seqloja
        df_gerencial['Codigo_Produto_Clean'] = pd.to_numeric(df_gerencial['Código Produto'], errors='coerce').fillna(0).astype(int).astype(str)
        df_gerencial['seqloja'] = df_gerencial['Codigo_Produto_Clean'] + '-' + df_gerencial['loja_code']
        
        # Drop temporary column
        df_gerencial.drop(columns=['Codigo_Produto_Clean'], inplace=True)

        # Organizar colunas: colocar seqloja na posição H (index 7)
        cols = df_gerencial.columns.tolist()
        if 'loja_code' in cols:
            cols.remove('loja_code')
        if 'seqloja' in cols:
            cols.remove('seqloja')

        # Insert 'seqloja' at index 7 (Column H) se for possível
        if len(cols) >= 7:
            cols.insert(7, 'seqloja')
        else:
            cols.append('seqloja') # Fallback
            
        df_gerencial = df_gerencial[cols]

        # 3. Cruzar dados
        df_consinco['seqloja'] = df_consinco['seqloja'].astype(str)

        # Trazendo CODACESSO junto com cod_conexao e STATUSCOMPRA
        # Verificar se colunas existem antes de selecionar
        cols_consinco_needed = ['seqloja', 'cod_conexao', 'CODACESSO', 'STATUSCOMPRA']
        cols_consinco_avail = [c for c in cols_consinco_needed if c in df_consinco.columns]
        
        df_merged = pd.merge(df_gerencial, df_consinco[cols_consinco_avail], on='seqloja', how='left')

        df_sw['cod_conexao'] = df_sw['cod_conexao'].astype(str)
        if 'cod_conexao' in df_merged.columns:
            # Ensure we are not merging on mixed types if cod_conexao has floats/NaNs
            df_merged['cod_conexao'] = df_merged['cod_conexao'].fillna('').astype(str).replace('nan', '')
            df_sw['cod_conexao'] = df_sw['cod_conexao'].fillna('').astype(str).replace('nan', '')


        cols_to_bring = ['EmbSeparacao', 'CapacidadeGondola', 'PontoPed', 'EstoqueIdeal', 'ltmix', 'TpComercial']
        # Adicionar cod_conexao para o merge
        cols_sw = ['cod_conexao'] + [c for c in cols_to_bring if c in df_sw.columns]

        df_final = pd.merge(df_merged, df_sw[cols_sw], on='cod_conexao', how='left')

        # 4. Organizar colunas finais
        final_cols_available = df_final.columns.tolist()

        # Separar colunas
        cols_before_seqloja = cols[:7]
        cols_after_seqloja = cols[8:] # Assumindo que seqloja está em index 7

        sw_cols = [c for c in cols_to_bring if c in final_cols_available]
        codacesso_col = ['CODACESSO'] if 'CODACESSO' in final_cols_available else []
        status_col = ['STATUSCOMPRA'] if 'STATUSCOMPRA' in final_cols_available else []

        ordered_cols = cols_before_seqloja + ['seqloja'] + sw_cols + cols_after_seqloja + codacesso_col + status_col
        ordered_cols = [c for c in ordered_cols if c in final_cols_available]

        df_final = df_final[ordered_cols]

        # Converter colunas numéricas para int (preenchendo NaN c/ 0)
        numeric_cols_candidates = [
            'EmbSeparacao', 'CapacidadeGondola', 'PontoPed', 'EstoqueIdeal', 'CODACESSO',
            'Quantidade em Estoque', 'Quantidade Reservada', 'Quantidade Disponível', 
            'Quantidade Estoque Mínimo', 'Quantidade  Estoque Máximo'
        ]
        
        for col in numeric_cols_candidates:
            if col in df_final.columns:
                try:
                    # Fill NaN with 0
                    df_final[col] = df_final[col].fillna(0)
                    # Handle string formatting (replace , with .) if it's a string
                    if df_final[col].dtype == 'object':
                         df_final[col] = df_final[col].astype(str).str.replace(',', '.')

                    # Convert to numeric (coercing errors just in case, though 0 should be fine)
                    df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)
                    # Convert to int
                    df_final[col] = df_final[col].astype(int)
                except Exception as e:
                    print(f"Aviso: Não foi possível converter a coluna '{col}' para int: {e}")

        # Filtra duplicados mantendo a linha com maior EmbSeparacao (dados válidos)
        if 'EmbSeparacao' in df_final.columns and 'original_index' in df_final.columns:
             print("Filtrando duplicados por original_index (priorizando EmbSeparacao > 0)...")
             # Sort by original_index and EmbSeparacao
             df_final = df_final.sort_values(by=['original_index', 'EmbSeparacao'], ascending=[True, False])
             # Keep first occurrence (highest EmbSeparacao for each original row)
             df_final = df_final.drop_duplicates(subset=['original_index'], keep='first')
        
        # Restore original order
        if 'original_index' in df_final.columns:
            print("Restaurando ordem original do arquivo...")
            df_final = df_final.sort_values(by='original_index')
            df_final = df_final.drop(columns=['original_index'])

        # Salvar Excel
        output_file = 'gerencial_atualizado.xlsx'
        df_final.to_excel(output_file, index=False)
        
        # Salvar Parquet
        output_parquet = os.path.join('bd', 'gerencial_atualizado.parquet')
        # Garantir conversão de tipos object para string onde necessário para evitar erro do pyarrow
        for col in df_final.select_dtypes(include=['object']).columns:
             df_final[col] = df_final[col].astype(str)
             
        df_final.to_parquet(output_parquet, index=False)
        
        return True, f"Arquivos '{output_file}' e '{output_parquet}' atualizados com sucesso!"

    except Exception as e:
        return False, f"Erro durante o processamento: {e}"

if __name__ == "__main__":
    success, msg = atualizar_gerencial()
    print(msg)
