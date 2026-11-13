import os
import sys
from pathlib import Path
import pandas as pd

# Ajuste de encoding para o terminal Windows
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if stream and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass


def localizar_arquivo_origem(base_dir: Path) -> Path:
    """Localiza o arquivo rankeador_abc_produtos.txt na pasta import_querys ou local."""
    candidatos = [
        base_dir.parent / "import_querys" / "rankeador_abc_produtos.txt",
        base_dir / "rankeador_abc_produtos.txt",
        base_dir.parent.parent / "Aplicativos" / "import_querys" / "rankeador_abc_produtos.txt",
    ]
    for c in candidatos:
        if c.exists():
            return c.resolve()

    raise FileNotFoundError(
        f"Arquivo 'rankeador_abc_produtos.txt' não encontrado. Locais verificados: {[str(c) for c in candidatos]}"
    )


def carregar_txt(caminho_txt: Path) -> pd.DataFrame:
    """Carrega o arquivo TXT tentando codificações comuns do ambiente Consinco/Windows."""
    for enc in ("utf-8-sig", "cp1252", "latin1"):
        try:
            df = pd.read_csv(caminho_txt, sep=";", encoding=enc, dtype=str, low_memory=False)
            print(f"[INFO] Arquivo lido com sucesso ({enc}): {caminho_txt}")
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Não foi possível decodificar o arquivo: {caminho_txt}")


def tratar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Limpa textos e converte colunas numéricas e monetárias para tipos nativos."""
    df = df.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]

    # Limpeza de colunas de texto
    cols_texto = ["COMPRADOR", "DEPARTAMENTO", "SUBGRUPO", "DESCRICAO", "STATUS_COMPRA", "RANK"]
    for col in cols_texto:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    # Conversão de código inteiro
    if "SEQCODIGO" in df.columns:
        df["SEQCODIGO"] = (
            pd.to_numeric(df["SEQCODIGO"].astype(str).str.strip(), errors="coerce")
            .fillna(0)
            .astype("int64")
        )

    # Conversão de colunas decimais (padrão Pt-BR com vírgula)
    cols_decimais = ["VALOR_VENDIDO", "PERC_PARTICIPACAO", "PERC_ACUMULADO"]
    for col in cols_decimais:
        if col in df.columns:
            s_clean = (
                df[col]
                .astype(str)
                .str.strip()
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            df[col] = pd.to_numeric(s_clean, errors="coerce").fillna(0.0).astype("float64")

    return df


def exportar_excel_profissional(df: pd.DataFrame, caminho_excel: Path) -> None:
    """Gera arquivo Excel com formatação profissional, filtros e cabeçalho congelado."""
    with pd.ExcelWriter(caminho_excel, engine="xlsxwriter") as writer:
        nome_aba = "Ranking ABC"
        df.to_excel(writer, sheet_name=nome_aba, index=False, header=False, startrow=1)

        workbook = writer.book
        worksheet = writer.sheets[nome_aba]

        # Estilos corporativos
        fmt_header = workbook.add_format({
            "bold": True,
            "font_name": "Segoe UI",
            "font_size": 10,
            "bg_color": "#1B365D",
            "font_color": "#FFFFFF",
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "border_color": "#1B365D",
        })

        fmt_texto_esq = workbook.add_format({
            "font_name": "Segoe UI",
            "font_size": 9,
            "align": "left",
            "valign": "vcenter",
            "border": 1,
            "border_color": "#D3D3D3",
        })

        fmt_texto_centro = workbook.add_format({
            "font_name": "Segoe UI",
            "font_size": 9,
            "align": "center",
            "valign": "vcenter",
            "border": 1,
            "border_color": "#D3D3D3",
        })

        fmt_inteiro = workbook.add_format({
            "font_name": "Segoe UI",
            "font_size": 9,
            "align": "center",
            "valign": "vcenter",
            "num_format": "#,##0",
            "border": 1,
            "border_color": "#D3D3D3",
        })

        fmt_moeda = workbook.add_format({
            "font_name": "Segoe UI",
            "font_size": 9,
            "align": "right",
            "valign": "vcenter",
            "num_format": "R$ #,##0.00",
            "border": 1,
            "border_color": "#D3D3D3",
        })

        fmt_percentual = workbook.add_format({
            "font_name": "Segoe UI",
            "font_size": 9,
            "align": "right",
            "valign": "vcenter",
            "num_format": "0.00",
            "border": 1,
            "border_color": "#D3D3D3",
        })

        # Escrever cabeçalho na linha 0
        worksheet.set_row(0, 26)
        for col_idx, col_name in enumerate(df.columns):
            worksheet.write(0, col_idx, col_name, fmt_header)

        # Ajustar largura e formatação por coluna
        for col_idx, col_name in enumerate(df.columns):
            max_data_len = 0
            if len(df) > 0:
                if col_name == "VALOR_VENDIDO":
                    max_data_len = 16
                elif col_name in ("PERC_PARTICIPACAO", "PERC_ACUMULADO"):
                    max_data_len = 10
                else:
                    max_data_len = int(df[col_name].astype(str).map(len).max())

            largura = min(max(max_data_len + 3, len(col_name) + 5, 12), 50)

            if col_name == "SEQCODIGO":
                worksheet.set_column(col_idx, col_idx, largura, fmt_inteiro)
            elif col_name == "VALOR_VENDIDO":
                worksheet.set_column(col_idx, col_idx, largura, fmt_moeda)
            elif col_name in ("PERC_PARTICIPACAO", "PERC_ACUMULADO"):
                worksheet.set_column(col_idx, col_idx, largura, fmt_percentual)
            elif col_name in ("STATUS_COMPRA", "RANK"):
                worksheet.set_column(col_idx, col_idx, largura, fmt_texto_centro)
            else:
                worksheet.set_column(col_idx, col_idx, largura, fmt_texto_esq)

        # Ativar filtro em todas as colunas e congelar primeira linha (cabeçalho)
        if len(df) > 0:
            worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
        worksheet.freeze_panes(1, 0)


def executar_conversao() -> None:
    dir_destino = Path(__file__).parent.resolve()
    dir_destino.mkdir(parents=True, exist_ok=True)

    caminho_txt = localizar_arquivo_origem(dir_destino)
    caminho_parquet = dir_destino / "rankeador_abc_produtos.parquet"
    caminho_excel = dir_destino / "rankeador_abc_produtos.xlsx"

    # 1. Leitura e saneamento
    df_bruto = carregar_txt(caminho_txt)
    df_limpo = tratar_dados(df_bruto)

    # 2. Exportação para Parquet
    print(f"[INFO] Gerando Parquet: {caminho_parquet}")
    df_limpo.to_parquet(caminho_parquet, index=False)

    # 3. Exportação para Excel formatado
    print(f"[INFO] Gerando Excel formatado: {caminho_excel}")
    exportar_excel_profissional(df_limpo, caminho_excel)

    # 4. Validação de integridade
    df_check_pq = pd.read_parquet(caminho_parquet)
    print("\n" + "=" * 65)
    print("[SUCESSO] CONVERSÃO DO RANKING ABC CONCLUÍDA!")
    print(f"  -> Origem TXT : {caminho_txt} ({len(df_bruto)} linhas)")
    print(f"  -> Parquet    : {caminho_parquet} ({df_check_pq.shape[0]} linhas x {df_check_pq.shape[1]} colunas)")
    print(f"  -> Excel      : {caminho_excel} ({len(df_limpo)} linhas x {len(df_limpo.columns)} colunas)")
    print("=" * 65)


if __name__ == "__main__":
    executar_conversao()

