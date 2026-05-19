from __future__ import annotations

import argparse
import concurrent.futures
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pdfplumber


BASE_DIR = Path(__file__).resolve().parent
PDFS_MODULE_PATH = BASE_DIR / "pdfs.py"
OUTPUT_DIR = BASE_DIR / "saida"
CONSOLIDATED_JSON_PATH = OUTPUT_DIR / "contratos_consolidados.json"
FAILURES_PATH = OUTPUT_DIR / "falhas_processamento_pdfs.json"
DEFAULT_PRIORITY_PATH = BASE_DIR / "relatorio" / "lista_prioridade.xlsx"
REVIEW_DIR = BASE_DIR / "revisao_humana"
REVIEW_LOG_PATH = OUTPUT_DIR / "revisao_humana_log.json"
JSON_MARKER = "__JSON_RESULT__="


def load_pdfs_module():
    spec = importlib.util.spec_from_file_location("zpdfs", PDFS_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_priority_module():
    priority_module_path = BASE_DIR / "priorizar_contratos.py"
    spec = importlib.util.spec_from_file_location(
        "zprioridade",
        priority_module_path,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_existing_records() -> tuple[object, list[dict[str, object]]]:
    mod = load_pdfs_module()
    checkpoint = mod.load_checkpoint()
    records = list(checkpoint.get("records", []))
    return mod, records


def load_priority_items(priority_path: Path) -> list[dict[str, object]]:
    if not priority_path.exists():
        return []
    priority_mod = load_priority_module()
    items = priority_mod.iter_priority_rows(priority_path)
    for index, item in enumerate(items):
        item["ordem_prioridade"] = index
    return items


def score_priority_match(
    pdf_path: Path,
    priority_items: list[dict[str, object]],
) -> tuple[int, float, str]:
    if not priority_items:
        return (10**9, 0.0, "")

    priority_mod = load_priority_module()
    pdf_key = priority_mod.build_lookup_key(pdf_path.stem)
    if not pdf_key:
        return (10**9, 0.0, "")

    best_order = 10**9
    best_score = 0.0
    best_name = ""
    for item in priority_items:
        priority_key = str(item.get("chave_prioridade", ""))
        if not priority_key:
            continue
        if pdf_key == priority_key:
            return (
                int(item.get("ordem_prioridade", 10**9)),
                1.0,
                str(item.get("fornecedor_prioridade", "")),
            )
        if not priority_mod.has_meaningful_overlap(pdf_key, priority_key):
            continue
        score = priority_mod.combined_score(pdf_key, priority_key)
        if score < 0.78:
            continue
        order = int(item.get("ordem_prioridade", 10**9))
        if (order, -score) < (best_order, -best_score):
            best_order = order
            best_score = score
            best_name = str(item.get("fornecedor_prioridade", ""))

    return (best_order, best_score, best_name)


def sort_pending_by_priority(
    pending_pdfs: list[Path],
    priority_items: list[dict[str, object]],
) -> list[Path]:
    def has_native_text(pdf_path: Path) -> int:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    return 0
                text = pdf.pages[0].extract_text() or ""
            return 1 if len(text.strip()) >= 80 else 0
        except Exception:
            return 0

    decorated: list[tuple[tuple[int, int, float, int, str], Path]] = []
    for pdf_path in pending_pdfs:
        order, score, matched_name = score_priority_match(
            pdf_path,
            priority_items,
        )
        decorated.append(
            (
                (
                    0 if order < 10**9 else 1,
                    order,
                    -score,
                    -has_native_text(pdf_path),
                    pdf_path.stat().st_size,
                    pdf_path.name,
                ),
                pdf_path,
            )
        )
    decorated.sort(key=lambda item: item[0])
    return [item[1] for item in decorated]


def list_pending_pdfs(
    mod,
    records: list[dict[str, object]],
    failures: list[dict[str, object]],
    reprocess_failures: bool,
) -> list[Path]:
    processed = {str(record.get("arquivo_pdf", "")) for record in records}
    failed = {
        str(failure.get("arquivo_pdf", ""))
        for failure in failures
        if failure.get("arquivo_pdf")
    }
    return [
        pdf_path for pdf_path in mod.list_pdf_files()
        if pdf_path.name not in processed
        and (reprocess_failures or pdf_path.name not in failed)
    ]


def build_child_command(
    pdf_path: Path,
    timeout_seconds: int,
) -> list[str]:
    scan_last_page = "True" if timeout_seconds > 20 else "False"
    mod_path_literal = json.dumps(PDFS_MODULE_PATH.as_posix())
    pdf_path_literal = json.dumps(pdf_path.as_posix())
    child_code = (
        "import importlib.util, json;"
        "from pathlib import Path;"
        f"mod_path=Path({mod_path_literal});"
        "spec=importlib.util.spec_from_file_location('zpdfs', mod_path);"
        "mod=importlib.util.module_from_spec(spec);"
        "spec.loader.exec_module(mod);"
        "record,_=mod.extract_contract_data("
        f"Path({pdf_path_literal}), keep_debug_assets=False, "
        f"scan_last_page={scan_last_page});"
        f"print('{JSON_MARKER}' + json.dumps(record, ensure_ascii=True))"
    )
    return [sys.executable, "-c", child_code]


def extract_single_pdf(
    pdf_path: Path,
    timeout_seconds: int,
) -> dict[str, object]:
    result = subprocess.run(
        build_child_command(pdf_path, timeout_seconds),
        capture_output=True,
        timeout=timeout_seconds,
    )
    stdout = result.stdout.decode("utf-8", errors="replace")
    stderr = result.stderr.decode("utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(stderr.strip() or stdout.strip())

    for line in stdout.splitlines()[::-1]:
        if line.startswith(JSON_MARKER):
            return json.loads(line[len(JSON_MARKER):])
    raise RuntimeError(
        "Resultado JSON nao encontrado na saida do subprocesso."
    )


def save_failures(failures: list[dict[str, object]]) -> None:
    FAILURES_PATH.write_text(
        json.dumps(failures, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_failures() -> list[dict[str, object]]:
    if not FAILURES_PATH.exists() or FAILURES_PATH.stat().st_size == 0:
        return []
    return json.loads(FAILURES_PATH.read_text(encoding="utf-8"))


def remove_failure_entries(
    failures: list[dict[str, object]],
    pdf_name: str,
) -> list[dict[str, object]]:
    return [
        failure for failure in failures
        if str(failure.get("arquivo_pdf", "")) != pdf_name
    ]


def load_review_log() -> list[dict[str, object]]:
    if not REVIEW_LOG_PATH.exists() or REVIEW_LOG_PATH.stat().st_size == 0:
        return []
    return json.loads(REVIEW_LOG_PATH.read_text(encoding="utf-8"))


def save_review_log(entries: list[dict[str, object]]) -> None:
    REVIEW_LOG_PATH.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def is_strongly_illegible(record: dict[str, object], pdf_path: Path) -> bool:
    first_page_line_count = int(record.get("linhas_extraidas_pagina_1") or 0)
    last_page_line_count = int(
        record.get("linhas_extraidas_pagina_final") or 0,
    )
    empty_markers = [
        record.get("cnpj") in (None, ""),
        record.get("data_assinatura") in (None, ""),
        record.get("forma_pagamento") in (None, ""),
        record.get("bonus_percentual") in (None, ""),
        record.get("politica_trocas") in (None, ""),
        record.get("tipos_investimento_detectados") in (None, ""),
    ]
    no_structure = record.get("layout_tipo") == "NAO_IDENTIFICADO"
    supplier_fallback = (
        str(record.get("fornecedor_nome", "")).strip().upper()
        == pdf_path.stem.strip().upper()
    )
    very_low_ocr_signal = (first_page_line_count + last_page_line_count) <= 5
    return (
        no_structure
        and supplier_fallback
        and all(empty_markers)
        and very_low_ocr_signal
    )


def should_move_to_review(reason: str) -> bool:
    normalized = reason.lower()
    if "permission denied" in normalized:
        return False
    if "timeout_" in normalized:
        return False
    review_markers = [
        "pdf",
        "ocr",
        "image",
        "resultado json nao encontrado",
        "cannot identify image file",
        "syntax error",
    ]
    return any(marker in normalized for marker in review_markers)


def move_pdf_to_review(
    pdf_path: Path,
    motivo: str,
    review_log: list[dict[str, object]],
) -> None:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    target_path = REVIEW_DIR / pdf_path.name
    if target_path.exists():
        stem = target_path.stem
        suffix = target_path.suffix
        counter = 2
        while target_path.exists():
            target_path = REVIEW_DIR / f"{stem}_{counter}{suffix}"
            counter += 1
    shutil.move(str(pdf_path), str(target_path))
    review_log.append(
        {
            "arquivo_origem": pdf_path.name,
            "arquivo_revisao": target_path.name,
            "motivo": motivo,
        }
    )
    save_review_log(review_log)


def save_progress_outputs(mod, records: list[dict[str, object]]) -> None:
    mod.save_checkpoint(records)
    try:
        mod.save_consolidated_outputs(records)
    except PermissionError:
        prepared_records = mod.prepare_records_for_output(records)
        CONSOLIDATED_JSON_PATH.write_text(
            json.dumps(prepared_records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Processa PDFs pendentes com timeout por arquivo e checkpoint "
            "continuo."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Tempo maximo em segundos por PDF.",
    )
    parser.add_argument(
        "--limite",
        type=int,
        default=0,
        help="Limita a quantidade de PDFs pendentes processados nesta rodada.",
    )
    parser.add_argument(
        "--reprocessar-falhas",
        action="store_true",
        help="Tenta novamente PDFs que ja falharam em rodadas anteriores.",
    )
    parser.add_argument(
        "--planilha-prioridade",
        type=Path,
        default=DEFAULT_PRIORITY_PATH,
        help="Planilha usada para ordenar os pendentes pela fila prioritaria.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Quantidade de subprocessos executados em paralelo nesta rodada.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mod, records = load_existing_records()
    failures = load_failures()
    review_log = load_review_log()
    pending_pdfs = list_pending_pdfs(
        mod,
        records,
        failures,
        args.reprocessar_falhas,
    )
    priority_items = load_priority_items(args.planilha_prioridade)
    pending_pdfs = sort_pending_by_priority(pending_pdfs, priority_items)
    if args.limite > 0:
        pending_pdfs = pending_pdfs[:args.limite]

    total = len(pending_pdfs)
    print(f"Pendentes nesta rodada: {total}")
    if priority_items and pending_pdfs:
        print(f"Primeiro da fila prioritaria: {pending_pdfs[0].name}")
    if not pending_pdfs:
        mod.save_consolidated_outputs(records)
        print(f"TOTAL_FINAL={len(records)}")
        return

    def handle_result(
        index: int,
        pdf_path: Path,
        outcome: str,
        payload: dict[str, object] | Exception | None,
    ) -> None:
        nonlocal failures, records
        if outcome == "ok":
            assert isinstance(payload, dict)
            record = payload
            if is_strongly_illegible(record, pdf_path):
                move_pdf_to_review(
                    pdf_path,
                    "extracao_sem_estrutura_minima",
                    review_log,
                )
                print(
                    f"REVISAO {index}/{total} | arquivo={pdf_path.name}"
                )
                return
            failures = remove_failure_entries(failures, pdf_path.name)
            records.append(record)
            save_progress_outputs(mod, records)
            save_failures(failures)
            print(
                f"OK {index}/{total} | total_base={len(records)} | "
                f"arquivo={pdf_path.name}"
            )
            return

        if outcome == "timeout":
            failures = remove_failure_entries(failures, pdf_path.name)
            failure = {
                "arquivo_pdf": pdf_path.name,
                "motivo": f"timeout_{args.timeout}s",
            }
            failures.append(failure)
            save_failures(failures)
            print(f"TIMEOUT {index}/{total} | arquivo={pdf_path.name}")
            return

        assert isinstance(payload, Exception)
        failures = remove_failure_entries(failures, pdf_path.name)
        failure = {
            "arquivo_pdf": pdf_path.name,
            "motivo": str(payload),
        }
        failures.append(failure)
        save_failures(failures)
        if should_move_to_review(failure["motivo"]):
            move_pdf_to_review(pdf_path, failure["motivo"], review_log)
        print(f"ERRO {index}/{total} | arquivo={pdf_path.name}")

    def run_one(pdf_path: Path) -> tuple[str, dict[str, object] | Exception]:
        try:
            return "ok", extract_single_pdf(pdf_path, args.timeout)
        except subprocess.TimeoutExpired:
            return "timeout", subprocess.TimeoutExpired([], args.timeout)
        except Exception as exc:
            return "error", exc

    if args.workers <= 1:
        for index, pdf_path in enumerate(pending_pdfs, start=1):
            outcome, payload = run_one(pdf_path)
            handle_result(index, pdf_path, outcome, payload)
    else:
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.workers,
        ) as executor:
            future_map = {
                executor.submit(run_one, pdf_path): (index, pdf_path)
                for index, pdf_path in enumerate(pending_pdfs, start=1)
            }
            for future in concurrent.futures.as_completed(future_map):
                index, pdf_path = future_map[future]
                outcome, payload = future.result()
                handle_result(index, pdf_path, outcome, payload)

    save_failures(failures)
    print(f"TOTAL_FINAL={len(records)}")
    print(f"FALHAS={len(failures)}")
    print(f"SAIDA={OUTPUT_DIR}")


if __name__ == "__main__":
    main()
