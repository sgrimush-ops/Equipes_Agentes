import pandas as pd
import os
import sys

def parse_br_currency(x):
    if pd.isna(x):
        return 0.0
    x = str(x).strip()
    if ',' in x and '.' in x:
        x = x.replace('.', '').replace(',', '.')
    elif ',' in x:
        x = x.replace(',', '.')
    try:
        return float(x)
    except:
        return 0.0

def load_and_clean_data(input_file):
    print("Lendo o arquivo de dados (a_pagar_empresa.txt)...")
    encodings = ['cp850', 'cp1252', 'latin1', 'utf-8']
    separators = [';', '\t', ',']
    
    df = None
    for enc in encodings:
        for sep in separators:
            try:
                temp_df = pd.read_csv(input_file, sep=sep, encoding=enc, engine='python', on_bad_lines='skip')
                if len(temp_df.columns) > 5:
                    df = temp_df
                    break
            except Exception:
                continue
        if df is not None:
            break
            
    if df is None or len(df.columns) < 5:
        print("Erro ao ler o arquivo. Verifique se o formato está correto (separado por ponto-e-vírgula ou tabulado).")
        sys.exit(1)

    # Filtrar apenas linhas com EMPRESA válida (números inteiros), ignorando quebras de linha em observações
    if 'EMPRESA' in df.columns:
        df = df[df['EMPRESA'].astype(str).str.strip().str.isdigit()].copy()
        df['EMPRESA'] = df['EMPRESA'].astype(str).str.strip()
    else:
        df['EMPRESA'] = '1'

    print(f"Total de registros válidos carregados: {len(df)}")
    print("Limpeza e tratamento de dados (removendo lógica de projeção - apenas títulos lançados)...")

    # Limpar colunas numéricas
    val_cols = ['VALOR_OPERACAO', 'VALOR_NOMINAL_TITULO', 'VALOR_PAGO_TITULO', 'SALDO_DEVEDOR_TITULO']
    for col in val_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_br_currency)
        else:
            df[col] = 0.0

    # Definir coluna principal de valor
    if 'VALOR_OPERACAO' in df.columns:
        df['VALOR'] = df['VALOR_OPERACAO']
    elif 'VALOR_PROJETADO' in df.columns:
        df['VALOR'] = df['VALOR_PROJETADO'].apply(parse_br_currency)
    else:
        df['VALOR'] = 0.0

    # Tratar datas
    if 'DATA_VENCIMENTO' in df.columns:
        df['DATA_VENCIMENTO_DT'] = pd.to_datetime(df['DATA_VENCIMENTO'], format='%d/%m/%Y', errors='coerce')
    else:
        print("Aviso: Coluna DATA_VENCIMENTO não encontrada.")
        df['DATA_VENCIMENTO_DT'] = pd.NaT

    # Preencher espécie se estiver vazia
    if 'ESPECIE' in df.columns:
        df['ESPECIE'] = df['ESPECIE'].fillna('OUTROS').astype(str).str.strip()
    else:
        df['ESPECIE'] = 'GERAL'

    # Ordenar cronologicamente
    df = df.sort_values(['DATA_VENCIMENTO_DT', 'EMPRESA']).reset_index(drop=True)
    return df

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, 'a_pagar_empresa.txt')
    output_file = os.path.join(current_dir, 'Resumo_Contas_a_Pagar_Empresa.xlsx')

    if not os.path.exists(input_file):
        print(f"Erro: O arquivo '{input_file}' não foi encontrado na pasta {current_dir}.")
        print("Execute primeiro o script 0-buscar_txt.py para trazer o arquivo da pasta import_querys.")
        sys.exit(1)

    df = load_and_clean_data(input_file)

    print("Gerando Resumos por Tipo de Título (Espécie)...")

    # 1. Visão por Data de Vencimento x Espécie (Tipo de Título)
    pivot_especie_dia = pd.pivot_table(
        df, 
        values='VALOR', 
        index='DATA_VENCIMENTO_DT', 
        columns='ESPECIE', 
        aggfunc='sum', 
        fill_value=0,
        margins=True,
        margins_name='Total Geral'
    ).reset_index()
    
    # Formata a data de volta para string limpa
    pivot_especie_dia['DATA_VENCIMENTO'] = pivot_especie_dia['DATA_VENCIMENTO_DT'].apply(
        lambda x: x.strftime('%d/%m/%Y') if hasattr(x, 'strftime') else str(x)
    )
    cols1 = ['DATA_VENCIMENTO'] + [c for c in pivot_especie_dia.columns if c not in ['DATA_VENCIMENTO', 'DATA_VENCIMENTO_DT']]
    pivot_especie_dia = pivot_especie_dia[cols1]

    # 2. Visão Consolidada por Espécie (Total Operações vs Nominal vs Saldo Devedor)
    if 'SEQ_TITULO' in df.columns:
        df_dedup = df.drop_duplicates('SEQ_TITULO')
    else:
        df_dedup = df

    tot_op = df.groupby('ESPECIE')['VALOR_OPERACAO'].sum()
    tot_nom = df_dedup.groupby('ESPECIE')['VALOR_NOMINAL_TITULO'].sum()
    tot_sald = df_dedup.groupby('ESPECIE')['SALDO_DEVEDOR_TITULO'].sum()
    qtd_op = df.groupby('ESPECIE')['VALOR_OPERACAO'].count()
    qtd_tit = df_dedup.groupby('ESPECIE')['VALOR_NOMINAL_TITULO'].count()

    resumo_especie = pd.DataFrame({
        'Qtd_Operacoes': qtd_op,
        'Qtd_Titulos_Únicos': qtd_tit,
        'Total_Valor_Operacao': tot_op,
        'Total_Nominal_Titulos': tot_nom,
        'Total_Saldo_Devedor': tot_sald
    }).reset_index().fillna(0)
    
    # Adicionando linha de Total Geral
    total_row = pd.DataFrame({
        'ESPECIE': ['Total Geral'],
        'Qtd_Operacoes': [resumo_especie['Qtd_Operacoes'].sum()],
        'Qtd_Titulos_Únicos': [resumo_especie['Qtd_Titulos_Únicos'].sum()],
        'Total_Valor_Operacao': [resumo_especie['Total_Valor_Operacao'].sum()],
        'Total_Nominal_Titulos': [resumo_especie['Total_Nominal_Titulos'].sum()],
        'Total_Saldo_Devedor': [resumo_especie['Total_Saldo_Devedor'].sum()]
    })
    resumo_especie = pd.concat([resumo_especie, total_row], ignore_index=True)

    # 3. Visão por Empresa x Espécie
    pivot_empresa_especie = pd.pivot_table(
        df,
        values='VALOR',
        index='EMPRESA',
        columns='ESPECIE',
        aggfunc='sum',
        fill_value=0,
        margins=True,
        margins_name='Total Geral'
    ).reset_index()

    # Exportando para Excel
    print(f"Salvando resultados em: {output_file}")
    try:
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.drop(columns=['DATA_VENCIMENTO_DT', 'VALOR'], errors='ignore').to_excel(writer, sheet_name='Base_Dados', index=False)
            pivot_especie_dia.to_excel(writer, sheet_name='Visao_Especie_Dia', index=False)
            resumo_especie.to_excel(writer, sheet_name='Visao_Especie_Totais', index=False)
            pivot_empresa_especie.to_excel(writer, sheet_name='Visao_Empresa_Especie', index=False)
        print("Planilha criada com sucesso!")
    except Exception as e:
        print(f"Erro ao salvar a planilha do Excel: {e}")
        print("Certifique-se de fechar a planilha se ela estiver aberta no Excel.")

if __name__ == '__main__':
    main()
