from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PDFS_MODULE_PATH = BASE_DIR / "pdfs.py"
PENDING_MODULE_PATH = BASE_DIR / "processar_pdfs_pendentes.py"


def load_module(module_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Substitui placeholders e preenche PDFs faltantes com extração "
            "real, salvando a base consolidada ao longo do processo."
        ),
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=0,
        help=(
            "Limita quantos PDFs pendentes reais serao processados nesta "
            "rodada."
        ),
    )
    parser.add_argument(
        "--salvar-a-cada",
        type=int,
        default=10,
        help="Salva checkpoint e consolidado a cada N PDFs processados.",
    )
    parser.add_argument(
        "--forcar-ultima-pagina",
        action="store_true",
        help="Sempre extrai tambem a ultima pagina, sem usar o modo rapido.",
    )
    parser.add_argument(
        "--modo-alvo",
        choices=["todos", "faltantes", "placeholders"],
        default="todos",
        help="Define se processa faltantes, placeholders ou ambos.",
    )
    return parser.parse_args()


def should_retry_full(record: dict[str, object]) -> bool:
    line_count = int(record.get("linhas_extraidas_pagina_1") or 0)
    no_layout = str(record.get("layout_tipo", "")) == "NAO_IDENTIFICADO"
    empty_core = all(
        record.get(field) in (None, "")
        for field in [
            "cnpj",
            "data_assinatura",
            "forma_pagamento",
            "bonus_percentual",
            "politica_trocas",
        ]
    )
    return no_layout and empty_core and line_count <= 8


def build_target_list(
    pdf_mod,
    pending_mod,
    records: list[dict[str, object]],
    target_mode: str,
) -> list[Path]:
    by_file = {
        str(record.get("arquivo_pdf", "")): record
        for record in records
        if record.get("arquivo_pdf")
    }
    priority_items = pending_mod.load_priority_items(
        pending_mod.DEFAULT_PRIORITY_PATH,
    )
    all_pdfs = pdf_mod.list_pdf_files()
    targets = []
    for pdf_path in all_pdfs:
        current = by_file.get(pdf_path.name)
        if current is None and target_mode in {"todos", "faltantes"}:
            targets.append(pdf_path)
            continue
        if (
            current is not None
            and target_mode in {"todos", "placeholders"}
            and str(current.get("layout_tipo", "")) == "PENDENTE_EXTRAIR"
        ):
            targets.append(pdf_path)
    return pending_mod.sort_pending_by_priority(targets, priority_items)


def replace_record(
    records: list[dict[str, object]],
    new_record: dict[str, object],
) -> None:
    pdf_name = str(new_record.get("arquivo_pdf", ""))
    for index, record in enumerate(records):
        if str(record.get("arquivo_pdf", "")) == pdf_name:
            records[index] = new_record
            return
    records.append(new_record)


def main() -> None:
    args = parse_args()
    pdf_mod = load_module(PDFS_MODULE_PATH, "zpdfs_finalize")
    pending_mod = load_module(PENDING_MODULE_PATH, "zpending_finalize")

    checkpoint = pdf_mod.load_checkpoint()
    records = list(checkpoint.get("records", []))
    targets = build_target_list(
        pdf_mod,
        pending_mod,
        records,
        args.modo_alvo,
    )
    if args.limite > 0:
        targets = targets[:args.limite]

    total = len(targets)
    print(f"ALVOS_REAIS={total}")
    if not targets:
        pdf_mod.save_consolidated_outputs(records)
        print(f"TOTAL_FINAL={len(records)}")
        return

    for index, pdf_path in enumerate(targets, start=1):
        try:
            record, _ = pdf_mod.extract_contract_data(
                pdf_path,
                keep_debug_assets=False,
                scan_last_page=args.forcar_ultima_pagina,
            )
            if not args.forcar_ultima_pagina and should_retry_full(record):
                record, _ = pdf_mod.extract_contract_data(
                    pdf_path,
                    keep_debug_assets=False,
                    scan_last_page=True,
                )
            replace_record(records, record)
            print(
                f"OK {index}/{total} | total_base={len(records)} | "
                f"arquivo={pdf_path.name} | "
                f"layout={record.get('layout_tipo', '')}"
            )
        except Exception as exc:
            print(f"ERRO {index}/{total} | arquivo={pdf_path.name} | {exc}")

        if index % args.salvar_a_cada == 0:
            pdf_mod.save_checkpoint(records)
            pdf_mod.save_consolidated_outputs(records)

    pdf_mod.save_checkpoint(records)
    pdf_mod.save_consolidated_outputs(records)
    print(f"TOTAL_FINAL={len(records)}")


if __name__ == "__main__":
    main()
