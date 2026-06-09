import os
import sys
from pathlib import Path
import pandas as pd
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

def convert_txt_to_excel():
    print("=" * 60)
    print("  CONVERSOR DE FATURAMENTO: TXT -> EXCEL")
    print("=" * 60)

    # Definir diretórios de busca
    current_dir = Path(__file__).parent.resolve()
    querys_dir = current_dir / "querys"
    
    # Procurar pelo arquivo faturamento.txt
    txt_path = None
    possible_paths = [
        current_dir / "faturamento.txt",
        querys_dir / "faturamento.txt",
        current_dir / "consulta_faturamento.txt",
        querys_dir / "consulta_faturamento.txt"
    ]
    
    for path in possible_paths:
        if path.exists():
            txt_path = path
            break
            
    if not txt_path:
        # Procurar por qualquer arquivo .txt que contenha 'faturamento' no nome no diretório atual e querys
        all_txts = list(current_dir.glob("*.txt")) + list(querys_dir.glob("*.txt"))
        for path in all_txts:
            if 'faturamento' in path.name.lower():
                txt_path = path
                break
                
    if not txt_path:
        print("Erro: Arquivo 'faturamento.txt' não encontrado no diretório local.")
        print(f"Diretórios pesquisados:\n - {current_dir}\n - {querys_dir}")
        print("\nPor favor, salve a exportação do Consinco como 'faturamento.txt' e tente novamente.")
        sys.exit(1)

    print(f"Arquivo de origem encontrado: {txt_path.resolve()}")
    
    # Tentar ler com diferentes encodings
    df = None
    for encoding in ['utf-8-sig', 'latin-1', 'utf-8']:
        try:
            # Consinco costuma exportar com separador ';' ou tabulação. Vamos testar os dois.
            df = pd.read_csv(txt_path, sep=None, encoding=encoding, dtype=str, engine='python')
            print(f"Leitura bem-sucedida usando encoding: {encoding}")
            break
        except Exception as e:
            continue
            
    if df is None or df.empty:
        print("Erro: Não foi possível ler o arquivo. Verifique o formato do arquivo TXT.")
        sys.exit(1)

    print(f"Dados carregados: {len(df)} linhas e {len(df.columns)} colunas.")
    
    # Padronizar nomes das colunas (remover espaços, maiúsculo)
    df.columns = [str(c).strip().upper() for c in df.columns]
    print(f"Colunas identificadas: {list(df.columns)}")
    
    # Converter colunas numéricas
    col_valor = None
    col_codigo = None
    
    for col in df.columns:
        if 'VALOR' in col or 'FATURADO' in col:
            col_valor = col
        elif 'CODIGO' in col or 'FORNECEDOR' in col:
            if 'DESCRICAO' not in col:
                col_codigo = col

    # Tratar os dados
    if col_valor:
        # Limpar pontos e trocar vírgulas por pontos se necessário antes de converter para float
        df[col_valor] = df[col_valor].fillna('0')
        df[col_valor] = df[col_valor].astype(str).str.strip()
        # Se contiver R$, limpa
        df[col_valor] = df[col_valor].str.replace('R$', '', regex=False).str.strip()
        # Tratar formatação brasileira (ex: 1.250,50 -> 1250.50)
        # Se houver ponto como separador de milhar e vírgula como decimal
        has_comma = df[col_valor].str.contains(',', regex=False).any()
        has_dot = df[col_valor].str.contains('.', regex=False).any()
        
        if has_comma and has_dot:
            # Caso "1.250,50" -> remove ponto, substitui vírgula por ponto
            df[col_valor] = df[col_valor].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        elif has_comma:
            # Caso "1250,50" -> substitui vírgula por ponto
            df[col_valor] = df[col_valor].str.replace(',', '.', regex=False)
            
        df[col_valor] = pd.to_numeric(df[col_valor], errors='coerce').fillna(0.0)
        print(f"Coluna de valor '{col_valor}' convertida para numérico.")
        
    if col_codigo:
        try:
            df[col_codigo] = pd.to_numeric(df[col_codigo], errors='coerce').fillna(0).astype(int)
        except:
            pass
        print(f"Coluna de código '{col_codigo}' ajustada.")

    # Gerar nome do Excel de saída
    excel_path = current_dir / "faturamento.xlsx"
    
    # Salvar DataFrame temporário no Excel
    df.to_excel(excel_path, index=False, engine='openpyxl')
    
    # Formatação visual com openpyxl
    print("Aplicando formatação visual premium no Excel...")
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    ws.title = "Faturamento"
    
    # Habilitar linhas de grade
    ws.views.sheetView[0].showGridLines = True
    
    # Estilos de design
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=11, bold=False)
    fill_header = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid") # Azul corporativo
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    
    # Formatar cabeçalho
    for col_idx in range(1, len(df.columns) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center
        cell.border = thin_border
        
    # Formatar linhas de dados
    for row_idx in range(2, len(df) + 2):
        # Zebrada: alternar fundo branco e cinza muito claro
        fill_data = PatternFill(start_color="F9FBFD" if row_idx % 2 == 0 else "FFFFFF", 
                                end_color="F9FBFD" if row_idx % 2 == 0 else "FFFFFF", 
                                fill_type="solid")
                                
        for col_idx in range(1, len(df.columns) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = font_data
            cell.fill = fill_data
            cell.border = thin_border
            
            # Alinhamentos e formatos específicos
            col_name = df.columns[col_idx - 1]
            if col_name == col_valor:
                cell.number_format = 'R$ #,##0.00'
                cell.alignment = align_right
            elif col_name == col_codigo or 'CNPJ' in col_name or 'CPF' in col_name:
                cell.alignment = align_center
            else:
                cell.alignment = align_left

    # Adicionar linha de total no final
    if col_valor:
        total_row_idx = len(df) + 2
        # Mesclar as primeiras colunas para escrever "TOTAL GERAL"
        ws.cell(row=total_row_idx, column=1, value="TOTAL GERAL")
        ws.cell(row=total_row_idx, column=1).font = Font(name="Calibri", size=11, bold=True)
        ws.cell(row=total_row_idx, column=1).alignment = align_right
        
        # Preencher fundo da linha de total
        fill_total = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid") # Azul clarinho
        
        # Encontrar o índice da coluna de valor para colocar a fórmula do Excel
        val_col_idx = list(df.columns).index(col_valor) + 1
        col_letter = get_column_letter(val_col_idx)
        
        # Colocar a fórmula da soma
        total_cell = ws.cell(row=total_row_idx, column=val_col_idx, value=f"=SUM({col_letter}2:{col_letter}{total_row_idx - 1})")
        total_cell.font = Font(name="Calibri", size=11, bold=True)
        total_cell.number_format = 'R$ #,##0.00'
        total_cell.alignment = align_right
        
        # Aplicar bordas e preenchimento na linha de total
        double_bottom_border = Border(
            top=Side(style='thin', color='A6A6A6'),
            bottom=Side(style='double', color='000000'),
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9')
        )
        
        for col_idx in range(1, len(df.columns) + 1):
            cell = ws.cell(row=total_row_idx, column=col_idx)
            cell.fill = fill_total
            cell.border = double_bottom_border

    # Auto-ajustar largura das colunas
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            # Se for fórmula, estimar tamanho
            val_str = str(cell.value)
            if val_str.startswith('='):
                val_str = "R$ 999.999.999,99" # Tamanho médio estimado do total
            max_len = max(max_len, len(val_str))
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # Salvar alterações
    wb.save(excel_path)
    wb.close()
    
    print(f"\n[SUCESSO] Planilha Excel gerada e formatada com sucesso!")
    print(f"Local do arquivo: {excel_path.resolve()}")
    print("=" * 60)

if __name__ == "__main__":
    convert_txt_to_excel()
