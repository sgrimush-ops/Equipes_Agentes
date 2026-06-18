import pandas as pd
import os
import sys

import re

def parse_br_currency(x):
    x = str(x).strip()
    # Se contém ponto e vírgula, assume que ponto é milhar e vírgula é decimal (ex: 1.234,56)
    if ',' in x and '.' in x:
        x = x.replace('.', '').replace(',', '.')
    # Se tem só vírgula, assume que é decimal (ex: 1234,56)
    elif ',' in x:
        x = x.replace(',', '.')
    # Se não tem nenhum ou só ponto, tenta converter direto
    try:
        return float(x)
    except:
        return 0.0

def expand_installments(df):
    print("Verificando e quebrando prazos de pagamento múltiplos (ex: 30/60/90)...")
    if 'DATA_PREV_ENTREGA' in df.columns and 'DATA_EMISSAO' in df.columns:
        dt_prev = pd.to_datetime(df['DATA_PREV_ENTREGA'], format='%d/%m/%Y', errors='coerce')
        dt_emi = pd.to_datetime(df['DATA_EMISSAO'], format='%d/%m/%Y', errors='coerce')
        base_dates = dt_prev.fillna(dt_emi)
    else:
        base_dates = pd.Series(pd.NaT, index=df.index)

    new_rows = []
    df = df.reset_index(drop=True)
    base_dates = base_dates.reset_index(drop=True)
    
    split_count = 0
    for i, row in df.iterrows():
        is_projecao = str(row.get('ORIGEM', '')).startswith('2')
        prazo_str = str(row.get('PRAZO_PAGAMENTO_DIAS', '')).strip()
        
        # Verifica se é projeção e se tem separadores de parcelas
        if is_projecao and ('/' in prazo_str or ',' in prazo_str or '-' in prazo_str):
            prazos = re.findall(r'\d+', prazo_str)
            if len(prazos) > 1:
                n = len(prazos)
                val_parcela = row.get('VALOR_PROJETADO', 0) / n
                base_dt = base_dates.iloc[i]
                
                for idx, prazo in enumerate(prazos):
                    new_row = row.copy()
                    new_row['VALOR_PROJETADO'] = val_parcela
                    new_row['PARCELA'] = f"{idx + 1}/{n}"
                    
                    if pd.notnull(base_dt):
                        new_dt = base_dt + pd.Timedelta(days=int(prazo))
                        new_row['DATA_VENCIMENTO_DT'] = new_dt
                        new_row['DATA_VENCIMENTO'] = new_dt.strftime('%d/%m/%Y')
                        
                    new_rows.append(new_row)
                split_count += 1
                continue
                
        new_rows.append(row)
        
    if split_count > 0:
        print(f"-> {split_count} pedidos projetados foram divididos em múltiplas parcelas.")
    return pd.DataFrame(new_rows)

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, 'a_pagar.txt')
    output_file = os.path.join(current_dir, 'Resumo_Compras_a_Pagar.xlsx')

    if not os.path.exists(input_file):
        print(f"Erro: O arquivo '{input_file}' não foi encontrado na pasta {current_dir}.")
        print("Lembre-se de salvar o resultado da query nesse arquivo antes de rodar o script.")
        sys.exit(1)

    print("Lendo o arquivo de dados...")
    encodings = ['utf-8', 'latin1', 'cp1252', 'utf-16']
    separators = [';', '\t', ',']
    
    df = None
    for enc in encodings:
        for sep in separators:
            try:
                temp_df = pd.read_csv(input_file, sep=sep, encoding=enc)
                if len(temp_df.columns) > 5:
                    df = temp_df
                    break
            except Exception:
                continue
        if df is not None:
            break
            
    if df is None or len(df.columns) < 5:
        print("Erro ao ler o arquivo. Verifique se o formato está correto (tabulado ou ponto-e-vírgula).")
        sys.exit(1)

    print("Processando valores e datas...")
    # Limpa e converte os valores
    if 'VALOR_PROJETADO' in df.columns:
        df['VALOR_PROJETADO'] = df['VALOR_PROJETADO'].apply(parse_br_currency)

    # Converte datas
    if 'DATA_VENCIMENTO' in df.columns:
        df['DATA_VENCIMENTO_DT'] = pd.to_datetime(df['DATA_VENCIMENTO'], format='%d/%m/%Y', errors='coerce')
    else:
        print("Aviso: Coluna DATA_VENCIMENTO não encontrada.")
        df['DATA_VENCIMENTO_DT'] = pd.NaT

    # ---> EXPANDIR PARCELAS AQUI <---
    df = expand_installments(df)
    
    # Ordenar o dataframe cronologicamente usando a data possivelmente atualizada
    df = df.sort_values('DATA_VENCIMENTO_DT')

    print("Gerando Resumos...")

    # 1. Resumo por Dia e Origem (Real vs Projetado)
    pivot_origem = pd.pivot_table(
        df, 
        values='VALOR_PROJETADO', 
        index='DATA_VENCIMENTO_DT', 
        columns='ORIGEM', 
        aggfunc='sum', 
        fill_value=0,
        margins=True,
        margins_name='Total Geral'
    ).reset_index()
    
    # Formata a data de volta para string limpa
    pivot_origem['DATA_VENCIMENTO'] = pivot_origem['DATA_VENCIMENTO_DT'].apply(
        lambda x: x.strftime('%d/%m/%Y') if hasattr(x, 'strftime') else x
    )
    # Reordena colunas e remove a datetime original
    cols = ['DATA_VENCIMENTO'] + [c for c in pivot_origem.columns if c not in ['DATA_VENCIMENTO', 'DATA_VENCIMENTO_DT']]
    pivot_origem = pivot_origem[cols]

    # 2. Resumo por Dia e Comprador
    if 'COMPRADOR' in df.columns:
        pivot_comprador = pd.pivot_table(
            df, 
            values='VALOR_PROJETADO', 
            index=['DATA_VENCIMENTO_DT', 'ORIGEM'], 
            columns='COMPRADOR', 
            aggfunc='sum', 
            fill_value=0,
            margins=True,
            margins_name='Total Geral'
        ).reset_index()
        
        pivot_comprador['DATA_VENCIMENTO'] = pivot_comprador['DATA_VENCIMENTO_DT'].apply(
            lambda x: x.strftime('%d/%m/%Y') if hasattr(x, 'strftime') else x
        )
        cols2 = ['DATA_VENCIMENTO', 'ORIGEM'] + [c for c in pivot_comprador.columns if c not in ['DATA_VENCIMENTO', 'DATA_VENCIMENTO_DT', 'ORIGEM']]
        pivot_comprador = pivot_comprador[cols2]
    else:
        pivot_comprador = pd.DataFrame({'Aviso': ['Coluna COMPRADOR não encontrada']})

    # Exportando para Excel
    print(f"Salvando resultados em: {output_file}")
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.drop(columns=['DATA_VENCIMENTO_DT'], errors='ignore').to_excel(writer, sheet_name='Base_Dados', index=False)
            pivot_origem.to_excel(writer, sheet_name='Visao_Origem', index=False)
            pivot_comprador.to_excel(writer, sheet_name='Visao_Comprador', index=False)
        print("Planilha criada com sucesso!")
    except Exception as e:
        print(f"Erro ao salvar a planilha do Excel: {e}")
        print("Você precisa instalar a biblioteca openpyxl: pip install openpyxl pandas")

if __name__ == '__main__':
    main()
