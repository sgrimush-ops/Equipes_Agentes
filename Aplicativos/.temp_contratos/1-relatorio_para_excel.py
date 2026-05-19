from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RELATORIO_DIR = BASE_DIR / "relatorio"
OUTPUT_DIR = BASE_DIR / "saida"
INPUT_PATH = RELATORIO_DIR / "contas_a_receber.txt"
OUTPUT_XLSX = OUTPUT_DIR / "contas_a_receber_convertido.xlsx"
OUTPUT_JSON = OUTPUT_DIR / "contas_a_receber_resumo_fornecedor.json"

NUMERIC_COLUMNS = [
    "dias_de_atraso",
    "multa",
    "juros",
    "percentual_desc_financeiro",
    "percentual_desc_acordo",
    "desconto",
    "taxa_adm",
    "vlr_original",
    "valor_aberto",
    "valor_liquido",
]

DATE_COLUMNS = [
    "dt_emissao",
    "dt_movimento",
    "vencimento_programado",
]

DROP_COLUMNS = {
    "a",
    "p",
}


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.lower()
    return re.sub(r"[^a-z0-9]+", "_", ascii_value).strip("_")


def normalize_header(value: str) -> str:
    value = value.strip()
    replacements = {
        "%": "percentual",
        ".": " ",
        "/": " ",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return slugify(value)


def normalize_supplier_name(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def build_supplier_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_value = ascii_value.upper()
    ascii_value = re.sub(r"\b(LTDA|S/A|SA|ME|EPP|EIRELI)\b", " ", ascii_value)
    ascii_value = re.sub(r"[^A-Z0-9]+", " ", ascii_value)
    ascii_value = re.sub(r"\s+", " ", ascii_value).strip()
    return ascii_value


def split_supplier(value: str) -> tuple[str, str]:
    match = re.match(r"\s*(\d+)\s*-\s*(.+?)\s*$", value)
    if not match:
        cleaned = normalize_supplier_name(value)
        return "", cleaned
    return match.group(1), normalize_supplier_name(match.group(2))


def read_report(path: Path) -> pd.DataFrame:
    with path.open("r", encoding="cp1252", newline="") as handle:
        reader = csv.reader(handle, delimiter=";")
        rows = list(reader)

    if not rows:
        return pd.DataFrame()

    header = rows[0]
    while header and not header[-1].strip():
        header.pop()

    normalized_headers = [normalize_header(column) for column in header]
    records: list[list[str]] = []
    for row in rows[1:]:
        if not any(cell.strip() for cell in row):
            continue

        if len(row) < len(normalized_headers):
            row = row + [""] * (len(normalized_headers) - len(row))
        elif len(row) > len(normalized_headers):
            row = row[: len(normalized_headers)]

        records.append(row)

    dataframe = pd.DataFrame(records, columns=normalized_headers)
    dataframe = dataframe.fillna("")
    dataframe = dataframe.drop(
        columns=[
            column for column in dataframe.columns
            if column in DROP_COLUMNS
        ],
        errors="ignore",
    )
    dataframe = dataframe.loc[
        :,
        [
            column for column in dataframe.columns
            if (dataframe[column].astype(str).str.strip() != "").any()
        ],
    ]
    return dataframe


def convert_numeric(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .replace("", "0")
    )
    return pd.to_numeric(cleaned, errors="coerce").fillna(0.0)


def prepare_detail(dataframe: pd.DataFrame) -> pd.DataFrame:
    detail = dataframe.copy()
    detail[["codigo_pessoa", "fornecedor_relatorio"]] = detail["pessoa"].apply(
        lambda value: pd.Series(split_supplier(value))
    )
    detail = detail.drop(columns=["pessoa"], errors="ignore")

    ordered_front = ["codigo_pessoa", "fornecedor_relatorio"]
    remaining = [
        column for column in detail.columns if column not in ordered_front
    ]
    detail = detail[ordered_front + remaining]

    for column in NUMERIC_COLUMNS:
        if column in detail.columns:
            detail[column] = convert_numeric(detail[column])

    for column in DATE_COLUMNS:
        if column in detail.columns:
            detail[column] = pd.to_datetime(
                detail[column],
                format="%d/%m/%Y",
                errors="coerce",
            )

    return detail


def build_supplier_summary(detail: pd.DataFrame) -> pd.DataFrame:
    aggregations: dict[str, tuple[str, str]] = {
        "quantidade_titulos": ("fornecedor_relatorio", "size"),
        "valor_original_total": ("vlr_original", "sum"),
        "valor_aberto_total": ("valor_aberto", "sum"),
        "dias_de_atraso": ("dias_de_atraso", "max"),
    }
    if "valor_liquido" in detail.columns:
        aggregations["valor_liquido_total"] = ("valor_liquido", "sum")
    if "vencimento_programado" in detail.columns:
        aggregations["primeiro_vencimento"] = (
            "vencimento_programado",
            "min",
        )
        aggregations["ultimo_vencimento"] = (
            "vencimento_programado",
            "max",
        )

    summary = detail.groupby(
        ["codigo_pessoa", "fornecedor_relatorio"],
        dropna=False,
        as_index=False,
    ).agg(**aggregations)
    summary = summary.sort_values(
        ["valor_aberto_total", "fornecedor_relatorio"],
        ascending=[False, True],
    )
    return summary


def build_contract_lookup(summary: pd.DataFrame) -> pd.DataFrame:
    amount_column = (
        "valor_liquido_total"
        if "valor_liquido_total" in summary.columns
        else "valor_aberto_total"
    )
    lookup = summary[[
        "codigo_pessoa",
        "fornecedor_relatorio",
        "dias_de_atraso",
        amount_column,
    ]].copy()
    lookup = lookup.rename(
        columns={
            "fornecedor_relatorio": "fornecedor_relatorio_receber",
            "valor_liquido_total": "a_receber",
            "valor_aberto_total": "a_receber",
        }
    )
    return lookup


def apply_date_format(worksheet, dataframe: pd.DataFrame) -> None:
    for column_name in DATE_COLUMNS:
        if column_name not in dataframe.columns:
            continue
        column_index = dataframe.columns.get_loc(column_name) + 1
        for row_index in range(2, len(dataframe) + 2):
            cell = worksheet.cell(row=row_index, column=column_index)
            cell.number_format = "d/m/yyyy"


def write_outputs(
    detail: pd.DataFrame,
    summary: pd.DataFrame,
    lookup: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    detail = detail.fillna("")
    summary = summary.fillna("")
    lookup = lookup.fillna("")
    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        detail.to_excel(writer, sheet_name="detalhe", index=False)
        summary.to_excel(writer, sheet_name="resumo_fornecedor", index=False)
        lookup.to_excel(writer, sheet_name="para_contratos", index=False)
        apply_date_format(writer.sheets["detalhe"], detail)
        apply_date_format(writer.sheets["resumo_fornecedor"], summary)

    OUTPUT_JSON.write_text(
        lookup.to_json(orient="records", force_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {INPUT_PATH}")

    dataframe = read_report(INPUT_PATH)
    detail = prepare_detail(dataframe)
    summary = build_supplier_summary(detail)
    lookup = build_contract_lookup(summary)
    write_outputs(detail, summary, lookup)

    print(f"Linhas detalhadas: {len(detail)}")
    print(f"Fornecedores resumidos: {len(summary)}")
    print(f"Excel gerado em: {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
