"""
Agente_Limpeza.py — Agente de Limpeza do Ecossistema Equipes_Agentes
--------------------------------------------------------------
Varre recursivamente toda a árvore do projeto, identifica arquivos
temporários, de debug e caches e os remove com confirmação interativa.

Uso:
    python janitor.py           → Relatório + confirmação antes de deletar
    python janitor.py --dry-run → Apenas exibe o relatório, sem deletar nada
"""

if __name__ == '__main__':
    import os
    from pathlib import Path
    try:
        os.chdir(Path(__file__).parent.parent.resolve())
    except NameError:
        pass

import sys
import shutil
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

# ───────────────────────────────────────────────
# RAIZ DO ECOSSISTEMA
# ───────────────────────────────────────────────
RAIZ = Path(__file__).parent.parent.resolve()

# ───────────────────────────────────────────────
# PASTAS PROTEGIDAS (nunca entrar/apagar)
# ───────────────────────────────────────────────
PASTAS_PROTEGIDAS = {
    ".venv",
    ".agents",
    ".antigravity",
    ".claude",
    "memoria_squad",
    "historico_ruptura",
    "dist",               # binários compilados do GAM
}

# ───────────────────────────────────────────────
# ARQUIVOS PROTEGIDOS (nunca apagar por nome)
# ───────────────────────────────────────────────
ARQUIVOS_PROTEGIDOS = {
    "requirements.txt",
    ".gitignore",
    ".env",
    ".env.example",
    ".mcp.json",
    "CLAUDE.md",
    "README.md",
}

# ───────────────────────────────────────────────
# REGRAS DE LIMPEZA — (descrição, fn: Path → bool)
# ───────────────────────────────────────────────
def _e_debug(p: Path) -> bool:
    return p.is_file() and (
        p.name.startswith("debug_") or
        p.name.startswith("test_") or
        p.name.endswith("_test.py")
    ) and p.suffix == ".py"

def _e_saida_temp(p: Path) -> bool:
    NOMES = {"out.txt", "output.txt", "saida.txt", "saida_teste.txt",
             "verify_output.txt", "saida_agente.txt"}
    return p.is_file() and p.name.lower() in NOMES

def _e_preview(p: Path) -> bool:
    return p.is_file() and (
        "_preview." in p.name.lower() or
        p.name.lower().startswith("preview_")
    ) and p.suffix.lower() in {".xlsx", ".csv", ".html"}

def _e_pycache_dir(p: Path) -> bool:
    return p.is_dir() and p.name == "__pycache__"

def _e_pyc(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() in {".pyc", ".pyo"}

def _e_build_lixo(p: Path) -> bool:
    """Logs e HTMLs de inspeção gerados pelo PyInstaller (build/)."""
    if p.is_file() and "build" in p.parts:
        if p.name.startswith("warn-") and p.suffix == ".txt":
            return True
        if p.name.startswith("xref-") and p.suffix == ".html":
            return True
    return False

def _e_pasta_temp(p: Path) -> bool:
    """A pasta Aplicativos/temp/ inteira."""
    return p.is_dir() and p.name == "temp" and p.parent.name == "Aplicativos"

REGRAS: List[Tuple[str, callable]] = [
    ("🐛  Script de Debug/Teste",       _e_debug),
    ("📄  Saída temporária (.txt)",      _e_saida_temp),
    ("📊  Preview descartável",          _e_preview),
    ("📁  Cache Python (__pycache__/)",  _e_pycache_dir),
    ("🔩  Bytecode compilado (.pyc)",    _e_pyc),
    ("⚙️   Log de build PyInstaller",     _e_build_lixo),
    ("🗂️   Pasta temp/",                  _e_pasta_temp),
]

# ───────────────────────────────────────────────
# PROTEÇÃO DE ARQUIVOS RECENTES (< N horas)
# ───────────────────────────────────────────────
HORAS_PROTEGIDAS = 24

def _recente(p: Path) -> bool:
    try:
        mtime = datetime.fromtimestamp(p.stat().st_mtime)
        return (datetime.now() - mtime) < timedelta(hours=HORAS_PROTEGIDAS)
    except Exception:
        return False

# ───────────────────────────────────────────────
# VARREDURA
# ───────────────────────────────────────────────
def _protegido(p: Path) -> bool:
    """Retorna True se alguma parte do caminho é pasta protegida."""
    partes = {parte for parte in p.parts}
    return bool(partes & PASTAS_PROTEGIDAS) or p.name in ARQUIVOS_PROTEGIDOS

def varrer(raiz: Path) -> List[Tuple[str, Path, int, bool]]:
    """Retorna lista de (categoria, path, bytes, e_recente)."""
    candidatos = []

    for caminho in sorted(raiz.rglob("*")):
        if _protegido(caminho):
            continue
        for descricao, regra in REGRAS:
            if regra(caminho):
                try:
                    tamanho = (
                        caminho.stat().st_size if caminho.is_file()
                        else sum(f.stat().st_size for f in caminho.rglob("*") if f.is_file())
                    )
                except Exception:
                    tamanho = 0
                recente = _recente(caminho) if caminho.is_file() else False
                candidatos.append((descricao, caminho, tamanho, recente))
                break  # só aplica primeira regra correspondente

    return candidatos

# ───────────────────────────────────────────────
# RELATÓRIO
# ───────────────────────────────────────────────
def _formatar_tamanho(b: int) -> str:
    if b < 1024:
        return f"{b} B"
    elif b < 1024 ** 2:
        return f"{b/1024:.1f} KB"
    return f"{b/1024**2:.1f} MB"

def exibir_relatorio(candidatos: List[Tuple]) -> None:
    if not candidatos:
        print("\n✅  Ecossistema limpo! Nada a remover.\n")
        return

    # Agrupa por categoria
    por_categoria: dict = {}
    for desc, caminho, tamanho, recente in candidatos:
        por_categoria.setdefault(desc, []).append((caminho, tamanho, recente))

    total_bytes = sum(t for _, _, t, _ in candidatos)
    n_recentes  = sum(1 for _, _, _, r in candidatos if r)

    print("\n" + "═" * 68)
    print("  🧹  RELATÓRIO DE LIMPEZA — ECOSSISTEMA EQUIPES_AGENTES")
    print("═" * 68)

    for desc, itens in por_categoria.items():
        print(f"\n  {desc}  ({len(itens)} item/s)")
        for caminho, tamanho, recente in itens:
            flag = " ⚠️  RECENTE (<24h)" if recente else ""
            rel  = caminho.relative_to(RAIZ)
            print(f"    {'📁' if caminho.is_dir() else '📄'}  {rel}  [{_formatar_tamanho(tamanho)}]{flag}")

    print("\n" + "─" * 68)
    print(f"  📦  Total: {len(candidatos)} item/s  |  {_formatar_tamanho(total_bytes)}")
    if n_recentes:
        print(f"  ⚠️   {n_recentes} item/s com menos de {HORAS_PROTEGIDAS}h — serão ignorados na deleção")
    print("─" * 68 + "\n")

# ───────────────────────────────────────────────
# DELEÇÃO
# ───────────────────────────────────────────────
def deletar(candidatos: List[Tuple]) -> List[Tuple]:
    """Deleta somente itens não-recentes. Retorna lista de (path, ok, erro)."""
    resultados = []
    para_deletar = [(d, c, t) for d, c, t, r in candidatos if not r]

    for desc, caminho, tamanho in para_deletar:
        try:
            if caminho.is_dir():
                shutil.rmtree(caminho)
            else:
                caminho.unlink()
            resultados.append((caminho, True, None))
        except Exception as e:
            resultados.append((caminho, False, str(e)))

    return resultados

# ───────────────────────────────────────────────
# LOG
# ───────────────────────────────────────────────
def salvar_log(resultados: List[Tuple], dry_run: bool) -> Path:
    log_dir = RAIZ / "Agentes" / ".motor" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "janitor_log.txt"
    modo = "DRY-RUN" if dry_run else "EXECUÇÃO REAL"
    linhas = [
        f"=== JANITOR — {modo} === {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ]
    for caminho, ok, erro in resultados:
        rel  = caminho.relative_to(RAIZ)
        stat = "OK" if ok else f"ERRO: {erro}"
        linhas.append(f"[{stat}]  {rel}")

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n\n")

    return log_path

# ───────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Agente de limpeza do ecossistema Equipes_Agentes"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Apenas exibe o relatório sem deletar nada"
    )
    parser.add_argument(
        "--yes", "-y", "--force", action="store_true",
        help="Executa a limpeza sem pedir confirmação (Modo Automático)"
    )
    args = parser.parse_args()

    print(f"\n🔍  Varrendo: {RAIZ}")
    candidatos = varrer(RAIZ)
    exibir_relatorio(candidatos)

    if not candidatos:
        return

    if args.dry_run:
        print("ℹ️   Modo DRY-RUN ativo — nenhum arquivo foi apagado.\n")
        salvar_log([(c, True, None) for _, c, _, _ in candidatos], dry_run=True)
        return

    if not args.yes:
        resposta = input("  Deseja remover os itens listados (exceto recentes)? [S/N]: ").strip().upper()
        if resposta != "S":
            print("\n❌  Operação cancelada pelo usuário.\n")
            return
    else:
        print("  🚀  Modo automático (--yes) ativo. Pulando confirmação.")

    print("\n🗑️   Removendo...\n")
    resultados = deletar(candidatos)

    ok  = [r for r in resultados if r[1]]
    err = [r for r in resultados if not r[1]]

    print(f"  ✅  {len(ok)} item/s removidos com sucesso.")
    if err:
        print(f"  ⚠️   {len(err)} erro/s:")
        for caminho, _, erro in err:
            print(f"       {caminho.name}: {erro}")

    log = salvar_log(resultados, dry_run=False)
    print(f"\n  📋  Log salvo em: {log.relative_to(RAIZ)}\n")


if __name__ == "__main__":
    main()
