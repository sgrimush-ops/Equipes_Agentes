import os
import json
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_dir, "nbo.txt")
    excel_file = os.path.join(base_dir, "nbo_analise_abastecimento.xlsx")
    html_file = os.path.join(base_dir, "dashboard_nbo.html")
    
    # 1. Carregar Dados
    df = pd.read_csv(input_file, sep=';', decimal=',', encoding='utf-8')
    
    # Garantir conversões numéricas
    int_cols = [
        'COD_LOJA', 'COD_PRODUTO', 'EMB_COMPRA', 'EMB_TRANSF', 
        'ESTQ_DISP_LOJA', 'ESTQ_FISICO_LOJA', 'ESTQ_RESERVADO_LOJA',
        'ESTQ_MIN_PADRAO', 'ESTQ_MAX_PADRAO', 'ESTQ_MIN_PONTO_EXTRA',
        'ESTQ_MAX_PONTO_EXTRA', 'PONTOS_EXTRAS_ATIVOS', 'ESTQ_MIN_TOTAL',
        'ESTQ_MAX_TOTAL', 'ESTQ_DISP_TOTAL_CD', 'ESTQ_DISP_CD15',
        'ESTQ_DISP_CD16', 'ESTQ_DISP_CD50', 'VDA_30D_QTD',
        'PEND_COMPRA_FORNEC', 'PEND_EXPEDICAO_CD', 'EM_TRANSITO_CD_LOJA',
        'TOTAL_PEND_RECEBER'
    ]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            
    float_cols = ['VDA_30D_VALOR', 'MEDIA_VDA_DIA', 'DIAS_ESTOQUE_LOJA', 'DIAS_ESTOQUE_REDE', 'DIAS_COB_COM_PENDENTES']
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(float)
            
    # Garantir a coerência das somas de Padrão + Ponto Extra = Total
    df['ESTQ_MIN_TOTAL'] = df['ESTQ_MIN_PADRAO'] + df['ESTQ_MIN_PONTO_EXTRA']
    df['ESTQ_MAX_TOTAL'] = df['ESTQ_MAX_PADRAO'] + df['ESTQ_MAX_PONTO_EXTRA']
            
    # Mapeamento e Descrição da FORMA_ABASTECIMENTO
    def descrever_abastecimento(forma):
        forma_str = str(forma).strip().upper()
        if forma_str == 'M':
            return 'M - Centralizado via CD'
        elif forma_str == 'L':
            return 'L - Direto na Loja (DSD)'
        elif forma_str == 'C':
            return 'C - Cross-Docking CD'
        elif forma_str == 'T':
            return 'T - Transf. Loja-a-Loja'
        return f'{forma_str} - Outro'
        
    df['FORMA_ABASTECIMENTO_DESC'] = df['FORMA_ABASTECIMENTO'].apply(descrever_abastecimento)
    
    # Classificação Simplificada de Status
    def classificar_status(status):
        if '4 -' in str(status):
            return 'Abaixo Mín. (Saldo no CD)'
        elif '5 -' in str(status):
            return 'Abaixo Mín. (CD Zerado / Comprar)'
        elif '6 -' in str(status):
            return 'Abaixo Mín. (A Caminho / Pedido)'
        elif '8 -' in str(status):
            return 'Regular / Normal'
        elif '9 -' in str(status):
            return 'Excesso de Estoque'
        return status

    df['STATUS_SIMPLIFICADO'] = df['STATUS_RUPTURA'].apply(classificar_status)
    
    # 2. Gerar Excel Estilizado
    wb = openpyxl.Workbook()
    default_sheet = wb.active
    wb.remove(default_sheet)
    
    font_family = "Segoe UI"
    
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # Dark Slate
    header_font = Font(name=font_family, size=11, bold=True, color="FFFFFF")
    
    pe_header_fill = PatternFill(start_color="854D0E", end_color="854D0E", fill_type="solid") # Bronze/Ocre para Pontos Extras
    pe_header_font = Font(name=font_family, size=11, bold=True, color="FEF08A")
    
    abast_header_fill = PatternFill(start_color="0369A1", end_color="0369A1", fill_type="solid") # Sky Blue para Abastecimento
    abast_header_font = Font(name=font_family, size=11, bold=True, color="E0F2FE")
    
    sub_header_fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
    sub_header_font = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    
    border_thin = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    
    border_card = Border(
        left=Side(style='medium', color='CBD5E1'),
        right=Side(style='medium', color='CBD5E1'),
        top=Side(style='medium', color='CBD5E1'),
        bottom=Side(style='medium', color='CBD5E1')
    )
    
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    pe_active_fill = PatternFill(start_color="FEF9C3", end_color="FEF9C3", fill_type="solid") # Amarelo Destaque PE
    
    # Cores de Status
    fill_st4 = PatternFill(start_color="FFEDD5", end_color="FFEDD5", fill_type="solid") # Laranja Claro
    font_st4 = Font(name=font_family, size=10, bold=True, color="C2410C")
    
    fill_st5 = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid") # Vermelho Claro
    font_st5 = Font(name=font_family, size=10, bold=True, color="B91C1C")
    
    fill_st6 = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid") # Amarelo Claro
    font_st6 = Font(name=font_family, size=10, bold=True, color="B45309")
    
    fill_st8 = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid") # Verde Claro
    font_st8 = Font(name=font_family, size=10, bold=True, color="15803D")
    
    fill_st9 = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid") # Indigo/Azul Claro
    font_st9 = Font(name=font_family, size=10, bold=True, color="4338CA")
    
    # Cores de Abastecimento (M vs L)
    fill_abast_m = PatternFill(start_color="E0F2FE", end_color="E0F2FE", fill_type="solid") # Azul Suave (CD)
    font_abast_m = Font(name=font_family, size=9.5, bold=True, color="0369A1")
    
    fill_abast_l = PatternFill(start_color="F3E8FF", end_color="F3E8FF", fill_type="solid") # Roxo Suave (Direto Loja)
    font_abast_l = Font(name=font_family, size=9.5, bold=True, color="7E22CE")

    # ==========================================
    # ABA 1: RESUMO EXECUTIVO (DASHBOARD)
    # ==========================================
    ws_kpi = wb.create_sheet(title="📊 Resumo Executivo")
    ws_kpi.views.sheetView[0].showGridLines = True
    
    # Título Principal
    ws_kpi.merge_cells("B2:L2")
    ws_kpi["B2"] = "DIAGNÓSTICO EXECUTIVO DE NBO, ABASTECIMENTO (CD vs LOJA DIRETA) E PONTOS EXTRAS"
    ws_kpi["B2"].font = Font(name=font_family, size=14, bold=True, color="FFFFFF")
    ws_kpi["B2"].alignment = Alignment(horizontal="center", vertical="center")
    ws_kpi["B2"].fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    ws_kpi.row_dimensions[2].height = 36
    
    # Subtítulo
    ws_kpi.merge_cells("B3:L3")
    ws_kpi["B3"] = "Forma de Abastecimento (M = Compra CD / L = Direto Loja DSD), Mín/Máx Padrão + Ponto Extra e Cobertura"
    ws_kpi["B3"].font = Font(name=font_family, size=10, italic=True, color="E2E8F0")
    ws_kpi["B3"].alignment = Alignment(horizontal="center", vertical="center")
    ws_kpi["B3"].fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    ws_kpi.row_dimensions[3].height = 20
    
    # Cards de KPIs
    cnt_m = len(df[df['FORMA_ABASTECIMENTO'] == 'M'])
    cnt_l = len(df[df['FORMA_ABASTECIMENTO'] == 'L'])
    
    kpis = [
        {"col_start": "B", "col_end": "C", "title": "TOTAL DE ITENS", "val": len(df), "fmt": "#,##0", "color_bg": "F1F5F9", "color_txt": "0F172A"},
        {"col_start": "D", "col_end": "D", "title": "VIA CD (M)", "val": cnt_m, "fmt": "#,##0", "color_bg": "E0F2FE", "color_txt": "0369A1"},
        {"col_start": "E", "col_end": "E", "title": "DIRETO LOJA (L)", "val": cnt_l, "fmt": "#,##0", "color_bg": "F3E8FF", "color_txt": "7E22CE"},
        {"col_start": "F", "col_end": "G", "title": "FATURAMENTO 30D", "val": df['VDA_30D_VALOR'].sum(), "fmt": "R$ #,##0.00", "color_bg": "F1F5F9", "color_txt": "0F172A"},
        {"col_start": "H", "col_end": "H", "title": "ESTOQUE LOJAS", "val": df['ESTQ_FISICO_LOJA'].sum(), "fmt": "#,##0", "color_bg": "F1F5F9", "color_txt": "0F172A"},
        {"col_start": "I", "col_end": "I", "title": "PONTOS EXTRAS", "val": len(df[df['PONTOS_EXTRAS_ATIVOS'] > 0]), "fmt": "#,##0", "color_bg": "FEF9C3", "color_txt": "854D0E"},
        {"col_start": "J", "col_end": "J", "title": "SALDO CDs", "val": df['ESTQ_DISP_TOTAL_CD'].sum(), "fmt": "#,##0", "color_bg": "F1F5F9", "color_txt": "0F172A"},
        {"col_start": "K", "col_end": "K", "title": "ABAIXO MÍNIMO", "val": len(df[df['STATUS_RUPTURA'].str.contains('ABAIXO', na=False)]), "fmt": "#,##0", "color_bg": "FEE2E2", "color_txt": "B91C1C"},
        {"col_start": "L", "col_end": "L", "title": "EXCESSO (> MÁX)", "val": len(df[df['STATUS_RUPTURA'].str.contains('EXCESSO', na=False)]), "fmt": "#,##0", "color_bg": "E0E7FF", "color_txt": "4338CA"}
    ]
    
    ws_kpi.row_dimensions[5].height = 18
    ws_kpi.row_dimensions[6].height = 28
    
    for k in kpis:
        cs = k["col_start"]
        ce = k["col_end"]
        if cs != ce:
            ws_kpi.merge_cells(f"{cs}5:{ce}5")
            ws_kpi.merge_cells(f"{cs}6:{ce}6")
        
        c_title = ws_kpi[f"{cs}5"]
        c_title.value = k["title"]
        c_title.font = Font(name=font_family, size=8, bold=True, color="64748B")
        c_title.alignment = Alignment(horizontal="center", vertical="center")
        c_title.fill = PatternFill(start_color=k["color_bg"], end_color=k["color_bg"], fill_type="solid")
        
        c_val = ws_kpi[f"{cs}6"]
        c_val.value = k["val"]
        c_val.font = Font(name=font_family, size=13, bold=True, color=k["color_txt"])
        c_val.alignment = Alignment(horizontal="center", vertical="center")
        c_val.fill = PatternFill(start_color=k["color_bg"], end_color=k["color_bg"], fill_type="solid")
        c_val.number_format = k["fmt"]
        
        cols_range = range(openpyxl.utils.column_index_from_string(cs), openpyxl.utils.column_index_from_string(ce) + 1)
        for c_idx in cols_range:
            ws_kpi.cell(row=5, column=c_idx).border = border_card
            ws_kpi.cell(row=6, column=c_idx).border = border_card

    # Tabela 1: Resumo por Status
    ws_kpi["B9"] = "1. DISTRIBUIÇÃO CONSOLIDADA POR STATUS DE ABASTECIMENTO"
    ws_kpi["B9"].font = Font(name=font_family, size=11, bold=True, color="0F172A")
    
    st_headers = ["Status de Ruptura / Estoque", "Qtd Itens", "% Total", "Venda 30D (R$)", "Estq Loja", "Mín. Padrão", "Mín. P.Extra", "Mín. Total", "Estq CDs", "Regra Operacional"]
    ws_kpi.row_dimensions[10].height = 22
    for i, h in enumerate(st_headers, start=2):
        cell = ws_kpi.cell(row=10, column=i, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center" if i > 2 and i != 11 else "left", vertical="center")
        cell.border = border_thin
        
    status_order = [
        ("4 - ABAIXO DO MINIMO (TEM SALDO NO CD / SEM PEDIDO)", "Transferir do CD para Loja (Abast. M)", fill_st4, font_st4),
        ("5 - ABAIXO DO MINIMO (CD ZERADO / SEM PEDIDO COMPRA)", "Emitir Pedido Compra (CD se M / Direto Loja se L)", fill_st5, font_st5),
        ("6 - ABAIXO DO MINIMO (COM PEDIDO/TRANSITO A CAMINHO)", "Acompanhar Chegada do Pedido / Trânsito CD", fill_st6, font_st6),
        ("8 - REGULAR / NORMAL", "Manter Monitoramento Padrão de Reposição", fill_st8, font_st8),
        ("9 - EXCESSO DE ESTOQUE (> MAXIMO)", "Pausar Compras / Remanejar / Promocionar", fill_st9, font_st9)
    ]
    
    curr_row = 11
    total_itens = len(df)
    for st_name, acao, fill_c, font_c in status_order:
        sub = df[df['STATUS_RUPTURA'] == st_name]
        qtd = len(sub)
        pct = qtd / total_itens if total_itens > 0 else 0
        vlr = sub['VDA_30D_VALOR'].sum()
        estq_l = sub['ESTQ_FISICO_LOJA'].sum()
        min_pad = sub['ESTQ_MIN_PADRAO'].sum()
        min_pe = sub['ESTQ_MIN_PONTO_EXTRA'].sum()
        min_tot = sub['ESTQ_MIN_TOTAL'].sum()
        estq_cd = sub['ESTQ_DISP_TOTAL_CD'].sum()
        
        ws_kpi.row_dimensions[curr_row].height = 20
        c1 = ws_kpi.cell(row=curr_row, column=2, value=st_name)
        c1.fill = fill_c; c1.font = font_c; c1.alignment = Alignment(horizontal="left", vertical="center"); c1.border = border_thin
        
        c2 = ws_kpi.cell(row=curr_row, column=3, value=qtd)
        c2.font = Font(name=font_family, size=10, bold=True); c2.alignment = Alignment(horizontal="right", vertical="center"); c2.border = border_thin; c2.number_format = "#,##0"
        
        c3 = ws_kpi.cell(row=curr_row, column=4, value=pct)
        c3.font = Font(name=font_family, size=10); c3.alignment = Alignment(horizontal="right", vertical="center"); c3.border = border_thin; c3.number_format = "0.0%"
        
        c4 = ws_kpi.cell(row=curr_row, column=5, value=vlr)
        c4.font = Font(name=font_family, size=10); c4.alignment = Alignment(horizontal="right", vertical="center"); c4.border = border_thin; c4.number_format = "R$ #,##0.00"
        
        c5 = ws_kpi.cell(row=curr_row, column=6, value=estq_l)
        c5.font = Font(name=font_family, size=10); c5.alignment = Alignment(horizontal="right", vertical="center"); c5.border = border_thin; c5.number_format = "#,##0"
        
        c6 = ws_kpi.cell(row=curr_row, column=7, value=min_pad)
        c6.font = Font(name=font_family, size=10); c6.alignment = Alignment(horizontal="right", vertical="center"); c6.border = border_thin; c6.number_format = "#,##0"
        
        c7 = ws_kpi.cell(row=curr_row, column=8, value=min_pe)
        c7.font = Font(name=font_family, size=10, bold=(min_pe > 0)); c7.alignment = Alignment(horizontal="right", vertical="center"); c7.border = border_thin; c7.number_format = "#,##0"
        if min_pe > 0: c7.fill = pe_active_fill
        
        c8 = ws_kpi.cell(row=curr_row, column=9, value=min_tot)
        c8.font = Font(name=font_family, size=10, bold=True); c8.alignment = Alignment(horizontal="right", vertical="center"); c8.border = border_thin; c8.number_format = "#,##0"
        
        c9 = ws_kpi.cell(row=curr_row, column=10, value=estq_cd)
        c9.font = Font(name=font_family, size=10); c9.alignment = Alignment(horizontal="right", vertical="center"); c9.border = border_thin; c9.number_format = "#,##0"
        
        c10 = ws_kpi.cell(row=curr_row, column=11, value=acao)
        c10.font = Font(name=font_family, size=9, italic=True); c10.alignment = Alignment(horizontal="left", vertical="center"); c10.border = border_thin
        
        curr_row += 1
        
    # Total Geral Tabela 1
    ws_kpi.row_dimensions[curr_row].height = 22
    tot_cells = [
        (2, "TOTAL GERAL", Alignment(horizontal="left", vertical="center")),
        (3, f"=SUM(C11:C{curr_row-1})", Alignment(horizontal="right", vertical="center"), "#,##0"),
        (4, f"=SUM(D11:D{curr_row-1})", Alignment(horizontal="right", vertical="center"), "0.0%"),
        (5, f"=SUM(E11:E{curr_row-1})", Alignment(horizontal="right", vertical="center"), "R$ #,##0.00"),
        (6, f"=SUM(F11:F{curr_row-1})", Alignment(horizontal="right", vertical="center"), "#,##0"),
        (7, f"=SUM(G11:G{curr_row-1})", Alignment(horizontal="right", vertical="center"), "#,##0"),
        (8, f"=SUM(H11:H{curr_row-1})", Alignment(horizontal="right", vertical="center"), "#,##0"),
        (9, f"=SUM(I11:I{curr_row-1})", Alignment(horizontal="right", vertical="center"), "#,##0"),
        (10, f"=SUM(J11:J{curr_row-1})", Alignment(horizontal="right", vertical="center"), "#,##0"),
        (11, "-", Alignment(horizontal="center", vertical="center"))
    ]
    for item in tot_cells:
        c = ws_kpi.cell(row=curr_row, column=item[0], value=item[1])
        c.fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
        c.font = Font(name=font_family, size=10, bold=True, color="0F172A")
        c.alignment = item[2]
        c.border = border_thin
        if len(item) > 3: c.number_format = item[3]

    # Tabela 2: Comparativo Forma de Abastecimento (M vs L)
    curr_row += 3
    ws_kpi.cell(row=curr_row, column=2, value="2. CANAL DE SUPRIMENTO: M (VIA CD) vs L (DIRETO LOJA)").font = Font(name=font_family, size=11, bold=True, color="0369A1")
    
    abast_headers = ["Forma de Abastecimento", "Significado Operacional", "Qtd SKUs", "% Sortimento", "Venda 30D (R$)", "Estoque Loja", "Estoque CDs", "Impacto no Fluxo de Compra"]
    curr_row += 1
    ws_kpi.row_dimensions[curr_row].height = 22
    for i, h in enumerate(abast_headers, start=2):
        c = ws_kpi.cell(row=curr_row, column=i, value=h)
        c.fill = abast_header_fill; c.font = abast_header_font; c.alignment = Alignment(horizontal="center" if i in [4, 5] else "left", vertical="center"); c.border = border_thin
        
    canais = [
        ("M - Centralizado via CD", "Compra feita para os Centros de Distribuição (CD 15/50), que abastecem as lojas via transferência", 'M', fill_abast_m, font_abast_m, "Demanda monitoramento diário do saldo em CD e emissão de transferência loja."),
        ("L - Direto na Loja (DSD)", "Compra Direta: O fornecedor entrega diretamente na filial (Não passa nem utiliza estoque do CD)", 'L', fill_abast_l, font_abast_l, "Pedido emitido direto filial x fornecedor. Saldo em CD não afeta reposição.")
    ]
    
    curr_row += 1
    for canal_nome, sig_op, cod_f, f_fill, f_font, impacto in canais:
        sub_c = df[df['FORMA_ABASTECIMENTO'] == cod_f]
        qtd_c = len(sub_c)
        pct_c = qtd_c / total_itens if total_itens > 0 else 0
        vlr_c = sub_c['VDA_30D_VALOR'].sum()
        estq_l_c = sub_c['ESTQ_FISICO_LOJA'].sum()
        estq_cd_c = sub_c['ESTQ_DISP_TOTAL_CD'].sum()
        
        ws_kpi.row_dimensions[curr_row].height = 24
        c1 = ws_kpi.cell(row=curr_row, column=2, value=canal_nome)
        c1.fill = f_fill; c1.font = f_font; c1.alignment = Alignment(horizontal="left", vertical="center"); c1.border = border_thin
        
        c2 = ws_kpi.cell(row=curr_row, column=3, value=sig_op)
        c2.font = Font(name=font_family, size=9); c2.alignment = Alignment(horizontal="left", vertical="center"); c2.border = border_thin
        
        c3 = ws_kpi.cell(row=curr_row, column=4, value=qtd_c)
        c3.font = Font(name=font_family, size=10, bold=True); c3.alignment = Alignment(horizontal="right", vertical="center"); c3.border = border_thin; c3.number_format = "#,##0"
        
        c4 = ws_kpi.cell(row=curr_row, column=5, value=pct_c)
        c4.font = Font(name=font_family, size=10); c4.alignment = Alignment(horizontal="right", vertical="center"); c4.border = border_thin; c4.number_format = "0.0%"
        
        c5 = ws_kpi.cell(row=curr_row, column=6, value=vlr_c)
        c5.font = Font(name=font_family, size=10); c5.alignment = Alignment(horizontal="right", vertical="center"); c5.border = border_thin; c5.number_format = "R$ #,##0.00"
        
        c6 = ws_kpi.cell(row=curr_row, column=7, value=estq_l_c)
        c6.font = Font(name=font_family, size=10); c6.alignment = Alignment(horizontal="right", vertical="center"); c6.border = border_thin; c6.number_format = "#,##0"
        
        c7 = ws_kpi.cell(row=curr_row, column=8, value=estq_cd_c)
        c7.font = Font(name=font_family, size=10); c7.alignment = Alignment(horizontal="right", vertical="center"); c7.border = border_thin; c7.number_format = "#,##0"
        
        c8 = ws_kpi.cell(row=curr_row, column=9, value=impacto)
        c8.font = Font(name=font_family, size=9, italic=True); c8.alignment = Alignment(horizontal="left", vertical="center"); c8.border = border_thin
        
        curr_row += 1

    # Larguras na aba Executivo
    kpi_col_widths = {
        'A': 4, 'B': 24, 'C': 40, 'D': 12, 'E': 14, 'F': 18, 'G': 14, 'H': 14, 'I': 18, 'J': 14, 'K': 14, 'L': 38
    }
    for col_letter, width in kpi_col_widths.items():
        ws_kpi.column_dimensions[col_letter].width = width

    # ==========================================
    # ABA 2: BASE NBO COMPLETA E DETALHADA
    # ==========================================
    ws_base = wb.create_sheet(title="📋 Base NBO Detalhada")
    ws_base.views.sheetView[0].showGridLines = True
    ws_base.freeze_panes = "A2"
    
    cols_base = list(df.columns)
    ws_base.row_dimensions[1].height = 28
    for col_idx, col_name in enumerate(cols_base, start=1):
        c = ws_base.cell(row=1, column=col_idx, value=col_name)
        if 'PONTO_EXTRA' in col_name or col_name in ['ESTQ_MIN_TOTAL', 'ESTQ_MAX_TOTAL', 'PONTOS_EXTRAS_ATIVOS']:
            c.fill = pe_header_fill; c.font = pe_header_font
        elif 'ABASTECIMENTO' in col_name:
            c.fill = abast_header_fill; c.font = abast_header_font
        else:
            c.fill = header_fill; c.font = header_font
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = border_thin
        
    for row_idx, row in df.iterrows():
        excel_row = row_idx + 2
        ws_base.row_dimensions[excel_row].height = 20
        status_val = str(row['STATUS_RUPTURA'])
        abast_val = str(row['FORMA_ABASTECIMENTO']).strip().upper()
        tem_pe = int(row['PONTOS_EXTRAS_ATIVOS']) > 0
        
        is_zebra = (row_idx % 2 == 1)
        base_fill = pe_active_fill if tem_pe else (zebra_fill if is_zebra else white_fill)
        
        for col_idx, col_name in enumerate(cols_base, start=1):
            val = row[col_name]
            c = ws_base.cell(row=excel_row, column=col_idx, value=val)
            c.fill = base_fill
            c.font = Font(name=font_family, size=9.5)
            c.border = border_thin
            
            if col_name in ['COD_LOJA', 'COD_PRODUTO', 'EMB_COMPRA', 'EMB_TRANSF', 'FORMA_ABASTECIMENTO', 'PONTOS_EXTRAS_ATIVOS']:
                c.alignment = Alignment(horizontal="center", vertical="center")
            elif col_name in ['DESCRICAO_PRODUTO', 'DEPARTAMENTO', 'SECAO', 'COMPRADOR', 'FORNECEDOR_PRINCIPAL', 'FORMA_ABASTECIMENTO_DESC']:
                c.alignment = Alignment(horizontal="left", vertical="center")
            elif col_name in ['VDA_30D_VALOR']:
                c.alignment = Alignment(horizontal="right", vertical="center")
                c.number_format = "R$ #,##0.00"
            elif col_name in ['MEDIA_VDA_DIA', 'DIAS_ESTOQUE_LOJA', 'DIAS_ESTOQUE_REDE', 'DIAS_COB_COM_PENDENTES']:
                c.alignment = Alignment(horizontal="right", vertical="center")
                c.number_format = "#,##0.0"
            elif col_name in int_cols:
                c.alignment = Alignment(horizontal="right", vertical="center")
                c.number_format = "#,##0"
                if col_name in ['ESTQ_MIN_TOTAL', 'ESTQ_MAX_TOTAL']:
                    c.font = Font(name=font_family, size=9.5, bold=True)
            else:
                c.alignment = Alignment(horizontal="left", vertical="center")
                
            # Formatação especial de Forma de Abastecimento
            if col_name in ['FORMA_ABASTECIMENTO', 'FORMA_ABASTECIMENTO_DESC']:
                if abast_val == 'M':
                    c.fill = fill_abast_m; c.font = font_abast_m
                elif abast_val == 'L':
                    c.fill = fill_abast_l; c.font = font_abast_l
                
            # Cores na coluna de Status
            if col_name in ['STATUS_RUPTURA', 'STATUS_SIMPLIFICADO']:
                if '4 -' in status_val:
                    c.fill = fill_st4; c.font = font_st4
                elif '5 -' in status_val:
                    c.fill = fill_st5; c.font = font_st5
                elif '6 -' in status_val:
                    c.fill = fill_st6; c.font = font_st6
                elif '8 -' in status_val:
                    c.fill = fill_st8; c.font = font_st8
                elif '9 -' in status_val:
                    c.fill = fill_st9; c.font = font_st9

    for col_idx, col_name in enumerate(cols_base, start=1):
        col_letter = get_column_letter(col_idx)
        max_len = max(len(str(col_name)), max(df[col_name].astype(str).str.len().max(), 0))
        adjusted_width = min(max(max_len + 3, 10), 45)
        ws_base.column_dimensions[col_letter].width = adjusted_width
        
    ws_base.auto_filter.ref = f"A1:{get_column_letter(len(cols_base))}{len(df)+1}"

    # ==========================================
    # ABA 3: DEDICADA PONTOS EXTRAS
    # ==========================================
    ws_pe_aba = wb.create_sheet(title="📌 Pontos Extras (Detalhamento)")
    ws_pe_aba.views.sheetView[0].showGridLines = True
    ws_pe_aba.freeze_panes = "A3"
    
    ws_pe_aba.merge_cells("A1:O1")
    ws_pe_aba["A1"] = "DECOMPOSIÇÃO COMPLETA: MÍNIMO / MÁXIMO PADRÃO + PONTO EXTRA = TOTAL"
    ws_pe_aba["A1"].font = Font(name=font_family, size=13, bold=True, color="FEF08A")
    ws_pe_aba["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws_pe_aba["A1"].fill = PatternFill(start_color="854D0E", end_color="854D0E", fill_type="solid")
    ws_pe_aba.row_dimensions[1].height = 28
    
    pe_cols_view = [
        "Loja", "Cód. Produto", "Descrição do Produto", "Abastecimento", "Comprador", "Fornecedor Principal",
        "Qtd PEs", "Mín. Padrão", "Mín. Ponto Extra", "Mín. Total (=Pad+PE)", 
        "Máx. Padrão", "Máx. Ponto Extra", "Máx. Total (=Pad+PE)", "Estoque Físico Loja", "Status de Ruptura"
    ]
    ws_pe_aba.row_dimensions[2].height = 24
    for i, h in enumerate(pe_cols_view, start=1):
        c = ws_pe_aba.cell(row=2, column=i, value=h)
        c.fill = sub_header_fill; c.font = sub_header_font; c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.border = border_thin
        
    df_pe = df[df['PONTOS_EXTRAS_ATIVOS'] > 0].copy()
    for r_idx, (_, row) in enumerate(df_pe.iterrows(), start=3):
        ws_pe_aba.row_dimensions[r_idx].height = 20
        status_val = str(row['STATUS_RUPTURA'])
        abast_val = str(row['FORMA_ABASTECIMENTO']).strip().upper()
        f_st = fill_st6 if '6 -' in status_val else (fill_st8 if '8 -' in status_val else fill_st9)
        fnt_st = font_st6 if '6 -' in status_val else (font_st8 if '8 -' in status_val else font_st9)
        
        ws_pe_aba.cell(row=r_idx, column=1, value=f"Loja {row['COD_LOJA']}").alignment = Alignment(horizontal="center", vertical="center")
        ws_pe_aba.cell(row=r_idx, column=2, value=row['COD_PRODUTO']).alignment = Alignment(horizontal="center", vertical="center")
        ws_pe_aba.cell(row=r_idx, column=3, value=row['DESCRICAO_PRODUTO']).alignment = Alignment(horizontal="left", vertical="center")
        
        c_ab = ws_pe_aba.cell(row=r_idx, column=4, value=row['FORMA_ABASTECIMENTO_DESC'])
        c_ab.alignment = Alignment(horizontal="center", vertical="center")
        c_ab.fill = fill_abast_m if abast_val == 'M' else fill_abast_l
        c_ab.font = font_abast_m if abast_val == 'M' else font_abast_l
        
        ws_pe_aba.cell(row=r_idx, column=5, value=row['COMPRADOR']).alignment = Alignment(horizontal="left", vertical="center")
        ws_pe_aba.cell(row=r_idx, column=6, value=row['FORNECEDOR_PRINCIPAL']).alignment = Alignment(horizontal="left", vertical="center")
        
        c_pe = ws_pe_aba.cell(row=r_idx, column=7, value=row['PONTOS_EXTRAS_ATIVOS'])
        c_pe.alignment = Alignment(horizontal="center", vertical="center"); c_pe.fill = pe_active_fill; c_pe.font = Font(name=font_family, size=10, bold=True)
        
        # Mínimos
        ws_pe_aba.cell(row=r_idx, column=8, value=row['ESTQ_MIN_PADRAO']).number_format = "#,##0"
        c_minpe = ws_pe_aba.cell(row=r_idx, column=9, value=row['ESTQ_MIN_PONTO_EXTRA'])
        c_minpe.number_format = "#,##0"; c_minpe.fill = pe_active_fill; c_minpe.font = Font(name=font_family, size=10, bold=True)
        c_mintot = ws_pe_aba.cell(row=r_idx, column=10, value=f"=H{r_idx}+I{r_idx}")
        c_mintot.number_format = "#,##0"; c_mintot.font = Font(name=font_family, size=10, bold=True)
        
        # Máximos
        ws_pe_aba.cell(row=r_idx, column=11, value=row['ESTQ_MAX_PADRAO']).number_format = "#,##0"
        c_maxpe = ws_pe_aba.cell(row=r_idx, column=12, value=row['ESTQ_MAX_PONTO_EXTRA'])
        c_maxpe.number_format = "#,##0"; c_maxpe.fill = pe_active_fill; c_maxpe.font = Font(name=font_family, size=10, bold=True)
        c_maxtot = ws_pe_aba.cell(row=r_idx, column=13, value=f"=K{r_idx}+L{r_idx}")
        c_maxtot.number_format = "#,##0"; c_maxtot.font = Font(name=font_family, size=10, bold=True)
        
        c_est = ws_pe_aba.cell(row=r_idx, column=14, value=row['ESTQ_FISICO_LOJA'])
        c_est.number_format = "#,##0"; c_est.font = Font(name=font_family, size=10, bold=True)
        
        c_st = ws_pe_aba.cell(row=r_idx, column=15, value=status_val)
        c_st.fill = f_st; c_st.font = fnt_st
        
        for c_idx in range(1, 16):
            cell_curr = ws_pe_aba.cell(row=r_idx, column=c_idx)
            cell_curr.border = border_thin
            if c_idx in [8, 9, 10, 11, 12, 13, 14]:
                cell_curr.alignment = Alignment(horizontal="right", vertical="center")

    pe_aba_widths = [12, 14, 38, 22, 16, 36, 10, 14, 16, 20, 14, 16, 20, 18, 35]
    for idx, w in enumerate(pe_aba_widths, start=1):
        ws_pe_aba.column_dimensions[get_column_letter(idx)].width = w

    # ==========================================
    # ABA 4: MATRIZ POR LOJA
    # ==========================================
    ws_loja = wb.create_sheet(title="🏬 Análise por Loja")
    ws_loja.views.sheetView[0].showGridLines = True
    ws_loja.freeze_panes = "A3"
    
    ws_loja.merge_cells("A1:P1")
    ws_loja["A1"] = "DIAGNÓSTICO CONSOLIDADO DE ESTOQUE, ABASTECIMENTO (CD vs LOJA) E PONTOS EXTRAS POR FILIAL"
    ws_loja["A1"].font = Font(name=font_family, size=13, bold=True, color="FFFFFF")
    ws_loja["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws_loja["A1"].fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    ws_loja.row_dimensions[1].height = 28
    
    loja_headers = [
        "Loja", "Total SKUs", "Via CD (M)", "Direto Loja (L)", "PEs Ativos", "Status 4 (CD Saldo)", "Status 5 (Comprar)", "Status 6 (A Caminho)", 
        "Status 8 (Regular)", "Status 9 (Excesso)", "% Ruptura/Risco", "Mín. Padrão", "Mín. P.Extra", "Mín. Total", "Estoque Loja (Un)", "Venda 30D (R$)"
    ]
    ws_loja.row_dimensions[2].height = 24
    for i, h in enumerate(loja_headers, start=1):
        c = ws_loja.cell(row=2, column=i, value=h)
        c.fill = sub_header_fill; c.font = sub_header_font; c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True); c.border = border_thin
        
    lojas = sorted(df['COD_LOJA'].unique())
    for idx, lj in enumerate(lojas, start=3):
        sub_l = df[df['COD_LOJA'] == lj]
        tot = len(sub_l)
        l_m = len(sub_l[sub_l['FORMA_ABASTECIMENTO'] == 'M'])
        l_l = len(sub_l[sub_l['FORMA_ABASTECIMENTO'] == 'L'])
        pes = sub_l['PONTOS_EXTRAS_ATIVOS'].sum()
        s4 = len(sub_l[sub_l['STATUS_RUPTURA'].str.contains('4 -', na=False)])
        s5 = len(sub_l[sub_l['STATUS_RUPTURA'].str.contains('5 -', na=False)])
        s6 = len(sub_l[sub_l['STATUS_RUPTURA'].str.contains('6 -', na=False)])
        s8 = len(sub_l[sub_l['STATUS_RUPTURA'].str.contains('8 -', na=False)])
        s9 = len(sub_l[sub_l['STATUS_RUPTURA'].str.contains('9 -', na=False)])
        pct_rup = (s4 + s5 + s6) / tot if tot > 0 else 0
        min_pad = sub_l['ESTQ_MIN_PADRAO'].sum()
        min_pe = sub_l['ESTQ_MIN_PONTO_EXTRA'].sum()
        min_tot = sub_l['ESTQ_MIN_TOTAL'].sum()
        estq = sub_l['ESTQ_FISICO_LOJA'].sum()
        vlr = sub_l['VDA_30D_VALOR'].sum()
        
        ws_loja.row_dimensions[idx].height = 20
        is_zebra = (idx % 2 == 1)
        b_fill = zebra_fill if is_zebra else white_fill
        
        row_vals = [
            (1, f"Loja {lj}", Alignment(horizontal="center", vertical="center"), "@", Font(name=font_family, size=10, bold=True)),
            (2, tot, Alignment(horizontal="right", vertical="center"), "#,##0", None),
            (3, l_m, Alignment(horizontal="right", vertical="center"), "#,##0", font_abast_m if l_m > 0 else None, fill_abast_m if l_m > 0 else None),
            (4, l_l, Alignment(horizontal="right", vertical="center"), "#,##0", font_abast_l if l_l > 0 else None, fill_abast_l if l_l > 0 else None),
            (5, pes, Alignment(horizontal="right", vertical="center"), "#,##0", Font(name=font_family, size=10, bold=True) if pes > 0 else None, pe_active_fill if pes > 0 else None),
            (6, s4, Alignment(horizontal="right", vertical="center"), "#,##0", font_st4 if s4 > 0 else None, fill_st4 if s4 > 0 else None),
            (7, s5, Alignment(horizontal="right", vertical="center"), "#,##0", font_st5 if s5 > 0 else None, fill_st5 if s5 > 0 else None),
            (8, s6, Alignment(horizontal="right", vertical="center"), "#,##0", font_st6 if s6 > 0 else None, fill_st6 if s6 > 0 else None),
            (9, s8, Alignment(horizontal="right", vertical="center"), "#,##0", font_st8 if s8 > 0 else None, fill_st8 if s8 > 0 else None),
            (10, s9, Alignment(horizontal="right", vertical="center"), "#,##0", font_st9 if s9 > 0 else None, fill_st9 if s9 > 0 else None),
            (11, pct_rup, Alignment(horizontal="right", vertical="center"), "0.0%", None),
            (12, min_pad, Alignment(horizontal="right", vertical="center"), "#,##0", None),
            (13, min_pe, Alignment(horizontal="right", vertical="center"), "#,##0", Font(name=font_family, size=10, bold=True) if min_pe > 0 else None, pe_active_fill if min_pe > 0 else None),
            (14, min_tot, Alignment(horizontal="right", vertical="center"), "#,##0", Font(name=font_family, size=10, bold=True)),
            (15, estq, Alignment(horizontal="right", vertical="center"), "#,##0", None),
            (16, vlr, Alignment(horizontal="right", vertical="center"), "R$ #,##0.00", None)
        ]
        
        for item in row_vals:
            col_pos = item[0]
            val = item[1]
            align = item[2]
            fmt = item[3]
            fnt = item[4] if len(item) > 4 and item[4] is not None else Font(name=font_family, size=9.5)
            fll = item[5] if len(item) > 5 and item[5] is not None else b_fill
            
            c = ws_loja.cell(row=idx, column=col_pos, value=val)
            c.alignment = align
            c.number_format = fmt
            c.font = fnt
            c.fill = fll
            c.border = border_thin

    for col_idx in range(1, 17):
        ws_loja.column_dimensions[get_column_letter(col_idx)].width = 15
    ws_loja.column_dimensions['A'].width = 12
    ws_loja.column_dimensions['P'].width = 18

    # ==========================================
    # ABA 5: ITENS CRÍTICOS (AÇÃO IMEDIATA)
    # ==========================================
    ws_crit = wb.create_sheet(title="🚨 Ações Imediatas (Críticos)")
    ws_crit.views.sheetView[0].showGridLines = True
    ws_crit.freeze_panes = "A2"
    
    df_criticos = df[df['STATUS_RUPTURA'].str.contains('4 -|5 -', na=False)].copy()
    crit_cols = [
        'COD_LOJA', 'COD_PRODUTO', 'DESCRICAO_PRODUTO', 'FORMA_ABASTECIMENTO_DESC', 'COMPRADOR', 'FORNECEDOR_PRINCIPAL',
        'ESTQ_FISICO_LOJA', 'ESTQ_MIN_PADRAO', 'ESTQ_MIN_PONTO_EXTRA', 'ESTQ_MIN_TOTAL',
        'ESTQ_MAX_PADRAO', 'ESTQ_MAX_PONTO_EXTRA', 'ESTQ_MAX_TOTAL', 'ESTQ_DISP_TOTAL_CD',
        'VDA_30D_QTD', 'MEDIA_VDA_DIA', 'DIAS_ESTOQUE_LOJA', 'STATUS_RUPTURA'
    ]
    
    ws_crit.row_dimensions[1].height = 26
    for col_idx, col_name in enumerate(crit_cols, start=1):
        c = ws_crit.cell(row=1, column=col_idx, value=col_name)
        if 'PONTO_EXTRA' in col_name or 'TOTAL' in col_name:
            c.fill = pe_header_fill; c.font = pe_header_font
        elif 'ABASTECIMENTO' in col_name:
            c.fill = abast_header_fill; c.font = abast_header_font
        else:
            c.fill = header_fill; c.font = header_font
        c.alignment = Alignment(horizontal="center", vertical="center"); c.border = border_thin
        
    for row_idx, (_, row) in enumerate(df_criticos.iterrows(), start=2):
        ws_crit.row_dimensions[row_idx].height = 20
        status_val = str(row['STATUS_RUPTURA'])
        abast_val = str(row['FORMA_ABASTECIMENTO']).strip().upper()
        f_st = fill_st4 if '4 -' in status_val else fill_st5
        fnt_st = font_st4 if '4 -' in status_val else font_st5
        
        for col_idx, col_name in enumerate(crit_cols, start=1):
            val = row[col_name]
            c = ws_crit.cell(row=row_idx, column=col_idx, value=val)
            c.font = Font(name=font_family, size=9.5)
            c.border = border_thin
            c.fill = white_fill
            
            if col_name in ['COD_LOJA', 'COD_PRODUTO']:
                c.alignment = Alignment(horizontal="center", vertical="center")
            elif col_name in ['DESCRICAO_PRODUTO', 'COMPRADOR', 'FORNECEDOR_PRINCIPAL', 'FORMA_ABASTECIMENTO_DESC']:
                c.alignment = Alignment(horizontal="left", vertical="center")
            elif col_name in ['MEDIA_VDA_DIA', 'DIAS_ESTOQUE_LOJA']:
                c.alignment = Alignment(horizontal="right", vertical="center")
                c.number_format = "#,##0.0"
            elif col_name in int_cols:
                c.alignment = Alignment(horizontal="right", vertical="center")
                c.number_format = "#,##0"
                if 'TOTAL' in col_name: c.font = Font(name=font_family, size=9.5, bold=True)
                
            if col_name == 'FORMA_ABASTECIMENTO_DESC':
                c.fill = fill_abast_m if abast_val == 'M' else fill_abast_l
                c.font = font_abast_m if abast_val == 'M' else font_abast_l
                
            if col_name == 'STATUS_RUPTURA':
                c.fill = f_st; c.font = fnt_st
                
    for col_idx, col_name in enumerate(crit_cols, start=1):
        col_letter = get_column_letter(col_idx)
        max_len = max(len(str(col_name)), max(df_criticos[col_name].astype(str).str.len().max() if len(df_criticos) > 0 else 0, 0))
        ws_crit.column_dimensions[col_letter].width = min(max(max_len + 3, 10), 45)
        
    ws_crit.auto_filter.ref = f"A1:{get_column_letter(len(crit_cols))}{len(df_criticos)+1}"

    # Salvar Excel
    wb.save(excel_file)
    print(f"Excel atualizado com sucesso em: {excel_file}")
    
    # 3. Gerar Dados JSON para o Dashboard HTML
    records_json = df.to_dict(orient='records')
    
    # HTML Dashboard Ultra Premium com todos os IDs íntegros
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portal NBO - Diagnóstico de Abastecimento, CD vs Loja & Pontos Extras</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{
                        brand: {{
                            50: '#f0fdfa',
                            100: '#ccfbf1',
                            500: '#14b8a6',
                            600: '#0d9488',
                            700: '#0f766e',
                            800: '#115e59',
                            900: '#134e4a',
                        }},
                        darkbg: '#0B1120',
                        cardbg: '#1E293B',
                        cardborder: '#334155'
                    }},
                    fontFamily: {{
                        sans: ['Inter', 'Segoe UI', 'sans-serif'],
                        display: ['Outfit', 'sans-serif']
                    }}
                }}
            }}
        }}
    </script>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">
    <!-- FontAwesome Icons -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {{
            font-family: 'Inter', sans-serif;
        }}
        .font-display {{
            font-family: 'Outfit', sans-serif;
        }}
        /* Custom scrollbars */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        ::-webkit-scrollbar-track {{
            background: #0f172a;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #334155;
            border-radius: 4px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: #475569;
        }}
        .glass-panel {{
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}
        .light .glass-panel {{
            background: rgba(255, 255, 255, 0.85);
            border: 1px solid rgba(0, 0, 0, 0.08);
        }}
    </style>
</head>
<body class="bg-darkbg text-slate-100 min-h-screen transition-colors duration-200">

    <!-- Top Navigation Bar -->
    <header class="sticky top-0 z-50 glass-panel border-b border-slate-700/60 shadow-lg px-6 py-3.5">
        <div class="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div class="flex items-center space-x-4">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-teal-500/20 text-slate-950 font-bold text-xl">
                    <i class="fa-solid fa-boxes-stacked"></i>
                </div>
                <div>
                    <div class="flex items-center space-x-2">
                        <h1 class="text-xl font-bold font-display tracking-tight text-white flex items-center gap-2">
                            Portal NBO <span class="text-xs px-2.5 py-0.5 rounded-full bg-teal-500/20 text-teal-300 font-semibold border border-teal-500/30">Totvs Consinco ERP</span>
                        </h1>
                    </div>
                    <p class="text-xs text-slate-400">Abastecimento: <strong>M = Via CD</strong> vs <strong>L = Direto Loja (DSD)</strong> | Mín/Máx Padrão + Pontos Extras</p>
                </div>
            </div>

            <!-- Header Quick Actions -->
            <div class="flex items-center space-x-3">
                <span class="inline-flex items-center px-3 py-1 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
                    <i class="fa-regular fa-clock mr-1.5 text-teal-400"></i> Atualizado: <strong class="ml-1 text-white" id="lblTimestamp">Hoje</strong>
                </span>
                <button onclick="exportarCSV()" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-teal-600 hover:bg-teal-500 text-white shadow-md shadow-teal-900/30 transition flex items-center gap-1.5">
                    <i class="fa-solid fa-file-excel"></i> Exportar Dados
                </button>
                <button onclick="toggleTheme()" class="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition text-sm">
                    <i id="themeIcon" class="fa-solid fa-sun"></i>
                </button>
            </div>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 md:px-6 py-6 space-y-6">

        <!-- KPI SUMMARY CARDS (TODOS OS 8 CARDS) -->
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
            <!-- Card 1: SKUs -->
            <div class="glass-panel p-3 rounded-xl border border-slate-700/50 relative overflow-hidden group hover:border-teal-500/40 transition">
                <div class="flex items-center justify-between">
                    <span class="text-[9px] font-semibold text-slate-400 uppercase tracking-wider">Itens Analisados</span>
                    <span class="w-6 h-6 rounded-lg bg-teal-500/10 text-teal-400 flex items-center justify-center text-xs"><i class="fa-solid fa-barcode"></i></span>
                </div>
                <div class="mt-1 text-lg font-extrabold font-display text-white" id="kpi_total_skus">0</div>
                <div class="text-[9px] text-slate-400 mt-0.5"><span class="text-teal-400 font-medium" id="kpi_lojas_ativas">0 lojas</span></div>
            </div>

            <!-- Card 2: Abastecimento M vs L -->
            <div class="glass-panel p-3 rounded-xl border border-sky-500/40 bg-sky-950/10 relative overflow-hidden group hover:border-sky-500/60 transition">
                <div class="flex items-center justify-between">
                    <span class="text-[9px] font-bold text-sky-300 uppercase tracking-wider">CD vs Direto</span>
                    <span class="w-6 h-6 rounded-lg bg-sky-500/20 text-sky-300 flex items-center justify-center text-xs"><i class="fa-solid fa-truck-ramp-box"></i></span>
                </div>
                <div class="mt-1 text-sm font-extrabold font-display text-white flex items-center gap-1">
                    <span class="text-sky-400" id="kpi_abast_m">M: 0</span>
                    <span class="text-slate-500">|</span>
                    <span class="text-purple-400" id="kpi_abast_l">L: 0</span>
                </div>
                <div class="text-[9px] text-slate-400 mt-0.5" id="kpi_abast_sub">M: CD | L: DSD</div>
            </div>

            <!-- Card 3: Vendas 30D -->
            <div class="glass-panel p-3 rounded-xl border border-slate-700/50 relative overflow-hidden group hover:border-blue-500/40 transition">
                <div class="flex items-center justify-between">
                    <span class="text-[9px] font-semibold text-slate-400 uppercase tracking-wider">Venda 30D</span>
                    <span class="w-6 h-6 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center text-xs"><i class="fa-solid fa-sack-dollar"></i></span>
                </div>
                <div class="mt-1 text-lg font-extrabold font-display text-white" id="kpi_venda_30d">R$ 0</div>
                <div class="text-[9px] text-slate-400 mt-0.5" id="kpi_venda_qtd">0 un</div>
            </div>

            <!-- Card 4: Estoque Loja -->
            <div class="glass-panel p-3 rounded-xl border border-slate-700/50 relative overflow-hidden group hover:border-emerald-500/40 transition">
                <div class="flex items-center justify-between">
                    <span class="text-[9px] font-semibold text-slate-400 uppercase tracking-wider">Estoque Lojas</span>
                    <span class="w-6 h-6 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-xs"><i class="fa-solid fa-shop"></i></span>
                </div>
                <div class="mt-1 text-lg font-extrabold font-display text-white" id="kpi_estq_loja">0</div>
                <div class="text-[9px] text-slate-400 mt-0.5">Saldo gôndolas</div>
            </div>

            <!-- Card 5: Pontos Extras Ativos -->
            <div class="glass-panel p-3 rounded-xl border border-amber-500/40 bg-amber-950/10 relative overflow-hidden group hover:border-amber-500/60 transition cursor-pointer" onclick="trocarAba('aba_pontos_extras')">
                <div class="flex items-center justify-between">
                    <span class="text-[9px] font-bold text-amber-300 uppercase tracking-wider">Pontos Extras</span>
                    <span class="w-6 h-6 rounded-lg bg-amber-500/20 text-amber-300 flex items-center justify-center text-xs"><i class="fa-solid fa-thumbtack"></i></span>
                </div>
                <div class="mt-1 text-lg font-extrabold font-display text-amber-300" id="kpi_pontos_extras">0</div>
                <div class="text-[9px] text-amber-400 mt-0.5" id="kpi_pe_sub">+0 un Mín. PE</div>
            </div>

            <!-- Card 6: Saldo CDs -->
            <div class="glass-panel p-3 rounded-xl border border-slate-700/50 relative overflow-hidden group hover:border-cyan-500/40 transition">
                <div class="flex items-center justify-between">
                    <span class="text-[9px] font-semibold text-slate-400 uppercase tracking-wider">Saldo CDs</span>
                    <span class="w-6 h-6 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center text-xs"><i class="fa-solid fa-warehouse"></i></span>
                </div>
                <div class="mt-1 text-lg font-extrabold font-display text-white" id="kpi_estq_cd">0</div>
                <div class="text-[9px] text-slate-400 mt-0.5" id="kpi_cd_breakdown">CD15: 0 | CD50: 0</div>
            </div>

            <!-- Card 7: Abaixo Mínimo -->
            <div class="glass-panel p-3 rounded-xl border border-red-500/30 bg-red-950/10 relative overflow-hidden group hover:border-red-500/50 transition cursor-pointer" onclick="filtrarStatus('ABAIXO')">
                <div class="flex items-center justify-between">
                    <span class="text-[9px] font-semibold text-red-400 uppercase tracking-wider">Abaixo Mínimo</span>
                    <span class="w-6 h-6 rounded-lg bg-red-500/20 text-red-400 flex items-center justify-center text-xs animate-pulse"><i class="fa-solid fa-triangle-exclamation"></i></span>
                </div>
                <div class="mt-1 text-lg font-extrabold font-display text-red-400" id="kpi_abaixo_min">0</div>
                <div class="text-[9px] text-red-300/80 mt-0.5" id="kpi_abaixo_sub">Críticos: 0 sem ped</div>
            </div>

            <!-- Card 8: Excesso -->
            <div class="glass-panel p-3 rounded-xl border border-indigo-500/30 bg-indigo-950/10 relative overflow-hidden group hover:border-indigo-500/50 transition cursor-pointer" onclick="filtrarStatus('EXCESSO')">
                <div class="flex items-center justify-between">
                    <span class="text-[9px] font-semibold text-indigo-400 uppercase tracking-wider">Excesso (> Máx)</span>
                    <span class="w-6 h-6 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-xs"><i class="fa-solid fa-layer-group"></i></span>
                </div>
                <div class="mt-1 text-lg font-extrabold font-display text-indigo-300" id="kpi_excesso">0</div>
                <div class="text-[9px] text-indigo-300/80 mt-0.5" id="kpi_excesso_pct">0% da base</div>
            </div>
        </div>

        <!-- FILTROS DINÂMICOS INTERATIVOS (TODOS OS 6 FILTROS) -->
        <div class="glass-panel p-4 rounded-2xl border border-slate-700/60 shadow-md">
            <div class="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 flex-1">
                    <!-- Filtro Loja -->
                    <div>
                        <label class="block text-[10px] font-semibold text-slate-400 uppercase mb-1">Loja</label>
                        <select id="filtroLoja" onchange="aplicarFiltros()" class="w-full bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-teal-500">
                            <option value="">Todas as Lojas</option>
                        </select>
                    </div>

                    <!-- Filtro Forma de Abastecimento -->
                    <div>
                        <label class="block text-[10px] font-semibold text-sky-400 uppercase mb-1">Abastecimento</label>
                        <select id="filtroAbastecimento" onchange="aplicarFiltros()" class="w-full bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-sky-300 font-medium focus:outline-none focus:border-sky-500">
                            <option value="">Todos (M e L)</option>
                            <option value="M">M - Centralizado via CD</option>
                            <option value="L">L - Direto na Loja (DSD)</option>
                        </select>
                    </div>

                    <!-- Filtro Comprador -->
                    <div>
                        <label class="block text-[10px] font-semibold text-slate-400 uppercase mb-1">Comprador</label>
                        <select id="filtroComprador" onchange="aplicarFiltros()" class="w-full bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-teal-500">
                            <option value="">Todos Compradores</option>
                        </select>
                    </div>

                    <!-- Filtro Departamento -->
                    <div>
                        <label class="block text-[10px] font-semibold text-slate-400 uppercase mb-1">Departamento</label>
                        <select id="filtroDepartamento" onchange="aplicarFiltros()" class="w-full bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-teal-500">
                            <option value="">Todos Deptos</option>
                        </select>
                    </div>

                    <!-- Filtro Ponto Extra -->
                    <div>
                        <label class="block text-[10px] font-semibold text-amber-400 uppercase mb-1">Ponto Extra</label>
                        <select id="filtroPontoExtra" onchange="aplicarFiltros()" class="w-full bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-amber-300 font-medium focus:outline-none focus:border-amber-500">
                            <option value="">Todos Itens</option>
                            <option value="COM_PE">Somente c/ Ponto Extra</option>
                            <option value="SEM_PE">Sem Ponto Extra</option>
                        </select>
                    </div>

                    <!-- Filtro Status -->
                    <div>
                        <label class="block text-[10px] font-semibold text-slate-400 uppercase mb-1">Status Ruptura</label>
                        <select id="filtroStatus" onchange="aplicarFiltros()" class="w-full bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-teal-500">
                            <option value="">Todos Status</option>
                            <option value="4 -">Status 4: CD Saldo</option>
                            <option value="5 -">Status 5: Comprar Urg.</option>
                            <option value="6 -">Status 6: A Caminho</option>
                            <option value="8 -">Status 8: Regular</option>
                            <option value="9 -">Status 9: Excesso</option>
                        </select>
                    </div>
                </div>

                <!-- Botão Reset e Busca Rápida -->
                <div class="flex items-end gap-2">
                    <div class="relative w-full sm:w-56">
                        <input type="text" id="filtroBusca" oninput="aplicarFiltros()" placeholder="Buscar produto ou cód..." class="w-full bg-slate-800 border border-slate-700 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500">
                        <i class="fa-solid fa-magnifying-glass absolute left-2.5 top-2 text-xs text-slate-400"></i>
                    </div>
                    <button onclick="limparFiltros()" title="Limpar todos os filtros" class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition text-xs font-semibold">
                        <i class="fa-solid fa-rotate-left"></i>
                    </button>
                </div>
            </div>
            
            <!-- Contador de Registros Ativos -->
            <div class="mt-2.5 pt-2 border-t border-slate-700/50 flex items-center justify-between text-xs text-slate-400">
                <div id="statusFiltroInfo">Exibindo <span class="font-bold text-teal-400" id="cntFiltrados">0</span> de <span class="font-bold text-white" id="cntTotal">0</span> registros</div>
                <div class="flex items-center gap-3 text-[11px]">
                    <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-sky-400"></span> M (Via CD)</span>
                    <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-purple-400"></span> L (Direto Loja)</span>
                    <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-amber-400"></span> Ponto Extra</span>
                    <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-red-500"></span> Crítico</span>
                </div>
            </div>
        </div>

        <!-- ABAS PRINCIPAIS -->
        <div class="flex border-b border-slate-700/80 space-x-1 overflow-x-auto">
            <button onclick="trocarAba('aba_visao_geral')" id="btn_aba_visao_geral" class="tab-btn px-4 py-2.5 text-xs font-semibold border-b-2 border-teal-500 text-teal-400 flex items-center gap-2 whitespace-nowrap">
                <i class="fa-solid fa-chart-pie"></i> Visão Geral & Gráficos
            </button>
            <button onclick="trocarAba('aba_pontos_extras')" id="btn_aba_pontos_extras" class="tab-btn px-4 py-2.5 text-xs font-semibold border-b-2 border-transparent text-amber-400 hover:text-amber-300 flex items-center gap-2 whitespace-nowrap">
                <i class="fa-solid fa-thumbtack"></i> Pontos Extras (Padrão + PE = Total) (<span id="cntBadgePE" class="font-bold">0</span>)
            </button>
            <button onclick="trocarAba('aba_acoes_criticas')" id="btn_aba_acoes_criticas" class="tab-btn px-4 py-2.5 text-xs font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2 whitespace-nowrap">
                <i class="fa-solid fa-bolt text-red-400"></i> Matriz de Ação Rápida (<span id="cntBadgeCriticos" class="text-red-400 font-bold">0</span>)
            </button>
            <button onclick="trocarAba('aba_por_loja')" id="btn_aba_por_loja" class="tab-btn px-4 py-2.5 text-xs font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2 whitespace-nowrap">
                <i class="fa-solid fa-store"></i> Diagnóstico por Loja
            </button>
            <button onclick="trocarAba('aba_tabela_completa')" id="btn_aba_tabela_completa" class="tab-btn px-4 py-2.5 text-xs font-semibold border-b-2 border-transparent text-slate-400 hover:text-slate-200 flex items-center gap-2 whitespace-nowrap">
                <i class="fa-solid fa-table-list"></i> Tabela Detalhada
            </button>
        </div>

        <!-- CONTEÚDO DA ABA 1: VISÃO GERAL & GRÁFICOS -->
        <div id="aba_visao_geral" class="tab-content space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Gráfico 1: Status Donut -->
                <div class="glass-panel p-5 rounded-2xl border border-slate-700/60 shadow-md">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-sm font-bold text-white font-display flex items-center gap-2">
                            <i class="fa-solid fa-chart-pie text-teal-400"></i> Distribuição por Status de Ruptura
                        </h3>
                    </div>
                    <div class="h-64 relative flex items-center justify-center">
                        <canvas id="chartStatus"></canvas>
                    </div>
                </div>

                <!-- Gráfico 2: Diagnóstico por Loja -->
                <div class="glass-panel p-5 rounded-2xl border border-slate-700/60 shadow-md">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-sm font-bold text-white font-display flex items-center gap-2">
                            <i class="fa-solid fa-chart-column text-teal-400"></i> Ruptura e Excesso por Loja
                        </h3>
                    </div>
                    <div class="h-64 relative">
                        <canvas id="chartLojas"></canvas>
                    </div>
                </div>

                <!-- Gráfico 3: Vendas vs Estoque por Comprador -->
                <div class="glass-panel p-5 rounded-2xl border border-slate-700/60 shadow-md">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-sm font-bold text-white font-display flex items-center gap-2">
                            <i class="fa-solid fa-user-tie text-teal-400"></i> Venda 30D (R$) e Estoque por Comprador
                        </h3>
                    </div>
                    <div class="h-64 relative">
                        <canvas id="chartComprador"></canvas>
                    </div>
                </div>

                <!-- Gráfico 4: Cobertura por Departamento -->
                <div class="glass-panel p-5 rounded-2xl border border-slate-700/60 shadow-md">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-sm font-bold text-white font-display flex items-center gap-2">
                            <i class="fa-solid fa-boxes-packing text-teal-400"></i> Volume de SKUs por Departamento
                        </h3>
                    </div>
                    <div class="h-64 relative">
                        <canvas id="chartDepto"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- CONTEÚDO DA ABA 2: PONTOS EXTRAS DETALHADO -->
        <div id="aba_pontos_extras" class="tab-content hidden space-y-6">
            <div class="glass-panel p-4 rounded-2xl border border-amber-500/40 bg-amber-950/15">
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div>
                        <h3 class="text-sm font-bold text-amber-300 font-display flex items-center gap-2">
                            <i class="fa-solid fa-thumbtack text-amber-400"></i> Gestão de Pontos Extras (Ilhas & Pontas de Gôndola)
                        </h3>
                        <p class="text-xs text-slate-300 mt-1">
                            A regra de suprimento do NBO soma o <strong>Mínimo Padrão + Mínimo do Ponto Extra</strong> para compor o <strong>Mínimo Total</strong> (e equivalentemente para o Máximo).
                        </p>
                    </div>
                    <div class="flex items-center gap-3 text-xs">
                        <div class="px-3 py-1.5 rounded-xl bg-slate-800 border border-amber-500/30 text-amber-300">
                            Mín. PE Adicional: <strong class="text-white" id="lblSomaMinPE">0 un</strong>
                        </div>
                        <div class="px-3 py-1.5 rounded-xl bg-slate-800 border border-amber-500/30 text-amber-300">
                            Máx. PE Adicional: <strong class="text-white" id="lblSomaMaxPE">0 un</strong>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Tabela Exclusiva de Pontos Extras -->
            <div class="glass-panel rounded-2xl border border-slate-700/60 shadow-md overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs text-slate-300">
                        <thead class="bg-slate-800 text-slate-400 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-700">
                            <tr>
                                <th class="p-3">Loja</th>
                                <th class="p-3">Cód</th>
                                <th class="p-3">Produto</th>
                                <th class="p-3">Abastecimento</th>
                                <th class="p-3">Comprador</th>
                                <th class="p-3 text-center text-amber-300 font-bold">PEs</th>
                                <th class="p-3 text-right">Mín. Padrão</th>
                                <th class="p-3 text-right text-amber-300 font-bold">+ Mín. PE</th>
                                <th class="p-3 text-right text-white font-extrabold bg-slate-800/80">= Mín. Total</th>
                                <th class="p-3 text-right">Máx. Padrão</th>
                                <th class="p-3 text-right text-amber-300 font-bold">+ Máx. PE</th>
                                <th class="p-3 text-right text-white font-extrabold bg-slate-800/80">= Máx. Total</th>
                                <th class="p-3 text-right font-bold text-teal-300">Estq Loja</th>
                                <th class="p-3">Status de Ruptura</th>
                            </tr>
                        </thead>
                        <tbody id="tbodyPontosExtras" class="divide-y divide-slate-700/50">
                            <!-- Injetado via JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- CONTEÚDO DA ABA 3: MATRIZ DE AÇÃO RÁPIDA -->
        <div id="aba_acoes_criticas" class="tab-content hidden space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div class="glass-panel p-4 rounded-2xl border border-orange-500/40 bg-orange-950/10">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-xs font-bold text-orange-400 uppercase tracking-wider">Ação 1: Transferir do CD (M)</span>
                        <span class="px-2 py-0.5 rounded-full text-[10px] bg-orange-500/20 text-orange-300 font-bold" id="cntAcaoCD">0 itens</span>
                    </div>
                    <p class="text-xs text-slate-300">Itens via CD (M) com estoque baixo na loja, mas com <strong>saldo disponível no CD</strong>. Emitir transferência do CD para a Loja.</p>
                </div>

                <div class="glass-panel p-4 rounded-2xl border border-red-500/40 bg-red-950/10">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-xs font-bold text-red-400 uppercase tracking-wider">Ação 2: Comprar Fornecedor</span>
                        <span class="px-2 py-0.5 rounded-full text-[10px] bg-red-500/20 text-red-300 font-bold" id="cntAcaoCompra">0 itens</span>
                    </div>
                    <p class="text-xs text-slate-300">Loja abaixo do mínimo, <strong>CD zerado ou item Direto Loja (L) sem pedidos</strong>. Emitir pedido urgente com o fornecedor.</p>
                </div>

                <div class="glass-panel p-4 rounded-2xl border border-indigo-500/40 bg-indigo-950/10">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-xs font-bold text-indigo-400 uppercase tracking-wider">Ação 3: Bloquear/Promocionar Excesso</span>
                        <span class="px-2 py-0.5 rounded-full text-[10px] bg-indigo-500/20 text-indigo-300 font-bold" id="cntAcaoExcesso">0 itens</span>
                    </div>
                    <p class="text-xs text-slate-300">Itens acima do estoque máximo com cobertura alta. Pausar pedidos e avaliar remanejamento entre lojas.</p>
                </div>
            </div>

            <!-- Tabela de Itens Críticos -->
            <div class="glass-panel rounded-2xl border border-slate-700/60 shadow-md overflow-hidden">
                <div class="p-4 border-b border-slate-700/60 flex items-center justify-between">
                    <h3 class="text-sm font-bold text-white font-display flex items-center gap-2">
                        <i class="fa-solid fa-triangle-exclamation text-red-400"></i> Fila de Decisão: Itens Abaixo do Mínimo
                    </h3>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs text-slate-300">
                        <thead class="bg-slate-800/80 text-slate-400 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-700">
                            <tr>
                                <th class="p-3">Loja</th>
                                <th class="p-3">Cód</th>
                                <th class="p-3">Descrição do Produto</th>
                                <th class="p-3">Abastecimento</th>
                                <th class="p-3">Comprador</th>
                                <th class="p-3 text-right">Estq Loja</th>
                                <th class="p-3 text-right">Mín. Padrão</th>
                                <th class="p-3 text-right text-amber-300">Mín. PE</th>
                                <th class="p-3 text-right text-white font-bold">= Mín. Total</th>
                                <th class="p-3 text-right font-bold text-teal-400">Saldo CDs</th>
                                <th class="p-3 text-right">Vda 30D</th>
                                <th class="p-3 text-right">Dias Estq</th>
                                <th class="p-3">Status / Diagnóstico</th>
                            </tr>
                        </thead>
                        <tbody id="tbodyCriticos" class="divide-y divide-slate-700/50">
                            <!-- Injetado via JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- CONTEÚDO DA ABA 4: DIAGNÓSTICO POR LOJA -->
        <div id="aba_por_loja" class="tab-content hidden space-y-6">
            <div class="glass-panel rounded-2xl border border-slate-700/60 shadow-md overflow-hidden">
                <div class="p-4 border-b border-slate-700/60 flex items-center justify-between">
                    <h3 class="text-sm font-bold text-white font-display flex items-center gap-2">
                        <i class="fa-solid fa-store text-teal-400"></i> Painel Comparativo de Filiais (Lojas)
                    </h3>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-left text-xs text-slate-300">
                        <thead class="bg-slate-800/80 text-slate-400 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-700">
                            <tr>
                                <th class="p-3">Loja</th>
                                <th class="p-3 text-right">Total Itens</th>
                                <th class="p-3 text-right text-sky-400">Via CD (M)</th>
                                <th class="p-3 text-right text-purple-400">Direto Loja (L)</th>
                                <th class="p-3 text-right text-amber-300 font-bold">PEs Ativos</th>
                                <th class="p-3 text-right text-orange-400">CD Saldo (4)</th>
                                <th class="p-3 text-right text-red-400">Comprar (5)</th>
                                <th class="p-3 text-right text-amber-400">A Caminho (6)</th>
                                <th class="p-3 text-right text-emerald-400">Regular (8)</th>
                                <th class="p-3 text-right text-indigo-400">Excesso (9)</th>
                                <th class="p-3 text-right">% Em Risco</th>
                                <th class="p-3 text-right">Mín. Total</th>
                                <th class="p-3 text-right font-medium">Estoque Físico</th>
                            </tr>
                        </thead>
                        <tbody id="tbodyLojas" class="divide-y divide-slate-700/50">
                            <!-- Injetado via JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- CONTEÚDO DA ABA 5: TABELA COMPLETA -->
        <div id="aba_tabela_completa" class="tab-content hidden space-y-4">
            <div class="glass-panel rounded-2xl border border-slate-700/60 shadow-md overflow-hidden">
                <div class="p-4 border-b border-slate-700/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <h3 class="text-sm font-bold text-white font-display flex items-center gap-2">
                        <i class="fa-solid fa-list-check text-teal-400"></i> Registros Detalhados NBO
                    </h3>
                    <div class="text-xs text-slate-400">
                        Clique nos cabeçalhos para ordenar
                    </div>
                </div>

                <div class="overflow-x-auto max-h-[600px]">
                    <table class="w-full text-left text-xs text-slate-300" id="tabelaGeral">
                        <thead class="bg-slate-800 text-slate-300 font-semibold uppercase text-[10px] tracking-wider sticky top-0 z-10 border-b border-slate-700">
                            <tr>
                                <th class="p-3 cursor-pointer" onclick="ordenarPor('COD_LOJA')">Loja <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3 cursor-pointer" onclick="ordenarPor('COD_PRODUTO')">Cód <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3 cursor-pointer" onclick="ordenarPor('DESCRICAO_PRODUTO')">Produto <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3 cursor-pointer" onclick="ordenarPor('FORMA_ABASTECIMENTO')">Abast. <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3 cursor-pointer" onclick="ordenarPor('COMPRADOR')">Comprador <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3 text-right cursor-pointer" onclick="ordenarPor('ESTQ_FISICO_LOJA')">Estq Loja <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3 text-right cursor-pointer" onclick="ordenarPor('ESTQ_MIN_PADRAO')">Mín. Pad <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3 text-right text-amber-300 cursor-pointer" onclick="ordenarPor('ESTQ_MIN_PONTO_EXTRA')">+ Mín. PE <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3 text-right text-white font-bold cursor-pointer" onclick="ordenarPor('ESTQ_MIN_TOTAL')">= Mín. Tot <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3 text-right cursor-pointer" onclick="ordenarPor('ESTQ_MAX_PADRAO')">Máx. Pad <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3 text-right text-amber-300 cursor-pointer" onclick="ordenarPor('ESTQ_MAX_PONTO_EXTRA')">+ Máx. PE <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3 text-right text-white font-bold cursor-pointer" onclick="ordenarPor('ESTQ_MAX_TOTAL')">= Máx. Tot <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3 text-right cursor-pointer" onclick="ordenarPor('ESTQ_DISP_TOTAL_CD')">Saldo CD <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3 text-right cursor-pointer" onclick="ordenarPor('VDA_30D_VALOR')">Vda 30D <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3 text-right cursor-pointer" onclick="ordenarPor('DIAS_ESTOQUE_LOJA')">Dias <i class="fa-solid fa-sort text-slate-500"></i></th>
                                <th class="p-3">Status de Ruptura</th>
                            </tr>
                        </thead>
                        <tbody id="tbodyGeral" class="divide-y divide-slate-700/50">
                            <!-- Injetado via JS -->
                        </tbody>
                    </table>
                </div>

                <!-- Paginação -->
                <div class="p-3 border-t border-slate-700/60 flex items-center justify-between text-xs text-slate-400">
                    <div>Página <span id="lblPaginaAtual" class="font-bold text-white">1</span> de <span id="lblTotalPaginas" class="font-bold text-white">1</span></div>
                    <div class="flex items-center space-x-2">
                        <button onclick="mudarPagina(-1)" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300">Anterior</button>
                        <button onclick="mudarPagina(1)" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300">Próxima</button>
                    </div>
                </div>
            </div>
        </div>

    </main>

    <!-- Base de Dados Bruta Embutida -->
    <script>
        const RAW_DATA = {json.dumps(records_json, ensure_ascii=False)};
        
        let filteredData = [...RAW_DATA];
        let paginaAtual = 1;
        const itensPorPagina = 25;
        let colunaOrdenada = 'COD_LOJA';
        let ordemAsc = true;
        
        let chartStatusInstance = null;
        let chartLojasInstance = null;
        let chartCompradorInstance = null;
        let chartDeptoInstance = null;

        document.addEventListener('DOMContentLoaded', () => {{
            const lblDate = document.getElementById('lblTimestamp');
            if (lblDate) lblDate.innerText = new Date().toLocaleDateString('pt-BR');
            popularSelects();
            aplicarFiltros();
        }});

        function popularSelects() {{
            const lojas = [...new Set(RAW_DATA.map(d => d.COD_LOJA))].sort((a,b) => a-b);
            const compradores = [...new Set(RAW_DATA.map(d => d.COMPRADOR))].sort();
            const deptos = [...new Set(RAW_DATA.map(d => d.DEPARTAMENTO))].sort();

            const selLoja = document.getElementById('filtroLoja');
            if (selLoja) {{
                lojas.forEach(l => {{
                    const opt = document.createElement('option');
                    opt.value = l;
                    opt.text = `Loja ${{l}}`;
                    selLoja.appendChild(opt);
                }});
            }}

            const selComp = document.getElementById('filtroComprador');
            if (selComp) {{
                compradores.forEach(c => {{
                    const opt = document.createElement('option');
                    opt.value = c;
                    opt.text = c;
                    selComp.appendChild(opt);
                }});
            }}

            const selDept = document.getElementById('filtroDepartamento');
            if (selDept) {{
                deptos.forEach(d => {{
                    const opt = document.createElement('option');
                    opt.value = d;
                    opt.text = d;
                    selDept.appendChild(opt);
                }});
            }}
        }}

        function aplicarFiltros() {{
            const elLoja = document.getElementById('filtroLoja');
            const elAbast = document.getElementById('filtroAbastecimento');
            const elComp = document.getElementById('filtroComprador');
            const elDept = document.getElementById('filtroDepartamento');
            const elPE = document.getElementById('filtroPontoExtra');
            const elStatus = document.getElementById('filtroStatus');
            const elBusca = document.getElementById('filtroBusca');

            const loja = elLoja ? elLoja.value : '';
            const abast = elAbast ? elAbast.value : '';
            const comprador = elComp ? elComp.value : '';
            const depto = elDept ? elDept.value : '';
            const pontoExtra = elPE ? elPE.value : '';
            const status = elStatus ? elStatus.value : '';
            const busca = elBusca ? elBusca.value.toLowerCase().trim() : '';

            filteredData = RAW_DATA.filter(row => {{
                if (loja && String(row.COD_LOJA) !== String(loja)) return false;
                if (abast && String(row.FORMA_ABASTECIMENTO).trim().toUpperCase() !== String(abast).trim().toUpperCase()) return false;
                if (comprador && row.COMPRADOR !== comprador) return false;
                if (depto && row.DEPARTAMENTO !== depto) return false;
                if (pontoExtra === 'COM_PE' && Number(row.PONTOS_EXTRAS_ATIVOS || 0) <= 0) return false;
                if (pontoExtra === 'SEM_PE' && Number(row.PONTOS_EXTRAS_ATIVOS || 0) > 0) return false;
                if (status && !String(row.STATUS_RUPTURA).includes(status)) return false;
                if (busca) {{
                    const matchDesc = String(row.DESCRICAO_PRODUTO).toLowerCase().includes(busca);
                    const matchCod = String(row.COD_PRODUTO).includes(busca);
                    const matchForn = String(row.FORNECEDOR_PRINCIPAL).toLowerCase().includes(busca);
                    if (!matchDesc && !matchCod && !matchForn) return false;
                }}
                return true;
            }});

            paginaAtual = 1;
            atualizarKPIs();
            renderizarGraficos();
            renderizarTabelaPontosExtras();
            renderizarTabelaCriticos();
            renderizarTabelaLojas();
            renderizarTabelaGeral();
        }}

        function limparFiltros() {{
            const elLoja = document.getElementById('filtroLoja');
            const elAbast = document.getElementById('filtroAbastecimento');
            const elComp = document.getElementById('filtroComprador');
            const elDept = document.getElementById('filtroDepartamento');
            const elPE = document.getElementById('filtroPontoExtra');
            const elStatus = document.getElementById('filtroStatus');
            const elBusca = document.getElementById('filtroBusca');

            if (elLoja) elLoja.value = '';
            if (elAbast) elAbast.value = '';
            if (elComp) elComp.value = '';
            if (elDept) elDept.value = '';
            if (elPE) elPE.value = '';
            if (elStatus) elStatus.value = '';
            if (elBusca) elBusca.value = '';
            aplicarFiltros();
        }}

        function filtrarStatus(tipo) {{
            const selStatus = document.getElementById('filtroStatus');
            if (selStatus) {{
                if (tipo === 'ABAIXO') {{
                    selStatus.value = '5 -';
                }} else if (tipo === 'EXCESSO') {{
                    selStatus.value = '9 -';
                }}
                aplicarFiltros();
                trocarAba('aba_tabela_completa');
            }}
        }}

        function formatarMoeda(val) {{
            return 'R$ ' + Number(val || 0).toLocaleString('pt-BR', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
        }}

        function formatarNumero(val) {{
            return Number(val || 0).toLocaleString('pt-BR');
        }}

        function setTexto(id, texto) {{
            const el = document.getElementById(id);
            if (el) el.innerText = texto;
        }}

        function atualizarKPIs() {{
            const totalSkus = filteredData.length;
            const lojasUnicas = new Set(filteredData.map(d => d.COD_LOJA)).size;
            const totalVendaValor = filteredData.reduce((acc, d) => acc + (Number(d.VDA_30D_VALOR) || 0), 0);
            const totalVendaQtd = filteredData.reduce((acc, d) => acc + (Number(d.VDA_30D_QTD) || 0), 0);
            const totalEstqLoja = filteredData.reduce((acc, d) => acc + (Number(d.ESTQ_FISICO_LOJA) || 0), 0);
            const totalEstqCD = filteredData.reduce((acc, d) => acc + (Number(d.ESTQ_DISP_TOTAL_CD) || 0), 0);
            const cd15 = filteredData.reduce((acc, d) => acc + (Number(d.ESTQ_DISP_CD15) || 0), 0);
            const cd50 = filteredData.reduce((acc, d) => acc + (Number(d.ESTQ_DISP_CD50) || 0), 0);

            const cntM = filteredData.filter(d => String(d.FORMA_ABASTECIMENTO).trim().toUpperCase() === 'M').length;
            const cntL = filteredData.filter(d => String(d.FORMA_ABASTECIMENTO).trim().toUpperCase() === 'L').length;

            const itensPE = filteredData.filter(d => Number(d.PONTOS_EXTRAS_ATIVOS || 0) > 0);
            const somaMinPE = itensPE.reduce((acc, d) => acc + (Number(d.ESTQ_MIN_PONTO_EXTRA) || 0), 0);
            const somaMaxPE = itensPE.reduce((acc, d) => acc + (Number(d.ESTQ_MAX_PONTO_EXTRA) || 0), 0);

            const st4 = filteredData.filter(d => String(d.STATUS_RUPTURA).includes('4 -')).length;
            const st5 = filteredData.filter(d => String(d.STATUS_RUPTURA).includes('5 -')).length;
            const st6 = filteredData.filter(d => String(d.STATUS_RUPTURA).includes('6 -')).length;
            const st8 = filteredData.filter(d => String(d.STATUS_RUPTURA).includes('8 -')).length;
            const st9 = filteredData.filter(d => String(d.STATUS_RUPTURA).includes('9 -')).length;

            const abaixoMinTotal = st4 + st5 + st6;

            setTexto('kpi_total_skus', formatarNumero(totalSkus));
            setTexto('kpi_lojas_ativas', `${{lojasUnicas}} loja${{lojasUnicas > 1 ? 's' : ''}}`);
            setTexto('kpi_abast_m', `M: ${{cntM}}`);
            setTexto('kpi_abast_l', `L: ${{cntL}}`);
            setTexto('kpi_venda_30d', formatarMoeda(totalVendaValor));
            setTexto('kpi_venda_qtd', formatarNumero(totalVendaQtd) + ' un');
            setTexto('kpi_estq_loja', formatarNumero(totalEstqLoja));
            setTexto('kpi_estq_cd', formatarNumero(totalEstqCD));
            setTexto('kpi_cd_breakdown', `CD15: ${{formatarNumero(cd15)}} | CD50: ${{formatarNumero(cd50)}}`);

            setTexto('kpi_pontos_extras', formatarNumero(itensPE.length));
            setTexto('kpi_pe_sub', `+${{formatarNumero(somaMinPE)}} un Mín. PE`);
            setTexto('cntBadgePE', formatarNumero(itensPE.length));
            setTexto('lblSomaMinPE', `${{formatarNumero(somaMinPE)}} un`);
            setTexto('lblSomaMaxPE', `${{formatarNumero(somaMaxPE)}} un`);

            setTexto('kpi_abaixo_min', formatarNumero(abaixoMinTotal));
            setTexto('kpi_abaixo_sub', `CD Saldo: ${{st4}} | Comprar: ${{st5}} | Ped: ${{st6}}`);

            setTexto('kpi_excesso', formatarNumero(st9));
            const pctExcesso = totalSkus > 0 ? ((st9 / totalSkus) * 100).toFixed(1) : '0';
            setTexto('kpi_excesso_pct', `${{pctExcesso}}% da base`);

            setTexto('cntFiltrados', formatarNumero(totalSkus));
            setTexto('cntTotal', formatarNumero(RAW_DATA.length));
            setTexto('cntBadgeCriticos', formatarNumero(st4 + st5));

            setTexto('cntAcaoCD', `${{st4}} iten${{st4 === 1 ? '' : 's'}}`);
            setTexto('cntAcaoCompra', `${{st5}} iten${{st5 === 1 ? '' : 's'}}`);
            setTexto('cntAcaoExcesso', `${{st9}} iten${{st9 === 1 ? '' : 's'}}`);
        }}

        function getAbastecimentoBadge(forma) {{
            const f = String(forma || '').trim().toUpperCase();
            if (f === 'M') {{
                return `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30 flex items-center gap-1 w-fit" title="Abastecimento Centralizado via CD (CD15 / CD50)"><i class="fa-solid fa-warehouse"></i> M (Via CD)</span>`;
            }} else if (f === 'L') {{
                return `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center gap-1 w-fit" title="Compra Direta na Loja (DSD / Fornecedor entrega na filial)"><i class="fa-solid fa-truck-moving"></i> L (Direto Loja)</span>`;
            }}
            return `<span class="px-2 py-0.5 rounded text-[10px] bg-slate-700 text-slate-300">${{f}}</span>`;
        }}

        function getStatusBadge(status) {{
            const s = String(status || '');
            if (s.includes('4 -')) {{
                return `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-orange-500/20 text-orange-300 border border-orange-500/30 flex items-center gap-1 w-fit"><i class="fa-solid fa-truck-ramp-box"></i> CD Saldo (Transferir)</span>`;
            }} else if (s.includes('5 -')) {{
                return `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-300 border border-red-500/30 flex items-center gap-1 w-fit"><i class="fa-solid fa-cart-plus"></i> Comprar Urgente</span>`;
            }} else if (s.includes('6 -')) {{
                return `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1 w-fit"><i class="fa-solid fa-truck-arrow-right"></i> A Caminho / Pedido</span>`;
            }} else if (s.includes('8 -')) {{
                return `<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1 w-fit"><i class="fa-solid fa-circle-check"></i> Regular / Normal</span>`;
            }} else if (s.includes('9 -')) {{
                return `<span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center gap-1 w-fit"><i class="fa-solid fa-cubes-stacked"></i> Excesso (> Máximo)</span>`;
            }}
            return `<span class="px-2 py-0.5 rounded text-[10px] bg-slate-700 text-slate-300">${{s}}</span>`;
        }}

        function renderizarGraficos() {{
            const canvasStatus = document.getElementById('chartStatus');
            const canvasLojas = document.getElementById('chartLojas');
            const canvasComp = document.getElementById('chartComprador');
            const canvasDepto = document.getElementById('chartDepto');

            // 1. Donut Chart Status
            if (canvasStatus) {{
                const st4 = filteredData.filter(d => String(d.STATUS_RUPTURA).includes('4 -')).length;
                const st5 = filteredData.filter(d => String(d.STATUS_RUPTURA).includes('5 -')).length;
                const st6 = filteredData.filter(d => String(d.STATUS_RUPTURA).includes('6 -')).length;
                const st8 = filteredData.filter(d => String(d.STATUS_RUPTURA).includes('8 -')).length;
                const st9 = filteredData.filter(d => String(d.STATUS_RUPTURA).includes('9 -')).length;

                if (chartStatusInstance) chartStatusInstance.destroy();
                const ctxStatus = canvasStatus.getContext('2d');
                chartStatusInstance = new Chart(ctxStatus, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['4. Saldo no CD', '5. Comprar Urgente', '6. A Caminho', '8. Regular', '9. Excesso'],
                        datasets: [{{
                            data: [st4, st5, st6, st8, st9],
                            backgroundColor: ['#f97316', '#ef4444', '#f59e0b', '#10b981', '#6366f1'],
                            borderWidth: 2,
                            borderColor: '#1e293b'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'bottom',
                                labels: {{ color: '#94a3b8', font: {{ size: 10 }} }}
                            }}
                        }},
                        cutout: '68%'
                    }}
                }});
            }}

            // 2. Bar Chart Lojas
            if (canvasLojas) {{
                const lojas = [...new Set(filteredData.map(d => d.COD_LOJA))].sort((a,b) => a-b);
                const dataCriticos = lojas.map(lj => filteredData.filter(d => d.COD_LOJA === lj && String(d.STATUS_RUPTURA).includes('ABAIXO')).length);
                const dataRegular = lojas.map(lj => filteredData.filter(d => d.COD_LOJA === lj && String(d.STATUS_RUPTURA).includes('REGULAR')).length);
                const dataExcesso = lojas.map(lj => filteredData.filter(d => d.COD_LOJA === lj && String(d.STATUS_RUPTURA).includes('EXCESSO')).length);

                if (chartLojasInstance) chartLojasInstance.destroy();
                const ctxLojas = canvasLojas.getContext('2d');
                chartLojasInstance = new Chart(ctxLojas, {{
                    type: 'bar',
                    data: {{
                        labels: lojas.map(l => `Loja ${{l}}`),
                        datasets: [
                            {{ label: 'Abaixo Mínimo', data: dataCriticos, backgroundColor: '#ef4444' }},
                            {{ label: 'Regular', data: dataRegular, backgroundColor: '#10b981' }},
                            {{ label: 'Excesso', data: dataExcesso, backgroundColor: '#6366f1' }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            x: {{ stacked: true, ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }}, grid: {{ display: false }} }},
                            y: {{ stacked: true, ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }}, grid: {{ color: '#334155' }} }}
                        }},
                        plugins: {{
                            legend: {{ position: 'top', labels: {{ color: '#94a3b8', font: {{ size: 10 }} }} }}
                        }}
                    }}
                }});
            }}

            // 3. Bar Chart Compradores
            if (canvasComp) {{
                const compradores = [...new Set(filteredData.map(d => d.COMPRADOR))].sort();
                const vendasComp = compradores.map(c => filteredData.filter(d => d.COMPRADOR === c).reduce((acc, d) => acc + (Number(d.VDA_30D_VALOR) || 0), 0));
                const estqComp = compradores.map(c => filteredData.filter(d => d.COMPRADOR === c).reduce((acc, d) => acc + (Number(d.ESTQ_FISICO_LOJA) || 0), 0));

                if (chartCompradorInstance) chartCompradorInstance.destroy();
                const ctxComp = canvasComp.getContext('2d');
                chartCompradorInstance = new Chart(ctxComp, {{
                    type: 'bar',
                    data: {{
                        labels: compradores,
                        datasets: [
                            {{
                                label: 'Venda 30D (R$)',
                                data: vendasComp,
                                backgroundColor: '#0d9488',
                                yAxisID: 'y'
                            }},
                            {{
                                label: 'Estoque Físico (Un)',
                                data: estqComp,
                                backgroundColor: '#3b82f6',
                                yAxisID: 'y1'
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            x: {{ ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }}, grid: {{ display: false }} }},
                            y: {{
                                type: 'linear',
                                position: 'left',
                                ticks: {{ color: '#0d9488', font: {{ size: 10 }}, callback: v => 'R$ ' + (v/1000).toFixed(0) + 'k' }},
                                grid: {{ color: '#334155' }}
                            }},
                            y1: {{
                                type: 'linear',
                                position: 'right',
                                ticks: {{ color: '#3b82f6', font: {{ size: 10 }} }},
                                grid: {{ display: false }}
                            }}
                        }},
                        plugins: {{
                            legend: {{ position: 'top', labels: {{ color: '#94a3b8', font: {{ size: 10 }} }} }}
                        }}
                    }}
                }});
            }}

            // 4. Depto Chart
            if (canvasDepto) {{
                const deptos = [...new Set(filteredData.map(d => d.DEPARTAMENTO))].sort();
                const skusDepto = deptos.map(dp => filteredData.filter(d => d.DEPARTAMENTO === dp).length);

                if (chartDeptoInstance) chartDeptoInstance.destroy();
                const ctxDepto = canvasDepto.getContext('2d');
                chartDeptoInstance = new Chart(ctxDepto, {{
                    type: 'bar',
                    data: {{
                        labels: deptos,
                        datasets: [{{
                            label: 'Total SKUs',
                            data: skusDepto,
                            backgroundColor: ['#6366f1', '#14b8a6', '#f59e0b', '#ec4899'],
                            borderRadius: 6
                        }}]
                    }},
                    options: {{
                        indexAxis: 'y',
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            x: {{ ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }}, grid: {{ color: '#334155' }} }},
                            y: {{ ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }}, grid: {{ display: false }} }}
                        }},
                        plugins: {{
                            legend: {{ display: false }}
                        }}
                    }}
                }});
            }}
        }}

        function renderizarTabelaPontosExtras() {{
            const tbody = document.getElementById('tbodyPontosExtras');
            if (!tbody) return;
            tbody.innerHTML = '';

            const itensPE = filteredData.filter(d => Number(d.PONTOS_EXTRAS_ATIVOS || 0) > 0);

            if (itensPE.length === 0) {{
                tbody.innerHTML = `<tr><td colspan="14" class="p-4 text-center text-slate-500 italic">Nenhum item com ponto extra ativo para os filtros selecionados.</td></tr>`;
                return;
            }}

            itensPE.forEach(row => {{
                const minTot = Number(row.ESTQ_MIN_PADRAO || 0) + Number(row.ESTQ_MIN_PONTO_EXTRA || 0);
                const maxTot = Number(row.ESTQ_MAX_PADRAO || 0) + Number(row.ESTQ_MAX_PONTO_EXTRA || 0);

                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/60 transition";
                tr.innerHTML = `
                    <td class="p-3 font-bold text-white">Loja ${{row.COD_LOJA}}</td>
                    <td class="p-3 text-slate-400">${{row.COD_PRODUTO}}</td>
                    <td class="p-3 font-medium text-white">${{row.DESCRICAO_PRODUTO}}<br><span class="text-[10px] text-slate-400">${{row.FORNECEDOR_PRINCIPAL}}</span></td>
                    <td class="p-3">${{getAbastecimentoBadge(row.FORMA_ABASTECIMENTO)}}</td>
                    <td class="p-3 text-slate-300">${{row.COMPRADOR}}</td>
                    <td class="p-3 text-center"><span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold border border-amber-500/40">${{row.PONTOS_EXTRAS_ATIVOS}}</span></td>
                    <td class="p-3 text-right text-slate-300">${{formatarNumero(row.ESTQ_MIN_PADRAO)}}</td>
                    <td class="p-3 text-right font-bold text-amber-300">+${{formatarNumero(row.ESTQ_MIN_PONTO_EXTRA)}}</td>
                    <td class="p-3 text-right font-extrabold text-white bg-slate-800/60">${{formatarNumero(minTot)}}</td>
                    <td class="p-3 text-right text-slate-300">${{formatarNumero(row.ESTQ_MAX_PADRAO)}}</td>
                    <td class="p-3 text-right font-bold text-amber-300">+${{formatarNumero(row.ESTQ_MAX_PONTO_EXTRA)}}</td>
                    <td class="p-3 text-right font-extrabold text-white bg-slate-800/60">${{formatarNumero(maxTot)}}</td>
                    <td class="p-3 text-right font-bold text-teal-300">${{formatarNumero(row.ESTQ_FISICO_LOJA)}}</td>
                    <td class="p-3">${{getStatusBadge(row.STATUS_RUPTURA)}}</td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function renderizarTabelaCriticos() {{
            const tbody = document.getElementById('tbodyCriticos');
            if (!tbody) return;
            tbody.innerHTML = '';

            const criticos = filteredData.filter(d => String(d.STATUS_RUPTURA).includes('4 -') || String(d.STATUS_RUPTURA).includes('5 -') || String(d.STATUS_RUPTURA).includes('6 -'));

            if (criticos.length === 0) {{
                tbody.innerHTML = `<tr><td colspan="13" class="p-4 text-center text-slate-500 italic">Nenhum item crítico para os filtros selecionados.</td></tr>`;
                return;
            }}

            criticos.forEach(row => {{
                const temPE = Number(row.PONTOS_EXTRAS_ATIVOS || 0) > 0;
                const minTot = Number(row.ESTQ_MIN_PADRAO || 0) + Number(row.ESTQ_MIN_PONTO_EXTRA || 0);

                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/50 transition";
                tr.innerHTML = `
                    <td class="p-3 font-bold text-white">Loja ${{row.COD_LOJA}}</td>
                    <td class="p-3 text-slate-400">${{row.COD_PRODUTO}}</td>
                    <td class="p-3 font-medium text-white">${{row.DESCRICAO_PRODUTO}}<br><span class="text-[10px] text-slate-400">${{row.FORNECEDOR_PRINCIPAL}}</span></td>
                    <td class="p-3">${{getAbastecimentoBadge(row.FORMA_ABASTECIMENTO)}}</td>
                    <td class="p-3 text-slate-300">${{row.COMPRADOR}}</td>
                    <td class="p-3 text-right font-bold text-red-400">${{formatarNumero(row.ESTQ_FISICO_LOJA)}}</td>
                    <td class="p-3 text-right text-slate-300">${{formatarNumero(row.ESTQ_MIN_PADRAO)}}</td>
                    <td class="p-3 text-right ${{temPE ? 'text-amber-300 font-bold' : 'text-slate-600'}}">${{temPE ? '+' + formatarNumero(row.ESTQ_MIN_PONTO_EXTRA) : '-'}}</td>
                    <td class="p-3 text-right font-extrabold text-white">${{formatarNumero(minTot)}}</td>
                    <td class="p-3 text-right font-bold ${{row.ESTQ_DISP_TOTAL_CD > 0 ? 'text-teal-400' : 'text-slate-500'}}">${{formatarNumero(row.ESTQ_DISP_TOTAL_CD)}}</td>
                    <td class="p-3 text-right text-slate-300">${{formatarNumero(row.VDA_30D_QTD)}}</td>
                    <td class="p-3 text-right font-semibold text-amber-300">${{Number(row.DIAS_ESTOQUE_LOJA || 0).toFixed(1)}} d</td>
                    <td class="p-3">${{getStatusBadge(row.STATUS_RUPTURA)}}</td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function renderizarTabelaLojas() {{
            const tbody = document.getElementById('tbodyLojas');
            if (!tbody) return;
            tbody.innerHTML = '';

            const lojas = [...new Set(filteredData.map(d => d.COD_LOJA))].sort((a,b) => a-b);
            lojas.forEach(lj => {{
                const sub = filteredData.filter(d => d.COD_LOJA === lj);
                const tot = sub.length;
                const cntM = sub.filter(d => String(d.FORMA_ABASTECIMENTO).trim().toUpperCase() === 'M').length;
                const cntL = sub.filter(d => String(d.FORMA_ABASTECIMENTO).trim().toUpperCase() === 'L').length;
                const pes = sub.reduce((acc, d) => acc + (Number(d.PONTOS_EXTRAS_ATIVOS) || 0), 0);
                const s4 = sub.filter(d => String(d.STATUS_RUPTURA).includes('4 -')).length;
                const s5 = sub.filter(d => String(d.STATUS_RUPTURA).includes('5 -')).length;
                const s6 = sub.filter(d => String(d.STATUS_RUPTURA).includes('6 -')).length;
                const s8 = sub.filter(d => String(d.STATUS_RUPTURA).includes('8 -')).length;
                const s9 = sub.filter(d => String(d.STATUS_RUPTURA).includes('9 -')).length;
                const pctRisco = tot > 0 ? (((s4 + s5 + s6) / tot) * 100).toFixed(1) : 0;
                
                const minPad = sub.reduce((acc, d) => acc + (Number(d.ESTQ_MIN_PADRAO) || 0), 0);
                const minPE = sub.reduce((acc, d) => acc + (Number(d.ESTQ_MIN_PONTO_EXTRA) || 0), 0);
                const minTot = minPad + minPE;
                const estq = sub.reduce((acc, d) => acc + (Number(d.ESTQ_FISICO_LOJA) || 0), 0);

                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/50 transition cursor-pointer";
                tr.onclick = () => {{
                    const elL = document.getElementById('filtroLoja');
                    if (elL) elL.value = lj;
                    aplicarFiltros();
                    trocarAba('aba_tabela_completa');
                }};
                tr.innerHTML = `
                    <td class="p-3 font-bold text-teal-300 flex items-center gap-1.5"><i class="fa-solid fa-shop text-xs text-slate-500"></i> Loja ${{lj}}</td>
                    <td class="p-3 text-right font-semibold text-white">${{formatarNumero(tot)}}</td>
                    <td class="p-3 text-right text-sky-400 font-bold">${{cntM}}</td>
                    <td class="p-3 text-right text-purple-400 font-bold">${{cntL}}</td>
                    <td class="p-3 text-right ${{pes > 0 ? 'font-bold text-amber-300 bg-amber-500/10 rounded' : 'text-slate-600'}}">${{pes}}</td>
                    <td class="p-3 text-right ${{s4 > 0 ? 'font-bold text-orange-400' : 'text-slate-600'}}">${{s4}}</td>
                    <td class="p-3 text-right ${{s5 > 0 ? 'font-bold text-red-400' : 'text-slate-600'}}">${{s5}}</td>
                    <td class="p-3 text-right ${{s6 > 0 ? 'font-bold text-amber-400' : 'text-slate-600'}}">${{s6}}</td>
                    <td class="p-3 text-right text-emerald-400">${{s8}}</td>
                    <td class="p-3 text-right text-indigo-300">${{s9}}</td>
                    <td class="p-3 text-right font-bold ${{Number(pctRisco) > 15 ? 'text-red-400' : 'text-slate-400'}}">${{pctRisco}}%</td>
                    <td class="p-3 text-right font-extrabold text-white">${{formatarNumero(minTot)}}</td>
                    <td class="p-3 text-right text-slate-300">${{formatarNumero(estq)}}</td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function renderizarTabelaGeral() {{
            const tbody = document.getElementById('tbodyGeral');
            if (!tbody) return;
            tbody.innerHTML = '';

            const sorted = [...filteredData].sort((a, b) => {{
                let valA = a[colunaOrdenada];
                let valB = b[colunaOrdenada];
                if (typeof valA === 'string') {{
                    return ordemAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
                }}
                return ordemAsc ? (valA - valB) : (valB - valA);
            }});

            const totalPaginas = Math.ceil(sorted.length / itensPorPagina) || 1;
            if (paginaAtual > totalPaginas) paginaAtual = totalPaginas;

            setTexto('lblPaginaAtual', paginaAtual);
            setTexto('lblTotalPaginas', totalPaginas);

            const inicio = (paginaAtual - 1) * itensPorPagina;
            const paginados = sorted.slice(inicio, inicio + itensPorPagina);

            if (paginados.length === 0) {{
                tbody.innerHTML = `<tr><td colspan="16" class="p-6 text-center text-slate-400 italic">Nenhum registro encontrado com os filtros aplicados. Clique em Limpar Filtros para ver todos os itens.</td></tr>`;
                return;
            }}

            paginados.forEach(row => {{
                const temPE = Number(row.PONTOS_EXTRAS_ATIVOS || 0) > 0;
                const minTot = Number(row.ESTQ_MIN_PADRAO || 0) + Number(row.ESTQ_MIN_PONTO_EXTRA || 0);
                const maxTot = Number(row.ESTQ_MAX_PADRAO || 0) + Number(row.ESTQ_MAX_PONTO_EXTRA || 0);

                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-800/50 transition " + (temPE ? "bg-amber-950/10" : "");
                tr.innerHTML = `
                    <td class="p-3 font-semibold text-white">Lj ${{row.COD_LOJA}}</td>
                    <td class="p-3 text-slate-400">${{row.COD_PRODUTO}}</td>
                    <td class="p-3 font-medium text-white">
                        ${{row.DESCRICAO_PRODUTO}}
                        ${{temPE ? '<span class="ml-1.5 px-1.5 py-0.2 rounded text-[9px] bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold"><i class="fa-solid fa-thumbtack"></i> PE: ' + row.PONTOS_EXTRAS_ATIVOS + '</span>' : ''}}
                        <br><span class="text-[10px] text-slate-500">${{row.FORNECEDOR_PRINCIPAL}}</span>
                    </td>
                    <td class="p-3">${{getAbastecimentoBadge(row.FORMA_ABASTECIMENTO)}}</td>
                    <td class="p-3 text-slate-300">${{row.COMPRADOR}}</td>
                    <td class="p-3 text-right font-bold text-white">${{formatarNumero(row.ESTQ_FISICO_LOJA)}}</td>
                    <td class="p-3 text-right text-slate-400">${{formatarNumero(row.ESTQ_MIN_PADRAO)}}</td>
                    <td class="p-3 text-right ${{temPE ? 'text-amber-300 font-bold' : 'text-slate-600'}}">${{temPE ? '+' + formatarNumero(row.ESTQ_MIN_PONTO_EXTRA) : '-'}}</td>
                    <td class="p-3 text-right font-extrabold text-white bg-slate-800/40">${{formatarNumero(minTot)}}</td>
                    <td class="p-3 text-right text-slate-400">${{formatarNumero(row.ESTQ_MAX_PADRAO)}}</td>
                    <td class="p-3 text-right ${{temPE ? 'text-amber-300 font-bold' : 'text-slate-600'}}">${{temPE ? '+' + formatarNumero(row.ESTQ_MAX_PONTO_EXTRA) : '-'}}</td>
                    <td class="p-3 text-right font-extrabold text-white bg-slate-800/40">${{formatarNumero(maxTot)}}</td>
                    <td class="p-3 text-right ${{row.ESTQ_DISP_TOTAL_CD > 0 ? 'text-teal-400 font-bold' : 'text-slate-600'}}">${{formatarNumero(row.ESTQ_DISP_TOTAL_CD)}}</td>
                    <td class="p-3 text-right text-white">${{formatarMoeda(row.VDA_30D_VALOR)}}</td>
                    <td class="p-3 text-right font-semibold text-amber-300">${{Number(row.DIAS_ESTOQUE_LOJA || 0).toFixed(1)}}</td>
                    <td class="p-3">${{getStatusBadge(row.STATUS_RUPTURA)}}</td>
                `;
                tbody.appendChild(tr);
            }});
        }}

        function ordenarPor(col) {{
            if (colunaOrdenada === col) {{
                ordemAsc = !ordemAsc;
            }} else {{
                colunaOrdenada = col;
                ordemAsc = true;
            }}
            renderizarTabelaGeral();
        }}

        function mudarPagina(delta) {{
            const totalPaginas = Math.ceil(filteredData.length / itensPorPagina) || 1;
            const nova = paginaAtual + delta;
            if (nova >= 1 && nova <= totalPaginas) {{
                paginaAtual = nova;
                renderizarTabelaGeral();
            }}
        }}

        function trocarAba(abaId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(el => {{
                el.classList.remove('border-teal-500', 'text-teal-400', 'border-amber-500', 'text-amber-400');
                el.classList.add('border-transparent', 'text-slate-400');
            }});

            const targetAba = document.getElementById(abaId);
            if (targetAba) targetAba.classList.remove('hidden');
            
            const btn = document.getElementById('btn_' + abaId);
            if (btn) {{
                if (abaId === 'aba_pontos_extras') {{
                    btn.classList.add('border-amber-500', 'text-amber-400');
                }} else {{
                    btn.classList.add('border-teal-500', 'text-teal-400');
                }}
                btn.classList.remove('border-transparent', 'text-slate-400');
            }}

            window.dispatchEvent(new Event('resize'));
        }}

        function toggleTheme() {{
            const html = document.documentElement;
            const icon = document.getElementById('themeIcon');
            if (html.classList.contains('dark')) {{
                html.classList.remove('dark');
                html.classList.add('light');
                if (icon) icon.className = 'fa-solid fa-moon';
            }} else {{
                html.classList.remove('light');
                html.classList.add('dark');
                if (icon) icon.className = 'fa-solid fa-sun';
            }}
            window.dispatchEvent(new Event('resize'));
        }}

        function exportarCSV() {{
            let csv = "Loja;Codigo;Descricao;FormaAbastecimento;DescricaoAbastecimento;Departamento;Comprador;PontosExtras;EstoqueMinPadrao;EstoqueMinPE;EstoqueMinTotal;EstoqueMaxPadrao;EstoqueMaxPE;EstoqueMaxTotal;EstoqueLoja;EstoqueCD;Venda30D_Valor;DiasEstoque;Status\\n";
            filteredData.forEach(row => {{
                const minTot = Number(row.ESTQ_MIN_PADRAO || 0) + Number(row.ESTQ_MIN_PONTO_EXTRA || 0);
                const maxTot = Number(row.ESTQ_MAX_PADRAO || 0) + Number(row.ESTQ_MAX_PONTO_EXTRA || 0);
                csv += `${{row.COD_LOJA}};${{row.COD_PRODUTO}};"${{row.DESCRICAO_PRODUTO}}";"${{row.FORMA_ABASTECIMENTO}}";"${{row.FORMA_ABASTECIMENTO_DESC}}";"${{row.DEPARTAMENTO}}";"${{row.COMPRADOR}}";${{row.PONTOS_EXTRAS_ATIVOS}};${{row.ESTQ_MIN_PADRAO}};${{row.ESTQ_MIN_PONTO_EXTRA}};${{minTot}};${{row.ESTQ_MAX_PADRAO}};${{row.ESTQ_MAX_PONTO_EXTRA}};${{maxTot}};${{row.ESTQ_FISICO_LOJA}};${{row.ESTQ_DISP_TOTAL_CD}};${{row.VDA_30D_VALOR}};${{row.DIAS_ESTOQUE_LOJA}};"${{row.STATUS_RUPTURA}}"\\n`;
            }});
            const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `nbo_export_${{new Date().toISOString().slice(0,10)}}.csv`;
            a.click();
        }}
    </script>
</body>
</html>
"""
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Dashboard HTML gerado com sucesso em: {html_file}")

if __name__ == '__main__':
    main()
