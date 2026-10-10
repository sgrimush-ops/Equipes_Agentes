import os
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import warnings

warnings.filterwarnings('ignore')

input_dir = r"c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\.tratamento_dados\Rel_free"
output_file = os.path.join(input_dir, "..", "Relatorio_Consolidado_Estoque_Parado.xlsx")

# Current date: 2026-10-10 (from prompt metadata)
current_date = datetime(2026, 10, 10)
six_months_ago = current_date - relativedelta(months=6)
three_months_ago = current_date - relativedelta(months=3)

all_data = []
store_data = {}

columns = [
    "Cod. Interno", "Cod. Principal", "Mercadoria", "Cod. Fornecedor", "Marca", 
    "Estoque", "Vlr Estoque", "Custo Praticado", "Preço de Venda", "Preço Promocional", 
    "Data Última Entrada", "Data Última Venda"
]

def clean_estoque(x):
    if pd.isna(x): return 0.0
    x = str(x).strip()
    # Para o estoque, o '.' é o separador decimal (ex: 1.000 significa 1)
    x = x.replace(',', '.')
    try:
        return float(x)
    except:
        return 0.0

def clean_currency(x):
    if pd.isna(x): return 0.0
    x = str(x).strip()
    # Moedas vêm como "1.044,33", '.' é milhar e ',' é decimal
    x = x.replace('.', '').replace(',', '.')
    try:
        return float(x)
    except:
        return 0.0

for file in os.listdir(input_dir):
    if file.endswith(".csv"):
        store_name = file.replace(".csv", "")
        file_path = os.path.join(input_dir, file)
        
        # Read the csv, skipping the bad rows
        # The file is comma separated, with some quoted strings containing commas.
        import csv
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f, delimiter=',')
                rows = []
                for row in reader:
                    # check if row is a data row (first column is digit)
                    if len(row) >= 12 and str(row[0]).strip().isdigit():
                        rows.append(row[:12])
            
            if not rows:
                continue
                
            df = pd.DataFrame(rows, columns=columns)
            
            # Clean numeric columns
            df['Estoque'] = df['Estoque'].apply(clean_estoque)
            df['Vlr Estoque'] = df['Vlr Estoque'].apply(clean_currency)
            
            # Parse dates
            df['Data Última Entrada'] = pd.to_datetime(df['Data Última Entrada'], format='%d/%m/%Y', errors='coerce')
            df['Data Última Venda'] = pd.to_datetime(df['Data Última Venda'], format='%d/%m/%Y', errors='coerce')
            
            # Filter out entries in the last 6 months and sales in the last 3 months
            mask_entrada = pd.isnull(df['Data Última Entrada']) | (df['Data Última Entrada'] < six_months_ago)
            mask_venda = pd.isnull(df['Data Última Venda']) | (df['Data Última Venda'] < three_months_ago)
            
            # Filter out specific prefixes in Mercadoria ("CONS-" or "IMOB-")
            mask_desc = ~df['Mercadoria'].astype(str).str.upper().str.startswith('CONS-') & \
                        ~df['Mercadoria'].astype(str).str.upper().str.startswith('IMOB-')
            
            df_filtered = df[mask_entrada & mask_venda & mask_desc].copy()
            
            df_filtered['Loja'] = store_name
            
            store_data[store_name] = df_filtered
            all_data.append(df_filtered)
            
        except Exception as e:
            print(f"Error processing {file}: {e}")

if not all_data:
    print("Nenhum dado encontrado ou lido com sucesso.")
    exit()

df_all = pd.concat(all_data, ignore_index=True)

# Consolidado Empresa
# Agrupar por Cod. Interno, Cod. Principal, Mercadoria, Marca
consolidado = df_all.groupby(['Cod. Interno', 'Cod. Principal', 'Mercadoria', 'Marca'], dropna=False).agg({
    'Estoque': 'sum',
    'Vlr Estoque': 'sum',
    'Loja': lambda x: ', '.join(sorted(x.dropna().unique()))
}).reset_index()
consolidado.rename(columns={'Loja': 'Lojas com Estoque'}, inplace=True)
consolidado = consolidado.sort_values(by='Vlr Estoque', ascending=False)

# Ranking Marcas
ranking_marcas = df_all.groupby('Marca', dropna=False).agg({
    'Estoque': 'sum',
    'Vlr Estoque': 'sum'
}).reset_index()
ranking_marcas = ranking_marcas.sort_values(by='Vlr Estoque', ascending=False)

# Restaurar Data Última Entrada para string formatada
for k, v in store_data.items():
    v['Data Última Entrada'] = v['Data Última Entrada'].dt.strftime('%d/%m/%Y')
    v['Data Última Venda'] = v['Data Última Venda'].dt.strftime('%d/%m/%Y')
    
# Save to Excel with Dashboard Formatting
with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
    workbook = writer.book
    
    # Formats for Dashboard
    header_format = workbook.add_format({
        'bold': True, 'bg_color': '#1F497D', 'font_color': 'white', 
        'border': 1, 'align': 'center', 'valign': 'vcenter'
    })
    currency_format = workbook.add_format({'num_format': 'R$ #,##0.00', 'border': 1})
    number_format = workbook.add_format({'num_format': '#,##0.000', 'border': 1})
    text_format = workbook.add_format({'border': 1})
    
    def format_worksheet(worksheet, df):
        # Write headers
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Set column widths and formats
        for i, col in enumerate(df.columns):
            max_len = max(df[col].map(lambda x: len(str(x))).max() if len(df) > 0 else 0, len(str(col))) + 2
            max_len = min(max_len, 50) # Cap at 50
            if 'Vlr' in col or 'Custo' in col or 'Preço' in col:
                worksheet.set_column(i, i, max_len, currency_format)
            elif 'Estoque' in col:
                worksheet.set_column(i, i, max_len, number_format)
            else:
                worksheet.set_column(i, i, max_len, text_format)
                
        # Autofilter
        if len(df) > 0:
            worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)

    # 1. Consolidado
    consolidado.to_excel(writer, sheet_name='Consolidado_Empresa', index=False, header=False, startrow=1)
    worksheet_cons = writer.sheets['Consolidado_Empresa']
    format_worksheet(worksheet_cons, consolidado)
    worksheet_cons.freeze_panes(1, 0)
    
    # 2. Ranking Marcas
    ranking_marcas.to_excel(writer, sheet_name='Ranking_Marcas', index=False, header=False, startrow=1)
    worksheet_rank = writer.sheets['Ranking_Marcas']
    format_worksheet(worksheet_rank, ranking_marcas)
    worksheet_rank.freeze_panes(1, 0)
    
    # Add a chart to Ranking Marcas
    chart = workbook.add_chart({'type': 'column'})
    max_chart_rows = min(10, len(ranking_marcas))
    if max_chart_rows > 0:
        chart.add_series({
            'name': 'Valor em Estoque Parado',
            'categories': ['Ranking_Marcas', 1, 0, max_chart_rows, 0],
            'values':     ['Ranking_Marcas', 1, 2, max_chart_rows, 2],
            'fill':       {'color': '#C0504D'},
        })
        chart.set_title({'name': 'Top 10 Marcas com Estoque Parado (R$)'})
        chart.set_x_axis({'name': 'Marcas'})
        chart.set_y_axis({'name': 'Valor (R$)'})
        chart.set_style(11)
        chart.set_size({'width': 700, 'height': 400})
        worksheet_rank.insert_chart('E2', chart)
    
    # 3. Cada loja
    for store_name, df_store in store_data.items():
        df_store_out = df_store.drop(columns=['Loja'])
        df_store_out.to_excel(writer, sheet_name=store_name, index=False, header=False, startrow=1)
        worksheet_store = writer.sheets[store_name]
        format_worksheet(worksheet_store, df_store_out)
        worksheet_store.freeze_panes(1, 0)

print(f"Relatório gerado com sucesso em: {output_file}")
