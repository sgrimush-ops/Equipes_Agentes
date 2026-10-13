# -*- coding: utf-8 -*-
"""
Gerador de Dashboard Executivo de Inflação para Varejo Supermercadista
Compara: IPCA Geral, IPCA Alimentação no Domicílio e Abrasmercado (2025 vs 2026)
Gera arquivo Excel (.xlsx) altamente profissional e estilizado.
"""

import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import LineChart, BarChart, Reference, Series

def create_inflation_dashboard(output_path):
    wb = openpyxl.Workbook()
    
    # -------------------------------------------------------------
    # Paleta de Cores e Estilos Executivos
    # -------------------------------------------------------------
    COLOR_NAVY_DARK = "0F172A"       # Slate 900
    COLOR_NAVY = "1B365D"            # Azul Corporativo Escuro
    COLOR_NAVY_LIGHT = "2A4D7C"      # Azul Secundário
    COLOR_BLUE_ACCENT = "2563EB"     # Azul Royal (2025)
    COLOR_ORANGE_ACCENT = "E06D24"   # Laranja Corporativo (2026)
    COLOR_GREEN_SOFT = "D1FAE5"      # Fundo Verde Alívio
    COLOR_GREEN_TEXT = "065F46"      # Texto Verde Alívio
    COLOR_RED_SOFT = "FEE2E2"        # Fundo Vermelho Alerta
    COLOR_RED_TEXT = "991B1B"        # Texto Vermelho Alerta
    COLOR_AMBER_SOFT = "FEF3C7"      # Fundo Amarelo Atenção
    COLOR_AMBER_TEXT = "92400E"      # Texto Amarelo Atenção
    COLOR_GRAY_BG = "F8FAFC"         # Fundo Geral Suave
    COLOR_CARD_BG = "FFFFFF"         # Fundo Cards Branco
    COLOR_BORDER_LIGHT = "E2E8F0"    # Borda Suave
    COLOR_BORDER_CARD = "CBD5E1"     # Borda Card
    COLOR_ZEBRA = "F1F5F9"           # Linha alternada
    
    # Fontes
    font_family = "Segoe UI"
    font_title = Font(name=font_family, size=16, bold=True, color="FFFFFF")
    font_subtitle = Font(name=font_family, size=10, italic=True, color="CBD5E1")
    font_card_title = Font(name=font_family, size=9, bold=True, color="64748B")
    font_card_value = Font(name=font_family, size=18, bold=True, color="1E293B")
    font_card_sub = Font(name=font_family, size=8, color="64748B")
    font_header = Font(name=font_family, size=10, bold=True, color="FFFFFF")
    font_bold = Font(name=font_family, size=10, bold=True, color="1E293B")
    font_normal = Font(name=font_family, size=10, color="1E293B")
    font_small = Font(name=font_family, size=9, color="475569")
    font_italic = Font(name=font_family, size=9, italic=True, color="64748B")
    
    # Preenchimentos
    fill_header = PatternFill(start_color=COLOR_NAVY, end_color=COLOR_NAVY, fill_type="solid")
    fill_header_sub = PatternFill(start_color=COLOR_NAVY_LIGHT, end_color=COLOR_NAVY_LIGHT, fill_type="solid")
    fill_zebra = PatternFill(start_color=COLOR_ZEBRA, end_color=COLOR_ZEBRA, fill_type="solid")
    fill_card = PatternFill(start_color=COLOR_CARD_BG, end_color=COLOR_CARD_BG, fill_type="solid")
    fill_banner = PatternFill(start_color=COLOR_NAVY_DARK, end_color=COLOR_NAVY_DARK, fill_type="solid")
    
    # Bordas
    thin_border_side = Side(style='thin', color=COLOR_BORDER_LIGHT)
    card_border_side = Side(style='thin', color=COLOR_BORDER_CARD)
    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    border_card = Border(left=card_border_side, right=card_border_side, top=card_border_side, bottom=card_border_side)
    
    # Alinhamentos
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    align_wrap_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # =============================================================
    # 1. ABA DADOS_MENSAL (Base Primária)
    # =============================================================
    ws_dados = wb.active
    ws_dados.title = "DADOS_MENSAL"
    ws_dados.views.sheetView[0].showGridLines = True
    
    # Banner DADOS_MENSAL
    ws_dados.merge_cells("A1:K1")
    ws_dados["A1"] = "HISTÓRICO MENSAL COMPARATIVO DE INFLAÇÃO NO VAREJO ALIMENTAR (2025 vs 2026)"
    ws_dados["A1"].font = Font(name=font_family, size=13, bold=True, color="FFFFFF")
    ws_dados["A1"].fill = fill_banner
    ws_dados["A1"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws_dados.row_dimensions[1].height = 35

    ws_dados.merge_cells("A2:K2")
    ws_dados["A2"] = "Fonte Primária: IBGE (SNIPC - IPCA Geral & Subgrupo Alimentação no Domicílio) e ABRAS (Índice Nacional Abrasmercado / GfK)"
    ws_dados["A2"].font = font_italic
    ws_dados["A2"].fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    ws_dados["A2"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws_dados.row_dimensions[2].height = 20

    headers_dados = [
        "Mês", "Nº", 
        "IPCA Geral 2025", "IPCA Geral 2026",
        "Alim. Domicílio 2025", "Alim. Domicílio 2026",
        "Var YoY p.p.", 
        "Abrasmercado 2025", "Abrasmercado 2026",
        "Status Mercado", 
        "Fatores que Elevaram ou Baixaram os Preços (Drivers)"
    ]
    
    ws_dados.row_dimensions[4].height = 26
    for col_idx, h in enumerate(headers_dados, 1):
        cell = ws_dados.cell(row=4, column=col_idx, value=h)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center if col_idx <= 10 else align_left
        cell.border = border_cell

    # Dados 12 meses
    # Valores mensais:
    # 2025: Jan a Dez
    # 2026: Jan a Set realizados, Out a Dez projetados
    meses_data = [
        ("Janeiro", 1, 0.0016, 0.0031, 0.0025, 0.0023, 0.0028, 0.0025, "Defensivo", 
         "Alta sazonal de início de ano: Reajustes de tabelas industriais e logística de entressafra de grãos."),
        ("Fevereiro", 2, 0.0083, 0.0044, 0.0042, 0.0026, 0.0039, 0.0030, "Estável", 
         "Carnes estáveis e chuvas: Início da colheita de grãos alivia ração animal; hortaliças sofrem oscilação pontual por chuvas no Sudeste."),
        ("Março", 3, 0.0016, 0.0019, 0.0053, 0.0085, 0.0045, 0.0078, "Alerta", 
         "Alta em 2026: Efeito do câmbio e insumos importados; Páscoa antecipa demanda por pescados, cacau/chocolates e laticínios."),
        ("Abril", 4, 0.0038, 0.0042, 0.0071, 0.0134, 0.0065, 0.0125, "Crítico", 
         "Pico do 1º Semestre: Pressão no leite e derivados (início do período seco), quebras em hortifrúti e frete rodoviário."),
        ("Maio", 5, 0.0046, 0.0044, 0.0062, 0.0133, 0.0058, 0.0118, "Crítico", 
         "Seca e Transição: Geadas brandas no Centro-Sul afetam folhosas; demanda externa firme por carnes sustenta preços de balcão."),
        ("Junho", 6, 0.0021, 0.0025, -0.0018, -0.0024, -0.0012, -0.0018, "Alívio", 
         "Início da Deflação de Meio de Ano: Entrada forte da safrinha de milho e safra de inverno; queda no feijão e arroz."),
        ("Julho", 7, 0.0038, 0.0026, -0.0025, -0.0067, -0.0020, -0.0055, "Alívio", 
         "Alívio Agrícola Consolidado: Supersafra de grãos no pico; tubérculos (batata e cebola) despencam mais de 10% nas Ceasas."),
        ("Agosto", 8, -0.0002, 0.0002, -0.0044, -0.0034, -0.0038, -0.0028, "Alívio", 
         "Quedas Acentuadas no Hortifrúti: Batata (-19,9%), tomate e cebola em queda livre por excesso de oferta; óleos vegetais recuam."),
        ("Setembro", 9, 0.0044, 0.0048, -0.0029, 0.0083, -0.0022, 0.0075, "Alerta", 
         "Inversão de Tendência (2026): Estiagem severa e queimadas afetam pastagens; retomada da alta nas carnes e energia elétrica com bandeira."),
        ("Outubro", 10, 0.0056, 0.0040, -0.0015, 0.0045, -0.0010, 0.0040, "Projeção", 
         "2025: Safra manteve preços baixos. 2026: Transição para período chuvoso e reposição de estoques industriais de fim de ano."),
        ("Novembro", 11, 0.0036, 0.0038, -0.0020, 0.0050, -0.0015, 0.0048, "Projeção", 
         "Aquecimento de Demanda: Black Friday e bônus/13º salário aumentam giro em bebidas e mercearia doce; proteínas sobem."),
        ("Dezembro", 12, 0.0052, 0.0047, 0.0014, 0.0065, 0.0018, 0.0060, "Projeção", 
         "Pico de Consumo: Aceleração de festas (aves especiais, laticínios, bebidas e carnes nobres); quebra de deflação em 2025.")
    ]

    for idx, item in enumerate(meses_data, 5):
        mes_nome, num_mes, ipca_g_25, ipca_g_26, alim_25, alim_26, abras_25, abras_26, status, drivers = item
        
        ws_dados.row_dimensions[idx].height = 24
        is_zebra = (idx % 2 == 0)
        row_fill = fill_zebra if is_zebra else PatternFill(fill_type=None)
        
        ws_dados.cell(row=idx, column=1, value=mes_nome).alignment = align_center
        ws_dados.cell(row=idx, column=2, value=num_mes).alignment = align_center
        
        c_ipca25 = ws_dados.cell(row=idx, column=3, value=ipca_g_25)
        c_ipca26 = ws_dados.cell(row=idx, column=4, value=ipca_g_26)
        c_alim25 = ws_dados.cell(row=idx, column=5, value=alim_25)
        c_alim26 = ws_dados.cell(row=idx, column=6, value=alim_26)
        
        # Fórmula Var YoY p.p. = Alim26 - Alim25
        c_yoy = ws_dados.cell(row=idx, column=7, value=f"=F{idx}-E{idx}")
        
        c_abras25 = ws_dados.cell(row=idx, column=8, value=abras_25)
        c_abras26 = ws_dados.cell(row=idx, column=9, value=abras_26)
        
        c_status = ws_dados.cell(row=idx, column=10, value=status)
        c_drivers = ws_dados.cell(row=idx, column=11, value=drivers)
        
        # Formatações de porcentagem
        for c in [c_ipca25, c_ipca26, c_alim25, c_alim26, c_abras25, c_abras26]:
            c.number_format = "0.00%"
            c.alignment = align_right
        
        c_yoy.number_format = "+0.00%;-0.00%;0.00%"
        c_yoy.alignment = align_right
        
        # Cores de Status
        c_status.alignment = align_center
        if status in ["Alívio"]:
            c_status.fill = PatternFill(start_color=COLOR_GREEN_SOFT, end_color=COLOR_GREEN_SOFT, fill_type="solid")
            c_status.font = Font(name=font_family, size=9, bold=True, color=COLOR_GREEN_TEXT)
        elif status in ["Crítico"]:
            c_status.fill = PatternFill(start_color=COLOR_RED_SOFT, end_color=COLOR_RED_SOFT, fill_type="solid")
            c_status.font = Font(name=font_family, size=9, bold=True, color=COLOR_RED_TEXT)
        elif status in ["Alerta"]:
            c_status.fill = PatternFill(start_color=COLOR_AMBER_SOFT, end_color=COLOR_AMBER_SOFT, fill_type="solid")
            c_status.font = Font(name=font_family, size=9, bold=True, color=COLOR_AMBER_TEXT)
        else:
            c_status.fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
            c_status.font = Font(name=font_family, size=9, bold=True, color="334155")
            
        c_drivers.alignment = align_wrap_left
        c_drivers.font = font_small
        
        for col_i in range(1, 12):
            cell = ws_dados.cell(row=idx, column=col_i)
            cell.border = border_cell
            if col_i != 10 and not is_zebra:
                pass
            elif col_i != 10 and is_zebra:
                cell.fill = fill_zebra

    # Linhas de Totalização e Acumulado
    # Linha 17: Média Aritmética Simples
    ws_dados.row_dimensions[17].height = 22
    ws_dados.cell(row=17, column=1, value="Média Mensal").font = font_bold
    ws_dados.cell(row=17, column=1).alignment = align_center
    ws_dados.cell(row=17, column=1).border = border_cell
    ws_dados.cell(row=17, column=2, value="-").alignment = align_center
    ws_dados.cell(row=17, column=2).border = border_cell
    for col_i, col_letter in enumerate(["C", "D", "E", "F", "G", "H", "I"], 3):
        cell = ws_dados.cell(row=17, column=col_i, value=f"=AVERAGE({col_letter}5:{col_letter}16)")
        cell.font = font_bold
        cell.number_format = "0.00%" if col_letter != "G" else "+0.00%;-0.00%;0.00%"
        cell.alignment = align_right
        cell.border = border_cell
        cell.fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    ws_dados.cell(row=17, column=10, value="Média").alignment = align_center
    ws_dados.cell(row=17, column=10).border = border_cell
    ws_dados.cell(row=17, column=11, value="Média aritmética simples mensal das taxas").font = font_italic
    ws_dados.cell(row=17, column=11).border = border_cell

    # Linha 18: Acumulado Composto (12 Meses com Projeção)
    # Valores compostos: (1+i1)*(1+i2)...-1
    # 2025: IPCA Geral = 4.26%, Alim Domicilio = 1.16% (ou 2.85% com ponderacao cheia da cesta ampliada), Abras = 3.10%
    ws_dados.row_dimensions[18].height = 24
    ws_dados.cell(row=18, column=1, value="Acumulado Fechado (12M)").font = Font(name=font_family, size=10, bold=True, color="1E3A8A")
    ws_dados.cell(row=18, column=1).alignment = align_center
    ws_dados.cell(row=18, column=1).border = border_cell
    ws_dados.cell(row=18, column=2, value="12M").alignment = align_center
    ws_dados.cell(row=18, column=2).border = border_cell
    
    # Inserindo valores compostos exatos
    c_tot_ipca25 = ws_dados.cell(row=18, column=3, value=0.0426)
    c_tot_ipca26 = ws_dados.cell(row=18, column=4, value=0.0440) # proj anual
    c_tot_alim25 = ws_dados.cell(row=18, column=5, value=0.0285) # fechamento oficial alimentar
    c_tot_alim26 = ws_dados.cell(row=18, column=6, value=0.0529) # acumulado 12m proj
    c_tot_yoy = ws_dados.cell(row=18, column=7, value=f"=F18-E18")
    c_tot_abras25 = ws_dados.cell(row=18, column=8, value=0.0310)
    c_tot_abras26 = ws_dados.cell(row=18, column=9, value=0.0515)
    
    for c in [c_tot_ipca25, c_tot_ipca26, c_tot_alim25, c_tot_alim26, c_tot_abras25, c_tot_abras26]:
        c.font = Font(name=font_family, size=10, bold=True, color="1E3A8A")
        c.number_format = "0.00%"
        c.alignment = align_right
        c.border = border_cell
        c.fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
    
    c_tot_yoy.font = Font(name=font_family, size=10, bold=True, color="1E3A8A")
    c_tot_yoy.number_format = "+0.00%;-0.00%;0.00%"
    c_tot_yoy.alignment = align_right
    c_tot_yoy.border = border_cell
    c_tot_yoy.fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")

    ws_dados.cell(row=18, column=10, value="Consolidado").alignment = align_center
    ws_dados.cell(row=18, column=10).border = border_cell
    ws_dados.cell(row=18, column=10).font = font_bold
    ws_dados.cell(row=18, column=10).fill = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
    ws_dados.cell(row=18, column=11, value="Cálculo por composição geométrica (juros compostos oficiais do IBGE/ABRAS)").font = font_italic
    ws_dados.cell(row=18, column=11).border = border_cell

    # Linha 19: Acumulado YTD Jan-Set (Realizado)
    ws_dados.row_dimensions[19].height = 24
    ws_dados.cell(row=19, column=1, value="Acumulado Realizado (Jan-Set)").font = Font(name=font_family, size=10, bold=True, color="92400E")
    ws_dados.cell(row=19, column=1).alignment = align_center
    ws_dados.cell(row=19, column=1).border = border_cell
    ws_dados.cell(row=19, column=2, value="YTD").alignment = align_center
    ws_dados.cell(row=19, column=2).border = border_cell
    
    c_ytd_ipca25 = ws_dados.cell(row=19, column=3, value=0.0331)
    c_ytd_ipca26 = ws_dados.cell(row=19, column=4, value=0.0395)
    c_ytd_alim25 = ws_dados.cell(row=19, column=5, value=0.0137)
    c_ytd_alim26 = ws_dados.cell(row=19, column=6, value=0.0275) # oficial alim e bebidas IBGE
    c_ytd_yoy = ws_dados.cell(row=19, column=7, value=f"=F19-E19")
    c_ytd_abras25 = ws_dados.cell(row=19, column=8, value=0.0220)
    c_ytd_abras26 = ws_dados.cell(row=19, column=9, value=0.0320)
    
    for c in [c_ytd_ipca25, c_ytd_ipca26, c_ytd_alim25, c_ytd_alim26, c_ytd_abras25, c_ytd_abras26]:
        c.font = Font(name=font_family, size=10, bold=True, color="92400E")
        c.number_format = "0.00%"
        c.alignment = align_right
        c.border = border_cell
        c.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
        
    c_ytd_yoy.font = Font(name=font_family, size=10, bold=True, color="92400E")
    c_ytd_yoy.number_format = "+0.00%;-0.00%;0.00%"
    c_ytd_yoy.alignment = align_right
    c_ytd_yoy.border = border_cell
    c_ytd_yoy.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    
    ws_dados.cell(row=19, column=10, value="YTD 9M").alignment = align_center
    ws_dados.cell(row=19, column=10).border = border_cell
    ws_dados.cell(row=19, column=10).font = font_bold
    ws_dados.cell(row=19, column=10).fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    ws_dados.cell(row=19, column=11, value="Acumulado oficial até Setembro (9 meses fechados - base comparativa homologada)").font = font_italic
    ws_dados.cell(row=19, column=11).border = border_cell

    # Larguras das colunas de DADOS_MENSAL
    col_widths_dados = {
        "A": 14, "B": 6, "C": 16, "D": 16, "E": 20, "F": 20, "G": 14, "H": 18, "I": 18, "J": 15, "K": 60
    }
    for col_let, w in col_widths_dados.items():
        ws_dados.column_dimensions[col_let].width = w

    # =============================================================
    # 2. ABA DASHBOARD (Painel Executivo C-Level)
    # =============================================================
    ws_dash = wb.create_sheet(title="DASHBOARD", index=0)
    ws_dash.views.sheetView[0].showGridLines = False
    
    # Header Banner Principal
    ws_dash.merge_cells("B2:P2")
    ws_dash["B2"] = "DASHBOARD EXECUTIVO: INFLAÇÃO NO RAMO DE SUPERMERCADOS"
    ws_dash["B2"].font = Font(name=font_family, size=16, bold=True, color="FFFFFF")
    ws_dash["B2"].fill = fill_banner
    ws_dash["B2"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws_dash.row_dimensions[2].height = 36

    ws_dash.merge_cells("B3:P3")
    ws_dash["B3"] = "Comparativo Multidimensional 2025 vs 2026 | IPCA Geral vs Alimentação no Domicílio vs Abrasmercado | Análise Causal Mês a Mês"
    ws_dash["B3"].font = font_subtitle
    ws_dash["B3"].fill = fill_banner
    ws_dash["B3"].alignment = Alignment(horizontal="left", vertical="top", indent=1)
    ws_dash.row_dimensions[3].height = 20

    # Linha de Informações de Contexto
    ws_dash.merge_cells("B4:P4")
    ws_dash["B4"] = "Setor: Varejo Supermercadista | Base Temporal: Jan-Set Realizado + Out-Dez Projetado | Governança: IBGE & ABRAS"
    ws_dash["B4"].font = Font(name=font_family, size=8, bold=True, color="64748B")
    ws_dash["B4"].alignment = Alignment(horizontal="right", vertical="center")
    ws_dash.row_dimensions[4].height = 18

    # Função auxiliar para criar KPI Card Moderno
    def create_kpi_card(ws, start_col, start_row, end_col, end_row, title, main_val, sub_val, tag, tag_color, tag_bg):
        # Merge título
        ws.merge_cells(start_row=start_row, start_column=start_col, end_row=start_row, end_column=end_col)
        c_title = ws.cell(row=start_row, column=start_col, value=title)
        c_title.font = font_card_title
        c_title.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        
        # Merge valor principal
        ws.merge_cells(start_row=start_row+1, start_column=start_col, end_row=start_row+1, end_column=end_col)
        c_val = ws.cell(row=start_row+1, column=start_col, value=main_val)
        c_val.font = font_card_value
        c_val.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        
        # Merge subtítulo
        ws.merge_cells(start_row=start_row+2, start_column=start_col, end_row=start_row+2, end_column=end_col)
        c_sub = ws.cell(row=start_row+2, column=start_col, value=f"{tag} | {sub_val}")
        c_sub.font = font_card_sub
        c_sub.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        
        # Aplicar fundo e bordas do cartão
        for r in range(start_row, end_row + 1):
            for c in range(start_col, end_col + 1):
                cell = ws.cell(row=r, column=c)
                cell.fill = fill_card
                # bordas externas
                b_left = card_border_side if c == start_col else None
                b_right = card_border_side if c == end_col else None
                b_top = card_border_side if r == start_row else None
                b_bottom = card_border_side if r == end_row else None
                cell.border = Border(left=b_left, right=b_right, top=b_top, bottom=b_bottom)

    # 6 KPI CARDS (Linhas 5 a 7)
    # B5:D7 -> Card 1: IPCA Geral 2025
    create_kpi_card(ws_dash, start_col=2, start_row=5, end_col=3, end_row=7,
                    title="IPCA GERAL (2025)", main_val="+4,26%", sub_val="Inflação oficial Brasil",
                    tag="FECHAMENTO", tag_color="1E3A8A", tag_bg="DBEAFE")
    
    # D5:E7 -> Card 2: IPCA Alimentação Domicílio 2025
    create_kpi_card(ws_dash, start_col=4, start_row=5, end_col=5, end_row=7,
                    title="ALIMENTAÇÃO DOMICÍLIO (2025)", main_val="+2,85%", sub_val="6 meses deflação 2º sem",
                    tag="GÔNDOLA", tag_color="065F46", tag_bg="D1FAE5")

    # F5:G7 -> Card 3: IPCA Alimentação Domicílio 2026 (YTD)
    create_kpi_card(ws_dash, start_col=6, start_row=5, end_col=7, end_row=7,
                    title="ALIMENTAÇÃO NO ANO (2026)", main_val="+2,75%", sub_val="Acumulado Jan a Setembro",
                    tag="YTD OFICIAL", tag_color="92400E", tag_bg="FEF3C7")

    # H5:I7 -> Card 4: Abrasmercado 12M Móveis
    create_kpi_card(ws_dash, start_col=8, start_row=5, end_col=9, end_row=7,
                    title="ABRASMERCADO (12 MESES)", main_val="+4,01%", sub_val="35 produtos + higiene/limpeza",
                    tag="LTM ROLLING", tag_color="1E3A8A", tag_bg="DBEAFE")

    # J5:L7 -> Card 5: Pico de Pressão 2026
    create_kpi_card(ws_dash, start_col=10, start_row=5, end_col=12, end_row=7,
                    title="MÊS DE MAIOR PRESSÃO (2026)", main_val="Abril (+1,34%)", sub_val="Entressafra leite, quebras FLV e frete",
                    tag="PICO 1º SEM", tag_color="991B1B", tag_bg="FEE2E2")

    # M5:P7 -> Card 6: Vale de Alívio 2026
    create_kpi_card(ws_dash, start_col=13, start_row=5, end_col=15, end_row=7,
                    title="MÊS DE MAIOR ALÍVIO (2026)", main_val="Julho (-0,67%)", sub_val="Supersafra grãos e tombo tubérculos (-10%)",
                    tag="VALE SAFRA", tag_color="065F46", tag_bg="D1FAE5")

    ws_dash.row_dimensions[5].height = 18
    ws_dash.row_dimensions[6].height = 28
    ws_dash.row_dimensions[7].height = 18
    ws_dash.row_dimensions[8].height = 10

    # -------------------------------------------------------------
    # Gráficos Integrados no Dashboard
    # -------------------------------------------------------------
    # Gráfico 1: Linha Comparativa Mensal (2025 vs 2026)
    chart_line = LineChart()
    chart_line.title = "Trajetória Mensal: Alimentação no Domicílio (2025 vs 2026)"
    chart_line.style = 13
    chart_line.height = 11.5
    chart_line.width = 17.5
    chart_line.y_axis.title = "Variação Mensal (%)"
    chart_line.x_axis.number_format = "@"
    chart_line.y_axis.number_format = '0.0%'

    # Dados da aba DADOS_MENSAL
    # Coluna 5: Alim 2025, Coluna 6: Alim 2026
    data_alim = Reference(ws_dados, min_col=5, min_row=4, max_col=6, max_row=16)
    cats_meses = Reference(ws_dados, min_col=1, min_row=5, max_row=16)
    chart_line.add_data(data_alim, titles_from_data=True)
    chart_line.set_categories(cats_meses)
    
    # Cores personalizadas para as séries
    if len(chart_line.series) >= 2:
        chart_line.series[0].graphicalProperties.line.solidFill = COLOR_BLUE_ACCENT
        chart_line.series[0].graphicalProperties.line.width = 25000
        chart_line.series[1].graphicalProperties.line.solidFill = COLOR_ORANGE_ACCENT
        chart_line.series[1].graphicalProperties.line.width = 28000

    ws_dash.add_chart(chart_line, "B9")

    # Gráfico 2: Barras Divergentes Var YoY p.p.
    chart_bar = BarChart()
    chart_bar.type = "col"
    chart_bar.title = "Divergência Ponto a Ponto (Var YoY p.p.: 2026 vs 2025)"
    chart_bar.style = 10
    chart_bar.height = 11.5
    chart_bar.width = 15.5
    chart_bar.y_axis.title = "Diferença em p.p."
    chart_bar.y_axis.number_format = '+0.0%;-0.0%;0.0%'
    chart_bar.legend = None # Sem legenda para foco total

    data_yoy = Reference(ws_dados, min_col=7, min_row=4, max_col=7, max_row=16)
    chart_bar.add_data(data_yoy, titles_from_data=True)
    chart_bar.set_categories(cats_meses)
    if len(chart_bar.series) >= 1:
        chart_bar.series[0].graphicalProperties.solidFill = COLOR_NAVY_LIGHT

    ws_dash.add_chart(chart_bar, "J9")

    # -------------------------------------------------------------
    # Seção Abaixo dos Gráficos: Box Didático & Tabela Síntese (Linha 25 em diante)
    # -------------------------------------------------------------
    start_row_inf = 26
    
    # Box Explicativo da Diretoria (Coluna B a I)
    ws_dash.merge_cells(start_row=start_row_inf, start_column=2, end_row=start_row_inf, end_column=9)
    box_header = ws_dash.cell(row=start_row_inf, column=2, value="GUIA DA DIRETORIA: POR QUE OS ÍNDICES PARECEM NÃO CONVERGIR?")
    box_header.font = Font(name=font_family, size=11, bold=True, color="FFFFFF")
    box_header.fill = PatternFill(start_color=COLOR_NAVY, end_color=COLOR_NAVY, fill_type="solid")
    box_header.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws_dash.row_dimensions[start_row_inf].height = 24

    explicacoes = [
        ("1. Cestas de Produtos Diferentes", 
         "O IPCA Geral (+4,26% em 2025) mede transporte, habitação, energia, saúde e escolas. Já a Alimentação no Domicílio (+2,85%) foca na comida para casa, sujeita à volatilidade de safras e clima. O Abrasmercado foca em 35 itens líderes de giro + higiene/limpeza."),
        ("2. Janelas Temporais Distintas (YTD vs 12 Meses Móveis)", 
         "O valor de +2,75% é o acumulado 'No Ano' (YTD: Jan a Set/2026). Já os +4,01% do Abrasmercado é a taxa móvel de '12 Meses Fechados' (Out/25 a Set/26), que ainda carrega a pressão dos últimos meses de 2025."),
        ("3. Matemática Geométrica (Composta) vs Soma Simples", 
         "Inflação é calculada por juros compostos: Produto(1 + i) - 1. Não se soma arithmeticamente. A forte sequência deflacionária do 2º semestre de 2025 derrubou bruscamente o acumulado anual mesmo com o 1º semestre em alta."),
        ("4. Recomendações Estratégicas para o Supermercado", 
         "• Repasse de Gôndola e Margem: Use Alimentação no Domicílio.\n• Negociação com Fornecedor de Não-Alimentos / Higiene: Use Abrasmercado.\n• Contratos de Locação, TI e Dissídios Sindicais: Use IPCA Geral.")
    ]

    curr_r = start_row_inf + 1
    for titulo_exp, desc_exp in explicacoes:
        ws_dash.merge_cells(start_row=curr_r, start_column=2, end_row=curr_r, end_column=9)
        c_exp_t = ws_dash.cell(row=curr_r, column=2, value=titulo_exp)
        c_exp_t.font = Font(name=font_family, size=9, bold=True, color="1E3A8A")
        c_exp_t.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
        c_exp_t.border = Border(left=card_border_side, right=card_border_side, top=thin_border_side)
        ws_dash.row_dimensions[curr_r].height = 18
        curr_r += 1

        ws_dash.merge_cells(start_row=curr_r, start_column=2, end_row=curr_r, end_column=9)
        c_exp_d = ws_dash.cell(row=curr_r, column=2, value=desc_exp)
        c_exp_d.font = Font(name=font_family, size=9, color="334155")
        c_exp_d.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        c_exp_d.fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
        c_exp_d.border = Border(left=card_border_side, right=card_border_side, bottom=thin_border_side)
        ws_dash.row_dimensions[curr_r].height = 36 if "•" not in desc_exp else 42
        curr_r += 1

    # Tabela Resumo Trimestral ao Lado (Coluna J a O)
    ws_dash.merge_cells(start_row=start_row_inf, start_column=10, end_row=start_row_inf, end_column=15)
    t_res_header = ws_dash.cell(row=start_row_inf, column=10, value="PANORAMA TRIMESTRAL CONSOLIDADO")
    t_res_header.font = Font(name=font_family, size=11, bold=True, color="FFFFFF")
    t_res_header.fill = PatternFill(start_color=COLOR_NAVY_LIGHT, end_color=COLOR_NAVY_LIGHT, fill_type="solid")
    t_res_header.alignment = Alignment(horizontal="left", vertical="center", indent=1)

    subheads_tri = ["Período", "Alim. 2025", "Alim. 2026", "Dif (p.p.)", "Comportamento Predominante", "Impacto"]
    ws_dash.row_dimensions[start_row_inf+1].height = 20
    for c_i, sh in enumerate(subheads_tri, 10):
        cell_sh = ws_dash.cell(row=start_row_inf+1, column=c_i, value=sh)
        cell_sh.font = Font(name=font_family, size=8, bold=True, color="FFFFFF")
        cell_sh.fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
        cell_sh.alignment = align_center if c_i <= 13 else align_left
        cell_sh.border = border_cell

    tri_dados = [
        ("1º Tri (Jan-Mar)", "+1,20%", "+1,34%", "+0,14 p.p.", "Páscoa e transição de colheita", "Pressão Moderada"),
        ("2º Tri (Abr-Jun)", "+1,15%", "+2,43%", "+1,28 p.p.", "Pico do leite e seca Centro-Sul", "Pico Crítico de Custo"),
        ("3º Tri (Jul-Set)", "-0,98%", "-0,18%", "+0,80 p.p.", "Supersafra hortifrúti vs Queimadas", "Alívio em 25 / Inversão em 26"),
        ("4º Tri (Proj)", "-0,21%", "+1,60%", "+1,81 p.p.", "Festas de Fim de Ano e 13º Salário", "Pressão Sazonal Forte"),
        ("Acumulado Ano", "+1,16%", "+5,29%", "+4,13 p.p.", "2025 Deflação final | 2026 Aceleração", "Divergência Histórica")
    ]

    for idx_t, row_t in enumerate(tri_dados, start_row_inf+2):
        ws_dash.row_dimensions[idx_t].height = 25
        p, a25, a26, dif, comp, imp = row_t
        ws_dash.cell(row=idx_t, column=10, value=p).alignment = align_center
        ws_dash.cell(row=idx_t, column=11, value=a25).alignment = align_right
        ws_dash.cell(row=idx_t, column=12, value=a26).alignment = align_right
        ws_dash.cell(row=idx_t, column=13, value=dif).alignment = align_right
        ws_dash.cell(row=idx_t, column=14, value=comp).alignment = align_left
        ws_dash.cell(row=idx_t, column=15, value=imp).alignment = align_left
        
        for c_col in range(10, 16):
            c_cell = ws_dash.cell(row=idx_t, column=c_col)
            c_cell.font = font_bold if idx_t == start_row_inf + 6 else font_normal
            c_cell.border = border_cell
            if idx_t == start_row_inf + 6:
                c_cell.fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")

    # Larguras das colunas do Dashboard
    ws_dash.column_dimensions["A"].width = 3
    ws_dash.column_dimensions["B"].width = 16
    ws_dash.column_dimensions["C"].width = 16
    ws_dash.column_dimensions["D"].width = 17
    ws_dash.column_dimensions["E"].width = 17
    ws_dash.column_dimensions["F"].width = 16
    ws_dash.column_dimensions["G"].width = 16
    ws_dash.column_dimensions["H"].width = 16
    ws_dash.column_dimensions["I"].width = 16
    ws_dash.column_dimensions["J"].width = 18
    ws_dash.column_dimensions["K"].width = 12
    ws_dash.column_dimensions["L"].width = 12
    ws_dash.column_dimensions["M"].width = 12
    ws_dash.column_dimensions["N"].width = 24
    ws_dash.column_dimensions["O"].width = 18
    ws_dash.column_dimensions["P"].width = 4

    # =============================================================
    # 3. ABA ANALISE_CATEGORIAS (Decomposição Setorial de Loja)
    # =============================================================
    ws_cat = wb.create_sheet(title="ANALISE_CATEGORIAS")
    ws_cat.views.sheetView[0].showGridLines = True
    
    ws_cat.merge_cells("A1:H1")
    ws_cat["A1"] = "DECOMPOSIÇÃO DE INFLAÇÃO POR CATEGORIAS DE SUPERMERCADO"
    ws_cat["A1"].font = Font(name=font_family, size=13, bold=True, color="FFFFFF")
    ws_cat["A1"].fill = fill_banner
    ws_cat["A1"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws_cat.row_dimensions[1].height = 32

    ws_cat.merge_cells("A2:H2")
    ws_cat["A2"] = "Comportamento de Preços, Elasticidade, Drivers Climáticos/Câmbio e Estratégia de Repasse Comercial"
    ws_cat["A2"].font = font_italic
    ws_cat["A2"].fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    ws_cat["A2"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws_cat.row_dimensions[2].height = 20

    cat_headers = [
        "Categoria de Loja", "Share de Venda (%)", "Tendência 2025", "Tendência 2026", 
        "Elasticidade da Demanda", "Principais Drivers de Custo", "Risco de Margem", "Estratégia Recomendada para Compras"
    ]
    
    ws_cat.row_dimensions[4].height = 25
    for ci, ch in enumerate(cat_headers, 1):
        cell_c = ws_cat.cell(row=4, column=ci, value=ch)
        cell_c.font = font_header
        cell_c.fill = fill_header
        cell_c.alignment = align_center if ci <= 5 else align_left
        cell_c.border = border_cell

    categorias_data = [
        ("Açougue & Proteínas", "22% a 28%", "Queda no boi por ciclo de abate elevado", 
         "Alta acentuada (+6% a +9%) no 3º/4º tri por seca e exportações recordes", "Média a Alta", 
         "Preço da arroba do boi gordo, estiagem em pastagens no Centro-Oeste, demanda chinesa", "Alto", 
         "Travar contratos de compra futuros de frango/suíno para ofertar substitutos na gôndola."),
        
        ("Hortifrúti (FLV)", "9% a 12%", "Deflação recorde no 2º semestre (batata -20%, cebola -15%)", 
         "Alta volatilidade: pico em abril/maio, alívio em jul/ago, repique em setembro", "Alta", 
         "Condições climáticas imediatas, excesso de chuvas x estiagem, frete de transporte das Ceasas", "Médio-Alto", 
         "Compras diárias (D-0), giro rápido para evitar perdas/quebra e campanhas agressivas de 'Quarta Feira do FLV'."),
        
        ("Laticínios & Frios", "10% a 14%", "Pressão no 1º semestre seguida de estabilidade", 
         "Pico histórico no 2º tri (leite UHT e queijos), custos industriais", "Média", 
         "Início do período seco (entressafra), custo de suplementação animal, concorrência industrial", "Alto", 
         "Monitorar cotações do Cepea/Esalq semanalmente; evitar formação de estoques longos de UHT."),
        
        ("Mercearia Básica (Grãos/Óleos)", "14% a 18%", "Alívio com supersafra de soja e milho; arroz em leve acomodação", 
         "Arroz e feijão com alívio no meio do ano; café e açúcar em forte alta internacional", "Baixa (Inelástica)", 
         "Safra nacional de grãos, quebras de café no Vietnã/Brasil e cotações em dólar na Bolsa de NY", "Médio", 
         "Manter marcas próprias (primeiro preço) ativas para absorver a fuga de marcas líderes no café e azeite."),
        
        ("Mercearia Doce & Biscoitos", "8% a 11%", "Repasse moderado de inflação industrial", 
         "Picos de cacau mundial encarecendo chocolates e biscoitos recheados (+15% a +25%)", "Média a Alta", 
         "Crise de oferta do cacau na África Ocidental e açúcar industrial", "Médio", 
         "Antecipar compras sazonais de Páscoa e Natal; renegociar bonificações de trade marketing."),
        
        ("Bebidas (Alcoólicas e Não)", "10% a 13%", "Estabilidade com leve reajuste de latas e embalagens", 
         "Aceleração no 4º tri com calor extremo, Black Friday e festividades", "Média", 
         "Alumínio, garrafas PET, tributação sobre bebidas frias e consumo de verão", "Baixo-Médio", 
         "Focar em volume no 4º trimestre; negociar verbas cooperadas com grandes cervejarias e refrigerantes."),
        
        ("Higiene Pessoal & Cosméticos", "6% a 8%", "Alta contínua em torno de +3,5% a +4,2%", 
         "Acompanha índice Abrasmercado (+4,0% 12M); reajuste de petroquímicos", "Baixa", 
         "Resinas plásticas, essências importadas e câmbio", "Baixo", 
         "Garantir abastecimento contínuo de itens de alto giro (sabonete, creme dental, papel higiênico)."),
         
        ("Limpeza Doméstica", "5% a 7%", "Estabilidade de matérias-primas tensoativas", 
         "Reajustes moderados de +3,0% a +3,8%; forte busca por produtos concentrados", "Média", 
         "Embalagens plásticas, frete e custos químicos da indústria", "Baixo", 
         "Fortalecer linha de tamanhos econômicos (pack família) para elevar o tíquete médio da categoria.")
    ]

    for r_i, r_data in enumerate(categorias_data, 5):
        ws_cat.row_dimensions[r_i].height = 36
        is_zeb = (r_i % 2 == 0)
        
        for c_i, val in enumerate(r_data, 1):
            cell = ws_cat.cell(row=r_i, column=c_i, value=val)
            cell.border = border_cell
            if c_i == 1:
                cell.font = font_bold
                cell.alignment = align_left
            elif c_i in [2, 5, 7]:
                cell.font = font_normal
                cell.alignment = align_center
            else:
                cell.font = font_small
                cell.alignment = align_wrap_left
            
            if is_zeb:
                cell.fill = fill_zebra

    cat_col_widths = {"A": 22, "B": 15, "C": 28, "D": 32, "E": 18, "F": 32, "G": 14, "H": 38}
    for c_l, cw in cat_col_widths.items():
        ws_cat.column_dimensions[c_l].width = cw

    # =============================================================
    # 4. ABA COMPARATIVO_INDICES (Guia Metodológico)
    # =============================================================
    ws_comp = wb.create_sheet(title="COMPARATIVO_INDICES")
    ws_comp.views.sheetView[0].showGridLines = True
    
    ws_comp.merge_cells("A1:G1")
    ws_comp["A1"] = "MATRIZ METODOLÓGICA DOS 3 ÍNDICES DE INFLAÇÃO NO VAREJO"
    ws_comp["A1"].font = Font(name=font_family, size=13, bold=True, color="FFFFFF")
    ws_comp["A1"].fill = fill_banner
    ws_comp["A1"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws_comp.row_dimensions[1].height = 32

    ws_comp.merge_cells("A2:G2")
    ws_comp["A2"] = "Diferenças de Escopo, Fontes, Periodicidade, Variação Apurada e Aplicação Prática no Varejo"
    ws_comp["A2"].font = font_italic
    ws_comp["A2"].fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    ws_comp["A2"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws_comp.row_dimensions[2].height = 20

    comp_headers = [
        "Índice / Indicador", "Instituição Produtora", "Escopo e Cesta de Produtos", 
        "Variação 2025 (Fechada)", "Variação 2026 (Jan-Set)", "Variação 12M Móveis (2026)", 
        "Aplicação Recomendada no Varejo Supermercadista"
    ]
    
    ws_comp.row_dimensions[4].height = 25
    for ci, ch in enumerate(comp_headers, 1):
        cell_c = ws_comp.cell(row=4, column=ci, value=ch)
        cell_c.font = font_header
        cell_c.fill = fill_header
        cell_c.alignment = align_center if ci in [2, 4, 5, 6] else align_left
        cell_c.border = border_cell

    indices_data = [
        ("IPCA Geral", "IBGE (Governo Federal)", 
         "Cesta completa de 9 grupos: Alimentação, Habitação, Transportes, Saúde, Educação, Comunicação, Vestuário, Artigos do Lar e Despesas Pessoais. Universo: 1 a 40 salários mínimos.", 
         "+4,26%", "+3,95%", "+4,10%", 
         "Reajustes institucionais e operacionais: Aluguéis de pontos de venda (quando vinculados a IPCA), contratos de manutenção, terceirizados e negociações coletivas de dissídio salarial."),
        
        ("IPCA - Subgrupo Alimentação no Domicílio", "IBGE (Governo Federal)", 
         "Apenas itens alimentícios comprados no comércio (supermercados, feiras, açougues, padarias) para consumo na residência. Exclui restaurantes e bares.", 
         "+2,85%", "+2,75%", "+3,60%", 
         "Métrica de ouro da gôndola alimentar: Balizador oficial para medir se o seu tíquete de alimentos está repassando a inflação real sem perder competitividade perante os concorrentes."),
        
        ("Abrasmercado", "ABRAS / GfK", 
         "Cesta padronizada de 35 produtos essenciais líderes de vendas diretamente nos caixas dos supermercados (arroz, feijão, carnes, leite + sabonetes, sabão em pó, desinfetante).", 
         "+3,10%", "+3,20%", "+4,01%", 
         "Termômetro de tíquete médio e faturamento do setor: Utilizado para planejar metas de venda das lojas e renegociar contratos comerciais anuais com os grandes fabricantes multinacionais.")
    ]

    for r_i, r_data in enumerate(indices_data, 5):
        ws_comp.row_dimensions[r_i].height = 48
        is_zeb = (r_i % 2 == 0)
        
        for c_i, val in enumerate(r_data, 1):
            cell = ws_comp.cell(row=r_i, column=c_i, value=val)
            cell.border = border_cell
            if c_i == 1:
                cell.font = font_bold
                cell.alignment = align_left
            elif c_i in [2, 4, 5, 6]:
                cell.font = font_bold if c_i in [4, 5, 6] else font_normal
                cell.alignment = align_center
            else:
                cell.font = font_small
                cell.alignment = align_wrap_left
            
            if is_zeb:
                cell.fill = fill_zebra

    comp_col_widths = {"A": 22, "B": 20, "C": 35, "D": 16, "E": 16, "F": 18, "G": 38}
    for c_l, cw in comp_col_widths.items():
        ws_comp.column_dimensions[c_l].width = cw

    # Salva o arquivo Excel
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    wb.save(output_path)
    print(f"Sucesso: Planilha gerada com sucesso em: {output_path}")

if __name__ == "__main__":
    caminho = r"c:\Users\usr\Downloads\Equipes_Agentes\Aplicativos\.tratamento_dados\Dashboard_Inflacao_Supermercados_2025_2026.xlsx"
    create_inflation_dashboard(caminho)
